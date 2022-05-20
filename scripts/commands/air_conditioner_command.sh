curl -H "Content-type: application/json" -d '{
    "type": "air_conditioner",
    "room": "Room3",
    "mode": "warm"
}' 'http://35.207.111.217:5002/device_state'