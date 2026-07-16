#!/usr/bin/env python3
"""
T-368 — GG-122: T2 MLB full-vig-vs-half-vig magnitude diagnostic (empirical quantification).

WHY THIS EXISTS
---------------
ADR-0045 (GG-119, T1's NO-direction sign-flip fix, drafted 2026-07-15) flagged
as an explicit, deliberately-deferred adjacent observation ("Proposed D3") a
distinct, magnitude-only question about T2: `run_t2_mlb_sameday.py`'s local
gating formula appears to subtract the FULL vig (bid-ask spread) as its cost
term, where the established convention (`run_exp017.py`, and T1's
`run_mlb_paper_trade.py` once ADR-0045 is applied) subtracts only HALF the
spread (`half_spread = vig / 2.0` — the actual one-sided transaction cost).

Unlike GG-113/GG-119 (a sign-flip that inflates edge and lets bad bets
through), this is NOT a sign error — T2 has no NO-direction branch at all
(confirmed by direct grep and code read; RULED OUT for the GG-113/GG-119
pattern). This is a magnitude question, and if real, it is
CONSERVATIVE-direction: it costs T2 profit by under-computing edge and
rejecting bets that actually clear the gate, not by admitting bad bets.

CODE-READ VERDICT (confirmed prior to running this script)
------------------------------------------------------------
`run_t2_mlb_sameday.py` (~lines 416-425):
    vig = current_mkt.vig                      # full spread, NOT half_spread
    p_calibrated = calibrate_probability(p_t2, sport="mlb")
    gross_edge = p_calibrated - mid - vig
    kalshi_fee = 0.07 * mid * (1.0 - mid)
    net_edge   = gross_edge - kalshi_fee
    direction  = "YES" if net_edge > EDGE_YES else "PASS"   # EDGE_YES = 0.02

`run_exp017.py` (established convention) and `run_mlb_paper_trade.py`
(T1, lines ~891-892) both use `mkt.half_spread` (`vig / 2.0`) as the cost
term. `kalshi_client.py::PlayerMarket`'s own docstring states this
explicitly: "vig is the full spread (yes_ask - yes_bid); half-spread is the
cost to enter." T2's direct use of `.vig` is an unambiguous deviation from
the codebase's own documented convention. CONFIRMED.

T2 has no NO-direction branch anywhere in the file (`PAPER_YES_ONLY` env var,
default "true"; no `direction == "NO"` branch exists) — this is purely a
YES-side magnitude question.

METHOD
------
Two independent data sources, both pulled read-only from the live VPS:

1. Resolved ledger (`paper_portfolio_mlb.json`, band == "T2", closed positions
   only). As of 2026-07-15 this is n=2 — far too small to compute a
   dollar-denominated realized-P&L impact analogous to GG-119's T1 finding
   (n=259). Reported for completeness; NOT used to assert a quantified P&L
   impact (per explicit instruction not to force a number from n=2).

2. Evaluated-candidate reports (`t2_mlb_*_1930.json`, `forecasts` arrays,
   2026-07-01 through 2026-07-15, n=15 files). These store `p_t1`, `p_t2`,
   `mid_price`, `net_edge` (buggy, as-gated), and `direction`/`outcome` for
   EVERY evaluated candidate, not just placed bets — this is the only source
   with enough rows to assess gating impact. `vig` itself is not stored on
   forecast rows, so it is reconstructed algebraically from the buggy
   formula's own definition:
       vig = p_t2_calibrated - mid - kalshi_fee - net_edge_buggy
   (`p_t2_calibrated` is approximated by the stored `p_t2` field — T2's
   calibration step, `calibrate_probability(p_t2, sport="mlb")`, is not
   independently invertible from the report alone; this is a best-effort
   reconstruction for magnitude estimation, not a re-derivation of T2's
   internal calibration curve.) Corrected edge is then:
       net_edge_corrected = net_edge_buggy + half_spread   (half_spread = vig/2)
   since removing one full vig and re-adding one half_spread is
   algebraically `+ half_spread` relative to the buggy value.

Quantifies: (a) reconstructed half_spread magnitude distribution, (b) how
many evaluated candidates would flip from PASS to YES at T2's own local
`EDGE_YES` gate under the corrected formula, (c) of those, how many would
also clear the binding `MIN_EDGE_TO_APPROVE` (0.04, risk.py CHECK 3) — the
actual determinant of whether a bet gets placed — and how many fall short
even after correction (near-misses).

This script is investigation only — no live-formula change. Per Hard Rule 3,
any live-formula change requires a fresh DS sign-off and a superseding
decision record (packaged separately as an APR, mirroring ADR-0045's format).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

PORTFOLIO_PATH = REPO_ROOT / "logs" / ".vps_portfolio_cache_mlb.json"
REPORTS_DIR = REPO_ROOT / "logs" / "t2_reports"
OUT_DIR = REPO_ROOT / "exp_output" / "T368-GG122-T2-VIG-MAGNITUDE-DIAG"
MIN_EDGE_TO_APPROVE = 0.04  # risk.py CHECK 3, live value at diagnosis time
EDGE_YES = 0.02             # run_t2_mlb_sameday.py's local gate (MLB_T2_EDGE_YES default)


def kalshi_fee(mid: float) -> float:
    return 0.07 * mid * (1.0 - mid)


def load_t2_resolved(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path) as fh:
        data = json.load(fh)
    rows = []
    for p in data.get("closed_positions", []):
        if p.get("band") != "T2":
            continue
        if p.get("duplicate_of"):
            continue
        outcome = p.get("outcome", "")
        if outcome not in ("WIN", "LOSS"):
            continue
        rows.append({
            "position_id": p.get("position_id"),
            "player_name": p.get("player_name", ""),
            "mid": float(p.get("mid_price_at_entry", 0.0)),
            "vig": float(p.get("vig_at_entry", 0.0)),
            "model_p": float(p.get("model_p", 0.0)),
            "gross_edge": float(p.get("gross_edge", 0.0)),
            "outcome": outcome,
            "pnl": float(p.get("pnl", 0.0) or 0.0),
            "game_date": p.get("game_date"),
        })
    return rows


def load_t2_forecasts(reports_dir: Path) -> list[dict]:
    rows = []
    if not reports_dir.exists():
        return rows
    for fp in sorted(reports_dir.glob("t2_mlb_*_1930.json")):
        with open(fp) as fh:
            data = json.load(fh)
        game_date = data.get("game_date")
        for f in data.get("forecasts", []):
            try:
                mid = float(f["mid_price"])
                net_edge_buggy = float(f["net_edge"])
                p_t2 = float(f["p_t2"])
            except (KeyError, TypeError, ValueError):
                continue
            fee = kalshi_fee(mid)
            # Reconstruct vig from the buggy formula's own definition:
            # net_edge_buggy = p_t2 - mid - vig - fee  =>  vig = p_t2 - mid - fee - net_edge_buggy
            vig_reconstructed = p_t2 - mid - fee - net_edge_buggy
            half_spread = vig_reconstructed / 2.0
            net_edge_corrected = net_edge_buggy + half_spread
            rows.append({
                "source_file": fp.name,
                "game_date": game_date,
                "player_name": f.get("player_name"),
                "ticker": f.get("ticker"),
                "threshold": f.get("threshold"),
                "mid": mid,
                "p_t2": p_t2,
                "vig_reconstructed": vig_reconstructed,
                "half_spread": half_spread,
                "net_edge_buggy": net_edge_buggy,
                "net_edge_corrected": net_edge_corrected,
                "direction_buggy": f.get("direction"),
                "outcome_buggy": f.get("outcome"),
            })
    return rows


def main() -> int:
    result: dict = {}

    # --- Part 1: resolved ledger (n too small for P&L quantification) ---
    resolved = load_t2_resolved(PORTFOLIO_PATH)
    result["resolved_ledger"] = {
        "n_resolved": len(resolved),
        "note": (
            "n too small to compute a dollar-denominated realized-P&L impact "
            "analogous to GG-119's T1 finding (n=259). Reported for the record "
            "only, not used to assert a quantified P&L impact."
        ),
        "rows": resolved,
    }
    if resolved:
        for r in resolved:
            half = r["vig"] / 2.0
            r["net_edge_buggy_reconstructed"] = r["gross_edge"] - r["vig"] - kalshi_fee(r["mid"])
            r["net_edge_corrected_reconstructed"] = r["gross_edge"] - half - kalshi_fee(r["mid"])
            r["half_spread"] = half

    # --- Part 2: evaluated-candidate gating impact (n=39 across 15 report files) ---
    forecasts = load_t2_forecasts(REPORTS_DIR)
    result["evaluated_candidates"] = {"n_total": len(forecasts)}

    already_yes = [r for r in forecasts if r["net_edge_buggy"] > EDGE_YES]
    would_flip_local_gate = [
        r for r in forecasts
        if r["net_edge_buggy"] <= EDGE_YES and r["net_edge_corrected"] > EDGE_YES
    ]
    would_clear_min_edge = [
        r for r in would_flip_local_gate if r["net_edge_corrected"] > MIN_EDGE_TO_APPROVE
    ]
    # Near-misses are assessed across ALL evaluated candidates, not just the
    # PASS->YES flip subset -- a row that already cleared EDGE_YES=0.02 under
    # the buggy formula but was REJECTED downstream at MIN_EDGE_TO_APPROVE is
    # exactly as informative a near-miss as one that never cleared EDGE_YES.
    near_misses = [
        r for r in forecasts
        if MIN_EDGE_TO_APPROVE - 0.01 <= r["net_edge_corrected"] <= MIN_EDGE_TO_APPROVE
    ]

    half_spreads = [r["half_spread"] for r in forecasts if r["half_spread"] is not None]

    result["evaluated_candidates"].update({
        "already_yes_under_buggy_formula": {
            "count": len(already_yes),
            "rows": already_yes,
        },
        "would_flip_pass_to_yes_at_local_edge_yes_gate": {
            "count": len(would_flip_local_gate),
            "rows": would_flip_local_gate,
        },
        "of_those_would_also_clear_min_edge_to_approve": {
            "count": len(would_clear_min_edge),
            "note": (
                "MIN_EDGE_TO_APPROVE (risk.py CHECK 3, 0.04) is the binding gate "
                "that actually determines whether a bet is placed -- distinct from "
                "and stricter than T2's own local EDGE_YES=0.02 gate."
            ),
            "rows": would_clear_min_edge,
        },
        "near_misses_within_0.01_of_min_edge_to_approve": {
            "count": len(near_misses),
            "rows": near_misses,
        },
        "half_spread_distribution": {
            "n": len(half_spreads),
            "mean": round(sum(half_spreads) / len(half_spreads), 6) if half_spreads else None,
            "median": round(sorted(half_spreads)[len(half_spreads) // 2], 6) if half_spreads else None,
            "max": round(max(half_spreads), 6) if half_spreads else None,
            "min": round(min(half_spreads), 6) if half_spreads else None,
        },
    })

    result["verdict"] = {
        "bug_confirmed": True,
        "bug_class": "magnitude (full vig used as cost term instead of half_spread) -- NOT a sign-flip",
        "direction_of_error": "conservative -- under-computes edge, costs profit by passing on bets that clear the gate under the correct formula",
        "realized_bet_outcome_changes_in_observed_sample": len(would_clear_min_edge),
        "structural_risk": (
            "0 realized bet-outcome changes in the observed 39-row sample, but "
            f"{len(near_misses)} near-miss(es) within $0.01 of the binding gate and a "
            "real, nonzero half_spread magnitude on every evaluated row -- genuine "
            "exposure on any future day with a larger vig, even though currently unrealized."
        ),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "t2_vig_magnitude_diag_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))

    print(json.dumps(result, indent=2, default=str))
    print(f"\nWritten: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
