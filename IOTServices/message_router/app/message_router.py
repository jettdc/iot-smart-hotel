from activator import RoomActivator
from flask import Flask, request
import paho.mqtt.client as mqtt
from flask_cors import CORS
import threading
import requests
import secrets
import json
import os

UNIQ_ID = secrets.token_hex(nbytes=16)

MQTT_SERVER = os.getenv('MQTT_SERVER_ADDRESS')
MQTT_PORT = int(os.getenv('MQTT_SERVER_PORT'))

DATA_INGEST_SERVER_HOST = os.getenv('API_SERVER_ADDRESS')
DATA_INGEST_SERVER_PORT = os.getenv('API_SERVER_PORT')
DATA_INGEST_SERVER_URL = "http://" + DATA_INGEST_SERVER_HOST + ":" + DATA_INGEST_SERVER_PORT

SELF_HOST = os.getenv('API_HOST')
SELF_PORT = os.getenv('API_PORT')

ALL_TOPICS = "#"
CONFIG_TOPIC = ""
TEMPERATURE_TOPIC = ""
AIR_CONDITIONER_TOPIC = ""
BLIND_TOPIC = ""

index_room = 1

current_temperature = {"temperature": {"active": False, "temperature": 0}}
current_air = {"air_conditioner": {"active": False, "level": 0}}
current_presence = {"presence": {"active": False, "detected": False}}

saved_rooms = {}

client = None
app = Flask(__name__)


def store_message(obj):
    pass


def on_connect(client, userdata, flags, rc):
    print("Connected on subscribe with code ", rc)

    client.subscribe(ALL_TOPICS)

    print("Subscribed to all.")


def parse_room(room_name):
    # of form 'Room00', so: Room00 => 00
    return int(room_name[4:])


def create_ingest_message(room, type, value, timestamp):
    return {
        "room": parse_room(room),
        "type": type,
        "value": value,
        "date": timestamp,
    }


def on_message(client, userdata, msg):
    global current_temperature, current_air, current_presence, index_room

    print("Message received at ", msg.topic, " with message ", msg.payload.decode())

    topic = msg.topic.split('/')

    if topic[-1] == "config":
        # If the room is not configured yet, configure it
        if saved_rooms.get(msg.payload.decode()) is None:
            print("Subscribing to all again")
            client.subscribe(ALL_TOPICS)
            # Assign a room name and put it in the lookup table, lookup by id
            room_name = "Room" + str(index_room)
            index_room += 1
            saved_rooms[msg.payload.decode()] = room_name
            print("Digital with id ", msg.payload.decode(), " saved as ", room_name)

            print("Subscribing to room connect/disconnect channels...")
            client.subscribe("hotel/rooms/" + room_name + "/disconnect")
            client.subscribe("hotel/rooms/" + room_name + "/connect")

            # Tell the digital twin what room number they have been assigned as
            client.publish(msg.topic + "/room", payload=room_name, qos=0, retain=True)
            print("Published ", room_name, " at topic ", msg.topic + "/room")

            return

    elif 'disconnect' in topic:
        room = topic[-2]
        print("Deactivating room: ", room)
        activator = RoomActivator(room)
        activator.set_not_active()

    elif 'connect' in topic:
        room = topic[-2]
        print("Activating room: ", room)
        activator = RoomActivator(room)
        activator.register_or_set_active()

    elif 'telemetry' in topic:
        room = topic[-3]
        ttype = topic[-1]
        timestamp = json.loads(msg.payload.decode())["timestamp"]
        if ttype == "temperature":
            current_temperature = json.loads(msg.payload.decode())
            value = current_temperature["temperature"]["temperature"]
            requests.post(
                DATA_INGEST_SERVER_URL + "/device_state",
                json=create_ingest_message(room, ttype, value, timestamp)
            )

        elif ttype == "air_conditioner":
            current_air = json.loads(msg.payload.decode())
            value = current_air["air_conditioner"]["level"]
            requests.post(
                DATA_INGEST_SERVER_URL + "/device_state",
                json=create_ingest_message(room, ttype + "_level", value, timestamp)
            )
            mode = current_air["air_conditioner"]["mode"]
            requests.post(
                DATA_INGEST_SERVER_URL + "/device_state",
                json=create_ingest_message(room, ttype + "_mode", mode, timestamp)
            )

        elif ttype == "presence":
            current_presence = json.loads(msg.payload.decode())
            value = current_presence["presence"]["detected"]
            requests.post(
                DATA_INGEST_SERVER_URL + "/device_state",
                json=create_ingest_message(room, ttype, value, timestamp)
            )

        elif ttype == "blind":
            current_blind = json.loads(msg.payload.decode())
            value = current_blind["blind"]["level"]
            requests.post(
                DATA_INGEST_SERVER_URL + "/device_state",
                json=create_ingest_message(room, ttype, value, timestamp)
            )

        elif ttype == "balcony_light":
            current_balcony_light = json.loads(msg.payload.decode())
            value = current_balcony_light["balcony_light"]["level"]
            requests.post(
                DATA_INGEST_SERVER_URL + "/device_state",
                json=create_ingest_message(room, ttype + "_level", value, timestamp)
            )
            on = current_balcony_light["balcony_light"]["on"]
            requests.post(
                DATA_INGEST_SERVER_URL + "/device_state",
                json=create_ingest_message(room, ttype + "_on", on, timestamp)
            )

        elif ttype == "interior_light":
            current_interior_light = json.loads(msg.payload.decode())
            value = current_interior_light["interior_light"]["level"]
            requests.post(
                DATA_INGEST_SERVER_URL + "/device_state",
                json=create_ingest_message(room, ttype + "_level", value, timestamp)
            )
            on = current_interior_light["interior_light"]["on"]
            requests.post(
                DATA_INGEST_SERVER_URL + "/device_state",
                json=create_ingest_message(room, ttype + "_on", on, timestamp)
            )


def connect_mqtt():
    c = mqtt.Client("ROUTER-" + UNIQ_ID)
    c.username_pw_set(username="dso_server", password="dso_password")
    c.on_connect = on_connect
    c.on_message = on_message
    c.connect(MQTT_SERVER, MQTT_PORT, 60)
    return c


def publish_command(c_room, c_type, command):
    topic = "hotel/rooms/" + c_room + "/command/" + c_type
    client.publish(topic, payload=command, qos=0, retain=True)
    print("Published command for", c_type, ":", command, 'at', topic)


def send_command(params):
    c_type = params["type"]

    command = None
    if c_type == "air_conditioner":
        command = json.dumps({"mode": params["mode"]})
    elif c_type == "blind":
        command = json.dumps({"level": params["level"]})
    elif c_type == "balcony_light":
        command = json.dumps({"level": params["level"], "on": params["on"]})
    elif c_type == "interior_light":
        command = json.dumps({"level": params["level"], "on": params["on"]})
    else:
        return {"response": "Incorrect type param"}, 401

    publish_command(params["room"], c_type, command)

    return {"response": c_type + " command successfully sent."}, 200


"""
{
"room": str e.g. "Room3"
"type": str e.g. "blind"
"[other params]" e.g. "level": 102
}
"""


@app.route('/device_state', methods=['POST'])
def device_state():
    if request.method == 'POST':
        params = request.get_json()
        return send_command(params)


@app.route('/facade', methods=['POST'])
def command_facade():
    params = request.get_json()

    if params.get('rooms') is None:
        return {'response': 'Missing rooms array.'}, 401

    if params.get('states') is None:
        return {'response': 'Missing states array.'}, 401

    rooms = params['rooms']
    states = params['states']

    if len(rooms) != len(states):
        return {'response': 'Must have a boolean state corresponding to each room.'}, 401

    for i, room in enumerate(rooms):
        print("FACADE: SENDING", room, states[i])
        send_command({
            'room': room,
            'type': 'balcony_light',
            'on': states[i],
            'level': 100 if states[i] else 0,
        })


def mqtt_listener():
    client.loop_forever()


if __name__ == "__main__":
    client = connect_mqtt()
    t1 = threading.Thread(target=mqtt_listener)
    t1.setDaemon(True)
    t1.start()

    CORS(app)
    app.run(host=SELF_HOST, port=SELF_PORT, debug=False)
