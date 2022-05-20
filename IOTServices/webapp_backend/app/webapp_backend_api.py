from flask import Flask, request
from flask_cors import CORS
import requests
import json
import os

app = Flask(__name__)
CORS(app)

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
DATA_INGESTION_API_PORT = os.getenv('DATA_INGESTION_API_PORT')
DATA_INGESTION_API_URL = 'http://' + os.getenv('DATA_INGESTION_API_ADDRESS') + ":" + DATA_INGESTION_API_PORT
MESSAGE_ROUTER_API_PORT = os.getenv('MESSAGE_ROUTER_API_PORT')
MESSAGE_ROUTER_API_URL = 'http://' + os.getenv('MESSAGE_ROUTER_API_ADDRESS') + ":" + MESSAGE_ROUTER_API_PORT


@app.route('/device_state', methods=['POST'])
def device_state():
    if request.method == 'POST':
        params = request.get_json()
        r = requests.post(
            MESSAGE_ROUTER_API_URL + "/device_state",
            json=params
        )
        return json.dumps(r.json()), r.status_code



@app.route('/device_state/<room>', methods=['GET'])
def room_state(room):
    r = requests.get(DATA_INGESTION_API_URL + '/device_state/' + room)
    return r.json(), r.status_code


@app.route('/facade', methods=['POST'])
def change_facade():
    params = request.get_json()

    if params.get('rooms') is None:
        return {'response': 'Missing rooms array.'}, 401

    if params.get('states') is None:
        return {'response': 'Missing states array.'}, 401

    rooms = params['rooms']
    states = params['states']

    if len(rooms) != len(states):
        return {'response': 'Must have a boolean state corresponding to each room.'}, 401

    requests.post(MESSAGE_ROUTER_API_URL + '/facade',
                  json=request.get_json())

    return {'response': 'Successfully requested facade change.'}, 200


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=False)
