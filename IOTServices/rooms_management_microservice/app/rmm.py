import mysql.connector
import os
import requests
import json

DATA_INGEST_ADDRESS = os.getenv('DATA_INGESTION_API_ADDRESS')
DATA_INGEST_PORT = os.getenv('DATA_INGESTION_API_PORT')
DATA_INGEST_URL = "http://" + DATA_INGEST_ADDRESS + ":" + DATA_INGEST_PORT


def connect_database():
    mydb = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
    )
    return mydb


def device_registered(device):
    db = connect_database()
    with db.cursor() as cursor:
        sql = "SELECT * FROM device_registration WHERE name=%s LIMIT 1;"
        cursor.execute(sql, (device,))
        result = cursor.fetchall()
        cursor.close()
        db.close()
        return len(result) > 0


def parse_room(room):
    """
    Room3 => 3
    """
    return room[4:]


def get_room_state_json(room):
    return json.dumps(requests.get(
        DATA_INGEST_URL + "/device_state/" + parse_room(room),
    ).json())


def register_device(device):
    db = connect_database()
    with db.cursor() as cursor:
        sql = "INSERT INTO device_registration (name, active, room_state) VALUES (%s, %s, %s)"
        cursor.execute(sql, (device, True, get_room_state_json(device)))
        db.commit()
        cursor.close()
        db.close()
        return


def activate_device(device):
    db = connect_database()
    with db.cursor() as cursor:
        sql = "UPDATE device_registration SET active=1, room_state=%s WHERE name=%s"
        cursor.execute(sql, (get_room_state_json(device), device))
        db.commit()
        cursor.close()
        db.close()
        return


def register_or_activate_device(device):
    if not device_registered(device):
        register_device(device)
        return

    activate_device(device)


def de_activate_device(device):
    db = connect_database()
    with db.cursor() as cursor:
        sql = "UPDATE device_registration SET active=0, room_state=%s WHERE name=%s"
        cursor.execute(sql, (get_room_state_json(device), device))
        db.commit()
        cursor.close()
        db.close()
        return
