#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2019
Martin Guthrie

"""
import logging
from core.test_item import TestItem
from public.prism.api import ResultAPI


# file and class name must match
class pydso(TestItem):
    """ DSO Functions

    Notes:
        1) With {"shared": true} one scope is shared by all the channels, up to 4 channels,
           and scope input self.chan + 1 is wired to the jig of self.chan.  The scope is
           locked while a channel uses it.
        2) Without it, each channel has its own scope, and its input 1 is wired to the jig.
        3) get_drivers(self.chan, ...) returns this channel's scope, or the shared scope,
           so this code works for both.

    see: https://www.keysight.com/upload/cmc_upload/All/7000A_series_prog_guide.pdf
    """
    DEMO_TIME_DELAY = 1.0
    DEMO_TIME_RND_ENABLE = 1
    DSO = "AGILENT_DSO_USB_1"

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("{}.{}".format(__name__, self.chan))
        self.dso = None
        self.dso_ch = 1
        self.dso_lock = None

    def PYDSO000SETUP(self):
        """ Get driver from SharedState Open DSO and get DSO name, serial number,
        and save it to the record
        - a shared scope is locked with a lock shared by all channels, a scope of
          this channel's own has a lock of its own

        {"id": "PYDSO000SETUP",           "enable": true },
        """
        ctx = self.item_start()  # always first line of test

        # drivers are stored in the shared_state and are retrieved as,
        drivers = self.shared_state.get_drivers(self.chan, type=self.DSO)
        if len(drivers) != 1:
            self.logger.error("Unexpected number of drivers: {}".format(drivers))
            self.log_bullet("Unexpected number of drivers")
            self.item_end(ResultAPI.RECORD_RESULT_INTERNAL_ERROR)
            return
        self.dso = drivers[0]['obj']["hwdrv"]
        self.logger.info("Found dso: {}".format(self.dso))

        if drivers[0]["channel"] is None:  # shared scope
            self.dso_ch = self.chan + 1
            self.dso_lock = self.DSO
        else:
            self.dso_ch = 1
            self.dso_lock = "{}.{}".format(self.DSO, self.chan)

        with self.shared_lock(self.dso_lock):
            deets = self.dso.query('*IDN?')

        # save scope serial number and info, traceability
        dso_sn = drivers[0]['obj']["unique_id"]
        success, result, _bullet = ctx.record.measurement("dso_sn", dso_sn, ResultAPI.UNIT_STRING)
        self.log_bullet(_bullet)
        success, result, _bullet = ctx.record.measurement("dso", deets.strip(),
                                                          ResultAPI.UNIT_STRING)
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

        with self.shared_lock(self.dso_lock):
            # reset the scope to a known state
            self.dso.write('*RST')
            if chan != 1:  # after reset, chan 1 is already on
                self.dso.write(':CHANnel1:DISPlay OFF')  # turn off channel 1
                self.dso.write(':CHANnel{}:DISPlay ON'.format(chan))  # turn off channel 1

            self.dso.write(':CHANnel{}:SCALe 100mV'.format(chan))

            vpp = self.dso.query(':MEASure:VPP? CHANnel{}'.format(chan))
            value = float(vpp)
            success, _result, _bullet = ctx.record.measurement(
                "VPP{}".format(chan), value, ResultAPI.UNIT_VOLTS)

            self.log_bullet("Switched to channel {}".format(chan))
            self.log_bullet(_bullet)
            self.sleep(0.1)  # give it some time to sit here, else its too fast
        self.item_end()  # always last line of test

    def PYDSO020AUTOMEAS(self):
        """ Autoscale and then measure stuff

        {"id": "PYDSO020AUTOMEAS",   "enable": true, "50Ohm": true },
        """
        ctx = self.item_start()  # always first line of test
        chan50Ohm = ctx.item.get("50Ohm", False)

        with self.shared_lock(self.dso_lock):
            # reset the scope to a known state
            self.logger.info("reset")
            self.dso.write('*RST')
            if self.dso_ch != 1:  # after reset, chan 1 is already on
                self.dso.write(':CHANnel1:DISPlay OFF')  # turn off channel 1
                self.dso.write(':CHANnel{}:DISPlay ON'.format(self.dso_ch))  # turn off channel 1
            self.sleep(0.5)  # give it some time to sit here, else its too fast

            if chan50Ohm:
                self.dso.write(':CHANnel{}:IMPedance FIFTy'.format(self.dso_ch))

            self.logger.info("autoscale")
            self.dso.write(':AUT CHAN{}'.format(self.dso_ch))
            self.sleep(1.0)  # give it some time to sit here, else its too fast

            vpp = self.dso.query(':MEASure:VPP? CHANnel{}'.format(self.dso_ch))
            value = float(vpp)
            self.logger.info("VPP: {}".format(value))
            success, _result, _bullet = ctx.record.measurement(
                "VPP{}".format(self.dso_ch), value, ResultAPI.UNIT_VOLTS)
            self.log_bullet(_bullet)

            dc = self.dso.query(':MEASure:DUTYcycle? CHANnel{}'.format(self.dso_ch))
            dc = float(dc)
            self.logger.info("DC: {}".format(dc))
            success, _result, _bullet = ctx.record.measurement(
                "DUTYCYCLE{}".format(self.dso_ch), dc, ResultAPI.UNIT_FLOAT)
            self.log_bullet(_bullet)

            freq = self.dso.query(':MEASure:FREQ? CHANnel{}'.format(self.dso_ch))
            freq = float(freq)
            self.logger.info("FREQ: {}".format(dc))
            success, _result, _bullet = ctx.record.measurement(
                "FREQ{}".format(self.dso_ch), freq, ResultAPI.UNIT_FLOAT)
            self.log_bullet(_bullet)

        self.item_end()  # always last line of test

    def PYDSO999TRDN(self):
        ctx = self.item_start()  # always first line of test

        self.item_end()  # always last line of test
