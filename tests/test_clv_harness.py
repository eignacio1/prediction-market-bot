from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "scripts"
_SRC = Path(__file__).parent.parent / "src"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from clv_harness import (  # noqa: E402
    ClvRow,
    InvalidEntryPriceError,
    InvalidSideError,
    NoClosingObservationError,
    PriceObservation,
    TickerNotFoundError,
    TickerSeries,
    backward_placebo_check,
    cohort_aggregate,
    compute_clv_row,
    mean_reversion_decomposition,
)


def _series(ticker: str, mips: list[float], *, start_hour: int = 0, game_id: str = "26JUL021410CINMIL") -> TickerSeries:
    obs = tuple(
        PriceObservation(
            ts=f"2026-07-02T{start_hour + i:02d}:00:00Z",
            mip=m,
            inning=min(9, 1 + i),
            gross_edge=0.06 if i == 0 else None,
            p_t4=0.50,
            vig=0.02,
        )
        for i, m in enumerate(mips)
    )
    return TickerSeries(ticker=ticker, game_id=game_id, observations=obs)


# --------------------------------------------------------------------------- #
# §7 malformed-input contract -- refuse loudly, never impute
# --------------------------------------------------------------------------- #

def test_raises_on_ticker_not_found():
    series_map = {"KXMLBHIT-AAA": _series("KXMLBHIT-AAA", [0.40, 0.45, 0.50])}
    with pytest.raises(TickerNotFoundError):
        compute_clv_row(
            ticker="KXMLBHIT-DOES-NOT-EXIST",
            entry_ts="2026-07-02T00:30:00Z",
            entry_price=0.40,
            side="YES",
            size_or_none=None,
            series_map=series_map,
        )


def test_raises_on_no_closing_observation_after_entry():
    series_map = {"KXMLBHIT-AAA": _series("KXMLBHIT-AAA", [0.40, 0.45, 0.50])}
    with pytest.raises(NoClosingObservationError):
        compute_clv_row(
            ticker="KXMLBHIT-AAA",
            entry_ts="2026-07-02T02:00:00Z",  # entry at the *last* observation's ts
            entry_price=0.50,
            side="YES",
            size_or_none=None,
            series_map=series_map,
        )


def test_raises_on_no_second_to_last_closing_observation():
    series_map = {"KXMLBHIT-AAA": _series("KXMLBHIT-AAA", [0.40, 0.45, 0.50])}
    with pytest.raises(NoClosingObservationError):
        compute_clv_row(
            ticker="KXMLBHIT-AAA",
            entry_ts="2026-07-02T01:00:00Z",  # only one row strictly after
            entry_price=0.45,
            side="YES",
            size_or_none=None,
            series_map=series_map,
            closing_index_from_end=2,
        )


@pytest.mark.parametrize("bad_side", ["yes", "no", "Y", "", None, "MAYBE"])
def test_raises_on_invalid_side(bad_side):
    series_map = {"KXMLBHIT-AAA": _series("KXMLBHIT-AAA", [0.40, 0.45, 0.50])}
    with pytest.raises(InvalidSideError):
        compute_clv_row(
            ticker="KXMLBHIT-AAA",
            entry_ts="2026-07-02T00:00:00Z",
            entry_price=0.40,
            side=bad_side,
            size_or_none=None,
            series_map=series_map,
        )


@pytest.mark.parametrize("bad_price", [None, float("nan"), 0.0, -0.1, 1.0, 1.5])
def test_raises_on_invalid_entry_price(bad_price):
    series_map = {"KXMLBHIT-AAA": _series("KXMLBHIT-AAA", [0.40, 0.45, 0.50])}
    with pytest.raises(InvalidEntryPriceError):
        compute_clv_row(
            ticker="KXMLBHIT-AAA",
            entry_ts="2026-07-02T00:00:00Z",
            entry_price=bad_price,
            side="YES",
            size_or_none=None,
            series_map=series_map,
        )


def test_does_not_swallow_errors_in_a_loop():
    """Cohort-building code must catch these per-row; compute_clv_row itself must not."""
    series_map = {"KXMLBHIT-AAA": _series("KXMLBHIT-AAA", [0.40, 0.45, 0.50])}
    entries = [
        {"ticker": "KXMLBHIT-AAA", "entry_ts": "2026-07-02T00:00:00Z", "entry_price": 0.40, "side": "YES"},
        {"ticker": "KXMLBHIT-MISSING", "entry_ts": "2026-07-02T00:00:00Z", "entry_price": 0.40, "side": "YES"},
    ]
    ok = 0
    raised = 0
    for e in entries:
        try:
            compute_clv_row(
                ticker=e["ticker"],
                entry_ts=e["entry_ts"],
                entry_price=e["entry_price"],
                side=e["side"],
                size_or_none=None,
                series_map=series_map,
            )
            ok += 1
        except TickerNotFoundError:
            raised += 1
    assert ok == 1
    assert raised == 1


# --------------------------------------------------------------------------- #
# Correctness sanity checks
# --------------------------------------------------------------------------- #

def test_clv_sign_convention_yes():
    series_map = {"KXMLBHIT-AAA": _series("KXMLBHIT-AAA", [0.40, 0.45, 0.60])}
    row = compute_clv_row(
        ticker="KXMLBHIT-AAA",
        entry_ts="2026-07-02T00:00:00Z",
        entry_price=0.40,
        side="YES",
        size_or_none=None,
        series_map=series_map,
    )
    # entry_mip=0.40 (at/before entry_ts), closing_mip=0.60 -> CLV = +0.20 for YES
    assert row.entry_mip == pytest.approx(0.40)
    assert row.closing_mip == pytest.approx(0.60)
    assert row.clv == pytest.approx(0.20)


def test_clv_sign_convention_no_is_negated():
    series_map = {"KXMLBHIT-AAA": _series("KXMLBHIT-AAA", [0.40, 0.45, 0.60])}
    row = compute_clv_row(
        ticker="KXMLBHIT-AAA",
        entry_ts="2026-07-02T00:00:00Z",
        entry_price=0.60,
        side="NO",
        size_or_none=None,
        series_map=series_map,
    )
    # same price path, but NO side flips the sign: CLV = -(0.60-0.40) = -0.20
    assert row.clv == pytest.approx(-0.20)


def test_robustness_variant_uses_second_to_last_row():
    series_map = {"KXMLBHIT-AAA": _series("KXMLBHIT-AAA", [0.40, 0.45, 0.50, 0.70])}
    row_primary = compute_clv_row(
        ticker="KXMLBHIT-AAA",
        entry_ts="2026-07-02T00:00:00Z",
        entry_price=0.40,
        side="YES",
        size_or_none=None,
        series_map=series_map,
        closing_index_from_end=1,
    )
    row_r2 = compute_clv_row(
        ticker="KXMLBHIT-AAA",
        entry_ts="2026-07-02T00:00:00Z",
        entry_price=0.40,
        side="YES",
        size_or_none=None,
        series_map=series_map,
        closing_index_from_end=2,
    )
    assert row_primary.closing_mip == pytest.approx(0.70)
    assert row_r2.closing_mip == pytest.approx(0.50)


def test_own_dislocation_none_with_insufficient_history():
    series_map = {"KXMLBHIT-AAA": _series("KXMLBHIT-AAA", [0.40, 0.45])}
    row = compute_clv_row(
        ticker="KXMLBHIT-AAA",
        entry_ts="2026-07-02T00:30:00Z",
        entry_price=0.40,
        side="YES",
        size_or_none=None,
        series_map=series_map,
    )
    assert row.own_dislocation is None  # only 1 prior observation, floor is 3


def test_own_dislocation_computed_with_sufficient_history():
    series_map = {
        "KXMLBHIT-AAA": _series("KXMLBHIT-AAA", [0.30, 0.32, 0.34, 0.36, 0.50], start_hour=0)
    }
    row = compute_clv_row(
        ticker="KXMLBHIT-AAA",
        entry_ts="2026-07-02T03:30:00Z",  # after 4 prior obs (0.30,0.32,0.34,0.36)
        entry_price=0.36,
        side="YES",
        size_or_none=None,
        series_map=series_map,
    )
    assert row.own_dislocation is not None
    trailing_mean = (0.30 + 0.32 + 0.34 + 0.36) / 4
    assert row.own_dislocation == pytest.approx(0.36 - trailing_mean)


def test_cohort_aggregate_empty_is_well_formed():
    agg = cohort_aggregate([])
    assert agg["n"] == 0
    assert agg["by_ticker"]["mean"] is None
    assert agg["by_game"]["mean"] is None


def test_cohort_aggregate_nonempty_has_ci_bracketing_mean():
    rows = []
    for i in range(40):
        series_map = {f"KXMLBHIT-{i}": _series(f"KXMLBHIT-{i}", [0.30, 0.35, 0.50], game_id=f"GAME{i%5}")}
        rows.append(
            compute_clv_row(
                ticker=f"KXMLBHIT-{i}",
                entry_ts=f"2026-07-02T00:00:00Z",
                entry_price=0.30,
                side="YES",
                size_or_none=None,
                series_map=series_map,
            )
        )
    agg = cohort_aggregate(rows)
    assert agg["n"] == 40
    assert agg["by_ticker"]["ci_low"] <= agg["by_ticker"]["mean"] <= agg["by_ticker"]["ci_high"]
    assert agg["by_game"]["ci_low"] <= agg["by_game"]["mean"] <= agg["by_game"]["ci_high"]


def test_backward_placebo_insufficient_n():
    result = backward_placebo_check([])
    assert result["passes"] is None
    assert result["reason"] == "insufficient_n"


def test_mean_reversion_insufficient_n():
    result = mean_reversion_decomposition([])
    assert result["passes"] is None
    assert result["reason"] == "insufficient_n"
