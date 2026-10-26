"""Tests for public/prism/drivers/prism_play hwdrv (scripts#64).

Run from the scripts repo root: python -m pytest tests
PrismPlay is replaced with a fake, no named pipes are made.
"""
import pytest

from public.prism.drivers.prism_play import hwdrv_prism_play as hwdrv_module
from public.prism.drivers.prism_play.hwdrv_prism_play import HWDriver


class FakePrismPlay:
    DRIVER_TYPE = "PrismPlay"

    def __init__(self, channel, work_dir, loggerIn=None):
        self.channel = channel
        self.work_dir = work_dir

    def version(self):
        return "0.1.0"

    def unique_id(self):
        return "{:04}".format(self.channel)

    def jig_closed_detect(self):
        return False

    def show_pass_fail(self, p=False, f=False, o=False):
        pass

    def show_msg(self, msg):
        pass

    def close(self):
        pass


@pytest.fixture(autouse=True)
def fake_play(monkeypatch):
    monkeypatch.setattr(hwdrv_module, "PrismPlay", FakePrismPlay)
    monkeypatch.setattr(hwdrv_module, "pub_notice", lambda msg, **kw: None)


@pytest.mark.parametrize("args", [None, {}, {"channels": 2}])
def test_missing_work_dir_raises_value_error(args):
    with pytest.raises(ValueError, match="work_dir"):
        HWDriver().discover_channels(args)


def test_channels_default_and_given():
    num, dtype, drivers = HWDriver().discover_channels({"work_dir": "actions-runner"})
    assert (num, dtype, len(drivers)) == (hwdrv_module.NUM_CHANNELS_DEFAULT, "PrismPlay", 1)

    num, _, drivers = HWDriver().discover_channels({"work_dir": "actions-runner", "channels": 3})
    assert num == 3
    assert [d["id"] for d in drivers] == [0, 1, 2]
    assert drivers[0]["hwdrv"].work_dir == "actions-runner"
