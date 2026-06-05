"""
Tests: T3 Momentum Integration
================================
Covers:
    - load_t3_signals: fresh report → returns signal dict
    - load_t3_signals: stale report (>900s) → returns {}
    - load_t3_signals: no report file → returns {}
    - load_t3_signals: malformed JSON → returns {}
    - load_t3_signals: multiple report files → selects most recent
    - load_t3_signals: empty forecasts list → returns {}
    - Non-contamination: absent report → t3_signals empty → NEUTRAL on every ticker
    - Multiplier arithmetic: CONFIRM=1.15, FADE=0.75, NEUTRAL=1.0
    - Negative-edge FADE: |edge| shrinks correctly (sign preserved)
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.t3_signal_loader import (
    T3_MAX_STALENESS_S,
    load_t3_signals,
)
from prediction_market_bot.run_paper_trade import (
    T3_CONFIRM_MULTIPLIER,
    T3_FADE_MULTIPLIER,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GAME_DATE = "20260605"
TICKER_A  = "KXNBAPTS-26JUN05BOSMIA-BOSGA-25"
TICKER_B  = "KXNBAPTS-26JUN05BOSMIA-MIAGO-22"


def _make_report(tmp_path: Path, run_at: datetime, forecasts: list[dict],
                 suffix: str = "2130") -> Path:
    report = {
        "session_id": "T3-TEST",
        "band": "T3",
        "game_date": GAME_DATE,
        "run_at": run_at.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "forecasts": forecasts,
    }
    path = tmp_path / f"t3_{GAME_DATE}_{suffix}.json"
    path.write_text(json.dumps(report))
    return path


def _forecast(ticker: str, signal: str) -> dict:
    return {"kalshi_ticker": ticker, "momentum_signal": signal, "t3_edge_adjusted": 0.05}


# ---------------------------------------------------------------------------
# load_t3_signals — file-system behaviour
# ---------------------------------------------------------------------------

class TestLoadT3Signals:
    def test_fresh_report_returns_signals(self, tmp_path):
        now = datetime.now(timezone.utc)
        _make_report(tmp_path, now - timedelta(seconds=60), [
            _forecast(TICKER_A, "CONFIRM"),
            _forecast(TICKER_B, "FADE"),
        ])
        result = load_t3_signals(tmp_path, GAME_DATE)
        assert result == {TICKER_A: "CONFIRM", TICKER_B: "FADE"}

    def test_stale_report_returns_empty(self, tmp_path):
        now = datetime.now(timezone.utc)
        _make_report(tmp_path, now - timedelta(seconds=T3_MAX_STALENESS_S + 1), [
            _forecast(TICKER_A, "CONFIRM"),
        ])
        assert load_t3_signals(tmp_path, GAME_DATE) == {}

    def test_exactly_at_staleness_boundary_returns_empty(self, tmp_path):
        now = datetime.now(timezone.utc)
        _make_report(tmp_path, now - timedelta(seconds=T3_MAX_STALENESS_S), [
            _forecast(TICKER_A, "CONFIRM"),
        ])
        # age == boundary → stale (strictly greater check: > not >=)
        assert load_t3_signals(tmp_path, GAME_DATE) == {}

    def test_no_report_returns_empty(self, tmp_path):
        assert load_t3_signals(tmp_path, GAME_DATE) == {}

    def test_malformed_json_returns_empty(self, tmp_path):
        bad = tmp_path / f"t3_{GAME_DATE}_2130.json"
        bad.write_text("{bad json{{")
        assert load_t3_signals(tmp_path, GAME_DATE) == {}

    def test_empty_forecasts_list_returns_empty(self, tmp_path):
        now = datetime.now(timezone.utc)
        _make_report(tmp_path, now - timedelta(seconds=30), [])
        assert load_t3_signals(tmp_path, GAME_DATE) == {}

    def test_selects_most_recent_of_multiple_files(self, tmp_path):
        now = datetime.now(timezone.utc)
        _make_report(tmp_path, now - timedelta(seconds=200), [
            _forecast(TICKER_A, "FADE"),
        ], suffix="2115")
        _make_report(tmp_path, now - timedelta(seconds=60), [
            _forecast(TICKER_A, "CONFIRM"),
        ], suffix="2130")
        result = load_t3_signals(tmp_path, GAME_DATE)
        assert result[TICKER_A] == "CONFIRM"

    def test_missing_run_at_field_returns_signals(self, tmp_path):
        """No run_at → no staleness check → signals returned."""
        report = {
            "session_id": "T3-TEST",
            "game_date": GAME_DATE,
            "forecasts": [_forecast(TICKER_A, "NEUTRAL")],
        }
        (tmp_path / f"t3_{GAME_DATE}_2130.json").write_text(json.dumps(report))
        result = load_t3_signals(tmp_path, GAME_DATE)
        assert result == {TICKER_A: "NEUTRAL"}

    def test_wrong_game_date_not_matched(self, tmp_path):
        now = datetime.now(timezone.utc)
        _make_report(tmp_path, now - timedelta(seconds=30), [
            _forecast(TICKER_A, "CONFIRM"),
        ], suffix="2130")
        assert load_t3_signals(tmp_path, "20260604") == {}


# ---------------------------------------------------------------------------
# Non-contamination guarantee
# ---------------------------------------------------------------------------

class TestNonContamination:
    def test_absent_report_gives_neutral_on_all_tickers(self, tmp_path):
        """Empty dict means every .get(ticker, 'NEUTRAL') returns NEUTRAL."""
        t3_signals = load_t3_signals(tmp_path, GAME_DATE)
        assert t3_signals == {}
        assert t3_signals.get(TICKER_A, "NEUTRAL") == "NEUTRAL"
        assert t3_signals.get(TICKER_B, "NEUTRAL") == "NEUTRAL"

    def test_unknown_ticker_falls_back_to_neutral(self, tmp_path):
        now = datetime.now(timezone.utc)
        _make_report(tmp_path, now - timedelta(seconds=30), [
            _forecast(TICKER_A, "CONFIRM"),
        ])
        t3_signals = load_t3_signals(tmp_path, GAME_DATE)
        assert t3_signals.get(TICKER_B, "NEUTRAL") == "NEUTRAL"


# ---------------------------------------------------------------------------
# Multiplier arithmetic
# ---------------------------------------------------------------------------

class TestMultiplierArithmetic:
    def test_confirm_multiplier_value(self):
        assert T3_CONFIRM_MULTIPLIER == 1.15

    def test_fade_multiplier_value(self):
        assert T3_FADE_MULTIPLIER == 0.75

    def test_confirm_increases_positive_edge(self):
        t1_edge = 0.05
        result = t1_edge * T3_CONFIRM_MULTIPLIER
        assert abs(result - 0.0575) < 1e-9

    def test_fade_decreases_positive_edge(self):
        t1_edge = 0.05
        result = t1_edge * T3_FADE_MULTIPLIER
        assert abs(result - 0.0375) < 1e-9

    def test_neutral_leaves_edge_unchanged(self):
        t1_edge = 0.05
        t3_signal = "NEUTRAL"
        edge = t1_edge * T3_CONFIRM_MULTIPLIER if t3_signal == "CONFIRM" else (
               t1_edge * T3_FADE_MULTIPLIER   if t3_signal == "FADE"    else t1_edge)
        assert edge == t1_edge

    def test_fade_on_negative_edge_reduces_magnitude(self):
        """FADE on a NO-side edge (negative) should shrink |edge|, not flip sign."""
        t1_edge = -0.05   # NO bet signal
        result = t1_edge * T3_FADE_MULTIPLIER
        assert result == pytest.approx(-0.0375)
        assert abs(result) < abs(t1_edge)

    def test_confirm_on_negative_edge_increases_magnitude(self):
        """CONFIRM on NO-side edge should strengthen the NO signal."""
        t1_edge = -0.05
        result = t1_edge * T3_CONFIRM_MULTIPLIER
        assert result == pytest.approx(-0.0575)
        assert abs(result) > abs(t1_edge)

    def test_staleness_constant_matches_cron_interval(self):
        """900s == 15 min — must match PIPE-06 cron schedule."""
        assert T3_MAX_STALENESS_S == 900
