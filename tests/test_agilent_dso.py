"""Tests for public/prism/drivers/agilent_dso_usb_1 hwdrv, USB or Ethernet interface.

Run from the scripts repo root: python -m pytest tests
No scope is used, pyvisa.ResourceManager is replaced with a fake.
"""
import pytest

from public.prism.drivers.agilent_dso_usb_1 import hwdrv_agilent_dso_usb_1 as hwdrv_module
from public.prism.drivers.agilent_dso_usb_1.hwdrv_agilent_dso_usb_1 import HWDriver

IDN = "AGILENT TECHNOLOGIES,DSO7104B,MY49520121,06.00.0003"
USB_DSO = "USB0::2391::5981::MY49520121::0::INSTR"


class FakeInstr:
    def __init__(self, idn):
        self.idn = idn
        self.writes = []
        self.closed = False

    def query(self, cmd):
        return self.idn + "\n"

    def write(self, cmd):
        self.writes.append(cmd)

    def close(self):
        self.closed = True


class FakeRM:
    """ :param instruments: {resource: idn}, a resource not listed fails to open """
    def __init__(self, instruments):
        self.instruments = instruments
        self.opened = []
        self.queries = []

    def list_resources(self, query="?*::INSTR"):
        self.queries.append(query)
        return tuple(r for r in self.instruments if r.startswith("USB"))

    def open_resource(self, resource, open_timeout=None):
        self.opened.append(resource)
        if resource not in self.instruments:
            raise ConnectionError("no route to {}".format(resource))
        return FakeInstr(self.instruments[resource])


@pytest.fixture
def rm(monkeypatch):
    """ :return: function to install a FakeRM with the given instruments,
                 and the USB hub port path of each USB serial number
    """
    def install(instruments, usb_paths=None):
        fake = FakeRM(instruments)
        monkeypatch.setattr(hwdrv_module.pyvisa, "ResourceManager", lambda: fake)
        monkeypatch.setattr(HWDriver, "_usb_port_paths", lambda self: usb_paths or {})
        return fake
    monkeypatch.setattr(hwdrv_module, "pub_notice", lambda msg, **kw: None)
    return install


def usb(serial):
    return "USB0::2391::5981::{}::0::INSTR".format(serial)


def idn(serial):
    return "AGILENT TECHNOLOGIES,DSO7104B,{},06.00.0003".format(serial)


def tcpip(ip):
    return "TCPIP0::{}::INSTR".format(ip)


@pytest.mark.parametrize("args", [None, {}, {"interface": "usb"}])
def test_usb_default_one_per_channel(rm, args):
    fake = rm({USB_DSO: IDN})
    num, dtype, drivers = HWDriver().discover_channels(args)
    assert (num, dtype) == (1, "AGILENT_DSO_USB_1")
    assert fake.opened == [USB_DSO]
    assert HWDriver.QUERY_STRING in fake.queries
    assert drivers[0]["id"] == 0
    assert drivers[0]["unique_id"] == "MY49520121"
    assert drivers[0]["hwdrv"].writes == ["*RST"]


def test_usb_shared(rm):
    rm({USB_DSO: IDN})
    num, _, drivers = HWDriver().discover_channels({"shared": True})
    assert num == 0
    assert len(drivers) == 1


def test_usb_channels_in_usb_port_order(rm):
    rm({usb("A"): idn("A"), usb("B"): idn("B")}, usb_paths={"A": (1, 3), "B": (1, 2)})
    num, _, drivers = HWDriver().discover_channels()
    assert num == 2
    assert [(d["id"], d["unique_id"]) for d in drivers] == [(0, "B"), (1, "A")]


def test_usb_unknown_port_sorts_last(rm):
    # [Edge] a scope not found by udev still gets a channel, after the others
    rm({usb("A"): idn("A"), usb("B"): idn("B")}, usb_paths={"B": (1, 2)})
    _, _, drivers = HWDriver().discover_channels()
    assert [d["unique_id"] for d in drivers] == ["B", "A"]


def test_usb_shared_with_two_scopes_is_error(rm):
    # [Unhappy] which scope would be the shared one is unknown
    rm({usb("A"): idn("A"), usb("B"): idn("B")})
    d = HWDriver()
    assert d.discover_channels({"shared": True})[0] == -1
    assert d.instrs == []


def test_usb_not_white_listed_is_skipped(rm):
    # [Edge] an unsupported scope is closed, the supported one gets channel 0
    rm({usb("A"): "AGILENT TECHNOLOGIES,DSO9999X,A,1", usb("B"): idn("B")},
       usb_paths={"A": (1, 1), "B": (1, 2)})
    num, _, drivers = HWDriver().discover_channels()
    assert num == 1
    assert drivers[0]["unique_id"] == "B"


def test_ethernet(rm):
    resource = tcpip("192.168.1.100")
    fake = rm({resource: IDN, USB_DSO: IDN})
    num, _, drivers = HWDriver().discover_channels({"interface": "ethernet", "ip": "192.168.1.100"})
    assert num == 1
    assert fake.opened == [resource]  # USB is not scanned
    assert fake.queries == []
    assert drivers[0]["hwdrv"].writes == ["*RST"]


def test_ethernet_ip_list_in_channel_order(rm):
    ips = ["10.0.0.2", "10.0.0.1"]
    rm({tcpip("10.0.0.1"): idn("A"), tcpip("10.0.0.2"): idn("B")})
    num, _, drivers = HWDriver().discover_channels({"interface": "ethernet", "ip": ips})
    assert num == 2
    assert [(d["id"], d["unique_id"]) for d in drivers] == [(0, "B"), (1, "A")]


def test_ethernet_shared(rm):
    rm({tcpip("10.0.0.1"): IDN})
    args = {"interface": "ethernet", "ip": ["10.0.0.1"], "shared": True}
    assert HWDriver().discover_channels(args)[0] == 0


def test_ethernet_shared_with_two_ips_is_error(rm):
    # [Unhappy]
    fake = rm({tcpip("10.0.0.1"): idn("A"), tcpip("10.0.0.2"): idn("B")})
    args = {"interface": "ethernet", "ip": ["10.0.0.1", "10.0.0.2"], "shared": True}
    assert HWDriver().discover_channels(args)[0] == -1
    assert fake.opened == []


def test_ethernet_unreachable_returns_error(rm):
    # [Unhappy]
    rm({})
    assert HWDriver().discover_channels({"interface": "ethernet", "ip": "10.0.0.1"})[0] == -1


def test_ethernet_one_missing_scope_is_error_and_closes_others(rm):
    # [Unhappy] skipping it would move the next scope to the wrong channel
    rm({tcpip("10.0.0.1"): idn("A")})
    d = HWDriver()
    args = {"interface": "ethernet", "ip": ["10.0.0.1", "10.0.0.2"]}
    assert d.discover_channels(args)[0] == -1
    assert d.instrs == []


def test_not_white_listed_is_closed(rm):
    # [Unhappy]
    rm({USB_DSO: "AGILENT TECHNOLOGIES,DSO9999X,X,1"})
    d = HWDriver()
    num, _, drivers = d.discover_channels()
    assert (num, drivers, d.instrs) == (-1, [], [])


@pytest.mark.parametrize("args, match", [({"interface": "ethernet"}, "ip"),
                                         ({"interface": "ethernet", "ip": ""}, "ip"),
                                         ({"interface": "ethernet", "ip": []}, "ip"),
                                         ({"interface": "ethernet", "ip": [1]}, "ip"),
                                         ({"interface": "gpib"}, "interface"),
                                         ({"only_one": True}, "only_one is renamed shared")])
def test_bad_args_raise_value_error(rm, args, match):
    # [Unhappy]
    rm({})
    with pytest.raises(ValueError, match=match):
        HWDriver().discover_channels(args)


def test_close_closes_every_scope(rm):
    rm({usb("A"): idn("A"), usb("B"): idn("B")})
    d = HWDriver()
    _, _, drivers = d.discover_channels()
    instrs = [x["hwdrv"] for x in drivers]
    d.close()
    assert all(i.closed for i in instrs)


class FakeUdevDev:
    def __init__(self, sys_name, attrs):
        self.sys_name = sys_name
        self.attributes = attrs


def test_usb_port_paths_from_udev(monkeypatch):
    devs = [FakeUdevDev("1-2.3", {"idVendor": b"0957", "serial": b"A"}),
            FakeUdevDev("1-4", {"idVendor": b"046d", "serial": b"X"}),  # not Agilent
            FakeUdevDev("1-5", {"idVendor": b"0957"}),  # no serial
            FakeUdevDev("usb2", {"idVendor": b"0957", "serial": b"B"})]

    class FakeContext:
        def list_devices(self, **kw):
            return devs
    monkeypatch.setattr(hwdrv_module.pyudev, "Context", FakeContext)
    assert HWDriver()._usb_port_paths() == {"A": (1, 2, 3), "B": (2,)}
