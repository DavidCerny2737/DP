from flask import Flask, Response
from flask import render_template, redirect, url_for, request, jsonify, send_from_directory
import detect
from utils.recognition import initialize_recognition, get_representants_table, LOG_IMAGES_DIR

from flask_sock import Sock
import base64
from flask_wtf.csrf import CSRFProtect
import secrets
import json

sock = Sock()
app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(16)
csrf = CSRFProtect(app)
sock.init_app(app)
stream_width = None
stream_height = None
model = None

NAV_LOG = 'LOG'
NAV_STREAM = 'STREAM'
#IMG_SIZE = (416, 416)
IMG_SIZE_KEY = 'imgSize'


# for GPU run use device: '0'
# for optimized onnx run on GPU use onnx: True, but first export model using export_onnx.py with proper IMAGE_SIZE constant
CONFIG = {'weights': ['old_weights/best.pt'], 'img-size': 512, 'conf-thres': 0.4, 'iou-thres': 0.6, 'device': '0', 'view-img': True,
            'save-txt': False, 'agnostic-nms': True, 'augment': False, 'update': False, 'cfg': 'models/yolov4-csp.cfg',
            'names': 'data/coco.names', 'save-img': False, 'classes': None, 'onnx': False}



@app.route('/main/config', methods=['POST'])
def config():
    global model
    if model is None:
        CONFIG['img-size'] = request.json['width']
        print('Image size is ' + str(CONFIG['img-size']))
        print('Starting to initialize model')
        model = detect.Model(CONFIG)
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


@app.route('/main/table', methods=['POST'])
def get_table():
    table = get_representants_table()
    return jsonify(table)


@app.route('/main/log/<filename>')
def download_file(filename):
    return send_from_directory(LOG_IMAGES_DIR, filename)


@sock.route('/detect')
def detect_frame(ws):
    while True:
        # remove image/png base64; ... preamble from POST
        data = ws.receive()[22:]
        base64_bytes = base64.b64decode(data)
        result_data = model.forward(base64_bytes)
        result = [res.to_json() for res in result_data]
        ws.send(json.dumps(result))


def default_props(active=NAV_STREAM):
    return {'active': active}


if __name__ == '__main__':
    app.run()
