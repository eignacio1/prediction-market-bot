import importlib.util
from pathlib import Path

p = Path(__file__).resolve().parents[1] / "12_EXPLORATORY/market_history/score_vs_market.py"
s = importlib.util.spec_from_file_location("svm", p); svm = importlib.util.module_from_spec(s); s.loader.exec_module(svm)
q = importlib.util.spec_from_file_location("fgh", p.with_name("fetch_game_hourly.py")); fgh = importlib.util.module_from_spec(q); q.loader.exec_module(fgh)


def candle(end, bid, ask):
    return {"end_period_ts": end, "yes_bid": {"close": str(bid)}, "yes_ask": {"close": str(ask)}}


def test_pre_game_mid_uses_last_candle_at_or_before_cutoff():
    cs = [candle(100, 0.40, 0.44), candle(200, 0.50, 0.54), candle(300, 0.90, 0.94)]
    mid, spread, ts = svm.pre_game_mid(cs, 250)
    assert (round(mid, 4), round(spread, 4), ts) == (0.52, 0.04, 200)   # the 300 candle is after the cutoff
    assert svm.pre_game_mid(cs, 50) is None


def test_pre_game_mid_skips_candles_without_a_two_sided_quote():
    assert svm.pre_game_mid([{"end_period_ts": 1, "yes_bid": {}, "yes_ask": {"close": "0.5"}}], 10) is None


def test_listed_team_maps_kalshi_alias():
    assert svm.listed_team("KXNHLGAME-25OCT09TBVGK-TB") == "TBL"


def test_one_per_event_keeps_first_sorted_ticker():
    mk = [{"ticker": "E1-B", "event_ticker": "E1"}, {"ticker": "E1-A", "event_ticker": "E1"}, {"ticker": "E2-Z", "event_ticker": "E2"}]
    assert [m["ticker"] for m in fgh.one_per_event(mk)] == ["E1-A", "E2-Z"]
