import RPi.GPIO as GPIO
import Adafruit_DHT
import time
import threading
from threading import Semaphore
import signal
import sys
import paho.mqtt.client as mqtt
import json

humidity = 0
temp = 0
mutex = Semaphore(3)

BUTTON_PIN = 21

PERSON = False
setTemp = 20
room = 'Room1'
ac = False

MQTT_SERVER = '35.207.85.144'
MQTT_PORT = 1884

# TOPICS
tempTopic = 'hotel/physical_rooms/' + room + '/telemetry/temperature'
presenceTopic = 'hotel/physical_rooms/' + room + '/telemetry/presence'
acTopic = 'hotel/physical_rooms/' + room + '/telemetry/air_conditioner'
CONFIG_TOPIC = 'hotel/rooms/'+room+'/config'
RESPONSE_TOPIC = 'hotel/rooms/'+room+'/config/room'
is_connected = False

def signal_handler(sig, frame):
    GPIO.cleanup()

def on_connect(client, user_data, flags, rc):
    client.subscribe(RESPONSE_TOPIC)
    print('connected to mqtt')

def on_message(client, user_data, msg):
    global is_connected #only message from digital twin is config rsp
    is_connected = True

def on_publish(client, user_data, msg):
    print('published to digital twin')

def connect_mqtt(client):
    global MQTT_PORT, MQTT_SERVER, is_connected
    client.username_pw_set(username="dso_server", password="dso_password")
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.on_message = on_message
    print(MQTT_PORT, MQTT_SERVER)
    client.connect(MQTT_SERVER, MQTT_PORT, 60)
    client.loop_start()
    while not is_connected:
        client.publish(CONFIG_TOPIC, payload=room, qos=0, retain = False)
        print('sent id', room, 'to topic', CONFIG_TOPIC)
        time.sleep(5)
    client.loop_stop()

def button_released_callback(channel):
    global PERSON
    mutex.acquire()
    if PERSON:
        print('people leaving')
        PERSON = not PERSON
    else:
        print('people return')
        PERSON = not PERSON
    mutex.release()


def setup_button():
    GPIO.setmode(GPIO.BCM)

    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    GPIO.add_event_detect(BUTTON_PIN, GPIO.RISING,
                          callback=button_released_callback, bouncetime=200)


def setup_dht():
    global temp, humidity, mutex
    mutex.acquire()
    humidity, temp, = Adafruit_DHT.read(Adafruit_DHT.DHT11, 4)
    mutex.release()


def signal_handler(sig, frame):
    destroy()



def setup_pi():
    # connect to mosquito
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    setup_button()
    setup_dht()
    signal.signal(signal.SIGINT, signal_handler)



def tempSensor():
    global humidity, temp, mutex, PERSON
    while True:
        mutex.acquire()
        humidity, temp, = Adafruit_DHT.read(Adafruit_DHT.DHT11, 4)
        if humidity is not None and temp is not None:
            client.publish(tempTopic, payload=json.dumps({
                "temperature": {
                    "active": True,
                    "temperature": temp
                }
            }), qos=0, retain=False)

        else:
            #print("sensory failure. check wiring.")
            client.publish(tempTopic, payload=json.dumps({
                "temperature": {
                    "active": False,
                    "temperature": temp
                }
            }), qos=0, retain=False)
        time.sleep(3)
        mutex.release()


def presenceSensor():
    global PERSON
    while True:
        mutex.acquire()
        client.publish(presenceTopic, payload=json.dumps({
            "presence": {
                "active": True,
                "detected": PERSON
            }
        }), qos=0, retain=False)
        mutex.release()
        time.sleep(3)


def acSensor():
    global humidity, temp, ac, mutex, PERSON
    while True:
        mutex.acquire()
        #if PERSON:
        if temp > 22:
            ac = True
        else:
            ac = False
        client.publish(acTopic, payload=json.dumps({
            "air_conditioner": {
                "mode": 1,
                "active": ac,
                "level": temp
            }
        }), qos=0, retain=False)
        mutex.release()
        time.sleep(3)


def destroy():
    global mutex
    mutex.acquire()
    GPIO.cleanup()
    mutex.release()
    sys.exit(0)


if __name__ == '__main__':
    client = mqtt.Client()
    connect_mqtt(client)
    client.loop_forever()
    setup_pi()

    try:
        t1 = threading.Thread(target=presenceSensor)
        t2 = threading.Thread(target=tempSensor)
        t3 = threading.Thread(target=acSensor)

        t1.setDaemon(True)
        t2.setDaemon(True)
        t3.setDaemon(True)

        t1.start()
        t2.start()
        t3.start()

        t1.join()
        t2.join()
        t3.join()

    except KeyboardInterrupt:
        destroy()
