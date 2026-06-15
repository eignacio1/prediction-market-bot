"""
Tests: T-174 WS2 — Clean Dataset Extraction (GG-034 dark-period transition)
===========================================================================
Invariants:
  - Every bet (open + closed) becomes exactly one row — nothing is dropped.
  - Contamination is LABELED, not filtered (operator directive): duplicate twins
    (T-169), fee-contaminated bets (ADR-0016), and failed/local-only Kalshi
    orders (GG-014) are flagged via is_clean / contamination columns.
  - Realized P&L is ledger-derived (pnl + exit_pnl), 0.0 for still-open bets.
  - Realized P&L splits clean vs contaminated and reconciles to the total.
  - Finals game windows map from game_date.
  - CSV emits the stable COLUMNS contract and round-trips.
"""

import csv
import json

import pytest

from prediction_market_bot.analytics.clean_dataset import (
    build_dataset,
    contamination_flags,
    extract_bets,
    finals_game,
    summarize,
    to_csv,
    COLUMNS,
    CLEAN_LABEL,
    CONTAM_DUPLICATE,
    CONTAM_FEE,
    CONTAM_KALSHI_FAILED,
    CONTAM_LOCAL_ONLY,
)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def _closed(pid, pnl, *, game_date="2026-06-05", status="CLOSED",
            outcome="WIN", **extra):
    base = {
        "position_id": pid, "status": status, "outcome": outcome,
        "game_date": game_date, "direction": "NO", "size_usd": 50.0,
        "mid_price_at_entry": 0.2, "kalshi_order_status": "resting",
    }
    if status == "EXITED":
        base["exit_pnl"] = pnl
    else:
        base["pnl"] = pnl
    base.update(extra)
    return base


def _open(pid, *, game_date="2026-06-13", **extra):
    base = {
        "position_id": pid, "status": "OPEN", "game_date": game_date,
        "direction": "YES", "size_usd": 25.0, "mid_price_at_entry": 0.45,
        "kalshi_order_status": "resting",
    }
    base.update(extra)
    return base


def _state(closed=None, open_=None):
    return {
        "bankroll_usd": 130.62, "initial_bankroll_usd": 1000.0,
        "total_realized_pnl": -8.46, "current_daily_loss": 0.0,
        "daily_loss_date": "2026-06-14",
        "closed_positions": closed or [], "open_positions": open_ or [],
    }


# ---------------------------------------------------------------------------
# Finals game mapping
# ---------------------------------------------------------------------------

def test_finals_game_mapping():
    assert finals_game("2026-06-05") == "G2"
    assert finals_game("2026-06-08") == "G3"
    assert finals_game("2026-06-13") == "G5"
    assert finals_game("2026-07-01") == "UNMAPPED"
    assert finals_game(None) == "UNMAPPED"


# ---------------------------------------------------------------------------
# Contamination flags
# ---------------------------------------------------------------------------

def test_clean_bet_has_no_flags():
    assert contamination_flags(_closed("A", 10.0)) == []


def test_duplicate_twin_flagged():
    assert contamination_flags(_open("D", duplicate_of="POS-ORIG")) == [CONTAM_DUPLICATE]


def test_fee_contaminated_flagged():
    assert contamination_flags(_closed("F", 5.0, fee_contaminated=True)) == [CONTAM_FEE]


def test_kalshi_failed_flagged():
    assert contamination_flags(
        _closed("K", -5.0, kalshi_order_status="failed: HTTP 503")) == [CONTAM_KALSHI_FAILED]


def test_local_only_flagged():
    assert contamination_flags(
        _closed("L", 1.0, kalshi_order_status="local_only")) == [CONTAM_LOCAL_ONLY]


def test_multiple_flags_sorted():
    pos = _closed("M", -2.0, fee_contaminated=True,
                  kalshi_order_status="failed: HTTP 429", duplicate_of="X")
    assert contamination_flags(pos) == sorted(
        [CONTAM_DUPLICATE, CONTAM_FEE, CONTAM_KALSHI_FAILED])


# ---------------------------------------------------------------------------
# Extraction: nothing dropped, realized pnl derived
# ---------------------------------------------------------------------------

def test_extract_keeps_every_bet():
    state = _state(
        closed=[_closed("A", 10.0), _closed("B", -20.0, status="EXITED", outcome=None)],
        open_=[_open("C"), _open("D", duplicate_of="A")],
    )
    rows = extract_bets(state)
    assert len(rows) == 4  # 2 closed + 2 open, nothing filtered


def test_exit_pnl_counted_for_exited():
    state = _state(closed=[_closed("E", -7.5, status="EXITED", outcome=None)])
    rows = extract_bets(state)
    assert rows[0]["realized_pnl"] == pytest.approx(-7.5)


def test_open_bet_realized_pnl_is_zero():
    state = _state(open_=[_open("O")])
    rows = extract_bets(state)
    assert rows[0]["status"] == "OPEN"
    assert rows[0]["realized_pnl"] == 0.0


def test_contamination_column_labeled_not_dropped():
    state = _state(closed=[
        _closed("clean", 10.0),
        _closed("fee", -5.0, fee_contaminated=True),
    ])
    rows = extract_bets(state)
    by_id = {r["position_id"]: r for r in rows}
    assert by_id["clean"]["is_clean"] is True
    assert by_id["clean"]["contamination"] == CLEAN_LABEL
    assert by_id["fee"]["is_clean"] is False
    assert by_id["fee"]["contamination"] == CONTAM_FEE


# ---------------------------------------------------------------------------
# Summary: P&L split reconciles
# ---------------------------------------------------------------------------

def test_summary_pnl_split_reconciles():
    state = _state(closed=[
        _closed("c1", 30.0),                              # clean
        _closed("c2", -10.0),                             # clean
        _closed("x1", -40.0, fee_contaminated=True),      # contaminated
        _closed("x2", 5.0, kalshi_order_status="failed: HTTP 503"),  # contaminated
    ], open_=[_open("o1")])
    rows = extract_bets(state)
    s = summarize(rows)
    assert s["realized_pnl_clean"] == pytest.approx(20.0)
    assert s["realized_pnl_contaminated"] == pytest.approx(-35.0)
    # Clean + contaminated == total, and open bets contribute nothing.
    assert s["realized_pnl_total"] == pytest.approx(-15.0)
    assert s["realized_pnl_clean"] + s["realized_pnl_contaminated"] == pytest.approx(
        s["realized_pnl_total"])
    assert s["n_open"] == 1
    assert s["n_closed"] == 4
    assert s["contamination_reasons"][CONTAM_FEE] == 1
    assert s["contamination_reasons"][CONTAM_KALSHI_FAILED] == 1


def test_summary_groups_by_finals_game():
    state = _state(closed=[
        _closed("g2", 10.0, game_date="2026-06-05"),
        _closed("g3a", -5.0, game_date="2026-06-08"),
        _closed("g3b", -5.0, game_date="2026-06-08"),
    ])
    s = summarize(extract_bets(state))
    assert s["by_finals_game"]["G2"]["n_closed"] == 1
    assert s["by_finals_game"]["G3"]["n_closed"] == 2
    assert s["by_finals_game"]["G3"]["realized_pnl"] == pytest.approx(-10.0)


# ---------------------------------------------------------------------------
# CSV contract + round-trip
# ---------------------------------------------------------------------------

def test_csv_roundtrip_stable_columns(tmp_path):
    state = _state(closed=[_closed("A", 10.0)], open_=[_open("B", duplicate_of="A")])
    rows = extract_bets(state)
    out = to_csv(rows, tmp_path / "ds.csv")
    with out.open() as fh:
        reader = csv.DictReader(fh)
        assert reader.fieldnames == COLUMNS
        loaded = list(reader)
    assert len(loaded) == 2
    twin = next(r for r in loaded if r["position_id"] == "B")
    assert twin["contamination"] == CONTAM_DUPLICATE
    assert twin["is_clean"] == "False"


def test_build_dataset_from_file(tmp_path):
    state = _state(closed=[_closed("A", -251.21)], open_=[_open("B")])
    p = tmp_path / "book.json"
    p.write_text(json.dumps(state))
    rows, summary = build_dataset(p)
    assert len(rows) == 2
    assert summary["realized_pnl_total"] == pytest.approx(-251.21)
