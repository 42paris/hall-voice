#!/bin/bash

#
# EXECUTION TIME IS VERY LONG
#

# Create json file with every MP3 files
find $PWD/mp3/ -iname "*.mp3" -type f | jq -R '.' | jq -s . > everymp3.json

# Sanitize
python3 $PWD/sanitize.py -v --db -12.0 -- everymp3.json

# Delete json file
rm everymp3.json