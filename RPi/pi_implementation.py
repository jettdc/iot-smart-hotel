import random

from abstract_rpi import AbstractRoomDevice
from threading import Semaphore
import RPi.GPIO as GPIO
import signal
import time
import sys
import math


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

    def button_release_callback(self, channel):
        self.sensor_lock.acquire()
        self.sensors["presence"]["detected"] = not self.sensors["presence"]["detected"]
        self.sensor_lock.release()

    def setup_motor(self):
        GPIO.setup(self.MOTOR_INPUT_PIN, GPIO.OUT)
        GPIO.setup(self.MOTOR_INPUT_X_PIN, GPIO.OUT)
        GPIO.setup(self.MOTOR_INPUT_Y_PIN, GPIO.OUT)
        GPIO.output(self.MOTOR_INPUT_PIN, GPIO.LOW)

    def setup_blind(self):
        GPIO.setup(self.SERVO_INPUT_PIN, GPIO.OUT)
        self.blind_pwm = GPIO.PWM(self.SERVO_INPUT_PIN, 100)
        self.blind_pwm.start(7.5)
        self.blind_pwm.ChangeDutyCycle(0)


    def setup_button(self):
        GPIO.setup(self.BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.add_event_detect(self.BUTTON_PIN, GPIO.RISING,
                              callback=lambda channel: self.button_release_callback(channel), bouncetime=100)

    def setup_interior_led(self):
        GPIO.setup(self.RED_LED_PIN, GPIO.OUT)
        self.int_pwm = GPIO.PWM(self.RED_LED_PIN, 100)
        self.int_pwm.start(0)

    def setup_balcony_led(self):
        GPIO.setup(self.GREEN_LED_PIN, GPIO.OUT)
        self.bal_pwm = GPIO.PWM(self.GREEN_LED_PIN, 100)
        self.bal_pwm.start(0)

    """
    RPI LIFECYCLE METHODS
    """

    def device_setup(self):
        GPIO.setwarnings(True)
        GPIO.cleanup([
            self.BUTTON_PIN,
            self.RED_LED_PIN,
            self.GREEN_LED_PIN,
            self.MOTOR_INPUT_PIN,
            self.MOTOR_INPUT_X_PIN,
            self.MOTOR_INPUT_Y_PIN,
            self.SERVO_INPUT_PIN,
            self.DHT_INPUT_PIN, ])
        GPIO.setmode(GPIO.BCM)

        self.setup_blind()
        self.setup_motor()
        self.setup_button()
        self.setup_balcony_led()
        self.setup_interior_led()

        signal.signal(signal.SIGINT, self.destroy)

    def destroy(self, signum, frame):
        GPIO.cleanup([
            self.BUTTON_PIN,
            self.RED_LED_PIN,
            self.GREEN_LED_PIN,
            self.MOTOR_INPUT_PIN,
            self.MOTOR_INPUT_X_PIN,
            self.MOTOR_INPUT_Y_PIN,
            self.SERVO_INPUT_PIN,
            self.DHT_INPUT_PIN, ])
        sys.exit(0)

    """
    SENSOR LISTENERS/PUBLISHERS
    """

    def presence_listener(self):

        self.sensor_lock.acquire()
        self.sensors["presence"]["active"] = True
        self.sensor_lock.release()

        # Initiate the button on the RPi

        while True:
            self.publish_presence()
            time.sleep(2)

    def temperature_listener(self):
        self.sensor_lock.acquire()
        self.sensors["air_conditioner"]["active"] = True
        self.sensor_lock.release()

        while True:
            # Simulate temperature changing
            self.sensor_lock.acquire()
            self.sensors["temperature"] = {
                "active": True,
                "temperature": random.randint(0, 40)
            }
            self.sensor_lock.release()

            self.publish_temperature()

            time.sleep(10)

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

        while True:
            # Blind should only be changed by the upstream, so do nothing
            self.publish_blind()
            time.sleep(2)

    def balcony_light_listener(self):

        self.sensor_lock.acquire()
        self.sensors["balcony_light"]["active"] = True
        self.sensor_lock.release()

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
            GPIO.output(self.MOTOR_INPUT_PIN, GPIO.LOW)
            GPIO.output(self.MOTOR_INPUT_Y_PIN, GPIO.LOW)
            GPIO.output(self.MOTOR_INPUT_X_PIN, GPIO.LOW)
        elif requested_mode == 1:  # WARM
            self.sensors["air_conditioner"]["level"] = 50
            print('back')
            GPIO.output(self.MOTOR_INPUT_PIN, GPIO.HIGH)
            GPIO.output(self.MOTOR_INPUT_Y_PIN, GPIO.HIGH)
            GPIO.output(self.MOTOR_INPUT_X_PIN, GPIO.LOW)
        else:  # COLD
            self.sensors["air_conditioner"]["level"] = 100
            GPIO.output(self.MOTOR_INPUT_PIN, GPIO.HIGH)
            GPIO.output(self.MOTOR_INPUT_Y_PIN, GPIO.LOW)
            GPIO.output(self.MOTOR_INPUT_X_PIN, GPIO.HIGH)

        self.sensor_lock.release()

        #pwm = GPIO.PWM(self.MOTOR_INPUT_PIN, 100)
        #pwm.start(self.sensors["air_conditioner"]["level"])

    def angleCalc(self, angle):
        A = 0
        B = 180
        C = 5
        D = 10
        result = C*(1-((angle-A)/(B-A)))+D*((angle-A)/(B-A))
        self.safe_print('angle calc:', result)
        return math.floor(result)

    def handle_blind_command(self, requested_blind_level):
        self.safe_print("COMMAND RECEIVED: Setting blind to", requested_blind_level)

        self.sensor_lock.acquire()
        self.sensors["blind"]["level"] = requested_blind_level
        self.sensor_lock.release()

        # self.blind_pwm.start(7.5)

        if requested_blind_level <= 0:
            self.blind_pwm.ChangeDutyCycle(5)
        elif requested_blind_level >= 180:
            self.blind_pwm.ChangeDutyCycle(10)
        else:
            self.blind_pwm.ChangeDutyCycle(self.angleCalc(requested_blind_level))
        time.sleep(1)
        self.blind_pwm.ChangeDutyCycle(0)
        #self.blind_pwm.stop()

    def handle_balcony_light_command(self, should_be_on, level):
        print("COMMAND RECEIVED: Turning balcony light", should_be_on, "and to level", level)

        self.sensor_lock.acquire()
        self.sensors["balcony_light"]["on"] = should_be_on
        self.sensor_lock.release()

        if should_be_on and 0 < level <= 100:
            self.bal_pwm.ChangeDutyCycle(0)
            self.sensor_lock.acquire()
            self.sensors["balcony_light"]["level"] = float(level)
            self.sensor_lock.release()

            for x in range(0, level):
                self.bal_pwm.ChangeDutyCycle(x + 1)
                time.sleep(0.01)

        elif should_be_on and level > 100:
            self.bal_pwm.ChangeDutyCycle(0)
            self.sensor_lock.acquire()
            self.sensors["balcony_light"]["level"] = 100.0
            self.sensor_lock.release()

            for x in range(0, 100):
                self.bal_pwm.ChangeDutyCycle(x + 1)
                time.sleep(0.01)

        else:
            self.bal_pwm.ChangeDutyCycle(0.0)
            self.sensor_lock.acquire()

            self.sensors["balcony_light"]["level"] = 0.0

            self.sensor_lock.release()


    def handle_interior_light_command(self, should_be_on, level):
        print("COMMAND RECEIVED: Turning interior light", should_be_on, "and to level", level)

        self.sensor_lock.acquire()
        self.sensors["interior_light"]["on"] = should_be_on
        self.sensor_lock.release()

        if should_be_on and 0 < level <= 100:
            self.int_pwm.ChangeDutyCycle(0)
            self.sensor_lock.acquire()
            self.sensors["interior_light"]["level"] = float(level)
            self.sensor_lock.release()

            for x in range(0,level):
                self.int_pwm.ChangeDutyCycle(x+1)
                time.sleep(0.01)

        elif should_be_on and level > 100:
            self.int_pwm.ChangeDutyCycle(0)
            self.sensor_lock.acquire()
            self.sensors["interior_light"]["level"] = 100.0
            self.sensor_lock.release()

            for x in range(0,100):
                self.int_pwm.ChangeDutyCycle(x+1)
                time.sleep(0.01)

        else:
            self.int_pwm.ChangeDutyCycle(0.0)
            self.sensor_lock.acquire()

            self.sensors["interior_light"]["level"] = 0.0

            self.sensor_lock.release()


if __name__ == "__main__":
    simulator = RoomDevice("Room3")
    simulator.start()
