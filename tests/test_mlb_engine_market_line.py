import json
import pandas as pd
import pytest

from prediction_market_bot.mlb_engine import market_line as mk


def test_parse_event_known_answer_and_dst():
    e = mk.parse_event("KXMLBGAME-26SEP101905COLNYY")
    assert (e["away"], e["home"]) == ("COL", "NYY")
    assert e["start_utc"].isoformat() == "2026-09-10T23:05:00+00:00"  # 19:05 EDT = 23:05Z
    assert mk.parse_event("KXMLBGAME-26SEP121915CWSSTL")["home"] == "STL"
    assert mk.parse_event("KXMLBGAME-26OCT311905COLNYY")["start_utc"].hour == 23
    assert mk.parse_event("garbage") is None


def _row(ticker, ts, bid, ask, series):
    return {"run_ts": ts, "series_ticker": series, "ticker": ticker, "event_ticker": ticker.rsplit("-", 1)[0],
            "yes_bid": str(bid), "yes_ask": str(ask), "volume": "5"}


def test_last_pregame_never_uses_snapshots_inside_cutoff_and_moneyline_normalises(tmp_path):
    ev = "KXMLBGAME-26SEP101905COLNYY"  # first pitch 23:05Z
    rows = [_row(ev + "-NYY", "2026-09-10T20:00:00Z", 0.60, 0.62, "KXMLBGAME"),
            _row(ev + "-COL", "2026-09-10T20:00:00Z", 0.40, 0.42, "KXMLBGAME"),
            _row(ev + "-NYY", "2026-09-10T22:59:00Z", 0.99, 1.00, "KXMLBGAME"),  # inside the 10-min cutoff: ignored
            _row(ev + "-COL", "2026-09-10T22:59:00Z", 0.01, 0.02, "KXMLBGAME")]
    (tmp_path / "prices_2026-09-10.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    c = mk.last_pregame(str(tmp_path / "*.jsonl"))
    m = mk.moneyline(c)
    assert len(m) == 1 and m.p_home_mkt[0] == pytest.approx(0.61 / (0.61 + 0.41))
    assert m.half_spread[0] == pytest.approx(0.01)


def test_total_rung_picks_closest_to_half(tmp_path):
    ev = "KXMLBTOTAL-26SEP101905COLNYY"
    rows = [_row(f"{ev}-{k}", "2026-09-10T20:00:00Z", m - 0.01, m + 0.01, "KXMLBTOTAL")
            for k, m in ((8, 0.74), (9, 0.64), (10, 0.52), (11, 0.44))]
    (tmp_path / "prices_2026-09-10.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    t = mk.total_rung(mk.last_pregame(str(tmp_path / "*.jsonl")))
    assert t.k[0] == 10 and t.p_mkt[0] == pytest.approx(0.52)
