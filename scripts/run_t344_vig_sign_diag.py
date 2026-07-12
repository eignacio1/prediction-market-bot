#!/usr/bin/env python3
"""
T-344 — GG-105 decomposition: vig-sign-flip diagnostic + candidate-mechanism test.

WHY THIS EXISTS
---------------
GG-105 (T-322/T-324/T-329/T-332/T-333) established a robust, tercile-monotonic
ANTI-PREDICTIVE relationship between T4M-PROJ's computed edge and realized win
rate on clean_n data, and ruled out sizing artifact (T-329), game-state
concentration (T-332), default-fill masking (H3, T-333), and the offline
analysis tool's vig omission as a *tooling* discrepancy (H5, T-333 — the live
formula "already correctly includes vig", so the pattern was declared to
persist "under the corrected formula too").

T-333's H5 built a "live-parity" formula that deliberately mirrors
`run_t4_mlb_live.py`'s actual gross_edge -> directional_gross_edge flip logic
exactly — including flipping vig's sign along with the rest of gross_edge
when direction is NO. This diagnostic asks a narrower, previously-untested
question: is that live-code behavior itself economically correct, independent
of whether the offline tool matches it?

The codebase's own pre-existing, documented convention for vig (see
run_exp017.py:41 "kalshi_vig: full spread (ask - bid)" and its
`half_vig = vig / 2.0`; `price_paid = mip + half_vig` for YES,
`price_paid = (1-mip) + half_vig` for NO) treats vig as a symmetric
COST that applies regardless of direction — you always cross the spread
away from the mid, whichever side you trade. `run_t4_mlb_live.py:952-1032`
instead computes `gross_edge = p_t4 - mip - vig` (vig baked in as a YES-frame
cost) and then negates the *entire* expression for NO-direction bets
(`directional_gross_edge = -gross_edge`), which algebraically converts vig
from a cost into a credit for every NO-direction bet. This is a candidate
fee/edge-frame artifact (mechanism (b) in T-344's scope) distinct from
GG-077 (the already-fixed fee_net_edge storage-layer sign bug) and distinct
from T-333's H5 (a tooling-parity question, not an economic-correctness one).

METHOD
------
Load the current clean_n T4M-PROJ resolved ledger. For each position, compute
edge under three framings:
  1. LIVE (buggy, as-gated)   — mirrors run_t4_mlb_live.py exactly (vig sign
     flips with direction). Trivially ~100% positive by construction (every
     resolved position cleared this exact gate) — included only to make the
     circularity explicit, not as a real test.
  2. ANALYSIS (current tool)  — e17.compute_fee_net_edge(): omits vig
     entirely for both directions (T-333's H5 finding).
  3. CORRECTED (symmetric vig) — mirrors run_exp017.py's own established
     half-spread convention: vig is always a cost, never a credit, regardless
     of direction. (Uses full vig, not half, to isolate the sign question
     from the magnitude question — see memo for the follow-on half-vig note.)

Re-run edge_monotonicity()-equivalent (Fisher exact, tercile win-rate table)
under each framing. If the CORRECTED framing resolves or weakens the
anti-predictive pattern, mechanism (b) is implicated as (partial) cause. If
it persists or strengthens under CORRECTED, (b) is ruled out as sufficient
explanation and the sign-flip bug is escalated as its own, separate,
governance gap (real, but not the driver of GG-105).

Additionally splits by direction (YES-only / NO-only) to distinguish a pure
compositional artifact (YES/NO base-rate mix shifting across terciles) from
a genuine within-direction inversion.

This script is investigation only — no live-formula change. Per Hard Rule 3
and ADR-0039 Tier B precedent, any live-formula change requires a fresh DS
sign-off and a superseding ADR.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_exp017_mlb as e17  # noqa: E402
from prediction_market_bot.logic_epoch import CURRENT_LOGIC_EPOCH  # noqa: E402

LEDGER_PATH = REPO_ROOT / "logs" / "t4_mlb_resolved_ledger.jsonl"
OUT_DIR = REPO_ROOT / "exp_output" / "T344-VIG-SIGN-DIAG"


def kalshi_fee(mip: float) -> float:
    return 0.07 * mip * (1.0 - mip)


def live_buggy_edge(r: dict) -> float:
    """Mirrors run_t4_mlb_live.py:952-1037 exactly (vig sign flips w/ direction)."""
    mip, mp, vig = float(r["mip"]), float(r["model_p"]), float(r["vig"])
    fee = kalshi_fee(mip)
    gross = mp - mip - vig
    directional_gross = gross if gross > 0 else -gross
    return directional_gross - fee


def analysis_no_vig_edge(r: dict) -> float:
    """e17.compute_fee_net_edge(): omits vig entirely (T-333's H5 finding)."""
    return e17.compute_fee_net_edge(r["direction"], float(r["model_p"]), float(r["mip"]))


def corrected_symmetric_vig_edge(r: dict) -> float:
    """vig always a cost, mirroring run_exp017.py's half-spread convention (sign only)."""
    mip, mp, vig = float(r["mip"]), float(r["model_p"]), float(r["vig"])
    fee = kalshi_fee(mip)
    if r["direction"] == "YES":
        return (mp - mip - vig) - fee
    return (mip - mp - vig) - fee


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
    thirds = [s[: n // 3], s[n // 3 : 2 * n // 3], s[2 * n // 3 :]]
    out = []
    for i, t in enumerate(thirds, 1):
        wr = sum(1 for r in t if r["outcome"] == "WIN") / len(t)
        out.append({
            "tercile": i, "n": len(t),
            "edge_min": round(edge_fn(t[0]), 4), "edge_max": round(edge_fn(t[-1]), 4),
            "win_rate": round(wr, 4),
        })
    return out


def main() -> int:
    rows = [json.loads(l) for l in LEDGER_PATH.open()]
    clean = [r for r in rows if r.get("logic_epoch") == CURRENT_LOGIC_EPOCH]

    result: dict = {"clean_n": len(clean), "raw_n": len(rows), "logic_epoch": CURRENT_LOGIC_EPOCH}

    result["by_direction_unconditional"] = {
        d: {
            "n": sum(1 for r in clean if r["direction"] == d),
            "win_rate": round(
                sum(1 for r in clean if r["direction"] == d and r["outcome"] == "WIN")
                / max(1, sum(1 for r in clean if r["direction"] == d)),
                4,
            ),
        }
        for d in ("YES", "NO")
    }

    framings = [
        ("live_buggy", live_buggy_edge),
        ("analysis_no_vig", analysis_no_vig_edge),
        ("corrected_symmetric_vig", corrected_symmetric_vig_edge),
    ]
    result["monotonicity_by_framing"] = {
        label: analyze(clean, fn, label) for label, fn in framings
    }
    result["terciles_all_corrected"] = tercile_table(clean, corrected_symmetric_vig_edge)
    result["terciles_yes_only_corrected"] = tercile_table(
        [r for r in clean if r["direction"] == "YES"], corrected_symmetric_vig_edge
    )
    result["terciles_no_only_corrected"] = tercile_table(
        [r for r in clean if r["direction"] == "NO"], corrected_symmetric_vig_edge
    )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / "vig_sign_diag_results.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))

    print(json.dumps(result, indent=2, default=str))
    print(f"\nWritten: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
