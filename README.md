# sensor.community to home-assistant via MQTT
[Sensor.Community](https://sensor.community) has instructions how to [build](https://sensor.community/en/sensors/) your own sensors. They provide a nice map and some functionality. There is also an integration ([Sensor.Community](https://www.home-assistant.io/integrations/luftdaten/) to pull a station data inside home assistant. Unfortunately this goes over the internet and so is not quite desirable.

This simple daemon will help you to integrate the sensor station into home assistant via MQTT.

# How to Use
The easiest way to use this is to run it as a docker container `docker run -d --restart always --name luftdaten2mqtt -p 8080:8080 zeridon/luftdaten2mqtt:latest`

# Use without docker
make sure you have `bottle` and `paho-mqtt` installed and then simply `python ./luftdaten2mqtt.py`

# Settings
Settings are controled via environment variables. The following variables are available:

| Variable | Default | Description |
| -------- | ------- | ----------- |
| HTTP_PORT | 8080 | Port to listen on for incomming traffic |
| MQTT_HOST | 192.168.1.1 | Host where MQTT Broker (e.g. mosquitto) is running |
| MQTT_USER | user | Username to use when connecting to MQTT Broker |
| MQTT_PASS | pass | Password to use when connecting to MQTT Broker |
| MQTT_TOPIC | luftdaten/ | Base topic to which to submit data |
| LOG_LEVEL | DEBUG | Verbosity level for logging (DEBUG, INFO, NOTICE, ERROR) |

# How to configure a luftdaten Sensor
Luftdaten sensors have an option to configure custom api to which to send the data. The proper configuration is as follows:

| Parameter | Value | Description |
| --------- | ----- | ----------- |
| Server | 192.168.1.5 | The address/host where this program is running |
| Path | /luftdaten/json2mqtt | The path to which the sensor will `POST` the data |
| Port | 8080 | The value of HTTP_PORT (or if using Docker the externally mapped port |

# TODO
 * Add more env parameters for better configurability

# Performance
Not really tested but with simplistic load test performs good enough. My current network is 6 sensors and so far i have seen no issues.
