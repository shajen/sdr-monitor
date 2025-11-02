import logging
import re
import json
import sdr.utils.satellites


class SatellitesManager:
    def __init__(self):
        self.__logger = logging.getLogger("Satellites")
        self.__satellites_regex = re.compile("sdr/satellites/(\\w+)/(\\w+)/get")

    def on_message(self, client, message):
        topic = message.topic
        m = self.__satellites_regex.match(topic)
        if m:
            scanner = m.group(1)
            device = m.group(2)
            query = json.loads(message.payload.decode("utf-8"))
            self.__logger.info("get satellites query, scanner: %s, device: %s, satellites: %s" % (scanner, device, len(query["satellites"])))
            reader = sdr.utils.satellites.SatellitesFlightReader(query["api_key"], query["latitude"], query["longitude"], query["altitude"], True)
            flights = reader.get_visible_satellites_flights(query["satellites"], True)
            client.publish("sdr/satellites/%s/%s/set" % (scanner, device), json.dumps(flights))
            return True
        return False
