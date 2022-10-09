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


# TODO: Jenkins: pass-fail criteria as related to Jenkins
# TODO: Jenkins: store results location
# TODO: Jenkins: token location

# TODO: configure multiple grids
# TODO: gracefully terminate flood
# TODO: monitor grip performance

""" Configure logger """
console = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s", "%H:%M:%S")
console.setFormatter(formatter)
LOG = logging.getLogger("")
LOG.addHandler(console)
LOG.setLevel(logging.INFO)


def signal_handler(signal, frame):
    """ handle Cntrl C """
    print("You pressed Ctrl+C!")
    sys.exit(0)


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


def load_yml(config_file):
    """ Load YAML file """
    try:
        with open(config_file, "r") as stream:
            return yaml.full_load(stream)
    except yaml.YAMLError as err:
        LOG.error(err)
        sys.exit(1)


def flood_files(files):
    """build flood files list, exit if any file is missing
    or have the wrong extensions
    """
    rl = []
    for f in files:
        if os.path.isfile(f) and f.lower().endswith((".jmx", ".csv", ".txt", ".dat")):
            rl.append(eval(f'("flood_files[]", open("{f}","rb"))'))
        else:
            LOG.error(f"File {f} not found or has the wrong extension. Bye")
            sys.exit(1)
    return rl


""" read flood API token """
FLOOD_API_TOKEN = get_token()

URL = "https://api.flood.io/floods"
# URL = 'https://api.flood.io/api/v3/floods'

""" Parse arguments """
parser = argparse.ArgumentParser()
parser.add_argument("ymlfile", help="Configuration file (yml) required")
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

if not os.path.isfile(args.ymlfile):
    LOG.error("Configuration file not found")
    sys.exit(1)

""" read yaml configuration file """
cnfg = load_yml(args.ymlfile)
LOG.info(f"Executing with config: {args.ymlfile}")

""" setting defaults """
cnfg.setdefault("provisioning", 6)  # the time it takes for grids to start
cnfg.setdefault("frequency", 30)  # elapse seconds between status reports

""" flood defaults """
cnfg.setdefault("tool", "jmeter")
cnfg.setdefault("privacy", "private")
cnfg.setdefault("rampup", 0)
cnfg.setdefault("grids", {}).setdefault("infrastructure", "demand")
cnfg.setdefault("grids", {}).setdefault("instance_type", "m5.xlarge")
cnfg.setdefault("grids", {}).setdefault("instance_quantity", 1)

LOG.debug(json.dumps(cnfg, indent=2))

""" define validation schema """
schema = {
    "project": {"required": True, "type": "string", "empty": False},
    "name": {"required": True, "type": "string", "empty": False},
    "threads": {"required": True, "type": "integer", "min": 1, "empty": False},
    "duration": {"required": True, "type": "integer", "min": 60, "empty": False},
    "grids": {
        "type": "dict",
        "schema": {
            "region": {"type": "string", "empty": False},
        },
    },
    "files": {
        "type": "list",
        "schema": {
            "required": True,
            "type": "string",
        },
    },
    "parameters": {
        "type": "list",
        "schema": {"type": "string", "regex": "^[\w._-]*=[ '//\w._,()-]*$"},
    },
}

v = Validator(schema, allow_unknown=True)
if v.validate(cnfg):
    LOG.info("Configuration file validated")
else:
    LOG.error(f"Configuration validation error: {v.errors}")
    sys.exit(1)

""" set up the stop_after """
cnfg["grids"]["stop_after"] = cnfg["duration"] / 60 + cnfg["provisioning"]

""" build POST flood command """
config = {
    "flood[tool]": cnfg["tool"],
    "flood[privacy]": cnfg["privacy"],
    "flood[project]": cnfg["project"],
    "flood[name]": cnfg["name"],
    "flood[threads]": cnfg["threads"],
    "flood[duration]": cnfg["duration"],  # seconds
    "flood[rampup]": cnfg["rampup"],  # seconds
    "flood[grids][][infrastructure]": cnfg["grids"]["infrastructure"],
    "flood[grids][][region]": cnfg["grids"]["region"],
    "flood[grids][][instance_quantity]": cnfg["grids"]["instance_quantity"],
    "flood[grids][][instance_type]": cnfg["grids"]["instance_type"],
    "flood[grids][][stop_after]": cnfg["grids"]["stop_after"],
}

""" add 'override parameters' if available """
if "parameters" in cnfg:
    config["flood[override_parameters]"] = " ".join(
        [f"-J{p}" for p in cnfg["parameters"]]
    )

LOG.debug(pprint(config))

""" build files """
files = flood_files(cnfg["files"])

LOG.debug(f"flood files {files}")

""" submit POST request """
try:
    r = requests.post(
        URL,
        files=files,
        data=config,
        auth=(f"{FLOOD_API_TOKEN}", ""),
    )
    r.raise_for_status()
except requests.exceptions.HTTPError as err:
    LOG.debug(f"Post response: {r.text}")
    LOG.error(err)
    sys.exit(1)
except requests.exceptions.RequestException as err:
    LOG.error(err)
    sys.exit(1)

LOG.debug(json.dumps(r.json(), indent=4, sort_keys=True))

""" extract flood information """
try:
    flood_uuid = json.loads(r.text)["uuid"]
except KeyError:
    LOG.err(json.loads(r.text))
    sys.exit(1)

LOG.info(f"Submitted Flood: {flood_uuid}")

""" wait for flood to finish """
while True:
    try:
        r = requests.get(URL + "/" + flood_uuid, auth=(f"{FLOOD_API_TOKEN}", ""))
    except requests.exceptions.RequestException as err:
        LOG.error(err)
        sys.exit(1)

    LOG.debug(json.dumps(r.json(), indent=4, sort_keys=True))

    LOG.info(f"{json.loads(r.text)['status']} ...")

    if json.loads(r.text)["status"] in ["finished", "stopped", "problem"]:
        break
    else:
        time.sleep(cnfg["frequency"])

LOG.debug(json.dumps(r.json(), indent=4, sort_keys=True))

flood_beg = json.loads(r.text)["started"]
flood_end = json.loads(r.text)["stopped"]

""" abort execution if status is not finished """
if json.loads(r.text)["status"] in ["stopped", "problem"]:
    LOG.error(f"Test was STOPPED at {flood_end}")
    sys.exit(1)

LOG.info(f"\nstarted: {flood_beg} - finished: {flood_end}")
LOG.info(f'\nTo share results "Enable Secret Link" https://app.flood.io/{flood_uuid}')

""" capture 'Archive Results' tar filename """
FILEURL = json.loads(r.text)["_embedded"]["archives"][0]["href"]
LOG.debug(FILEURL)

""" process 'Archive Results' tar file """
try:
    r = requests.get(FILEURL, stream=True)
except requests.exceptions.RequestException as err:
    LOG.error(err)
    sys.exit(1)
else:
    tar_fname = flood_uuid + ".tar.gz"
    try:
        with open(tar_fname, "wb") as ft:
            ft.write(r.raw.read())
    except Exception as err:
        LOG.error(err)
        sys.exit(1)
    else:
        """ create artifacts directory if it's configured """
        if artifacts_dir := cnfg.get("settings", {}).get("artifacts-dir"):
            os.makedirs(artifacts_dir, exist_ok=True)
            artifacts_dir = artifacts_dir + "/" + flood_uuid
        else:
            artifacts_dir = "flood-results"

        with tarfile.open(tar_fname) as ft:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner=numeric_owner) 
                
            
            safe_extract(ft, artifacts_dir)
        LOG.debug(f"Extracted {tar_fname} -> {artifacts_dir}")

        if os.path.isdir(artifacts_dir):
            """ save test input files """
            for f in cnfg["files"]:
                shutil.copy(f, artifacts_dir)
            """ relocate result files for easy access """
            for f in glob.glob(f"{artifacts_dir}/flood/results/*"):
                shutil.copy(f, artifacts_dir)

        """ store tar file and ymal file in tar_dir """
        shutil.move(tar_fname, f"{artifacts_dir}/flood")
        shutil.copy(args.ymlfile, artifacts_dir)

        LOG.info(f"Results directory: {artifacts_dir}")
