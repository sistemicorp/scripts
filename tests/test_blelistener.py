"""Tests for public/prism/drivers/ble_listener/BLEListener.py.

Run from the scripts repo root: python -m pytest tests
No BLE hardware is used, BleakScanner is replaced with a fake.
"""
import asyncio
import datetime

import pytest
from bleak.exc import BleakError
from bleak.backends.scanner import AdvertisementData

from public.prism.drivers.ble_listener import BLEListener as ble_module
from public.prism.drivers.ble_listener.BLEListener import BLEListener

UID_A = "abbaff00-e56a-484c-b832-8b17cf6cbfe8"
UID_B = "0000180f-0000-1000-8000-00805f9b34fb"
SCAN_DELAY_S = 0.05
START_TIMEOUT_S = 2.0


def make_ad(service_uuids, rssi=-50):
    return AdvertisementData(local_name=None, manufacturer_data={}, service_data={},
                             service_uuids=service_uuids, tx_power=None, rssi=rssi,
                             platform_data=())


def running_listener():
    """Listener that accepts lookups without starting the scanner."""
    ble = BLEListener(scan_delay_s=SCAN_DELAY_S)
    ble._running = True
    return ble


class FakeScanner:
    """Stands in for BleakScanner, start_error is raised by start()."""
    start_error = None
    start_delay_s = 0.0
    stops = 0

    def __init__(self, detection_callback=None):
        self.detection_callback = detection_callback

    async def start(self):
        await asyncio.sleep(FakeScanner.start_delay_s)
        if FakeScanner.start_error:
            raise FakeScanner.start_error

    async def stop(self):
        FakeScanner.stops += 1


@pytest.fixture
def fake_scanner(monkeypatch):
    FakeScanner.start_error = None
    FakeScanner.start_delay_s = 0.0
    FakeScanner.stops = 0
    monkeypatch.setattr(ble_module, "BleakScanner", FakeScanner)
    return FakeScanner


def test_device_found_stores_every_service_uuid():
    ble = running_listener()
    ble._device_found(None, make_ad([UID_B, UID_A]))
    assert sorted(ble.uids()) == sorted([UID_A, UID_B])


def test_device_found_ignores_ad_without_service_uuids():
    # [Edge] beacons with only manufacturer data are not stored
    ble = running_listener()
    ble._device_found(None, make_ad([]))
    assert ble.uids() == []


def test_device_found_keeps_latest_rssi_and_first_seen():
    ble = running_listener()
    ble._device_found(None, make_ad([UID_A], rssi=-80))
    first_seen = ble._uids[UID_A]["first_seen"]
    ble._device_found(None, make_ad([UID_A], rssi=-40))
    success, ad = ble.is_uid_present(UID_A, remove=False)
    assert success and ad["rssi"] == -40
    assert ad["first_seen"] == first_seen


def test_is_uid_present_remove_pops_immediately():
    ble = running_listener()
    ble._device_found(None, make_ad([UID_A]))
    assert ble.is_uid_present(UID_A)[1] is not None
    # the next DUT with the same UID must be scanned again
    assert ble.is_uid_present(UID_A) == (True, None)


def test_is_uid_present_without_remove_keeps_uid():
    ble = running_listener()
    ble._device_found(None, make_ad([UID_A]))
    ble.is_uid_present(UID_A, remove=False)
    assert ble.is_uid_present(UID_A, remove=False)[1] is not None


def test_is_uid_present_ignores_case():
    # [Edge] scripts may write the UUID in upper case
    ble = running_listener()
    ble._device_found(None, make_ad([UID_A.upper()]))
    assert ble.is_uid_present(UID_A.upper())[1] is not None


def test_is_uid_present_not_running_is_error():
    # [Unhappy] scanner not running is an internal error, not "not found"
    ble = BLEListener()
    assert ble.is_uid_present(UID_A) == (False, None)


def test_uid_not_seen_within_expire_time_is_removed():
    # [Edge] expiry is from last seen
    ble = running_listener()
    ble._device_found(None, make_ad([UID_A]))
    ble._uids[UID_A]["timestamp"] -= ble._expire_time + datetime.timedelta(seconds=1)
    assert ble.is_uid_present(UID_A) == (True, None)


def test_start_scanner_success_and_close(fake_scanner):
    ble = BLEListener(scan_delay_s=SCAN_DELAY_S)
    assert ble.start_scanner(START_TIMEOUT_S) is True
    assert ble.is_running()
    ble.close()
    assert not ble.is_running()
    assert ble._thread is None  # scanner thread exited
    assert fake_scanner.stops >= 1


def test_start_scanner_after_close_restarts(fake_scanner):
    ble = BLEListener(scan_delay_s=SCAN_DELAY_S)
    assert ble.start_scanner(START_TIMEOUT_S)
    ble.close()
    assert ble.start_scanner(START_TIMEOUT_S)
    ble.close()


@pytest.mark.parametrize("error", [BleakError("No Bluetooth adapters found."),
                                   FileNotFoundError(2, "No such file or directory")])
def test_start_scanner_reports_ble_not_available(fake_scanner, error):
    # [Unhappy] scripts#11: no adapter, or D-Bus not reachable
    fake_scanner.start_error = error
    ble = BLEListener(scan_delay_s=SCAN_DELAY_S)
    assert ble.start_scanner(START_TIMEOUT_S) is False
    assert not ble.is_running()
    assert ble.is_uid_present(UID_A) == (False, None)


def test_start_scanner_timeout(fake_scanner):
    # [Unhappy] scanner start hangs, then the late scanner exits by itself
    fake_scanner.start_delay_s = 0.3
    ble = BLEListener(scan_delay_s=SCAN_DELAY_S)
    assert ble.start_scanner(timeout_s=0.05) is False
    assert not ble.is_running()
    ble.close()
    assert ble._thread is None
