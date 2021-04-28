#!/usr/bin/env python

import json
import requests
import urllib.request
import tarfile
from jsonpath_ng import jsonpath, parse
import argparse
import logging
import time
import sys
import os
import glob
import shutil

# logging configuration
console = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s",
                              "%H:%M:%S")
console.setFormatter(formatter)
LOG = logging.getLogger("")
LOG.addHandler(console)
LOG.setLevel(logging.INFO)


def get_token(tf):
    try:
        with open(tf) as fd:
            return fd.read().rstrip('\n')
    except FileNotFoundError as err:
        LOG.error(err)
        sys.exit(1)


# read flood API token
FLOOD_API_TOKEN = get_token("./.flood_token")

# parse argument uuid
parser = argparse.ArgumentParser()
parser.add_argument("uuid", help="Enter flood uuid")
parser.add_argument('-d', '--debug',
                    help="Print debugging statements",
                    action="store_true",
                    )
args = parser.parse_args()

if args.debug:
    LOG.setLevel(logging.DEBUG)

# build URL using uuid
# URL='https://api.flood.io/floods/' + args.uuid
URL = 'https://api.flood.io/floods/' + args.uuid + '/report'

try:
    r = requests.get(URL, auth=(f'{FLOOD_API_TOKEN}', ''))
except requests.exceptions.RequestException as err:
    LOG.error(err)
    sys.exit(1)

LOG.debug(json.dumps(r.json(), indent=4, sort_keys=True))

LOG.info(f"\n{json.loads(r.text)['summary']}")
