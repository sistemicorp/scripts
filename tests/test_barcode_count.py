"""Tests for the barcode count example (scripts#41): scanners driver, count_0.scr
program, make_barcodes.py, and prism_dev sub defaults.

Run from the scripts repo root: python -m pytest tests
"""
import io
import re
import subprocess
import wave

import jstyleson
import pytest

import prism_dev
from core.shared_state import SharedState
from public.prism.api import ResultAPI
from public.prism.drivers.scanners import hwdrv_scanners
from public.prism.drivers.scanners import Scanners as scanners_mod
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


# ---- Ready beep ---------------------------------------------------------------

class FakeRun:
    """ Records subprocess.run calls, returns returncode """
    def __init__(self, returncode=0, raises=None):
        self.calls = []
        self.returncode = returncode
        self.raises = raises

    def __call__(self, cmd, **kwargs):
        self.calls.append((cmd, kwargs))
        if self.raises: raise self.raises
        return subprocess.CompletedProcess(cmd, self.returncode, stderr=b"no device")


class ListLogger:
    def __init__(self):
        self.warnings = []

    def warning(self, msg): self.warnings.append(msg)
    def info(self, *a, **k): pass


def beep_scanner(monkeypatch, run, aplay="/usr/bin/aplay"):
    monkeypatch.setattr(scanners_mod.shutil, "which", lambda name: aplay)
    monkeypatch.setattr(scanners_mod.subprocess, "run", run)
    return Scanner(loggerIn=ListLogger())


def test_beep_wav_is_valid_tone():
    with wave.open(io.BytesIO(scanners_mod.beep_wav())) as w:
        assert (w.getnchannels(), w.getsampwidth()) == (1, 2)
        assert w.getframerate() == scanners_mod.BEEP_RATE_HZ
        assert w.getnframes() == int(scanners_mod.BEEP_SEC * scanners_mod.BEEP_RATE_HZ)


def test_ready_beep_plays_wav_on_aplay_stdin(monkeypatch):
    run = FakeRun()
    s = beep_scanner(monkeypatch, run)
    s.ready_beep(0).join()
    cmd, kwargs = run.calls[0]
    assert cmd == ["/usr/bin/aplay", "-q", "-"]
    assert kwargs["input"] == scanners_mod.beep_wav()
    assert s.logger.warnings == []


def test_ready_beep_does_not_block(monkeypatch):
    run = FakeRun()
    s = beep_scanner(monkeypatch, run)
    timer = s.ready_beep(60)
    assert timer.is_alive() and run.calls == []
    timer.cancel()


def test_ready_beep_audio_device(monkeypatch):
    run = FakeRun()
    monkeypatch.setattr(scanners_mod, "AUDIO_DEVICE", "plughw:CARD=Generic_1,DEV=0")
    beep_scanner(monkeypatch, run)._play_beep()
    assert run.calls[0][0] == ["/usr/bin/aplay", "-q", "-D", "plughw:CARD=Generic_1,DEV=0", "-"]


def test_ready_beep_no_aplay_warns_once(monkeypatch):
    # [Unhappy] no aplay on the computer, the test carries on silently
    run = FakeRun()
    s = beep_scanner(monkeypatch, run, aplay=None)
    s._play_beep()
    s._play_beep()
    assert run.calls == [] and len(s.logger.warnings) == 1


@pytest.mark.parametrize("run", [FakeRun(returncode=1),
                                 FakeRun(raises=subprocess.TimeoutExpired("aplay", 5)),
                                 FakeRun(raises=OSError("no exec"))])
def test_ready_beep_aplay_error_warns_once(monkeypatch, run):
    # [Unhappy] aplay fails (no sound device, hangs, cannot run)
    s = beep_scanner(monkeypatch, run)
    s._play_beep()
    s._play_beep()
    assert len(s.logger.warnings) == 1


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
    assert drivers[0]["play_poll_sec"] == scanners_mod.PLAY_POLL_SEC


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

class QuietScanner(Scanner):
    """ Counts ready beeps instead of playing them """
    def __init__(self):
        super().__init__()
        self.beeps = 0

    def ready_beep(self, delay_sec=scanners_mod.BEEP_DELAY_SEC):
        self.beeps += 1


@pytest.fixture
def scan_item():
    """ :return: function(textbox_response, args=None) -> (record, scanner) """
    script = prism_dev.apply_sub_defaults(load_script())

    def run(response, args=None):
        item = dict(script["tests"][0]["items"][0])
        if args is not None: item["args"] = args
        ss = SharedState()
        scanner = QuietScanner()
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
    assert scanner.beeps == 1


@pytest.mark.parametrize("ready_beep, beeps", [(False, 0), (None, 1)])
def test_scan_ready_beep_arg(scan_item, ready_beep, beeps):
    # [Edge] ready_beep false turns the beep off, absent means on
    args = {"regex": load_script()["tests"][0]["items"][0]["args"]["regex"]}
    if ready_beep is not None: args["ready_beep"] = ready_beep
    _, scanner = scan_item({"success": True, "textbox": "P001-S00123", "err": None},
                           args=prism_dev.attrdict(args))
    assert scanner.beeps == beeps


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


# ---- prism_dev play_poll_sec --------------------------------------------------

def test_play_poll_sec_default_and_in_range():
    assert prism_dev.play_poll_sec(None) == prism_dev.PLAY_POLL_SEC
    assert prism_dev.play_poll_sec(scanners_mod.PLAY_POLL_SEC) == scanners_mod.PLAY_POLL_SEC
    assert prism_dev.play_poll_sec(prism_dev.PLAY_POLL_MAX_SEC) == prism_dev.PLAY_POLL_MAX_SEC


@pytest.mark.parametrize("value, expect", [(0, prism_dev.PLAY_POLL_MIN_SEC),
                                           (0.05, prism_dev.PLAY_POLL_MIN_SEC),
                                           (5, prism_dev.PLAY_POLL_MAX_SEC)])
def test_play_poll_sec_clamped(value, expect):
    # [Edge] outside the range is clamped to the nearest limit, like Prism
    assert prism_dev.play_poll_sec(value) == expect


@pytest.mark.parametrize("value", ["0.2", True])
def test_play_poll_sec_not_a_number_uses_default(value):
    # [Unhappy] a bad driver value type uses the default, like Prism
    assert prism_dev.play_poll_sec(value) == prism_dev.PLAY_POLL_SEC
