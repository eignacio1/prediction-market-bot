"""Tests for scripts/build_t4_outcome_store.py (T-421).

Coverage areas:
  - ticker_game_date(): correct parse of the embedded date token, including a
    doubleheader-suffixed ticker; None on malformed input (GG-164 fix).
  - group_by_ticker(): many cycle-log rows fold into one ticker record;
    has_forecast is True iff any row in the group carries p_t4;
    game_date is ticker-derived, not the raw (unreliable) field.
  - load_store/write_store: JSONL round-trip is lossless and atomic (no
    partial file left behind on a mid-write crash).
  - attempt_resolution(): MLB_R -> MLB_P -> ESPN fallback order; stops at
    the first source that resolves; every source tried is recorded in
    `attempts` with its result, even on total failure (first-class failure
    data, not a silent drop).
  - run_backfill(): already-resolved tickers are never re-attempted
    (idempotent/resumable); unresolved tickers are retried and accumulate
    additional attempts on a second run.

All network-touching resolution helpers (_fetch_mlb_hits, _espn_fetch_hits)
are mocked — no real HTTP calls are made by this test module.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

MODULE_PATH = Path(__file__).parent.parent / "scripts" / "build_t4_outcome_store.py"
_spec = importlib.util.spec_from_file_location("build_t4_outcome_store", MODULE_PATH)
outcome_store = importlib.util.module_from_spec(_spec)
sys.modules["build_t4_outcome_store"] = outcome_store
_spec.loader.exec_module(outcome_store)


# ---------------------------------------------------------------------------
# ticker_game_date
# ---------------------------------------------------------------------------

class TestTickerGameDate:
    @pytest.mark.unit
    def test_standard_ticker(self):
        assert outcome_store.ticker_game_date(
            "KXMLBHIT-26JUL021410CINMIL-MILWCONTRERAS24-2"
        ) == "2026-07-02"

    @pytest.mark.unit
    def test_doubleheader_suffix_does_not_break_date_parse(self):
        assert outcome_store.ticker_game_date(
            "KXMLBHIT-26JUL171335TBBOSG1-BOSDEVERS11-1"
        ) == "2026-07-17"
        assert outcome_store.ticker_game_date(
            "KXMLBHIT-26JUL171335TBBOSG2-BOSDEVERS11-1"
        ) == "2026-07-17"

    @pytest.mark.unit
    def test_year_boundary_month(self):
        assert outcome_store.ticker_game_date(
            "KXMLBHIT-26AUG011610MINSEA-SEACRALEIGH29-1"
        ) == "2026-08-01"

    @pytest.mark.unit
    def test_malformed_ticker_returns_none(self):
        assert outcome_store.ticker_game_date("NOT-A-TICKER") is None
        assert outcome_store.ticker_game_date("") is None


# ---------------------------------------------------------------------------
# group_by_ticker
# ---------------------------------------------------------------------------

class TestGroupByTicker:
    @pytest.mark.unit
    def test_folds_multiple_rows_into_one_record(self):
        rows = [
            {"ticker": "KXMLBHIT-26JUL021410CINMIL-MILWCONTRERAS24-2",
             "player_id": 661388, "player_name": "William Contreras",
             "threshold": 2, "game_date": "2026-07-02", "p_t4": 0.12},
            {"ticker": "KXMLBHIT-26JUL021410CINMIL-MILWCONTRERAS24-2",
             "player_id": 661388, "player_name": "William Contreras",
             "threshold": 2, "game_date": "2026-07-03", "p_t4": 0.15},
        ]
        grouped = outcome_store.group_by_ticker(rows)
        assert len(grouped) == 1
        g = grouped["KXMLBHIT-26JUL021410CINMIL-MILWCONTRERAS24-2"]
        assert g["n_cycle_rows"] == 2
        assert g["has_forecast"] is True
        # ticker-derived date wins over the raw (possibly wrong, GG-164) field
        assert g["game_date"] == "2026-07-02"
        assert g["date_source"] == "ticker"

    @pytest.mark.unit
    def test_vig_skip_only_group_has_no_forecast(self):
        rows = [
            {"ticker": "KXMLBHIT-26JUL031915NYMATL-ATLMOLSON28-2",
             "player_id": 621566, "player_name": "Matt Olson",
             "threshold": 2, "game_date": "2026-07-03", "vig_skip": True},
        ]
        grouped = outcome_store.group_by_ticker(rows)
        g = grouped["KXMLBHIT-26JUL031915NYMATL-ATLMOLSON28-2"]
        assert g["has_forecast"] is False

    @pytest.mark.unit
    def test_mixed_vig_skip_and_forecast_rows_is_has_forecast_true(self):
        ticker = "KXMLBHIT-26JUL031915NYMATL-ATLMOLSON28-2"
        rows = [
            {"ticker": ticker, "player_id": 621566, "player_name": "Matt Olson",
             "threshold": 2, "game_date": "2026-07-03", "vig_skip": True},
            {"ticker": ticker, "player_id": 621566, "player_name": "Matt Olson",
             "threshold": 2, "game_date": "2026-07-03", "p_t4": 0.3},
        ]
        grouped = outcome_store.group_by_ticker(rows)
        assert grouped[ticker]["has_forecast"] is True
        assert grouped[ticker]["n_cycle_rows"] == 2

    @pytest.mark.unit
    def test_malformed_ticker_falls_back_to_raw_game_date(self):
        rows = [
            {"ticker": "GARBAGE-TICKER", "player_id": 1, "player_name": "X",
             "threshold": 1, "game_date": "2026-07-02", "p_t4": 0.1},
        ]
        grouped = outcome_store.group_by_ticker(rows)
        g = grouped["GARBAGE-TICKER"]
        assert g["date_source"] == "raw_fallback"
        assert g["game_date"] == "2026-07-02"


# ---------------------------------------------------------------------------
# load_store / write_store round-trip
# ---------------------------------------------------------------------------

class TestStoreRoundTrip:
    @pytest.mark.unit
    def test_round_trip_is_lossless(self, tmp_path):
        store_path = tmp_path / "outcome_store.jsonl"
        store = {
            "T1": {"ticker": "T1", "resolved": True, "actual_hits": 2.0},
            "T2": {"ticker": "T2", "resolved": False, "attempts": [{"source": "MLB_R", "result": None}]},
        }
        outcome_store.write_store(store_path, store)
        loaded = outcome_store.load_store(store_path)
        assert loaded == store

    @pytest.mark.unit
    def test_write_is_atomic_no_tmp_file_left_behind(self, tmp_path):
        store_path = tmp_path / "outcome_store.jsonl"
        outcome_store.write_store(store_path, {"T1": {"ticker": "T1", "resolved": True}})
        leftovers = list(tmp_path.glob(".outcome_store_*"))
        assert leftovers == []
        assert store_path.exists()

    @pytest.mark.unit
    def test_load_missing_store_returns_empty_dict(self, tmp_path):
        assert outcome_store.load_store(tmp_path / "does_not_exist.jsonl") == {}


# ---------------------------------------------------------------------------
# attempt_resolution — fallback order and first-class failure data
# ---------------------------------------------------------------------------

class TestAttemptResolution:
    @pytest.mark.unit
    def test_resolves_on_mlb_regular_season_first_try(self):
        rec = {"player_id": 1, "game_date": "2026-07-02", "player_name": "X"}
        with patch.object(outcome_store, "_fetch_mlb_hits", return_value=2.0) as m_mlb, \
             patch.object(outcome_store, "_espn_fetch_hits") as m_espn:
            outcome_store.attempt_resolution(rec)

        assert rec["resolved"] is True
        assert rec["actual_hits"] == 2.0
        assert rec["resolution_source"] == "MLB_R"
        assert len(rec["attempts"]) == 1
        assert rec["attempts"][0]["source"] == "MLB_R"
        m_mlb.assert_called_once_with(1, "2026-07-02", "R")
        m_espn.assert_not_called()

    @pytest.mark.unit
    def test_falls_back_to_postseason_then_espn(self):
        rec = {"player_id": 1, "game_date": "2026-10-15", "player_name": "X"}
        with patch.object(outcome_store, "_fetch_mlb_hits", side_effect=[None, 3.0]) as m_mlb, \
             patch.object(outcome_store, "_espn_fetch_hits") as m_espn:
            outcome_store.attempt_resolution(rec)

        assert rec["resolved"] is True
        assert rec["resolution_source"] == "MLB_P"
        sources_tried = [a["source"] for a in rec["attempts"]]
        assert sources_tried == ["MLB_R", "MLB_P"]
        assert m_mlb.call_count == 2
        m_espn.assert_not_called()

    @pytest.mark.unit
    def test_falls_back_to_espn_when_both_mlb_attempts_fail(self):
        rec = {"player_id": 1, "game_date": "2026-07-02", "player_name": "William Contreras"}
        with patch.object(outcome_store, "_fetch_mlb_hits", return_value=None), \
             patch.object(outcome_store, "_espn_fetch_hits", return_value=1.0) as m_espn:
            outcome_store.attempt_resolution(rec)

        assert rec["resolved"] is True
        assert rec["resolution_source"] == "ESPN"
        sources_tried = [a["source"] for a in rec["attempts"]]
        assert sources_tried == ["MLB_R", "MLB_P", "ESPN"]
        m_espn.assert_called_once_with("William Contreras", "2026-07-02")

    @pytest.mark.unit
    def test_total_failure_records_every_source_as_unresolved_not_dropped(self):
        rec = {"player_id": 1, "game_date": "2026-07-02", "player_name": "X"}
        with patch.object(outcome_store, "_fetch_mlb_hits", return_value=None), \
             patch.object(outcome_store, "_espn_fetch_hits", return_value=None):
            outcome_store.attempt_resolution(rec)

        assert rec["resolved"] is False
        assert "actual_hits" not in rec
        assert len(rec["attempts"]) == 3
        assert all(a["result"] is None for a in rec["attempts"])
        assert rec["attempt_count"] == 3
        assert "last_attempted_at" in rec
        assert "first_attempted_at" in rec

    @pytest.mark.unit
    def test_no_player_name_skips_espn_but_still_records_it(self):
        rec = {"player_id": 1, "game_date": "2026-07-02", "player_name": None}
        with patch.object(outcome_store, "_fetch_mlb_hits", return_value=None), \
             patch.object(outcome_store, "_espn_fetch_hits") as m_espn:
            outcome_store.attempt_resolution(rec)

        assert rec["resolved"] is False
        sources_tried = [a["source"] for a in rec["attempts"]]
        assert sources_tried == ["MLB_R", "MLB_P", "ESPN"]
        espn_attempt = rec["attempts"][-1]
        assert espn_attempt["result"] is None
        assert "skipped" in espn_attempt["detail"]
        m_espn.assert_not_called()

    @pytest.mark.unit
    def test_captured_stderr_surfaces_as_detail_on_failure(self):
        def _mlb_side_effect(*_args):
            import sys as _sys
            print("HTTPError: 403 Forbidden", file=_sys.stderr)
            return None

        rec = {"player_id": 1, "game_date": "2026-07-02", "player_name": None}
        with patch.object(outcome_store, "_fetch_mlb_hits", side_effect=_mlb_side_effect), \
             patch.object(outcome_store, "_espn_fetch_hits", return_value=None):
            outcome_store.attempt_resolution(rec)

        assert "403 Forbidden" in rec["attempts"][0]["detail"]


# ---------------------------------------------------------------------------
# run_backfill — idempotency / resumability
# ---------------------------------------------------------------------------

class TestRunBackfillIdempotency:
    @pytest.mark.unit
    def test_already_resolved_ticker_is_never_refetched(self, tmp_path):
        cycle_log = tmp_path / "cycle_log.jsonl"
        ticker = "KXMLBHIT-26JUL021410CINMIL-MILWCONTRERAS24-2"
        cycle_log.write_text(json.dumps({
            "ticker": ticker, "player_id": 661388, "player_name": "William Contreras",
            "threshold": 2, "game_date": "2026-07-02", "p_t4": 0.12,
        }) + "\n")

        store_path = tmp_path / "store.jsonl"
        outcome_store.write_store(store_path, {
            ticker: {"ticker": ticker, "player_id": 661388, "player_name": "William Contreras",
                     "threshold": 2, "game_date": "2026-07-02", "resolved": True,
                     "actual_hits": 2.0, "attempts": [{"source": "MLB_R", "result": 2.0}]},
        })

        with patch.object(outcome_store, "_fetch_mlb_hits") as m_mlb, \
             patch.object(outcome_store, "_espn_fetch_hits") as m_espn:
            summary = outcome_store.run_backfill(cycle_log, store_path, limit=None)

        m_mlb.assert_not_called()
        m_espn.assert_not_called()
        assert summary["attempted_this_run"] == 0
        assert summary["resolved_total"] == 1

    @pytest.mark.unit
    def test_unresolved_ticker_is_retried_and_accumulates_attempts(self, tmp_path):
        cycle_log = tmp_path / "cycle_log.jsonl"
        ticker = "KXMLBHIT-26JUL021410CINMIL-MILWCONTRERAS24-2"
        cycle_log.write_text(json.dumps({
            "ticker": ticker, "player_id": 661388, "player_name": "William Contreras",
            "threshold": 2, "game_date": "2026-07-02", "p_t4": 0.12,
        }) + "\n")

        store_path = tmp_path / "store.jsonl"

        with patch.object(outcome_store, "_fetch_mlb_hits", return_value=None), \
             patch.object(outcome_store, "_espn_fetch_hits", return_value=None):
            outcome_store.run_backfill(cycle_log, store_path, limit=None)

        first_pass = outcome_store.load_store(store_path)
        assert first_pass[ticker]["resolved"] is False
        assert first_pass[ticker]["attempt_count"] == 3

        with patch.object(outcome_store, "_fetch_mlb_hits", return_value=None), \
             patch.object(outcome_store, "_espn_fetch_hits", return_value=None):
            outcome_store.run_backfill(cycle_log, store_path, limit=None)

        second_pass = outcome_store.load_store(store_path)
        assert second_pass[ticker]["attempt_count"] == 6
        assert len(second_pass[ticker]["attempts"]) == 6
