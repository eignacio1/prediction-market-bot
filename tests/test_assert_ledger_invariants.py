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

_SCRIPTS = Path(__file__).parent.parent / "scripts"
_SRC = Path(__file__).parent.parent / "src"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from assert_ledger_invariants import (  # noqa: E402
    assert_A_ticker_date,
    assert_C_entry_price_bounds,
    assert_G_gross_edge_formula,
    assert_H_no_dual_direction_open,
    assert_N_player_token_consistency,
    cross_path_agreement,
    run,
)
from prediction_market_bot.logic_epoch import CURRENT_LOGIC_EPOCH  # noqa: E402


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
