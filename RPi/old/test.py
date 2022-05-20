import random

import paho.mqtt.client as mqtt
import time
import threading

import json

is_connected = False
CONFIG_TOPIC = 'hotel/rooms/Room3/config'
client = None


def on_connect(client, userdata, flags, rc):
    print("Connected on subscribe with code ", rc)

    client.subscribe('#')

    print("Subscribed to all.")


def on_message(client, userdata, msg):
    global current_temperature, current_air, current_blind, index_room, is_connected

    print("Message received at ", msg.topic, " with message ", msg.payload.decode())

    topic = (msg.topic).split('/')
    if "config" in topic:
        is_connected = True
    elif "command" in topic:
        if topic[-1] == "air-conditioner":
            print("Received a command for the air conditioner.")
            payload = json.loads(msg.payload)
            print("If this were the actual raspberry pi, it would now set the mode to ", payload["mode"])



def connect_mqtt():
    global is_connected
    c = mqtt.Client("Tester")
    c.username_pw_set(username="dso_server", password="dso_password")
    c.on_connect = on_connect
    c.on_message = on_message
    c.connect('35.207.111.217', 1884, 60)
    c.loop_start()
    while is_connected == False:
        c.publish(CONFIG_TOPIC, payload='Room3', qos=0, retain=False)
        print('sent id Room3', 'to topic', CONFIG_TOPIC)
        time.sleep(1)
    c.loop_stop()

    return c


def random_fire():
    while True:
        print("Publishing presence")
        client.publish('hotel/physical_rooms/Room3/telemetry/presence',
                       payload=json.dumps({
                           "presence": {
                               "active": True,
                               "detected": True if random.randint(0, 1) else False
                           }
                       }), qos=0, retain=False)
        time.sleep(random.randint(1, 5))


def random_fire2():
    while True:
        print("Publishing air")
        client.publish('hotel/physical_rooms/Room3/telemetry/air_conditioner',
                       payload=json.dumps({
                           "air_conditioner": {
                               "active": True,
                               "level": True if random.randint(0, 1) else False
                           }
                       }), qos=0, retain=False)
        time.sleep(random.randint(1, 5))


def random_fire3():
    while True:
        print("Publishing temp")
        client.publish('hotel/physical_rooms/Room3/telemetry/temperature',
                       payload=json.dumps({
                           "temperature": {
                               "active": True,
                               "temperature": True if random.randint(0, 1) else False
                           }
                       }), qos=0, retain=False)
        time.sleep(random.randint(1, 5))


if __name__ == "__main__":
    client = connect_mqtt()
    client.loop_forever()

    t1 = threading.Thread(target=random_fire)
    t2 = threading.Thread(target=random_fire2)
    t3 = threading.Thread(target=random_fire3)

    t1.setDaemon(True)
    t2.setDaemon(True)
    t3.setDaemon(True)

    t1.start()
    t2.start()
    t3.start()

    t1.join()
    t2.join()
    t3.join()
