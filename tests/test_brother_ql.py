"""Tests for public/prism/drivers/brother_ql hwdrv (shared vs per channel printers),
the brother_v0 example, and prism_dev shared driver checks.

Run from the scripts repo root: python -m pytest tests
No printer is used, the pyudev scan is replaced with a fake list.
"""
import sys
import types

import pytest

import prism_dev
from core.shared_state import SharedState
from public.prism.api import ResultAPI
from public.prism.drivers.brother_ql import hwdrv_brother_ql as hwdrv_module
from public.prism.drivers.brother_ql.hwdrv_brother_ql import BrotherQL, DRIVER_TYPE
from public.prism.scripts.example.brother_v0.brthr00xx import brthr00xx

LP0 = "/dev/usb/lp0"
LP1 = "/dev/usb/lp1"


def printers(*devnodes):
    """ the _find_brother_printers() list, in USB hub port order """
    return [((1, i), d, "Brother", "QL-700", "1-{}".format(i)) for i, d in enumerate(devnodes)]


@pytest.fixture
def notices(monkeypatch, tmp_path):
    """ fake USB scan, labels go to tmp_path, :return: list of pub_notice texts """
    sent = []
    monkeypatch.setattr(hwdrv_module.pyudev, "Context", lambda: None)
    monkeypatch.setattr(BrotherQL, "WORKING_PATH", str(tmp_path))
    monkeypatch.setattr(hwdrv_module, "pub_notice", lambda msg, **kw: sent.append(msg))
    return sent


def discover(monkeypatch, devnodes, args=None):
    monkeypatch.setattr(hwdrv_module.HWDriver, "_find_brother_printers",
                        lambda self, context: printers(*devnodes))
    d = hwdrv_module.HWDriver()
    num, drv_type, drivers = d.discover_channels(args)
    assert drv_type == DRIVER_TYPE
    if num >= 0:
        assert d.num_channels() == num
    return num, drivers


def test_one_printer_per_channel(monkeypatch, notices):
    """ without only_one, each printer is a channel, in USB port order (was always 0) """
    num, drivers = discover(monkeypatch, [LP0, LP1])
    assert num == 2
    assert [d["id"] for d in drivers] == [0, 1]
    assert [d["hwdrv"].path for d in drivers] == [LP0, LP1]


def test_only_one_is_shared(monkeypatch, notices):
    num, drivers = discover(monkeypatch, [LP0], {"only_one": True})
    assert num == 0
    assert len(drivers) == 1


def test_only_one_found_two_is_error(monkeypatch, notices):
    """ [Unhappy] only_one but two printers, can't know which one to use """
    num, drivers = discover(monkeypatch, [LP0, LP1], {"only_one": True})
    assert num == -1
    assert drivers == []
    assert any("found 2" in n for n in notices)


def test_none_found_is_error(monkeypatch, notices):
    """ [Unhappy] no printer attached """
    num, drivers = discover(monkeypatch, [], {"only_one": True})
    assert num == -1
    assert drivers == []


def test_test_label_notice_counts_printers(monkeypatch, notices):
    """ [Edge] the test label loop overwrote the count, the notice said 1 for 2 printers """
    labels = []
    monkeypatch.setattr(BrotherQL, "print_ruid_barcode",
                        lambda self, ruid, chan=0: labels.append(ruid) or True)
    num, _ = discover(monkeypatch, [LP0, LP1], {"test_label": True})
    assert num == 2
    assert labels == ["id0-" + LP0, "id1-" + LP1]
    assert "HWDriver:hwdrv_brother_ql.py: found 2" in notices


def test_test_label_print_fails_is_error(monkeypatch, notices):
    """ [Unhappy] validation fails if the test label does not print """
    monkeypatch.setattr(BrotherQL, "print_ruid_barcode", lambda self, ruid, chan=0: False)
    num, drivers = discover(monkeypatch, [LP0], {"test_label": True})
    assert num == -1
    assert drivers == []


# ---- brother_v0 example ------------------------------------------------------

def run_setup(monkeypatch, notices, devnodes, args, chan):
    """ discover printers into a SharedState, run BRTHR0xxSETUP on chan,
    :return: record, printer selected by the test item """
    num, drivers = discover(monkeypatch, devnodes, args)
    ss = SharedState()
    ss.add_drivers(DRIVER_TYPE, drivers, shared=(num == 0))
    script = {"info": {}, "config": {}, "tests": []}
    con = prism_dev.ChanCon(chan, script, ss, "brother_v0.scr")
    con._item, con._options = {"id": "BRTHR0xxSETUP", "enable": True}, {}
    t = brthr00xx(con, chan, ss)
    t.BRTHR0xxSETUP()
    return con.record, t.printer


def test_example_uses_channel_printer(monkeypatch, notices):
    """ per channel printers, channel 1 gets the 2nd printer (was not found) """
    record, printer = run_setup(monkeypatch, notices, [LP0, LP1], None, chan=1)
    assert record.record_test_get_result() == ResultAPI.RECORD_RESULT_PASS
    assert printer.path == LP1


def test_example_uses_shared_printer(monkeypatch, notices):
    record, printer = run_setup(monkeypatch, notices, [LP0], {"only_one": True}, chan=1)
    assert record.record_test_get_result() == ResultAPI.RECORD_RESULT_PASS
    assert printer.path == LP0


# ---- prism_dev shared driver check ---------------------------------------------

def test_prism_dev_shared_driver_without_objects_is_error(monkeypatch):
    """ [Unhappy] 0 channels (shared) with an empty list, Prism rejects it, so must prism_dev """
    class HWDriver:
        def discover_channels(self):
            return 0, "EMPTY", []

    module = types.ModuleType("fake_shared_empty")
    module.HWDriver = HWDriver
    monkeypatch.setitem(sys.modules, "fake_shared_empty", module)
    script = {"info": {}, "config": {"drivers": ["fake_shared_empty"]}, "tests": []}
    con = prism_dev.ChanCon(0, script, SharedState(), "shared_empty.scr")
    with pytest.raises(ValueError, match="no driver object"):
        con.run()
