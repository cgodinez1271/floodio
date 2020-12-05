#!/usr/bin/env python

import json
import requests
from jsonpath_ng import jsonpath, parse


def get_token(tf):
    try:
        with open(tf) as fd:
            return fd.read().strip('\n')
    except FileNotFoundError as err:
        raise SystemExit(err)


# read flood API token
FLOOD_API_TOKEN = get_token('./.flood_token')

URL = 'https://api.flood.io/floods/'

try:
    r = requests.get(URL, auth=(f'{FLOOD_API_TOKEN}', ''))
    r.raise_for_status()
except requests.exceptions.HTTPError as err:
    raise SystemExit(err)

# load response into a dictionary
json_data = json.loads(r.text)

# create list of uuid's
uuid_jsonpath_expr = parse('*.floods[*].uuid')
uuid_list = [match.value for match in uuid_jsonpath_expr.find(json_data)]

# create list of name's
name_jsonpath_expr = parse('*.floods[*].name')
name_list = [match.value for match in name_jsonpath_expr.find(json_data)]

# build dictionary using zip()
name_uuid = dict(zip(name_list, uuid_list))

# print dictionary
for key, value in name_uuid.items():
    print(f'{value} => {key}')

