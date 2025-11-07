from sdr.utils.gain_tester_thread import GainTesterThread
import json
import logging
import monitor.settings as settings
import re
import time


class GainTesterController:
    def __init__(self):
        self.__logger = logging.getLogger("GainController")
        self.__regex = re.compile("sdr/gain_test/(\\w+)/(\\w+)/(\\w+)")
        self.__threads = []

    def stop(self):
        for thread in self.__threads:
            thread.stop()
            thread.join()

    def __start(self, name, scanner, device, sample_rate, frequency_range, duration, gain_list):
        self.__stop(scanner, device)
        thread = GainTesterThread(settings.MQTT["url"], settings.MQTT["user"], settings.MQTT["password"], name, scanner, device, sample_rate, frequency_range, duration, gain_list)
        thread.start()
        self.__threads.append(thread)

    def __stop(self, scanner, device):
        for thread in self.__threads[:]:
            if thread.scanner() == scanner and thread.device() == device:
                thread.stop()
                thread.join()
                time.sleep(5)
                self.__threads.remove(thread)

    def __send_status(self, client, scanner, device, message):
        data = {"message": message}
        client.publish("sdr/gain_test/%s/%s/status" % (scanner, device), json.dumps(data))

    def on_message(self, client, message):
        topic = message.topic
        m = self.__regex.match(topic)
        if m:
            scanner = m.group(1)
            device = m.group(2)
            action = m.group(3)
            self.__logger.info(f"scanner: {scanner}, device: {device}, action: {action}")
            alert = "Do not change device configuration during test! Only one test can be performed at a time!"
            if action == "start":
                data = json.loads(message.payload.decode("utf-8"))
                self.__logger.info(f"data: {data}")
                self.__start(data["name"], scanner, device, data["sample_rate"], data["frequency_range"], data["duration"], data["gains"])
                client.publish("sdr/gain_test/%s/%s/ok" % (scanner, device))
                self.__send_status(client, scanner, device, f"Gain test started. {alert}")
            elif action == "stop":
                self.__stop(scanner, device)
                client.publish("sdr/gain_test/%s/%s/ok" % (scanner, device))
                self.__send_status(client, scanner, device, "Gain test stopped.")
            elif action == "get_status":
                threads = [t for t in self.__threads if (t.scanner() == scanner and t.device() == device)]
                if 0 < len(threads):
                    self.__send_status(client, scanner, device, f"Gain test is running. {alert}")
                else:
                    self.__send_status(client, scanner, device, "Gain test is not running.")
            self.__logger.info(f"number of active tests: {len(self.__threads)}")
            return True
        return False
