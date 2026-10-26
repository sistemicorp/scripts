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
    """ :return: function to install a FakeRM with the given instruments """
    def install(instruments):
        fake = FakeRM(instruments)
        monkeypatch.setattr(hwdrv_module.pyvisa, "ResourceManager", lambda: fake)
        return fake
    monkeypatch.setattr(hwdrv_module, "pub_notice", lambda msg, **kw: None)
    return install


@pytest.mark.parametrize("args", [None, {}, {"interface": "usb"}])
def test_usb_default(rm, args):
    fake = rm({USB_DSO: IDN})
    num, dtype, drivers = HWDriver().discover_channels(args)
    assert (num, dtype) == (0, "AGILENT_DSO_USB_1")
    assert fake.opened == [USB_DSO]
    assert HWDriver.QUERY_STRING in fake.queries
    assert drivers[0]["hwdrv"].writes == ["*RST"]


def test_ethernet(rm):
    resource = "TCPIP0::192.168.1.100::INSTR"
    fake = rm({resource: IDN, USB_DSO: IDN})
    num, _, drivers = HWDriver().discover_channels({"interface": "ethernet", "ip": "192.168.1.100"})
    assert num == 0
    assert fake.opened == [resource]  # USB is not scanned
    assert fake.queries == []
    assert drivers[0]["hwdrv"].writes == ["*RST"]


def test_ethernet_unreachable_returns_error(rm):
    rm({})
    assert HWDriver().discover_channels({"interface": "ethernet", "ip": "10.0.0.1"})[0] == -1


def test_not_white_listed_is_closed(rm):
    rm({USB_DSO: "AGILENT TECHNOLOGIES,DSO9999X,X,1"})
    d = HWDriver()
    num, _, drivers = d.discover_channels()
    assert (num, drivers, d.instr) == (-1, [], None)


@pytest.mark.parametrize("args, match", [({"interface": "ethernet"}, "ip"),
                                         ({"interface": "gpib"}, "interface")])
def test_bad_args_raise_value_error(rm, args, match):
    rm({})
    with pytest.raises(ValueError, match=match):
        HWDriver().discover_channels(args)
