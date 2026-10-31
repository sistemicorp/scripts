"""Tests for TestItem.expect(): a failed driver response ends the item
INTERNAL_ERROR, through prism_dev's ChanCon.call_item.
"""
import pytest

import prism_dev
from core.shared_state import SharedState
from core import test_item
from core.test_item import EquipmentError
from public.prism.api import ResultAPI

SCRIPT = {"info": {"product": "P0", "bom": "B0", "lot": "L0", "location": "here"},
          "config": {"fail_fast": True, "drivers": []},
          "tests": [{"module": "m", "options": {},
                     "items": [{"id": "A0", "enable": True}]}]}
FAILED = {"success": False, "method": "vbat_read", "result": {"error": "timeout"}}


class Item(test_item.TestItem):
    """A test item calling expect() on a given driver response"""

    def __init__(self, con, response):
        super().__init__(con, 0, SharedState())
        self.response = response
        self.after = False

    def A0(self):
        ctx = self.item_start()  # noqa: F841
        self.expect(self.response)
        self.after = True
        self.item_end()


@pytest.fixture
def con():
    c = prism_dev.ChanCon(0, SCRIPT, SharedState(), "test_expect")
    c._item, c._options = SCRIPT["tests"][0]["items"][0], {}
    c.bullets = []
    c.log_bullet = lambda text, ovrwrite_last_line=False: c.bullets.append(text)
    return c


def test_expect_passes_successful_response(con):
    response = {"success": True, "method": "vbat_read", "result": {"v": 3.0}}
    item = Item(con, response)
    assert item.expect(response) is response
    con.call_item(item.A0)
    assert item.after
    assert con.record.record_test_get_result() == ResultAPI.RECORD_RESULT_PASS


def test_expect_failed_response_ends_item(con):
    # [Unhappy] the rest of the item does not run, the item is INTERNAL_ERROR
    item = Item(con, FAILED)
    con.call_item(item.A0)
    assert not item.after
    assert con.record.record_test_get_result() == ResultAPI.RECORD_RESULT_INTERNAL_ERROR
    assert con.bullets == ["!vbat_read failed! timeout"]


def test_expect_not_caught_by_except_exception(con):
    # [Edge] a script's broad `except Exception` does not swallow it
    item = Item(con, FAILED)
    with pytest.raises(EquipmentError):
        try:
            item.expect(FAILED)
        except Exception:
            pytest.fail("EquipmentError caught by except Exception")


def test_expect_rejects_non_dict(con):
    # [Unhappy] a bool from e.g. init() is a script bug, not an equipment error
    item = Item(con, True)
    with pytest.raises(TypeError):
        item.expect(True)
