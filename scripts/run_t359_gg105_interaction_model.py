#!/usr/bin/env python3
"""
T-359 — GG-105 escalation: formal H1 x H4 interaction-model test.

WHY THIS EXISTS
---------------
T-333 (scoping) and T-344 (decomposition) converged on model miscalibration /
overconfidence as GG-105's leading mechanism, built on four pieces of
convergent evidence: within-NO-direction tercile decay staying >50% win rate
at every tercile (not a sign flip), calibration slope b=0.600 excluding 1.0,
T1's calibrated p_t1 loaded but discarded (H2), and two untested candidate
noise sources flagged but never jointly tested — H1 (ba_l10, a noisy
~10-game/~35-40-AB rolling batting average, used as a fixed unregressed
per-AB Bernoulli parameter) and H4 (ab_remaining estimator drift under the
near-universal batting_slot=0 fallback, 654/666 = 98.2% of this cohort).
T-344's own "Recommended next steps" explicitly named this as outstanding:
"A formal interaction model testing H1xH4 jointly (T-333 flagged this as not
yet built)." This script is that test.

SEQUENCING
----------
Per explicit operator instruction, this does not run until Window 1's GG-113
(vig-sign-flip) fix is deployed -- verified independently this session (VPS
HEAD == 858db3a, t4-mlb active, GOVERNANCE_GAP_LOG.md GG-113 Status ==
RESOLVED) before this script was written.

DATA -- WHY EPOCH 3, NOT CURRENT_LOGIC_EPOCH
---------------------------------------------
GG-113's fix bumped CURRENT_LOGIC_EPOCH 3->4 and, as an accepted deliberate
cost of that fix (DS sign-off), reset T4M-PROJ's clean_n to 0 going forward
(confirmed live this session: epoch-4 raw_n=0 in the resolved ledger, minutes
post-deploy). Naively reusing run_band_monitor.filter_clean() (which filters
on CURRENT_LOGIC_EPOCH) would therefore silently return an empty cohort --
exactly the failure class GG-113's own close-out flagged for
test_backfill_logic_epoch.py / test_power_calc.py. This script instead
explicitly filters logic_epoch == 3 (frozen, complete, n=666 as of this
session -- natural growth from T-344's n=412, same epoch, not a re-derivation
of the epoch boundary). This is valid: ba_l10 / ab_remaining / h_so_far /
threshold are raw upstream inputs, wholly unaffected by GG-113 (a gating/edge
sign bug downstream of these inputs). Every p_t4 in this script is
independently recomputed from those raw inputs via the live formula
(p_hits_gte_threshold), never the ledger's stored model_p/edge -- continuing
this project's standing GG-077/GG-100 discipline of never trusting a stored
edge field. Edge is then computed under T-344's already-validated CORRECTED
(symmetric-vig) framing, not the live-buggy or vig-omitted framings, since
CORRECTED is the economically-correct baseline this test should be
attenuating away from.

METHOD
------
1. Join epoch-3 clean_n T4M-PROJ resolved positions to t4_mlb_cycle_log.jsonl
   via the T-332-established forecast_id -> cycle_id join (100% join rate
   here too: 666/666).
2. H1 (ba_l10 shrinkage): empirical-Bayes shrinkage of ba_l10 toward the
   cohort's own observed mean ba_l10 (an internal, data-derived prior --
   consistent with this project's standing rule against citing unsourced
   external constants for architectural claims; no external "league average"
   figure is invoked). Pseudo-count k in {0, 20, 40, 80, 160}, k=0 = exact
   live-formula reproduction (sanity-checked against stored model_p).
   AB_WINDOW=37 (midpoint of T-333/T-344's documented "~35-40 AB" rolling
   window -- exact per-player windowed AB counts are not captured anywhere
   in this pipeline's schema, so this is a stated assumption, not a fitted
   value).
3. H4 (ab_remaining estimator drift): rather than imputing unknown
   batting_slot (would require a fresh T2 slot pull, deferred per T-333
   Sec 2.6), segment the joined cohort by whether the live ab_remaining was
   already slot-aware-accurate (batting_slot != 0, n=12 here) vs
   flat-default-derived (batting_slot == 0, n=654) and compare pattern
   strength between segments -- a natural-experiment test using data already
   in hand, not an imputation.
4. H1xH4 interaction: re-run the full H1 shrinkage sweep restricted to the
   slot_fallback-only subset (n=654, still comfortably above MIN_N), so H1's
   effect is measured with H4's known confound held structurally constant
   (only fallback-path rows), then compared against the full-cohort sweep.
5. All monotonicity verdicts computed via e17.edge_monotonicity() (audited,
   unmodified) through bm.to_mlb_positions() -- never a reimplemented Fisher
   test, per GG-100 discipline.

VERDICT CRITERION
------------------
If increasing shrinkage strength (k) monotonically attenuates the Fisher
significance / tercile spread of the CORRECTED-vig anti-predictive pattern,
that is direct, testable support for H1 as a real contributing mechanism
(and for a shrinkage-based remediation). If the slot_fallback segment shows a
markedly stronger inversion than the slot_known segment, that supports H4.
If neither attenuates the pattern at any tested setting, that weighs against
this session's leading hypothesis and the remediation proposal must say so
plainly rather than force a conclusion the data doesn't support.

Run:
  python3 scripts/run_t359_gg105_interaction_model.py
  python3 scripts/run_t359_gg105_interaction_model.py --cycle-log logs/.vps_t4_mlb_cycle_log_cache.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_band_monitor as bm          # noqa: E402  load_t4_ledger, to_mlb_positions
import run_exp017_mlb as e17           # noqa: E402  edge_monotonicity, MIN_N, E_* (audited)
from prediction_market_bot.run_t4_mlb_live import (  # noqa: E402  live formula, imported not copied
    p_hits_gte_threshold,
)
from run_t332_gamestate_diag import (  # noqa: E402  T-332's audited join, reused not reimplemented
    load_cycle_index,
    cycle_id_from_forecast_id,
)

DEFAULT_T4_LEDGER = REPO_ROOT / "logs" / "t4_mlb_resolved_ledger.jsonl"
DEFAULT_CYCLE_LOG = REPO_ROOT / "logs" / ".vps_t4_mlb_cycle_log_cache.jsonl"
OUT_DIR = REPO_ROOT / "exp_output" / "T359-GG105-INTERACTION-MODEL"

FROZEN_EPOCH = 3          # see module docstring: NOT CURRENT_LOGIC_EPOCH (now 4, clean_n=0)
AB_WINDOW = 37             # midpoint of documented "~35-40 AB" ba_l10 rolling window
SHRINKAGE_K = [0, 20, 40, 80, 160]


def kalshi_fee(mip: float) -> float:
    return 0.07 * mip * (1.0 - mip)


def corrected_symmetric_vig_edge(direction: str, model_p: float, mip: float, vig: float) -> float:
    """T-344's validated CORRECTED framing: vig always a cost, never a credit."""
    fee = kalshi_fee(mip)
    if direction == "YES":
        return (model_p - mip - vig) - fee
    return (mip - model_p - vig) - fee


def load_epoch3_clean(path: Path) -> list[dict]:
    recs = bm.load_t4_ledger(path)
    return [r for r in recs if r.get("logic_epoch") == FROZEN_EPOCH]


def join(recs: list[dict], cycle_idx: dict) -> tuple[list[dict], int]:
    joined, misses = [], 0
    for r in recs:
        cid = cycle_id_from_forecast_id(str(r.get("forecast_id", "")))
        gs = cycle_idx.get((cid, r.get("kalshi_ticker")))
        if gs is None:
            misses += 1
            continue
        r2 = dict(r)
        for f in ("ba_l10", "h_so_far", "ab_so_far", "ab_remaining", "inning", "batting_slot"):
            r2[f"_gs_{f}"] = gs.get(f)
        joined.append(r2)
    return joined, misses


def shrink(ba_l10: float, prior: float, k: int) -> float:
    if k == 0:
        return ba_l10
    return (AB_WINDOW * ba_l10 + k * prior) / (AB_WINDOW + k)


def recompute_positions(joined: list[dict], k: int, prior: float, subset: list[dict] | None = None) -> list:
    """Recompute p_t4 with ba_l10 shrunk at pseudo-count k, rebuild MLBPosition list."""
    rows = subset if subset is not None else joined
    out = []
    for r in rows:
        h_so_far = int(r["_gs_h_so_far"] or 0)
        ab_remaining = int(r["_gs_ab_remaining"] or 0)
        ba_raw = float(r["_gs_ba_l10"] if r["_gs_ba_l10"] is not None else 0.25)
        ba_adj = shrink(ba_raw, prior, k)
        threshold = int(r.get("_thr", 0) or 0)
        p_t4_prime = p_hits_gte_threshold(h_so_far, threshold, ba_adj, ab_remaining)
        fne = corrected_symmetric_vig_edge(r["_dir"], p_t4_prime, r["_mip"], float(r.get("vig", 0.0) or 0.0))
        r2 = dict(r)
        r2["_model_p"] = p_t4_prime
        r2["_fne"] = fne
        out.append(r2)
    return bm.to_mlb_positions(out)


def repro_sanity_check(joined: list[dict]) -> dict:
    """k=0 should exactly reproduce the live formula's stored model_p (join fidelity check)."""
    diffs = []
    for r in joined:
        h_so_far = int(r["_gs_h_so_far"] or 0)
        ab_remaining = int(r["_gs_ab_remaining"] or 0)
        ba_raw = float(r["_gs_ba_l10"] if r["_gs_ba_l10"] is not None else 0.25)
        threshold = int(r.get("_thr", 0) or 0)
        repro = p_hits_gte_threshold(h_so_far, threshold, ba_raw, ab_remaining)
        diffs.append(abs(repro - r["_model_p"]))
    n = len(diffs)
    return {
        "n": n,
        "max_abs_diff": max(diffs) if diffs else None,
        "mean_abs_diff": (sum(diffs) / n) if n else None,
        "exact_matches": sum(1 for d in diffs if d < 1e-9),
    }


def verdict_row(positions, alpha: float = 0.10) -> dict:
    if len(positions) < e17.MIN_N:
        return {"n": len(positions), "verdict": "UNDERPOWERED",
                "reason": f"n={len(positions)} < MIN_N={e17.MIN_N} (GG-098)"}
    mono = e17.edge_monotonicity(positions, alpha=alpha)
    return mono


def build_report(t4_ledger: Path, cycle_log: Path) -> dict:
    clean = load_epoch3_clean(t4_ledger)
    cycle_idx = load_cycle_index(cycle_log)
    joined, misses = join(clean, cycle_idx)

    prior = sum(float(r["_gs_ba_l10"] or 0.25) for r in joined) / len(joined)

    sanity = repro_sanity_check(joined)

    slot_known = [r for r in joined if (r["_gs_batting_slot"] or 0) != 0]
    slot_fallback = [r for r in joined if (r["_gs_batting_slot"] or 0) == 0]

    h1_sweep_all = {
        k: verdict_row(recompute_positions(joined, k, prior)) for k in SHRINKAGE_K
    }
    h1_sweep_fallback_only = {
        k: verdict_row(recompute_positions(joined, k, prior, subset=slot_fallback)) for k in SHRINKAGE_K
    }
    h4_segment = {
        "slot_known": verdict_row(recompute_positions(joined, 0, prior, subset=slot_known)),
        "slot_fallback": verdict_row(recompute_positions(joined, 0, prior, subset=slot_fallback)),
    }

    return {
        "frozen_epoch": FROZEN_EPOCH,
        "clean_n_epoch3": len(clean),
        "n_joined": len(joined),
        "n_join_misses": misses,
        "ba_l10_cohort_mean_prior": round(prior, 4),
        "ab_window_assumption": AB_WINDOW,
        "repro_sanity_check_k0_vs_stored_model_p": sanity,
        "n_slot_known": len(slot_known),
        "n_slot_fallback": len(slot_fallback),
        "H1_shrinkage_sweep_full_cohort": h1_sweep_all,
        "H1xH4_shrinkage_sweep_fallback_only": h1_sweep_fallback_only,
        "H4_segment_by_slot_data_quality": h4_segment,
    }


def _fmt_row(k, v: dict) -> str:
    if v.get("verdict") == "UNDERPOWERED":
        return f"    k={k:<4} n={v['n']:<4} UNDERPOWERED ({v['reason']})"
    return (f"    k={k:<4} n={v['n']:<4} verdict={v['verdict']:<16} "
            f"fisher_p={v['fisher_pvalue']:.4f}  wr_pos={v['winrate_edge_pos']:.3f}  "
            f"wr_neg={v['winrate_edge_neg']:.3f}")


def _print_report(r: dict) -> None:
    print("=" * 100)
    print("T-359 — GG-105 ESCALATION: H1 x H4 FORMAL INTERACTION-MODEL TEST")
    print("=" * 100)
    print(f"\nfrozen_epoch={r['frozen_epoch']}  clean_n={r['clean_n_epoch3']}  "
          f"joined={r['n_joined']}  misses={r['n_join_misses']}")
    print(f"ba_l10 cohort-mean prior (internal, data-derived) = {r['ba_l10_cohort_mean_prior']}")
    sc = r["repro_sanity_check_k0_vs_stored_model_p"]
    print(f"\nJoin/repro sanity (k=0 recompute vs stored model_p): "
          f"n={sc['n']} exact_matches={sc['exact_matches']} "
          f"max_abs_diff={sc['max_abs_diff']:.6f} mean_abs_diff={sc['mean_abs_diff']:.6f}")

    print(f"\n--- H1: ba_l10 shrinkage sweep (full cohort, n={r['n_joined']}) ---")
    for k in SHRINKAGE_K:
        print(_fmt_row(k, r["H1_shrinkage_sweep_full_cohort"][str(k) if str(k) in r["H1_shrinkage_sweep_full_cohort"] else k]))

    print(f"\n--- H4: segmentation by ab_remaining data quality (k=0, no shrinkage) ---")
    print(f"    slot_known (accurate ab_remaining, n={r['n_slot_known']}): "
          f"{r['H4_segment_by_slot_data_quality']['slot_known']}")
    print(f"    slot_fallback (flat-default ab_remaining, n={r['n_slot_fallback']}): "
          f"{r['H4_segment_by_slot_data_quality']['slot_fallback']}")

    print(f"\n--- H1xH4: ba_l10 shrinkage sweep, restricted to slot_fallback subset (n={r['n_slot_fallback']}) ---")
    for k in SHRINKAGE_K:
        row = r["H1xH4_shrinkage_sweep_fallback_only"]
        row = row[str(k)] if str(k) in row else row[k]
        print(_fmt_row(k, row))
    print("=" * 100)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--t4-ledger", type=Path, default=DEFAULT_T4_LEDGER)
    p.add_argument("--cycle-log", type=Path, default=DEFAULT_CYCLE_LOG)
    p.add_argument("--out", type=Path, default=OUT_DIR)
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    if not args.cycle_log.exists():
        print(f"ERROR: cycle log not found at {args.cycle_log}. Pull it first: "
              f"scp prediction-market-vps:/opt/prediction-market-bot/logs/"
              f"t4_mlb_cycle_log.jsonl {args.cycle_log}", file=sys.stderr)
        return 1

    result = build_report(args.t4_ledger, args.cycle_log)
    args.out.mkdir(parents=True, exist_ok=True)
    out_json = args.out / "interaction_model_results.json"
    out_json.write_text(json.dumps(result, indent=2, default=str))
    _print_report(result)
    print(f"\nWrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
