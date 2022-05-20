from abstract_rpi import AbstractRoomDevice
import threading
import random
import time


class RoomDeviceSimulator(AbstractRoomDevice):
    """
    No I/O, so no lifecycle methods needed
    """

    def device_setup(self):
        return

    def destroy(self):
        return

    """
    PUBLISHERS/LISTENERS
    """

    def presence_listener(self):
        self.sensor_lock.acquire()
        self.sensors["air_conditioner"]["active"] = True
        self.sensor_lock.release()
        while True:
            # Simulate button being pressed
            self.sensor_lock.acquire()
            self.sensors["presence"] = {
                "active": True,
                "detected": True if random.randint(0, 1) else False
            }
            self.sensor_lock.release()

            self.publish_presence()

            time.sleep(random.randint(5, 10))

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

            time.sleep(random.randint(5, 10))

    def air_conditioner_listener(self):
        self.sensor_lock.acquire()
        self.sensors["air_conditioner"]["active"] = True
        self.sensor_lock.release()
        while True:
            # Simulate ac, which should only change mode based on command
            # and change level based on temperature
            # I guess?
            self.sensor_lock.acquire()
            self.sensors["air_conditioner"] = {
                "active": True,
                "mode": self.sensors["air_conditioner"]["mode"],
                # Should not change own mode, should only let temperature do that
                "level": random.randint(0, 100)
            }
            self.sensor_lock.release()

            self.publish_air_conditioner()

            time.sleep(random.randint(5, 10))

    def blind_listener(self):
        self.sensor_lock.acquire()
        self.sensors["blind"]["active"] = True
        self.sensor_lock.release()

        while True:
            # Blind should only be changed by the upstream, so do nothing
            self.publish_blind()
            time.sleep(random.randint(5, 10))

    def balcony_light_listener(self):
        self.sensor_lock.acquire()
        self.sensors["balcony_light"]["active"] = True
        self.sensor_lock.release()

        while True:
            # Balcony light only changed by command
            self.publish_balcony_light()
            time.sleep(random.randint(5, 10))

    def interior_light_listener(self):
        self.sensor_lock.acquire()
        self.sensors["interior_light"]["active"] = True
        self.sensor_lock.release()

        while True:
            # Balcony light only changed by command
            self.publish_interior_light()

            time.sleep(random.randint(5, 10))

    """
    USER COMMAND HANDLERS
    """

    def handle_air_conditioner_command(self, requested_mode):
        self.safe_print("COMMAND RECEIVED: Setting AC mode to", requested_mode)

        self.sensor_lock.acquire()
        self.sensors["air_conditioner"]["mode"] = requested_mode
        self.sensor_lock.release()

    def handle_blind_command(self, requested_blind_level):
        self.safe_print("COMMAND RECEIVED: Setting blind to", requested_blind_level)

        self.sensor_lock.acquire()
        self.sensors["blind"]["level"] = requested_blind_level
        self.sensor_lock.release()

    def handle_balcony_light_command(self, should_be_on, level):
        self.safe_print("COMMAND RECEIVED: Turning balcony light", should_be_on, "and to level", level)

        self.sensor_lock.acquire()
        self.sensors["balcony_light"]["on"] = should_be_on
        self.sensors["balcony_light"]["level"] = level
        self.sensor_lock.release()

    def handle_interior_light_command(self, should_be_on, level):
        self.safe_print("COMMAND RECEIVED: Turning interior light", should_be_on, "and to level", level)

        self.sensor_lock.acquire()
        self.sensors["interior_light"]["on"] = should_be_on
        self.sensors["interior_light"]["level"] = level
        self.sensor_lock.release()


"""
DEVICE SIMULATORS

Interacts with the rest of the IoT solution in exactly the same way as the physical RPi
"""

NUM_DEVICES_TO_SIMULATE = 70


def start_simulator(room_index, verbose=True):
    simulator = RoomDeviceSimulator("Room" + str(room_index + 1), verbose)
    simulator.start()


if __name__ == "__main__":
    threads = []
    for i in range(NUM_DEVICES_TO_SIMULATE):
        t = threading.Thread(target=start_simulator, args=(i,), kwargs={"verbose": True}, daemon=True)
        t.start()

        threads.append(t)

    while True:
        pass
