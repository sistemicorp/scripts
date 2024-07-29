#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2023
Martin Guthrie

"""
import time
import asyncio
import datetime
from threading import Timer, Lock
from bleak import BleakScanner, BleakError
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

try:
    # run locally
    from stublogger import StubLogger
except:
    # run from prism
    from public.prism.drivers.common.stublogger import StubLogger


VERSION = "0.1.0"
DRIVER_TYPE = "BLE_LISTENER"


class BLEListener(object):
    """ Prism HW Driver for BLE Listener
    - monitor BLE, gather/store beacon values
    - this example stores BLE UUIDS data in a dict with the key being
      the UID.  rssi and time of first detection is recorded as well
    - When a UID has been around for EXPIRE_UID_TIME_SECONDS it will be removed

    """

    EXPIRE_UID_TIME_SECONDS = 60 * 5
    SCAN_SLEEP_TIME_S = 0.5

    def __init__(self,
                 scan_delay_s=SCAN_SLEEP_TIME_S,
                 expire_time_s=EXPIRE_UID_TIME_SECONDS,
                 loggerIn=None):
        if loggerIn: self.logger = loggerIn
        else: self.logger = StubLogger()

        self._uniqie_id = 0
        self._id = 0
        self._running = False
        self._expire_time = expire_time_s
        self._scan_delay_s = scan_delay_s
        self._scanner = BleakScanner(detection_callback=self._device_found)
        self._uids = {}
        self._lock = Lock()
        self._last_prune = datetime.datetime.now()

    async def scanner(self):
        """ Scan for devices.
        """
        self.logger.info(f"Starting scanner with {self._scan_delay_s} seconds")
        try:
            while self._running:
                await self._scanner.start()
                await asyncio.sleep(self.SCAN_SLEEP_TIME_S)
                await self._scanner.stop()

        except BleakError as e:
            self.logger.error(e)
            self._running = False

        self.logger.info(f"{DRIVER_TYPE} closed")

    def _device_found(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """ Decode iBeacon.
        """
        self.logger.debug(f"manu  : {advertisement_data.manufacturer_data}")
        self.logger.debug(f" data : {advertisement_data.service_data}")
        self.logger.debug(f" uids : {advertisement_data.service_uuids}")

        if not advertisement_data.service_uuids: return

        with self._lock:
            uid = advertisement_data.service_uuids[0]
            if uid not in self._uids:
                self.logger.info(f"uuid: {uid}")
                self._uids[uid] = {"rssi": advertisement_data.rssi,
                                   "tx": advertisement_data.tx_power,
                                   "ad": advertisement_data,  # store everything, dups rssi and tx
                                   "timestamp": datetime.datetime.now(),
                                   "_remove": False,
                                   }

            # prune any old entries
            past = datetime.datetime.now() - datetime.timedelta(seconds=self._expire_time)
            if past > self._last_prune:
                self._uids = {k: v for k, v in self._uids.items() if v["timestamp"] > past}
                self._last_prune = datetime.datetime.now()

            # prune any devices that have been flagged for removal
            self._uids = {k: v for k, v in self._uids.items() if not v["_remove"]}

            self.logger.info(f"{len(self._uids)} items")

    def version(self):
        """ Version of this driver.  Typically, this would be coming
        from the remote hardware.  The version of remote software/hardware
        should be something that is expected.

        :return:
        """
        return VERSION

    def unique_id(self):
        """ A string that uniquely identifies this piece of hardware.
        Used for tracking purposes.

        :return: string
        """
        return "{:04}".format(self._uniqie_id)

    def id(self):
        """ The id is related to the channel/slot number which is related
        to the physical locations of the test jigs.  Prism will arrange the
        slots such that the lowest id is channel/slot 0, etc

        :return: integer
        """
        return self._id

    def close(self):
        """ Always called at the end of a test sequence by Prism
        - perform any reset, or closing of the hardware if the testing is done, or ended
        - note the result state (Pass|Fail) of the DUT is not known and should not be assumed,
          meaning that this hardware may be in an unknown state.  This close() function
          allows you to get back to a known state, if required.

        :return: None
        """
        self.logger.info("closing...")
        self._running = False

    def is_running(self):
        return self._running

    def _timer_start_scan(self):
        self.logger.info("starting BLE scanner")
        asyncio.run(self.scanner())
        self.logger.info("async completed")

    def start_scanner(self):
        # called by hardware driver init
        if self._running: return
        self._running = True
        Timer(0.1, self._timer_start_scan).start()

    def is_uid_present(self, uid: str, remove: bool=True):
        """ Determine if BLE Advertisement was received
        - DUT advertised UID must be known
        - this function likely needs to be polled until your
          DUT UID is scanned
        - use a suitable timeout for when DUT ad is not received

        Expected usage,
            polling, found = 5, False
            while polling and not found:
                polling -= 1  # limit polling

                success, ad = ble_listener.is_uid_present(<uid>)
                if not success:
                    # internal error, return early

                if ad is not None:
                    found = True
                    break

                time.sleep(1.0)

            if found:
                # qualify other ad properties, rssi for example
                # if ad["rssi"] > -50: ...


        :param uid: <str>
        :return: True, <dict> if no error
                 False, None if error
        """
        if not self._running:
            self.logger.error("not running")
            return False, None

        with self._lock:
            if uid in self._uids:
                self._uids[uid]["_remove"] = remove  # mark for deletion
                return True, self._uids[uid]

        return True, None

    # ---------------------------------------------------------------------------------------------
    # Prism Player functions
    # - there are none
    # ---------------------------------------------------------------------------------------------
