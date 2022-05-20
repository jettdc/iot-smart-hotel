# Operating Systems Design Final IoT Solution
#### Jett Crowson & Ben Weiler

## Running
- In GCP, start the `iot` and `twins` virtual machines and open ssh windows into both
- In `iot`
  - `$ cd session13`
  - `$ bash scripts/start_iot_services.sh`
- In `twins`
  - `$ cd session13`
  - `$ bash scripts/start_digital_twins.sh` to start 4 digital twins, or
  - `$ bash scripts/start_digital_twins_full.sh` to start 70 digital twins

## Project Structure
```
.
├── DigitalTwin
│   ├── README.md
│   ├── digital_twin
│   │   ├── Dockerfile
│   │   └── app
│   │       └── digital_twin.py
│   ├── docker-compose.yaml
│   └── launch_instances.sh
├── IOTServices
│   ├── MQTT-1
│   │   ├── Dockerfile
│   │   └── app
│   │       └── mosquitto.conf
│   ├── MQTT-2
│   │   ├── Dockerfile
│   │   └── app
│   │       └── mosquitto.conf
│   ├── data_ingestion_microservice
│   │   ├── Dockerfile
│   │   └── app
│   │       ├── __init__.py
│   │       ├── __pycache__
│   │       ├── data_ingestion.py
│   │       └── data_ingestion_api_rest.py
│   ├── docker-compose.yaml
│   ├── frontend
│   │   ├── Dockerfile
│   │   └── app
│   │       ├── index.html
│   │       ├── js_lib.js
│   │       ├── logo.png
│   │       └── styles.css
│   ├── mariaDB
│   │   ├── access_db.sh
│   │   ├── create.sql
│   │   ├── get_all.sql
│   │   └── setup.sql
│   ├── message_router
│   │   ├── Dockerfile
│   │   └── app
│   │       ├── __init__.py
│   │       ├── activator.py
│   │       └── message_router.py
│   ├── rooms_management_microservice
│   │   ├── Dockerfile
│   │   └── app
│   │       ├── rmm.py
│   │       └── rmm_api.py
│   └── webapp_backend
│       ├── Dockerfile
│       └── app
│           └── webapp_backend_api.py
├── README.md
├── RPi
│   ├── __init__.py
│   ├── __pycache__
│   │   └── abstract_rpi.cpython-310.pyc
│   ├── abstract_rpi.py
│   ├── abstract_rpi.pyc
│   ├── pi_implementation.py
│   └── pi_simulation.py
└── scripts
    ├── __init__.py
    ├── access_db.sh
    ├── commands
    │   ├── air_conditioner_command.sh
    │   ├── balcony_light_command.sh
    │   ├── blind_command.sh
    │   └── interior_light_command.sh
    ├── frontend_requests
    │   ├── __init__.py
    │   ├── facades
    │   │   ├── __init__.py
    │   │   ├── facade_command_generator.py
    │   │   └── square_outline_facade.sh
    │   └── get_room_info.sh
    ├── start_digital_twins.sh
    ├── start_digital_twins_full.sh
    └── start_iot_services.sh

```