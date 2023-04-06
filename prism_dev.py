#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019-2023
Martin Guthrie

"""
import os
import sys
import argparse
import jstyleson
import logging
import logging.handlers as handlers
import importlib
import time

from public.prism.api import ResultAPI
from public.prism.ResultBaseKeysV1 import ResultBaseKeysV1
from core.shared_state import SharedState
from prism_result_scan import scan_result_file

logger = None


class attrdict(dict):
    """
    Attribute Dictionary.

    Enables getting/setting/deleting dictionary keys via attributes.
    Getting/deleting a non-existent key via attribute raises `AttributeError`.
    Objects are passed to `__convert` before `dict.__setitem__` is called.

    This class rebinds `__setattr__` to call `dict.__setitem__`. Attributes
    will not be set on the object, but will be added as keys to the dictionary.
    This prevents overwriting access to built-in attributes. Since we defined
    `__getattr__` but left `__getattribute__` alone, built-in attributes will
    be returned before `__getattr__` is called. Be careful::

        >>> a = attrdict()
        >>> a['key'] = 'value'
        >>> a.key
        'value'
        >>> a['keys'] = 'oops'
        >>> a.keys
        <built-in method keys of attrdict object at 0xabcdef123456>

    Use `'key' in a`, not `hasattr(a, 'key')`, as a consequence of the above.
    """
    def __init__(self, *args, **kwargs):
        # We trust the dict to init itself better than we can.
        dict.__init__(self, *args, **kwargs)
        # Because of that, we do duplicate work, but it's worth it.
        for k, v in self.items():
            self.__setitem__(k, v)

    def __getattr__(self, k):
        try:
            return dict.__getitem__(self, k)
        except KeyError:
            # Maintain consistent syntactical behaviour.
            raise AttributeError(
                "'attrdict' object has no attribute '" + str(k) + "'"
            )

    def __setitem__(self, k, v):
        dict.__setitem__(self, k, attrdict.__convert(v))

    __setattr__ = __setitem__

    def __delattr__(self, k):
        try:
            dict.__delitem__(self, k)
        except KeyError:
            raise AttributeError(
                "'attrdict' object has no attribute '" + str(k) + "'"
            )

    @staticmethod
    def __convert(o):
        """
        Recursively convert `dict` objects in `dict`, `list`, `set`, and
        `tuple` objects to `attrdict` objects.
        """
        if isinstance(o, dict):
            o = attrdict(o)
        elif isinstance(o, list):
            o = list(attrdict.__convert(v) for v in o)
        elif isinstance(o, set):
            o = set(attrdict.__convert(v) for v in o)
        elif isinstance(o, tuple):
            o = tuple(attrdict.__convert(v) for v in o)
        return o


class ChanCon(object):

    def __init__(self, num=0, script=None, shared_state=None, script_filename="UNKNOWN", operator="UNKNOWN"):
        self.logger = logging.getLogger("{}.{}".format(__class__.__name__, num))
        self.ch = num
        self.script = script
        self.shared_state = shared_state
        self.operator = operator
        self.num_channels = 0

        self.record = ResultBaseKeysV1(0, "prismdev", script_filename)
        self.record.record_info_set(script.get("info", {}))
        self.record.record_record_meta_init()

    def item_start(self):
        d = {"item": self._item,
             # item dict from the script, ex {"id": "TST000", "enable": true,  "args": {"min": 0, "max": 2}}
             "options": self._options,  # options dict from the script, ex { "fail_fast": false }
             "record": self.record,

             # TODO: add more stuff as needed
             }
        self.record.record_item_create(d["item"]["id"])
        return attrdict(d)

    def item_end(self, item_result_state=ResultAPI.RECORD_RESULT_PASS, _next=None):
        self.logger.debug("{}, {}".format(self._item["id"], item_result_state))

        if self.record.record_test_get_result() not in [ResultAPI.RECORD_RESULT_UNKNOWN]:
            # there must have been another early failure, either a timeout or crash...
            # bail on processing, assume its already been done...
            self.logger.warning("record_test_set_result already set... aborting")
            return

        # process a list of results, set the final state to the first non pass state
        if isinstance(item_result_state, list):
            _final = ResultAPI.RECORD_RESULT_PASS
            for result in item_result_state:
                if result is not ResultAPI.RECORD_RESULT_PASS:
                    _final = result
                    break
            item_result_state = _final

        self.record.record_test_set_result(item_result_state)
        self.record.record_item_end()

    def log_bullet(self, text, ovrwrite_last_line):
        self.logger.info("BULLET: {}".format(text))

    def run(self):
        show_pass_fail = None

        # process HW drivers
        num_channels = -1
        for hwdrv in self.script["config"]["drivers"]:
            logger.info("HWDRV: {}".format(hwdrv))
            hwdrv_sname = hwdrv.split(".")[-1]
            hwdrv_module = importlib.import_module(hwdrv)
            hwdrv_module_klass = getattr(hwdrv_module, "HWDriver")
            hwdriver = hwdrv_module_klass()

            _num_channels, driver_type, drivers = hwdriver.discover_channels()

            if _num_channels >= 0:  # add to shared state if all good
                shared = False
                if _num_channels == 0: shared = True
                self.shared_state.add_drivers(driver_type, drivers, shared)

                # call the player function if exist, ignore result, but see logs
                if drivers:
                    if drivers[0].get('play', None):
                        play = drivers[0].get('play')()
                        while not play:
                            play = drivers[0].get("play")()
                            self.logger.info("player: {}".format(play))
                            if not play: time.sleep(1)

                    if show_pass_fail is None:
                        show_pass_fail = drivers[0].get("show_pass_fail", None)
                        if show_pass_fail:
                            show_pass_fail(False, False, False)

            self.logger.info("{} - number channels {}".format(hwdrv_sname, _num_channels))
            if _num_channels == 0:
                # this HW DRV does not indicate number of channels, its a shared resource
                pass
            elif _num_channels < 0:
                raise ValueError('Error returned by HWDRV {}'.format(hwdrv_sname))
            elif num_channels == -1:
                num_channels = _num_channels
            elif num_channels != _num_channels:
                self.logger.error(
                    "{} - number channels {} does not match previous HWDRV".format(hwdriver, _num_channels))
                raise ValueError('Mismatch number of channels between HW Drivers')

        self.num_channels = num_channels
        self.logger.info("number channels {}".format(self.num_channels))
        if self.num_channels < 1:
            self.logger.error("Invalid number of channels, must be >0")
            raise ValueError('Invalid number of channels')

        fail_fast = self.script["config"].get("fail_fast", True)

        for test in self.script["tests"]:

            self._options = test["options"]

            logger.info("Module: {}".format(test["module"]))
            test_module = importlib.import_module(test["module"])
            klass = test["module"].split(".")[-1]
            logger.debug("class: {}".format(klass))

            test_module_klass = getattr(test_module, klass)
            test_klass = test_module_klass(controller=self, chan=self.ch, shared_state=self.shared_state)

            for item in test["items"]:
                logger.info("ITEM: {}".format(item))
                if item.get("enable", True):
                    self._item = item
                    if not getattr(test_klass, item["id"], False):
                        msg = "method {} is not in module {}".format(item["id"], test_klass)
                        logger.error(msg)
                        raise ValueError(msg)

                    func = getattr(test_klass, item["id"])
                    func()

                    if fail_fast and self.record.record_meta_get_result() != ResultAPI.RECORD_RESULT_PASS:
                        break

        self.record.record_record_meta_fini()
        result_file = self.record.record_publish()

        if show_pass_fail is not None:
            p = f = o = False
            if self.record.record_meta_get_result() == ResultAPI.RECORD_RESULT_PASS:
                p = True
            elif self.record.record_meta_get_result() == ResultAPI.RECORD_RESULT_FAIL:
                f = True
            else:
                o = True
            show_pass_fail(p, f, o)

        return result_file


def setup_logging(log_file_name_prefix="log", level=logging.INFO, path="./log"):
    global logger
    logger = logging.getLogger()
    logger.setLevel(level)

    log_file_name_prefix = os.path.basename(log_file_name_prefix)

    if not os.path.exists(path): os.makedirs(path)

    # Here we define our formatter
    FORMAT = "%(relativeCreated)5d %(filename)30s:%(lineno)4s - %(name)30s:%(funcName)20s() %(levelname)-5.5s : %(message)s"
    formatter = logging.Formatter(FORMAT)

    allLogHandler_filename = os.path.join(path, "".join([log_file_name_prefix, ".log"]))
    allLogHandler = handlers.RotatingFileHandler(allLogHandler_filename, maxBytes=1024 * 1024, backupCount=4)
    allLogHandler.setLevel(logging.INFO)
    allLogHandler.setFormatter(formatter)

    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(formatter)

    logger.addHandler(allLogHandler)
    logger.addHandler(consoleHandler)


def read_json_file_to_dict(file):
    if not os.path.isfile(file):
        msg = "Unable to find json file %s" % file
        logger.error(msg)
        return False, msg

    with open(file) as f:
        json_data = f.read()

    try:
        result_dict = jstyleson.loads(json_data)  # OK

    except Exception as e:
        logger.error(e)
        return False, e

    return True, result_dict


def parse_args():
    """
    :return: args
    """
    epilog = """
Usage examples:
    python3 prism_dev.py --script ./public/prism/scripts/example/prod_v0/prod_0.scr 
    python3 prism_dev.py --script ./public/prism/scripts/example/pybrd_v0/pybrd_0.scr 

Sistemi Corporation, copyright, all rights reserved, 2019
    """
    parser = argparse.ArgumentParser(description='prism_dev',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog=epilog)

    parser.add_argument("--script",
                        dest="script",
                        action="store",
                        required=True,
                        help="Path to script file to run")

    parser.add_argument("--result-scan",
                        dest="result_scan",
                        action="store_true",
                        help="Scan result file for correctness")

    args = parser.parse_args()
    args_dict = vars(args)
    return args_dict


def script_validated(script):
    if not script.get("info", False):
        logger.error("Script is missing 'info' section")
        return False

    if not script.get("config", False):
        logger.error("Script is missing 'config' section")
        return False

    if not script["config"].get("drivers", False):
        logger.error("Script is missing 'config.drivers' section")
        return False

    if script.get("subs", False):
        logger.error("'subs' are not supported in console development")
        logger.error("Rename 'subs' to something else, make the substitutions manually, and retry")
        return False

    # TODO: add more stuff, check imports....

    logger.info("Script passed validation tests")
    return True


def main():
    setup_logging(log_file_name_prefix="dev", path="log")

    args = parse_args()
    logger.info("args: {}".format(args))
    if args is None:
        logger.error("Failed to parse args")
        return 1

    # read script
    success, script = read_json_file_to_dict(args["script"])
    if not success:
        logger.error(script)
        return 1

    # validate script
    if not script_validated(script):
        logger.error("Script failed to validate")
        return 1

    shared_state = SharedState()

    con = ChanCon(0, script, shared_state, args["script"])
    result_file = con.run()

    # close any drivers
    drivers = shared_state.get_drivers(0)
    for d in drivers:
        if d['obj'].get("close", False):
            d["obj"]["close"]()

    # TODO: publish shutdown

    if args["result_scan"]:
        logger.info(f"Running result record scan on {result_file}")
        scan_result_file(result_file)

    return 0


if __name__ == "__main__":
    retcode = main()
    sys.exit(retcode)
