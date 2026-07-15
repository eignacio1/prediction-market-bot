#!/usr/bin/env python3
"""
T-362 — GG-119 confirmation: T1 MLB vig-sign-flip diagnostic (empirical quantification).

WHY THIS EXISTS
---------------
GG-113 (2026-07-14, ADR-0043) found and fixed a sign-flip bug in T4M-PROJ's
NO-direction gating: negating an already vig-inclusive `gross_edge` expression
via plain negation flips the embedded half-spread (vig/2) cost into a credit
for every NO bet. GG-119 was registered the same session as an explicit,
deliberately-deferred suspicion that T1 MLB (`run_mlb_paper_trade.py::
_directional_edge()`) and T2 MLB (`run_t2_mlb_sameday.py`'s local gating
formula) carry the same pattern.

This script performs the direct-code-read confirmation (already done manually
against run_exp017.py's symmetric-vig convention) plus the empirical
quantification against the live T1 resolved ledger, mirroring
`scripts/run_t344_vig_sign_diag.py`'s method exactly (same three-framing
approach, same tercile/Fisher-exact monotonicity check), per Window 1's
explicit instruction.

CODE-READ VERDICT (confirmed prior to running this script)
------------------------------------------------------------
T1 (`run_mlb_paper_trade.py::_directional_edge()`, lines ~295-305):
    directional_gross = gross_edge if direction == "YES" else -gross_edge
    return directional_gross - kalshi_fee
`gross_edge` is always stored YES-frame: `p_calibrated - mid - half_spread`
(half_spread = vig/2, matching run_exp017.py's convention). For YES bets this
is correct (gross_edge - fee = the right YES-frame edge, unchanged). For NO
bets, `-gross_edge` = `-(p - mid - half)` = `(mid - p + half) - `... i.e. the
embedded `-half` term flips to `+half`, converting the half-spread bid-ask
cost into a credit — structurally the identical GG-113 pattern, confirmed by
direct read against run_exp017.py's `yes_ask = mip + half; no_ask = (1-mip)
+ half` (vig always a cost, both directions).
CONFIRMED for T1.

T2 (`run_t2_mlb_sameday.py`, ~lines 414-425):
    gross_edge = p_calibrated - mid - vig      # NOTE: full vig, not half
    net_edge   = gross_edge - kalshi_fee
    direction  = "YES" if net_edge > EDGE_YES else "PASS"
T2 has NO "NO"-direction branch anywhere in the file (confirmed via grep for
`"NO"`/`direction ==`/`EDGE_NO` — none exist). The sign-flip pattern requires
negating a vig-inclusive expression for a NO branch that does not exist here.
RULED OUT for T2 (this specific pattern).

Adjacent, distinct observation (NOT the GG-119 pattern, noted for the record
only): T2 subtracts the FULL vig as its cost term where T1/run_exp017.py use
half-vig (vig/2). This is the same "full-vig-vs-half-vig magnitude question"
ADR-0043 flagged as open for T4M-PROJ (Open items, D-item 2) — this script
does not attempt to resolve it, and it is a conservative-direction error
(costs the book too much edge, not too little), unlike the sign-flip pattern.

METHOD (mirrors run_t344_vig_sign_diag.py)
-------------------------------------------
Load T1's resolved positions (band == "T1") from the live portfolio JSON.
Recompute edge under three framings using ONLY stored fields (gross_edge,
model_p, mid_price_at_entry, vig_at_entry, direction) — never trusting the
position's own stored `fee_net_edge` field, which is independently computed
by paper_trader.py::open_position() and is NOT what gated the bet (see
run_exp017_mlb.py's loader note, GG-077):
  1. LIVE (buggy, as-gated)   — mirrors _directional_edge() exactly.
  2. CORRECTED (symmetric vig, sign-only) — flips the raw signal term for NO
     but keeps half-spread as a cost in both directions, mirroring
     run_exp017.py's convention. Magnitude (half vs full vig) is NOT touched
     here — isolates the sign question only, exactly as T-344 did for T4.

Quantifies: (a) per-bet edge inflation on NO bets (should be exactly
2 x half_spread by construction), (b) how many resolved NO bets only cleared
MIN_EDGE_TO_APPROVE (0.04, risk.py) under the buggy formula and would NOT
have cleared it under the corrected formula, (c) aggregate P&L attributable
to that subgroup, (d) win-rate/monotonicity comparison across framings.

This script is investigation only — no live-formula change. Per Hard Rule 3
and ADR-0039 Tier B precedent, any live-formula change requires a fresh DS
sign-off and a superseding ADR. T1 is the active/primary G6 book, so the bar
for a unilateral fix is higher here than it was for T4M-PROJ (GG-113) — this
script's output is packaged as a decision request, not applied.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

PORTFOLIO_PATH = REPO_ROOT / "logs" / ".vps_portfolio_cache_mlb.json"
OUT_DIR = REPO_ROOT / "exp_output" / "T362-GG119-T1-VIG-DIAG"
MIN_EDGE_TO_APPROVE = 0.04  # risk.py CHECK 3, live value at diagnosis time


def kalshi_fee(mip: float) -> float:
    return 0.07 * mip * (1.0 - mip)


def live_buggy_edge(r: dict) -> float:
    """Mirrors run_mlb_paper_trade.py::_directional_edge() exactly."""
    gross_edge = float(r["gross_edge"])
    mip = float(r["mip"])
    fee = kalshi_fee(mip)
    directional_gross = gross_edge if r["direction"] == "YES" else -gross_edge
    return directional_gross - fee


def corrected_symmetric_vig_edge(r: dict) -> float:
    """Sign-only fix: half-spread stays a cost regardless of direction."""
    gross_edge = float(r["gross_edge"])
    mip = float(r["mip"])
    half = float(r["vig"]) / 2.0
    fee = kalshi_fee(mip)
    if r["direction"] == "YES":
        return gross_edge - fee  # unchanged — YES was never buggy
    return -gross_edge - 2.0 * half - fee


def fisher_pvalue(pos_wins: int, pos_n: int, neg_wins: int, neg_n: int):
    from scipy.stats import fisher_exact

    table = [[pos_wins, pos_n - pos_wins], [neg_wins, neg_n - neg_wins]]
    odds, p = fisher_exact(table)
    return odds, p


def analyze(clean: list[dict], edge_fn, label: str) -> dict:
    pos = [r for r in clean if edge_fn(r) > 0]
    neg = [r for r in clean if edge_fn(r) <= 0]
    wr_pos = sum(1 for r in pos if r["outcome"] == "WIN") / len(pos) if pos else float("nan")
    wr_neg = sum(1 for r in neg if r["outcome"] == "WIN") / len(neg) if neg else float("nan")
    odds = pval = None
    if pos and neg:
        odds, pval = fisher_pvalue(
            sum(1 for r in pos if r["outcome"] == "WIN"), len(pos),
            sum(1 for r in neg if r["outcome"] == "WIN"), len(neg),
        )
    return {
        "label": label, "n_pos": len(pos), "n_neg": len(neg),
        "winrate_pos": wr_pos, "winrate_neg": wr_neg,
        "fisher_odds_ratio": odds, "fisher_pvalue": pval,
    }


def tercile_table(subset: list[dict], edge_fn) -> list[dict]:
    s = sorted(subset, key=edge_fn)
    n = len(s)
    if n < 9:
        return []
    thirds = [s[: n // 3], s[n // 3: 2 * n // 3], s[2 * n // 3:]]
    out = []
    for i, t in enumerate(thirds, 1):
        wr = sum(1 for r in t if r["outcome"] == "WIN") / len(t)
        out.append({
            "tercile": i, "n": len(t),
            "edge_min": round(edge_fn(t[0]), 4), "edge_max": round(edge_fn(t[-1]), 4),
            "win_rate": round(wr, 4),
        })
    return out


def load_t1_closed(path: Path) -> list[dict]:
    with open(path) as fh:
        data = json.load(fh)
    rows = []
    for p in data.get("closed_positions", []):
        if p.get("band") != "T1":
            continue
        if p.get("duplicate_of"):
            continue
        outcome = p.get("outcome", "")
        if outcome not in ("WIN", "LOSS"):
            continue
        try:
            rows.append({
                "position_id": p.get("position_id"),
                "kalshi_ticker": p.get("kalshi_ticker", ""),
                "player_name": p.get("player_name", ""),
                "direction": str(p.get("direction", "YES")),
                "mip": float(p["mid_price_at_entry"]),
                "vig": float(p.get("vig_at_entry", 0.0)),
                "model_p": float(p["model_p"]),
                "gross_edge": float(p["gross_edge"]),
                "outcome": outcome,
                "pnl": float(p.get("pnl", 0.0) or 0.0),
                "size_usd": float(p.get("size_usd", 0.0) or 0.0),
                "logic_epoch": p.get("logic_epoch"),
                "resolved_at": p.get("resolved_at"),
            })
        except (KeyError, TypeError, ValueError):
            continue
    return rows


def main() -> int:
    rows = load_t1_closed(PORTFOLIO_PATH)
    result: dict = {"band": "T1", "n_resolved": len(rows)}

    result["by_direction"] = {
        d: {
            "n": sum(1 for r in rows if r["direction"] == d),
            "win_rate": round(
                sum(1 for r in rows if r["direction"] == d and r["outcome"] == "WIN")
                / max(1, sum(1 for r in rows if r["direction"] == d)), 4,
            ),
            "total_pnl": round(sum(r["pnl"] for r in rows if r["direction"] == d), 4),
        }
        for d in ("YES", "NO")
    }

    framings = [
        ("live_buggy", live_buggy_edge),
        ("corrected_symmetric_vig", corrected_symmetric_vig_edge),
    ]
    result["monotonicity_by_framing"] = {
        label: analyze(rows, fn, label) for label, fn in framings
    }
    result["terciles_no_only_live"] = tercile_table(
        [r for r in rows if r["direction"] == "NO"], live_buggy_edge
    )
    result["terciles_no_only_corrected"] = tercile_table(
        [r for r in rows if r["direction"] == "NO"], corrected_symmetric_vig_edge
    )

    # --- Core quantification: NO bets that only cleared MIN_EDGE_TO_APPROVE
    #     because of the inflation, i.e. live edge >= 0.04 but corrected < 0.04.
    no_rows = [r for r in rows if r["direction"] == "NO"]
    inflation_deltas = []
    falsely_admitted = []
    for r in no_rows:
        live_e = live_buggy_edge(r)
        corr_e = corrected_symmetric_vig_edge(r)
        delta = live_e - corr_e
        inflation_deltas.append(delta)
        if abs(live_e) >= MIN_EDGE_TO_APPROVE and abs(corr_e) < MIN_EDGE_TO_APPROVE:
            falsely_admitted.append({
                "position_id": r["position_id"],
                "kalshi_ticker": r["kalshi_ticker"],
                "player_name": r["player_name"],
                "live_edge": round(live_e, 4),
                "corrected_edge": round(corr_e, 4),
                "half_spread": round(r["vig"] / 2.0, 4),
                "outcome": r["outcome"],
                "pnl": r["pnl"],
            })

    result["no_bet_inflation"] = {
        "n_no_bets": len(no_rows),
        "mean_delta": round(sum(inflation_deltas) / len(inflation_deltas), 6) if inflation_deltas else None,
        "all_deltas_equal_2x_half_spread": all(
            abs(d - r["vig"]) < 1e-9 for d, r in zip(inflation_deltas, no_rows)
        ) if inflation_deltas else None,
    }
    result["falsely_admitted_no_bets"] = {
        "count": len(falsely_admitted),
        "pct_of_no_bets": round(100 * len(falsely_admitted) / len(no_rows), 2) if no_rows else 0,
        "pct_of_all_resolved": round(100 * len(falsely_admitted) / len(rows), 2) if rows else 0,
        "total_pnl": round(sum(x["pnl"] for x in falsely_admitted), 4),
        "wins": sum(1 for x in falsely_admitted if x["outcome"] == "WIN"),
        "losses": sum(1 for x in falsely_admitted if x["outcome"] == "LOSS"),
        "rows": falsely_admitted,
    }
    result["all_resolved_t1_total_pnl"] = round(sum(r["pnl"] for r in rows), 4)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "t1_vig_sign_diag_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))

    print(json.dumps(result, indent=2, default=str))
    print(f"\nWritten: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
