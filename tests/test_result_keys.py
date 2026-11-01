"""Tests for public/prism/ResultBaseKeysV1.py add_key() and measurement() limits and fail=.

Run from the scripts repo root: python -m pytest tests
"""
from public.prism.api import ResultAPI
from public.prism.ResultBaseKeysV1 import ResultBaseKeysV1

KEY_NAME = "sn"
MEAS_VALUE_MAX_LEN = 128  # Lente measurement.value column


def make_record():
    r = ResultBaseKeysV1(0, script_filename="test.scr")
    r._item = {"name": "tst00xx.TST000", "measurements": [], "fail_msg": {}}
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


FAIL_ENTRY = {"fid": "TST000-0", "msg": "3V_OUT low: check U7 R49"}


def test_measurement_fail_entry_recorded_on_fail():
    # scripts#66: fail= attaches the script fail entry when the measurement fails
    r = make_record()
    success, result, _ = r.measurement("v3", 2.1, ResultAPI.UNIT_VOLTS, 3.0, 3.6, fail=FAIL_ENTRY)
    assert success
    assert result == ResultAPI.RECORD_RESULT_FAIL
    assert r.record_item_get()["fail_msg"] == FAIL_ENTRY


def test_measurement_fail_entry_not_recorded_on_pass():
    r = make_record()
    success, result, _ = r.measurement("v3", 3.3, ResultAPI.UNIT_VOLTS, 3.0, 3.6, fail=FAIL_ENTRY)
    assert success
    assert result == ResultAPI.RECORD_RESULT_PASS
    assert r.record_item_get()["fail_msg"] == {}


def test_measurement_fail_entry_with_bool_and_force_fail():
    # [Edge] boolean check and force_fail use the same rule
    r = make_record()
    _, result, _ = r.measurement("dsr_off", False, ResultAPI.UNIT_BOOLEAN, fail=FAIL_ENTRY)
    assert result == ResultAPI.RECORD_RESULT_FAIL
    assert r.record_item_get()["fail_msg"] == FAIL_ENTRY

    r = make_record()
    _, result, _ = r.measurement("ver", "1.0", ResultAPI.UNIT_STRING, force_fail=True,
                                 fail=FAIL_ENTRY)
    assert result == ResultAPI.RECORD_RESULT_FAIL
    assert r.record_item_get()["fail_msg"] == FAIL_ENTRY


def test_measurement_fail_entry_not_a_dict():
    # [Unhappy] passing the index instead of ctx.item.fail[i] is an authoring error
    r = make_record()
    success, result, _ = r.measurement("v3", 2.1, ResultAPI.UNIT_VOLTS, 3.0, 3.6, fail=0)
    assert not success
    assert result == ResultAPI.RECORD_RESULT_INTERNAL_ERROR
    assert r.record_item_get()["measurements"] == []


def test_measurement_one_sided_max():
    # scripts#67: a float with max only checks max, min is stored as None
    r = make_record()
    success, result, bullet = r.measurement("v_off", 12.0, ResultAPI.UNIT_MILLIVOLTS, max=100)
    assert success and result == ResultAPI.RECORD_RESULT_PASS
    m = r.record_item_get()["measurements"][-1]
    assert m["min"] is None and m["max"] == "100" and m["value"] == "12"
    assert bullet == "v_off: 12 <= 100 milliVolts :: PASS"

    success, result, _ = r.measurement("v_off2", 150.0, ResultAPI.UNIT_MILLIVOLTS, max=100)
    assert success and result == ResultAPI.RECORD_RESULT_FAIL


def test_measurement_one_sided_min():
    r = make_record()
    success, result, bullet = r.measurement("ratio", 0.98, ResultAPI.UNIT_FLOAT, min=0.97)
    assert success and result == ResultAPI.RECORD_RESULT_PASS
    m = r.record_item_get()["measurements"][-1]
    assert m["min"] == "0.97" and m["max"] is None
    assert bullet == "ratio: 0.97 <= 0.98 Float :: PASS"

    _, result, _ = r.measurement("ratio2", 0.9, ResultAPI.UNIT_FLOAT, min=0.97)
    assert result == ResultAPI.RECORD_RESULT_FAIL


def test_measurement_one_sided_int():
    # [Edge] an error count with max only; the limit itself passes
    r = make_record()
    _, result, _ = r.measurement("errors", 0, ResultAPI.UNIT_INT, max=0)
    assert result == ResultAPI.RECORD_RESULT_PASS
    _, result, _ = r.measurement("errors2", 1, ResultAPI.UNIT_INT, max=0, fail=FAIL_ENTRY)
    assert result == ResultAPI.RECORD_RESULT_FAIL
    assert r.record_item_get()["fail_msg"] == FAIL_ENTRY


def test_measurement_one_sided_force_fail_and_types():
    r = make_record()
    _, result, _ = r.measurement("i", 1.0, ResultAPI.UNIT_MILLIAMPS, max=5, force_fail=True)
    assert result == ResultAPI.RECORD_RESULT_FAIL
    # [Unhappy] an int value with a float limit is still a type mismatch
    success, result, _ = r.measurement("n", 3, ResultAPI.UNIT_INT, max=5.0)
    assert not success and result == ResultAPI.RECORD_RESULT_INTERNAL_ERROR


def test_measurement_two_sided_unchanged():
    r = make_record()
    _, result, bullet = r.measurement("v3", 3.3, ResultAPI.UNIT_VOLTS, 3.0, 3.6)
    assert result == ResultAPI.RECORD_RESULT_PASS
    assert bullet == "v3: 3 <= 3.3 <= 3.6 Volts :: PASS"
