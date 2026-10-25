"""Tests for the barcode count example (scripts#41): scanners driver, count_0.scr
program, make_barcodes.py, and prism_dev sub defaults.

Run from the scripts repo root: python -m pytest tests
"""
import re
import jstyleson
import pytest

import prism_dev
from core.shared_state import SharedState
from public.prism.api import ResultAPI
from public.prism.drivers.scanners import hwdrv_scanners
from public.prism.drivers.scanners.Scanners import Scanner, DRIVER_TYPE
from public.prism.scripts.example.barcode_count_v0 import make_barcodes
from public.prism.scripts.example.barcode_count_v0.tst00xx import tst00xx

SCRIPT = "public/prism/scripts/example/barcode_count_v0/count_0.scr"
DATALOGIC = b"Datalogic ADC  Inc."


def load_script():
    with open(SCRIPT) as f:
        return jstyleson.loads(f.read())


# ---- Scanner player ---------------------------------------------------------

def test_player_toggles_jig_open_closed():
    s = Scanner()
    assert [s.jig_closed_always() for _ in range(4)] == [False, True, False, True]


def test_stop_player_holds_jig_open_until_start():
    s = Scanner()
    s.stop_player()
    assert s.player_stopped()
    assert not any(s.jig_closed_always() for _ in range(4))
    s.start_player()
    assert any(s.jig_closed_always() for _ in range(2))


# ---- HWDriver discovery -----------------------------------------------------

class FakeDevice:
    def __init__(self, path, manufacturer):
        self.device_path = path
        self.attributes = {} if manufacturer is None else {"manufacturer": manufacturer}


def fake_udev(monkeypatch, devices):
    class FakeContext:
        def list_devices(self, **kwargs):
            return devices
    monkeypatch.setattr(hwdrv_scanners.pyudev, "Context", FakeContext)
    monkeypatch.setattr(hwdrv_scanners, "pub_notice", lambda *a, **k: None)


def test_discover_one_scanner(monkeypatch):
    fake_udev(monkeypatch, [FakeDevice("/usb/3-1", b"Logitech"),
                            FakeDevice("/usb/3-2", DATALOGIC),
                            FakeDevice("/usb/3-3", None)])
    num, dtype, drivers = hwdrv_scanners.HWDriver().discover_channels()
    assert (num, dtype, len(drivers)) == (1, DRIVER_TYPE, 1)
    assert drivers[0]["unique_id"] == "/usb/3-2"
    assert drivers[0]["play"] == drivers[0]["hwdrv"].jig_closed_always


def test_discover_no_scanner_is_error(monkeypatch):
    # [Unhappy] no scanner attached
    fake_udev(monkeypatch, [FakeDevice("/usb/3-1", b"Logitech")])
    num, dtype, drivers = hwdrv_scanners.HWDriver().discover_channels()
    assert num < 0 and drivers == []


def test_discover_two_scanners_is_one_channel(monkeypatch):
    # [Edge] keyboard mode scans cannot be told apart, so still one channel
    fake_udev(monkeypatch, [FakeDevice("/usb/3-4", DATALOGIC),
                            FakeDevice("/usb/3-2", DATALOGIC)])
    num, _, drivers = hwdrv_scanners.HWDriver().discover_channels()
    assert num == 1 and len(drivers) == 1
    assert drivers[0]["unique_id"] == "/usb/3-2"


# ---- TST000_Scan ------------------------------------------------------------

@pytest.fixture
def scan_item():
    """ :return: function(textbox_response) -> (record, scanner) """
    script = prism_dev.apply_sub_defaults(load_script())
    item = script["tests"][0]["items"][0]

    def run(response):
        ss = SharedState()
        scanner = Scanner()
        ss.add_drivers(DRIVER_TYPE, [{"id": 0, "hwdrv": scanner}])
        con = prism_dev.ChanCon(0, script, ss, SCRIPT)
        con._item, con._options = item, script["tests"][0]["options"]
        t = tst00xx(con, 0, ss)
        t.input_textbox = lambda *a, **k: response
        t.TST000_Scan()
        return con.record, scanner
    return run


def test_scan_good_barcode(scan_item):
    record, scanner = scan_item({"success": True, "textbox": "P001-S00123\n", "err": None})
    assert record.record_test_get_result() == ResultAPI.RECORD_RESULT_PASS
    assert record._record["info"]["product"] == "P001"
    assert record._record["keys"]["key0"] == "sn:00123"
    assert not scanner.player_stopped()


def test_scan_bad_format_fails(scan_item):
    # [Unhappy] scan does not match P###-S#####
    record, scanner = scan_item({"success": True, "textbox": "P001-00123", "err": None})
    assert record.record_test_get_result() == ResultAPI.RECORD_RESULT_FAIL
    assert "keys" not in record._record or not record._record["keys"]
    assert not scanner.player_stopped()


def test_scan_timeout_stops_player(scan_item):
    # [Unhappy] no scan before the item timeout, stop restarting the script
    record, scanner = scan_item({"success": False, "textbox": None, "err": "Aborted"})
    assert record.record_test_get_result() == ResultAPI.RECORD_RESULT_FAIL
    assert scanner.player_stopped()


def test_lot_regex():
    regex = load_script()["subs"]["Lot"]["regex"]
    assert re.match(regex, "20261025-01")
    for bad in ["2026102501", "20261325-01", "20261000-01", "20261025-1", "19991025-01"]:
        assert not re.match(regex, bad), bad


# ---- make_barcodes ----------------------------------------------------------

def test_barcode_strings_match_script_regex():
    regex = load_script()["tests"][0]["items"][0]["args"]["regex"]
    codes = make_barcodes.barcode_strings("P001", 99998, 2)
    assert codes == ["P001-S99998", "P001-S99999"]
    assert all(re.match(regex, c) for c in codes)


def test_make_pdf(tmp_path):
    out = tmp_path / "codes.pdf"
    make_barcodes.make_pdf(make_barcodes.barcode_strings("P001", 1, 13), str(out))
    assert out.read_bytes().startswith(b"%PDF")


# ---- prism_dev sub defaults -------------------------------------------------

def test_apply_sub_defaults_uses_default_then_first_choice():
    script = prism_dev.apply_sub_defaults(load_script())
    assert "subs" not in script
    assert script["info"]["lot"] == "20261025-01"
    assert script["info"]["location"] == "canada/ontario/milton"


def test_apply_sub_defaults_num_type():
    script = {"subs": {"Max": {"type": "num", "widget": "select", "choices": [9.0, 10.0]}},
              "tests": [{"items": [{"id": "T", "args": {"max": "%%Max"}}]}]}
    script = prism_dev.apply_sub_defaults(script)
    assert script["tests"][0]["items"][0]["args"]["max"] == 9.0


def test_apply_sub_defaults_no_default_uses_placeholder():
    # [Edge] a textinput sub with no default gets a placeholder, by type
    script = {"subs": {"Lot": {"type": "str", "widget": "textinput"},
                       "Min": {"type": "num", "widget": "textinput"}},
              "info": {"lot": "%%Lot"},
              "tests": [{"items": [{"id": "T", "args": {"min": "%%Min"}}]}]}
    script = prism_dev.apply_sub_defaults(script)
    assert script["info"]["lot"] == prism_dev.SUB_PLACEHOLDER_STR
    assert script["tests"][0]["items"][0]["args"]["min"] == prism_dev.SUB_PLACEHOLDER_NUM
