"""W89.1 / GG-1082 / GG-441: the shipped default is ENFORCE (no env override)."""
import pytest

from prediction_market_bot.c4_risk_engine import exposure_gate as eg


@pytest.fixture(autouse=True)
def _dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("PMBOT_KILL_SWITCH_DIR", str(tmp_path))
    monkeypatch.delenv(eg.MODE_ENV, raising=False)


def _book(pnl, initial=1000.0):
    return {"initial_bankroll_usd": initial, "total_realized_pnl": pnl, "open_positions": []}


def test_shipped_default_is_enforce():
    assert eg.GATE_MODE == "enforce" and eg.gate_mode() == "enforce"


def test_order_on_tripped_book_refused(tmp_path):
    eg.record_book("MLB_T1", _book(-250.0), logs_dir=tmp_path)
    assert eg.gate_for_order("t1_mlb", tmp_path).startswith("exposure_gate_breach")


def test_missing_state_halts_and_healthy_book_passes(tmp_path):
    assert eg.gate_for_order("t1_mlb", tmp_path) is not None
    eg.record_book("MLB_T1", _book(-10.0), logs_dir=tmp_path)
    assert eg.gate_for_order("t1_mlb", tmp_path) is None
