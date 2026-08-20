"""Tests for scripts/run_power_calc.py — T-323, GG-004.

Covers: the inverse-normal / z_for helper against known critical values,
the analyze_band_power state machine (INSUFFICIENT_DATA / UNDERPOWERED /
NO_POSITIVE_EFFECT / COMPUTED), the n* formula against a hand-computed example, observed cadence
(and its "immature window" flag) against synthetic timestamped fixtures, and
the gap/met bookkeeping.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from run_power_calc import (
    MIN_N,
    z_for,
    _parse_ts,
    observed_cadence_per_week,
    analyze_band_power,
    MATURE_CADENCE_SPAN_DAYS,
    _market_type_for_record,
    _regroup_by_cell,
    _UNREGISTERED_SERIES_COUNTS,
)
from prediction_market_bot.logic_epoch import (
    CURRENT_LOGIC_EPOCH,
    clean_epoch_floor_for_band,
)


def _rec(pnl, resolved_at=None, entered_at=None, game_date=None, logic_epoch=None):
    # GG-113 (ADR-0043) advanced CURRENT_LOGIC_EPOCH 3 -> 4; default to the
    # live constant rather than a hardcoded value so "clean" fixtures here
    # don't go stale on the next epoch bump (this is exactly what broke when
    # the default was a bare literal `3` pre-fix).
    r = {"_pnl": pnl, "logic_epoch": CURRENT_LOGIC_EPOCH if logic_epoch is None else logic_epoch}
    if resolved_at is not None:
        r["resolved_at"] = resolved_at
    if entered_at is not None:
        r["entered_at"] = entered_at
    if game_date is not None:
        r["game_date"] = game_date
    return r


# ── z_for / inverse normal CDF ──────────────────────────────────────────────

class TestZFor:
    def test_alpha_05_one_sided(self):
        assert z_for(0.05) == pytest.approx(1.645, abs=0.001)

    def test_alpha_025_two_sided_half(self):
        assert z_for(0.025) == pytest.approx(1.960, abs=0.001)

    def test_alpha_01(self):
        assert z_for(0.01) == pytest.approx(2.326, abs=0.001)

    def test_median_is_zero(self):
        assert z_for(0.5) == pytest.approx(0.0, abs=1e-9)


# ── timestamp parsing ────────────────────────────────────────────────────────

class TestParseTs:
    def test_iso_with_millis_and_z(self):
        dt = _parse_ts("2026-07-07T06:33:30.683Z")
        assert dt is not None
        assert dt.year == 2026 and dt.month == 7 and dt.day == 7

    def test_date_only(self):
        dt = _parse_ts("2026-07-07")
        assert dt is not None and dt.day == 7

    def test_none_input(self):
        assert _parse_ts(None) is None

    def test_garbage_input(self):
        assert _parse_ts("not-a-date") is None


# ── observed cadence ─────────────────────────────────────────────────────────

class TestObservedCadence:
    def test_exact_one_week_span(self):
        recs = [
            _rec(1.0, resolved_at="2026-07-01T00:00:00Z"),
            _rec(1.0, resolved_at="2026-07-08T00:00:00Z"),
        ]
        cadence, span = observed_cadence_per_week(recs)
        assert span == pytest.approx(7.0, abs=0.01)
        assert cadence == pytest.approx(2 / 1.0, abs=0.01)  # 2 recs / 1 week

    def test_fewer_than_two_timestamps_returns_none(self):
        recs = [_rec(1.0, resolved_at="2026-07-01T00:00:00Z")]
        cadence, span = observed_cadence_per_week(recs)
        assert cadence is None and span is None

    def test_sub_day_span_returns_none_cadence(self):
        recs = [
            _rec(1.0, resolved_at="2026-07-01T00:00:00Z"),
            _rec(1.0, resolved_at="2026-07-01T01:00:00Z"),
        ]
        cadence, span = observed_cadence_per_week(recs)
        assert cadence is None
        assert span is not None and span < 1.0

    def test_falls_back_to_entered_at_then_game_date(self):
        recs = [
            _rec(1.0, entered_at="2026-07-01T00:00:00Z"),
            _rec(1.0, game_date="2026-07-08"),
        ]
        cadence, span = observed_cadence_per_week(recs)
        assert span == pytest.approx(7.0, abs=0.1)


# ── analyze_band_power state machine ────────────────────────────────────────

class TestAnalyzeBandPower:
    def test_insufficient_data_below_two_clean(self):
        r = analyze_band_power("T2", [_rec(1.0)], alpha=0.05, power=0.95)
        assert r["status"] == "INSUFFICIENT_DATA"
        assert r["clean_n"] == 1

    def test_zero_clean_is_insufficient(self):
        r = analyze_band_power("T3", [], alpha=0.05, power=0.95)
        assert r["status"] == "INSUFFICIENT_DATA"
        assert r["clean_n"] == 0

    def test_underpowered_below_min_n_even_with_negative_mean(self):
        # The GG-098 trap this branch exists for: a clean_n=2 cohort with
        # mu<0 must NOT read as a band-level NO_POSITIVE_EFFECT verdict.
        recs = [_rec(-1.0), _rec(-2.0)]
        r = analyze_band_power("T2", recs, alpha=0.05, power=0.95)
        assert r["status"] == "UNDERPOWERED"
        assert r["clean_n"] == 2
        assert r["min_n"] == MIN_N
        assert r["mean_pnl_per_bet"] < 0  # observed stats still reported

    def test_underpowered_below_min_n_even_with_positive_mean(self):
        # Symmetric trap: a tiny-n mu>0 cohort must not emit a computed n*.
        recs = [_rec(p) for p in [1.0, 2.0, 1.5, 0.5, 2.5]]
        r = analyze_band_power("T3", recs, alpha=0.05, power=0.95)
        assert r["status"] == "UNDERPOWERED"
        assert "n_star" not in r

    def test_non_positive_mean_reports_no_positive_effect(self):
        recs = [_rec(-1.0), _rec(1.0), _rec(-1.0), _rec(0.0)] * 10  # n=40, mean = -0.25
        r = analyze_band_power("T1", recs, alpha=0.05, power=0.95)
        assert r["status"] == "NO_POSITIVE_EFFECT"
        assert r["mean_pnl_per_bet"] < 0

    def test_positive_mean_computes_n_star_matching_manual_formula(self):
        pnl = [1.0, 2.0, -1.0, 3.0, 0.5, 1.5, 2.5, -0.5] * 4  # n=32 >= MIN_N
        recs = [_rec(p) for p in pnl]
        r = analyze_band_power("T1", recs, alpha=0.05, power=0.95)
        assert r["status"] == "COMPUTED"

        import statistics
        mu = statistics.mean(pnl)
        sigma = statistics.stdev(pnl)
        z_a = z_for(0.05)
        z_b = z_for(0.05)  # power=0.95 -> beta=0.05
        expected_n_star = math.ceil(((z_a + z_b) * sigma / mu) ** 2)
        assert r["n_star"] == expected_n_star

    def test_gap_and_met_when_clean_n_exceeds_n_star(self):
        # Tight, strongly positive, low-variance sample -> small n*.
        pnl = [1.0] * 50
        pnl[0] = 1.01  # avoid zero-variance edge case
        recs = [_rec(p) for p in pnl]
        r = analyze_band_power("T4M-PROJ", recs, alpha=0.05, power=0.95)
        assert r["status"] == "COMPUTED"
        assert r["gap_to_n_star"] == max(0, r["n_star"] - r["clean_n"])
        assert r["met"] == (r["gap_to_n_star"] == 0)

    def test_raw_n_and_clean_n_both_reported(self):
        # 3 clean, 2 not-clean (below T1's own clean-epoch floor, GG-124
        # per-band remediation -- NOT simply CURRENT_LOGIC_EPOCH - 1, since a
        # global-counter bump that never touched T1's write path must not
        # count as "old" for T1) -> clean_n should exclude the old ones.
        t1_floor = clean_epoch_floor_for_band("T1")
        clean = [_rec(1.0, logic_epoch=CURRENT_LOGIC_EPOCH) for _ in range(3)]
        dirty = [_rec(1.0, logic_epoch=t1_floor - 1) for _ in range(2)]
        all_recs = clean + dirty
        # analyze_band_power itself does not filter — filter_clean happens
        # inside it via import; verify raw_n reflects the full input list
        # regardless of status.
        r = analyze_band_power("T1", all_recs, alpha=0.05, power=0.95)
        assert r["raw_n"] == 5
        assert r["clean_n"] == 3

    def test_cadence_immature_flag_set_below_threshold(self):
        pnl = [1.0, 2.0, 1.5, 0.5, 2.5] * 6  # n=30 >= MIN_N
        recs = [
            _rec(p, resolved_at=f"2026-07-{(i % 10) + 1:02d}T00:00:00Z")
            for i, p in enumerate(pnl)
        ]  # 9-day span, under MATURE_CADENCE_SPAN_DAYS
        r = analyze_band_power("T1", recs, alpha=0.05, power=0.95)
        assert r["status"] == "COMPUTED"
        assert r["cadence_immature"] is True
        assert r["cadence_span_days"] < MATURE_CADENCE_SPAN_DAYS

    def test_cadence_immature_flag_false_when_span_is_long(self):
        pnl = [1.0, 2.0, 1.5, 0.5, 2.5] * 6  # n=30 >= MIN_N
        # spread evenly across 30 days -> mature span
        recs = [
            _rec(p, resolved_at=f"2026-07-{(i % 30) + 1:02d}T00:00:00Z")
            for i, p in enumerate(pnl)
        ]
        r = analyze_band_power("T1", recs, alpha=0.05, power=0.95)
        assert r["status"] == "COMPUTED"
        assert r["cadence_span_days"] is not None
        assert r["cadence_span_days"] >= MATURE_CADENCE_SPAN_DAYS
        assert r["cadence_immature"] is False

    def test_eta_weeks_is_none_when_cadence_unmeasurable(self):
        recs = [_rec(1.0), _rec(2.0), _rec(1.5)] * 10  # no timestamps at all
        r = analyze_band_power("T1", recs, alpha=0.05, power=0.95)
        assert r["status"] == "COMPUTED"
        assert r["cadence_bets_per_week"] is None
        assert r["eta_weeks"] is None


# ── GG-191: unregistered-series records must be counted, not silently dropped ──

def _ticker_rec(pnl, kalshi_ticker):
    r = _rec(pnl)
    r["kalshi_ticker"] = kalshi_ticker
    return r


class TestUnregisteredSeriesCounter:
    def setup_method(self):
        # run_all_cells() clears this at the start of a real run; tests must
        # not leak counts into each other or into that assumption.
        _UNREGISTERED_SERIES_COUNTS.clear()

    def test_registered_series_does_not_increment_counter(self):
        rec = _ticker_rec(1.0, "KXMLBHIT-26JUN241607BALLAA-T1.5")
        mt = _market_type_for_record(rec)
        assert mt is not None
        assert sum(_UNREGISTERED_SERIES_COUNTS.values()) == 0

    def test_unregistered_series_increments_counter_under_series_key(self):
        rec = _ticker_rec(1.0, "KXMLBUNKNOWNSERIES-26AUG011610MIANYM-T8.5")
        mt = _market_type_for_record(rec)
        assert mt is None
        assert _UNREGISTERED_SERIES_COUNTS["KXMLBUNKNOWNSERIES"] == 1

    def test_regroup_by_cell_drops_unregistered_but_counts_it(self):
        recs = [
            _ticker_rec(1.0, "KXMLBHIT-26JUN241607BALLAA-T1.5"),
            _ticker_rec(2.0, "KXMLBUNKNOWNSERIES-26AUG011610MIANYM-T8.5"),
        ]
        by_cell = _regroup_by_cell("T4M-PROJ", recs)
        total_grouped = sum(len(v) for v in by_cell.values())
        assert total_grouped == 1  # only the registered-series record survives
        assert _UNREGISTERED_SERIES_COUNTS["KXMLBUNKNOWNSERIES"] == 1

    def test_counter_does_not_leak_across_regroup_calls_after_clear(self):
        _regroup_by_cell("T4M-PROJ", [
            _ticker_rec(1.0, "KXMLBUNKNOWNSERIES-26AUG011610MIANYM-T8.5"),
        ])
        assert sum(_UNREGISTERED_SERIES_COUNTS.values()) == 1
        _UNREGISTERED_SERIES_COUNTS.clear()  # what run_all_cells() does per-run
        assert sum(_UNREGISTERED_SERIES_COUNTS.values()) == 0
