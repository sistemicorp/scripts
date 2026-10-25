"""Tests for public/prism/drivers/A4401_BOND (BOND driver, CLI and hwdrv).

Run from the scripts repo root: python -m pytest tests
No BOND hardware is used, the simpleRPC link is replaced with a fake.
"""
import json
import logging
import os
import runpy
import sys
import types

import pytest
from serial import SerialException

from public.prism.drivers.A4401_BOND import A4401_BOND as bond_module
from public.prism.drivers.A4401_BOND import hwdrv_A4401_BOND as hwdrv_module
from public.prism.drivers.A4401_BOND.A4401_BOND import A4401_BOND

DRIVER_DIR = os.path.dirname(bond_module.__file__)
HDR_DEF = os.path.join(DRIVER_DIR, "pogo_hdr_definition._json")
EXAMPLE_HDR_DEF = "public/prism/scripts/example/BOND_v0/assets/pogo_hdr_definition._json"
CLI = os.path.join(DRIVER_DIR, "A4401_BOND_cli.py")
FW_VERSION = A4401_BOND(None).my_version

MINIMAL_HDR = {
    "gpo_mv": 3300, "gpi_mv": 1000,
    "1": {"mode": "DAC,GPO", "port": "10,1"},
    "2": {"mode": "ADC", "port": "6"},
    "3": {"mode": "GPI", "port": "0"},
    "4": {"mode": None, "port": None},
}


class FakeRPC:
    """Stands in for simple_rpc Interface, answers every method with success."""

    def __init__(self, results=None, raises=None):
        self.calls = []
        self.results = results or {}
        self.raises = raises or {}
        self.device = {"methods": {"version": {}, "status": {}}}

    def call_method(self, name, *args):
        self.calls.append((name, args))
        if name in self.raises:
            raise self.raises[name]
        result = self.results.get(name, {})
        if callable(result):
            result = result(*args)
        if name == "version":
            result = {"version": FW_VERSION}
        if name == "status":
            result = {"setup_fail_code": 0}
        if name == "bist_voltage":
            result = {"pass": True}
        success = not (isinstance(result, dict) and "error" in result)
        return json.dumps({"success": success, "method": name, "result": result})

    def names(self):
        return [c[0] for c in self.calls]

    def close(self):
        pass


def write_hdr(tmp_path, headers, calibrate=False):
    config = dict(headers)
    config["calibrate_battery_emulator"] = calibrate
    path = tmp_path / "hdr._json"
    path.write_text("// comment line\n" + json.dumps(config))
    return str(path)


def make_bond(header_def=HDR_DEF, rpc=None):
    bond = A4401_BOND("/dev/null", loggerIn=logging.getLogger("test.bond"),
                      header_def_filename=header_def)
    bond.rpc = rpc or FakeRPC()
    return bond


def test_shipped_header_files_are_identical():
    with open(HDR_DEF) as a, open(EXAMPLE_HDR_DEF) as b:
        assert a.read() == b.read()


def test_shipped_header_file_loads():
    bond = make_bond()
    assert bond._load_config(HDR_DEF)
    assert bond._hdr_pins[1][1] == {"GPO": 1}
    assert bond._hdr_pins[1][9] == {"ADC": 6}
    assert bond._hdr_pins[3][16] == {}


def test_vbus_port_is_always_configured(tmp_path):
    hdr = {"gpo_mv": 3300, "gpi_mv": 1000, "2": {"mode": "GPO", "port": "8"}}
    bond = make_bond(write_hdr(tmp_path, {"3": hdr}))
    assert bond.init()
    hdr_init = [c for c in bond.rpc.calls if c[0] == "bond_max_hdr_init"]
    assert hdr_init == [("bond_max_hdr_init",
                         (3, [11], 1, [], 0, [8, 9], 2, [], 0, 3300, 1000))]


def test_init_sends_header_ports(tmp_path):
    bond = make_bond(write_hdr(tmp_path, {"1": MINIMAL_HDR}))
    assert bond.init()
    hdr_init = [c for c in bond.rpc.calls if c[0] == "bond_max_hdr_init"]
    assert hdr_init == [("bond_max_hdr_init",
                         (1, [6, 11], 2, [10], 1, [1], 1, [0], 1, 3300, 1000))]
    assert bond.rpc.names()[-1] == "reset"


def test_init_without_battery_calibration(tmp_path):
    """[Edge] calibrate_battery_emulator false used to fail init (iox_vbat_con gate)"""
    bond = make_bond(write_hdr(tmp_path, {"1": MINIMAL_HDR}, calibrate=False))
    assert bond.init()
    assert "bond_batt_emu_cal" not in bond.rpc.names()


def test_init_with_battery_calibration(tmp_path):
    bond = make_bond(write_hdr(tmp_path, {"1": MINIMAL_HDR}, calibrate=True))
    assert bond.init()
    assert "bond_batt_emu_cal" in bond.rpc.names()


def test_init_configure_headers_false(tmp_path):
    bond = make_bond(write_hdr(tmp_path, {"1": MINIMAL_HDR}))
    assert bond.init(configure_headers=False)
    assert "bond_max_hdr_init" not in bond.rpc.names()
    assert bond.bond_max_hdr_adc(1, 2)["success"]


def test_init_version_mismatch():
    """[Unhappy]"""
    rpc = FakeRPC()
    rpc.call_method = lambda name, *a: json.dumps(
        {"success": True, "method": name, "result": {"version": "0.0.0"}})
    bond = make_bond(rpc=rpc)
    assert not bond.init()


@pytest.mark.parametrize("pins, reason", [
    ({"1": {"mode": "ADC", "port": "6"}, "2": {"mode": "DAC", "port": "6"}}, "port used twice"),
    ({"1": {"mode": "FOO", "port": "6"}}, "invalid mode"),
    ({"1": {"mode": "DAC,GPO", "port": "6"}}, "mode/port length mismatch"),
    ({"1": {"mode": "ADC", "port": "11"}}, "port 11 is reserved"),
    ({"1": {"mode": "ADC", "port": "x"}}, "port not a number"),
])
def test_load_config_rejects(tmp_path, pins, reason):
    """[Unhappy] these were logged and skipped, or overflowed the firmware init table"""
    hdr = {"gpo_mv": 3300, "gpi_mv": 1000}
    hdr.update(pins)
    bond = make_bond()
    assert not bond._load_config(write_hdr(tmp_path, {"1": hdr})), reason


def test_load_config_rejects_vbus_port(tmp_path):
    """[Unhappy] HDR3 port 9 is the VBUS relay, the driver owns it"""
    hdr = {"gpo_mv": 3300, "gpi_mv": 1000, "16": {"mode": "GPO", "port": "9"}}
    bond = make_bond()
    assert not bond._load_config(write_hdr(tmp_path, {"3": hdr}))


def test_ldo_set_range():
    """[Unhappy]"""
    bond = make_bond()
    assert not bond.bond_ldo_set(599)["success"]
    assert not bond.bond_ldo_set(3901)["success"]
    assert bond.bond_ldo_set(3300)["success"]
    assert bond.rpc.calls == [("bond_ldo_set", (3300,))]


@pytest.mark.parametrize("levels", [
    {"gpi_mv": 1000},                       # gpo_mv missing, used to raise KeyError
    {"gpo_mv": 10001, "gpi_mv": 1000},
    {"gpo_mv": 3300, "gpi_mv": 2501},
])
def test_load_config_rejects_levels(tmp_path, levels):
    """[Unhappy]"""
    bond = make_bond()
    assert not bond._load_config(write_hdr(tmp_path, {"1": levels}))


def test_dac_on_dual_mode_pin(tmp_path):
    """[Edge] a "DAC,GPO" pin was rejected for both modes"""
    bond = make_bond(write_hdr(tmp_path, {"1": MINIMAL_HDR}))
    assert bond._load_config(bond._header_def_filename)
    assert bond.bond_max_hdr_dac(1, 1, 3300)["success"]
    assert bond.rpc.calls[-1] == ("bond_max_hdr_dac", (1, 10, 3300))
    assert bond.bond_max_hdr_gpo(1, 1, True)["success"]
    assert bond.rpc.calls[-1] == ("bond_max_hdr_gpo", (1, 1, True))


def test_header_pin_mode_errors(tmp_path):
    """[Unhappy] errors name the called method"""
    bond = make_bond(write_hdr(tmp_path, {"1": MINIMAL_HDR}))
    assert bond._load_config(bond._header_def_filename)
    r = bond.bond_max_hdr_dac(1, 2, 1000)
    assert not r["success"] and r["method"] == "bond_max_hdr_dac"
    assert not bond.bond_max_hdr_gpi(1, 2)["success"]
    assert not bond.bond_max_hdr_adc(1, 99)["success"]
    assert not bond.bond_max_hdr_adc(5, 1)["success"]
    assert not bond.bond_max_hdr_dac(1, 1, 10001)["success"]
    assert bond.bond_max_hdr_gpi(1, 3)["success"]
    assert bond.rpc.names() == ["bond_max_hdr_gpi"]


def test_header_api_before_config():
    """[Unhappy]"""
    bond = make_bond()
    assert not bond.bond_max_hdr_adc(1, 2)["success"]


def test_serial_error_is_a_failed_response():
    """[Unhappy] a USB unplug raised SerialException into the test script"""
    bond = make_bond(rpc=FakeRPC(raises={"vbat_read": SerialException("unplugged")}))
    r = bond.vbat_read()
    assert r["success"] is False
    assert "unplugged" in r["result"]["error"]


def test_call_when_closed():
    """[Unhappy]"""
    bond = make_bond()
    bond.close()
    assert not bond.reset()["success"]


@pytest.mark.parametrize("state, closed", [(1, True), (0, False)])
def test_jig_closed_detect(state, closed):
    bond = make_bond(rpc=FakeRPC(results={"read_gpio": {"state": state}}))
    assert bond.jig_closed_detect() is closed


def test_jig_closed_detect_error():
    """[Unhappy]"""
    bond = make_bond(rpc=FakeRPC(results={"read_gpio": {"error": "x"}}))
    assert bond.jig_closed_detect() is None


def test_jig_close_check_invalid_gpio(monkeypatch):
    """[Unhappy] the range check was MIN < x > MAX"""
    bond = make_bond()
    monkeypatch.setattr(bond, "JIG_CLOSE_GPIO", 42)
    assert not bond._jig_close_check()
    monkeypatch.setattr(bond, "JIG_CLOSE_GPIO", -1)
    assert not bond._jig_close_check()
    monkeypatch.setattr(bond, "JIG_CLOSE_GPIO", 6)
    assert bond._jig_close_check()


def test_list_methods():
    """[Edge] list() used a missing attribute"""
    assert make_bond().list() == ["version", "status"]


class FakeCliBond:
    """Stands in for A4401_BOND in the CLI, every header ADC read fails."""
    closed = False

    def __init__(self, *args, **kwargs):
        pass

    def init(self, configure_headers=True):
        FakeCliBond.configure_headers = configure_headers
        return True

    def bond_max_hdr_adc(self, hdr, pin):
        return {"success": False, "result": {"error": "bad pin"}}

    def version(self):
        return {"success": True}

    def close(self):
        FakeCliBond.closed = True


@pytest.mark.parametrize("argv, code", [
    (["-p", "x", "bond_max_hdr_adc", "--header", "1", "--pin", "6"], 1),
    (["-p", "x", "-n", "version"], 0),
])
def test_cli_exit_code(monkeypatch, argv, code):
    """[Unhappy] the CLI always exited 0"""
    fake = types.ModuleType("A4401_BOND")
    fake.A4401_BOND = FakeCliBond
    monkeypatch.setitem(sys.modules, "A4401_BOND", fake)
    monkeypatch.setattr(sys, "argv", ["A4401_BOND_cli.py"] + argv)
    with pytest.raises(SystemExit) as e:
        runpy.run_path(CLI, run_name="__main__")
    assert e.value.code == code
    assert FakeCliBond.closed
    assert FakeCliBond.configure_headers == ("-n" not in argv)


class FakeUdevDevice:
    def __init__(self, node, path):
        self.device_node = node
        self.device_path = path

    def find_parent(self, subsystem, device_type):
        return types.SimpleNamespace(attributes={"manufacturer": b"Teensyduino"})


class FakeHwdrvBond:
    """Stands in for A4401_BOND in the hwdrv, init fails on /dev/ttyACM9."""
    closed = []

    def __init__(self, port, loggerIn=None, header_def_filename=None):
        self.port = port

    def init(self):
        return self.port != "/dev/ttyACM9"

    def unique_id(self):
        return {"success": True, "result": {"unique_id": "uid-" + self.port}}

    def close(self):
        FakeHwdrvBond.closed.append(self.port)

    def jig_closed_detect(self):
        return False

    def show_pass_fail(self, p=False, f=False, o=False):
        pass

    def jig_reset(self):
        pass


@pytest.fixture
def fake_udev(monkeypatch):
    devices = []
    context = types.SimpleNamespace(list_devices=lambda subsystem: devices)
    monkeypatch.setattr(hwdrv_module.pyudev, "Context", lambda: context)
    monkeypatch.setattr(hwdrv_module, "A4401_BOND", FakeHwdrvBond)
    monkeypatch.setattr(hwdrv_module, "pub_notice", lambda *a, **k: None)
    FakeHwdrvBond.closed = []
    return devices


def test_hwdrv_discovers_and_orders_by_usb_path(fake_udev):
    fake_udev += [FakeUdevDevice("/dev/ttyACM2", "/usb3/3-2.4"),
                  FakeUdevDevice("/dev/ttyACM1", "/usb3/3-2.1"),
                  FakeUdevDevice("/dev/ttyS0", "/serial")]
    num, driver_type, drivers = hwdrv_module.HWDriver().discover_channels("hdr._json")
    assert num == 2 and driver_type == "A4401_BOND"
    assert [(d["id"], d["port"]) for d in drivers] == [(0, "/dev/ttyACM1"), (1, "/dev/ttyACM2")]
    assert drivers[0]["unique_id"] == "uid-/dev/ttyACM1"


def test_hwdrv_init_failure_closes_port(fake_udev):
    """[Unhappy] a failed init left the serial port open, and none found returned 0"""
    fake_udev.append(FakeUdevDevice("/dev/ttyACM9", "/usb3/3-2.9"))
    num, _, drivers = hwdrv_module.HWDriver().discover_channels("hdr._json")
    assert num == -1 and drivers == []
    assert FakeHwdrvBond.closed == ["/dev/ttyACM9"]
