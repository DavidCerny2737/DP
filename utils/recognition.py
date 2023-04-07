from PIL import Image
import numpy as np
from datetime import datetime, timedelta
from threading import Lock

import cv2
import os

# holds records of type: datetime of record, face.png\n
REPRESENTANTS_FILE = 'representants.txt'
REPRESENTANTS_DIR = 'representants'
LOG_IMAGES_DIR = 'images'
# LOG_FILE = '..\\log.txt'
DATETIME_FORMAT = '%d.%m.%Y %H:%M:%S'
TIMEDELTA_HOURS_FOR_CLEAR = timedelta(hours=1)

# array of representants encodings
representants_encodings = []
encoding_mutex = Lock()
representants_file_mutex = Lock()


def check_face(cv2_face_image, cv2_full_image):
    import face_recognition
    timestamp = datetime.today()
    img = cv2.cvtColor(cv2_face_image, cv2.COLOR_BGR2RGB)
    im_pil = Image.fromarray(img)

    file_empty = False
    try:
        representants_file_mutex.acquire()
        if os.stat(REPRESENTANTS_FILE).st_size == 0:
            file_empty = True
    finally:
        representants_file_mutex.release()

    if file_empty:
        put_img_to_representants(im_pil, timestamp, cv2_full_image)
        return

    im_np = np.array(im_pil)
    input_encodings = face_recognition.face_encodings(im_np, known_face_locations=[(0, im_pil.width, im_pil.height, 0)])[0]
    if len(representants_encodings) == 0:
        put_img_to_representants(im_pil, timestamp, cv2_full_image)
    else:
        try:
            encoding_mutex.acquire()
            result = face_recognition.compare_faces(representants_encodings, input_encodings)
        finally:
            encoding_mutex.release()
        if not any(result):
            put_img_to_representants(im_pil, timestamp, cv2_full_image)


def put_img_to_representants(pil_image, timestamp, cv2_full_image):
    import face_recognition
    index = sum(1 for x in os.listdir(REPRESENTANTS_DIR) if x.endswith('.png'))
    image_name = str(index) + '.png'

    # save new representant
    pil_image.save(os.path.join(REPRESENTANTS_DIR, image_name))

    # save full image
    cv2.imwrite(os.path.join(LOG_IMAGES_DIR, image_name), cv2_full_image)

    np_image = np.array(pil_image)
    image_encodings = face_recognition.face_encodings(np_image, known_face_locations=[(0, pil_image.width, pil_image.height, 0)])[0]
    try:
        encoding_mutex.acquire()
        representants_encodings.append(image_encodings)
    finally:
        encoding_mutex.release()

    try:
        representants_file_mutex.acquire()
        # write representant path and time
        with open(REPRESENTANTS_FILE, 'a') as f:
            f.write(timestamp.strftime(DATETIME_FORMAT) + ', ' + image_name + '\n')
    finally:
        representants_file_mutex.release()


def remove_old_representants():
    global representants_encodings

    ts_hour_before = datetime.today() - TIMEDELTA_HOURS_FOR_CLEAR
    image_names = []
    try:
        representants_file_mutex.acquire()
        with open(REPRESENTANTS_FILE, 'r') as f:
            lines = f.readlines()
    finally:
        representants_file_mutex.release()

    if len(lines) == 0:
        for file in os.listdir(REPRESENTANTS_DIR):
            os.remove(os.path.join(REPRESENTANTS_DIR, file))
        return

    for line in lines:
        parts = line.split(',')
        timestamp, filename = (datetime.strptime(parts[0].strip(), DATETIME_FORMAT), parts[1].strip())
        if timestamp < ts_hour_before:
            image_names.append(filename)

    try:
        representants_file_mutex.acquire()
        # remove from representants file
        with open(REPRESENTANTS_FILE, 'w') as f:
            for line in lines:
                im_name = line.split(',')[1].strip()
                if not im_name in image_names:
                    f.write(line)
    finally:
        representants_file_mutex.release()
    # delete png and in memory embeddings
    for image_name in image_names:
        if os.path.isfile(os.path.join(LOG_IMAGES_DIR, image_name)):
            os.remove(os.path.join(LOG_IMAGES_DIR, image_name))
        if os.path.isfile(os.path.join(REPRESENTANTS_DIR, image_name)):
            os.remove(os.path.join(REPRESENTANTS_DIR, image_name))

    try:
        encoding_mutex.acquire()
        representants_encodings = []
    finally:
        encoding_mutex.release()
    load_encodings()


def initialize_recognition():
    import face_recognition
    # no need for synchronization -> only starting thread will execute this
    if not os.path.isdir(REPRESENTANTS_DIR):
        os.mkdir(REPRESENTANTS_DIR)
    if not os.path.isdir(LOG_IMAGES_DIR):
        os.mkdir(LOG_IMAGES_DIR)
    if not os.path.isfile(REPRESENTANTS_FILE):
        repr_file = open(REPRESENTANTS_FILE, 'w')
        repr_file.close()
        return
    else:
        remove_old_representants()
        with open(REPRESENTANTS_FILE, 'r') as f:
            lines = f.readlines()
        for line in lines:
            parts = line.split(', ')
            timestamp, image_name = (datetime.strptime(parts[0].strip(), DATETIME_FORMAT), parts[1].strip())
            pil_image = Image.open(os.path.join(REPRESENTANTS_DIR, image_name))
            np_image = np.array(pil_image)
            encodings = face_recognition.face_encodings(np_image, known_face_locations=[(0, pil_image.width, pil_image.height, 0)])[0]
            representants_encodings.append(encodings)


def load_encodings():
    import face_recognition
    try:
        representants_file_mutex.acquire()
        with open(REPRESENTANTS_FILE, 'r') as f:
            lines = f.readlines()
    finally:
        representants_file_mutex.release()

    try:
        encoding_mutex.acquire()
        for line in lines:
            image_name = line.split(', ')[1].strip()
            pil_image = Image.open(os.path.join(REPRESENTANTS_DIR, image_name))
            np_image = np.array(pil_image)
            encodings = face_recognition.face_encodings(np_image, known_face_locations=[(0, pil_image.width, pil_image.height, 0)])[0]
            representants_encodings.append(encodings)
    finally:
        encoding_mutex.release()


def get_representants_table():
    try:
        representants_file_mutex.acquire()
        if not os.path.exists(REPRESENTANTS_FILE):
            f = open(REPRESENTANTS_FILE, 'w')
            f.close()

        with open(REPRESENTANTS_FILE, 'r') as f:
            lines = f.readlines()
    finally:
        representants_file_mutex.release()

    result = {}
    i = 0
    for line in lines:
        parts = line.split(', ')
        timestamp, image_name = (parts[0].strip(), parts[1].strip())
        result[i] = (timestamp, image_name)
        i += 1
    return result
