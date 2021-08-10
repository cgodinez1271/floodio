#!/usr/bin/env python

import argparse
import glob
import json
import logging
import os
import shutil
import sys
import tarfile

import requests

""" Configure logger """
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

""" set debug level per cli argument """
if args.debug:
    LOG.setLevel(logging.DEBUG)

# build URL using uuid
URL = "https://api.flood.io/floods/" + args.uuid

try:
    r = requests.get(URL, auth=(f"{FLOOD_API_TOKEN}", ""))
except requests.exceptions.RequestException as err:
    LOG.error(err)
    sys.exit(1)

LOG.debug(json.dumps(r.json(), indent=4, sort_keys=True))

# capture 'Archive Results' tar file name
FILEURL = json.loads(r.text)["_embedded"]["archives"][0]["href"]

LOG.debug(FILEURL)

# process 'Archive Results' tar file
try:
    r = requests.get(FILEURL, stream=True)
except requests.exceptions.RequestException as err:
    LOG.error(err)
    sys.exit(1)
else:
    # local destinantion file
    tar_fname = args.uuid + ".tar.gz"
    try:
        with open(tar_fname, "wb") as ft:
            ft.write(r.raw.read())
    except Exception as err:
        LOG.error(err)
        sys.exit(1)
    else:
        artifacts_dir = "flood-results"

        with tarfile.open(tar_fname) as ft:
            ft.extractall(artifacts_dir)
        LOG.info(f"Extracted {tar_fname} -> {artifacts_dir}")

        # relocate results file
        if os.path.isdir(artifacts_dir):
            for f in glob.glob(f"{artifacts_dir}/flood/results/*"):
                shutil.copy(f, artifacts_dir)
        # store tar file
        shutil.move(tar_fname, f"{artifacts_dir}/flood")

        LOG.info(f"Results files: {artifacts_dir}")
