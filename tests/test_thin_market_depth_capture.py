"""W80P.1: scripts/thin_market_depth_capture.py -- bounded, rate-limited, resumable order-book capture (no network)."""
from __future__ import annotations

import importlib.util
import json
import sys
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
spec = importlib.util.spec_from_file_location("thin_capture", REPO / "scripts" / "thin_market_depth_capture.py")
tc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tc)
bs = tc.bs

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc).timestamp()


def _iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class FakeKalshi:
    """Opener for bs.Client: serves /markets listings, order books and candles from dicts; counts calls per path."""

    def __init__(self, markets, books=None, fail=(), broken_filter=False):
        self.markets, self.books, self.fail, self.calls = markets, books or {}, set(fail), []
        self.broken_filter = broken_filter      # a server that returns nothing whenever a close-time bound is sent

    def __call__(self, url):
        u = urllib.parse.urlparse(url)
        q = dict(urllib.parse.parse_qsl(u.query))
        path = u.path.split("/trade-api/v2", 1)[1]
        self.calls.append(path)
        if any(f in path for f in self.fail):
            raise urllib.error.HTTPError(url, 404, "nf", {}, None)
        if path == "/markets":
            ms = [m for m in self.markets if m["series"] == q["series_ticker"]]
            if "max_close_ts" in q:             # Kalshi filters on close_time, like the real server
                ms = [] if self.broken_filter else [
                    m for m in ms if int(q["min_close_ts"]) <= bs.iso_ts(m["close_time"]) <= int(q["max_close_ts"])]
            return 200, json.dumps({"markets": ms, "cursor": ""}).encode()
        if path.endswith("/orderbook"):
            t = path.split("/")[2]
            return 200, json.dumps({"orderbook": self.books.get(t, {"yes": [[40, 10]], "no": [[55, 7]]})}).encode()
        if path.endswith("/candlesticks"):
            return 200, json.dumps({"candlesticks": [{"end_period_ts": 1, "price": {"close": 50}}]}).encode()
        raise urllib.error.HTTPError(url, 404, "nf", {}, None)


def _m(ticker, series, event_in_h, open_ago_h=72, close_lag_h=45):
    """Event in `event_in_h` hours; close_time trails the event by close_lag_h, as Kalshi sets it (NFL: ~45 h)."""
    return {"ticker": ticker, "series": series, "event_ticker": ticker.rsplit("-", 1)[0],
            "occurrence_datetime": _iso(NOW + event_in_h * 3600),
            "close_time": _iso(NOW + (event_in_h + close_lag_h) * 3600), "open_time": _iso(NOW - open_ago_h * 3600),
            "yes_bid": 40, "yes_ask": 45, "volume": 100, "open_interest": 50}


def _client(fake):
    return bs.Client(opener=fake, pause=0, sleep=lambda s: None)


def _rows(store, stream):
    out = []
    for f in sorted(store.glob(f"{stream}_*.jsonl")):
        out += [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    return out


def test_only_markets_within_48h_are_snapshotted_closest_first(tmp_path):
    fake = FakeKalshi([_m("KXNFLTOTAL-A-1", "KXNFLTOTAL", 30), _m("KXNFLTOTAL-B-1", "KXNFLTOTAL", 2),
                       _m("KXNFLTOTAL-C-1", "KXNFLTOTAL", 60)])
    res = tc.run(_client(fake), tmp_path, now=NOW, sha="abc", series_list=("KXNFLTOTAL",))
    rows = _rows(tmp_path, "books")
    assert [r["ticker"] for r in rows] == ["KXNFLTOTAL-B-1", "KXNFLTOTAL-A-1"]
    assert res["books"] == 2 and res["listed"] == 2
    r = rows[0]
    assert r["book"]["orderbook"]["yes"] == [[40, 10]] and r["runtime_commit_sha"] == "abc"
    assert r["source_url"].endswith("/markets/KXNFLTOTAL-B-1/orderbook") and r["content_sha256"]
    assert r["listing_top"]["yes_bid"] == 40 and 0 < r["secs_to_event"] <= 2 * 3600
    assert r["secs_to_close"] == r["secs_to_event"] + 45 * 3600 and r["secs_to_kickoff_est"] == r["secs_to_event"] - 3 * 3600


def test_markets_whose_close_time_trails_the_event_by_45h_are_listed(tmp_path):
    # the 2026-10-19 defect: close_time = event + 45 h put every game inside 48 h outside a close_time window
    fake = FakeKalshi([_m("KXNFLGAME-G-1", "KXNFLGAME", 20)])
    res = tc.run(_client(fake), tmp_path, now=NOW, sha="s", series_list=("KXNFLGAME",))
    assert res["listed"] == 1 and res["books"] == 1 and res["fallback"] == 0


def test_filtered_listing_empty_falls_back_to_unfiltered_and_alarms(tmp_path, capsys):
    fake = FakeKalshi([_m("KXNFLGAME-G-1", "KXNFLGAME", 20), _m("KXNFLGAME-G-2", "KXNFLGAME", 90)], broken_filter=True)
    res = tc.run(_client(fake), tmp_path, now=NOW, sha="s", series_list=("KXNFLGAME",))
    assert res["listed"] == 1 and res["books"] == 1 and res["fallback"] == 1
    assert "THIN_CAPTURE ALARM" in capsys.readouterr().out


def test_genuinely_empty_board_is_quiet_not_an_alarm(tmp_path, capsys):
    fake = FakeKalshi([_m("KXNFLGAME-G-2", "KXNFLGAME", 90)])
    res = tc.run(_client(fake), tmp_path, now=NOW, sha="s", series_list=("KXNFLGAME",))
    assert res["listed"] == 0 and res["fallback"] == 0 and "ALARM" not in capsys.readouterr().out


def test_candle_daily_cap_leaves_the_books_their_budget(tmp_path, monkeypatch):
    monkeypatch.setattr(tc, "MAX_CANDLE_DAILY_BYTES", 600)
    fake = FakeKalshi([_m(f"KXNBAPTS-P-{i}", "KXNBAPTS", 1) for i in range(6)])
    tc.run(_client(fake), tmp_path, now=NOW, sha="s", series_list=("KXNBAPTS",))
    fake.markets = []
    res = tc.run(_client(fake), tmp_path, now=NOW + 3600 + tc.SETTLE_GRACE_S + 60, sha="s", series_list=("KXNBAPTS",))
    assert res["candle_capped"] == 1 and res["candle_markets"] < 6
    assert sum(f.stat().st_size for f in tmp_path.glob("candles_*.jsonl")) <= 600
    assert res["cap"] == "none"                                # the book cap is untouched


def test_near_markets_every_run_far_markets_every_3h_and_unchanged_rows_are_small(tmp_path):
    fake = FakeKalshi([_m("KXNBATOTAL-N-1", "KXNBATOTAL", 5), _m("KXNBATOTAL-F-1", "KXNBATOTAL", 30)])
    tc.run(_client(fake), tmp_path, now=NOW, sha="s", series_list=("KXNBATOTAL",))
    res = tc.run(_client(fake), tmp_path, now=NOW + 1800, sha="s", series_list=("KXNBATOTAL",))
    assert res["due"] == 1 and res["unchanged"] == 1          # far market not due 30 min later; near one is
    last = _rows(tmp_path, "books")[-1]
    assert last["ticker"] == "KXNBATOTAL-N-1" and "book" not in last and last["unchanged_of"]
    res = tc.run(_client(fake), tmp_path, now=NOW + 3 * 3600, sha="s", series_list=("KXNBATOTAL",))
    assert res["due"] == 2                                     # 3 h later the far market is due again


def test_books_per_run_cap(tmp_path, monkeypatch):
    monkeypatch.setattr(tc, "MAX_BOOKS_PER_RUN", 3)
    fake = FakeKalshi([_m(f"KXNFLSPREAD-E-{i}", "KXNFLSPREAD", 1 + i) for i in range(8)])
    res = tc.run(_client(fake), tmp_path, now=NOW, sha="s", series_list=("KXNFLSPREAD",))
    assert res["due"] == 8 and res["books"] == 3
    assert [r["ticker"] for r in _rows(tmp_path, "books")] == [f"KXNFLSPREAD-E-{i}" for i in range(3)]
    tc.run(_client(fake), tmp_path, now=NOW + 60, sha="s", series_list=("KXNFLSPREAD",))
    tc.run(_client(fake), tmp_path, now=NOW + 120, sha="s", series_list=("KXNFLSPREAD",))
    # least-recently-snapshotted first: after three runs every due market has been served, none starved
    assert {r["ticker"] for r in _rows(tmp_path, "books")} == {f"KXNFLSPREAD-E-{i}" for i in range(8)}


def test_daily_byte_cap_stops_writes_and_says_so(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(tc, "MAX_DAILY_BYTES", 900)
    fake = FakeKalshi([_m(f"KXNFLGAME-G-{i}", "KXNFLGAME", 1 + i) for i in range(5)])
    res = tc.run(_client(fake), tmp_path, now=NOW, sha="s", series_list=("KXNFLGAME",))
    assert res["cap"].startswith("daily cap") and res["books"] < 5
    assert sum(f.stat().st_size for f in tmp_path.glob("*.jsonl")) <= 900
    assert "THIN_CAPTURE CAP" in capsys.readouterr().out


def test_candles_after_close_then_ticker_leaves_state(tmp_path):
    fake = FakeKalshi([_m("KXNBAPTS-P-1", "KXNBAPTS", 1)])
    tc.run(_client(fake), tmp_path, now=NOW, sha="s", series_list=("KXNBAPTS",))
    assert "KXNBAPTS-P-1" in json.loads((tmp_path / "state.json").read_text())["tickers"]
    fake.markets = []                                          # closed: no longer listed as open
    res = tc.run(_client(fake), tmp_path, now=NOW + 1 * 3600 + tc.SETTLE_GRACE_S + 60, sha="s",
                 series_list=("KXNBAPTS",))
    assert res["candle_markets"] == 1
    c = _rows(tmp_path, "candles")
    assert sorted(r["period"] for r in c) == [1, 60] and all(r["ticker"] == "KXNBAPTS-P-1" for r in c)
    one = next(r for r in c if r["period"] == 1)
    assert one["end_ts"] - one["start_ts"] <= tc.MINUTE_LOOKBACK_S + 120
    assert json.loads((tmp_path / "state.json").read_text())["tickers"] == {}


def test_candle_failure_retries_then_gives_up(tmp_path):
    fake = FakeKalshi([_m("KXNFLRECYDS-R-1", "KXNFLRECYDS", 1)])
    tc.run(_client(fake), tmp_path, now=NOW, sha="s", series_list=("KXNFLRECYDS",))
    fake.markets, fake.fail = [], {"candlesticks"}
    t = NOW + 1 * 3600 + tc.SETTLE_GRACE_S + 60
    for i in range(tc.MAX_CANDLE_TRIES):
        res = tc.run(_client(fake), tmp_path, now=t + i * 1800, sha="s", series_list=("KXNFLRECYDS",))
        assert res["candle_errors"] == 1
    assert res["dropped"] == 1 and json.loads((tmp_path / "state.json").read_text())["tickers"] == {}


def test_failed_book_and_failed_series_do_not_stop_the_run(tmp_path):
    fake = FakeKalshi([_m("KXNFLTOTAL-A-1", "KXNFLTOTAL", 2), _m("KXNFLTOTAL-B-1", "KXNFLTOTAL", 3)],
                      fail={"/markets/KXNFLTOTAL-A-1/orderbook"})
    res = tc.run(_client(fake), tmp_path, now=NOW, sha="s", series_list=("KXNFLTOTAL", "KXNFLMISSING"))
    assert res["errors"] == 1 and res["books"] == 1
    # an unknown series lists empty (the fake returns no markets); a listing 404 counts as series_errors
    fake.fail = {"/markets"}
    res = tc.run(_client(fake), tmp_path, now=NOW + 60, sha="s", series_list=("KXNFLTOTAL",))
    assert res["series_errors"] == 1


def test_concurrent_run_skips(tmp_path):
    import fcntl
    tmp_path.mkdir(exist_ok=True)
    held = open(tmp_path / ".lock", "w")
    fcntl.flock(held, fcntl.LOCK_EX | fcntl.LOCK_NB)
    res = tc.run(_client(FakeKalshi([])), tmp_path, now=NOW, sha="s", series_list=())
    assert res == {"skipped": True}


def test_no_order_endpoint_is_ever_called(tmp_path):
    fake = FakeKalshi([_m("KXNBASPREAD-S-1", "KXNBASPREAD", 1)])
    tc.run(_client(fake), tmp_path, now=NOW, sha="s", series_list=("KXNBASPREAD",))
    tc.run(_client(fake), tmp_path, now=NOW + 10 * 3600, sha="s", series_list=("KXNBASPREAD",))
    assert fake.calls and not any("order" in p and not p.endswith("/orderbook") for p in fake.calls)
    assert not any("portfolio" in p for p in fake.calls)
