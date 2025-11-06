import common.utils.mqtt
import copy
import datetime
import itertools
import json
import logging
import threading
import time


class GainTesterThread(threading.Thread):
    def __init__(self, mqtt_url, mqtt_user, mqtt_password, alias, scanner, device, sample_rate, frequency_range, duration, gain_list):
        super().__init__()
        self.__logger = logging.getLogger("GainThread")
        self.__stop_event = threading.Event()
        self.__client = common.utils.mqtt.MqttSyncClient(mqtt_url, mqtt_user, mqtt_password, "gain-tester")
        self.__alias = alias or device
        self.__scanner = scanner
        self.__device = device
        self.__sample_rate = sample_rate
        self.__frequency_range = frequency_range
        self.__duration = datetime.timedelta(seconds=duration)
        self.__gain_list = gain_list

    def scanner(self):
        return self.__scanner

    def device(self):
        return self.__device

    def __get_device(self, config):
        for _device in config["devices"]:
            [driver, serial] = self.__device.split("_")
            if _device["driver"] == driver and _device["serial"] == serial:
                return _device
        return None

    def __get_device_gains(self, config):
        return self.__get_device(config)["gains"]

    def __update_config(self, config, gains):
        config["crontabs"] = []
        config["satellites"] = []
        alias = self.__alias
        for key in sorted(gains.keys()):
            if isinstance(gains[key], float):
                alias += f"_{key}{gains[key]*10:03.0f}"
            else:
                alias += f"_{key}{gains[key]:02d}"
        self.__logger.debug(f"alias: {alias}")
        _device = self.__get_device(config)
        _device["alias"] = alias
        _device["sample_rate"] = self.__sample_rate
        _device["ranges"] = [self.__frequency_range]
        for item in _device["gains"]:
            name = item["name"]
            if name in gains:
                item["value"] = gains[name]

    def __wait(self):
        start_time = time.time()
        while datetime.timedelta(seconds=time.time() - start_time) <= self.__duration and not self.__stop_event.is_set():
            time.sleep(0.1)

    def __test_gains(self, config, gains):
        self.__logger.info(f"run test: {gains}")
        self.__update_config(config, gains)
        self.__logger.debug(f"test gains: {self.__get_device_gains(config)}")
        self.__client.send_and_get(f"sdr/config/{self.__scanner}", f"sdr/config/{self.__scanner}/success", json.dumps(config))
        self.__wait()

    def __test_gain_list(self, config):
        for gain_name, gain_values in self.__gain_list.items():
            self.__logger.info(f"gain: {gain_name}, values: {gain_values}")

        for gain in self.__get_device_gains(config):
            if gain["name"] not in self.__gain_list:
                self.__gain_list[gain["name"]] = gain["options"]
        gains = self.__gain_list.items()
        names = [name for name, _ in gains]
        value_lists = [vals for _, vals in gains]
        gains_combinations = [dict(zip(names, combo)) for combo in itertools.product(*value_lists)]
        total_duration = self.__duration * len(gains_combinations)
        end_time = datetime.datetime.now().replace(microsecond=0) + total_duration
        self.__logger.info(f"total duration: {total_duration}, finish at: {end_time}")
        for gains in gains_combinations:
            if self.__stop_event.is_set():
                break
            self.__test_gains(config, gains)

    def run(self):
        self.__logger.info("started")
        self.__client.start()
        config = self.__client.send_and_get("sdr/list", f"sdr/status/{self.__scanner}")
        config = json.loads(config)
        self.__logger.info(
            f"scanner: {self.__scanner}, device: {self.__device}, alias: {self.__alias}, sample rate: {self.__sample_rate}, range: {self.__frequency_range}, single test duration: {self.__duration} seconds"
        )
        self.__test_gain_list(copy.deepcopy(config))
        self.__client.send_and_get(f"sdr/config/{self.__scanner}", f"sdr/config/{self.__scanner}/success", json.dumps(config))
        self.__logger.info(f"restoring original config")
        time.sleep(1)
        self.__client.stop()
        self.__logger.info("stopped")

    def stop(self):
        self.__logger.warning("received stop signal")
        self.__stop_event.set()
