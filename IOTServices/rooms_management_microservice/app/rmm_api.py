from rmm import register_or_activate_device, de_activate_device
from flask import Flask, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)


@app.route('/activate/<device>', methods=['POST'])
def ad(device):
    register_or_activate_device(device)
    return {"response": "Successfully activated the device."}, 200


@app.route('/deactivate/<device>', methods=['POST'])
def dd(device):
    de_activate_device(device)
    return {"response": "Successfully activated the device."}, 200


HOST = os.getenv('HOST')
PORT = int(os.getenv('PORT'))
app.run(host=HOST, port=PORT, debug=False)
