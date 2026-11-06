"""W105.5 / B-054: the runner logs EVERY decision (NO_BET included) on a fixture night."""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "12_EXPLORATORY" / "longshot_bias"))

import run_ride_board as rr  # noqa: E402
from prediction_market_bot.decision_trees import ride  # noqa: E402
from prediction_market_bot.decision_trees.router import Evidence  # noqa: E402


def mk(ticker, bid, ask, event="KXNBAGAME-26NOV07LALBOS"):
    return {"ticker": ticker, "event_ticker": event, "yes_bid_dollars": bid, "yes_ask_dollars": ask}


def test_every_decision_logged_incl_no_bet(tmp_path):
    from calib import tier
    ev = Evidence(ride=ride.load())
    mkts = {"KXNBAGAME": [mk("A", "0.40", "0.44"), mk("B", None, None), mk("C", "0.01", "0.99")]}
    now = 1794000000.0
    counts = rr.run(mkts, now, ev, tier, tmp_path, archive_dir=tmp_path / "none", place=False)
    rows = [json.loads(l) for l in (tmp_path / "decisions.jsonl").read_text().splitlines()]
    assert len(rows) == 3 and sum(counts.values()) == 3
    assert {"route", "why", "cell_status", "yes_bid", "yes_ask", "tier", "ticker"} <= set(rows[0])
    assert any(r["route"] == "NO_BET" for r in rows)


def test_move_1h_uses_only_past_snapshot():
    hist = [(1000.0, 0.50), (4600.0, 0.55)]
    assert rr.move_1h(hist, 4600.0, 0.60) == pytest.approx(0.10)
    assert rr.move_1h([(4500.0, 0.5)], 4600.0, 0.6) is None
    assert rr.move_1h([], 4600.0, 0.6) is None


def test_sport_of():
    assert rr.sport_of("KXNHLGAME") == "nhl" and rr.sport_of("KXFOO") == "other"
