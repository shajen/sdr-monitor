import crontab
import datetime
import json
import logging
import re
import sdr.utils.satellites


class Scheduler:
    def __init__(self):
        self.__logger = logging.getLogger("Scheduler")
        self.__regex = re.compile("sdr/scheduler/(\\w+)/(\\w+)/get")

    def __get_expression_execution_times(self, expression, duration):
        init_datetime = datetime.datetime.now().astimezone()
        last_datetime = init_datetime
        cron = crontab.CronTab(expression)
        execution_times = []
        execution_times.append(cron.previous(last_datetime, default_utc=False, return_datetime=True))
        while last_datetime <= init_datetime + duration:
            last_datetime = cron.next(last_datetime, default_utc=False, return_datetime=True)
            execution_times.append(last_datetime)
            last_datetime += datetime.timedelta(seconds=1)
        return execution_times

    def __get_crontab_scheduled_transmissions(self, query):
        crontabs = query["crontabs"]
        self.__logger.info("crontabs: %s" % (len(crontabs)))
        scheduled_transmissions = []
        for crontab in crontabs:
            self.__logger.info(f"processing crontab, name: {crontab['name']}, expression: {crontab['expression']}")
            for dt in self.__get_expression_execution_times(crontab["expression"], datetime.timedelta(minutes=90)):
                scheduled_transmissions.append(
                    {
                        "name": crontab["name"],
                        "begin": int(dt.timestamp()),
                        "end": int((dt + datetime.timedelta(seconds=crontab["duration"])).timestamp()),
                        "frequency": crontab["frequency"],
                        "bandwidth": crontab["bandwidth"],
                        "modulation": crontab["modulation"],
                    }
                )
        return scheduled_transmissions

    def __get_satellite_scheduled_transmissions(self, query):
        self.__logger.info("satellites: %s" % (len(query["satellites"])))
        reader = sdr.utils.satellites.SatellitesFlightReader(query["latitude"], query["longitude"], query["altitude"], True)
        return reader.get_visible_satellites_flights(query["satellites"], True)

    def on_message(self, client, message):
        topic = message.topic
        m = self.__regex.match(topic)
        if m:
            scanner = m.group(1)
            device = m.group(2)
            self.__logger.info("get query")
            query = json.loads(message.payload.decode("utf-8"))
            scheduled_transmissions = self.__get_crontab_scheduled_transmissions(query)
            scheduled_transmissions += self.__get_satellite_scheduled_transmissions(query)
            scheduled_transmissions.sort(key=lambda value: value["begin"])
            client.publish("sdr/scheduler/%s/%s/set" % (scanner, device), json.dumps(scheduled_transmissions))
            return True
        return False
