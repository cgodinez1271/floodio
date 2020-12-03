# Support scripts for Flood.io

## Purpose

Two scripts to download the JMeter **jtl** file which is not available by default. These scripts are built using the Flood API V2. See the the documentation [here](https://github.com/flood-io/api-docs).

## Pre-requisites

Using these scripts have 3 pre-requisites:

1. An Flood.io account
2. A Flood API access token. Add this token to a file name **.flood_token**
3. Including the **Simple Data Writer** listener to the JMeter test plan. Set the *filename* to "/data/flood/results/results_${__time(MM-dd-yyyy-HH-mm-ss,)}.jtl" to the file does not overwritten.

## flood_uuid.py

This script identifies the flood uuids and the test names associated to the Flood token.

```
1kVxMpJ4z9zIckMGrZlcHJBh1S1 => Demo Flood - JMeter
1kVxMszXLAdEfOsxRj4QuUqg7ql => Demo Flood - Element
```
## get_jtl_file.py

This script downloads the *tar.gz* file associated to a flood uuid, and extracts the **jtl** file into a directory flood directory.

```
tree flood 

flood
└── results
    └── results_12-03-2020-17-57-41.jtl

1 directory, 1 file
```

The last step is to upload the '.jtl' file into the JMeter GUI to visualize the results using any of the graphing listener or create the HTML report.

Linkedin: https://www.linkedin.com/in/carlosgodinez/
Web: https://jemeterenespanol.com
