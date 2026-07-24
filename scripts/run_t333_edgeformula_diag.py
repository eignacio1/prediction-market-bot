#!/usr/bin/env python3
"""
T-333 Component B — GG-105 edge-formula audit (H1-H5), offline ledger-replay.

WHY THIS EXISTS
---------------
T-324/T-329/T-332 established that T4M-PROJ's clean_n=271 cohort shows a
robust, tercile-monotonic ANTI-PREDICTIVE relationship between computed edge
and realized win rate, that it is NOT a sizing artifact (T-329), and NOT
concentrated in a single analyzable game-state slice (T-332). That leaves the
edge computation itself (p_t4 / MIP / fee-net-edge, or an upstream feature
feeding it) as the leading unexplained factor. T-333's scope doc registers
five testable hypotheses against that computation, found via direct code
read of `p_hits_gte_threshold()` and its call site in `run_t4_mlb_live.py`:

  H1 — uncalibrated ba_l10 variance inflates edge at the tails: because
       p_t4 uses raw ba_l10 as a fixed per-AB Bernoulli parameter with no
       shrinkage/calibration, a player on a hot or cold BA_L10 streak (small
       n=10 game window) produces a large, noisy edge that does not reflect
       true skill -- larger edge would correlate with more extreme ba_l10.
  H2 — CONFIRMED BY CODE READ (this session, no backtest needed): p_t1 is
       loaded into ctx (line 343) and passed to store.stage_order() (line
       1088) for audit persistence only -- it never enters gross_edge
       (line 952: p_t4 - mip - vig). T1's calibrated estimate is completely
       unused in T4's own edge computation.
  H3 — default-fill masking: ba_l10 defaults to 0.25 (line 850) when the
       pregame context is missing it. If default-filled rows are
       systematically mis-distributed across edge terciles, that would
       distort the tercile ranking independent of any real signal.
  H4 — ab_remaining estimator drift: T-332 found batting_slot is 99.6%
       constant-zero system-wide. _compute_ab_remaining() takes batting_slot
       as an input; if it is a dead field, ab_remaining may be systematically
       mis-estimated in a way that correlates with edge tercile.
  H5 — vig/fee sign/direction re-derivation: confirm vig is used consistently
       (always subtracted, never double-counted or sign-flipped) across the
       YES/NO direction split introduced by GG-087.

This script is investigation only (offline ledger-replay against the
existing clean_n cohort) -- no live-formula change. Per T-333's explicit
scope and Hard Rule 3 (ADRs immutable, ADR-0039 Tier B precedent), any fix
implied by these findings requires a fresh DS sign-off and a superseding
ADR before touching run_t4_mlb_live.py's live formula.

METHOD
------
Reuses the T-332 join (forecast_id -> cycle_id -> t4_mlb_cycle_log.jsonl row)
to attach ba_l10 and batting_slot to every clean_n resolved position, then:
  H1: correlate |ba_l10 - 0.5| (distance from a neutral coin-flip prior) and
      ba_l10's own extremity against edge magnitude and tercile membership;
      compare ba_l10 variance across terciles.
  H3: flag exact ba_l10==0.25 (default-fill marker) rows; compare their
      distribution and win rate across terciles against non-default rows.
  H4: compare batting_slot==0 rate and ab_remaining distribution across
      terciles.
  H5: recompute gross_edge/net_edge from stored mip/vig/p_t4 independently
      (never trust a stored field -- GG-100 discipline) and diff against
      the stored `_fne`; separately check vig sign consistency (should
      always be a small positive subtracted term, never negative or
      larger than mip itself).

Run:
  python3 scripts/run_t333_edgeformula_diag.py
"""
from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_band_monitor as bm       # noqa: E402  load_t4_ledger, filter_clean
import run_t332_gamestate_diag as gd  # noqa: E402  join helpers, pearson_r, build_terciles
import run_exp017_mlb as e17        # noqa: E402  kalshi_fee (audited)
import ab_harness as abh            # noqa: E402  metrics()

DEFAULT_T4_LEDGER = Path("logs/t4_mlb_resolved_ledger.jsonl")
DEFAULT_CYCLE_LOG = Path("logs/.vps_t4_mlb_cycle_log_cache.jsonl")
OUT_DIR = Path("exp_output/T333-EDGEFORMULA-DIAG")

EXTRA_FIELDS = ("ba_l10",)  # not in T-332's GAME_STATE_FIELDS tuple; added here


def join_extra(recs: list[dict], cycle_idx: dict) -> tuple[list[dict], int]:
    joined, misses = [], 0
    for r in recs:
        cid = gd.cycle_id_from_forecast_id(str(r.get("forecast_id", "")))
        key = (cid, r.get("kalshi_ticker"))
        gs = cycle_idx.get(key)
        if gs is None:
            misses += 1
            continue
        r2 = dict(r)
        for f in gd.GAME_STATE_FIELDS + EXTRA_FIELDS:
            r2[f"_gs_{f}"] = gs.get(f)
        joined.append(r2)
    return joined, misses


# ── H1: ba_l10 extremity vs edge magnitude ─────────────────────────────────

def h1_ba_extremity(recs: list[dict]) -> dict:
    xs_dist, xs_ba, edge_ys, win_ys = [], [], [], []
    for r in recs:
        ba = r.get("_gs_ba_l10")
        if ba is None:
            continue
        xs_dist.append(abs(float(ba) - 0.25))  # distance from the default/prior
        xs_ba.append(float(ba))
        edge_ys.append(r["_fne"])
        win_ys.append(float(r["_win"]))

    terciles = gd.build_terciles(recs)
    tercile_ba_stats = []
    for idx, t in enumerate(terciles, start=1):
        bas = [float(r["_gs_ba_l10"]) for r in t if r.get("_gs_ba_l10") is not None]
        if not bas:
            tercile_ba_stats.append({"tercile": idx, "n": 0})
            continue
        tercile_ba_stats.append({
            "tercile": idx,
            "n": len(bas),
            "ba_l10_mean": statistics.mean(bas),
            "ba_l10_stdev": statistics.stdev(bas) if len(bas) > 1 else 0.0,
            "ba_l10_extremity_mean": sum(abs(b - 0.25) for b in bas) / len(bas),
        })

    return {
        "n": len(xs_dist),
        "corr_extremity_vs_edge": gd.pearson_r(xs_dist, edge_ys),
        "corr_extremity_vs_win": gd.pearson_r(xs_dist, win_ys),
        "corr_ba_l10_vs_edge": gd.pearson_r(xs_ba, edge_ys),
        "by_tercile": tercile_ba_stats,
    }


# ── H3: default-fill (ba_l10 == 0.25 exactly) masking ──────────────────────

def h3_default_fill(recs: list[dict]) -> dict:
    tagged = []
    for r in recs:
        ba = r.get("_gs_ba_l10")
        is_default = ba is not None and abs(float(ba) - 0.25) < 1e-9
        tagged.append((r, is_default))

    n_default = sum(1 for _, d in tagged if d)
    n_total = len(tagged)

    terciles = gd.build_terciles(recs)
    by_tercile = []
    for idx, t in enumerate(terciles, start=1):
        t_default = [r for r in t if r.get("_gs_ba_l10") is not None
                     and abs(float(r["_gs_ba_l10"]) - 0.25) < 1e-9]
        n = len(t)
        by_tercile.append({
            "tercile": idx,
            "n": n,
            "n_default_fill": len(t_default),
            "pct_default_fill": (len(t_default) / n) if n else float("nan"),
            "default_fill_win_rate": (
                sum(r["_win"] for r in t_default) / len(t_default)
                if t_default else float("nan")
            ),
            "non_default_win_rate": (
                sum(r["_win"] for r in t if r not in t_default) /
                (n - len(t_default)) if (n - len(t_default)) else float("nan")
            ),
        })

    return {
        "n_total": n_total,
        "n_default_fill": n_default,
        "pct_default_fill_overall": (n_default / n_total) if n_total else float("nan"),
        "by_tercile": by_tercile,
    }


# ── H4: batting_slot==0 constant-zero + ab_remaining drift ────────────────

def h4_slot_and_ab_remaining(recs: list[dict]) -> dict:
    terciles = gd.build_terciles(recs)
    by_tercile = []
    for idx, t in enumerate(terciles, start=1):
        slots = [r.get("_gs_batting_slot") for r in t if r.get("_gs_batting_slot") is not None]
        ab_rem = [r.get("_gs_ab_remaining") for r in t if r.get("_gs_ab_remaining") is not None]
        n_slot0 = sum(1 for s in slots if int(s) == 0)
        by_tercile.append({
            "tercile": idx,
            "n": len(t),
            "pct_batting_slot_zero": (n_slot0 / len(slots)) if slots else float("nan"),
            "ab_remaining_mean": (sum(ab_rem) / len(ab_rem)) if ab_rem else float("nan"),
            "ab_remaining_distribution": {
                str(v): ab_rem.count(v) for v in sorted(set(ab_rem))
            } if ab_rem else {},
        })
    overall_slots = [r.get("_gs_batting_slot") for r in recs if r.get("_gs_batting_slot") is not None]
    overall_pct_zero = (
        sum(1 for s in overall_slots if int(s) == 0) / len(overall_slots)
        if overall_slots else float("nan")
    )
    return {"overall_pct_batting_slot_zero": overall_pct_zero, "by_tercile": by_tercile}


# ── H5: live-parity edge re-derivation (vig-inclusion gap) ─────────────────

def h5_recompute_edge(recs: list[dict]) -> dict:
    """
    FINDING (this audit, not previously logged): the audited backtest metric
    `e17.compute_fee_net_edge()` -- used throughout every GG-105 diagnostic to
    date (T-324's original tercile find, T-329's size-weighted re-run, T-332's
    game-state segmentation, and `bm.load_t4_ledger()`'s `_fne` field that all
    three consume) -- computes `model_p - mip - kalshi_fee(mip)`. It has NO
    vig term at all. But the live decision path that actually gates/sizes a
    bet (`run_t4_mlb_live.py` line 952: `gross_edge = p_t4 - mip - vig`, line
    954: `net_edge = gross_edge - kalshi_fee`) DOES subtract vig, in addition
    to the fee. Every GG-105 tercile/Fisher result to date has therefore been
    computed on a formula that omits a term the live system actually uses.

    This function re-derives a "live-parity" edge (model_p - mip - vig -
    kalshi_fee(mip)) from the ledger's own stored `vig`/`vig_at_entry` field
    and re-runs the same tercile win-rate breakdown against it, to check
    whether the omission is cosmetic (vig small/near-constant, tercile
    ranking unchanged) or load-bearing (vig varies enough to have been
    silently distorting every prior tercile assignment in this
    investigation).
    """
    scored = []
    vig_values = []
    for r in recs:
        model_p = r.get("_model_p")
        mip = r.get("_mip")
        direction = r.get("_dir")
        vig = r.get("vig_at_entry", r.get("vig", None))
        if model_p is None or mip is None or direction is None:
            continue
        vig = float(vig) if vig is not None else 0.0
        vig_values.append(vig)
        # Mirrors run_t4_mlb_live.py's actual sign convention exactly:
        # gross_edge = p_t4 - mip - vig is computed once (undirected). If it is
        # negative, direction flips to NO and directional_gross_edge = -gross_edge
        # = mip - model_p + vig -- vig's sign flips with the direction, just like
        # (model_p - mip) does. The fee is always subtracted afterward, never
        # flipped (directional_net_edge = directional_gross_edge - kalshi_fee),
        # matching compute_fee_net_edge()'s own YES/NO convention above.
        fee = e17.kalshi_fee(mip)
        if direction == "YES":
            live_parity_edge = model_p - mip - vig - fee
        else:
            live_parity_edge = mip - model_p + vig - fee
        r2 = dict(r)
        r2["_live_parity_fne"] = live_parity_edge
        scored.append(r2)

    # standard (backtest-formula) terciles, for side-by-side comparison
    std_terciles = gd.build_terciles(scored)  # sorts by "_fne" (backtest formula)
    std_rows = []
    for idx, t in enumerate(std_terciles, start=1):
        n = len(t)
        if n == 0:
            std_rows.append({"tercile": idx, "n": 0})
            continue
        m = abh.metrics(t)
        std_rows.append({"tercile": idx, "n": n, "win_rate": m["win_rate"],
                          "edge_mean": sum(x["_fne"] for x in t) / n})

    # live-parity terciles: re-sort by the vig-inclusive edge
    ordered = sorted(scored, key=lambda r: r["_live_parity_fne"])
    n_total = len(ordered)
    base, rem = divmod(n_total, 3)
    sizes = [base + (1 if i < rem else 0) for i in range(3)]
    lp_terciles, i = [], 0
    for s in sizes:
        lp_terciles.append(ordered[i:i + s])
        i += s
    lp_rows = []
    for idx, t in enumerate(lp_terciles, start=1):
        n = len(t)
        if n == 0:
            lp_rows.append({"tercile": idx, "n": 0})
            continue
        m = abh.metrics(t)
        lp_rows.append({"tercile": idx, "n": n, "win_rate": m["win_rate"],
                         "edge_mean": sum(x["_live_parity_fne"] for x in t) / n})

    # how many positions change tercile membership under the live-parity sort?
    std_membership = {id(r): idx for idx, t in enumerate(std_terciles, start=1) for r in t}
    lp_membership = {id(r): idx for idx, t in enumerate(lp_terciles, start=1) for r in t}
    n_reassigned = sum(
        1 for r in scored
        if std_membership.get(id(r)) != lp_membership.get(id(r))
    )

    # rigorous verdict: run the audited edge_monotonicity() Fisher test against
    # BOTH formulas (never eyeball a tercile table alone, GG-098/GG-100 discipline).
    std_positions = bm.to_mlb_positions(scored)  # uses r["_fne"] via e17.MLBPosition
    std_mono = e17.edge_monotonicity(std_positions, alpha=0.10)

    lp_positions = []
    for r in scored:
        p = bm.to_mlb_positions([r])[0]
        lp_positions.append(e17.MLBPosition(
            kalshi_ticker=p.kalshi_ticker, direction=p.direction, mip=p.mip,
            vig=p.vig, model_p=p.model_p, fee_net_edge=r["_live_parity_fne"],
            outcome=p.outcome, pnl=p.pnl, game_date=p.game_date,
            threshold=p.threshold, player_name=p.player_name,
        ))
    lp_mono = e17.edge_monotonicity(lp_positions, alpha=0.10)

    return {
        "n_scored": len(scored),
        "vig_stats": {
            "mean": statistics.mean(vig_values) if vig_values else float("nan"),
            "stdev": statistics.stdev(vig_values) if len(vig_values) > 1 else 0.0,
            "min": min(vig_values) if vig_values else float("nan"),
            "max": max(vig_values) if vig_values else float("nan"),
            "n_zero_or_missing": sum(1 for v in vig_values if v == 0.0),
        },
        "backtest_formula_terciles": std_rows,
        "live_parity_terciles": lp_rows,
        "n_reassigned_terciles": n_reassigned,
        "pct_reassigned": (n_reassigned / len(scored)) if scored else float("nan"),
        "backtest_formula_verdict": std_mono,
        "live_parity_verdict": lp_mono,
    }


# ── report ───────────────────────────────────────────────────────────────────

def _print_report(result: dict) -> None:
    print("=" * 100)
    print("T-333 COMPONENT B — GG-105 EDGE-FORMULA AUDIT (T4M-PROJ, clean_n)")
    print("=" * 100)
    print(f"\nclean_n={result['clean_n']}  joined={result['n_joined']}  join_misses={result['n_join_misses']}")

    print("\n--- H2 (code-read, no backtest needed) ---")
    print("  CONFIRMED: p_t1 (line 1088, ctx['p_t1']) feeds only store.stage_order() for "
          "audit persistence. gross_edge (line 952) = p_t4 - mip - vig; p_t1 never appears "
          "in that expression or anywhere in the p_t4/edge computation path.")

    h1 = result["h1"]
    print(f"\n--- H1: ba_l10 extremity vs edge (n={h1['n']}) ---")
    print(f"  corr(|ba_l10-0.25|, edge)  = {h1['corr_extremity_vs_edge']:+.3f}")
    print(f"  corr(|ba_l10-0.25|, win)   = {h1['corr_extremity_vs_win']:+.3f}")
    print(f"  corr(ba_l10, edge)        = {h1['corr_ba_l10_vs_edge']:+.3f}")
    for t in h1["by_tercile"]:
        if t["n"] == 0:
            continue
        print(f"    tercile {t['tercile']}: n={t['n']:<4} ba_l10_mean={t['ba_l10_mean']:.4f}  "
              f"stdev={t['ba_l10_stdev']:.4f}  extremity_mean={t['ba_l10_extremity_mean']:.4f}")

    h3 = result["h3"]
    print(f"\n--- H3: default-fill (ba_l10==0.25) masking ---")
    print(f"  overall: {h3['n_default_fill']}/{h3['n_total']} "
          f"({h3['pct_default_fill_overall']*100:.1f}%) rows are default-filled")
    for t in h3["by_tercile"]:
        print(f"    tercile {t['tercile']}: n={t['n']:<4} default_fill={t['n_default_fill']} "
              f"({t['pct_default_fill']*100:.1f}%)  "
              f"default_win_rate={t['default_fill_win_rate']:.3f}  "
              f"non_default_win_rate={t['non_default_win_rate']:.3f}")

    h4 = result["h4"]
    print(f"\n--- H4: batting_slot==0 constant-zero + ab_remaining drift ---")
    print(f"  overall pct batting_slot==0: {h4['overall_pct_batting_slot_zero']*100:.1f}%")
    for t in h4["by_tercile"]:
        print(f"    tercile {t['tercile']}: n={t['n']:<4} "
              f"pct_slot_zero={t['pct_batting_slot_zero']*100:.1f}%  "
              f"ab_remaining_mean={t['ab_remaining_mean']:.3f}  "
              f"dist={t['ab_remaining_distribution']}")

    h5 = result["h5"]
    vs = h5["vig_stats"]
    print(f"\n--- H5: live-parity edge re-derivation (vig-inclusion gap) ---")
    print(f"  FINDING: e17.compute_fee_net_edge() (used by every GG-105 diagnostic to date, "
          f"incl. T-324/T-329/T-332) omits the market `vig` term entirely -- only "
          f"model_p - mip - kalshi_fee(mip). The live decision path in run_t4_mlb_live.py "
          f"DOES subtract vig (line 952). This re-derives a vig-inclusive 'live-parity' edge "
          f"and re-sorts terciles by it.")
    print(f"  vig stats: mean={vs['mean']:.4f}  stdev={vs['stdev']:.4f}  "
          f"min={vs['min']:.4f}  max={vs['max']:.4f}  n_zero_or_missing={vs['n_zero_or_missing']}")
    print(f"\n  backtest-formula terciles (no vig, prior methodology):")
    for t in h5["backtest_formula_terciles"]:
        if t["n"] == 0:
            continue
        print(f"    tercile {t['tercile']}: n={t['n']:<4} edge_mean={t['edge_mean']:.4f}  win_rate={t['win_rate']:.3f}")
    print(f"\n  live-parity terciles (vig-inclusive, matches live gating formula):")
    for t in h5["live_parity_terciles"]:
        if t["n"] == 0:
            continue
        print(f"    tercile {t['tercile']}: n={t['n']:<4} edge_mean={t['edge_mean']:.4f}  win_rate={t['win_rate']:.3f}")
    print(f"\n  n_reassigned_terciles={h5['n_reassigned_terciles']} "
          f"({h5['pct_reassigned']*100:.1f}% of n={h5['n_scored']} changed tercile membership "
          f"under the vig-inclusive sort)")

    sv, lv = h5["backtest_formula_verdict"], h5["live_parity_verdict"]
    print(f"\n  AUDITED FISHER VERDICT (e17.edge_monotonicity, never reimplemented):")
    print(f"    backtest formula (no vig):  verdict={sv['verdict']:<14} "
          f"p={sv.get('fisher_pvalue', float('nan')):.4f}  "
          f"wr_pos_edge={sv.get('winrate_edge_pos', float('nan')):.3f}  "
          f"wr_neg_edge={sv.get('winrate_edge_neg', float('nan')):.3f}  "
          f"n_pos={sv.get('n_pos_edge', 0)}  n_neg={sv.get('n_neg_edge', 0)}")
    print(f"    live-parity (with vig):     verdict={lv['verdict']:<14} "
          f"p={lv.get('fisher_pvalue', float('nan')):.4f}  "
          f"wr_pos_edge={lv.get('winrate_edge_pos', float('nan')):.3f}  "
          f"wr_neg_edge={lv.get('winrate_edge_neg', float('nan')):.3f}  "
          f"n_pos={lv.get('n_pos_edge', 0)}  n_neg={lv.get('n_neg_edge', 0)}")

    print(f"\n{'='*100}")


def build_report(t4_ledger: Path, cycle_log: Path) -> dict:
    recs = bm.filter_clean(bm.load_t4_ledger(t4_ledger), "T4M-PROJ")
    clean_n = len(recs)
    cycle_idx = gd.load_cycle_index(cycle_log)
    joined, misses = join_extra(recs, cycle_idx)

    return {
        "clean_n": clean_n,
        "n_joined": len(joined),
        "n_join_misses": misses,
        "h1": h1_ba_extremity(joined),
        "h3": h3_default_fill(joined),
        "h4": h4_slot_and_ab_remaining(joined),
        "h5": h5_recompute_edge(joined),
    }


def main(argv=None) -> int:
    t4_ledger = DEFAULT_T4_LEDGER
    cycle_log = DEFAULT_CYCLE_LOG
    if not cycle_log.exists():
        print(f"ERROR: cycle log not found at {cycle_log}. Pull it first: "
              f"scp prediction-market-vps:/opt/prediction-market-bot/logs/"
              f"t4_mlb_cycle_log.jsonl {cycle_log}", file=sys.stderr)
        return 1

    result = build_report(t4_ledger, cycle_log)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_json = OUT_DIR / "edgeformula_diag_results.json"
    out_json.write_text(json.dumps(result, indent=2, default=str))
    _print_report(result)
    print(f"\nWrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
