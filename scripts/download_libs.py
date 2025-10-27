from urllib.parse import urlparse
import argparse
import json
import logging
import os
import requests
import shlex


def run(*args):
    parser = argparse.ArgumentParser(description="Download libs")
    parser.add_argument("-c", "--config", help="path to config file", type=str, metavar="file", required=True)
    parser.add_argument("-o", "--output", help="path to output directory", type=str, metavar="dir", required=True)
    args = parser.parse_args(shlex.split(args[0] if len(args) else ""))

    logger = logging.getLogger("Libs")
    logger.setLevel(logging.INFO)
    os.makedirs(args.output, exist_ok=True)
    with open(args.config, "r") as f:
        for lib in json.load(f):
            url = lib["url"]
            filename = os.path.basename(urlparse(url).path)
            dest_path = os.path.join(args.output, lib["dir"], filename)

            if os.path.exists(dest_path):
                logger.info("already exists: %s" % url)
            else:
                logger.info("downloading: %s" % url)
                r = requests.get(url)
                r.raise_for_status()

                os.makedirs(os.path.join(args.output, lib["dir"]), exist_ok=True)
                with open(dest_path, "wb") as f:
                    f.write(r.content)

                logger.info("saved: %s to %s" % (url, dest_path))
