"""W88.2 Part B: shadow rows carry the exchange's own quote time and its age; additive, no decision reads it."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from prediction_market_bot.pregame_shadow.ledger import ROW_FIELDS
from prediction_market_bot.pregame_shadow.runner import quote_fields, run_once

NOW = datetime(2026, 10, 27, 1, 40, 0, tzinfo=timezone.utc)


def test_quote_fields_from_server_date():
    f = quote_fields({"_quote_server_date": "Tue, 27 Oct 2026 01:39:58 GMT"}, NOW)
    assert f == {"quote_ts_utc": "2026-10-27T01:39:58+00:00", "quote_age_s": 2.0,
                 "quote_ts_source": "kalshi_response_date"}


def test_quote_fields_missing_or_garbage_is_none_not_our_clock():
    for m in ({}, {"_quote_server_date": None}, {"_quote_server_date": "not a date"}):
        assert quote_fields(m, NOW) == {"quote_ts_utc": None, "quote_age_s": None, "quote_ts_source": None}


def test_run_once_rows_carry_quote_fields_and_keep_existing_ones(tmp_path):
    fc = SimpleNamespace(sport="MLB", p_yes=0.6, model_id="m", model_sha256="s", feature_row_sha256="f")
    forecaster = SimpleNamespace(forecast=lambda tkr, now: fc)
    m = {"ticker": "T-A", "event_ticker": "E", "yes_bid_dollars": "0.50", "yes_ask_dollars": "0.52",
         "_quote_server_date": "Tue, 27 Oct 2026 01:39:59 GMT"}
    start = NOW + timedelta(hours=20)
    res = run_once(forecaster=forecaster, cells=[("MLB_MONEYLINE", "S")], list_markets=lambda s: (True, [m]),
                   kickoff_for=lambda ev: (start, "test"), ledger_dir=tmp_path, run_id="r1", now_utc=NOW,
                   code_sha="x")
    assert res["written"] == {"MLB_MONEYLINE:T1": 1}
    row = json.loads(next(tmp_path.glob("*.jsonl")).read_text())
    assert all(f in row for f in ROW_FIELDS)
    assert list(row)[:len(ROW_FIELDS)] == list(ROW_FIELDS)      # existing fields untouched, in order
    assert row["quote_age_s"] == 1.0 and row["quote_ts_source"] == "kalshi_response_date"


def test_book_fields_read_sizes_or_say_none():
    """W105.2 / GG-1794: sizes from the market dict already fetched; absent is None, never 0."""
    from prediction_market_bot.pregame_shadow.runner import book_fields
    assert book_fields({"yes_bid_size_fp": "120.00", "yes_ask_size": 35}) == {"book_yes_bid_size": 120.0, "book_yes_ask_size": 35.0}
    assert book_fields({}) == {"book_yes_bid_size": None, "book_yes_ask_size": None}


def test_run_once_rows_and_on_row_carry_book_sizes(tmp_path):
    fc = SimpleNamespace(sport="MLB", p_yes=0.6, model_id="m", model_sha256="s", feature_row_sha256="f")
    forecaster = SimpleNamespace(forecast=lambda tkr, now: fc)
    m = {"ticker": "T-A", "event_ticker": "E", "yes_bid_dollars": "0.50", "yes_ask_dollars": "0.52",
         "yes_bid_size_fp": "80.00", "yes_ask_size_fp": "15.00"}
    seen = []
    run_once(forecaster=forecaster, cells=[("MLB_MONEYLINE", "S")], list_markets=lambda s: (True, [m]),
             kickoff_for=lambda ev: (NOW + timedelta(hours=20), "test"), ledger_dir=tmp_path, run_id="r1",
             now_utc=NOW, code_sha="x", on_row=seen.append)
    row = json.loads(next(tmp_path.glob("*.jsonl")).read_text())
    assert row["book_yes_bid_size"] == 80.0 and row["book_yes_ask_size"] == 15.0
    assert seen[0]["book_yes_bid_size"] == 80.0 and seen[0]["yes_bid"] == 0.50
