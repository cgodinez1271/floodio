#!/usr/bin/env python

import json
import requests
import urllib.request
import tarfile
from jsonpath_ng import jsonpath, parse
import argparse


def get_token(tf):
    try:
        with open(tf) as fd:
            return fd.read().rstrip('\n')
    except FileNotFoundError as err:
        raise SystemExit(err)


# read flood API token
FLOOD_API_TOKEN = get_token("./.flood_token")

# parse argument uuid
parser = argparse.ArgumentParser()
parser.add_argument("uuid", help="enter flood uuid")
args = parser.parse_args()

# build URL using uuid
URL = 'https://api.flood.io/floods/' + args.uuid + '/archives'

try:
    r = requests.get(URL, auth=(f'{FLOOD_API_TOKEN}', ''))
    r.raise_for_status()
except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

# use the json module to load response
json_data = json.loads(r.text)

# extract gz.tar file URL
jsonpath_expr = parse('*.archives[*].href')
archive_url = jsonpath_expr.find(json_data)

# extract gz.tar filename
fname = archive_url[0].value.split("/")[-1]

# download tar.gz file
print(f'Downloading {archive_url[0].value}')
urllib.request.urlretrieve(archive_url[0].value, fname)

# extract jtl file if any
if fname.endswith("tar.gz"):
    t = tarfile.open(fname, "r:gz")
    for member in t.getmembers():
        if ".jtl" in member.name:
            print(f'Extracting {member.name}')
            t.extract(member, path=".")
    t.close()

# TODO: what if the 'results.jtl' files does not exist?
# TODO: remove tar.gz file?
