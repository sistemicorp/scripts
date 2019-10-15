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
    """

    see: https://www.keysight.com/upload/cmc_upload/All/7000A_series_prog_guide.pdf
    """
    DEMO_TIME_DELAY = 1.0
    DEMO_TIME_RND_ENABLE = 1
    DSO = "AGILENT_DSO_USB_1"

    def __init__(self, controller, chan, shared_state):
        super().__init__(controller, chan, shared_state)
        self.logger = logging.getLogger("{}.{}".format(__name__, self.chan))
        self.dso = None

    def PYDSO000SETUP(self):
        """ Get driver from SharedState Open DSO and get DSO name, serial number, and save it to the record
        - need to create a lock so that multiple channels can lock this shard resource

        {"id": "PYDSO000SETUP",           "enable": true },
        """
        ctx = self.item_start()  # always first line of test

        # drivers are stored in the shared_state and are retrieved as,
        drivers = self.shared_state.get_drivers(self.chan, type=self.DSO)
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

        # save scope info
        _, _bullet = ctx.record.measurement("dso", deets, ResultAPI.UNIT_NONE)
        self.log_bullet(_bullet)

        self.item_end()  # always last line of test

    def PYDSO010SETCHAN(self):
        """ Change the channel of the scope, and measure voltage, just for fun

        {"id": "PYDSO010SETCHAN",   "enable": true, "chan": 1 },
        """
        ctx = self.item_start()  # always first line of test

        chan = ctx.item.chan
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
        _result, _bullet = ctx.record.measurement("VPP{}".format(chan), value, ResultAPI.UNIT_VOLTS)

        self.log_bullet("Switched to channel {}".format(chan))
        self.log_bullet(_bullet)
        time.sleep(0.1) # give it some time to sit here, else its too fast
        self.shared_lock(self.DSO).release()
        self.item_end()  # always last line of test

    def PYDSO020AUTO(self):
        """ Autoscale

        {"id": "PYDSO020AUTO",   "enable": true },
        """
        ctx = self.item_start()  # always first line of test

        self.shared_lock(self.DSO).acquire()

        # reset the scope to a known state
        self.dso.write('*RST')
        if self.chan != 1:  # after reset, chan 1 is already on
            self.dso.write(':CHANnel1:DISPlay OFF')  # turn off channel 1
            self.dso.write(':CHANnel{}:DISPlay ON'.format(self.chan))  # turn off channel 1

        self.dso.write(':AUToscale:CHANnels DISPlayed')

        time.sleep(0.1) # give it some time to sit here, else its too fast
        self.shared_lock(self.DSO).release()
        self.item_end()  # always last line of test

    def PYDSO030MEAS(self):
        """ Measure Stuff... no pass/fail

        {"id": "PYDSO030MEAS",   "enable": true },
        """
        ctx = self.item_start()  # always first line of test

        self.shared_lock(self.DSO).acquire()

        vpp = self.dso.query(':MEASure:VPP? CHANnel{}'.format(self.chan))
        value = float(vpp)
        _result, _bullet = ctx.record.measurement("VPP{}".format(self.chan), value, ResultAPI.UNIT_VOLTS)

        dc = self.dso.query(':MEASure:DUTYcycle? CHANnel{}'.format(self.chan))
        value = float(vpp)
        _result, _bullet = ctx.record.measurement("DUTYCYCLE{}".format(self.chan), dc, ResultAPI.UNIT_VOLTS)

        # TODO: add more measurement examples...

        time.sleep(0.1) # give it some time to sit here, else its too fast
        self.shared_lock(self.DSO).release()
        self.item_end()  # always last line of test

    def PYDSO999TRDN(self):
        ctx = self.item_start()  # always first line of test

        self.item_end()  # always last line of test

