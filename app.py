from flask import Flask
from flask import render_template, redirect, url_for, request, jsonify, send_from_directory
from flask_socketio import SocketIO
import detect
from utils.recognition import initialize_recognition, get_representants_table, LOG_IMAGES_DIR
from utils.general import *
import PIL


app = Flask(__name__)
socketio = SocketIO(app)
stream_width = None
stream_height = None
model = None

NAV_LOG = 'LOG'
NAV_STREAM = 'STREAM'
IMG_SIZE = (416, 416)
IMG_SIZE_KEY = 'imgSize'


@app.before_first_request
def setup_app():
    global model
    config = detect.provide_default_config()
    config['img-size'] = IMG_SIZE
    #config['onnx'] = False
    print('Image size is ' + str(config['img-size']))
    print('Starting to initialize model')
    model = detect.Model(config)
    print('Model initialzied and ready')
    print('Initializing face recognition module')
    initialize_recognition()
    print('Face recognition module initialized')


@app.route("/")
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


@socketio.on('frame')
def hangle_socket_message(data):
    #t0 = time.time()
    result = model.forward(data['blob'])
    #print('total server latency: (%.3fs)' % (time.time() - t0))
    socketio.emit('update-picture', result)


def default_props(active=NAV_STREAM):
    return {"active": active, IMG_SIZE_KEY: IMG_SIZE}


def collect_env_info():
    """Returns env info as a string.
    Code source: github.com/facebookresearch/maskrcnn-benchmark
    """
    from torch.utils.collect_env import get_pretty_env_info
    env_str = get_pretty_env_info()
    env_str += '\n        Pillow ({})'.format(PIL.__version__)
    return env_str


if __name__ == '__main__':
    #print(collect_env_info())
    socketio.run(app)