from flask import Flask
from flask import render_template, redirect, url_for, request, jsonify, send_from_directory
from app import detect
from app.utils.recognition import initialize_recognition, get_representants_table, LOG_IMAGES_DIR


app = Flask(__name__)
stream_width = None
stream_height = None
model = None

NAV_LOG = 'LOG'
NAV_STREAM = 'STREAM'
IMG_SIZE = 640
IMG_SIZE_KEY = 'imgSize'


@app.before_first_request
def setup_model():
    global model
    config = detect.provide_default_config()
    config['img-size'] = IMG_SIZE
    print('Image size is ' + str(config['img-size']))
    print('Starting to initialize model')
    model = detect.Model(config)
    print('Model initialzied and ready')
    print('Initializing face recognition module')
    initialize_recognition()
    print('Face recognition module initialized')


@app.route("/")
def root():
    return redirect(url_for('main'))


@app.route('/main')
def stream():
    table = get_representants_table()
    return render_template('main.html', table=[table], **default_props())


@app.route('/main/frame', methods=['POST'])
def frame():
    base64_img = request.data
    result = model.forward(base64_img)
    return jsonify({'content-type': 'image/png', 'data': result})


@app.route('/main/table', methods=['POST'])
def get_table():
    table = get_representants_table()
    return jsonify(table)


@app.route('/main/log/<filename>')
def download_file(filename):
    return send_from_directory(LOG_IMAGES_DIR, filename)


def default_props(active=NAV_STREAM):
    return {"active": active, IMG_SIZE_KEY: IMG_SIZE}


