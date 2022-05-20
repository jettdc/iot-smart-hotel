import datetime
import time
import paho.mqtt.client as mqtt
import json
import secrets
import os
import threading

UPSTREAM_MQTT_SERVER = os.getenv('MQTT-1_SERVER_ADDRESS')
UPSTREAM_MQTT_PORT = int(os.getenv('MQTT-1_SERVER_PORT'))

DOWNSTREAM_MQTT_SERVER = os.getenv('MQTT-2_SERVER_ADDRESS')
DOWNSTREAM_MQTT_PORT = int(os.getenv('MQTT-2_SERVER_PORT'))

ROOM_ID = secrets.token_hex(nbytes=16)

CONFIG_TOPIC = "hotel/rooms/" + ROOM_ID + "/config"
ROOM_TOPIC = CONFIG_TOPIC + "/room"

ALL_TOPICS = -1

TEMPERATURE_TOPIC = None
AIR_CONDITIONER_TOPIC = None
PRESENCE_TOPIC = None
BLIND_TOPIC = None
BALCONY_LIGHT_TOPIC = None
INTERIOR_LIGHT_TOPIC = None

AIR_CONDITIONER_COMMAND_TOPIC = None
BLIND_COMMAND_TOPIC = None
BALCONY_LIGHT_COMMAND_TOPIC = None
INTERIOR_LIGHT_COMMAND_TOPIC = None

DISCONNECT_TOPIC = None
CONNECTED_TOPIC = None

room_number = None

sensors = {}

current_temperature = {"temperature": {"active": False, "temperature": None}, "timestamp": str(datetime.datetime.now())}
current_air = {"air_conditioner": {"active": False, "mode": 0, "level": None},
               "timestamp": str(datetime.datetime.now())}
current_presence = {"presence": {"active": False, "detected": None}, "timestamp": str(datetime.datetime.now())}
current_blind = {"blind": {"active": False, "level": None}, "timestamp": str(datetime.datetime.now())}
current_balcony_light = {"balcony_light": {"active": False, "level": None, "on": None}, "timestamp": str(datetime.datetime.now())}
current_interior_light = {"interior_light": {"active": False, "level": None, "on": None}, "timestamp": str(datetime.datetime.now())}

upstream_client = None
downstream_client = None

pi_is_connected = False

# For storing the latest queued command (in JSON) for each
# of the components that can receive commands
queued_commands = {
    "air_conditioner": None,
    "blind": None,
    "balcony_light": None,
    "interior_light": None,
}


def retransmit_thread_target():
    global queued_commands, downstream_client


    # Allow time to subscribe
    print("queued_commands")
    print(queued_commands)
    time.sleep(3)

    for sensor in queued_commands:
        if queued_commands[sensor] is None:
            continue

        topic = None
        if sensor == "air_conditioner":
            topic = AIR_CONDITIONER_COMMAND_TOPIC
        elif sensor == "blind":
            topic = BLIND_COMMAND_TOPIC
        elif sensor == "balcony_light":
            topic = BALCONY_LIGHT_COMMAND_TOPIC
        elif sensor == "interior_light":
            topic = INTERIOR_LIGHT_COMMAND_TOPIC
        else:
            continue

        print("Republishing stored command for", sensor, ":", queued_commands[sensor], "at", topic)
        downstream_client.publish(topic, payload=queued_commands[sensor], qos=1, retain=False)

        queued_commands[sensor] = None


def retransmit_queued_commands():
    retransmit_thread = threading.Thread(target=retransmit_thread_target)
    retransmit_thread.setDaemon(True)
    retransmit_thread.start()

"""
START UPSTREAM
"""


def on_upstream_connect(client, userdata, flags, rc):
    print("Upstream: Digital twin connected to message router with code ", rc)

    print("Upstream: Subscribed to ", ROOM_TOPIC)
    # Where our room number will be published
    client.subscribe(ROOM_TOPIC)

    print("Upstream: Sending the ID ", ROOM_ID, ' to topic ', CONFIG_TOPIC)
    # Send the request for our room number to the message router.
    client.publish(CONFIG_TOPIC, payload=ROOM_ID, qos=0, retain=False)


def on_upstream_message(client, userdata, msg):
    global queued_commands, pi_is_connected, room_number

    print("Message received from upstream at", msg.topic, "with message", msg.payload.decode())

    topic = msg.topic.split("/")

    if "config" in topic:
        room_number = msg.payload.decode()
        print("Upstream: Room number received as ", room_number)

    elif "command" in topic:
        print(topic[-1], "command received:", msg.payload.decode())

        if not pi_is_connected:
            print("Pi is not connected. Storing the command for later transmission.")
            queued_commands[topic[-1]] = msg.payload.decode()

        elif topic[-1] == "air_conditioner":
            downstream_client.publish(AIR_CONDITIONER_COMMAND_TOPIC, payload=msg.payload.decode())

        elif topic[-1] == "blind":
            downstream_client.publish(BLIND_COMMAND_TOPIC, payload=msg.payload.decode())

        elif topic[-1] == "balcony_light":
            downstream_client.publish(BALCONY_LIGHT_COMMAND_TOPIC, payload=msg.payload.decode())

        elif topic[-1] == "interior_light":
            downstream_client.publish(INTERIOR_LIGHT_COMMAND_TOPIC, payload=msg.payload.decode())


def on_upstream_publish(client, userdata, result):
    print("Data published to upstream.")


def connect_upstream_mqtt():
    c = mqtt.Client('Upstream-' + ROOM_ID)
    c.username_pw_set(username="dso_server", password="dso_password")
    c.on_connect = on_upstream_connect
    c.on_publish = on_upstream_publish
    c.on_message = on_upstream_message
    c.connect(UPSTREAM_MQTT_SERVER, UPSTREAM_MQTT_PORT, 60)
    return c


def upstream_worker():
    global room_number, TEMPERATURE_TOPIC, AIR_CONDITIONER_TOPIC, PRESENCE_TOPIC, upstream_client, AIR_CONDITIONER_COMMAND_TOPIC, BLIND_COMMAND_TOPIC, BALCONY_LIGHT_COMMAND_TOPIC, INTERIOR_LIGHT_COMMAND_TOPIC, BLIND_TOPIC, BALCONY_LIGHT_TOPIC, INTERIOR_LIGHT_TOPIC

    # Upstream MQTT used for communication with message router
    upstream_client = connect_upstream_mqtt()

    upstream_client.loop_forever()

    # On connect, we request a room number for this digital twin, so here we wait
    # to receive it, and then update our topics accordingly (so that we can publish to them
    # when we receive data from the raspberry pi)
    while room_number is None:
        print("Waiting for room number in thread", threading.current_thread().ident)
        time.sleep(1)

    TELEMETRY_TOPIC = "hotel/rooms/" + str(room_number) + "/telemetry/"
    TEMPERATURE_TOPIC = TELEMETRY_TOPIC + "temperature"
    AIR_CONDITIONER_TOPIC = TELEMETRY_TOPIC + "air_conditioner"
    PRESENCE_TOPIC = TELEMETRY_TOPIC + "presence"
    BLIND_TOPIC = TELEMETRY_TOPIC + "blind"
    BALCONY_LIGHT_TOPIC = TELEMETRY_TOPIC + "balcony_light"
    INTERIOR_LIGHT_TOPIC = TELEMETRY_TOPIC + "interior_light"


"""
END UPSTREAM
"""

"""
START DOWNSTREAM
"""


def on_downstream_connect(client, userdata, flags, rc):
    global room_number, upstream_client, AIR_CONDITIONER_COMMAND_TOPIC, BLIND_COMMAND_TOPIC, BALCONY_LIGHT_COMMAND_TOPIC, INTERIOR_LIGHT_COMMAND_TOPIC, DISCONNECT_TOPIC, CONNECTED_TOPIC
    print("Downstream: Digital twin connected with code ", rc)

    print("Downstream: Subscribing to physical telemetry channels.")
    physical_room_telemetry_channel = 'hotel/physical_rooms/' + str(room_number) + '/telemetry'
    presence_channel = physical_room_telemetry_channel + '/presence'
    temperature_channel = physical_room_telemetry_channel + '/temperature'
    air_conditioner_channel = physical_room_telemetry_channel + '/air_conditioner'
    blind_channel = physical_room_telemetry_channel + '/blind'
    balcony_light_channel = physical_room_telemetry_channel + '/balcony_light'
    interior_light_channel = physical_room_telemetry_channel + '/interior_light'

    print("Downstream: Subscribing to physical channels")
    client.subscribe(presence_channel)
    client.subscribe(temperature_channel)
    client.subscribe(air_conditioner_channel)
    client.subscribe(blind_channel)
    client.subscribe(balcony_light_channel)
    client.subscribe(interior_light_channel)

    print('Subscribing to hotel/rooms/' + str(room_number) + '/config')
    client.subscribe('hotel/rooms/' + str(room_number) + '/config')

    print("Subscribing to disconnect topic")
    DISCONNECT_TOPIC = "hotel/rooms/" + str(room_number) + "/disconnect"
    client.subscribe(DISCONNECT_TOPIC)

    CONNECTED_TOPIC = "hotel/rooms/" + str(room_number) + "/connect"

    AIR_CONDITIONER_COMMAND_TOPIC = "hotel/rooms/" + str(room_number) + "/command/air_conditioner"
    BLIND_COMMAND_TOPIC = "hotel/rooms/" + str(room_number) + "/command/blind"
    BALCONY_LIGHT_COMMAND_TOPIC = "hotel/rooms/" + str(room_number) + "/command/balcony_light"
    INTERIOR_LIGHT_COMMAND_TOPIC = "hotel/rooms/" + str(room_number) + "/command/interior_light"

    print("Upstream subscribing to command topics to be able to pass commands on...")
    upstream_client.subscribe(AIR_CONDITIONER_COMMAND_TOPIC)
    upstream_client.subscribe(BLIND_COMMAND_TOPIC)
    upstream_client.subscribe(BALCONY_LIGHT_COMMAND_TOPIC)
    upstream_client.subscribe(INTERIOR_LIGHT_COMMAND_TOPIC)


def on_downstream_message(client, userdata, msg):
    # check if value has changed and send to upstream if so
    global pi_is_connected, current_temperature, current_air, current_presence, room_number, PRESENCE_TOPIC, upstream_client, current_blind, current_balcony_light, current_interior_light

    print("Downstream message received at ", msg.topic, " with message ", msg.payload.decode())

    topic = msg.topic.split('/')

    # Raspberry pi publishes its own room number to config topic
    # We receive this and recognize that a raspberry pi is trying to form a connection
    # So we publish our namesake to the config for our room number, which the raspberry pi should be subscribed to
    # When the pi receives the message, it can be sure that it is connected to the corresponding digital twin.
    if topic[-1] == "config":
        config_response_topic = "hotel/rooms/" + str(room_number) + "/config/room"
        print('Sending namesake and requesting activation for', config_response_topic)

        client.publish(config_response_topic, payload=ROOM_ID, qos=0, retain=False)
        upstream_client.publish(CONNECTED_TOPIC, qos=0, retain=False)

        pi_is_connected = True

        retransmit_queued_commands()

    elif topic[-1] == "disconnect":
        print("Disconnect or last will received")
        upstream_client.publish(DISCONNECT_TOPIC, qos=0, retain=False)

        pi_is_connected = False

    elif topic[-1] == "temperature":

        new_temp = json.loads(msg.payload.decode())

        # Forward message to message router if value has changed
        if new_temp["temperature"]["active"] != current_temperature["temperature"]["active"] \
                or new_temp["temperature"]["temperature"] != current_temperature["temperature"]["temperature"]:
            print("Temperature change detected. Publishing ", new_temp, "to upstream at topic ", TEMPERATURE_TOPIC)
            current_temperature = new_temp.copy()
            upstream_client.publish(TEMPERATURE_TOPIC, payload=json.dumps(new_temp), qos=0, retain=False)

    elif topic[-1] == "air_conditioner":

        new_air = json.loads(msg.payload.decode())

        # Forward message to message router if value has changed
        if new_air["air_conditioner"]["active"] != current_air["air_conditioner"]["active"] \
                or new_air["air_conditioner"]["level"] != current_air["air_conditioner"]["level"] \
                or new_air["air_conditioner"]["mode"] != current_air["air_conditioner"]["mode"]:
            print("Air conditioner change detected. Publishing ", new_air,
                  "to upstream at topic ", AIR_CONDITIONER_TOPIC)
            current_air = new_air.copy()
            upstream_client.publish(AIR_CONDITIONER_TOPIC, payload=json.dumps(new_air), qos=0, retain=False)

    elif topic[-1] == "presence":

        new_presence = json.loads(msg.payload.decode('utf-8'))

        # Forward message to message router if value has changed
        if new_presence["presence"]["active"] != current_presence["presence"]["active"] \
                or new_presence["presence"]["detected"] != current_presence["presence"]["detected"]:
            print("Presence change detected. Publishing ", new_presence, "to upstream at topic ", PRESENCE_TOPIC)
            current_presence = new_presence.copy()
            upstream_client.publish(PRESENCE_TOPIC, payload=json.dumps(new_presence), qos=0, retain=False)

    elif topic[-1] == "blind":

        new_blind = json.loads(msg.payload.decode())

        if new_blind["blind"]["active"] != current_blind["blind"]["active"] \
                or new_blind["blind"]["level"] != current_blind["blind"]["level"]:
            print("Blind change detected. Publishing")
            current_blind = new_blind.copy()
            upstream_client.publish(BLIND_TOPIC, payload=json.dumps(new_blind), qos=0, retain=False)

    elif topic[-1] == "balcony_light":

        new_balcony_light = json.loads(msg.payload.decode())

        if new_balcony_light["balcony_light"]["active"] != current_balcony_light["balcony_light"]["active"] \
                or new_balcony_light["balcony_light"]["level"] != current_balcony_light["balcony_light"]["level"] \
                or new_balcony_light["balcony_light"]["on"] != current_balcony_light["balcony_light"]["on"]:
            print("Balcony light change detected. Publishing.")
            current_balcony_light = new_balcony_light.copy()
            upstream_client.publish(BALCONY_LIGHT_TOPIC, payload=json.dumps(new_balcony_light), qos=0, retain=False)

    elif topic[-1] == "interior_light":

        new_interior_light = json.loads(msg.payload.decode())

        if new_interior_light["interior_light"]["active"] != current_interior_light["interior_light"]["active"] \
                or new_interior_light["interior_light"]["level"] != current_interior_light["interior_light"]["level"] \
                or new_interior_light["interior_light"]["on"] != current_interior_light["interior_light"]["on"]:
            print("Interior light change detected. Publishing.")
            current_interior_light = new_interior_light.copy()
            upstream_client.publish(INTERIOR_LIGHT_TOPIC, payload=json.dumps(new_interior_light), qos=0, retain=False)


def on_downstream_publish(client, userdata, result):
    print("Data published to downstream")


def connect_downstream_mqtt():
    c = mqtt.Client('Downstream-' + ROOM_ID)
    c.username_pw_set(username="dso_server", password="dso_password")
    c.on_connect = on_downstream_connect
    c.on_publish = on_downstream_publish
    c.on_message = on_downstream_message
    c.connect(DOWNSTREAM_MQTT_SERVER, DOWNSTREAM_MQTT_PORT, 60)
    return c


def downstream_worker():
    global room_number, TEMPERATURE_TOPIC, AIR_CONDITIONER_TOPIC, PRESENCE_TOPIC, downstream_client, AIR_CONDITIONER_COMMAND_TOPIC, BLIND_COMMAND_TOPIC, INTERIOR_LIGHT_COMMAND_TOPIC, BALCONY_LIGHT_COMMAND_TOPIC, BLIND_TOPIC, INTERIOR_LIGHT_TOPIC, BALCONY_LIGHT_TOPIC

    # Wait for room number, which is being fetched by the upstream_worker
    # We need this room number so that we may make an agreement with our raspberry pi (which has a static
    # room number) that we are in fact the correct digital twin for them. We also use this room number to
    # subscribe and publish to various places.
    while room_number is None:
        print("Waiting for room number in thread", threading.current_thread().ident)
        time.sleep(1)

    TELEMETRY_TOPIC = "hotel/rooms/" + str(room_number) + "/telemetry/"

    TEMPERATURE_TOPIC = TELEMETRY_TOPIC + "temperature"
    AIR_CONDITIONER_TOPIC = TELEMETRY_TOPIC + "air_conditioner"
    PRESENCE_TOPIC = TELEMETRY_TOPIC + "presence"
    BLIND_TOPIC = TELEMETRY_TOPIC + "blind"
    BALCONY_LIGHT_TOPIC = TELEMETRY_TOPIC + "balcony_light"
    INTERIOR_LIGHT_TOPIC = TELEMETRY_TOPIC + "interior_light"

    try:
        downstream_client = connect_downstream_mqtt()
        downstream_client.loop_forever()
    except:
        print("Device has entered an error state.")


"""
END DOWNSTREAM
"""

if __name__ == "__main__":
    upstream_thread = threading.Thread(target=upstream_worker)
    downstream_thread = threading.Thread(target=downstream_worker)

    upstream_thread.setDaemon(True)
    downstream_thread.setDaemon(True)

    upstream_thread.start()
    downstream_thread.start()

    upstream_thread.join()
    downstream_thread.join()
