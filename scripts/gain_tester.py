#!/usr/bin/env python3

import argparse
import common.utils.mqtt
import copy
import datetime
import itertools
import json
import logging
import logging.config
import sys
import time

AMP_GAIN = list(range(0, 28, 14))
LNA_GAIN = list(range(0, 48, 8))
VGA_GAIN = list(range(0, 64, 2))
TUNER_GAIN = [0.0, 0.9, 1.4, 2.7, 3.7, 7.7, 8.7, 12.5, 14.4, 15.7, 16.6, 19.7, 20.7, 22.9, 25.4, 28.0, 29.7, 32.8, 33.8, 36.4, 37.2, 38.6, 40.2, 42.1, 43.4, 43.9, 44.5, 48.0, 49.6]


def get_device(config, device):
    for _device in config["devices"]:
        [driver, serial] = device.split("_")
        if _device["driver"] == driver and _device["serial"] == serial:
            return _device
    return None


def get_device_gains(config, device):
    return get_device(config, device)["gains"]


def update_config(logger, config, name, device, gains):
    alias = name
    for key in sorted(gains.keys()):
        if isinstance(gains[key], float):
            alias += f"_{key}{gains[key]*10:03.0f}"
        else:
            alias += f"_{key}{gains[key]:02d}"
    logger.debug(f"alias: {alias}")
    _device = get_device(config, device)
    _device["alias"] = alias
    for item in _device["gains"]:
        name = item["name"]
        if name in gains:
            item["value"] = gains[name]


def test_gains(logger, client, name, config, scanner, device, duration, gains):
    logger.info(f"run test: {gains}")
    update_config(logger, config, name, device, gains)
    logger.debug(f"test gains: {get_device_gains(config, device)}")
    client.send_and_get(f"sdr/config/{scanner}", f"sdr/config/{scanner}/success", json.dumps(config))
    time.sleep(duration.total_seconds())


def test_gain_list(logger, client, name, config, scanner, device, duration, gain_list):
    for gain_name, gain_values in gain_list:
        logger.info(f"gain: {gain_name}, values: {gain_values}")

    names = [name for name, _ in gain_list]
    value_lists = [vals for _, vals in gain_list]
    gains_combinations = [dict(zip(names, combo)) for combo in itertools.product(*value_lists)]
    total_duration = duration * len(gains_combinations)
    logger.info(f"total test duration : {total_duration}")
    for gains in gains_combinations:
        test_gains(logger, client, name, config, scanner, device, duration, gains)


def test(logger, client, name, scanner, device, duration, gain_list):
    config = client.send_and_get("sdr/list", f"sdr/status/{scanner}")
    config = json.loads(config)
    logger.info(f"scanner: {scanner}, device: {device}, single test duration: {duration} seconds")
    logger.info(f"current gains: {get_device_gains(config,device)}")
    try:
        test_gain_list(logger, client, name, copy.deepcopy(config), scanner, device, duration, gain_list)
    except KeyboardInterrupt:
        logger.warning("received stop signal")
        client.send_and_get(f"sdr/config/{scanner}", f"sdr/config/{scanner}/success", json.dumps(config))
        logger.info(f"restoring gains: {get_device_gains(config, device)}")


def main(*args):
    parser = argparse.ArgumentParser(description="Gain tester", formatter_class=lambda prog: argparse.ArgumentDefaultsHelpFormatter(prog, max_help_position=40))
    parser.add_argument("-v", "--verbose", action="count", default=0)
    parser.add_argument("-n", "--name", help="set test name", type=str, metavar="name", default=None)
    parser.add_argument("--mqtt_url", help="set mqtt url", type=str, required=True, metavar="url")
    parser.add_argument("--mqtt_user", help="set mqtt user", type=str, required=True, metavar="user")
    parser.add_argument("--mqtt_password", help="set mqtt password", type=str, required=True, metavar="password")
    parser.add_argument("-s", "--scanner", help="set scanner", type=str, required=True, metavar="scanner_id")
    parser.add_argument("-d", "--device", help="set device", type=str, required=True, metavar="device_id")
    parser.add_argument("--amp", help="set amp gain", type=int, nargs="+", metavar="g", default=AMP_GAIN)
    parser.add_argument("--lna", help="set lna gain", type=int, nargs="+", metavar="g", default=LNA_GAIN)
    parser.add_argument("--vga", help="set vga gain", type=int, nargs="+", metavar="g", default=VGA_GAIN)
    parser.add_argument("--tuner", help="set tuner gain", type=float, nargs="+", metavar="g", default=TUNER_GAIN)
    parser.add_argument("--duration", help="set singe test duration time", type=float, metavar="seconds", default=60)
    args = parser.parse_args()

    level = [logging.WARNING, logging.INFO, logging.DEBUG][min(args.verbose, 2)]
    logging.getLogger().setLevel(level)

    logger = logging.getLogger("Gain")
    with common.utils.mqtt.MqttSyncClient(args.mqtt_url, args.mqtt_user, args.mqtt_password, "gain-tester") as client:
        name = args.name or args.device
        if args.device.startswith("rtlsdr_"):
            test(logger, client, name, args.scanner, args.device, datetime.timedelta(seconds=args.duration), [("TUNER", args.tuner)])
        elif args.device.startswith("hackrf_"):
            test(logger, client, name, args.scanner, args.device, datetime.timedelta(seconds=args.duration), [("AMP", args.amp), ("LNA", args.lna), ("VGA", args.vga)])
        else:
            logger.warning("unknown device driver")


if __name__ == "__main__":
    with open("logging.json", "r") as f:
        logging.config.dictConfig(json.load(f))
    main(sys.argv)
