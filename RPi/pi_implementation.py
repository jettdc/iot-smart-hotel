from math_helpers import scale_angle_to_pwm_value
from abstract_rpi import AbstractRoomDevice
from threading import Semaphore
import RPi.GPIO as GPIO
import signal
import random
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

    def button_release_callback(self, channel):
        self.sensor_lock.acquire()
        self.sensors["presence"]["detected"] = not self.sensors["presence"]["detected"]
        self.sensor_lock.release()

    def setup_interior_led(self):
        GPIO.setup(self.RED_LED_PIN, GPIO.OUT)
        self.int_pwm = GPIO.PWM(self.RED_LED_PIN, 100)
        self.int_pwm.start(0)

    def setup_balcony_led(self):
        GPIO.setup(self.GREEN_LED_PIN, GPIO.OUT)
        self.bal_pwm = GPIO.PWM(self.GREEN_LED_PIN, 100)
        self.bal_pwm.start(0)

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

        while True:
            self.publish_presence()
            time.sleep(2)

    def temperature_listener(self):
        self.sensor_lock.acquire()
        self.sensors["air_conditioner"]["active"] = True
        self.sensor_lock.release()

        while True:
            # Our temperature sensor was fried, so we are simulating readings.
            self.sensor_lock.acquire()
            self.sensors["temperature"]["temperature"] = random.randint(0, 40)
            self.sensor_lock.release()

            self.publish_temperature()

            time.sleep(2)

    def air_conditioner_listener(self):
        self.sensor_lock.acquire()
        self.sensors["air_conditioner"]["active"] = True
        self.sensor_lock.release()

        while True:
            # Air conditioner state only updated based on commands
            self.publish_air_conditioner()
            time.sleep(2)

    def blind_listener(self):
        self.sensor_lock.acquire()
        self.sensors["blind"]["active"] = True
        self.sensor_lock.release()

        while True:
            # Blind value only changed by command
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
        self.sensor_lock.release()

        if requested_mode == 0:  # OFF
            self.sensor_lock.acquire()
            self.sensors["air_conditioner"]["level"] = 0
            self.sensor_lock.release()

            GPIO.output(self.MOTOR_INPUT_PIN, GPIO.LOW)
            GPIO.output(self.MOTOR_INPUT_Y_PIN, GPIO.LOW)
            GPIO.output(self.MOTOR_INPUT_X_PIN, GPIO.LOW)

        elif requested_mode == 1:  # WARM
            self.sensor_lock.acquire()
            self.sensors["air_conditioner"]["level"] = 50
            self.sensor_lock.release()

            GPIO.output(self.MOTOR_INPUT_PIN, GPIO.HIGH)
            GPIO.output(self.MOTOR_INPUT_Y_PIN, GPIO.HIGH)
            GPIO.output(self.MOTOR_INPUT_X_PIN, GPIO.LOW)

        else:  # COLD
            self.sensor_lock.acquire()
            self.sensors["air_conditioner"]["level"] = 100
            self.sensor_lock.release()

            GPIO.output(self.MOTOR_INPUT_PIN, GPIO.HIGH)
            GPIO.output(self.MOTOR_INPUT_Y_PIN, GPIO.LOW)
            GPIO.output(self.MOTOR_INPUT_X_PIN, GPIO.HIGH)

    def handle_blind_command(self, requested_blind_level):
        self.safe_print("COMMAND RECEIVED: Setting blind to", requested_blind_level)

        self.sensor_lock.acquire()
        self.sensors["blind"]["level"] = requested_blind_level
        self.sensor_lock.release()

        if requested_blind_level <= 0:
            # -90 degrees
            self.blind_pwm.ChangeDutyCycle(5)
        elif requested_blind_level >= 180:
            # 90 degrees
            self.blind_pwm.ChangeDutyCycle(10)
        else:
            # Somewhere in between
            self.blind_pwm.ChangeDutyCycle(scale_angle_to_pwm_value(requested_blind_level))

        # Allow time for servo to move
        time.sleep(1)

        self.blind_pwm.ChangeDutyCycle(0)

    def handle_balcony_light_command(self, should_be_on, level):
        self.safe_print("COMMAND RECEIVED: Turning balcony light", should_be_on, "and to level", level)

        self.sensor_lock.acquire()
        self.sensors["balcony_light"]["on"] = should_be_on
        self.sensor_lock.release()

        if should_be_on and 0 < level <= 100:
            self.sensor_lock.acquire()
            self.sensors["balcony_light"]["level"] = float(level)
            self.sensor_lock.release()

            # Start at 0, fade to value
            self.bal_pwm.ChangeDutyCycle(0)
            for x in range(0, level):
                self.bal_pwm.ChangeDutyCycle(x + 1)
                time.sleep(0.01)

        elif should_be_on and level > 100:
            self.sensor_lock.acquire()
            self.sensors["balcony_light"]["level"] = 100.0
            self.sensor_lock.release()

            # Start at 0, fade to 100
            self.bal_pwm.ChangeDutyCycle(0)
            for x in range(0, 100):
                self.bal_pwm.ChangeDutyCycle(x + 1)
                time.sleep(0.01)

        else:
            self.sensor_lock.acquire()
            self.sensors["balcony_light"]["level"] = 0.0
            self.sensor_lock.release()

            # Immediately turn off.
            self.bal_pwm.ChangeDutyCycle(0.0)

    def handle_interior_light_command(self, should_be_on, level):
        self.safe_print("COMMAND RECEIVED: Turning interior light", should_be_on, "and to level", level)

        self.sensor_lock.acquire()
        self.sensors["interior_light"]["on"] = should_be_on
        self.sensor_lock.release()

        if should_be_on and 0 < level <= 100:
            self.sensor_lock.acquire()
            self.sensors["interior_light"]["level"] = float(level)
            self.sensor_lock.release()

            # Fade from 0 to value
            self.int_pwm.ChangeDutyCycle(0)
            for x in range(0, level):
                self.int_pwm.ChangeDutyCycle(x + 1)
                time.sleep(0.01)

        elif should_be_on and level > 100:
            self.sensor_lock.acquire()
            self.sensors["interior_light"]["level"] = 100.0
            self.sensor_lock.release()

            # Fade from 0 to 100
            self.int_pwm.ChangeDutyCycle(0)
            for x in range(0, 100):
                self.int_pwm.ChangeDutyCycle(x + 1)
                time.sleep(0.01)

        else:
            self.sensor_lock.acquire()
            self.sensors["interior_light"]["level"] = 0.0
            self.sensor_lock.release()

            # Immediately turn off.
            self.int_pwm.ChangeDutyCycle(0.0)


if __name__ == "__main__":
    simulator = RoomDevice("Room3")
    simulator.start()
