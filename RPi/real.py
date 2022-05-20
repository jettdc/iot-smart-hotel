from abstract_rpi import AbstractRoomDevice
from threading import Semaphore
import RPi.GPIO as GPIO
import Adafruit_DHT
import signal
import time
import sys


class RoomDevice(AbstractRoomDevice):
    """
    PIN CONSTANTS
    """
    BUTTON_PIN = 21
    RED_LED_PIN = 18
    GREEN_LED_PIN = 12
    MOTOR_INPUT_PIN = 25
    MOTOR_INPUT_X_PIN = 24
    MOTOR_INPUT_Y_PIN = 23
    SERVO_INPUT_PIN = 13
    DHT_INPUT_PIN = 4

    """
    SENSOR SETUP
    """

    def setup_motor(self):
        GPIO.setup(self.MOTOR_INPUT_PIN, GPIO.OUT)
        GPIO.setup(self.MOTOR_INPUT_X_PIN, GPIO.OUT)
        GPIO.setup(self.MOTOR_INPUT_Y_PIN, GPIO.OUT)

    def setup_servo(self):
        GPIO.setup(self.SERVO_INPUT_PIN, GPIO.OUT)

    def setup_button(self):
        GPIO.setmode(GPIO.BCM)  # GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def setup_interior_led(self):
        GPIO.setup(self.RED_LED_PIN, GPIO.OUT)
        pwm = GPIO.PWM(12, 100)

    def setup_balcony_led(self):
        GPIO.setup(self.GREEN_LED_PIN, GPIO.OUT)

    """
    RPI LIFECYCLE METHODS
    """

    def device_setup(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        signal.signal(signal.SIGINT, self.destroy)

    def destroy(self):
        GPIO.cleanup()
        sys.exit(0)

    """
    SENSOR LISTENERS/PUBLISHERS
    """

    def presence_listener(self):

        self.sensor_lock.acquire()
        self.sensors["presence"]["active"] = True
        self.sensor_lock.release()

        # Initiate the button on the RPi
        self.setup_button()

        while True:

            # If button is pressed
            if GPIO.input(self.BUTTON_PIN):
                self.safe_print("Button Pressed / Presence detected")

                self.sensor_lock.acquire()
                self.sensors["presence"]["detected"] = not self.sensors["presence"]["detected"]
                self.sensor_lock.release()

                self.publish_presence()

            time.sleep(2)

    def temperature_listener(self):

        self.sensor_lock.acquire()
        self.sensors["temperature"]["active"] = True
        self.sensor_lock.release()

        while True:
            # Read and update temperature
            self.sensor_lock.acquire()
            self.sensors["temperature"]["temperature"] = Adafruit_DHT.read(Adafruit_DHT.DHT11, self.DHT_INPUT_PIN)[1]
            self.sensor_lock.release()

            self.publish_temperature()

            time.sleep(3)

    def air_conditioner_listener(self):

        self.sensor_lock.acquire()
        self.sensors["air_conditioner"]["active"] = True
        self.sensor_lock.release()

        while True:
            # We are not updating the air conditioner here since its state changes based on user commands
            self.publish_air_conditioner()
            time.sleep(2)

    def blind_listener(self):

        self.sensor_lock.acquire()
        self.sensors["blind"]["active"] = True
        self.sensor_lock.release()

        self.setup_servo()

        while True:
            # Blind should only be changed by the upstream, so do nothing
            self.publish_blind()
            time.sleep(2)

    def balcony_light_listener(self):

        self.sensor_lock.acquire()
        self.sensors["balcony_light"]["active"] = True
        self.sensor_lock.release()

        self.setup_balcony_led()

        while True:
            # Balcony light only changed by commands
            self.publish_balcony_light()
            time.sleep(2)

    def interior_light_listener(self):

        self.sensor_lock.acquire()
        self.sensors["interior_light"]["active"] = True
        self.sensor_lock.release()

        while True:
            # Interior light only changed by command
            self.publish_interior_light()
            time.sleep(2)

    """
    USER COMMAND HANDLERS
    """

    def handle_air_conditioner_command(self, requested_mode):
        """
        We've decided to indicate AC mode by adjusting the DC/Fan level according to mode

        Off is, of course, 0 speed
        WARM is half speed
        COLD is full speed
        """

        self.safe_print("COMMAND RECEIVED: Setting AC mode to", requested_mode)

        self.sensor_lock.acquire()

        self.sensors["air_conditioner"]["mode"] = requested_mode
        if requested_mode == 0:  # OFF
            self.sensors["air_conditioner"]["level"] = 0
        if requested_mode == 1:  # WARM
            self.sensors["air_conditioner"]["level"] = 50
        else:  # COLD
            self.sensors["air_conditioner"]["level"] = 100

        self.sensor_lock.release()

        pwm = GPIO.PWM(self.MOTOR_INPUT_PIN, 100)
        pwm.start(self.sensors["air_conditioner"]["level"])

    def handle_blind_command(self, requested_blind_level):
        self.safe_print("COMMAND RECEIVED: Setting blind to", requested_blind_level)

        self.sensor_lock.acquire()
        self.sensors["blind"]["level"] = requested_blind_level
        self.sensor_lock.release()

        pwm = GPIO.PWM(self.SERVO_INPUT_PIN, 100)
        if requested_blind_level > 0:
            pwm.start(requested_blind_level)
        elif requested_blind_level < 0:
            pwm.start(0)
        else:
            pwm.start(180)

    def handle_balcony_light_command(self, should_be_on, level):
        print("COMMAND RECEIVED: Turning balcony light", should_be_on, "and to level", level)

        self.sensor_lock.acquire()
        self.sensors["balcony_light"]["on"] = should_be_on
        self.sensors["balcony_light"]["level"] = level
        self.sensor_lock.release()

        pwm = GPIO.PWM(self.GREEN_LED_PIN, 100)
        if should_be_on and 0 < level <= 100:
            pwm.start(level)
        elif level > 100:
            pwm.start(100)
        else:
            pwm.start(0)

    def handle_interior_light_command(self, should_be_on, level):
        print("COMMAND RECEIVED: Turning interior light", should_be_on, "and to level", level)

        self.sensor_lock.acquire()
        self.sensors["interior_light"]["on"] = should_be_on
        self.sensors["interior_light"]["level"] = level
        self.sensor_lock.release()

        pwm = GPIO.PWM(self.RED_LED_PIN, 100)
        if should_be_on and 0 < level <= 180:
            pwm.start(level)
        elif level > 100:
            pwm.start(100)
        else:
            pwm.start(0)


if __name__ == "__main__":
    simulator = RoomDevice("Room3")
    simulator.start()
