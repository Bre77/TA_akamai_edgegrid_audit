#!/bin/bash
cd "${0%/*}"
OUTPUT="${1:-TA_akamai_edgegrid_audit.spl}"
chmod -R u=rwX,go= *
chmod -R u-x+X *
chmod -R u=rwx,go= bin/*
rm -rf lib/splunk*
python3.9 -m pip install --upgrade -t lib -r lib/requirements.txt --no-dependencies
rm -rf lib/*/__pycache__
rm -rf lib/*/*/__pycache__
cd ..
tar -cpzf $OUTPUT --exclude=.* --overwrite TA_akamai_edgegrid_audit
