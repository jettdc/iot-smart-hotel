import mysql.connector
import os


def connect_database():
    mydb = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
    )
    return mydb


def insert_device_state(params):
    mydb = connect_database()
    with mydb.cursor() as mycursor:
        sql = "INSERT INTO device_state (room, type, value, date) VALUES (%s, %s, %s, %s)"
        values = (
            params["room"],
            params["type"],
            params["value"],
            params["date"]
        )
        mycursor.execute(sql, values)
        mydb.commit()
        mycursor.close()
        mydb.close()
        return mycursor


def process_response(res):
    state = {}
    for item in res:
        state[item[1]] = {
            "value": item[2],
            "timestamp": item[3]
        }
    return state


def get_device_state(room):
    mydb = connect_database()
    with mydb.cursor() as mycursor:
        sql = """
        (SELECT a.room, a.type, a.value, a.date 
            FROM (SELECT * FROM device_state WHERE room=%s) 
            a INNER JOIN (SELECT type, MAX(`date`) AS MaxTime 
            FROM (SELECT * FROM device_state WHERE room=%s) c 
            GROUP BY type) b 
            ON a.type = b.type AND a.date = b.MaxTime) 
        UNION 
        (SELECT '%s', 'active', active, NOW() 
            FROM device_registration 
            WHERE name LIKE CONCAT('%m', %s)
        );
        """
        mycursor.execute(sql, (int(room), int(room), int(room), int(room)))
        result = mycursor.fetchall()
        mycursor.close()
        mydb.close()
        return process_response(result)
