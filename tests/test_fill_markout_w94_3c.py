"""W94.3 Part C: fill markout. Known-answer tests for the maker/taker markout code."""
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
_spec = importlib.util.spec_from_file_location("fill_markout", REPO / "12_EXPLORATORY" / "fill_markout" / "fill_markout.py")
fm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fm)


def test_parse_ts_tolerant():
    assert fm.parse_ts("2026-10-29T00:08:14Z").second == 14
    assert fm.parse_ts("2026-10-29T00:08:14.12345678+00:00").microsecond == 123456
    assert fm.parse_ts("2026-10-29T00:08:14.5Z").microsecond == 500000
    assert fm.parse_ts("") is None and fm.parse_ts("garbage") is None


def test_signed_markout_sides():
    # YES bought at 0.40, mid later 0.45 -> +0.05; NO bought at 0.60 (yes bid 0.40), yes mid later 0.45 -> held mid 0.55 -> -0.05
    assert abs(fm.signed_markout("YES", 0.40, 0.45) - 0.05) < 1e-12
    assert abs(fm.signed_markout("NO", 0.60, 0.45) - (-0.05)) < 1e-12


def test_sport_game_latency():
    assert fm.sport_of("KXNFLTOTAL-26OCT26X") == "NFL" and fm.sport_of("KXMLBHIT-X") == "MLB"
    assert fm.game_of("KXNHLGAME-26OCT20TBVGK-TB") == "NHL|26OCT20TBVGK"
    assert [fm.latency_bucket(s) for s in (5, 60, 61, 601, None)] == ["<=60s", "<=60s", "60s-10m", ">10m", "unknown"]


def test_summarize_clusters_and_skips_none():
    rows = [{"game": "g1", "h1": 0.1}, {"game": "g1", "h1": 0.1}, {"game": "g2", "h1": 0.3}, {"game": "g3", "h1": None}]
    s = fm.summarize(rows, "h1", b=200)
    assert s["n"] == 3 and s["games"] == 2 and s["lo"] <= s["mean"] <= s["hi"]
    assert fm.summarize([], "h1")["n"] == 0


def _rec(tk, ts, bid, ask):
    return {"ticker": tk, "run_ts": ts, "yes_bid": str(bid), "yes_ask": str(ask), "status": "active", "series_ticker": "KXNFLTOTAL"}


def test_take_row_known_values():
    prev = _rec("KXNFLTOTAL-26OCT26A-T1", "2026-10-26T10:00:00Z", 0.40, 0.44)
    nxt = _rec("KXNFLTOTAL-26OCT26A-T1", "2026-10-26T10:10:00Z", 0.45, 0.49)
    for r in (prev, nxt):
        r["_ts"], r["_q"] = fm.parse_ts(r["run_ts"]), fm.two_sided(r)
    yes, no = fm.take_row(prev, nxt, "YES"), fm.take_row(prev, nxt, "NO")
    # YES at ask .44, next mid .47: markout +.03 = spread cost -.02 + drift +.05; the ask moved up so the quote is gone
    assert abs(yes["markout"] - 0.03) < 1e-9 and abs(yes["spread_cost"] + 0.02) < 1e-9 and abs(yes["drift"] - 0.05) < 1e-9
    assert yes["still_there"] == 0.0
    # NO at 1-.40 = .60, held mid later .53: markout -.07; bid rose so NO's price fell -> still there
    assert abs(no["markout"] + 0.07) < 1e-9 and no["still_there"] == 1.0
    assert abs(yes["markout"] - (yes["spread_cost"] + yes["drift"])) < 1e-12


def test_snapshot_pairs_gap_and_chain(tmp_path):
    rows = [_rec("KXNFLTOTAL-26OCT26A-T1", "2026-10-26T10:00:00Z", 0.4, 0.44),
            _rec("KXNFLTOTAL-26OCT26A-T1", "2026-10-26T10:00:30Z", 0.4, 0.44),   # same burst: not a next snapshot
            _rec("KXNFLTOTAL-26OCT26A-T1", "2026-10-26T10:10:00Z", 0.4, 0.44),
            _rec("KXNFLTOTAL-26OCT26A-T1", "2026-10-26T12:00:00Z", 0.4, 0.44)]   # 110 min later: too far
    (tmp_path / "prices_2026-10-26.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    pairs = list(fm.snapshot_pairs(tmp_path, "2026-10-11", ("KXNFL",)))
    assert len(pairs) == 1


def test_simulated_book_known_answer():
    sim = fm.simulate_book(n=200_000)
    # informed flow -> resting maker loses to the move: h - jump*w = .01 - .04*.5 = -.01
    assert abs(sim["maker_markout_theory"] + 0.01) < 1e-12
    assert abs(sim["maker_markout"] - sim["maker_markout_theory"]) < 4 * sim["maker_se"]
    assert sim["maker_markout"] < 0
    # an uninformed taker's drift is zero; its markout is just the spread
    assert abs(sim["taker_drift"]) < 4 * sim["taker_drift_se"]
    assert abs(sim["taker_markout"] - sim["taker_markout_theory"]) < 4 * sim["taker_drift_se"]
    # no informed flow -> maker is positive (earns the half-spread)
    assert fm.simulate_book(p_informed=0.0, n=50_000)["maker_markout"] > 0.009
