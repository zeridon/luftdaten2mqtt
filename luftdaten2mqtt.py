"""This module runs a bottle webserver and listens for a post request that
contains a JSON payload which will be transmitted over to an MQTT broker."""

import paho.mqtt.client as mqtt
import bottle
import logging
import datetime
import os

# TODO separate routes and logic

# units of measurements
VOLUME_MICROGRAMS_PER_CUBIC_METER = 'µg/m³'
TEMP_CELSIUS = '°C'

# sensor names
SENSOR_TEMPERATURE = 'temperature'
SENSOR_HUMIDITY = 'humidity'
SENSOR_BME280_TEMPERATURE = 'BME280_temperature'
SENSOR_BME280_HUMIDITY = 'BME280_humidity'
SENSOR_BME280_PRESSURE = 'BME280_pressure'
SENSOR_BMP_TEMPERATURE = 'BMP_temperature'
SENSOR_BMP_PRESSURE = 'BMP_pressure'
SENSOR_BMP280_TEMPERATURE = 'BMP280_temperature'
SENSOR_BMP280_PRESSURE = 'BMP280_pressure'
SENSOR_PM1 = 'SDS_P1'
SENSOR_PM2 = 'SDS_P2'
SENSOR_WIFI_SIGNAL = 'signal'
SENSOR_HTU21D_TEMPERATURE = 'HTU21D_temperature'
SENSOR_HTU21D_HUMIDITY = 'HTU21D_humidity'
SENSOR_SPS30_P0 = 'SPS30_P0'
SENSOR_SPS30_P2 = 'SPS30_P2'
SENSOR_SPS30_P4 = 'SPS30_P4'
SENSOR_SPS30_P1 = 'SPS30_P1'
SENSOR_PMS_P0 = 'PMS_P0'
SENSOR_PMS_P1 = 'PMS_P1'
SENSOR_PMS_P2 = 'PMS_P2'

# map for sensors
# SENSOR_NAME: [ Friendly Name, Unit of measurement, Device class ]
SENSOR_TYPES = {
    SENSOR_TEMPERATURE: ['Temperature', TEMP_CELSIUS, 'temperature'],
    SENSOR_HUMIDITY: ['Humidity', '%', 'humidity'],
    SENSOR_BME280_TEMPERATURE: ['Temperature', TEMP_CELSIUS, 'temperature'],
    SENSOR_BME280_HUMIDITY: ['Humidity', '%', 'humidity'],
    SENSOR_BME280_PRESSURE: ['Pressure', 'Pa', 'pressure'],
    SENSOR_BMP_TEMPERATURE: ['Temperature', TEMP_CELSIUS, 'temperature'],
    SENSOR_BMP_PRESSURE: ['Pressure', 'Pa', 'pressure'],
    SENSOR_BMP280_TEMPERATURE: ['Temperature', TEMP_CELSIUS, 'temperature'],
    SENSOR_BMP280_PRESSURE: ['Pressure', 'Pa', 'pressure'],
    SENSOR_PM1: ['PM10', VOLUME_MICROGRAMS_PER_CUBIC_METER, None],
    SENSOR_PM2: ['PM2.5', VOLUME_MICROGRAMS_PER_CUBIC_METER, None],
    SENSOR_WIFI_SIGNAL: ['Wifi signal', 'dBm', 'signal_strength'],
    SENSOR_HTU21D_TEMPERATURE: ['Temperature', TEMP_CELSIUS, 'temperature'],
    SENSOR_HTU21D_HUMIDITY: ['Humidity', '%', 'humidity'],
    SENSOR_SPS30_P0: ['PM1', VOLUME_MICROGRAMS_PER_CUBIC_METER, None],
    SENSOR_SPS30_P2: ['PM2.5', VOLUME_MICROGRAMS_PER_CUBIC_METER, None],
    SENSOR_SPS30_P4: ['PM4', VOLUME_MICROGRAMS_PER_CUBIC_METER, None],
    SENSOR_SPS30_P1: ['PM10', VOLUME_MICROGRAMS_PER_CUBIC_METER, None],
    SENSOR_PMS_P0: ['PM1', VOLUME_MICROGRAMS_PER_CUBIC_METER, None],
    SENSOR_PMS_P1: ['PM10', VOLUME_MICROGRAMS_PER_CUBIC_METER, None],
    SENSOR_PMS_P2: ['PM2.5', VOLUME_MICROGRAMS_PER_CUBIC_METER, None],
}

# icons for sensors that have no class
SENSOR_ICONS = {
    SENSOR_PM1: ['mdi:thought-bubble'],
    SENSOR_PM2: ['mdi:thought-bubble-outline'],
    SENSOR_SPS30_P0: ['mdi:cloud'],
    SENSOR_SPS30_P2: ['mdi:thought-bubble-outline'],
    SENSOR_SPS30_P4: ['mdi:cloud-outline'],
    SENSOR_SPS30_P1: ['mdi:thought-bubble'],
    SENSOR_PMS_P0: ['mdi:cloud'],
    SENSOR_PMS_P1: ['mdi:thought-bubble'],
    SENSOR_PMS_P2: ['mdi:thought-bubble-outline'],
}

application = bottle.default_app()

@application.post("/luftdaten/json2mqtt")
def route_luftdaten_json2mqtt():
    """The default route that is listening to post requests."""
    # take the json and parse it
    json_req = bottle.request.json
    logging.debug("json req received %s", json_req)

    if bottle.request.headers.get('X-Mac-Id'):
        publish(json_req, MQTT_TOPIC + bottle.request.headers.get('X-Mac-Id'))

def publish(json, topic_prefix):
    """ Publish to mqtt whatever we can/want"""

    if json["software_version"]:
        t = topic_prefix + "/firmware"
        val = json["software_version"]
        logging.debug("publishing to broker: '%s' '%s'", t, str(val))
        CLIENT.publish(topic=t, payload=val, retain=False)

    interval = 0
    for item in json["sensordatavalues"]:
        if str(item["value_type"]) == 'interval':
            interval = int(item["value"])/1000

    for item in json["sensordatavalues"]:
        # do not explode on unknown measurements
        if str(item["value_type"]) in SENSOR_TYPES:
            uniq_id = str(
                "luftdaten-" +
                str(topic_prefix).split('/')[-1] + "-" +
                str(item["value_type"])
            ).lower()
            dev_name = "Luftdaten " + str(bottle.request.headers.get('X-Sensor').split('-')[-1])

            # homeassistant autodiscovery
            t = "homeassistant/sensor/" + uniq_id + "/config"
            val = {
                "~": topic_prefix,
                "name": dev_name + " " + str(SENSOR_TYPES[str(item["value_type"])][0]),
                "stat_t": "~/"+str(item["value_type"]),
                "frc_upd": "False",
                "qos": 0,
                "uniq_id": uniq_id,
                "unit_of_meas": SENSOR_TYPES[str(item["value_type"])][1],
                "dev": {
                    "ids": [str(topic_prefix).split('/')[-1].lower()],
                    "name": dev_name,
                    "mdl": "DIY " + str(bottle.request.headers.get('X-Sensor')),
                    "sw": json["software_version"],
                    "mf": "DIY Luftdaten"
                },
                "exp_aft": 1.2*interval
            }

            # set device class if available, else set an icon to be better
            # looking
            if SENSOR_TYPES[str(item["value_type"])][2]:
                payload["dev_cla"] = SENSOR_TYPES[str(item["value_type"])][2]
            else:
                payload["icon"] = SENSOR_ICONS[str(item["value_type"])][0]

            logging.debug("publishing to broker: '%s' '%s'",t , str(val))
            CLIENT.publish(topic=topic, payload=str(payload).replace("'", '"'), retain=False)

            # report data
            t = topic_prefix + "/" + str(item["value_type"])
            val = item["value"]
            logging.debug("publishing to broker: '%s' '%s'", t, str(val))
            CLIENT.publish(topic=t, payload=val, retain=False)

@application.get("/luftdaten")
def route_index():
    # return page with current values
    pass


def setup():
    """ Port to listen on """
    global HTTP_PORT
    HTTP_PORT = os.getenv('HTTP_PORT', '8080')

    """ MQTT Related """
    global MQTT_HOST
    MQTT_HOST = os.getenv('MQTT_HOST', '192.168.1.1')
    global MQTT_TOPIC
    MQTT_TOPIC = os.getenv('MQTT_TOPIC', 'luftdaten/')
    global MQTT_USER
    MQTT_USER = os.getenv('MQTT_USER', 'user')
    global MQTT_PASS
    MQTT_PASS = os.getenv('MQTT_PASS', 'pass')

    logging.debug("connecting to mqtt broker %s", MQTT_HOST)
    global CLIENT
    CLIENT = mqtt.Client(clean_session=True)
    CLIENT.username_pw_set(username=MQTT_USER,password=MQTT_PASS)

    CLIENT.connect(MQTT_HOST)
    CLIENT.loop_start()


def run_server():
    """Run the bottle-server on the configured http-port."""
    bottle.run(
        app=application,
        host="0.0.0.0",
        port=HTTP_PORT,
        reloader=True
    )

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup()
    run_server()
