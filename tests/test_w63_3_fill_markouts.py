"""W63.3 Part B — markout analysis: held-side convention, two-sided-only mids, filled vs never-filled anchors."""
import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO / "src"))

import w63_3_fill_markouts as fm  # noqa: E402

T0 = 1_700_000_000


def _c(t, bid, ask):
    return {"end_period_ts": t, "yes_bid": {"close_dollars": str(bid)}, "yes_ask": {"close_dollars": str(ask)}}


@pytest.mark.unit
class TestCandles:
    def test_yes_and_no_held_side(self):
        C = fm.Candles([_c(T0, 0.40, 0.50)])
        assert C.quote(T0 + 5, "YES") == {"bid": 0.40, "ask": 0.50, "two_sided": True, "age_s": 5}
        q = C.quote(T0 + 5, "NO")
        assert (round(q["bid"], 2), round(q["ask"], 2)) == (0.50, 0.60)

    def test_one_sided_book_is_not_a_mid(self):
        assert fm.Candles([_c(T0, 0.0, 0.02)]).quote(T0, "YES")["two_sided"] is False
        assert fm.Candles([_c(T0, 0.54, 1.0)]).quote(T0, "YES")["two_sided"] is False

    def test_stale_or_missing_is_none(self):
        C = fm.Candles([_c(T0, 0.4, 0.5)])
        assert C.quote(T0 - 1, "YES") is None and C.quote(T0 + 4000, "YES") is None


@pytest.mark.unit
class TestBuild:
    def _world(self, tmp_path, filled):
        pos = {"position_id": "P1", "kalshi_ticker": "KXMLBHIT-GAME1-X-1", "direction": "YES", "kalshi_order_id": "O1",
               "band": "T4M-PROJ", "outcome": "WIN", "kalshi_settlement_value": 1.0, "mid_price_at_entry": 0.45}
        pf = tmp_path / "pf.json"; pf.write_text(json.dumps({"closed_positions": [pos]}))
        sc = tmp_path / "sc.jsonl"
        sc.write_text(json.dumps({"position_id": "P1", "fill_class": "CONFIRMED_FILLED" if filled else "CONFIRMED_NOT_FILLED"}) + "\n")
        sub = "2023-11-14T22:13:20+00:00"  # == T0
        venue = {"fills": [{"order_id": "O1", "created_time": "2023-11-14T22:14:20+00:00", "yes_price": 45, "count": 10, "is_taker": False}] if filled else [],
                 "orders": {"O1": {"created_time": sub, "type": "limit", "time_in_force": "good_till_canceled", "yes_price": 45}}}
        candles = {"KXMLBHIT-GAME1-X-1": [_c(T0, 0.40, 0.50), _c(T0 + 120, 0.30, 0.40), _c(T0 + 400, 0.20, 0.30)]}
        return pf, sc, venue, candles

    def test_filled_row_anchors_at_fill_and_is_adverse(self, tmp_path):
        pf, sc, venue, candles = self._world(tmp_path, True)
        [r] = fm.build("b", pf, sc, venue, candles)
        assert r["fill_price"] == 0.45 and r["secs_to_fill"] == 60.0 and r["is_taker"] is False
        assert r["mo_fill_1m"] == pytest.approx(0.35 - 0.45)
        assert r["limit_minus_venue_mid"] == pytest.approx(0.0)
        assert r["mo_settle"] == pytest.approx(0.55)

    def test_not_filled_row_anchors_at_limit_at_submit(self, tmp_path):
        pf, sc, venue, candles = self._world(tmp_path, False)
        [r] = fm.build("b", pf, sc, venue, candles)
        assert "fill_price" not in r and r["anchor_price"] == 0.45
        assert r["mo_sub_5m"] == pytest.approx(0.35 - 0.45)  # last candle <= T0+300s is the T0+120 one

    def test_ci_empty_is_none_not_zero(self):
        assert fm.ci([], "x") == {"n": 0, "mean": None, "ci95": None}
