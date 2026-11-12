import importlib.util
import json
from pathlib import Path

P = Path(__file__).resolve().parent.parent / "scripts" / "replay_router_w110_3.py"
spec = importlib.util.spec_from_file_location("replay_w110_3", P)
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)


def test_decisions_one_per_ticker_tier_and_no_bet_on_bad_book(tmp_path):
    rows = [{"run_ts": "2026-11-10T12:00:00Z", "series_ticker": "KXNHLGAME", "ticker": "KXNHLGAME-26NOV14BOSNYR-BOS",
             "event_ticker": "KXNHLGAME-26NOV14BOSNYR", "yes_bid": "0.4000", "yes_ask": "0.4200"}] * 3
    rows.append({**rows[0], "ticker": "T2", "yes_bid": "0.0000", "yes_ask": "0.5"})
    (tmp_path / "prices_2026-11-10.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    out, files = rp.decisions(str(tmp_path), 14)
    assert len(out) == 2 and files == ["prices_2026-11-10.jsonl"]
    assert [o for o in out if o["ticker"] == "T2"][0]["branch"] == "NO_BET"


def test_score_unfetched_counts_unsettled():
    rows = [{"branch": "RIDE", "side": "yes", "ticker": "X", "event": "E", "bid": 0.4, "ask": 0.42}]
    res, un = rp.score(rows, fetch=False)
    assert res == {} and un == {"RIDE": 1}


def test_replay_reads_leaf_map_and_is_not_all_no_bet(tmp_path):
    """W111.3: a T1 date-only-ticker market in a leaf the map routes is logged as that arm (replay bounds 1 and 2)."""
    from prediction_market_bot.decision_trees import leaf_map as lm

    d = lm.default_map().leaves
    mid_for = {"2": 0.57, "3": 0.72, "4": 0.9}
    kind = {"MONEYLINE": "GAME", "SPREAD": "SPREAD", "PUCK_LINE": "SPREAD", "GAME_TOTAL": "TOTAL"}
    pick = None
    for k, v in d.items():
        s, mt, b, fb, mb = k.split("|")
        suffix = mt.split("_", 1)[1]
        if s in ("NHL", "NBA", "NFL") and b == "T1" and mb == "na" and not v["thin"] and v["arm"] in ("RIDE", "FADE") \
                and fb in mid_for and suffix in kind:
            pick = (s, mt, v["arm"], mid_for[fb], f"KX{s}{kind[suffix]}")
            break
    assert pick, "map has no T1 RIDE/FADE leaf to test"
    s, mt, arm, mid, series = pick
    ev = f"{series}-26NOV14BOSNYR"
    row = {"run_ts": "2026-11-10T12:00:00Z", "series_ticker": series, "ticker": ev + "-BOS", "event_ticker": ev,
           "yes_bid": f"{mid - 0.01:.4f}", "yes_ask": f"{mid + 0.01:.4f}"}
    (tmp_path / "prices_2026-11-10.jsonl").write_text(json.dumps(row))
    out, _ = rp.decisions(str(tmp_path), 14)
    assert out[0]["tier"] in ("D2+", "D1", "T>24h") and out[0]["branch"] == arm
