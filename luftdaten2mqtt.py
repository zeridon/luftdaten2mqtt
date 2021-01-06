"""This module runs a bottle webserver and listens for a post request that
contains a JSON payload which will be transmitted over to an MQTT broker."""

import paho.mqtt.client as mqtt
import bottle
import logging
import datetime
import os

# TODO separate routes and logic

HTTP_PORT = 8080
MQTT_HOST = "192.168.1.1"
MQTT_TOPIC = "luftdaten/airrohr/"
MQTT_USER = "user"
MQTT_PASS = "pass"

application = bottle.default_app()


@application.post("/luftdaten/json2mqtt")
def route_luftdaten_json2mqtt():
    """The default route that is listening to post requests."""
    # take the json and parse it
    json_req = bottle.request.json
    logging.debug("json req received %s", json_req)
    #headers_string = [
    #    '{}: {}'.format(h, bottle.request.headers.get(h)) for h in bottle.request.headers.keys()
    #]
    #print('URL={}, method={}\nheaders:\n{}'.format(bottle.request.url, bottle.request.method,'\n'.join(headers_string)))

    if bottle.request.headers.get('X-Sensor'):
        publish(json_req, MQTT_TOPIC + bottle.request.headers.get('X-Sensor') + "/")
    #now = str(datetime.datetime.now())
    #publish({"stats/last_update": now,
    #         "stats/interval": 120}, MQTT_TOPIC)


def publish(json, topic_prefix):
    #print(json)
    #print(json["sensordatavalues"][0]["value_type"])
    if json["software_version"]:
        t = topic_prefix + "firmware"
        val = json["software_version"]
        logging.debug("publishing to broker: '%s' '%s'", t, str(val))
        CLIENT.publish(topic=t, payload=val, retain=False)
    for item in json["sensordatavalues"]:
        t = topic_prefix + str(item["value_type"])
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
    CLIENT = mqtt.Client(clean_session=True)
    CLIENT.username_pw_set(username=MQTT_USER,password=MQTT_PASS)

    CLIENT.connect(MQTT_HOST)
    CLIENT.loop_start()


def run_server():
    """Run the bottle-server on the configured http-port."""
    bottle.run(app=application,
               host="0.0.0.0", port=HTTP_PORT, reloader=True)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    setup()
    run_server()
