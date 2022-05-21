import sys
import time

import RPi.GPIO as GPIO

Enable = 25
inputOne = 24
inputTwo = 23


def setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(Enable, GPIO.OUT)
    GPIO.setup(inputTwo, GPIO.OUT)
    GPIO.setup(inputOne, GPIO.OUT)


def clean():
    GPIO.cleanup()
    sys.exit()


def task():
    #forward
    print('forward')
    GPIO.output(Enable, GPIO.HIGH)
    GPIO.output(inputOne, GPIO.LOW)
    GPIO.output(inputTwo, GPIO.HIGH)
    time.sleep(5)

    #backward
    print('back')
    GPIO.output(inputOne, GPIO.HIGH)
    GPIO.output(inputTwo, GPIO.LOW)

    time.sleep(5)

    #stop
    GPIO.output(Enable, GPIO.LOW)


if __name__ == '__main__':
    setup()
    try:
        task()
    except KeyboardInterrupt:
        clean()
