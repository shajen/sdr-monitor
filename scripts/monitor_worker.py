from sdr.utils.cleaner import Cleaner
from sdr.utils.reader import Reader
import argparse
import logging
import monitor.settings as settings
import shlex
import time


def run(*args):
    parser = argparse.ArgumentParser(description="Set worker config")
    parser.add_argument("-r", "--reader", help="enable reader", action="store_true")
    parser.add_argument("-clr", "--cleaner", help="enable cleaner", action="store_true")
    parser.add_argument("-cls", "--classifier", help="enable classifier", action="store_true")
    args = parser.parse_args(shlex.split(args[0] if len(args) else ""))

    threads = []
    if args.reader:
        threads.append(Reader(settings.MQTT))
    if args.cleaner:
        threads.append(Cleaner())
    if args.classifier:
        try:
            from sdr.utils.classifier import Classifier

            threads.append(Classifier())
        except Exception as e:
            logging.getLogger("Worker").warning("exception: %s" % e)

    for t in threads:
        t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for t in threads:
            t.stop()

    for t in threads:
        t.join()
