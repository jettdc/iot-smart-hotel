from data_ingestion import insert_device_state, get_device_state
from flask import Flask, request
from flask_cors import CORS
import os

app = Flask(__name__)
CORS(app)


@app.route('/device_state/<room>', methods=['GET'])
def gds(room):
    if room == "all":
        results = []
        for i in range(70):
            results.append(get_device_state(i + 1))
        return {"results": results}, 200

    res = get_device_state(room)
    return {"results": res}, 200


@app.route('/device_state', methods=['POST'])
def device_state():
    if request.method == 'POST':
        params = request.get_json()

        if len(params) != 4:
            return {"response": "Incorrect parameters"}, 401

        cursor = insert_device_state(params)
        return {"response": f"{cursor.rowcount} records inserted."}, 200


if __name__ == "__main__":
    HOST = os.getenv('HOST')
    PORT = int(os.getenv('PORT'))
    app.run(host=HOST, port=PORT, debug=False)
