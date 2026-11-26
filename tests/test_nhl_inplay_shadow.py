"""W129.7 Part C: the in-play shadow runner with fake feeds (no network): off by default, rows, staleness skip, recency."""
import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from prediction_market_bot.c1_signal_ingestion.nhl_ingest import Throttle

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("nhl_inplay_shadow", ROOT / "scripts" / "nhl_inplay_shadow.py")
sh = importlib.util.module_from_spec(spec)
sys.modules["nhl_inplay_shadow"] = sh
spec.loader.exec_module(sh)

FIX = ROOT / "tests" / "fixtures" / "nhl_pbp_live_2026020386.json"
NOW = datetime(2026, 11, 25, 23, 30, tzinfo=timezone.utc)
TICK = "KXNHLGAME-26NOV25WPGBOS-BOS"


class FakeModel:
    def raw_ladder(self, _row):
        return None, 3.0, 3.0


class FakeFcst:
    model = FakeModel()

    def _game(self, info):
        return {"game_id": 2026020386, "start_time_utc": "2026-11-25T23:00:00Z"}

    def feature_row(self, game, start):
        return {}


def nhl_opener(url):
    if "/score/now" in url:
        return 200, json.dumps({"games": [{"id": 2026020386, "gameState": "LIVE"}]}).encode()
    return 200, FIX.read_bytes()


def kalshi_opener(url):
    m = {"ticker": TICK, "event_ticker": "KXNHLGAME-26NOV25WPGBOS", "yes_bid_dollars": "0.30", "yes_ask_dollars": "0.34"}
    return 200, json.dumps({"markets": [m] if "KXNHLGAME" in url else [], "cursor": ""}).encode()


def _run(root, now=NOW):
    t = lambda: Throttle(interval_s=0.0, base_s=0.0)
    return sh.run_pass(root, now, FakeFcst(), t(), t(), nhl_opener, kalshi_opener, run_id="T")


def test_off_by_default():
    assert sh.enabled({}) is False and sh.enabled({"PM_NHL_INPLAY": "1"}) is True


def test_pass_writes_a_priced_row(tmp_path):
    s = _run(tmp_path)
    assert s["rows"] == 1 and s["recency"] == "OK"
    row = json.loads((tmp_path / "NHL_MONEYLINE_T4NHL-ARITH.jsonl").read_text().splitlines()[0])
    assert row["band"] == "T4NHL-ARITH" and row["strength"] == "H_PP" and (row["score_h"], row["score_a"]) == (0, 1)
    assert 0.0 < row["p_yes"] < 1.0 and row["mid"] == 0.32 and "feed_latency_ms" in row and "state_to_quote_s" in row


def test_no_order_fields(tmp_path):
    _run(tmp_path)
    row = json.loads((tmp_path / "NHL_MONEYLINE_T4NHL-ARITH.jsonl").read_text().splitlines()[0])
    assert not any(k in row for k in ("stake", "kelly", "order_id", "contracts"))


def test_frozen_clock_is_skipped_not_priced(tmp_path):
    _run(tmp_path)
    # same running clock fetched 100s later: the staleness gate must refuse it
    st = json.loads((tmp_path / sh.STATE_FILE).read_text())
    st["2026020386"]["clock_running"] = True
    (tmp_path / sh.STATE_FILE).write_text(json.dumps(st))
    d = json.loads(FIX.read_text())
    d["clock"]["running"] = True
    later = NOW + timedelta(seconds=100)
    fix_opener = lambda url: nhl_opener(url) if "/score/now" in url else (200, json.dumps(d).encode())
    t = lambda: Throttle(interval_s=0.0, base_s=0.0)
    s = sh.run_pass(tmp_path, later, FakeFcst(), t(), t(), fix_opener, kalshi_opener, run_id="T2")
    assert s["rows"] == 0 and s["skips"].get("clock_frozen") == 1


def test_health_fails_when_live_game_but_no_row(tmp_path):
    (tmp_path / sh.PASS_LOG).write_text(json.dumps({"ts_utc": NOW.isoformat(), "recency": "FAIL", "recency_detail": "x",
                                                    "live_games": 1, "rows": 0}) + "\n")
    assert sh.health(tmp_path, NOW)[0] == "FAIL"
    assert sh.health(tmp_path / "none", NOW)[0] == "IDLE"
