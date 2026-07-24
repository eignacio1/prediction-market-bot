#!/usr/bin/env python3
"""
T-332 — GG-105 diagnostic 2: game-state segmentation of T4M-PROJ's clean_n
edge-tercile inversion (T-324, extended by T-329's size-weighted re-run).

WHY THIS EXISTS
---------------
T-324 found T4M-PROJ's clean_n cohort (n=271) shows a statistically significant,
tercile-monotonic ANTI-PREDICTIVE relationship between computed edge and win rate
(74.4% -> 64.4% -> 58.2%). T-329 ruled out sizing-as-amplifier (candidate b) --
Kelly stake actually falls, not rises, across edge terciles. That leaves two
candidates open: (a) real signal / game-state noise (T4's core latency thesis:
does the inversion concentrate in specific innings/ab_remaining/score-states,
which would point to a structural noise source rather than a broken edge
formula), and (c) pre-epoch bug residue (already ruled out by construction --
clean_n filter + independently-recomputed edge, GG-100 defense pattern).

This script tests candidate (a) directly: it joins each clean_n resolved
position to the live-poll game state that was current AT THE MOMENT the bet's
edge was computed, then checks whether the inversion is uniform across game
states or concentrated in a specific slice.

DATA AVAILABILITY (checked before building this script, not assumed)
----------------------------------------------------------------------
`t4_mlb_cycle_log.jsonl` (VPS, 2026-07-02 .. present) logs one row per
(cycle_id, ticker) evaluation with `inning`, `ab_remaining`, `ab_so_far`,
`h_so_far`, `batting_slot`, `ba_l10`. It does NOT carry a score-differential
field -- CLAUDE.md already documents this as a known gap for T4M-FLOW
(score_diff never wired from a live poll); this script confirms the same gap
exists in T4M-PROJ's actual live-poll schema, not just T4M-FLOW's, so "score
differential" from the memo's diagnostic-2 proposal is NOT analyzable here and
is reported as an explicit data gap rather than silently dropped.

JOIN
----
Every resolved T4 position's `forecast_id` embeds its originating cycle_id:
  "T4-MLB-C0248-16d339-DJMERRILL3-2"  ->  cycle_id = "C0248-16d339"
Joined against cycle_log's (cycle_id, ticker) key. Verified 271/271 (100%) of
clean_n T4M-PROJ positions join successfully -- clean_n's date range
(2026-07-05 .. 2026-07-09) sits entirely inside the cycle log's coverage
window, so there is no truncation-driven join loss to account for.

METHOD
------
1. Attach game-state fields to every clean_n record via the join above.
2. Report simple point-biserial-style correlations: edge (_fne) vs each
   game-state variable, and win outcome (_win) vs each game-state variable --
   does game state predict edge magnitude or win rate on its own?
3. Bucket on inning (early 1-3 / mid 4-6 / late 7-9+) and ab_remaining
   (0 / 1 / 2+), the two dimensions this data actually supports out of the
   memo's three proposed dimensions.
4. Within each bucket, reproduce the T-324/T-329 tercile win-rate breakdown
   and run the audited edge_monotonicity() Fisher test (run_exp017_mlb.py --
   never reimplement this math, GG-100 discipline) where n allows (MIN_N=30
   inside e17.edge_monotonicity; smaller buckets get a descriptive-only table,
   never a verdict on an underpowered slice, per GG-098).
5. Verdict question: does ANTI-PREDICTIVE concentrate in one bucket (supports
   candidate (a), a structural noise source specific to that game state) or
   reproduce across most/all buckets (argues against a game-state confound and
   points back toward the edge computation itself)?

Run:
  python3 scripts/run_t332_gamestate_diag.py
  python3 scripts/run_t332_gamestate_diag.py --cycle-log logs/.vps_t4_mlb_cycle_log_cache.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_band_monitor as bm     # noqa: E402  load_t4_ledger, filter_clean, to_mlb_positions
import run_exp017_mlb as e17      # noqa: E402  edge_monotonicity, MIN_N (audited Fisher test)
import ab_harness as abh          # noqa: E402  metrics()

DEFAULT_T4_LEDGER = Path("logs/t4_mlb_resolved_ledger.jsonl")
DEFAULT_CYCLE_LOG = Path("logs/.vps_t4_mlb_cycle_log_cache.jsonl")
OUT_DIR = Path("exp_output/T332-GAMESTATE-DIAG")

GAME_STATE_FIELDS = ("inning", "ab_remaining", "ab_so_far", "h_so_far", "batting_slot")


# ── join ──────────────────────────────────────────────────────────────────────

def load_cycle_index(path: Path) -> dict[tuple[str, str], dict]:
    idx: dict[tuple[str, str], dict] = {}
    if not path.exists():
        return idx
    with open(path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            idx[(d["cycle_id"], d["ticker"])] = d
    return idx


def cycle_id_from_forecast_id(forecast_id: str) -> str | None:
    parts = forecast_id.split("-")
    # "T4-MLB-C0248-16d339-DJMERRILL3-2" -> parts[2]="C0248", parts[3]="16d339"
    if len(parts) < 4:
        return None
    return f"{parts[2]}-{parts[3]}"


def join_gamestate(recs: list[dict], cycle_idx: dict[tuple[str, str], dict]) -> tuple[list[dict], int]:
    joined, misses = [], 0
    for r in recs:
        cid = cycle_id_from_forecast_id(str(r.get("forecast_id", "")))
        key = (cid, r.get("kalshi_ticker"))
        gs = cycle_idx.get(key)
        if gs is None:
            misses += 1
            continue
        r2 = dict(r)
        for f in GAME_STATE_FIELDS:
            r2[f"_gs_{f}"] = gs.get(f)
        joined.append(r2)
    return joined, misses


# ── correlation (no scipy dependency needed for a simple Pearson r) ───────────

def pearson_r(xs: list[float], ys: list[float]) -> float:
    n = len(xs)
    if n < 2:
        return float("nan")
    mx = sum(xs) / n
    my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs)
    vy = sum((y - my) ** 2 for y in ys)
    if vx == 0 or vy == 0:
        return float("nan")
    return cov / (vx ** 0.5 * vy ** 0.5)


def correlations(recs: list[dict]) -> dict:
    out = {}
    for f in GAME_STATE_FIELDS:
        xs = [float(r[f"_gs_{f}"]) for r in recs if r.get(f"_gs_{f}") is not None]
        edge_ys = [r["_fne"] for r in recs if r.get(f"_gs_{f}") is not None]
        win_ys = [float(r["_win"]) for r in recs if r.get(f"_gs_{f}") is not None]
        out[f] = {
            "n": len(xs),
            "corr_with_edge": pearson_r(xs, edge_ys),
            "corr_with_win": pearson_r(xs, win_ys),
        }
    return out


# ── bucketing ────────────────────────────────────────────────────────────────

def inning_bucket(inning) -> str:
    if inning is None:
        return "unknown"
    inning = int(inning)
    if inning <= 3:
        return "early_1-3"
    if inning <= 6:
        return "mid_4-6"
    return "late_7+"


def ab_remaining_bucket(ab_remaining) -> str:
    if ab_remaining is None:
        return "unknown"
    ab_remaining = int(ab_remaining)
    if ab_remaining <= 0:
        return "0"
    if ab_remaining == 1:
        return "1"
    return "2+"


def build_terciles(recs: list[dict]) -> list[list[dict]]:
    ordered = sorted(recs, key=lambda r: r["_fne"])
    n = len(ordered)
    base, rem = divmod(n, 3)
    sizes = [base + (1 if i < rem else 0) for i in range(3)]
    terciles, i = [], 0
    for s in sizes:
        terciles.append(ordered[i:i + s])
        i += s
    return terciles


def tercile_table(recs: list[dict]) -> list[dict]:
    rows = []
    for idx, t in enumerate(build_terciles(recs), start=1):
        n = len(t)
        if n == 0:
            rows.append({"tercile": idx, "n": 0})
            continue
        m = abh.metrics(t)
        rows.append({
            "tercile": idx,
            "n": n,
            "edge_mean": sum(r["_fne"] for r in t) / n,
            "win_rate": m["win_rate"],
            "ev_per_bet_usd": m["ev_per_bet_usd"],
        })
    return rows


def analyze_bucket(name: str, recs: list[dict]) -> dict:
    n = len(recs)
    result = {"bucket": name, "n": n, "terciles": tercile_table(recs)}
    if n == 0:
        result["verdict"] = "EMPTY"
        return result
    m = abh.metrics(recs)
    result["win_rate"] = m["win_rate"]
    result["ev_per_bet_usd"] = m["ev_per_bet_usd"]
    result["pnl_per_dollar"] = m["pnl_per_dollar"]
    if n >= e17.MIN_N:
        positions = bm.to_mlb_positions(recs)
        mono = e17.edge_monotonicity(positions, alpha=0.10)
        result["edge_monotonicity"] = mono
        result["verdict"] = mono["verdict"]
    else:
        result["verdict"] = "UNDERPOWERED"
        result["reason"] = f"n={n} < MIN_N={e17.MIN_N} — descriptive only, no Fisher verdict (GG-098)"
    return result


# ── report ───────────────────────────────────────────────────────────────────

def _print_report(result: dict) -> None:
    print("=" * 100)
    print("T-332 — GG-105 DIAGNOSTIC 2: GAME-STATE SEGMENTATION (T4M-PROJ, clean_n)")
    print("=" * 100)
    print(f"\nclean_n={result['clean_n']}  joined={result['n_joined']}  join_misses={result['n_join_misses']}")
    print("\nDATA GAP: score-differential is NOT present in t4_mlb_cycle_log.jsonl's live-poll "
          "schema for T4M-PROJ (fields logged: inning, ab_remaining, ab_so_far, h_so_far, "
          "batting_slot, ba_l10 — no score_diff). Not analyzable here; matches CLAUDE.md's "
          "documented T4M-FLOW score_diff wiring gap, now confirmed for T4M-PROJ too.")

    print("\n--- Correlations (game-state var vs. edge magnitude / win outcome) ---")
    for f, c in result["correlations"].items():
        print(f"  {f:<14} n={c['n']:<5} corr_with_edge={c['corr_with_edge']:+.3f}  "
              f"corr_with_win={c['corr_with_win']:+.3f}")

    for dim in ("inning_bucket", "ab_remaining_bucket"):
        print(f"\n--- Bucketed by {dim} ---")
        for b in result[dim]:
            print(f"\n  [{b['bucket']}] n={b['n']}", end="")
            if b["n"] > 0:
                print(f"  win_rate={b.get('win_rate', float('nan')):.3f}  "
                      f"ev/bet=${b.get('ev_per_bet_usd', float('nan')):+.4f}  "
                      f"verdict={b['verdict']}")
                for t in b["terciles"]:
                    if t["n"] == 0:
                        continue
                    print(f"      tercile {t['tercile']}: n={t['n']:<4} "
                          f"edge_mean={t['edge_mean']:.4f}  win_rate={t['win_rate']:.3f}")
            else:
                print("  (empty)")

    print(f"\n{'='*100}")
    print("VERDICT SUMMARY")
    verdicts = {}
    for dim in ("inning_bucket", "ab_remaining_bucket"):
        for b in result[dim]:
            if b["n"] > 0:
                verdicts[f"{dim}={b['bucket']}"] = b["verdict"]
    anti = [k for k, v in verdicts.items() if v == e17.E_ANTI]
    mono = [k for k, v in verdicts.items() if v == e17.E_MONO]
    inc = [k for k, v in verdicts.items() if v not in (e17.E_ANTI, e17.E_MONO)]
    print(f"  ANTI-PREDICTIVE buckets ({len(anti)}): {anti}")
    print(f"  MONOTONIC buckets ({len(mono)}): {mono}")
    print(f"  INCONCLUSIVE/UNDERPOWERED buckets ({len(inc)}): {inc}")
    if anti and not mono:
        print("  -> Inversion reproduces across analyzable buckets that reach MIN_N — "
              "NOT concentrated in one game-state slice by this test. Weighs against "
              "candidate (a) as a simple game-state-noise confound; the edge computation "
              "itself remains the leading unexplained factor.")
    elif anti and mono:
        print("  -> Mixed signal: inversion present in some buckets, absent/reversed in "
              "others — inconsistent with a single uniform mechanism either way.")
    elif not anti:
        print("  -> No bucket at MIN_N reproduces the aggregate ANTI-PREDICTIVE verdict on "
              "its own; the aggregate finding may be an emergent property of pooling across "
              "game states rather than any single state driving it, or buckets are "
              "individually underpowered to detect it (see UNDERPOWERED list above).")
    print("=" * 100)


def build_report(t4_ledger: Path, cycle_log: Path) -> dict:
    recs = bm.filter_clean(bm.load_t4_ledger(t4_ledger), "T4M-PROJ")
    clean_n = len(recs)
    cycle_idx = load_cycle_index(cycle_log)
    joined, misses = join_gamestate(recs, cycle_idx)

    for r in joined:
        r["_ib"] = inning_bucket(r["_gs_inning"])
        r["_arb"] = ab_remaining_bucket(r["_gs_ab_remaining"])

    inning_buckets = ["early_1-3", "mid_4-6", "late_7+", "unknown"]
    ab_buckets = ["0", "1", "2+", "unknown"]

    result = {
        "clean_n": clean_n,
        "n_joined": len(joined),
        "n_join_misses": misses,
        "correlations": correlations(joined),
        "inning_bucket": [
            analyze_bucket(b, [r for r in joined if r["_ib"] == b]) for b in inning_buckets
        ],
        "ab_remaining_bucket": [
            analyze_bucket(b, [r for r in joined if r["_arb"] == b]) for b in ab_buckets
        ],
    }
    return result


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--t4-ledger", type=Path, default=DEFAULT_T4_LEDGER)
    p.add_argument("--cycle-log", type=Path, default=DEFAULT_CYCLE_LOG)
    p.add_argument("--out", type=Path, default=OUT_DIR)
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    if not args.cycle_log.exists():
        print(f"ERROR: cycle log not found at {args.cycle_log}. "
              f"Pull it first: scp prediction-market-vps:/opt/prediction-market-bot/logs/"
              f"t4_mlb_cycle_log.jsonl {args.cycle_log}", file=sys.stderr)
        return 1

    result = build_report(args.t4_ledger, args.cycle_log)
    args.out.mkdir(parents=True, exist_ok=True)
    out_json = args.out / "gamestate_diag_results.json"
    out_json.write_text(json.dumps(result, indent=2, default=str))
    _print_report(result)
    print(f"\nWrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
