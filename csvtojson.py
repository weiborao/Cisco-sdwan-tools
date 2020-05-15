#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Convert CSV file to JSON file.

import json
import csv
import sys
from collections import OrderedDict

def write_json(data, json_file):
    with open(json_file, "w") as f:
        f.write(json.dumps(data, sort_keys=False, indent=4, separators=(
            ',', ': '), encoding="utf-8", ensure_ascii=False))

def csv_json(file):

    with open(file) as csvfile:
        reader = csv.DictReader(csvfile)
        # title = reader.fieldnames
        for row in reader:

            json_file = row["csv-deviceId"] + ".json"
            if '/' in json_file:
                json_file = json_file.replace('/', '_')
            write_json(row, json_file)

if __name__ == "__main__":
    help_msg = '''\nUsage: 
            Export the Template CSV file and save to example.csv

            python3 csvtojson.py example.csv 
            
            The output file would be json file, and named with device SN.\n'''

    if len(sys.argv) < 2:
        print(help_msg)
        sys.exit(0)
    else:
        csvfile = sys.argv[1]

    csv_json(csvfile)
