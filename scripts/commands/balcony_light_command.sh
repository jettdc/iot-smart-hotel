curl -H "Content-type: application/json" -d '{
    "type": "balcony_light",
    "room": "Room3",
    "on": true,
    "level": 75
}' 'http://35.207.111.217:5002/device_state'