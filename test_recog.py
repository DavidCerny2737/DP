import face_recognition
from PIL import Image
import numpy as np


if __name__ == '__main__':
    im = Image.open('face.png')
    np_image_arr = np.array(im)
    image_encodings = face_recognition.face_encodings(np_image_arr, known_face_locations=[(0, im.width, im.height, 0)])[0]

    im2 = Image.open('face2.png')
    np_image2_arr = np.array(im2)
    image_encodings_2 = face_recognition.face_encodings(np_image2_arr, known_face_locations=[(0, im2.width, im2.height, 0)])[0]
    print(type(image_encodings))

    results = face_recognition.compare_faces([image_encodings], image_encodings_2)
    print(results)