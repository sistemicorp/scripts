"""Tests for public/prism/ResultBaseKeysV1.py add_key() and measurement() limits.

Run from the scripts repo root: python -m pytest tests
"""
from public.prism.api import ResultAPI
from public.prism.ResultBaseKeysV1 import ResultBaseKeysV1

KEY_NAME = "sn"
MEAS_VALUE_MAX_LEN = 128  # Lente measurement.value column


def make_record():
    r = ResultBaseKeysV1(0, script_filename="test.scr")
    r._item = {"name": "tst00xx.TST000", "measurements": []}
    return r


def test_add_key_at_limit():
    r = make_record()
    value = "x" * (ResultBaseKeysV1.KEY_MAX_LEN - len(KEY_NAME) - 1)
    assert r.add_key(KEY_NAME, value, slot=0)
    assert len(r.get_keys()["key0"]) == ResultBaseKeysV1.KEY_MAX_LEN


def test_add_key_too_long():
    # [Unhappy] scripts#62: a key longer than the Lente column fails on the station
    r = make_record()
    value = "x" * (ResultBaseKeysV1.KEY_MAX_LEN - len(KEY_NAME))
    assert not r.add_key(KEY_NAME, value, slot=0)
    assert not r.add_key(KEY_NAME, value)
    assert r.get_keys() == {}


def test_add_key_next_slot():
    r = make_record()
    assert r.add_key("a", 1)
    assert r.add_key("b", 2)
    assert r.get_keys() == {"key0": "a:1", "key1": "b:2"}


def test_add_key_slot_out_of_range():
    # [Edge] negative and past-the-end slots are refused
    r = make_record()
    assert not r.add_key(KEY_NAME, "1", slot=-1)
    assert not r.add_key(KEY_NAME, "1", slot=ResultBaseKeysV1.MAX_KEYS)
    assert r.get_keys() == {}


def test_add_key_slots_full():
    # [Unhappy]
    r = make_record()
    for i in range(ResultBaseKeysV1.MAX_KEYS):
        assert r.add_key(f"k{i}", i)
    assert not r.add_key("extra", 1)


def test_measurement_string_too_long():
    # [Unhappy] scripts#62: string values are already checked against the column size
    r = make_record()
    success, result, _ = r.measurement("ver", "v" * (MEAS_VALUE_MAX_LEN + 1),
                                       ResultAPI.UNIT_STRING)
    assert not success
    assert result == ResultAPI.RECORD_RESULT_INTERNAL_ERROR
    success, result, _ = r.measurement("ver", "v" * MEAS_VALUE_MAX_LEN, ResultAPI.UNIT_STRING)
    assert success and result == ResultAPI.RECORD_RESULT_PASS
