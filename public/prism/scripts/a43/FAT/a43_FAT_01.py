#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2024
Martin Guthrie

"""
import os
import base64
from PIL import Image, ImageDraw, ImageFont
import qrcode
from core.test_item import TestItem
from public.prism.api import ResultAPI

import logging
logger = logging.getLogger()


def QL_700_Label(model, serial, hwver):
    """ Create label for P1150 bottom side
    """
    TEMP_PATH = "public/prism/scripts/a43/temp"
    QRCODE_PATH = TEMP_PATH + "/qrcode.PNG"
    BODY_PATH = TEMP_PATH + "/pil_text.png"
    LABEL_PATH = TEMP_PATH + "/label.png"

    if not os.path.exists(TEMP_PATH):
        os.makedirs(TEMP_PATH)

    qr = qrcode.QRCode(version=1,
                       error_correction=qrcode.constants.ERROR_CORRECT_L,
                       box_size=8,
                       border=1)

    encrypted_info = "{}".format(serial)

    qr.add_data(encrypted_info)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(QRCODE_PATH)
    qrcode_path = os.path.abspath(QRCODE_PATH)

    img = Image.new('RGB', (696, 309), color='white')

    d = ImageDraw.Draw(img)
    font_path = './public/prism/drivers/brother_ql700/AnonymousPro-Regular.ttf'
    logger.debug(font_path)
    font = ImageFont.truetype(font_path, 34)
    d.text((10, 10), "MDL:{}".format(model), fill=(0, 0, 0), font=font)
    d.text((10, 40), "VER:{}".format(hwver), fill=(0, 0, 0), font=font)
    d.text((10, 70), "SN :{}".format(serial.upper()), fill=(0, 0, 0), font=font)
    d.text((10, 100), "www.sistemi.ca", fill=(0, 0, 0), font=font)
    d.text((10, 130), "Made in Canada", fill=(0, 0, 0), font=font)
    img.save(BODY_PATH)
    body_path = os.path.abspath(BODY_PATH)

    text = Image.open(body_path, 'r')
    barcode = Image.open(qrcode_path, 'r')

    label = Image.new('RGBA', (696, 180), color="white")
    label.paste(text, (0, 0))
    label.paste(barcode, (500, 0))
    label.save(LABEL_PATH)
    img_file = os.path.abspath(LABEL_PATH)

    with open("{}".format(img_file), 'rb') as image:
        str = base64.b64encode(image.read())
        file = open(TEMP_PATH + "/img.txt", 'w')
        file.write(str.decode("utf-8"))
        file.close()

    return img_file


# file and class name must match
class a43_FAT_01(TestItem):
    """

    """

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("{}.{}".format(__name__, self.chan))
        self.printer = None

    def FAT000SETUP(self):
        """ Setup

        """
        ctx = self.item_start()  # always first line of test
        printer_info = self.shared_state.get_drivers(None, type="Brother_QL-700")
        if not printer_info:
            self.logger.error("Printer not found")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.printer = printer_info[0]['obj']['hwdrv']
        self.item_end()  # always last line of test

    def FAT010_LABEL(self):
        ctx = self.item_start()  # always first line of test

        label_path = QL_700_Label("P1150","0123456", "a430800")
        self.printer._print_label(label_path)

        self.item_end()  # always last line of test

    def FAT999TRDN(self):
        """ Teardown

        """
        ctx = self.item_start()  # always first line of test
        # there is nothing to do...
        self.item_end()  # always last line of test



