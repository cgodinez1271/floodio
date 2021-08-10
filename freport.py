#!/usr/bin/env python

import argparse
import glob
import json
import logging
import os
import shutil
import sys
import tarfile
import time
from pprint import pprint

from cerberus import Validator

import requests

import yaml

# logging configuration
console = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s", "%H:%M:%S")
console.setFormatter(formatter)
LOG = logging.getLogger("")
LOG.addHandler(console)
LOG.setLevel(logging.INFO)


def get_token():
    """ Read token homedir """
    home = os.path.expanduser("~")

    if os.path.isfile(f"{home}/.fzt-rc"):
        tf = f"{home}/.fzt-rc"
    else:
        tf = "./.fzt-rc"

    try:
        with open(tf) as fd:
            return fd.read().strip("\n")
    except OSError as err:
        LOG.error(err)
        sys.exit(1)


# read flood API token
FLOOD_API_TOKEN = get_token()

# parse argument uuid
parser = argparse.ArgumentParser()
parser.add_argument("uuid", help="Enter flood uuid")
parser.add_argument(
    "-d",
    "--debug",
    help="Print debugging statements",
    action="store_true",
)
args = parser.parse_args()

if args.debug:
    LOG.setLevel(logging.DEBUG)

# build URL using uuid
# URL='https://api.flood.io/floods/' + args.uuid
URL = "https://api.flood.io/floods/" + args.uuid + "/report"

try:
    r = requests.get(URL, auth=(f"{FLOOD_API_TOKEN}", ""))
except requests.exceptions.RequestException as err:
    LOG.error(err)
    sys.exit(1)

LOG.debug(json.dumps(r.json(), indent=4, sort_keys=True))

LOG.info(f"\n{json.loads(r.text)['summary']}")
