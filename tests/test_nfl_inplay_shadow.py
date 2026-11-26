"""W130.1: NFL in-play shadow runner (T4NFL-ARITH / T4NFL-FLOW). Fake I/O on the saved ARI @ KC game; nothing touches a network."""
import ast
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
import run_nfl_inplay_shadow as r  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nfl_live_feed as feed  # noqa: E402

FX = json.loads((ROOT / "tests" / "fixtures" / "nfl_game_401873067_plays.json").read_text())
EV = {"id": FX["event_id"], "status": "STATUS_IN_PROGRESS", "date": "2026-11-23T01:20:00Z", "home_id": FX["home_id"],
      "home": "KC", "away": "ARI"}
CUT = 100


def _t(s):
    return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)


def _mk(ticker, series, bid, ask, strike=None):
    d = {"ticker": ticker, "event_ticker": ticker.rpartition("-")[0], "yes_bid_dollars": str(bid), "yes_ask_dollars": str(ask)}
    if strike is not None:
        d["floor_strike"] = strike
    return d


class FakeIo(r.Io):
    def __init__(self, plays=None, markets=None, status="STATUS_IN_PROGRESS", lag=6, line=(-6.5, 47.5)):
        self.plays_ = FX["plays"][:CUT] if plays is None else plays
        sts = feed.states_from_plays(self.plays_, FX["event_id"], FX["home_id"], "KC", "ARI", "2026-11-23T00:00:00Z", replay=True)
        self.last_wc = _t(sts[-1].wallclock_utc)
        self.ft = (self.last_wc + timedelta(seconds=lag)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self._now = self.last_wc + timedelta(seconds=lag + 2)
        self.status, self.line, self.pc_calls = status, line, 0
        ev = r.event_ticker
        self.mk = markets if markets is not None else {
            "KXNFLGAME": [_mk("KXNFLGAME-26NOV22ARIKC-KC", "g", 0.6, 0.62), _mk("KXNFLGAME-26NOV22ARIKC-ARI", "g", 0.37, 0.39)],
            "KXNFLSPREAD": [_mk("KXNFLSPREAD-26NOV22ARIKC-KC7", "s", 0.4, 0.42, 6.5), _mk("KXNFLSPREAD-26NOV22ARIKC-ARI3", "s", 0.2, 0.22, 2.5)],
            "KXNFLTOTAL": [_mk("KXNFLTOTAL-26NOV22ARIKC-48", "t", 0.5, 0.53, 47.5)],
            "KXNFLTEAMTOTAL": [_mk("KXNFLTEAMTOTAL-26NOV22ARIKC-KC28", "tt", 0.3, 0.33, 27.5), _mk("KXNFLTEAMTOTAL-26NOV22ARIKC-ARI10", "tt", 0.5, 0.0, 9.5)],
        }

    def scoreboard(self):
        return [{**EV, "status": self.status}], None

    def plays(self, eid):
        return self.plays_, None, self.ft

    def pickcenter(self, eid):
        self.pc_calls += 1
        return self.line

    def markets(self, et):
        return self.mk.get(et.split("-")[0], [])

    def now(self):
        return self._now


@pytest.fixture(autouse=True)
def _identity_normalise(monkeypatch):
    monkeypatch.setattr(feed, "normalise", lambda p: p)  # the fixture plays are already normalised


def test_off_by_default(tmp_path, capsys):
    assert not r.enabled({}) and r.enabled({"PM_NFL_INPLAY": "1"}) and not r.enabled({"PM_NFL_INPLAY": "0"})
    assert r.main(["--root", str(tmp_path)]) == 0
    assert "is off" in capsys.readouterr().out and not list(tmp_path.iterdir())


def test_event_ticker_and_alias():
    ev = {"date": "2026-11-27T01:20:00Z", "home": "WSH", "away": "LAR"}
    assert r.event_ticker("KXNFLGAME", ev) == "KXNFLGAME-26NOV26LAWAS"   # 20:20 ET on the 26th, Kalshi codes


def test_pass_writes_rows_per_market_and_band(tmp_path):
    s = r.run_pass(tmp_path, FakeIo(), run_id="T1")
    assert s["live_games"] == 1 and s["rows"] == 2 * 6 and s["recency"] == "OK"
    files = {p.name for p in tmp_path.glob("*.jsonl") if p.name != r.PASS_LOG}
    assert files == {f"{mt}_{b}.jsonl" for mt in ("nfl_moneyline", "nfl_spread", "nfl_game_total", "nfl_team_total")
                     for b in ("T4NFL-ARITH", "T4NFL-FLOW")}
    row = json.loads((tmp_path / "nfl_moneyline_T4NFL-FLOW.jsonl").read_text().splitlines()[0])
    arith = json.loads((tmp_path / "nfl_moneyline_T4NFL-ARITH.jsonl").read_text().splitlines()[0])
    assert row["mode"] == "flow_identity" and arith["mode"] == "arith" and row["p_yes"] == arith["p_yes"]
    assert row["feed_lag_s"] == 6.0 and row["state_to_quote_s"] >= 0 and row["half_spread"] == pytest.approx(0.01)
    assert row["pregame_margin"] == 6.5 and row["pregame_total"] == 47.5 and row["line_pre_kickoff"] is False
    tt = [json.loads(l) for l in (tmp_path / "nfl_team_total_T4NFL-ARITH.jsonl").read_text().splitlines()]
    assert {x["mode"] for x in tt} == {"team_total_ext_unvalidated"} and len(tt) == 1  # the one-sided book is skipped
    assert s["skips"].get("one_sided_book") == 1


def test_no_order_or_sizing_fields(tmp_path):
    r.run_pass(tmp_path, FakeIo())
    for p in tmp_path.glob("*_T4NFL-*.jsonl"):
        for l in p.read_text().splitlines():
            assert not {k for k in json.loads(l) if "kelly" in k or "stake" in k or "order" in k or "contracts" in k}


def test_pricing_known_answers():
    io = FakeIo()
    sts = feed.states_from_plays(io.plays_, FX["event_id"], FX["home_id"], "KC", "ARI", io.ft)
    st = sts[-1]
    ev = EV
    pk, _ = r.price_market("KXNFLGAME", {"team": "KC", "strike": None}, st, ev, 6.5, 47.5)
    pa, _ = r.price_market("KXNFLGAME", {"team": "ARI", "strike": None}, st, ev, 6.5, 47.5)
    assert pk + pa == pytest.approx(1.0)
    over, _ = r.price_market("KXNFLTOTAL", {"team": "", "strike": 47.5}, st, ev, 6.5, 47.5)
    assert 0.0 < over < 1.0
    # spread: KC wins by over k and ARI wins by over -k are complements-ish ordering: bigger strike -> lower probability
    lo, _ = r.price_market("KXNFLSPREAD", {"team": "KC", "strike": 3.5}, st, ev, 6.5, 47.5)
    hi, _ = r.price_market("KXNFLSPREAD", {"team": "KC", "strike": 13.5}, st, ev, 6.5, 47.5)
    assert lo > hi
    assert r.price_market("KXNFLGAME", {"team": "XYZ", "strike": None}, st, ev, 6.5, 47.5) is None


def test_stale_feed_is_skipped_and_counted(tmp_path):
    io = FakeIo()
    io._now = io.last_wc + timedelta(seconds=400)
    s = r.run_pass(tmp_path, io)
    assert s["rows"] == 0 and s["skips"] and set(s["skips"]) <= {"fetch_old", "newest_play_old"}


def test_overtime_abstains(tmp_path):
    io = FakeIo(plays=FX["plays"])
    sts = feed.states_from_plays(FX["plays"], FX["event_id"], FX["home_id"], "KC", "ARI", io.ft)
    assert sts[-1].secs_left_reg <= 0 or sts[-1].period > 4
    s = r.run_pass(tmp_path, io)
    assert s["rows"] == 0 and ("regulation_over" in s["skips"] or "overtime_abstain" in s["skips"])


def test_pregame_line_cached_before_kickoff_and_not_refetched(tmp_path):
    io = FakeIo(status="STATUS_SCHEDULED")
    io._now = datetime(2026, 11, 23, 0, 30, tzinfo=timezone.utc)   # 50 min before the 01:20Z kickoff
    r.run_pass(tmp_path, io)
    st = json.loads((tmp_path / r.STATE_FILE).read_text())
    assert st["_lines"][EV["id"]]["pre_kickoff"] is True and io.pc_calls == 1
    io2 = FakeIo()
    r.run_pass(tmp_path, io2)
    assert io2.pc_calls == 0
    row = json.loads((tmp_path / "nfl_moneyline_T4NFL-ARITH.jsonl").read_text().splitlines()[0])
    assert row["line_pre_kickoff"] is True


def test_no_open_market_and_no_line_are_counted(tmp_path):
    s = r.run_pass(tmp_path, FakeIo(markets={}))
    assert s["skips"].get("no_open_market_for_game") == 1 and s["rows"] == 0
    s2 = r.run_pass(tmp_path / "b", FakeIo(line=(None, None)))
    assert s2["skips"].get("no_pregame_line") == 1


def test_health_idle_ok_fail(tmp_path):
    now = datetime(2026, 11, 26, 20, 0, tzinfo=timezone.utc)
    assert r.health(tmp_path, now)[0] == "IDLE"
    (tmp_path / r.PASS_LOG).write_text(json.dumps({"ts_utc": now.isoformat(), "live_games": 1, "rows": 14, "recency": "OK"}) + "\n")
    assert r.health(tmp_path, now)[0] == "OK"
    with (tmp_path / r.PASS_LOG).open("a") as f:
        f.write(json.dumps({"ts_utc": now.isoformat(), "live_games": 1, "rows": 0, "recency": "FAIL", "recency_detail": "x"}) + "\n")
    assert r.health(tmp_path, now)[0] == "FAIL"


def test_write_recency():
    now = datetime(2026, 11, 26, 20, 0, tzinfo=timezone.utc)
    assert r.write_recency([], None, now)[0] == "IDLE"
    assert r.write_recency(["1"], None, now)[0] == "FAIL"
    assert r.write_recency(["1"], now - timedelta(seconds=700), now)[0] == "FAIL"
    assert r.write_recency(["1"], now - timedelta(seconds=60), now)[0] == "OK"


def test_runner_imports_no_order_code():
    forbidden_mod = ("kalshi_client", "paper_trader", "c4_risk_engine", "execution_bands", "venue_adapter",
                     "market_type_registry", "c5_execution")
    forbidden_names = {"submit_order", "open_position", "exit_position", "kelly", "place_order", "PaperTrader"}
    tree = ast.parse((ROOT / "scripts" / "run_nfl_inplay_shadow.py").read_text())
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            mods = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom):
            mods = [n.module or ""] + [f"{n.module}.{a.name}" for a in n.names]
        else:
            if isinstance(n, ast.Name):
                assert n.id not in forbidden_names
            continue
        assert not any(f in m for m in mods for f in forbidden_mod), mods
