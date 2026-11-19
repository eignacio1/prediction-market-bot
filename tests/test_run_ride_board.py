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


def test_ride_board_install_wanted_line_is_registry_live():
    import ride_board_install as inst
    import runtime_registry as rr
    lines = inst.wanted_lines(inst.CRON_CONF.read_text(), rr.load())
    assert len(lines) == 1 and "scripts/run_ride_board.py" in lines[0][1]
    assert "flock -n /tmp/ride_board.lock" in lines[0][1] and "RIDE_BOARD_ORDERS" not in lines[0][1]
    cur = "0 * * * * x\n"
    merged = inst.merged_crontab(cur, lines)
    assert inst.without_block(merged)[0] == cur


# ---- W119.3 Part A: the log is compact and a repeated NO_BET row is not re-logged ----
def _rows(d):
    p = d / "decisions.jsonl"
    return [json.loads(l) for l in p.read_text().splitlines()] if p.exists() else []


def _cycle(tmp_path, mkts, now):
    from calib import tier
    return rr.run(mkts, now, Evidence(ride=ride.load()), tier, tmp_path, archive_dir=tmp_path / "none", place=False)


def test_logged_row_has_only_the_kept_fields(tmp_path):
    _cycle(tmp_path, {"KXNBAGAME": [mk("A", "0.40", "0.44")]}, 1794000000.0)
    (r,) = _rows(tmp_path)
    assert set(r) == set(rr.LOG_FIELDS)
    for dropped in ("book", "cell", "agreed", "mid", "half_spread", "sport", "event_ticker"):
        assert dropped not in r


def test_repeated_no_bet_logged_once_then_heartbeat(tmp_path):
    m = {"KXNBAGAME": [mk("B", None, None)]}          # NO_BET, no price
    t0 = 1794000000.0
    for i in range(5):                                # five 5-min cycles, nothing changes
        _cycle(tmp_path, m, t0 + 300 * i)
    assert len(_rows(tmp_path)) == 1
    _cycle(tmp_path, m, t0 + rr.HEARTBEAT_S + 1)      # past the heartbeat: one more row
    assert len(_rows(tmp_path)) == 2


def test_changed_no_bet_reason_is_logged(tmp_path):
    t0 = 1794000000.0
    _cycle(tmp_path, {"KXNBAGAME": [mk("A", None, None)]}, t0)
    _cycle(tmp_path, {"KXNBAGAME": [mk("A", "0.01", "0.99")]}, t0 + 300)
    rows = _rows(tmp_path)
    assert len(rows) == 2 and rows[0]["why"] != rows[1]["why"]


def test_order_routing_rows_are_never_skipped():
    row = {"route": "RIDE", "ticker": "T", "side": "yes", "why": ["x"], "cell_status": "HELD_OUT", "tier": "T2"}
    state = {"T": [rr._state_key(row), 1000.0]}
    assert rr.should_log(row, state, 1010.0) is True
    nb = {**row, "route": "NO_BET", "side": None}
    state = {"T": [rr._state_key(nb), 1000.0]}
    assert rr.should_log(nb, state, 1010.0) is False


def test_corrupt_state_file_is_ignored(tmp_path):
    (tmp_path / rr.STATE_FILE).write_text("{not json")
    _cycle(tmp_path, {"KXNBAGAME": [mk("B", None, None)]}, 1794000000.0)
    assert len(_rows(tmp_path)) == 1
