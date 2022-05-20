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
