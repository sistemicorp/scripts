#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
import logging
import time
from core.test_item import TestItem
from public.prism.api import ResultAPI


# file and class name must match
class pydso(TestItem):
    """ DSO Functions

    Notes:
        1) This is a shared resource driver, implying that it is shared across all the
           active channels, and its assumed that up to 4 channels can exist, and therefor
           each DSO channel is available to each self.chan.  Therefore, self.dso_ch = self.chan
           and the DSO is expected to have a physical connection of Ch1 -> self.chan.

    see: https://www.keysight.com/upload/cmc_upload/All/7000A_series_prog_guide.pdf
    """
    DEMO_TIME_DELAY = 1.0
    DEMO_TIME_RND_ENABLE = 1
    DSO = "AGILENT_DSO_USB_1"

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("{}.{}".format(__name__, self.chan))
        self.dso = None
        self.dso_ch = self.chan + 1

    def PYDSO000SETUP(self):
        """ Get driver from SharedState Open DSO and get DSO name, serial number, and save it to the record
        - need to create a lock so that multiple channels can lock this shard resource

        {"id": "PYDSO000SETUP",           "enable": true },
        """
        ctx = self.item_start()  # always first line of test

        # drivers are stored in the shared_state and are retrieved as,
        drivers = self.shared_state.get_drivers(None, type=self.DSO)
        if len(drivers) > 1 or len(drivers) == 0:
            self.logger.error("Unexpected number of drivers: {}".format(drivers))
            self.log_bullet("Unexpected number of drivers")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return
        self.dso = drivers[0]['obj']["visa"]
        self.logger.info("Found dso: {}".format(self.dso))

        self.shared_lock(self.DSO).acquire()
        deets = self.dso.query('*IDN?')
        self.shared_lock(self.DSO).release()

        # save scope info, traceability
        success, result, _bullet = ctx.record.measurement("dso", deets, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)

        # save dso channel for traceability, for example, a systematic error found on channel X
        success, result, _bullet = ctx.record.measurement("chan", self.dso_ch, ResultAPI.UNIT_INT)
        self.log_bullet(_bullet)

        self.logger.info("DSO channel {} assigned".format(self.dso_ch))
        self.item_end()  # always last line of test

    def PYDSO010SETCHAN(self):
        """ Change the channel of the scope, and measure voltage, just for fun
        - this case depends on a setup being configured, ie set timebase, scale, etc

        {"id": "PYDSO010SETCHAN",   "enable": true, "chan": 1 },
        """
        ctx = self.item_start()  # always first line of test
        chan = ctx.item.get("chan", 1)

        if not (0 < chan < 5):
            self.logger.error("Invalid channel number: {} (1-4 accepted)".format(chan))
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return

        self.shared_lock(self.DSO).acquire()

        # reset the scope to a known state
        self.dso.write('*RST')
        if chan != 1:  # after reset, chan 1 is already on
            self.dso.write(':CHANnel1:DISPlay OFF')  # turn off channel 1
            self.dso.write(':CHANnel{}:DISPlay ON'.format(chan))  # turn off channel 1

        self.dso.write(':CHANnel{}:SCALe 100mV'.format(chan))

        vpp = self.dso.query(':MEASure:VPP? CHANnel{}'.format(chan))
        value = float(vpp)
        success, _result, _bullet = ctx.record.measurement("VPP{}".format(chan), value, ResultAPI.UNIT_VOLTS)

        self.log_bullet("Switched to channel {}".format(chan))
        self.log_bullet(_bullet)
        time.sleep(0.1) # give it some time to sit here, else its too fast
        self.shared_lock(self.DSO).release()
        self.item_end()  # always last line of test

    def PYDSO020AUTOMEAS(self):
        """ Autoscale and then measure stuff

        {"id": "PYDSO020AUTOMEAS",   "enable": true, "50Ohm": true },
        """
        ctx = self.item_start()  # always first line of test
        chan50Ohm = ctx.item.get("50Ohm", False)

        self.shared_lock(self.DSO).acquire()

        # reset the scope to a known state
        self.logger.info("reset")
        self.dso.write('*RST')
        if self.dso_ch != 1:  # after reset, chan 1 is already on
            self.dso.write(':CHANnel1:DISPlay OFF')  # turn off channel 1
            self.dso.write(':CHANnel{}:DISPlay ON'.format(self.dso_ch))  # turn off channel 1
        time.sleep(0.5) # give it some time to sit here, else its too fast

        if chan50Ohm:
            self.dso.write(':CHANnel{}:IMPedance FIFTy'.format(self.dso_ch))

        self.logger.info("autoscale")
        self.dso.write(':AUT CHAN{}'.format(self.dso_ch))
        time.sleep(1.0) # give it some time to sit here, else its too fast

        vpp = self.dso.query(':MEASure:VPP? CHANnel{}'.format(self.dso_ch))
        value = float(vpp)
        self.logger.info("VPP: {}".format(value))
        success, _result, _bullet = ctx.record.measurement("VPP{}".format(self.dso_ch), value, ResultAPI.UNIT_VOLTS)
        self.log_bullet(_bullet)

        dc = self.dso.query(':MEASure:DUTYcycle? CHANnel{}'.format(self.dso_ch))
        dc = float(dc)
        self.logger.info("DC: {}".format(dc))
        success, _result, _bullet = ctx.record.measurement("DUTYCYCLE{}".format(self.dso_ch), dc, ResultAPI.UNIT_FLOAT)
        self.log_bullet(_bullet)

        freq = self.dso.query(':MEASure:FREQ? CHANnel{}'.format(self.dso_ch))
        freq = float(freq)
        self.logger.info("FREQ: {}".format(dc))
        success, _result, _bullet = ctx.record.measurement("FREQ{}".format(self.dso_ch), freq, ResultAPI.UNIT_FLOAT)
        self.log_bullet(_bullet)

        self.shared_lock(self.DSO).release()
        self.item_end()  # always last line of test

    def PYDSO999TRDN(self):
        ctx = self.item_start()  # always first line of test

        self.item_end()  # always last line of test

