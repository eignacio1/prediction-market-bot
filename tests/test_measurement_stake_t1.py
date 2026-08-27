"""T-497/ADR-0059: T1 game-market flat measurement-stake wrapper tests.

Covers c5_execution/measurement_stake.py in isolation (no live pipeline
wiring — the module is not imported by run_mlb_paper_trade.py, per this
session's scope fence) and TASK 4's dry-run proof: a synthetic T1 game-market
position record passes the new assert_I2/assert_J2 ledger assertions.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from prediction_market_bot.c5_execution.measurement_stake import (  # noqa: E402
    MeasurementStakeRefused,
    T1_GAME_MARKET_TYPES,
    T1_MAX_HAIRCUT_PER_CONTRACT_USD,
    T1_MEASUREMENT_MAX_CONTRACTS,
    T1_MEASUREMENT_STAKE_USD,
    is_t1_game_market,
    t1_measurement_stake_and_stratum,
)
from assert_ledger_invariants import (  # noqa: E402
    assert_I2_t1_measurement_stake,
    assert_J2_t1_contracts_cap,
)


# ── stake formula ────────────────────────────────────────────────────────

def test_mid_price_stake_matches_flat_cap():
    # entry_price=0.40 -> 10*0.40=4.00, min(1.00, 4.00)=1.00 (flat stake binds)
    stake, contracts, stratum = t1_measurement_stake_and_stratum(0.40, 0.02)
    assert stake == T1_MEASUREMENT_STAKE_USD
    assert contracts == pytest.approx(2.5, abs=1e-9)
    assert stratum == "MID"


def test_low_price_stake_bound_by_contract_cap_not_flat_stake():
    # entry_price=0.05 -> 10*0.05=0.50, min(1.00, 0.50)=0.50 (contract cap binds)
    stake, contracts, stratum = t1_measurement_stake_and_stratum(0.05, 0.005)
    assert stake == 0.50
    assert contracts == pytest.approx(T1_MEASUREMENT_MAX_CONTRACTS, abs=1e-9)
    assert stratum == "LOW"


def test_high_price_stratum():
    stake, contracts, stratum = t1_measurement_stake_and_stratum(0.85, 0.03)
    assert stratum == "HIGH"
    assert stake == T1_MEASUREMENT_STAKE_USD


# ── fill-cost bound (the new-vs-ADR-0050 mechanism) ─────────────────────

def test_no_haircut_measurement_refuses():
    with pytest.raises(MeasurementStakeRefused, match="no live haircut measurement"):
        t1_measurement_stake_and_stratum(0.40, None)


def test_haircut_over_bound_refuses():
    with pytest.raises(MeasurementStakeRefused, match="exceeds bound"):
        t1_measurement_stake_and_stratum(0.40, T1_MAX_HAIRCUT_PER_CONTRACT_USD + 0.01)


def test_haircut_at_bound_is_allowed():
    stake, _, _ = t1_measurement_stake_and_stratum(0.40, T1_MAX_HAIRCUT_PER_CONTRACT_USD)
    assert stake == T1_MEASUREMENT_STAKE_USD


def test_run_line_tail_haircut_from_t488_is_refused():
    # T-488/GG-157 measured RUN_LINE max haircut = $0.4050/contract — this is
    # exactly the tail case the bound exists to catch, not wave through.
    with pytest.raises(MeasurementStakeRefused):
        t1_measurement_stake_and_stratum(0.40, 0.4050)


def test_game_winner_median_haircut_from_t488_clears():
    # T-488/GG-157 measured GAME_WINNER median haircut = $0.0350/contract —
    # comfortably under the $0.10 bound.
    stake, _, _ = t1_measurement_stake_and_stratum(0.40, 0.0350)
    assert stake == T1_MEASUREMENT_STAKE_USD


def test_entry_price_out_of_range_refuses():
    with pytest.raises(MeasurementStakeRefused, match="out of"):
        t1_measurement_stake_and_stratum(0.0, 0.01)
    with pytest.raises(MeasurementStakeRefused, match="out of"):
        t1_measurement_stake_and_stratum(1.5, 0.01)


def test_is_t1_game_market_scoping():
    assert is_t1_game_market("mlb_game_total")
    assert is_t1_game_market("mlb_moneyline")
    assert not is_t1_game_market("kxmlbhit")
    assert not is_t1_game_market("mlb_hit_prop")


# ── TASK 4 dry run: synthetic T1 game-market ledger record ─────────────

def _synthetic_t1_game_market_record(entry_price: float, haircut: float) -> dict:
    stake, contracts, stratum = t1_measurement_stake_and_stratum(entry_price, haircut)
    return {
        "position_id": "SYNTH-T1-GAMEMKT-0001",
        "band": "T1",
        "market_type": "mlb_game_total",
        "kalshi_ticker": "KXMLBTOTAL-26AUG26SEAHOU-T8.5",
        "logic_epoch": 12,
        "entry_price_paid": entry_price,
        "size_usd": stake,
        "contracts": contracts,
        "price_stratum": stratum,
        "status": "OPEN",
    }


def test_dry_run_synthetic_record_passes_I2_and_J2():
    rec = _synthetic_t1_game_market_record(entry_price=0.55, haircut=0.04)
    recs = [rec]

    result_i2 = assert_I2_t1_measurement_stake(recs, "T1")
    assert result_i2.no_formula is False
    assert result_i2.n_applicable == 1
    assert result_i2.n_violations == 0

    result_j2 = assert_J2_t1_contracts_cap(recs, "T1")
    assert result_j2.no_formula is False
    assert result_j2.n_applicable == 1
    assert result_j2.n_violations == 0


def test_prop_record_still_reports_no_formula_via_I2_J2():
    # A KXMLBHIT prop under band T1 must NOT be evaluated by the new
    # game-market-scoped assertions — market_type isn't in T1_GAME_MARKET_TYPES.
    prop_rec = {
        "position_id": "SYNTH-T1-PROP-0001",
        "band": "T1",
        "market_type": "kxmlbhit",
        "logic_epoch": 12,
        "entry_price_paid": 0.55,
        "size_usd": 42.0,
        "contracts": 1,
    }
    result_i2 = assert_I2_t1_measurement_stake([prop_rec], "T1")
    assert result_i2.n_applicable == 0
    assert result_i2.n_violations == 0


def test_non_t1_band_reports_no_formula():
    result_i2 = assert_I2_t1_measurement_stake([], "T4M-PROJ")
    assert result_i2.no_formula is True
    result_j2 = assert_J2_t1_contracts_cap([], "T4M-PROJ")
    assert result_j2.no_formula is True


def test_all_nine_adr0058_cells_covered():
    expected = {
        "mlb_moneyline", "mlb_run_line", "mlb_game_total",
        "mlb_team_total", "mlb_partial_game",
        "nfl_moneyline", "nfl_spread", "nfl_game_total", "nfl_team_total",
    }
    assert T1_GAME_MARKET_TYPES == expected
    assert len(T1_GAME_MARKET_TYPES) == 9
