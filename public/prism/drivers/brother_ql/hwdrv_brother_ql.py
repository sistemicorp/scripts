#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2020-2026
Vivian Guthrie, Martin Guthrie

USB Permissions:
When Prism runs from Docker, it has root permissions, so all is good.
However, when you are developing, your user account will not have USB permissions.
Use : sudo chmod -R 777 /dev/bus/usb/
To unlock USB. This is not a great security solution.
Also need to: sudo adduser $USER lp
And then reboot for that to take effect.

It is assumed only one (homogeneous) model of Brother printer is used in your deployment, and
the driver will only work with that model.

"""
import logging
from PIL import Image, ImageDraw, ImageFont
import qrcode
import re
import os
import subprocess
import base64
import pyudev
from core.const import PUB
from core.sys_log import pub_notice
from threading import Lock

VERSION = "0.0.1"
DRIVER_TYPE = "Brother_QL"

# According to PyPi brother_ql profile, these models are supported,
# QL-500 (✓), QL-550 (✓), QL-560 (✓), QL-570 (✓), QL-580N, QL-650TD, QL-700 (✓),
# QL-710W (✓), QL-720NW (✓), QL-800 (✓), QL-810W (✓), QL-820NWB (✓), QL-1050 (✓), and QL-1060N (✓)
# However, only the following has been tested in Prism, add or replace with your specific printer,
BROTHER_QL_MODELS = ["QL-700"]


class BrotherQL(object):
    """ Brother Ql-XXX Helper Class

    """
    DRIVER_PATH = os.path.dirname(os.path.abspath(__file__))
    WORKING_PATH = os.path.join(DRIVER_PATH, "wip")

    def __init__(self, id, path, model="QL-700"):
        self.logger = logging.getLogger("SC.{}".format(__class__.__name__))
        try:
            if not os.path.exists(self.WORKING_PATH):
                self.logger.info("creating {}".format(self.WORKING_PATH))
                os.makedirs(self.WORKING_PATH)

        except FileExistsError:
            pass

        except Exception as e:
            self.logger.error("Failed to make path for {}: {}".format(self.WORKING_PATH, e))
            notice = "ERROR path {} failed".format(self.WORKING_PATH)
            pub_notice(notice, sender="{}._make_dirs".format(__class__.__name__), type=PUB.NOTICES_ERROR)

        self.lock = Lock()
        self.path = path  # this is the linux usb path, /dev/usb/lp0
        self.id = id
        self.model = model

    def _filter_known_stderr_noise(self, stderr_text):
        """
        Remove known harmless warnings from stderr while preserving all real errors.
        """
        suppressed_markers = [
            "deprecation warning: brother_ql.devicedependent is deprecated",
        ]

        kept_lines = []
        suppressed_count = 0

        for line in stderr_text.splitlines():
            low = line.lower()
            if any(marker in low for marker in suppressed_markers):
                suppressed_count += 1
            else:
                kept_lines.append(line)

        return "\n".join(kept_lines).strip(), suppressed_count

    def _log_filtered_stderr(self, prefix, stderr_bytes):
        if not stderr_bytes:
            return

        stderr_text = str(stderr_bytes, "utf-8", errors="replace")
        filtered_text, suppressed_count = self._filter_known_stderr_noise(stderr_text)

        if filtered_text:
            self.logger.error("%s: %s", prefix, filtered_text)
        elif suppressed_count:
            self.logger.debug(
                "%s contained only suppressed warning(s): %d",
                prefix,
                suppressed_count
            )

    def _create_barcode(self, string):
        qr = qrcode.QRCode(version=1,
                           error_correction=qrcode.constants.ERROR_CORRECT_L,
                           box_size=5,
                           border=1)

        encrypted_info = "{}".format(string)

        qr.add_data(encrypted_info)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img_filename = os.path.join(self.WORKING_PATH, "qrcode.PNG")
        img.save(img_filename)
        return img_filename

    def _create_text(self, ruid, chan):
        img = Image.new('RGB', (696, 309), color='white')

        d = ImageDraw.Draw(img)
        font_path = os.path.join(self.DRIVER_PATH,'TIMES.TTF')
        self.logger.info(font_path)
        font = ImageFont.truetype(font_path, 50)
        d.text((10, 10), "RUID:{}".format(chan), fill=(0, 0, 0), font=font)
        font = ImageFont.truetype(font_path, 40)
        d.text((10, 54), "{}".format(ruid), fill=(0, 0, 0), font=font)
        img_file = os.path.join(self.WORKING_PATH, 'pil_text.png')
        img.save(img_file)
        return img_file

    def _create_label(self, text_path, barcode_path):
        text = Image.open(text_path, 'r')
        barcode = Image.open(barcode_path, 'r')

        label = Image.new('RGBA', (696, 280), color="white")
        label.paste(text, (0, 0))
        label.paste(barcode, (540, 120))
        img_file = os.path.join(self.WORKING_PATH, 'label.png')
        label.save(img_file)
        self.logger.info(img_file)
        self._save_as_base64(img_file)
        return img_file

    def _save_as_base64(self, img_path):
        with open("{}".format(img_path), 'rb') as image:
            str = base64.b64encode(image.read())
            file = open(os.path.join(self.WORKING_PATH, "img.txt"), 'w')
            file.write(str.decode("utf-8"))
            file.close()

    def _print_label(self, img_path):
        brother_ql = os.path.abspath(self.DRIVER_PATH + "/brother_ql")

        create_cmd = f'python3 {brother_ql}/brother_ql_create.py --model {self.model} {img_path} > {self.WORKING_PATH}/label.bin'
        self.logger.debug("create_cmd: %s", create_cmd)

        try:
            l_bin = subprocess.Popen(
                [create_cmd],
                cwd='.',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
            l_out, l_err = l_bin.communicate(timeout=30)

        except subprocess.TimeoutExpired:
            self.logger.exception("Timeout while creating label.bin")
            return False

        except Exception:
            self.logger.exception("Unexpected error while creating label.bin")
            return False

        if l_out:
            self.logger.info(str(l_out, 'utf-8', errors='replace'))
        self._log_filtered_stderr("create stderr", l_err)

        if l_bin.returncode:
            self.logger.error("create.returncode: %s", l_bin.returncode)
            return False

        print_cmd = [
            'python3',
            '{}/brother_ql_print.py'.format(brother_ql),
            '{}/label.bin'.format(self.WORKING_PATH),
            self.path
        ]
        self.logger.debug("print_cmd: %s", " ".join(print_cmd))

        try:
            printing = subprocess.Popen(
                print_cmd,
                cwd='.',
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            p_out, p_err = printing.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            self.logger.exception("Timeout while printing label")
            return False

        except Exception:
            self.logger.exception("Unexpected error while printing label")
            return False

        if p_out:
            self.logger.info(str(p_out, 'utf-8', errors='replace'))
        self._log_filtered_stderr("print stderr", p_err)

        if printing.returncode:
            self.logger.error("printing.returncode: {}".format(printing.returncode))
            return False

        self.logger.info("printed successfully")
        return True

    def print_ruid_barcode(self, ruid, chan=0):
        """ Print a label with the RUID and a barcode representation of the RUID

        :param ruid:
        :return: success <True/False>
        """
        with self.lock:
            barcode_path = self._create_barcode(ruid)
            text_path = self._create_text(ruid, chan)
            label_path = self._create_label(text_path, barcode_path)
            return self._print_label(label_path)

    def get_id_path(self):
        """ Get ID and path

        :return: id, path
        """
        return self.id, self.path


class HWDriver(object):
    """
    HWDriver is a class that installs a HW driver into the shared state.
    This is not the HW driver itself, just an installer.

    """
    SFN = os.path.basename(__file__)

    def __init__(self):
        self.logger = logging.getLogger("{}".format(self.SFN))
        self.logger.info("Start")
        self._num_chan = 0

    def _attr_str(self, dev, key):
        raw = dev.attributes.get(key)
        if raw is None:
            return ""
        if isinstance(raw, (bytes, bytearray)):
            return raw.decode("utf-8", errors="ignore").strip()
        return str(raw).strip()

    def _usb_port_sort_key(self, usb_dev):
        """
        Sort key based on USB topology path.
        Example usb_dev.sys_name:
          '1-2'      -> (1, 2)
          '1-2.3'    -> (1, 2, 3)
          '2-1.4.2'  -> (2, 1, 4, 2)
        """
        sys_name = getattr(usb_dev, "sys_name", "") or ""
        nums = [int(x) for x in re.findall(r"\d+", sys_name)]
        if nums:
            return tuple(nums)

        # fallback: unknown topology goes last, keep deterministic ordering
        devpath = getattr(usb_dev, "device_path", "") or ""
        return (10_000, hash(devpath) & 0xFFFF)

    def _find_brother_printers(self, context):
        """
        Returns a list of tuples sorted by USB hub port:
          [(sort_key, devnode, manufacturer, product, usb_sys_name), ...]
        """
        candidates = []
        seen_devnodes = set()
        model_set = set(BROTHER_QL_MODELS)

        # usblp printer character devices typically show up in usbmisc
        for lp_dev in context.list_devices(subsystem="usbmisc"):
            devnode = lp_dev.device_node
            if not devnode or not devnode.startswith("/dev/usb/lp"):
                continue
            if devnode in seen_devnodes:
                continue

            usb_dev = lp_dev.find_parent(subsystem="usb", device_type="usb_device")
            if usb_dev is None:
                continue

            manufacturer = self._attr_str(usb_dev, "manufacturer")
            product = self._attr_str(usb_dev, "product")

            if "Brother" not in manufacturer:
                continue
            if product not in model_set:
                continue

            sort_key = self._usb_port_sort_key(usb_dev)
            usb_sys_name = getattr(usb_dev, "sys_name", "")
            candidates.append((sort_key, devnode, manufacturer, product, usb_sys_name))
            seen_devnodes.add(devnode)

        candidates.sort(key=lambda x: x[0])
        return candidates

    def discover_channels(self, scriptArgs=None):
        """ Determine the number of channels, and populate hw drivers into shared state

        scriptArgs = {"only_one": true|false, "test_label": true|false}

            only_one = Only one Printed is expected to be found and will be shared
            test_label = Print a test label before starting the test script

        This driver is for the Brother QL only.
        Multiple printers will be ordered by the USB hub port they are connected to. Presumably,
        each printer is associated with a Jig, so the order of the printers is important.

        [ {"id": i,                    # ~slot number of the channel (see Note 1)
           "version": <VERSION>,       # version of the driver
           "hwdrv": <object>,          # instance of your hardware driver

           # optional
           "close": None,              # register a callback on closing the channel, or None
           "play": jig_closed_detect   # function for detecting jig closed
           "show_pass_fail": jig_led   # function for indicating pass/fail (like LED)
           "show_msg": jig_display     # function for indicating test status (like display)

           # not part of the required block
           "unique_id": <unique_id>,   # unique id of the hardware (for tracking purposes)
           ...
          }, ...
        ]

        Note:
        1) The hw driver objects are expected to have an 'slot' field, the lowest
           id is assigned to channel 0, the next highest to channel 1, etc

        :return: <#>, <list>
            where #: >0 number of channels,
                      0 does not indicate num channels, like a shared hardware driver
                     <0 error

                  list of drivers
        """
        drivers = []
        id = 0
        context = pyudev.Context()

        printers = self._find_brother_printers(context)
        for _, devnode, manufacturer, product, usb_sys_name in printers:
            self.logger.info("Found printer: %s %s at %s (usb=%s)", manufacturer, product, devnode, usb_sys_name)
            drivers.append({"id": id,
                            "version": VERSION,
                            "hwdrv": BrotherQL(id, devnode),
                            "play": None,
                            "show_pass_fail": None,
                            "show_msg": None,
                            "close": None})
            id += 1

        if not drivers:
            self.logger.error("printer not found")
            pub_notice("HWDriver:{}: Error none found".format(self.SFN), sender="discover_channels", type=PUB.NOTICES_ERROR)
            return -1, DRIVER_TYPE, []

        # do not allow the test script validation step to succeed if can't print a test label
        if scriptArgs and scriptArgs.get("test_label", False):
            for d in drivers:
                id, path = d["hwdrv"].get_id_path()
                success = d["hwdrv"].print_ruid_barcode("id{}-{}".format(id, path))
                if not success:
                    self.logger.error("failed to print")
                    pub_notice("HWDriver:{}: failed to print".format(self.SFN), sender="discover_channels", type=PUB.NOTICES_ERROR)
                    return -1, DRIVER_TYPE, []

        pub_notice("HWDriver:{}: found {}".format(self.SFN, id),
                   sender="discover_channels",
                   type=PUB.NOTICES_NORMAL)

        # Setting number of channels to zero means this device is shared across all test fixtures
        if scriptArgs and scriptArgs.get('only_one', False):
            self._num_chan = 0

        return self._num_chan, DRIVER_TYPE, drivers

    def num_channels(self):
        return self._num_chan

    def close(self):
        self.logger.info("closed")

# ===============================================================================================
# Debugging code
# - Test your hardware discovery here by running this file from PyCharm (be sure to set the working
#   directory as ~/git/scripts, else imports will fail)
# - the purpose is to valid discover_channels() is working
# - you will have to comment out pub_notice() and the core import whilst using this
#
if __name__ == '__main__':
    logging.basicConfig()
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    d = HWDriver()
    #d.discover_channels()
    d.discover_channels({"test_label": True})
    logger.info("Number channels: {}".format(d.num_channels()))
