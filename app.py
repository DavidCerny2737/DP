from flask import Flask
from flask import render_template, redirect, url_for, request, jsonify, send_from_directory
import detect
from utils.recognition import initialize_recognition, get_representants_table, LOG_IMAGES_DIR

from flask_wtf.csrf import CSRFProtect
import secrets
import json

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)
csrf = CSRFProtect(app)
stream_width = None
stream_height = None
model = None

NAV_LOG = 'LOG'
NAV_STREAM = 'STREAM'
IMG_SIZE = (416, 416)
IMG_SIZE_KEY = 'imgSize'


@app.route('/main/config', methods=['POST'])
def config():
    global model
    if model is None:
        config = detect.provide_default_config()
        config['img-size'] = request.json['width']
        config['onnx'] = False
        print('Image size is ' + str(config['img-size']))
        print('Starting to initialize model')
        model = detect.Model(config)
        print('Model initialzied and ready')
        print('Initializing face recognition module')
        initialize_recognition()
        print('Face recognition module initialized')
    return json.dumps({'data': ''}), 200, {'ContentType': 'application/json'}


@app.route('/')
def root():
    return redirect(url_for('stream'))


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
    return {'active': active, IMG_SIZE_KEY: IMG_SIZE}


if __name__ == '__main__':
    app.run()
