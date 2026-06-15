"""
Sport-Agnostic Bet-Record Contract (T-174 WS4)
==============================================
Component:    Analytics — cross-sport data contract
Phase active: Phase 6 (dark-period transition — NBA close-out → MLB build-out)
Status:       NEW — 2026-06-14 (T-174 WS4)

Purpose
-------
WS2 produced the canonical NBA Finals dataset (`clean_dataset.py`). Its column set
is NBA-flavoured (`kalshi_threshold`, `actual_pts`, `player_name`). This module
lifts that into a **sport-agnostic bet-record contract** — the single schema every
sport's extraction must conform to, so that:

  - the true G6 baseline, EXP-017, and any cross-sport P&L analysis read one shape;
  - adding MLB means a new C1/C2 that EMITS this contract — C4–C8 never change
    (the architectural invariant in CLAUDE.md: only C1/C2 are sport-specific).

This is the data contract WS4 hands to the MLB build. It is validated here against
the real 158-row NBA dataset via `from_nba_row`, so the contract is proven to cover
production data — not asserted to.

Design
------
The contract is field names + a validator, deliberately dependency-free. It does
NOT transform or score anything; contamination is already labeled upstream
(`clean_dataset.contamination_flags`). MLB extraction will populate `sport="MLB"`,
`stat_type` in {"strikeouts","hits","total_bases",...}, and the same contamination
columns.
"""

from __future__ import annotations

from typing import Any

SUPPORTED_SPORTS: frozenset[str] = frozenset({"NBA", "MLB"})
VALID_DIRECTIONS: frozenset[str] = frozenset({"YES", "NO"})
VALID_STATUSES: frozenset[str] = frozenset({"OPEN", "CLOSED", "EXITED"})
CLOSED_STATUSES: frozenset[str] = frozenset({"CLOSED", "EXITED"})

# Canonical, ordered bet-record contract (stable across sports).
BET_RECORD_FIELDS: list[str] = [
    "record_id",          # unique bet id (NBA: position_id)
    "sport",              # "NBA" | "MLB"
    "game_window",        # series/game label (NBA: finals_game e.g. "G3")
    "game_date",          # YYYY-MM-DD
    "subject_name",       # player (NBA: player_name)
    "subject_id",         # player id (NBA: player_id)
    "venue_ticker",       # venue contract id (NBA: kalshi_ticker)
    "stat_type",          # the stat the threshold is on (NBA: "points")
    "threshold",          # numeric line
    "direction",          # YES | NO
    "status",             # OPEN | CLOSED | EXITED
    "size_usd",
    "entry_price",        # mid price at entry (NBA: mid_price_at_entry)
    "vig",
    "model_p",
    "gross_edge",
    "fee_net_edge",
    "raw_edge",           # pre-overlay edge (NBA: t1_edge)
    "overlay_signal",     # momentum/qual overlay (NBA: t3_signal)
    "actual_stat",        # realized stat value (NBA: actual_pts)
    "outcome",            # WIN | LOSS | None
    "realized_pnl",       # ledger-derived; 0.0 for OPEN
    "venue_order_status", # NBA: kalshi_order_status
    "is_clean",
    "contamination",      # "clean" or pipe-joined flags
    "entered_at",
    "resolved_at",
]

# Minimal set any valid record must carry.
REQUIRED_FIELDS: frozenset[str] = frozenset({
    "record_id", "sport", "game_date", "subject_name", "stat_type",
    "threshold", "direction", "status", "size_usd", "realized_pnl",
    "is_clean", "contamination",
})

# NBA clean_dataset column -> canonical contract field.
_NBA_FIELD_MAP: dict[str, str] = {
    "position_id": "record_id",
    "finals_game": "game_window",
    "game_date": "game_date",
    "player_name": "subject_name",
    "player_id": "subject_id",
    "kalshi_ticker": "venue_ticker",
    "kalshi_threshold": "threshold",
    "direction": "direction",
    "status": "status",
    "size_usd": "size_usd",
    "mid_price_at_entry": "entry_price",
    "vig_at_entry": "vig",
    "model_p": "model_p",
    "gross_edge": "gross_edge",
    "fee_net_edge": "fee_net_edge",
    "t1_edge": "raw_edge",
    "t3_signal": "overlay_signal",
    "actual_pts": "actual_stat",
    "outcome": "outcome",
    "realized_pnl": "realized_pnl",
    "kalshi_order_status": "venue_order_status",
    "is_clean": "is_clean",
    "contamination": "contamination",
    "entered_at": "entered_at",
    "resolved_at": "resolved_at",
}


def from_nba_row(row: dict[str, Any]) -> dict[str, Any]:
    """Adapt one `clean_dataset` NBA row into a canonical bet record."""
    rec: dict[str, Any] = {f: None for f in BET_RECORD_FIELDS}
    for nba_field, canon in _NBA_FIELD_MAP.items():
        if nba_field in row:
            rec[canon] = row[nba_field]
    rec["sport"] = "NBA"
    rec["stat_type"] = "points"  # NBA Finals book is points markets (KXNBAPTS)
    return rec


def validate_bet_record(rec: dict[str, Any]) -> list[str]:
    """Return a list of violations (empty = valid contract record)."""
    errs: list[str] = []

    missing = REQUIRED_FIELDS - rec.keys()
    if missing:
        errs.append(f"missing required fields: {sorted(missing)}")
        return errs  # downstream checks need these present

    if rec["sport"] not in SUPPORTED_SPORTS:
        errs.append(f"sport {rec['sport']!r} not in {sorted(SUPPORTED_SPORTS)}")
    if rec["direction"] not in VALID_DIRECTIONS:
        errs.append(f"direction {rec['direction']!r} not in {sorted(VALID_DIRECTIONS)}")
    if rec["status"] not in VALID_STATUSES:
        errs.append(f"status {rec['status']!r} not in {sorted(VALID_STATUSES)}")

    try:
        if float(rec["size_usd"]) < 0:
            errs.append(f"size_usd negative: {rec['size_usd']}")
    except (TypeError, ValueError):
        errs.append(f"size_usd not numeric: {rec['size_usd']!r}")

    try:
        float(rec["threshold"])
    except (TypeError, ValueError):
        errs.append(f"threshold not numeric: {rec['threshold']!r}")

    # OPEN bets carry no realized P&L.
    if rec["status"] == "OPEN":
        try:
            if float(rec["realized_pnl"]) != 0.0:
                errs.append(f"OPEN record has non-zero realized_pnl: {rec['realized_pnl']}")
        except (TypeError, ValueError):
            errs.append(f"realized_pnl not numeric: {rec['realized_pnl']!r}")

    # is_clean / contamination must agree.
    is_clean = rec["is_clean"]
    contam = rec["contamination"]
    clean_str = str(is_clean).lower() in ("true", "1")
    if clean_str and contam != "clean":
        errs.append(f"is_clean=True but contamination={contam!r}")
    if not clean_str and contam == "clean":
        errs.append("is_clean=False but contamination='clean'")

    return errs


def validate_dataset(records: list[dict[str, Any]]) -> list[str]:
    """Validate a list of records; returns flattened violations prefixed by index."""
    out: list[str] = []
    for i, rec in enumerate(records):
        for e in validate_bet_record(rec):
            out.append(f"[{i}] {e}")
    return out
