"""This module runs a bottle webserver and listens for a post request that
contains a JSON payload which will be transmitted over to an MQTT broker."""

import paho.mqtt.client as mqtt
import bottle
import logging
import os
import signal
import sys

# TODO separate routes and logic

# units of measurements
VOLUME_MICROGRAMS_PER_CUBIC_METER = "µg/m³"
TEMP_CELSIUS = "°C"

# sensor names
SENSOR_TEMPERATURE = "temperature"
SENSOR_HUMIDITY = "humidity"
SENSOR_BME280_TEMPERATURE = "BME280_temperature"
SENSOR_BME280_HUMIDITY = "BME280_humidity"
SENSOR_BME280_PRESSURE = "BME280_pressure"
SENSOR_BMP_TEMPERATURE = "BMP_temperature"
SENSOR_BMP_PRESSURE = "BMP_pressure"
SENSOR_BMP280_TEMPERATURE = "BMP280_temperature"
SENSOR_BMP280_PRESSURE = "BMP280_pressure"
SENSOR_PM1 = "SDS_P1"
SENSOR_PM2 = "SDS_P2"
SENSOR_WIFI_SIGNAL = "signal"
SENSOR_HTU21D_TEMPERATURE = "HTU21D_temperature"
SENSOR_HTU21D_HUMIDITY = "HTU21D_humidity"
SENSOR_SPS30_P0 = "SPS30_P0"
SENSOR_SPS30_P2 = "SPS30_P2"
SENSOR_SPS30_P4 = "SPS30_P4"
SENSOR_SPS30_P1 = "SPS30_P1"
SENSOR_PMS_P0 = "PMS_P0"
SENSOR_PMS_P1 = "PMS_P1"
SENSOR_PMS_P2 = "PMS_P2"
SENSOR_RSSI = "signal"

# template placeholders
TEMPLATE_TEMPERATURE = "{{value|float|round(1)}}"
TEMPLATE_HUMIDITY = "{{value|float|round(0)}}"
TEMPLATE_PRESSURE = "{{((value|float)/100)|round(0)}}"
TEMPLATE_MICROGRAM = "{{value|float|round(0)}}"

# map for sensors
# SENSOR_NAME: [ Friendly Name, Unit of measurement, Device class ]
SENSOR_TYPES = {
    SENSOR_TEMPERATURE: ["Temperature", TEMP_CELSIUS, "temperature"],
    SENSOR_HUMIDITY: ["Humidity", "%", "humidity"],
    SENSOR_BME280_TEMPERATURE: ["Temperature", TEMP_CELSIUS, "temperature"],
    SENSOR_BME280_HUMIDITY: ["Humidity", "%", "humidity"],
    SENSOR_BME280_PRESSURE: ["Pressure", "hPa", "pressure"],
    SENSOR_BMP_TEMPERATURE: ["Temperature", TEMP_CELSIUS, "temperature"],
    SENSOR_BMP_PRESSURE: ["Pressure", "hPa", "pressure"],
    SENSOR_BMP280_TEMPERATURE: ["Temperature", TEMP_CELSIUS, "temperature"],
    SENSOR_BMP280_PRESSURE: ["Pressure", "hPa", "pressure"],
    SENSOR_PM1: ["PM10", VOLUME_MICROGRAMS_PER_CUBIC_METER, "pm10"],
    SENSOR_PM2: ["PM2.5", VOLUME_MICROGRAMS_PER_CUBIC_METER, "pm25"],
    SENSOR_WIFI_SIGNAL: ["Wifi signal", "dBm", "signal_strength"],
    SENSOR_HTU21D_TEMPERATURE: ["Temperature", TEMP_CELSIUS, "temperature"],
    SENSOR_HTU21D_HUMIDITY: ["Humidity", "%", "humidity"],
    SENSOR_SPS30_P0: ["PM1", VOLUME_MICROGRAMS_PER_CUBIC_METER, "pm1"],
    SENSOR_SPS30_P2: ["PM2.5", VOLUME_MICROGRAMS_PER_CUBIC_METER, "pm25"],
    SENSOR_SPS30_P4: ["PM4", VOLUME_MICROGRAMS_PER_CUBIC_METER, None],
    SENSOR_SPS30_P1: ["PM10", VOLUME_MICROGRAMS_PER_CUBIC_METER, "pm10"],
    SENSOR_PMS_P0: ["PM1", VOLUME_MICROGRAMS_PER_CUBIC_METER, "pm1"],
    SENSOR_PMS_P1: ["PM10", VOLUME_MICROGRAMS_PER_CUBIC_METER, "pm10"],
    SENSOR_PMS_P2: ["PM2.5", VOLUME_MICROGRAMS_PER_CUBIC_METER, "pm25"],
    SENSOR_RSSI: ["RSSI", "dB", "signal_strength"],
}

# icons for sensors that have no class
SENSOR_ICONS = {
    SENSOR_PM1: ["mdi:thought-bubble"],
    SENSOR_PM2: ["mdi:thought-bubble-outline"],
    SENSOR_SPS30_P0: ["mdi:cloud"],
    SENSOR_SPS30_P2: ["mdi:thought-bubble-outline"],
    SENSOR_SPS30_P4: ["mdi:cloud-outline"],
    SENSOR_SPS30_P1: ["mdi:thought-bubble"],
    SENSOR_PMS_P0: ["mdi:cloud"],
    SENSOR_PMS_P1: ["mdi:thought-bubble"],
    SENSOR_PMS_P2: ["mdi:thought-bubble-outline"],
}

# map for value templates
VALUE_TEMPLATES = {
    SENSOR_BME280_HUMIDITY: TEMPLATE_HUMIDITY,
    SENSOR_BME280_PRESSURE: TEMPLATE_PRESSURE,
    SENSOR_BME280_TEMPERATURE: TEMPLATE_TEMPERATURE,
    SENSOR_BMP280_PRESSURE: TEMPLATE_PRESSURE,
    SENSOR_BMP280_TEMPERATURE: TEMPLATE_TEMPERATURE,
    SENSOR_BMP_PRESSURE: TEMPLATE_PRESSURE,
    SENSOR_BMP_TEMPERATURE: TEMPLATE_TEMPERATURE,
    SENSOR_HTU21D_HUMIDITY: TEMPLATE_HUMIDITY,
    SENSOR_HTU21D_TEMPERATURE: TEMPLATE_TEMPERATURE,
    SENSOR_HUMIDITY: TEMPLATE_HUMIDITY,
    SENSOR_TEMPERATURE: TEMPLATE_TEMPERATURE,
    SENSOR_PM1: TEMPLATE_MICROGRAM,
    SENSOR_PM2: TEMPLATE_MICROGRAM,
    SENSOR_SPS30_P0: TEMPLATE_MICROGRAM,
    SENSOR_SPS30_P1: TEMPLATE_MICROGRAM,
    SENSOR_SPS30_P2: TEMPLATE_MICROGRAM,
    SENSOR_SPS30_P4: TEMPLATE_MICROGRAM,
    SENSOR_PMS_P0: TEMPLATE_MICROGRAM,
    SENSOR_PMS_P1: TEMPLATE_MICROGRAM,
    SENSOR_PMS_P2: TEMPLATE_MICROGRAM,
}

# Map for state classes
STATE_CLASSES = {
    SENSOR_TEMPERATURE: ["measurement"],
    SENSOR_HUMIDITY: ["measurement"],
    SENSOR_BME280_TEMPERATURE: ["measurement"],
    SENSOR_BME280_HUMIDITY: ["measurement"],
    SENSOR_BME280_PRESSURE: ["measurement"],
    SENSOR_BMP_TEMPERATURE: ["measurement"],
    SENSOR_BMP_PRESSURE: ["measurement"],
    SENSOR_BMP280_TEMPERATURE: ["measurement"],
    SENSOR_BMP280_PRESSURE: ["measurement"],
    SENSOR_PM1: ["measurement"],
    SENSOR_PM2: ["measurement"],
    SENSOR_HTU21D_TEMPERATURE: ["measurement"],
    SENSOR_HTU21D_HUMIDITY: ["measurement"],
    SENSOR_SPS30_P0: ["measurement"],
    SENSOR_SPS30_P2: ["measurement"],
    SENSOR_SPS30_P4: ["measurement"],
    SENSOR_SPS30_P1: ["measurement"],
    SENSOR_PMS_P0: ["measurement"],
    SENSOR_PMS_P1: ["measurement"],
    SENSOR_PMS_P2: ["measurement"],
    SENSOR_WIFI_SIGNAL: [None],
    SENSOR_RSSI: [None],
}

application = bottle.default_app()


@application.post("/luftdaten/json2mqtt")
def route_luftdaten_json2mqtt():
    """The default route that is listening to post requests."""
    # take the json and parse it
    json_req = bottle.request.json
    logging.debug("json req received %s", json_req)

    device_address = bottle.request.environ.get("HTTP_X_FORWARDED_FOR") or bottle.request.environ.get("REMOTE_ADDR")
    if bottle.request.headers.get("X-Mac-Id"):
        publish(json_req, MQTT_TOPIC + bottle.request.headers.get("X-Mac-Id"), device_address)


def publish(json, topic_prefix, device_address):
    """Publish to mqtt whatever we can/want"""

    if json["software_version"]:
        t = topic_prefix + "/firmware"
        val = json["software_version"]
        logging.debug("publishing to broker: '%s' '%s'", t, str(val))
        CLIENT.publish(topic=t, payload=val, retain=False)

    interval = 0
    for item in json["sensordatavalues"]:
        if str(item["value_type"]) == "interval":
            interval = int(item["value"]) / 1000

    for item in json["sensordatavalues"]:
        # do not explode on unknown measurements
        if str(item["value_type"]) in SENSOR_TYPES:
            uniq_id = str("luftdaten-" + str(topic_prefix).split("/")[-1] + "-" + str(item["value_type"])).lower()
            dev_name = "Luftdaten " + str(bottle.request.headers.get("X-Sensor").split("-")[-1])

            # homeassistant autodiscovery
            t = "homeassistant/sensor/" + uniq_id + "/config"
            val = {
                "~": topic_prefix,
                "name": dev_name + " " + str(SENSOR_TYPES[str(item["value_type"])][0]),
                "stat_t": "~/" + str(item["value_type"]),
                "frc_upd": "False",
                "qos": 0,
                "uniq_id": uniq_id,
                "unit_of_meas": SENSOR_TYPES[str(item["value_type"])][1],
                "dev": {
                    "ids": [str(topic_prefix).split("/")[-1].lower()],
                    "name": dev_name,
                    "mdl": "DIY " + str(bottle.request.headers.get("X-Sensor")),
                    "sw": json["software_version"],
                    "mf": "DIY Luftdaten",
                    "cu": "http://" + str(device_address),
                },
                "exp_aft": 4 * interval,
                "entity_category": "diagnostic",
                # add origin as per: https://github.com/home-assistant/core/pull/98782
                "o": {
                    "name": "luftdaten2mqtt",
                    "sw": "1.1.6",
                    "url": "https://github.com/zeridon/luftdaten2mqtt/issues",
                },
            }

            # set device class if available, else set an icon to be better
            # looking
            if SENSOR_TYPES[str(item["value_type"])][2]:
                val["dev_cla"] = SENSOR_TYPES[str(item["value_type"])][2]
            else:
                val["icon"] = SENSOR_ICONS[str(item["value_type"])][0]

            # Set value template if such exists
            if str(item["value_type"]) in VALUE_TEMPLATES:
                val["val_tpl"] = str(VALUE_TEMPLATES[str(item["value_type"])])

            # set state class if available
            if STATE_CLASSES[str(item["value_type"])][0]:
                val["stat_cla"] = STATE_CLASSES[str(item["value_type"])][0]

            logging.debug("publishing to broker: '%s' '%s'", t, str(val))
            CLIENT.publish(topic=t, payload=str(val).replace("'", '"'), retain=True)

            # report data
            t = topic_prefix + "/" + str(item["value_type"])
            val = item["value"]
            logging.debug("publishing to broker: '%s' '%s'", t, str(val))
            CLIENT.publish(topic=t, payload=val, retain=False)


@application.get("/status")
def status():
    return "OK"


"""Simple page documenting what this is"""


@application.get("/luftdaten")
@application.get("/")
def route_index():
    return bottle.template("index")


"""on_connect handler to disconnect and die in case of error"""


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logging.info("Connected to broker %s", MQTT_HOST)
    elif rc == 1:
        logging.error("Can't connect to MQTT Broker %s. Incorrect protocol", MQTT_HOST)
        os._exit(rc)
    elif rc == 2:
        logging.error("MQTT Broker %s Refused connection. Invalid Client ID", MQTT_HOST)
        os._exit(rc)
    elif rc == 3:
        logging.error("MQTT Broker %s available ", MQTT_HOST)
        os._exit(rc)
    elif rc == 4:
        logging.error("MQTT Broker %s Refused connection. Bad Username/Password", MQTT_HOST)
        os._exit(rc)
    elif rc == 5:
        logging.error("MQTT Broker %s Refused connection. Not Authorized", MQTT_HOST)
        os._exit(rc)
    else:
        logging.info("Reserved error code (%s), from Broker %s", rc, MQTT_HOST)
        os._exit(rc)


def setup():
    """Port to listen on"""
    global HTTP_PORT
    HTTP_PORT = os.getenv("HTTP_PORT", "8080")

    """ MQTT Related """
    global MQTT_HOST
    MQTT_HOST = os.getenv("MQTT_HOST", "192.168.1.1")
    global MQTT_TOPIC
    MQTT_TOPIC = os.getenv("MQTT_TOPIC", "luftdaten/")
    global MQTT_USER
    MQTT_USER = os.getenv("MQTT_USER", "")
    global MQTT_PASS
    MQTT_PASS = os.getenv("MQTT_PASS", "")

    logging.debug("connecting to mqtt broker %s", MQTT_HOST)
    global CLIENT
    CLIENT = mqtt.Client(clean_session=True)

    CLIENT.on_connect = on_connect
    if MQTT_USER and MQTT_PASS:
        CLIENT.username_pw_set(username=MQTT_USER, password=MQTT_PASS)

    CLIENT.connect(MQTT_HOST)
    CLIENT.loop_start()


def run_server():
    """Run the bottle-server on the configured http-port."""
    bottle.run(app=application, host="0.0.0.0", port=HTTP_PORT, reloader=True)


def sigterm_handler(signo, stack_frame):
    logging.debug("Processing SIGTERM, %s, %s" % (signo, stack_frame))
    sys.exit(0)


if __name__ == "__main__":
    """Hook our sigterm handler"""
    signal.signal(signal.SIGTERM, sigterm_handler)

    """ Init loglevel and errorcheck it """
    global LOG_LEVEL
    LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
    numeric_level = getattr(logging, LOG_LEVEL.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError("Invalid log level: %s" % LOG_LEVEL)

    """ setup logging """
    logging.basicConfig(level=numeric_level)

    """ Go for MQTT """
    setup()

    """ Open server """
    run_server()
