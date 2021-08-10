#!/usr/bin/env python

import json
import logging
import os
import sys

from jsonpath_ng import parse

import requests

""" Configure logger """
console = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s", "%H:%M:%S")
console.setFormatter(formatter)
LOG = logging.getLogger("")
LOG.addHandler(console)
LOG.setLevel(logging.INFO)

DEBUG = False


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

URL = "https://api.flood.io/floods/"

try:
    r = requests.get(URL, auth=(f"{FLOOD_API_TOKEN}", ""))
    r.raise_for_status()
except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

# load response into a dictionary
json_data = json.loads(r.text)

# create list of uuid's
uuid_jsonpath_expr = parse("*.floods[*].uuid")
uuid_list = [match.value for match in uuid_jsonpath_expr.find(json_data)]
DEBUG and print(uuid_list)

# create list of name's
name_jsonpath_expr = parse("*.floods[*].name")
name_list = [match.value for match in name_jsonpath_expr.find(json_data)]

# print values
for name, uuid in zip(name_list, uuid_list):
    print(f"{name} => {uuid}")
