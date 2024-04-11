#!/bin/bash
cd "${0%/*}"
OUTPUT="${1:-TA_akamai_edgegrid_audit.spl}"
chmod -R u=rwX,go= *
chmod -R u-x+X *
chmod -R u=rwx,go= *
python3 -m pip install --upgrade -t lib -r lib/requirements.txt --no-dependencies
rm -rf lib/splunklib/__pycache__
rm -rf lib/splunklib/searchcommands/__pycache__
rm -rf lib/splunklib/modularinput/__pycache__
rm -rf lib/*/__pycache__
tar -cpzf $OUTPUT --exclude=.* --overwrite ../TA_akamai_edgegrid_audit 