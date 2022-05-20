import paho.mqtt.client as mqtt
import threading
import datetime
import time
import json
import abc


class AbstractRoomDevice:
    publish_lock = threading.Lock()
    sensor_lock = threading.Lock()
    print_lock = threading.Lock()

    def __init__(self, room_name, verbose=True):
        self.verbose = verbose

        self.client = None
        self.room_name = room_name

        self.config_topic = 'hotel/rooms/' + room_name + '/config'
        self.temperature_topic = 'hotel/physical_rooms/' + room_name + '/telemetry/temperature'
        self.presence_topic = 'hotel/physical_rooms/' + room_name + '/telemetry/presence'
        self.air_conditioner_topic = 'hotel/physical_rooms/' + room_name + '/telemetry/air_conditioner'
        self.blind_topic = 'hotel/physical_rooms/' + room_name + '/telemetry/blind'
        self.balcony_light_topic = 'hotel/physical_rooms/' + room_name + '/telemetry/balcony_light'
        self.interior_light_topic = 'hotel/physical_rooms/' + room_name + '/telemetry/interior_light'

        self.disconnect_topic = "hotel/rooms/" + room_name + "/disconnect"

        self.sensors = {
            # Temperature sensor
            # Set level of air conditioner, but NOT mode
            "temperature": {
                "active": False,
                "temperature": 0
            },
            # Button
            # Interaction from pi side only
            "presence": {
                "active": False,
                "detected": False
            },
            # RGB  LED
            # DC MOTOR
            # Mode will be based on upstream command only, NOT temp
            # Command
            # { "mode": 0 | 1 | 2 }
            "air_conditioner": {
                "active": False,
                "mode": 0,  # off=0, warm=1, cold=2
                "level": 0,
            },
            # Servomotor
            # Can receive orders
            # { "level": int }
            "blind": {
                "active": False,
                "level": 0  # 0 = open, 180 = closed
            },
            # Blue LED
            # Can receive orders, moves gradually
            # { "on": bool, "level": int }
            "balcony_light": {
                "active": False,
                "on": False,
                "level": 0  # 0 = min, 100 = max
            },
            # White LED
            # Same as above essentially
            "interior_light": {
                "active": False,
                "on": False,
                "level": 0
            }
        }

        self.is_connected = False


    def start(self):
        self.mqtt_init()
        self.device_start()

    def device_start(self):
        self.device_setup()
        telemetry_listener = self.get_telemetry_listeners()
        try:
            threads = []
            for listener in telemetry_listener:
                thread = threading.Thread(target=listener)
                thread.setDaemon(True)
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

        except KeyboardInterrupt:
            self.shutdown()

    def get_telemetry_listeners(self):
        return [
            self.temperature_listener,
            self.air_conditioner_listener,
            self.blind_listener,
            self.balcony_light_listener,
            self.interior_light_listener,
            self.presence_listener,
        ]

    def mqtt_init(self):
        self.connect_mqtt()

    def connect_mqtt(self):
        c = mqtt.Client(self.room_name + "Client")
        c.username_pw_set(username="dso_server", password="dso_password")
        c.on_connect = self.get_on_connect_function()
        c.on_message = self.get_on_message_function()
        c.on_disconnect = self.get_on_disconnect_function()

        c.will_set(self.disconnect_topic, qos=0, retain=False)

        c.connect('35.207.111.217', 1884, 60)

        c.loop_start()
        while not self.is_connected:
            c.publish(self.config_topic, payload=self.room_name, qos=0, retain=False)
            if self.verbose:
                self.safe_print('Sent id', self.room_name, 'to topic', self.config_topic)
            time.sleep(1)
        self.client = c

    def get_on_connect_function(self):
        def on_connect(client, userdata, flags, rc):
            if self.verbose:
                self.safe_print("Connected on subscribe with code ", rc)
                self.safe_print("Subscribing to all.")

            client.subscribe('#')

            self.setup_command_channels(client)

        return on_connect

    def get_on_disconnect_function(self):
        def on_disconnect(client, userdata, rc):
            self.safe_print("Disconnecting")
            self.client.publish(self.disconnect_topic, qos=0, retain=False)

        return on_disconnect

    def get_on_message_function(self):
        def on_message(client, userdata, msg):
            topic = msg.topic.split('/')
            if self.verbose:
                self.safe_print("Message received at ", msg.topic, " with message ", msg.payload.decode())

            if self.room_name not in topic:
                return

            if "config" in topic:
                if self.verbose:
                    self.safe_print("Config message received at", msg.topic, "with message", msg.payload.decode())
                self.is_connected = True

            elif "command" in topic:
                if self.verbose:
                    self.safe_print("Command message received at", msg.topic, "with message", msg.payload.decode())

                command_target = topic[-1]
                self.safe_print(topic)
                if command_target == "air_conditioner":
                    mode = json.loads(msg.payload)["mode"]  # off, warm, cold
                    self.handle_air_conditioner_command(mode)

                elif command_target == "blind":
                    level = json.loads(msg.payload)["level"]  # int
                    self.handle_blind_command(level)

                elif command_target == "balcony_light":
                    on = json.loads(msg.payload)["on"]  # bool
                    level = json.loads(msg.payload)["level"]  # int
                    self.handle_balcony_light_command(on, level)

                elif command_target == "interior_light":
                    on = json.loads(msg.payload)["on"]  # bool
                    level = json.loads(msg.payload)["level"]  # int
                    self.handle_interior_light_command(on, level)

        return on_message

    def setup_command_channels(self, client):
        if self.verbose:
            self.safe_print("Subscribing to command topics...")

        AIR_CONDITIONER_COMMAND_TOPIC = "hotel/rooms/" + self.room_name + "/command/air_conditioner"
        BLIND_COMMAND_TOPIC = "hotel/rooms/" + self.room_name + "/command/blind"
        BALCONY_LIGHT_COMMAND_TOPIC = "hotel/rooms/" + self.room_name + "/command/balcony_light"
        INTERIOR_LIGHT_COMMAND_TOPIC = "hotel/rooms/" + self.room_name + "/command/interior_light"

        self.publish_lock.acquire()
        client.subscribe(AIR_CONDITIONER_COMMAND_TOPIC)
        client.subscribe(BLIND_COMMAND_TOPIC)
        client.subscribe(BALCONY_LIGHT_COMMAND_TOPIC)
        client.subscribe(INTERIOR_LIGHT_COMMAND_TOPIC)
        self.publish_lock.release()

    """
    Publishers for each telemetry type

    """

    def publish_presence(self):
        self.publish_telemetry("presence", self.presence_topic)

    def publish_temperature(self):
        self.publish_telemetry("temperature", self.temperature_topic)

    def publish_air_conditioner(self):
        self.publish_telemetry("air_conditioner", self.air_conditioner_topic)

    def publish_blind(self):
        self.publish_telemetry("blind", self.blind_topic)

    def publish_balcony_light(self):
        self.publish_telemetry("balcony_light", self.balcony_light_topic)

    def publish_interior_light(self):
        self.publish_telemetry("interior_light", self.interior_light_topic)

    def publish_telemetry(self, name, topic):
        self.safe_print("Publishing telemetry:", name, "to", topic, self.sensors[name])

        data = {name: self.sensors[name], "timestamp": str(datetime.datetime.now())}

        self.publish_lock.acquire()
        self.client.publish(topic,
                            payload=json.dumps(data),
                            qos=1, retain=False)

        self.publish_lock.release()


    """
    Pi Lifecycle Methods
    """

    def shutdown(self):
        self.client.disconnect()
        self.destroy()

    @abc.abstractmethod
    def device_setup(self):
        pass

    @abc.abstractmethod
    def destroy(self, signum, frame):
        pass

    """
    Listeners are responsible for listening to their components and 
    publishing their values, plus any side effects
    """

    @abc.abstractmethod
    def presence_listener(self):
        pass

    @abc.abstractmethod
    def temperature_listener(self):
        pass

    @abc.abstractmethod
    def air_conditioner_listener(self):
        pass

    @abc.abstractmethod
    def blind_listener(self):
        pass

    @abc.abstractmethod
    def balcony_light_listener(self):
        pass

    @abc.abstractmethod
    def interior_light_listener(self):
        pass

    """
    Command handlers are responsible for updating state of upstream 
    controllable components
    """

    @abc.abstractmethod
    def handle_air_conditioner_command(self, requested_mode):
        pass

    @abc.abstractmethod
    def handle_blind_command(self, requested_blind_level):
        pass

    @abc.abstractmethod
    def handle_balcony_light_command(self, should_be_on, level):
        pass

    @abc.abstractmethod
    def handle_interior_light_command(self, should_be_on, level):
        pass

    def safe_print(self, *a, **b):
        if self.verbose:
            with self.print_lock:
                print(self.room_name, ":", *a, **b)
