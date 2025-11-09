from sdr.utils.gain_tester_controller import GainTesterController
from sdr.utils.scheduler import Scheduler
from sdr.utils.spectogram_reader import SpectrogramReader
from sdr.utils.transmission_reader import TransmissionReader
import common.utils.mqtt
import django.db
import logging
import threading


class Reader(threading.Thread):
    def __init__(self, config):
        threading.Thread.__init__(self)
        self.__logger = logging.getLogger("Reader")

        self.__parsers = []
        self.__parsers.append(SpectrogramReader())
        self.__parsers.append(TransmissionReader())
        self.__parsers.append(Scheduler())
        self.__parsers.append(GainTesterController())

        self.__client = common.utils.mqtt.get_client(config["url"], config["user"], config["password"], "sdr-monitor", self)
        self.__client.on_connect = Reader.on_connect
        self.__client.on_message = Reader.on_message

    def run(self):
        self.__client.loop_forever()

    def stop(self):
        for parser in self.__parsers:
            try:
                parser.stop()
            except:
                pass
        self.__client.disconnect()

    def on_connect(client, userdata, flags, rc):
        self = userdata
        self.__logger.info("connected")
        self.__client.subscribe("sdr/spectrogram/+/+")
        self.__client.subscribe("sdr/transmission/+/+")
        self.__client.subscribe("sdr/scheduler/+/+/get")
        self.__client.subscribe("sdr/gain_test/+/+/start")
        self.__client.subscribe("sdr/gain_test/+/+/stop")
        self.__client.subscribe("sdr/gain_test/+/+/get_status")

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
