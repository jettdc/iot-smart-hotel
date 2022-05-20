import requests
import os


class RoomActivator:
    ROOM_MANAGEMENT_URL = "http://" + os.getenv('ROOM_MAN_ADDRESS') + ":" + os.getenv('ROOM_MAN_PORT')
    ACTIVATE_URL = ROOM_MANAGEMENT_URL + "/activate"
    DEACTIVATE_URL = ROOM_MANAGEMENT_URL + "/deactivate"

    def __init__(self, room_name):
        self.room_name = room_name

    def register_or_set_active(self):
        requests.post(self.ACTIVATE_URL + "/" + self.room_name)

    def set_not_active(self):
        res = requests.post(self.DEACTIVATE_URL + "/" + self.room_name)
