#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import json
import argparse


def read_json_file_to_dict(file):
    if not os.path.isfile(file):
        msg = "Unable to find json file %s" % file
        print(f"ERROR: {msg}")
        return False, msg

    with open(file) as f:
        json_data = f.read()

    try:
        result_dict = json.loads(json_data)  # OK

    except Exception as e:
        print(e)
        return False, e

    return True, result_dict


def parse_args():
    """
    :return: args
    """
    epilog = """
Usage examples:
    python3 prism_result_scan.py --result ./public/result/state/result_5e63895a-a5d8-47f9-a89c-cf669173bd16.json 

    """
    parser = argparse.ArgumentParser(description='prism_result_scan',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-r", "--result",
                        dest="result",
                        action="store",
                        required=True,
                        help="Path to result file to scan")

    args = parser.parse_args()
    return args


def scan_result_file(f):
    success, result = read_json_file_to_dict(f)
    if not success:
        print(f"ERROR: Failed to read result file: {f}")
        return 1

    try:
        # the result records could have been created by prism_dev or
        # by the Prism GUI, which have a slightly different layout,
        # accommodate either
        if "payload" in result:
            items = result["payload"]["result"]["items"]
        else:
            items = result["result"]["items"]

    except Exception as e:
        # this should never happen
        print(f"ERROR: {e}")
        return 1

    measurement_keys = []
    for item in items:
        for m in item["measurements"]:
            measurement_keys.append(m["name"])

    # scan for dups
    duplicates = False
    while measurement_keys:
        key = measurement_keys.pop(0)
        if key in measurement_keys:
            print(f"{key} <--- DUPLICATE")
            duplicates = True
        else:
            print(f"{key}")

    if not duplicates:
        print()
        print("Success!! There are no duplicate keys")



def main():
    """ Script to list all the measurement keys found in a result record
    and report if there are any duplicates.

    :return: 0 on success, non-zero on error
    """
    args = parse_args()
    scan_result_file(args.result)


if __name__ == "__main__":
    retcode = main()
    sys.exit(retcode)

