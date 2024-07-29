#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2020-2021
Vivian Guthrie, Martin Guthrie

"""
import logging
from PIL import Image, ImageDraw, ImageFont
import qrcode
import os
import subprocess
import base64
import usb
from core.const import PUB
from core.sys_log import pub_notice
from threading import Lock

VERSION = "0.0.1"

NUM_CHANNELS = 1  # set this to simulate multiple channels, range 1-4

DRIVER_TYPE = "Brother_QL-700"


class BrotherQL700(object):
    """ Brother Ql-700 Helper Class

    """
    DRIVER_PATH = "./public/prism/drivers/brother_ql700/"
    WORKING_PATH = DRIVER_PATH + "wip/"

    def __init__(self, id, path):
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
            pub_notice(notice, sender="{}._make_dirs".format(__class__.__name__), type=PUB.NOTICE_ERR)

        self.lock = Lock()
        self.path = path  # this is the linux usb path, /dev/usb/lp0
        self.id = id

    def _create_barcode(self, string):
        qr = qrcode.QRCode(version=1,
                           error_correction=qrcode.constants.ERROR_CORRECT_L,
                           box_size=5,
                           border=1)

        encrypted_info = "{}".format(string)

        qr.add_data(encrypted_info)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(self.WORKING_PATH + "qrcode.PNG")
        img_filename = os.path.abspath(self.WORKING_PATH + "qrcode.PNG")
        return img_filename

    def _create_text(self, ruid, chan):
        img = Image.new('RGB', (696, 309), color='white')

        d = ImageDraw.Draw(img)
        font_path = self.DRIVER_PATH + 'TIMES.TTF'
        self.logger.info(font_path)
        font = ImageFont.truetype(font_path, 50)
        d.text((10, 10), "RUID:{}".format(chan), fill=(0, 0, 0), font=font)
        font = ImageFont.truetype(font_path, 40)
        d.text((10, 54), "{}".format(ruid), fill=(0, 0, 0), font=font)
        img.save(self.WORKING_PATH + 'pil_text.png')
        img_file = os.path.abspath(self.WORKING_PATH + 'pil_text.png')
        return img_file

    def _create_label(self, text_path, barcode_path):
        text = Image.open(text_path, 'r')
        barcode = Image.open(barcode_path, 'r')

        label = Image.new('RGBA', (696, 280), color="white")
        label.paste(text, (0, 0))
        label.paste(barcode, (540, 120))
        label.save(self.WORKING_PATH + "label.png")
        img_file = os.path.abspath(self.WORKING_PATH + 'label.png')
        self.logger.info(img_file)
        self._save_as_base64(img_file)
        return img_file

    def _save_as_base64(self, img_path):
        with open("{}".format(img_path), 'rb') as image:
            str = base64.b64encode(image.read())
            file = open(self.WORKING_PATH + "img.txt", 'w')
            file.write(str.decode("utf-8"))
            file.close()

    def _print_label(self, img_path):
        brother_ql = os.path.abspath(self.DRIVER_PATH + "/brother_ql")

        l_bin = subprocess.Popen(
            ['python3 {}/brother_ql_create.py --model QL-700 {} > {}label.bin'.format(brother_ql, img_path, self.WORKING_PATH)],
            cwd='.', stdout=subprocess.PIPE, shell=True)

        # brother_ql_create --model QL-700 label.png > label.bin

        self.logger.info(str(l_bin.communicate()[0], 'utf-8'))

        printing = subprocess.Popen(
            ['python3', '{}/brother_ql_print.py'.format(brother_ql), '{}label.bin'.format(self.WORKING_PATH), self.path],
            cwd='.', stdout=subprocess.PIPE)

        self.logger.info(str(printing.communicate()[0], 'utf-8'))
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

    def discover_channels(self):
        """ Determine the number of channels, and populate hw drivers into shared state

        This driver is for the Brother QL-700 only.
        Multiple printers are not supported by this example driver.
        Multiple printers could be supported by assigning the /dev/usb/lp# to the channel
        number.

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
        dev = usb.core.find(find_all=True)
        for d in dev:
            # print(d) to see all the attributes
            manu = usb.util.get_string(d, d.iManufacturer)
            prod = usb.util.get_string(d, d.iProduct)
            if manu == "Brother" and prod in ["QL-700", ]:
                self.logger.info("Found {} {}".format(manu, prod))

                p = '/dev/usb/lp0'  # FIXME: when multiple printers exist, need to find file association

                drivers.append({"id": id,
                                "version": VERSION,
                                "hwdrv": BrotherQL700(id, p),
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
        for d in drivers:
            id, path = d["printer"].get_id_path()
            success = d["printer"].print_ruid_barcode("id{}-{}".format(id, path))
            if not success:
                self.logger.error("failed to print")
                pub_notice("HWDriver:{}: failed to print".format(self.SFN), sender="discover_channels", type=PUB.NOTICES_ERROR)
                return -1, DRIVER_TYPE, []

            pub_notice("HWDriver:{}: found {} {}".format(self.SFN, id, path), sender="discover_channels", type=PUB.NOTICES_NORMAL)

        # by returning 0, it means this return values DOES not represent number of channels
        return 0, DRIVER_TYPE, drivers

