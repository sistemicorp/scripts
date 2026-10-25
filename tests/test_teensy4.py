"""Tests for public/prism/drivers/teensy4 (Teensy4 driver, CLI and hwdrv).

Run from the scripts repo root: python -m pytest tests
No Teensy hardware is used, the simpleRPC link is replaced with a fake.
"""
import json
import logging
import os
import runpy
import sys
import threading
import types

import pytest
from serial import SerialException

from public.prism.drivers.teensy4 import Teensy4 as teensy_module
from public.prism.drivers.teensy4 import hwdrv_teensy4 as hwdrv_module
from public.prism.drivers.teensy4.Teensy4 import Teensy4

CLI = os.path.join(os.path.dirname(teensy_module.__file__), "Teensy4_cli.py")
FW_VERSION = Teensy4(None).my_version


class FakeRPC:
    """Stands in for simple_rpc Interface, answers every method with success."""

    def __init__(self, results=None, raises=None):
        self.calls = []
        self.results = results or {}
        self.raises = raises or {}
        self.device = {"methods": {"version": {}, "read_gpio": {}}}
        self.lock_held = []

    def call_method(self, name, *args):
        self.calls.append((name, args))
        if name in self.raises:
            raise self.raises[name]
        result = dict(self.results.get(name, {}))
        if name == "version":
            result = {"version": FW_VERSION}
        success = "error" not in result
        return json.dumps({"success": success, "method": name, "result": result})

    def close(self):
        pass


def make_teensy(rpc=None):
    t = Teensy4("/dev/null", loggerIn=logging.getLogger("test.teensy4"))
    t.rpc = rpc or FakeRPC()
    return t


def test_version_file_is_the_sketch_version():
    """[Edge] Python read a second copy of version.h in the vendored libraries"""
    assert Teensy4._version_file.endswith("server/teensy4_server/version.h")
    assert os.path.exists(Teensy4._version_file)


def test_init_sets_indicators_as_outputs():
    t = make_teensy()
    assert t.init()
    inits = [c[1] for c in t.rpc.calls if c[0] == "init_gpio"]
    assert inits == [(20, b"OUTPUT"), (21, b"OUTPUT"), (22, b"OUTPUT")]


def test_init_indicator_none(monkeypatch):
    """[Edge] a None indicator raised TypeError (None < 0)"""
    t = make_teensy()
    monkeypatch.setitem(t.TEST_INDICATORS, "other", {"gpio": None, "active_high": True})
    assert t.init()
    t.show_pass_fail(o=True)
    assert all(c[1][0] != None for c in t.rpc.calls if c[0] == "write_gpio")  # noqa: E711


@pytest.mark.parametrize("gpio", [42, -1])
def test_init_indicator_invalid(monkeypatch, gpio):
    """[Unhappy]"""
    t = make_teensy()
    monkeypatch.setitem(t.TEST_INDICATORS, "pass", {"gpio": gpio, "active_high": True})
    assert not t.init()


def test_init_gpio_failure_fails_init():
    """[Unhappy] init_gpio answers were ignored"""
    t = make_teensy(FakeRPC(results={"init_gpio": {"error": "bad pin"}}))
    assert not t.init()


def test_jig_close_check_invalid_gpio(monkeypatch):
    """[Unhappy] the range check was MIN < x > MAX"""
    t = make_teensy()
    for gpio, ok in ((42, False), (-1, False), (6, True)):
        monkeypatch.setattr(t, "JIG_CLOSE_GPIO", gpio)
        assert t._jig_close_check() is ok


@pytest.mark.parametrize("state, closed", [(0, True), (1, False)])
def test_jig_closed_detect(monkeypatch, state, closed):
    t = make_teensy(FakeRPC(results={"read_gpio": {"state": state}}))
    monkeypatch.setattr(t, "JIG_CLOSE_GPIO", 6)
    assert t.jig_closed_detect() is closed


def test_jig_closed_detect_uses_lock(monkeypatch):
    """[Edge] the player thread called the RPC without the lock, interleaving test RPCs"""
    t = make_teensy(FakeRPC(results={"read_gpio": {"state": 1}}))
    monkeypatch.setattr(t, "JIG_CLOSE_GPIO", 6)
    t._lock.acquire()
    done = threading.Event()
    threading.Thread(target=lambda: (t.jig_closed_detect(), done.set()), daemon=True).start()
    assert not done.wait(0.2)
    t._lock.release()
    assert done.wait(2)


@pytest.mark.parametrize("args, levels", [
    ({"p": True}, [(20, True), (21, False), (22, False)]),
    ({"f": True}, [(20, False), (21, True), (22, False)]),
    ({}, [(20, False), (21, False), (22, False)]),
])
def test_show_pass_fail(args, levels):
    t = make_teensy()
    t.show_pass_fail(**args)
    assert [c[1] for c in t.rpc.calls if c[0] == "write_gpio"] == levels


def test_show_pass_fail_active_low(monkeypatch):
    t = make_teensy()
    monkeypatch.setitem(t.TEST_INDICATORS, "pass", {"gpio": 20, "active_high": False})
    t.show_pass_fail(p=True)
    assert t.rpc.calls[0] == ("write_gpio", (20, False))


def test_serial_error_is_a_failed_response():
    """[Unhappy] a USB unplug raised SerialException into the test script"""
    t = make_teensy(FakeRPC(raises={"read_adc": SerialException("unplugged")}))
    r = t.read_adc(14)
    assert r["success"] is False and "unplugged" in r["result"]["error"]


def test_init_gpio_invalid_mode():
    """[Unhappy] the error used a 'value' key"""
    r = make_teensy().init_gpio(5, "FOO")
    assert r["success"] is False and "error" in r["result"]


def test_jig_reset_when_closed():
    """[Unhappy]"""
    t = make_teensy()
    t.close()
    assert not t.jig_reset()["success"]


def test_list_methods():
    """[Edge] list() used a missing attribute"""
    assert make_teensy().list() == ["version", "read_gpio"]


class FakeCliTeensy:
    def __init__(self, *args, **kwargs):
        pass

    def init(self):
        return True

    def read_gpio(self, pin):
        return {"success": pin != 99}

    def close(self):
        pass


@pytest.mark.parametrize("pin, code", [("99", 1), ("5", 0)])
def test_cli_exit_code(monkeypatch, pin, code):
    """[Unhappy] the CLI always exited 0"""
    fake = types.ModuleType("Teensy4")
    fake.Teensy4 = FakeCliTeensy
    monkeypatch.setitem(sys.modules, "Teensy4", fake)
    monkeypatch.setattr(sys, "argv", ["Teensy4_cli.py", "--port", "x", "read_gpio",
                                      "--pin-number", pin])
    with pytest.raises(SystemExit) as e:
        runpy.run_path(CLI, run_name="__main__")
    assert e.value.code == code


class FakeUdevDevice:
    def __init__(self, node, path, manufacturer=b"Teensyduino"):
        self.device_node = node
        self.device_path = path
        self.manufacturer = manufacturer

    def find_parent(self, subsystem, device_type):
        return types.SimpleNamespace(attributes={"manufacturer": self.manufacturer})


class FakeHwdrvTeensy:
    """Stands in for Teensy4 in the hwdrv, init fails on /dev/ttyACM9."""
    JIG_CLOSE_GPIO = None
    opened = []
    closed = []

    def __init__(self, port, loggerIn=None):
        self.port = port
        FakeHwdrvTeensy.opened.append(port)

    def init(self):
        return self.port != "/dev/ttyACM9"

    def unique_id(self):
        return {"success": True, "result": {"unique_id": "uid-" + self.port}}

    def close(self):
        FakeHwdrvTeensy.closed.append(self.port)

    def show_pass_fail(self, p=False, f=False, o=False):
        pass

    def jig_reset(self):
        pass


@pytest.fixture
def fake_udev(monkeypatch):
    devices = []
    context = types.SimpleNamespace(list_devices=lambda subsystem: devices)
    monkeypatch.setattr(hwdrv_module.pyudev, "Context", lambda: context)
    monkeypatch.setattr(hwdrv_module, "Teensy4", FakeHwdrvTeensy)
    monkeypatch.setattr(hwdrv_module, "pub_notice", lambda *a, **k: None)
    FakeHwdrvTeensy.opened = []
    FakeHwdrvTeensy.closed = []
    return devices


def test_hwdrv_only_opens_teensy_ports(fake_udev):
    """[Unhappy] every ttyACM was opened, a non-Teensy port hangs the simpleRPC handshake"""
    fake_udev += [FakeUdevDevice("/dev/ttyACM0", "/usb3/3-2.3", b"STMicroelectronics"),
                  FakeUdevDevice("/dev/ttyACM2", "/usb3/3-2.4"),
                  FakeUdevDevice("/dev/ttyACM1", "/usb3/3-2.1"),
                  FakeUdevDevice("/dev/ttyS0", "/serial")]
    num, driver_type, drivers = hwdrv_module.HWDriver().discover_channels()
    assert FakeHwdrvTeensy.opened == ["/dev/ttyACM2", "/dev/ttyACM1"]
    assert num == 2 and driver_type == "TEENSY4"
    assert [(d["id"], d["port"]) for d in drivers] == [(0, "/dev/ttyACM1"), (1, "/dev/ttyACM2")]
    assert drivers[0]["play"] is None


def test_hwdrv_init_failure_closes_port(fake_udev):
    """[Unhappy] a failed init left the serial port open, and none found returned 0"""
    fake_udev.append(FakeUdevDevice("/dev/ttyACM9", "/usb3/3-2.9"))
    num, _, drivers = hwdrv_module.HWDriver().discover_channels("args ignored")
    assert num == -1 and drivers == []
    assert FakeHwdrvTeensy.closed == ["/dev/ttyACM9"]
