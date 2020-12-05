# Support scripts for Flood.io

## Purpose

Two scripts to download the JMeter **jtl** file which is not available by default. These scripts are built using the Flood API V2. See the vendor documentation [here](https://github.com/flood-io/api-docs). The '.jtl' file is created by adding a listener to the JMeter test plan.

## Requirements

1. A Flood.io account (https://www.flood.io/)
2. A Flood API access token stored in a file named **.flood_token**
3. Adding the **Simple Data Writer** listener to the JMeter test plan. Set the *filename* to "/data/flood/results/results_${__time(MM-dd-yyyy-HH-mm-ss,)}.jtl" (so the file does not overwritten).

## flood_uuids.py

This script identifies the **flood uuids** and the test-names associated to the Flood token.

```
./flood_uuids.py

1l9n5tWn01zd1REd16zPBUbwaR3 => Demo Flood - JMeter
1kVxMszXLAdEfOsxRj4QuUqg7ql => Demo Flood - Element
```
## extract_jtl.py

This script downloads the *tar.gz* file associated to a *flood uuid*: 

```
./extract_jtl.py 1l9n5tWn01zd1REd16zPBUbwaR3

Downloading https://flood-archives.s3-accelerate.amazonaws.com/1l9n5tWn-pRCq6vs7-0.tar.gz
Extracting flood/results/results_12-03-2020-17-57-41.jtl
```

Extracts the **jtl** file into a directory:

```
tree flood

flood
└── results
    └── results_12-03-2020-17-57-41.jtl

1 directory, 1 file
```

## Using the '.jtl' file

The '.jtl' file can be used in 2 ways:

1. load the file into JMeter GUI to visualize the results using any of the graphing listener
2. create the HTML report

## Note

This script was designed to be executed on MacOS and Python 3.8.

## Disclaimer

This script come without warranty of any kind. Use them at your own risk. I assume no liability for the accuracy, correctness, completeness, or usefulness of any information provided by this site nor for any sort of damages using these scripts may cause.

Linkedin: https://www.linkedin.com/in/carlosgodinez/

Web: https://jemeterenespanol.com

