import json

facade = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]


def generate_facade_json():
    room_index = 1
    rooms = []
    states = []
    for row in facade:
        for column in row:
            rooms.append("Room" + str(room_index))
            room_index += 1
            states.append(True if column == 1 else False)
    return json.dumps({
        "rooms": rooms,
        "states": states
    })


if __name__ == "__main__":
    print(generate_facade_json())
