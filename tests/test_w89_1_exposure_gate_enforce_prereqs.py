"""W89.1 / GG-1240 / GG-1241: prerequisites for enforcing the exposure gate."""
import json
from unittest import mock

import pytest

from prediction_market_bot.c4_risk_engine import exposure_gate as eg
from prediction_market_bot.c5_execution.paper_trader import PaperTrader


@pytest.fixture(autouse=True)
def _dirs(tmp_path, monkeypatch):
    monkeypatch.setenv("PMBOT_KILL_SWITCH_DIR", str(tmp_path))
    monkeypatch.setenv(eg.MODE_ENV, "enforce")
    return tmp_path


def _book(positions=(), initial=1000.0):
    return {"initial_bankroll_usd": initial, "total_realized_pnl": 0.0,
            "open_positions": [dict(p) for p in positions]}


def test_shadow_settled_stake_never_trips_system_or_real_books(tmp_path):
    eg.record_book("MLB_T1", _book(), logs_dir=tmp_path)
    shadow = _book([{"kalshi_ticker": f"S{i}", "size_usd": 50.0, "status": "OPEN"} for i in range(40)])
    out = eg.record_book("SHADOW", shadow, {f"S{i}" for i in range(40)}, logs_dir=tmp_path)
    assert out["books"]["SHADOW"]["worst_case_drawdown_pct"] >= 1.0  # still reported
    assert out["breaches"] == []
    assert out["system"]["initial_bankroll_usd"] == 1000.0  # shadow notional not in the system sum
    assert eg.gate_for_order("t1_mlb", tmp_path) is None


def test_advisory_shadow_still_needs_a_writer(tmp_path):
    eg.record_book("MLB_T1", _book(), logs_dir=tmp_path)
    assert eg.gate_for_order("shadow", tmp_path) == "exposure_book_no_writer:SHADOW"


def test_missing_state_file_halts(tmp_path):
    assert eg.gate_for_order("t4_mlb", tmp_path) is not None


def test_papertrader_construction_seeds_t4_book(tmp_path):
    PaperTrader(tmp_path / "paper_portfolio_mlb_t4.json", mock.MagicMock(), kill_band="t4_mlb")
    st = json.loads((tmp_path / eg.STATE_FILE).read_text()) if hasattr(eg, "STATE_FILE") else \
        json.loads(eg.state_path(tmp_path).read_text())
    assert "MLB_T4" in st["books"]
    assert eg.gate_for_order("t4_mlb", tmp_path) is None
