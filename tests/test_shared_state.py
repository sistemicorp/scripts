"""Tests for core/shared_state.py (the prism_dev copy).

Run from the scripts repo root: python -m pytest tests
"""
from core.shared_state import SharedState

CHAN_TYPE = "FAKE"
SHARED_TYPE = "BLE_LISTENER"


def make_state():
    ss = SharedState()
    ss.add_drivers(CHAN_TYPE, [{"id": 0}, {"id": 1}])
    ss.add_drivers(SHARED_TYPE, [{"id": 0}], shared=True)
    return ss


def test_get_drivers_channel_includes_shared():
    # scripts#61: shared drivers are found by type from any channel, like Prism
    ss = make_state()
    drivers = ss.get_drivers(1, type=SHARED_TYPE)
    assert len(drivers) == 1 and drivers[0]["channel"] is None


def test_get_drivers_channel_any_type():
    ss = make_state()
    drivers = ss.get_drivers(0)
    assert sorted(d["type"] for d in drivers) == sorted([CHAN_TYPE, SHARED_TYPE])
    assert all(d["channel"] in [0, None] for d in drivers)


def test_get_drivers_none_is_shared_only():
    # [Edge] channel None returns only the shared drivers
    ss = make_state()
    drivers = ss.get_drivers(None)
    assert [d["type"] for d in drivers] == [SHARED_TYPE]


def test_get_drivers_unknown_type():
    # [Unhappy] no driver of that type installed
    assert make_state().get_drivers(0, type="NOPE") == []
