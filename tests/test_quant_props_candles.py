"""W109.4 -- props_candles on fake data with a known answer. No network."""
import json

from prediction_market_bot.quant import props_candles as P


def c(end, bid, ask):
    return {"end_period_ts": end, "yes_bid": {"close_dollars": bid}, "yes_ask": {"close_dollars": ask}}


def test_parse_ts_fraction_and_z():
    assert P.parse_ts("2026-11-10T05:35:25Z") == P.parse_ts("2026-11-10T05:35:25.123456Z")
    assert P.parse_ts("1970-01-01T00:01:00Z") == 60


def test_quote_carried_forward_and_never_from_future():
    cs = [c(100, "0.40", "0.44"), c(500, "0.70", "0.75")]
    q = P.quote_at(cs, 300)
    assert (q["bid"], q["ask"], q["age_s"]) == (0.40, 0.44, 200)
    assert P.quote_at(cs, 99) is None          # nothing before the first row
    assert P.quote_at(cs, 500)["bid"] == 0.70  # a row ending AT ts is usable


def test_one_sided_or_crossed_quote_rejected():
    assert P.quote_at([c(1, "0.00", "0.10")], 5) is None   # zero bid
    assert P.quote_at([c(1, "0.90", "1.00")], 5) is None   # one-dollar ask
    assert P.quote_at([c(1, "0.50", "0.40")], 5) is None   # crossed
    assert P.quote_at([{"end_period_ts": 1, "yes_bid": {}, "yes_ask": {"close_dollars": "0.5"}}], 5) is None


def test_entry_rows_leads_and_outcome():
    m = {"ticker": "KXNBAPTS-26NOV01AAABBB-X1-20", "event_ticker": "KXNBAPTS-26NOV01AAABBB", "result": "yes", "volume_fp": "10"}
    cs = [c(1000, "0.30", "0.34"), c(9000, "0.60", "0.64")]
    rows = P.entry_rows(m, cs, anchor_ts=10000, leads={"T-60": 3600, "T-5": 300})
    by = {r["lead"]: r for r in rows}
    assert by["T-60"]["ask"] == 0.34 and by["T-5"]["ask"] == 0.64
    assert by["T-60"]["y"] == 1.0 and by["T-60"]["series"] == "KXNBAPTS" and by["T-60"]["ts"] == 6400


def test_sample_events_keeps_events_whole_and_is_seeded():
    ms = [{"ticker": f"{e}-{i}", "event_ticker": e} for e in "ABCDE" for i in range(3)]
    a = P.sample_events(ms, 2, seed=1)
    assert a == P.sample_events(ms, 2, seed=1)
    assert len({m["event_ticker"] for m in a}) == 2 and len(a) == 6


def test_list_settled_dedups_pages_and_drops_scalar():
    pages = {
        "/markets": [{"markets": [{"ticker": "T1", "result": "yes", "close_time": "x"}, {"ticker": "T2", "result": "scalar", "close_time": "x"}], "cursor": "n"},
                     {"markets": [{"ticker": "T3", "result": "no", "close_time": "x"}], "cursor": ""}],
        "/historical/markets": [{"markets": [{"ticker": "T1", "result": "no", "close_time": "x"}, {"ticker": "T4", "result": "no", "close_time": "x"}], "cursor": ""}],
    }
    calls = {"/markets": 0, "/historical/markets": 0}

    def fetch(path):
        p = path.split("?")[0]
        i = calls[p]
        calls[p] += 1
        return pages[p][i]

    got = {m["ticker"]: m["result"] for m in P.list_settled(fetch, "S")}
    assert got == {"T1": "yes", "T3": "no", "T4": "no"}


def test_fetch_candles_batch_limit_and_missing():
    def fetch(path):
        return {"markets": [{"market_ticker": "A", "candlesticks": [c(1, "0.1", "0.2")]}]}
    out = P.fetch_candles(fetch, ["A", "B"], 0, 10)
    assert len(out["A"]) == 1 and out["B"] == []
    try:
        P.fetch_candles(fetch, [str(i) for i in range(101)], 0, 10)
        assert False
    except ValueError:
        pass


def test_cache_roundtrip(tmp_path):
    p = P.cache_path(str(tmp_path), "S")
    open(p, "w").write(json.dumps({"t": "T1", "c": []}) + "\nnot json\n")
    assert list(P.load_cache(str(tmp_path), "S")) == ["T1"]


def test_historical_schema_and_single_fetch():
    h = {"end_period_ts": 5, "yes_bid": {"close": "0.40"}, "yes_ask": {"close": "0.45"}}
    q = P.quote_at([h], 10)
    assert (q["bid"], q["ask"]) == (0.40, 0.45)
    seen = []

    def fetch(path):
        seen.append(path)
        return {"candlesticks": [h]}
    assert P.fetch_candles_one(fetch, "T1", 0, 9) == [h]
    assert seen[0].startswith("/historical/markets/T1/candlesticks?")
