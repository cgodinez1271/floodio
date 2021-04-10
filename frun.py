#!/usr/bin/env python

import json
import requests
import argparse
import time
import sys
import yaml
import os
import tarfile
import cerberus  # 1.3.2
from cerberus import Validator
import logging
import time
import sys
import os
import glob
import shutil
from datetime import datetime

# TODO: configure multiple grids
# TODO: gracefully terminate flood
# TODO: customize token file location

"""
Configure logger
"""
console = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s: %(message)s",
                              "%H:%M:%S")
console.setFormatter(formatter)
LOG = logging.getLogger("")
LOG.addHandler(console)
LOG.setLevel(logging.INFO)


def signal_handler(signal, frame):
    print('You pressed Ctrl+C!')
    sys.exit(0)


def get_token(tf):
    """
    Read token from current location
    """
    try:
        with open(tf) as fd:
            return fd.read().strip('\n')
    except FileNotFoundError as err:
        LOG.error(err)
        sys.exit(1)


def load_yml(config_file):
    """
    Load YAML file
    """
    try:
        with open(config_file, 'r') as stream:
            return yaml.full_load(stream)
    except yaml.YAMLError as err:
        LOG.error(err)
        sys.exit(1)


# read flood API token
FLOOD_API_TOKEN = get_token('./.flood_token')

URL = 'https://api.flood.io/floods'
# URL = 'https://api.flood.io/api/v3/floods'

"""
Parse arguments
"""
parser = argparse.ArgumentParser()
parser.add_argument("ymlfile",
                    help="Configuration file (yml) required"),
parser.add_argument('--frequency', '-f',
                    default=30,
                    type=int,
                    help="Reporting frequency (default: %(default)d secs)")
parser.add_argument('--provision', '-p',
                    default=5,
                    type=int,
                    help="Provision delay (default: %(default)d mins)")
args = parser.parse_args()

if not os.path.isfile(args.ymlfile):
    LOG.error('Configuration file not found')
    sys.exit(1)

# read yaml configuration file
cnfg = load_yml(args.ymlfile)
LOG.info(f'Executing with config: {args.ymlfile}')

# set some defaultso
cnfg.setdefault('tool', 'jmeter')
cnfg.setdefault('privacy', 'private')
cnfg.setdefault('rampup', 0)
cnfg.setdefault('grids', {}).setdefault('infrastructure', 'demand')
cnfg.setdefault('grids', {}).setdefault('instance_type', 'm5.xlarge')
cnfg.setdefault('grids', {}).setdefault('instance_quantity', 1)
# leap of faith: assume the duration is available
if 'stop_after' not in cnfg and 'duration' in cnfg:
    cnfg['grids']['stop_after'] = cnfg['duration'] / 60 + args.provision

LOG.debug(json.dumps(cnfg, indent=2))

# define validation schema
schema = {
    'project': {'required': True, 'type': 'string', 'empty': False},
    'name': {'required': True, 'type': 'string', 'empty': False},
    'threads': {'required': True, 'type': 'integer', 'min': 1, 'empty': False},
    'duration': {'required': True, 'type': 'integer', 'min': 60, 'empty': False},
    'grids': {
        'type': 'dict',
        'schema': {
            'region': {'type': 'string', 'empty': False},
        }
    },
    'flood_files': {
        'type': 'list',
        'schema': {'required': True, 'type': 'string', 'regex': '^\w*\.(jmx|csv|zip)$'}
    },
    'override_parameters': {
        'type': 'list',
        'schema': {'type': 'string', 'regex': '^(J|D)\w*=\w*$'}
    }
}

v = Validator(schema, allow_unknown=True)
if v.validate(cnfg):
    LOG.info('Configuration file validated')
else:
    LOG.error(f'Configuration validation error: {v.errors}')
    sys.exit(1)

# build POST flood command
config = {
    'flood[tool]': cnfg['tool'],
    'flood[privacy]': cnfg['privacy'],
    'flood[project]': cnfg['project'],
    'flood[name]': cnfg['name'],
    'flood[threads]': cnfg['threads'],
    'flood[duration]': cnfg['duration'],  # seconds
    'flood[rampup]': cnfg['rampup'],  # seconds
    'flood[grids][][infrastructure]': cnfg['grids']['infrastructure'],
    'flood[grids][][region]': cnfg['grids']['region'],
    'flood[grids][][instance_quantity]': cnfg['grids']['instance_quantity'],
    'flood[grids][][instance_type]': cnfg['grids']['instance_type'],
    'flood[grids][][stop_after]': cnfg['grids']['stop_after']
}

# add 'override parameters' if available
if 'override_parameters' in cnfg:
    config['flood[override_parameters]'] = ' '.join(
        [f'-{p}' for p in cnfg['override_parameters']])

LOG.debug(json.dumps(config, indent=2))

# add 'flood_files'
files = [eval(f'("flood_files[]", open("{f}","rb"))')
         for f in cnfg['flood_files']]

try:
    r = requests.post(URL, files=files, data=config,
                      auth=(f'{FLOOD_API_TOKEN}', ''))
except requests.exceptions.RequestException as err:
    LOG.error(err)
    sys.exit(1)

LOG.debug(json.dumps(r.json(), indent=4, sort_keys=True))

# extract flood uuid status
flood_uuid = json.loads(r.text)['uuid']
flood_beg = json.loads(r.text)['started']
LOG.info(f'Submitted Flood {flood_uuid}')

# wait for flood to finish
while True:
    try:
        r = requests.get(URL + '/' + flood_uuid,
                         auth=(f'{FLOOD_API_TOKEN}', ''))
    except requests.exceptions.RequestException as err:
        LOG.error(err)
        sys.exit(1)

    LOG.debug(json.dumps(r.json(), indent=4, sort_keys=True))
    LOG.info(json.loads(r.text)['status'])

    if json.loads(r.text)['status'] in ['finished', 'stopped']:
        break
    else:
        time.sleep(args.frequency)

LOG.debug(json.dumps(r.json(), indent=4, sort_keys=True))

flood_beg = json.loads(r.text)['started']
flood_end = json.loads(r.text)['stopped']

if json.loads(r.text)['status'] == 'stopped':
    LOG.error(f'Test was STOPPED at {flood_end}')
    sys.exit(1)

LOG.info(f'\nstarted: {flood_beg} - finished: {flood_end}')
LOG.info(
    f'\nTo share results "Enable Secret Link" https://app.flood.io/{flood_uuid}')

# capture 'Archive Results' tar filename
FILEURL = json.loads(r.text)['_embedded']['archives'][0]['href']
LOG.debug(FILEURL)

# process 'Archive Results' tar file
try:
    r = requests.get(FILEURL, stream=True)
except requests.exceptions.RequestException as err:
    LOG.error(err)
    sys.exit(1)
else:
    # local destinantion file
    tar_fname = flood_uuid + '.tar.gz'
    try:
        with open(tar_fname, 'wb') as ft:
            ft.write(r.raw.read())
    except Exception as err:
        LOG.error(err)
        sys.exit(1)
    else:
        tar_dir = datetime.now().strftime('%Y-%m-%d_%H-%M-%S.%f')
        with tarfile.open(tar_fname) as ft:
            ft.extractall(tar_dir)
        LOG.info(f'Extracted {tar_fname} -> {tar_dir}')

        # relocate files for easy access
        if os.path.isdir(tar_dir):
            for f in glob.glob(f'{tar_dir}/flood/files/*'):
                shutil.copy(f, tar_dir)
            for f in glob.glob(f'{tar_dir}/flood/results/*'):
                shutil.copy(f, tar_dir)

        # store tar file and ymal file
        shutil.move(tar_fname, f'{tar_dir}/flood')
        shutil.copy(args.ymlfile, tar_dir)

        LOG.info(f'Results directory: {tar_dir}')
