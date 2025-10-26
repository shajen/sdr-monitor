from sdr.utils.spectogram_reader import SpectrogramReader
from sdr.utils.transmission_reader import TransmissionReader
from urllib.parse import urlparse
import django.db
import logging
import paho.mqtt.client
import ssl
import threading


def parse_mqtt_url(url):
    url_data = urlparse(url)
    use_tls = url_data.scheme in ["wss", "mqtts"]
    use_ws = url_data.scheme in ["ws", "wss"]

    if not url_data.port:
        port = 443 if use_tls else 80
    else:
        port = url_data.port

    transport = "websockets" if use_ws else "tcp"
    return (url_data.hostname, port, url_data.path, transport, use_ws, use_tls)


class Reader(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.__logger = logging.getLogger("Reader")

        self.__parsers = []
        self.__parsers.append(SpectrogramReader())
        self.__parsers.append(TransmissionReader())

        (host, port, path, transport, use_ws, use_tls) = parse_mqtt_url(config["url"])
        self.__client = paho.mqtt.client.Client(paho.mqtt.client.CallbackAPIVersion.VERSION1, client_id="monitor", transport=transport)
        if use_tls:
            self.__client.tls_set(tls_version=ssl.PROTOCOL_TLS_CLIENT)
        if use_ws:
            self.__client.ws_set_options(path=path)
        self.__client.username_pw_set(config["user"], config["password"])
        self.__client.user_data_set(self)
        self.__client.connect(host, port)
        self.__client.on_connect = Reader.on_connect
        self.__client.on_message = Reader.on_message

    def run(self):
        self.__client.loop_forever()

    def stop(self):
        self.__client.disconnect()

    def on_connect(client, userdata, flags, rc):
        self = userdata
        self.__logger.info("connected")
        self.__client.subscribe("sdr/+/spectrogram")
        self.__client.subscribe("sdr/+/transmission")
        self.__client.subscribe("sdr/+/transmission/+")

    def on_message(client, userdata, message):
        self = userdata
        django.db.reset_queries()
        django.db.close_old_connections()
        for parser in self.__parsers:
            try:
                if parser.on_message(client, message):
                    return True
            except django.db.OperationalError:
                self.__logger.warn("reset db connection")
                django.db.connection.close()
            except Exception as e:
                pass
                self.__logger.warn("exception: %s" % e)
        self.__logger.warn("can not parse, topic: %s" % (message.topic))
