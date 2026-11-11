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
