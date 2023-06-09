#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2023
Martin Guthrie

This is a helper script to test scripts that contain substitutions.
Normally CLI prism_dev.py will not run a script with substitutions.
Use this script to process a script that has substitutions and save
a new script that has processed substitutions.

NOTE: the substitutions must be "set" within this script below.
      See the # !! MODIFY !! section line ~150

"""
import os
import re
import json
import jstyleson
import argparse

import logging
logger = logging.getLogger("subs")


SCRIPT_REPLACE_RE = r'\"%%.*?\"'   # "%%Text"


def find_sub_items(script_text):
    """ find items in the script text that are marked for substitution from user input
    The format of fields to be found is "%%Text"
    :param script_text:
    :return: a dict of items to be replaced in script
    """
    matches = re.finditer(SCRIPT_REPLACE_RE, script_text, re.MULTILINE)
    items = [item.group() for item in matches]
    return list(dict.fromkeys(items))  # removes duplicates


def find_sub_items_replace(script_text, replacements):
    """  Replace '%%Name' items in script from replacements

    - replacements that are of type "num", also need to remove surrounding quotes,
      a bit of a hack to do it here, but thats where we are...

    :param script_text:
    :param replacements: list of replacement dicts, [{'Lot': '12345'}, ...]
    :return:
    """
    script = jstyleson.loads(script_text)
    script_subs = script.pop("subs", {})
    logger.debug(script_subs)
    logger.info(replacements)

    def _sub_replace(k, v, t):
        #  In order to do the subs correctly, we need to know if the sub is
        #  a string or a num, to know whether the quotes ("") should be removed or not.
        if t == "num":
            return script_text.replace('"%%{}"'.format(k), str(v))
        else:
            return script_text.replace("%%{}".format(k), str(v))

    for r in replacements:
        for k, v in r.items():

            if k not in script_subs:
                logger.error(f"{k} not in script subs")
                return None

            if not isinstance(v, str):
                logger.error(f"sub {k} value {v} must be a string")
                return None

            logger.info(f"{k} -> {v}")
            script_text = _sub_replace(k, v, script_subs[k]["type"])

            # inner substitutions
            if "subs" in script_subs[k]:
                if v in script_subs[k]["subs"]:
                    for inner_k in script_subs[k]['subs'][v].keys():
                        _type = script_subs[k]['subs'][v][inner_k]["type"]
                        _val = script_subs[k]['subs'][v][inner_k]["val"]
                        logger.info(f"{k} -> {v} {inner_k} --> {_val}")
                        script_text = _sub_replace(inner_k, _val, _type)

    return script_text


def parse_args():
    """
    :return: args
    """
    epilog = """
Usage examples:
    python3 prism_subs.py -w --script public/prism/scripts/example/prod_v0/prod_1.scr 

    """
    parser = argparse.ArgumentParser(description='prism_result_scan',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("-s", "--script",
                        dest="script",
                        action="store",
                        required=True,
                        help="Path to script file to sub")

    parser.add_argument("-w", "--write",
                        dest="write",
                        action="store_true",
                        help="Write output to file")

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    logging.basicConfig()
    logger.setLevel(logging.INFO)

    logger.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    logger.info("SUBS WITHIN SCRIPT MUST BE MODIFIED TO SUIT THE TARGET SCRIPT")
    logger.info("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    args = parse_args()
    file = args.script

    if not os.path.isfile(file):
        logger.error(f"Unable to find json file {file}")
        exit(1)

    with open(file) as f:
        json_data = f.read()

    try:
        # check script formatting by importing it
        script = jstyleson.loads(json_data)  # OK

    except Exception as e:
        logger.error(e)
        exit(1)

    script_text = json.dumps(script, indent=2)

    # !! MODIFY !!
    # subs to test, normally this list comes from the GUI or the traveller
    # all the values must be strings
    s = [{"Lot": "12345"},
         {"Loc": "canada/ontario/milton"},
         #{"Loc": "us/newyork/buffalo"},
         {"TST000Max": "9"}
    ]
    final_script_text = find_sub_items_replace(script_text, s)
    # rename subs key so that prism_dev.py will not error
    final_script_text = final_script_text.replace("subs", "subs1", 1)
    logger.info(final_script_text)

    if args.write: # save output to file for use with prism_dev.py
        file_out = file.replace(".scr", "_sub.scr")
        with open(file_out, 'w') as f:
            f.write(final_script_text)
