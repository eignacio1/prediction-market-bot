"""
Tests — Sport-Agnostic Bet-Record Contract (T-174 WS4)

Proves the contract (a) round-trips the real NBA dataset cleanly and (b) rejects
the failure modes MLB extraction could introduce.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from prediction_market_bot.analytics import bet_record_contract as brc

_NBA_CSV = Path(__file__).resolve().parents[1] / "data" / "nba_finals_clean_dataset.csv"


def _valid_record(**overrides):
    rec = {f: None for f in brc.BET_RECORD_FIELDS}
    rec.update(
        record_id="pos-1",
        sport="MLB",
        game_date="2026-06-14",
        subject_name="Some Pitcher",
        stat_type="strikeouts",
        threshold=6.5,
        direction="YES",
        status="CLOSED",
        size_usd=10.0,
        realized_pnl=4.2,
        is_clean=True,
        contamination="clean",
    )
    rec.update(overrides)
    return rec


# --- contract shape ---------------------------------------------------------

def test_required_fields_are_subset_of_full_contract():
    assert brc.REQUIRED_FIELDS <= set(brc.BET_RECORD_FIELDS)


def test_nba_field_map_targets_are_all_contract_fields():
    for canon in brc._NBA_FIELD_MAP.values():
        assert canon in brc.BET_RECORD_FIELDS


def test_valid_record_passes():
    assert brc.validate_bet_record(_valid_record()) == []


# --- validator rejects failure modes ---------------------------------------

def test_missing_required_field_flagged():
    rec = _valid_record()
    del rec["threshold"]
    errs = brc.validate_bet_record(rec)
    assert any("missing required" in e for e in errs)


def test_unknown_sport_flagged():
    errs = brc.validate_bet_record(_valid_record(sport="NHL"))
    assert any("sport" in e for e in errs)


def test_bad_direction_flagged():
    errs = brc.validate_bet_record(_valid_record(direction="OVER"))
    assert any("direction" in e for e in errs)


def test_bad_status_flagged():
    errs = brc.validate_bet_record(_valid_record(status="PENDING"))
    assert any("status" in e for e in errs)


def test_negative_size_flagged():
    errs = brc.validate_bet_record(_valid_record(size_usd=-1.0))
    assert any("size_usd negative" in e for e in errs)


def test_non_numeric_threshold_flagged():
    errs = brc.validate_bet_record(_valid_record(threshold="high"))
    assert any("threshold not numeric" in e for e in errs)


def test_open_with_nonzero_pnl_flagged():
    errs = brc.validate_bet_record(_valid_record(status="OPEN", realized_pnl=5.0))
    assert any("OPEN record has non-zero realized_pnl" in e for e in errs)


def test_open_with_zero_pnl_ok():
    assert brc.validate_bet_record(_valid_record(status="OPEN", realized_pnl=0.0)) == []


def test_clean_contamination_disagreement_flagged():
    errs = brc.validate_bet_record(_valid_record(is_clean=True, contamination="fee_contaminated"))
    assert any("is_clean=True but contamination" in e for e in errs)
    errs2 = brc.validate_bet_record(_valid_record(is_clean=False, contamination="clean"))
    assert any("is_clean=False but contamination" in e for e in errs2)


# --- adapter + real-data round-trip ----------------------------------------

def test_from_nba_row_sets_sport_and_stat_type():
    rec = brc.from_nba_row({"position_id": "x", "player_name": "p", "kalshi_threshold": 20})
    assert rec["sport"] == "NBA"
    assert rec["stat_type"] == "points"
    assert rec["record_id"] == "x"
    assert rec["threshold"] == 20


@pytest.mark.skipif(not _NBA_CSV.exists(), reason="frozen NBA dataset not present")
def test_real_nba_dataset_conforms_to_contract():
    with _NBA_CSV.open() as fh:
        rows = list(csv.DictReader(fh))
    assert rows, "frozen dataset is empty"

    records = [brc.from_nba_row(r) for r in rows]
    violations = brc.validate_dataset(records)
    assert violations == [], f"real NBA dataset violates contract: {violations[:10]}"
