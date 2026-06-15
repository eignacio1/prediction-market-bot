"""
Clean Dataset Extraction — NBA Paper-Trading Ledger (T-174 WS2, GG-034)
=======================================================================
Component:    Analytics over C5 ledger + C6 audit log
Phase active: Phase 6 (dark-period transition — close the NBA paper era)
Status:       NEW — 2026-06-14 (T-174 WS2)

Purpose
-------
Reconstruct EVERY paper bet placed during the NBA Finals into one auditable,
flat table — the canonical historical record of the NBA T1 paper-trading era.

The driving principle (operator directive, dark-period transition):

    "We don't want easy fixes. Extract quality data — scope and LABEL the
     contamination, do not drop it."

So this tool never deletes a row. Contamination is surfaced as explicit columns
(`is_clean`, `contamination`) so any downstream consumer — the true G6 baseline,
EXP-017, or the MLB data contract (WS4) — can filter to the clean subset *or*
study the contaminated subset, from the same immutable source.

Ground truth
------------
The position ledger (`closed_positions` + `open_positions`) is authoritative for
realized P&L — established by GG-034: the `total_realized_pnl` scalar drifted from
the ledger under cross-process clobbering, but Σ over closed positions
(`pnl` + `exit_pnl`) is corroborated to the cent by the append-only C6 audit log
(−$251.21 across 117 closed Finals bets). Realized P&L here is therefore derived
from the same `_position_pnl` helper the fixed PaperTrader uses — never the scalar.

Contamination taxonomy
----------------------
A bet is flagged (one or more) when:
  - ``duplicate_twin``      — annotated ``duplicate_of`` (T-169 / GG-031): a
                              late-cron duplicate bet; double exposure, must be
                              excluded from per-market n in EV experiments.
  - ``fee_contaminated``    — ``fee_contaminated`` True (ADR-0016): the bet's
                              directional net-of-fee edge was negative; it should
                              not have cleared the gate on a fee-aware basis.
  - ``kalshi_order_failed`` — ``kalshi_order_status`` startswith "failed:"
                              (GG-014): the Kalshi demo order never placed; the
                              paper position is local-only, so its "fill" price
                              was never market-validated.
  - ``order_local_only``    — ``kalshi_order_status`` == "local_only": no order
                              was ever submitted to a venue.

A bet with none of these is ``clean``.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from prediction_market_bot.c5_execution.paper_trader import _position_pnl
from prediction_market_bot.c5_execution import portfolio_schema as ps

# ---------------------------------------------------------------------------
# Finals game window mapping (game_date → label)
# ---------------------------------------------------------------------------
# Verified against the live VPS book and MEMORY_BANK Finals schedule:
#   G1 Jun 3  (no bets in this book — predates the current ledger)
#   G2 Jun 5  (35 closed: 28W/7L, +$75.67)
#   G3 Jun 8  (47 closed: swing −$198.84)
#   G4 Jun 10 (35 closed)
#   G5 Jun 13 (41 open at extraction time)
FINALS_GAME_DATES: dict[str, str] = {
    "2026-06-03": "G1",
    "2026-06-05": "G2",
    "2026-06-08": "G3",
    "2026-06-10": "G4",
    "2026-06-13": "G5",
}

# Contamination flag labels (stable strings — downstream filters key on these).
CONTAM_DUPLICATE = "duplicate_twin"
CONTAM_FEE = "fee_contaminated"
CONTAM_KALSHI_FAILED = "kalshi_order_failed"
CONTAM_LOCAL_ONLY = "order_local_only"

CLEAN_LABEL = "clean"

# Column order for the emitted table (stable contract — WS4 MLB schema inherits it).
COLUMNS: list[str] = [
    "position_id",
    "finals_game",
    "game_date",
    "player_name",
    "player_id",
    "kalshi_ticker",
    "kalshi_threshold",
    "direction",
    "status",
    "size_usd",
    "mid_price_at_entry",
    "vig_at_entry",
    "model_p",
    "gross_edge",
    "fee_net_edge",
    "t1_edge",
    "t3_signal",
    "actual_pts",
    "outcome",
    "realized_pnl",
    "kalshi_order_status",
    "probable_injury_signal",
    "duplicate_of",
    "is_clean",
    "contamination",
    "entered_at",
    "resolved_at",
]


def finals_game(game_date: str | None) -> str:
    """Map a game_date to its Finals game label, or 'UNMAPPED' if outside the series."""
    if not game_date:
        return "UNMAPPED"
    return FINALS_GAME_DATES.get(game_date, "UNMAPPED")


def contamination_flags(pos: dict[str, Any]) -> list[str]:
    """Return the sorted list of contamination flags for one position (empty = clean)."""
    flags: list[str] = []
    if pos.get(ps.P_DUPLICATE_OF):
        flags.append(CONTAM_DUPLICATE)
    if pos.get("fee_contaminated"):
        flags.append(CONTAM_FEE)
    order_status = str(pos.get("kalshi_order_status", ""))
    if order_status.startswith("failed:"):
        flags.append(CONTAM_KALSHI_FAILED)
    if order_status == "local_only":
        flags.append(CONTAM_LOCAL_ONLY)
    return sorted(flags)


def _row(pos: dict[str, Any]) -> dict[str, Any]:
    flags = contamination_flags(pos)
    return {
        "position_id": pos.get(ps.P_POSITION_ID),
        "finals_game": finals_game(pos.get(ps.P_GAME_DATE)),
        "game_date": pos.get(ps.P_GAME_DATE),
        "player_name": pos.get("player_name"),
        "player_id": pos.get("player_id"),
        "kalshi_ticker": pos.get("kalshi_ticker"),
        "kalshi_threshold": pos.get("kalshi_threshold"),
        "direction": pos.get(ps.P_DIRECTION),
        "status": pos.get(ps.P_STATUS),
        "size_usd": round(float(pos.get(ps.P_SIZE_USD, 0.0)), 4),
        "mid_price_at_entry": pos.get(ps.P_MID_PRICE),
        "vig_at_entry": pos.get("vig_at_entry"),
        "model_p": pos.get("model_p"),
        "gross_edge": pos.get("gross_edge"),
        "fee_net_edge": pos.get("fee_net_edge"),
        "t1_edge": pos.get("t1_edge"),
        "t3_signal": pos.get("t3_signal"),
        "actual_pts": pos.get("actual_pts"),
        "outcome": pos.get(ps.P_OUTCOME),
        # Realized P&L: 0.0 for still-open positions (unrealized); for closed
        # positions, the same ledger-derived value the fixed PaperTrader trusts.
        "realized_pnl": round(_position_pnl(pos), 4) if pos.get(ps.P_STATUS) in ps.CLOSED_STATUSES else 0.0,
        "kalshi_order_status": pos.get("kalshi_order_status"),
        "probable_injury_signal": pos.get("probable_injury_signal"),
        "duplicate_of": pos.get(ps.P_DUPLICATE_OF),
        "is_clean": not flags,
        "contamination": CLEAN_LABEL if not flags else "|".join(flags),
        "entered_at": pos.get("entered_at"),
        "resolved_at": pos.get("resolved_at") or pos.get("exited_at"),
    }


def extract_bets(state: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten every bet (open + closed) in a portfolio state into one row list.

    Open positions appear with realized_pnl=0.0 (unrealized) and status OPEN;
    closed positions carry their ledger-derived realized P&L. No row is dropped —
    contamination is labeled, never filtered (operator directive).
    """
    rows: list[dict[str, Any]] = []
    for pos in state.get(ps.F_CLOSED_POSITIONS, []):
        rows.append(_row(pos))
    for pos in state.get(ps.F_OPEN_POSITIONS, []):
        rows.append(_row(pos))
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate the row table: counts and realized P&L split by clean/contaminated
    and by Finals game. Realized P&L sums only closed (status CLOSED/EXITED) rows."""
    closed = [r for r in rows if r["status"] in ps.CLOSED_STATUSES]
    clean_closed = [r for r in closed if r["is_clean"]]
    contam_closed = [r for r in closed if not r["is_clean"]]

    def _pnl(rs: list[dict[str, Any]]) -> float:
        return round(sum(r["realized_pnl"] for r in rs), 4)

    # Per-Finals-game breakdown.
    by_game: dict[str, dict[str, Any]] = {}
    for r in rows:
        g = r["finals_game"]
        b = by_game.setdefault(g, {"n_total": 0, "n_closed": 0, "realized_pnl": 0.0,
                                    "n_clean": 0, "n_contaminated": 0})
        b["n_total"] += 1
        if r["status"] in ps.CLOSED_STATUSES:
            b["n_closed"] += 1
            b["realized_pnl"] = round(b["realized_pnl"] + r["realized_pnl"], 4)
        if r["is_clean"]:
            b["n_clean"] += 1
        else:
            b["n_contaminated"] += 1

    # Contamination reason tally (a bet can carry multiple flags).
    reason_counts: dict[str, int] = {}
    for r in rows:
        if r["is_clean"]:
            continue
        for flag in r["contamination"].split("|"):
            reason_counts[flag] = reason_counts.get(flag, 0) + 1

    return {
        "n_bets_total": len(rows),
        "n_open": sum(1 for r in rows if r["status"] == ps.STATUS_OPEN),
        "n_closed": len(closed),
        "n_clean": sum(1 for r in rows if r["is_clean"]),
        "n_contaminated": sum(1 for r in rows if not r["is_clean"]),
        "realized_pnl_total": _pnl(closed),
        "realized_pnl_clean": _pnl(clean_closed),
        "realized_pnl_contaminated": _pnl(contam_closed),
        "contamination_reasons": dict(sorted(reason_counts.items())),
        "by_finals_game": dict(sorted(by_game.items())),
    }


def to_csv(rows: list[dict[str, Any]], path: Path) -> Path:
    """Write rows to CSV with the stable COLUMNS contract. Returns the path."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return path


def build_dataset(portfolio_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load a portfolio JSON, extract the bet table, and summarize it.

    Returns (rows, summary). Does not write anything — the CLI wrapper decides
    where the CSV lands. Pure read of the ledger.
    """
    state = json.loads(Path(portfolio_path).read_text())
    rows = extract_bets(state)
    return rows, summarize(rows)
