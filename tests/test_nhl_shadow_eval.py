import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


ev = _load("nhl_shadow_eval")
st = _load("nhl_shadow_settle")
NOW = datetime(2026, 10, 3, 12, tzinfo=timezone.utc)


class Stub:
    sport = "NHL"

    class F:
        def __init__(self, p): self.p_yes, self.model_id = p, "stub"; self.model_sha256 = self.feature_row_sha256 = "0" * 64; self.as_of_utc = NOW

    def __init__(self, p=0.6, none=False): self.p, self.none = p, none

    def forecast(self, t, as_of):
        return None if self.none else self.F(self.p)


def mkt(ticker="KXNHLGAME-26OCT03CHIBUF-BUF", ev_t="KXNHLGAME-26OCT03CHIBUF", bid="0.50", ask="0.54", **kw):
    return {"ticker": ticker, "event_ticker": ev_t, "yes_bid_dollars": bid, "yes_ask_dollars": ask,
            "occurrence_datetime": "2026-10-04T02:00:00Z", **kw}


INDEX = {("2026-10-03", frozenset(("CHI", "BUF"))): "2026-10-03T23:00:00Z"}  # 11h from NOW -> T1


def test_fee_and_edge_math():
    assert ev.fee_per_contract(0.5, 0.07) == pytest.approx(0.0175)
    ey, en = ev.edge_net(0.60, 0.50, 0.54, 0.07)
    assert ey == pytest.approx(0.60 - 0.54 - 0.07 * 0.54 * 0.46)
    assert en == pytest.approx(0.40 - 0.50 - 0.07 * 0.5 * 0.5)


def test_event_parse_and_start_resolution():
    assert ev.event_date_teams("KXNHLGAME-26OCT03CHIBUF") == ("2026-10-03", frozenset(("CHI", "BUF")))
    assert ev.event_date_teams("garbage") is None
    s, src = ev.resolve_start(mkt(), INDEX)
    assert src == "nhl_schedule" and s.hour == 23
    s, src = ev.resolve_start(mkt(ev_t="KXNHLGAME-26OCT04XXXYYY"), INDEX)
    assert src == "kalshi_occurrence_minus_3h" and s == datetime(2026, 10, 3, 23, tzinfo=timezone.utc)


@pytest.mark.parametrize("h,b", [(30, "T1"), (6, "T2"), (0.5, "T3"), (2, None), (0.1, None), (60, None), (-1, None)])
def test_band_windows(h, b):
    assert ev.band_for(h) == b


def test_rows_schema_and_band():
    rows = ev.evaluate({"KXNHLGAME": [mkt()]}, Stub(), INDEX, NOW - timedelta(hours=18), "r1", "abc")
    assert len(rows) == 1 and rows[0]["band"] == "T1" and rows[0]["market_type"] == "NHL_MONEYLINE"
    for k in ("run_id ts_utc sport market_type band horizon_hours_to_start event_ticker market_ticker p_yes yes_bid "
              "yes_ask mid half_spread fee_k007 fee_kmult e_net_yes_k007 e_net_no_k007 model_id model_sha256 "
              "feature_row_sha256 start_time_utc start_time_source code_sha").split():
        assert k in rows[0]
    assert rows[0]["mid"] == pytest.approx(0.52) and rows[0]["half_spread"] == pytest.approx(0.02)


def test_outside_window_forced_band_and_bad_quotes_skipped():
    assert ev.evaluate({"KXNHLGAME": [mkt()]}, Stub(), INDEX, NOW, "r", "x") == []          # 11h: no band
    assert ev.evaluate({"KXNHLGAME": [mkt()]}, Stub(), INDEX, NOW - timedelta(hours=18), "r", "x", "T3") == []
    now = NOW - timedelta(hours=18)
    for bad in (mkt(bid="0.00"), mkt(ask="1.00"), mkt(bid="0.6", ask="0.5"), {**mkt(), "yes_bid_dollars": None}):
        assert ev.evaluate({"KXNHLGAME": [bad]}, Stub(), INDEX, now, "r", "x") == []
    assert ev.evaluate({"KXNHLGAME": [mkt()]}, Stub(none=True), INDEX, now, "r", "x") == []  # forecaster abstains


def test_append_idempotent_and_append_only(tmp_path):
    rows = ev.evaluate({"KXNHLGAME": [mkt()]}, Stub(), INDEX, NOW - timedelta(hours=18), "r1", "abc")
    assert ev.append_rows(rows, tmp_path) == {"NHL_MONEYLINE_T1": 1}
    assert ev.append_rows(rows, tmp_path) == {}
    rows2 = [dict(rows[0], run_id="r2")]
    assert ev.append_rows(rows2, tmp_path) == {"NHL_MONEYLINE_T1": 1}
    assert len((tmp_path / "NHL_MONEYLINE_T1.jsonl").read_text().splitlines()) == 2


def test_fetch_markets_paginates_and_halves_on_429(monkeypatch):
    monkeypatch.setattr(ev.ni.time, "sleep", lambda s: None)
    calls = []

    def opener(url):
        calls.append(url)
        if len(calls) == 1:
            return 429, b""
        return 200, json.dumps({"markets": [{"ticker": f"T{len(calls)}"}], "cursor": "c" if len(calls) == 2 else ""}).encode()
    th = ev.ni.Throttle(0.0, base_s=0.0)
    th.interval_s = 1.0
    out = ev.fetch_open_markets("KXNHLGAME", th, opener=opener)
    assert len(out) == 2 and "cursor=c" in calls[-1] and th.interval_s > 1.0


def test_settle_join(tmp_path):
    row = {"run_id": "r", "market_ticker": "A", "market_type": "NHL_MONEYLINE", "band": "T1", "p_yes": 0.7,
           "mid": 0.6, "model_id": "m", "e_net_yes_k007": 0.1, "e_net_no_k007": -0.2, "start_time_utc": "x"}
    out = st.settle_rows([row, dict(row, market_ticker="B"), dict(row, market_ticker="C")],
                         {"A": {"status": "finalized", "result": "yes"}, "B": {"status": "open"},
                          "C": {"status": "settled", "result": "scalar"}})
    assert len(out) == 1 and out[0]["outcome"] == 1
    assert out[0]["brier_model"] == pytest.approx(0.09) and out[0]["brier_market"] == pytest.approx(0.16)
