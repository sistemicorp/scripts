#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sistemi Corporation, copyright, all rights reserved, 2023
Martin Guthrie

"""
import asyncio
import datetime
from threading import Thread, Event, Lock
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

try:
    # run locally
    from stublogger import StubLogger
except ImportError:
    # run from prism
    from public.prism.drivers.common.stublogger import StubLogger


VERSION = "0.2.0"
DRIVER_TYPE = "BLE_LISTENER"


class BLEListener(object):
    """ Prism HW Driver for BLE Listener
    - monitor BLE, gather/store advertisement values
    - this example stores BLE service UUIDS data in a dict with the key being
      the UUID.  The latest rssi, tx power and advertisement are stored, with
      the time of first and last detection
    - When a UUID has not been seen for EXPIRE_UID_TIME_SECONDS it will be removed

    """

    EXPIRE_UID_TIME_SECONDS = 60 * 5
    SCAN_SLEEP_TIME_S = 0.5
    START_TIMEOUT_S = 10.0
    STOP_TIMEOUT_S = 5.0

    def __init__(self,
                 scan_delay_s=SCAN_SLEEP_TIME_S,
                 expire_time_s=EXPIRE_UID_TIME_SECONDS,
                 loggerIn=None):
        if loggerIn:
            self.logger = loggerIn
        else:
            self.logger = StubLogger()

        self._unique_id = 0
        self._id = 0
        self._running = False
        self._expire_time = datetime.timedelta(seconds=expire_time_s)
        self._scan_delay_s = scan_delay_s
        self._thread = None
        self._started = Event()
        self._uids = {}
        self._lock = Lock()

    async def scanner(self):
        """ Scan for devices.
        - signals self._started once the first scan started, or failed
        - any exception stops the scanner, self._running is False on exit
        """
        self.logger.info(f"Starting scanner with {self._scan_delay_s} seconds")
        try:
            # created here so the scanner belongs to this event loop
            scanner = BleakScanner(detection_callback=self._device_found)
            while self._running:
                await scanner.start()
                self._started.set()
                try:
                    await asyncio.sleep(self._scan_delay_s)
                finally:
                    await scanner.stop()

        except Exception as e:
            # BleakError when the adapter is missing or off, OSError when D-Bus is unreachable
            self.logger.error(f"{DRIVER_TYPE}: {type(e).__name__}: {e}")

        finally:
            self._running = False
            self._started.set()

        self.logger.info(f"{DRIVER_TYPE} closed")

    def _prune(self):
        """ Remove UUIDs not seen within the expire time, caller holds self._lock
        """
        past = datetime.datetime.now() - self._expire_time
        self._uids = {k: v for k, v in self._uids.items() if v["timestamp"] > past}

    def _device_found(self, device: BLEDevice, advertisement_data: AdvertisementData):
        """ Store advertisement by service UUID.
        """
        self.logger.debug(f"manu  : {advertisement_data.manufacturer_data}")
        self.logger.debug(f" data : {advertisement_data.service_data}")
        self.logger.debug(f" uids : {advertisement_data.service_uuids}")

        if not advertisement_data.service_uuids:
            return

        now = datetime.datetime.now()
        with self._lock:
            for uid in advertisement_data.service_uuids:
                uid = uid.lower()
                first_seen = now
                if uid in self._uids:
                    first_seen = self._uids[uid]["first_seen"]
                else:
                    self.logger.info(f"uuid: {uid}")

                self._uids[uid] = {"rssi": advertisement_data.rssi,
                                   "tx": advertisement_data.tx_power,
                                   "ad": advertisement_data,  # store everything, dups rssi and tx
                                   "first_seen": first_seen,
                                   "timestamp": now,  # last seen
                                   }

            self._prune()
            self.logger.debug(f"{len(self._uids)} items")

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
        return "{:04}".format(self._unique_id)

    def id(self):
        """ The id is related to the channel/slot number which is related
        to the physical locations of the test jigs.  Prism will arrange the
        slots such that the lowest id is channel/slot 0, etc

        :return: integer
        """
        return self._id

    def close(self):
        """ Called by Prism when the script is unloaded
        - stops the scanner, waits for the scanner thread to exit

        :return: None
        """
        self.logger.info("closing...")
        self._running = False
        self._join()

    def _join(self):
        if self._thread is None:
            return
        self._thread.join(self._scan_delay_s + self.STOP_TIMEOUT_S)
        if self._thread.is_alive():
            self.logger.error("scanner thread did not exit")
            return
        self._thread = None

    def is_running(self):
        return self._running

    def _thread_scan(self):
        self.logger.info("starting BLE scanner")
        asyncio.run(self.scanner())
        self.logger.info("async completed")

    def start_scanner(self, timeout_s=START_TIMEOUT_S):
        """ Start the scanner thread, and wait for the first scan to start
        - called by hardware driver init

        :param timeout_s: time to wait for the scan to start
        :return: True if scanning, False if BLE is not available
        """
        if self._running:
            return True
        self._join()  # a previous scanner may still be stopping

        self._running = True
        self._started.clear()
        self._thread = Thread(target=self._thread_scan, name=DRIVER_TYPE, daemon=True)
        self._thread.start()

        if not self._started.wait(timeout_s):
            self.logger.error(f"scanner did not start within {timeout_s} seconds")
            self._running = False
            return False

        return self._running

    def uids(self):
        """ UUIDs currently seen, for debugging

        :return: list of UUID strings
        """
        with self._lock:
            self._prune()
            return list(self._uids.keys())

    def is_uid_present(self, uid: str, remove: bool = True):
        """ Determine if BLE Advertisement was received
        - DUT advertised UID must be known
        - this function likely needs to be polled until your
          DUT UID is scanned
        - use a suitable timeout for when DUT ad is not received
        - remove=True removes the UID, so the next DUT (with the same UID)
          must be scanned again

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
        :param remove: <bool>
        :return: True, <dict> if no error, <dict> is None if UID not present
                 False, None if error
        """
        if not self._running:
            self.logger.error("not running")
            return False, None

        uid = uid.lower()
        with self._lock:
            self._prune()
            if remove:
                return True, self._uids.pop(uid, None)

            ad = self._uids.get(uid, None)
            if ad is None:
                return True, None
            return True, dict(ad)

    # ---------------------------------------------------------------------------------------------
    # Prism Player functions
    # - there are none
    # ---------------------------------------------------------------------------------------------
