"""Tests for scripts/assert_ledger_invariants.py — T-432/BLOCK B.

Covers the three non-negotiable design rules (presence guard, band scope,
violation provenance), the core A/G/H assertions, cross-path agreement
joining, SOURCE_UNAVAILABLE graceful degradation, and --strict's exit-code
behavior (0 always in default mode; 1 only with --strict AND violations).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_SCRIPTS = Path(__file__).parent.parent / "scripts"
_SRC = Path(__file__).parent.parent / "src"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from assert_ledger_invariants import (  # noqa: E402
    UNKNOWN_MARKET_TYPE,
    VIG_FORMULA_VERIFIED_MARKET_TYPE,
    assert_A_ticker_date,
    assert_C_entry_price_bounds,
    assert_G_gross_edge_formula,
    assert_H_no_dual_direction_open,
    assert_I2_t1_measurement_stake,
    assert_J2_t1_contracts_cap,
    assert_K_fee_net_edge,
    assert_N_player_token_consistency,
    cross_path_agreement,
    positions_by_cell,
    run,
)
import assert_ledger_invariants as ali_module  # noqa: E402
from prediction_market_bot.c5_execution.market_type_registry import MarketType  # noqa: E402
from prediction_market_bot.logic_epoch import CURRENT_LOGIC_EPOCH  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_unknown_market_type_counter():
    # ali_module._UNKNOWN_MARKET_TYPE_COUNTS is a module-level Counter mutated
    # by positions_by_cell() on every call (T-509) -- without resetting it,
    # counts leak across tests in the same process and a test asserting an
    # exact count could pass or fail depending on test execution order.
    ali_module._UNKNOWN_MARKET_TYPE_COUNTS.clear()
    yield
    ali_module._UNKNOWN_MARKET_TYPE_COUNTS.clear()


def _rec(**kw) -> dict:
    base = {
        "position_id": "p1",
        "kalshi_ticker": "KXMLBHIT-26AUG081230ABCDEF-JSMITH25-1",
        "game_date": "2026-08-08",
        "kalshi_threshold": 1,
        "logic_epoch": CURRENT_LOGIC_EPOCH,
        "status": "CLOSED",
    }
    base.update(kw)
    return base


# ── presence guard ──────────────────────────────────────────────────────

def test_presence_guard_missing_field_is_absent_not_violation():
    recs = [_rec(entry_price_paid=None)]
    r = assert_C_entry_price_bounds(recs, "T4M-PROJ")
    assert r.n_absent == 1
    assert r.n_applicable == 0
    assert r.n_violations == 0


def test_presence_guard_out_of_bounds_value_is_a_violation():
    recs = [_rec(entry_price_paid=1.5)]
    r = assert_C_entry_price_bounds(recs, "T4M-PROJ")
    assert r.n_absent == 0
    assert r.n_applicable == 1
    assert r.n_violations == 1


# ── band scope ───────────────────────────────────────────────────────────

def test_G_band_scope_t1_uses_half_vig():
    recs = [_rec(gross_edge=0.10 - 0.40 - 0.02 / 2, model_p=0.10, mid_price_at_entry=0.40, vig_at_entry=0.02)]
    r = assert_G_gross_edge_formula(recs, "T1")
    assert r.no_formula is False
    assert r.n_violations == 0


def test_G_band_scope_t4_uses_full_vig():
    recs = [_rec(gross_edge=0.10 - 0.40 - 0.02, model_p=0.10, mid_price_at_entry=0.40, vig_at_entry=0.02)]
    r = assert_G_gross_edge_formula(recs, "T4M-PROJ")
    assert r.no_formula is False
    assert r.n_violations == 0


def test_G_wrong_formula_for_band_is_flagged():
    # T4 formula applied to a T1-formula record must show up as a violation.
    recs = [_rec(gross_edge=0.10 - 0.40 - 0.02 / 2, model_p=0.10, mid_price_at_entry=0.40, vig_at_entry=0.02)]
    r = assert_G_gross_edge_formula(recs, "T4M-PROJ")
    assert r.n_violations == 1


def test_G_unscoped_band_reports_no_formula_not_a_violation():
    recs = [_rec(gross_edge=0.05, model_p=0.10, mid_price_at_entry=0.40, vig_at_entry=0.02)]
    r = assert_G_gross_edge_formula(recs, "UNTAGGED")
    assert r.no_formula is True
    assert r.n_applicable == 0
    assert r.n_violations == 0


# ── violation provenance ────────────────────────────────────────────────

def test_A_violation_carries_epoch_and_timestamp_for_provenance():
    bad = _rec(
        kalshi_ticker="KXMLBHIT-26AUG081230ABCDEF-JSMITH25-1",
        game_date="2026-08-09",  # mismatched vs ticker's AUG08
        logic_epoch=12,
        entered_at="2026-08-09T00:00:00Z",
    )
    r = assert_A_ticker_date([bad], "T4M-PROJ")
    assert r.n_violations == 1
    line = r.to_jsonl_line()
    assert line["first_seen_epoch"] == 12
    assert line["last_seen_epoch"] == 12
    assert line["examples"][0]["entered_at"] == "2026-08-09T00:00:00Z"


def test_A_clean_match():
    good = _rec(kalshi_ticker="KXMLBHIT-26AUG081230ABCDEF-JSMITH25-1", game_date="2026-08-08")
    r = assert_A_ticker_date([good], "T4M-PROJ")
    assert r.n_violations == 0
    assert r.n_applicable == 1


def test_A_unparseable_ticker_is_absent_not_violation():
    bad = _rec(kalshi_ticker="NOT-A-VALID-TICKER", game_date="2026-08-08")
    r = assert_A_ticker_date([bad], "T4M-PROJ")
    assert r.n_absent == 1
    assert r.n_violations == 0


# ── H: dual-direction OPEN ──────────────────────────────────────────────

def test_H_flags_same_ticker_open_both_directions():
    recs = [
        _rec(position_id="p1", kalshi_ticker="TICK-1", status="OPEN", direction="YES"),
        _rec(position_id="p2", kalshi_ticker="TICK-1", status="OPEN", direction="NO"),
    ]
    r = assert_H_no_dual_direction_open(recs, "T1")
    assert r.n_applicable == 1
    assert r.n_violations == 1


def test_H_ignores_closed_positions():
    recs = [
        _rec(position_id="p1", kalshi_ticker="TICK-1", status="CLOSED", direction="YES"),
        _rec(position_id="p2", kalshi_ticker="TICK-1", status="CLOSED", direction="NO"),
    ]
    r = assert_H_no_dual_direction_open(recs, "T1")
    assert r.n_applicable == 0
    assert r.n_violations == 0


# ── N: player-token OR-heuristic ────────────────────────────────────────

def test_N_matches_last_word_convention():
    recs = [_rec(kalshi_ticker="KXMLBHIT-26AUG081230ABCDEF-BWITT9-1", player_name="Bobby Witt Jr.")]
    r = assert_N_player_token_consistency(recs, "T4M-PROJ")
    assert r.n_violations == 0


def test_N_matches_full_concat_convention():
    recs = [_rec(kalshi_ticker="KXMLBHIT-26AUG081230ABCDEF-EDELACRUZ22-1", player_name="Elly De La Cruz")]
    r = assert_N_player_token_consistency(recs, "T4M-PROJ")
    assert r.n_violations == 0


def test_N_flags_real_mismatch():
    recs = [_rec(kalshi_ticker="KXMLBHIT-26AUG081230ABCDEF-ZZZUNKNOWN9-1", player_name="Bobby Witt Jr.")]
    r = assert_N_player_token_consistency(recs, "T4M-PROJ")
    assert r.n_violations == 1


def test_N_matches_kalshi_truncated_token():
    # GG-175: Kalshi truncated "N"+"LOPEZ" (NLOPEZ) to "NLOPE" in the real
    # ticker for Nicky Lopez — a genuine truncation, not a bad position.
    recs = [_rec(kalshi_ticker="KXMLBHIT-26AUG081230ABCDEF-TEXNLOPE9-1", player_name="Nicky Lopez")]
    r = assert_N_player_token_consistency(recs, "T4M-PROJ")
    assert r.n_violations == 0


def test_N_still_flags_overly_short_truncation():
    # A token truncated below MIN_TRUNCATED_TOKEN_LEN must still be flagged
    # — the leniency has a floor, not an open-ended prefix match.
    recs = [_rec(kalshi_ticker="KXMLBHIT-26AUG081230ABCDEF-TEXNLO9-1", player_name="Nicky Lopez")]
    r = assert_N_player_token_consistency(recs, "T4M-PROJ")
    assert r.n_violations == 1


# ── cross-path agreement ────────────────────────────────────────────────

def test_cross_path_agreement_reports_measured_disagreement_not_zero():
    recs = [
        _rec(position_id="p1", kalshi_ticker="TICK-1", outcome="WIN", model_p=0.6,
             actual_hits=2, threshold=2, direction="YES", logic_epoch=12),
        _rec(position_id="p2", kalshi_ticker="TICK-2", outcome="WIN", model_p=0.6,
             actual_hits=0, threshold=2, direction="YES", logic_epoch=12),
    ]
    store = {
        "TICK-1": {"ticker": "TICK-1", "resolved": True, "actual_hits": 2},
        "TICK-2": {"ticker": "TICK-2", "resolved": True, "actual_hits": 1},  # disagrees: hits AND derived outcome (1 < threshold 2 -> LOSS, but ledger says WIN)
    }
    rows = cross_path_agreement(recs, "T4M-PROJ", store)
    assert len(rows) == 1
    row = rows[0]
    assert row["n_matched_in_store"] == 2
    assert row["hits_agree"] == 1
    assert row["hits_disagree"] == 1
    assert row["outcome_disagree"] >= 1  # TICK-2's derived outcome flips vs recorded WIN


def test_cross_path_agreement_unmatched_ticker_not_counted_as_disagreement():
    recs = [_rec(position_id="p1", kalshi_ticker="NOT-IN-STORE", outcome="WIN", model_p=0.6,
                  actual_hits=2, threshold=1, direction="YES", logic_epoch=12)]
    rows = cross_path_agreement(recs, "T4M-PROJ", {})
    assert rows[0]["n_unmatched_in_store"] == 1
    assert rows[0]["n_matched_in_store"] == 0


# ── SOURCE_UNAVAILABLE + --strict exit-code behavior ────────────────────

def test_run_handles_missing_sources_gracefully_and_exits_zero(tmp_path):
    missing = tmp_path / "does_not_exist.json"
    missing_jsonl = tmp_path / "does_not_exist.jsonl"
    report = tmp_path / "report.jsonl"
    code = run(missing, missing, missing_jsonl, report, strict=False)
    assert code == 0
    assert report.exists()
    lines = [json.loads(l) for l in report.read_text().splitlines()]
    kinds = {l["type"] for l in lines}
    assert "source_unavailable" in kinds


def test_run_exits_zero_by_default_even_with_violations(tmp_path):
    t1 = tmp_path / "t1.json"
    t4 = tmp_path / "t4.json"
    store = tmp_path / "store.jsonl"
    report = tmp_path / "report.jsonl"
    bad = _rec(kalshi_ticker="KXMLBHIT-26AUG081230ABCDEF-JSMITH25-1", game_date="2026-01-01", band="T1")
    t1.write_text(json.dumps({"open_positions": [], "closed_positions": [bad], "rejected_positions": []}))
    t4.write_text(json.dumps({"open_positions": [], "closed_positions": [], "rejected_positions": []}))
    store.write_text("")
    code = run(t1, t4, store, report, strict=False)
    assert code == 0


def test_run_exits_nonzero_with_strict_and_violations(tmp_path):
    t1 = tmp_path / "t1.json"
    t4 = tmp_path / "t4.json"
    store = tmp_path / "store.jsonl"
    report = tmp_path / "report.jsonl"
    bad = _rec(kalshi_ticker="KXMLBHIT-26AUG081230ABCDEF-JSMITH25-1", game_date="2026-01-01", band="T1")
    t1.write_text(json.dumps({"open_positions": [], "closed_positions": [bad], "rejected_positions": []}))
    t4.write_text(json.dumps({"open_positions": [], "closed_positions": [], "rejected_positions": []}))
    store.write_text("")
    code = run(t1, t4, store, report, strict=True)
    assert code == 1


def test_run_strict_with_no_violations_still_exits_zero(tmp_path):
    t1 = tmp_path / "t1.json"
    t4 = tmp_path / "t4.json"
    store = tmp_path / "store.jsonl"
    report = tmp_path / "report.jsonl"
    good = _rec(kalshi_ticker="KXMLBHIT-26AUG081230ABCDEF-JSMITH25-1", game_date="2026-08-08", band="T1")
    t1.write_text(json.dumps({"open_positions": [], "closed_positions": [good], "rejected_positions": []}))
    t4.write_text(json.dumps({"open_positions": [], "closed_positions": [], "rejected_positions": []}))
    store.write_text("")
    code = run(t1, t4, store, report, strict=True)
    assert code == 0


# ── T-509/ADR-0054(a) item 1: cell-awareness (positions_by_cell, G/K/I2/J2) ─

def test_positions_by_cell_groups_by_market_type_and_band():
    portfolio = {
        "open_positions": [],
        "closed_positions": [
            _rec(position_id="p1", band="T1", market_type=MarketType.MLB_PLAYER_PROP_HITS.value),
            _rec(position_id="p2", band="T1", market_type=MarketType.MLB_MONEYLINE.value),
            _rec(position_id="p3", band="T4M-PROJ", market_type=MarketType.MLB_PLAYER_PROP_HITS.value),
        ],
        "rejected_positions": [],
    }
    by_cell = positions_by_cell(portfolio)
    assert set(by_cell.keys()) == {
        (MarketType.MLB_PLAYER_PROP_HITS.value, "T1"),
        (MarketType.MLB_MONEYLINE.value, "T1"),
        (MarketType.MLB_PLAYER_PROP_HITS.value, "T4M-PROJ"),
    }
    assert len(by_cell[(MarketType.MLB_PLAYER_PROP_HITS.value, "T1")]) == 1
    assert ali_module._UNKNOWN_MARKET_TYPE_COUNTS == {}


def test_positions_by_cell_missing_market_type_grouped_as_unknown_and_counted():
    portfolio = {
        "open_positions": [],
        "closed_positions": [_rec(position_id="p1", band="T1")],  # no market_type key at all
        "rejected_positions": [],
    }
    by_cell = positions_by_cell(portfolio)
    assert (UNKNOWN_MARKET_TYPE, "T1") in by_cell
    assert len(by_cell[(UNKNOWN_MARKET_TYPE, "T1")]) == 1
    assert ali_module._UNKNOWN_MARKET_TYPE_COUNTS[(None, "T1")] == 1


def test_positions_by_cell_unrecognized_market_type_value_grouped_as_unknown_and_counted():
    portfolio = {
        "open_positions": [],
        "closed_positions": [_rec(position_id="p1", band="T4M-PROJ", market_type="not_a_real_market_type")],
        "rejected_positions": [],
    }
    by_cell = positions_by_cell(portfolio)
    assert (UNKNOWN_MARKET_TYPE, "T4M-PROJ") in by_cell
    assert ali_module._UNKNOWN_MARKET_TYPE_COUNTS[("not_a_real_market_type", "T4M-PROJ")] == 1


def test_G_non_verified_market_type_reports_no_formula_even_with_matching_band():
    # Same T1-formula-correct record as test_G_band_scope_t1_uses_half_vig,
    # but tagged with a game-market type instead of the verified props type --
    # G's formula was only verified against props data (ADR-0045/GG-119), so
    # this must be NO_FORMULA, not a silent clean evaluation under a formula
    # that was never checked against game-market data.
    recs = [_rec(gross_edge=0.10 - 0.40 - 0.02 / 2, model_p=0.10, mid_price_at_entry=0.40, vig_at_entry=0.02)]
    r = assert_G_gross_edge_formula(recs, "T1", market_type=MarketType.MLB_MONEYLINE.value)
    assert r.no_formula is True
    assert r.n_applicable == 0
    assert r.n_violations == 0


def test_G_verified_market_type_explicit_still_evaluates():
    recs = [_rec(gross_edge=0.10 - 0.40 - 0.02 / 2, model_p=0.10, mid_price_at_entry=0.40, vig_at_entry=0.02)]
    r = assert_G_gross_edge_formula(recs, "T1", market_type=VIG_FORMULA_VERIFIED_MARKET_TYPE)
    assert r.no_formula is False
    assert r.n_violations == 0


def test_K_non_verified_market_type_reports_no_formula():
    recs = [_rec(band="T4M-PROJ", logic_epoch=12)]
    r = assert_K_fee_net_edge(recs, "T4M-PROJ", market_type=MarketType.MLB_RUN_LINE.value)
    assert r.no_formula is True


def test_I2_non_game_market_type_reports_no_formula():
    # Old behaviour (pre-T-509) silently `continue`d past non-game-market
    # records inside the per-record loop, without ever setting no_formula --
    # a T1 cell entirely composed of props would have reported "0 applicable,
    # clean" rather than "not evaluated". The cell-level gate fixes this.
    recs = [_rec(band="T1", entry_price_paid=0.40, size_usd=25.0)]
    r = assert_I2_t1_measurement_stake(recs, "T1", market_type=MarketType.MLB_PLAYER_PROP_HITS.value)
    assert r.no_formula is True
    assert r.n_applicable == 0


def test_I2_game_market_type_evaluates():
    from prediction_market_bot.c5_execution.measurement_stake import (
        T1_MEASUREMENT_MAX_CONTRACTS,
        T1_MEASUREMENT_STAKE_USD,
    )
    epp = 0.40
    expected = round(min(T1_MEASUREMENT_STAKE_USD, T1_MEASUREMENT_MAX_CONTRACTS * epp), 4)
    recs = [_rec(band="T1", entry_price_paid=epp, size_usd=expected)]
    r = assert_I2_t1_measurement_stake(recs, "T1", market_type=MarketType.MLB_MONEYLINE.value)
    assert r.no_formula is False
    assert r.n_violations == 0


def test_J2_non_game_market_type_reports_no_formula():
    recs = [_rec(band="T1", contracts=1.0)]
    r = assert_J2_t1_contracts_cap(recs, "T1", market_type=MarketType.MLB_PLAYER_PROP_HITS.value)
    assert r.no_formula is True


def test_run_reports_cell_formula_coverage_and_unknown_market_type_summary(tmp_path):
    t1 = tmp_path / "t1.json"
    t4 = tmp_path / "t4.json"
    store = tmp_path / "store.jsonl"
    report = tmp_path / "report.jsonl"
    known = _rec(
        position_id="p1", band="T1", kalshi_ticker="KXMLBHIT-26AUG081230ABCDEF-JSMITH25-1",
        game_date="2026-08-08", market_type=MarketType.MLB_PLAYER_PROP_HITS.value,
    )
    unknown = _rec(
        position_id="p2", band="T1", kalshi_ticker="KXMLBHIT-26AUG081230ABCDEF-JSMITH25-1",
        game_date="2026-08-08",
    )  # no market_type field
    t1.write_text(json.dumps({"open_positions": [], "closed_positions": [known, unknown], "rejected_positions": []}))
    t4.write_text(json.dumps({"open_positions": [], "closed_positions": [], "rejected_positions": []}))
    store.write_text("")
    code = run(t1, t4, store, report, strict=False)
    assert code == 0
    lines = [json.loads(l) for l in report.read_text().splitlines()]
    kinds = {l["type"] for l in lines}
    assert "cell_formula_coverage" in kinds
    assert "unknown_market_type_summary" in kinds
    summary = next(l for l in lines if l["type"] == "run_summary")
    assert summary["total_cells"] >= 2
    assert summary["total_unknown_market_type_records"] == 1
    unknown_summary = next(l for l in lines if l["type"] == "unknown_market_type_summary")
    assert unknown_summary["total_records"] == 1
    assert unknown_summary["groups"][0]["band"] == "T1"


# ── W77.3 / GG-764: torn and corrupt reads are reported, never silent ──────

def test_load_jsonl_torn_line_recorded_and_good_lines_kept(tmp_path, capsys):
    import assert_ledger_invariants as m
    m._CORRUPT_READS.clear()
    f = tmp_path / "store.jsonl"
    f.write_text('{"ticker": "A"}\n{"ticker": "B"\n{"ticker": "C"}\n')
    out = m.load_jsonl(f)
    assert [r["ticker"] for r in out] == ["A", "C"]
    assert len(m._CORRUPT_READS) == 1 and m._CORRUPT_READS[0]["line_no"] == 2
    assert "[CORRUPT_READ]" in capsys.readouterr().err


def test_load_json_corrupt_file_recorded_not_raised(tmp_path):
    import assert_ledger_invariants as m
    m._CORRUPT_READS.clear()
    f = tmp_path / "pf.json"
    f.write_text('{"open_positions": [')
    assert m.load_json(f) is None
    assert m._CORRUPT_READS[0]["kind"] == "file"


def test_validators_state_reset_is_logged(tmp_path, caplog):
    from prediction_market_bot.c1_signal_ingestion import validators as v
    bad = tmp_path / "state.json"
    bad.write_text("{torn")
    with caplog.at_level("ERROR"):
        assert v._load_state(bad) == {}
    assert "CARDINALITY STATE RESET" in caplog.text


def test_L_accepts_cancelled_with_zero_pnl_and_flags_nonzero():
    """GG-691: CANCELLED is a legitimate outcome (pnl == 0); a CANCELLED row with pnl is still a violation."""
    ok = ali_module.assert_L_enums([_rec(outcome="CANCELLED", pnl=0.0)], "T1")
    bad = ali_module.assert_L_enums([_rec(outcome="CANCELLED", pnl=1.5)], "T1")
    unknown = ali_module.assert_L_enums([_rec(outcome="VOID", pnl=0.0)], "T1")
    assert ok.n_violations == 0
    assert bad.n_violations == 1
    assert unknown.n_violations == 1
