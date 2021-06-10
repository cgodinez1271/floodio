# Support scripts for Flood.io

## Purpose

Flood.io CLI scripts.

## Requirements

1. A Flood.io account (https://www.flood.io/)
2. The Flood API **access token** stored in a file named **.flood_token**

## frun.py

This script executes a test in the Flood.io cloud

```
./frun.py basic.yml
```

NOTE: this script uses basic.jmx and basic.csv

## fuuids.py

This script identifies the **flood uuids** and the test-names associated to the Flood token.

```
./flood_uuids.py
```

## fresults.py

This script downloads files associated to a *flood uuid*.

```
./fresults.py <flood_uuid>
```

## freport.py

This script downloads test results associated to a *flood uuid*.

```
./freport.py <flood_uuid>
```

These scripts was designed to be executed on MacOS and Python 3.8.

## Disclaimer

This script come without warranty of any kind. Use them at your own risk. I assume no liability for the accuracy, correctness, completeness, or usefulness of any information provided by this site nor for any sort of damages using these scripts may cause.

Linkedin: https://www.linkedin.com/in/carlosgodinez/

Web: https://jemeterenespanol.com

