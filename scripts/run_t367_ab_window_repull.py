#!/usr/bin/env python3
"""
T-367 — live AB_WINDOW re-pull: replace run_t359_gg105_interaction_model.py's
fixed AB_WINDOW=37 assumption with each player's real per-row rolling AB sum,
re-run the H1 shrinkage sweep, and diff against the k=37-fixed baseline.

WHY THIS EXISTS
---------------
T-365 (feasibility check, 2026-07-15) found the real ~10-game rolling AB sum
behind each player's ba_l10 (mlb_features.py:191, DEFAULT_WINDOW=10,
MIN_PERIODS=3) is never persisted anywhere on disk -- it's a transient
pandas Series, recomputed fresh every C2 run and discarded. The only source
is a live call per player to the MLB Stats API (fetch_batter_game_log,
mlb_ingestion.py:358). run_t359_gg105_interaction_model.py's H1 sweep used
AB_WINDOW=37 (a stated "~35-40 AB" midpoint assumption, not a fitted value)
for every row uniformly. This script replaces that fixed constant with each
row's own real rolling AB sum, re-derived from a live pull, and checks
whether the k=37-fixed sweep's monotonic-attenuation finding (which fed
APR-0025's k=40 recommendation) survives.

NOT a production change. Does not touch mlb_features.py, run_t4_mlb_live.py,
or ba_l10_shrunk (already live via ADR-0047 using the real ab_sum in
production -- this script only revisits the retrospective epoch-3 diagnostic
sweep from T-359 that predates ADR-0047's production fix). Diagnostic /
comparative only, per T-367's TODO_NEXT.md scope. Not blocking APR-0025
sign-off (already given, k=40 live since epoch 8 per ADR-0047).

METHOD
------
1. Load epoch-3 clean T4M-PROJ cohort (666 rows, 75 unique player_id) --
   same frozen cohort as run_t359, same join to t4_mlb_cycle_log.jsonl via
   the T-332 forecast_id -> cycle_id join.
2. For each of the 75 unique player_id values, live-fetch that player's
   season=2026 regular-season game log via MLBIngestionClient
   (DEFAULT_REQUEST_DELAY_S=0.6 rate-limit floor, unmodified -- ~45s
   minimum serial pull for 75 players). Cache to disk so re-runs of this
   script don't re-hit the API.
3. Reconstruct each row's real 10-game rolling AB sum as of its game_date,
   using the identical .shift(1).rolling(10, min_periods=3).sum() formula
   already in mlb_features.py:191 (reproduced here, not imported, since
   the production function does not expose ab_sum as an output column --
   see T-365 finding: it's a local Series, never persisted or returned).
4. Re-run the H1 shrinkage sweep (same SHRINKAGE_K = [0, 20, 40, 80, 160],
   same shrink() formula, same edge_monotonicity() verdict machinery
   reused unmodified from run_exp017_mlb per GG-100 discipline) with each
   row's real ab_sum substituted for the fixed AB_WINDOW=37.
5. Diff resulting Fisher-p / win-rate-gap table against the existing
   k=37-fixed baseline in
   exp_output/T359-GG105-INTERACTION-MODEL/interaction_model_results.json.

Run:
  python3 scripts/run_t367_ab_window_repull.py
  python3 scripts/run_t367_ab_window_repull.py --cycle-log logs/.vps_t4_mlb_cycle_log_cache.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import pandas as pd  # noqa: E402

import run_band_monitor as bm            # noqa: E402
import run_exp017_mlb as e17             # noqa: E402
import run_t359_gg105_interaction_model as t359  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import (  # noqa: E402
    MLBIngestionClient,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402
from prediction_market_bot.run_t4_mlb_live import p_hits_gte_threshold  # noqa: E402
from run_t332_gamestate_diag import (  # noqa: E402
    load_cycle_index,
    cycle_id_from_forecast_id,
)

DEFAULT_T4_LEDGER = REPO_ROOT / "logs" / "t4_mlb_resolved_ledger.jsonl"
DEFAULT_CYCLE_LOG = REPO_ROOT / "logs" / ".vps_t4_mlb_cycle_log_cache.jsonl"
BASELINE_JSON = REPO_ROOT / "exp_output" / "T359-GG105-INTERACTION-MODEL" / "interaction_model_results.json"
OUT_DIR = REPO_ROOT / "exp_output" / "T367-AB-WINDOW-REPULL"
GAME_LOG_CACHE = OUT_DIR / "game_logs_cache.json"

ROLL_WINDOW = 10       # matches mlb_features.py DEFAULT_WINDOW
MIN_PERIODS = 3        # matches mlb_features.py MIN_PERIODS
SEASON = 2026
FALLBACK_AB_WINDOW = t359.AB_WINDOW  # 37 -- used only if a live row can't be matched


def fetch_all_game_logs(player_ids: set[int], audit_log_path: Path) -> dict[str, list[dict]]:
    """Live-fetch (or read cache of) each player's season game log. One HTTP
    call per unique player, throttled at DEFAULT_REQUEST_DELAY_S."""
    GAME_LOG_CACHE.parent.mkdir(parents=True, exist_ok=True)
    cached: dict[str, list[dict]] = {}
    if GAME_LOG_CACHE.exists():
        cached = json.loads(GAME_LOG_CACHE.read_text())

    missing = sorted(pid for pid in player_ids if str(pid) not in cached)
    if not missing:
        print(f"All {len(player_ids)} player game logs already cached at {GAME_LOG_CACHE}.")
        return cached

    print(f"Fetching {len(missing)} of {len(player_ids)} player game logs live "
          f"(cached: {len(player_ids) - len(missing)})...")
    logger = AuditLogger(audit_log_path)
    client = MLBIngestionClient(logger=logger, snapshot_id="T367-AB-WINDOW-REPULL", _team_abbr_map={})

    for i, pid in enumerate(missing, 1):
        ok, df = client.fetch_batter_game_log(pid, season=SEASON, season_type="R")
        if not ok:
            print(f"  [{i}/{len(missing)}] player_id={pid}: FETCH FAILED (HTTP error) -- "
                  f"will fall back to AB_WINDOW={FALLBACK_AB_WINDOW} for this player", file=sys.stderr)
            cached[str(pid)] = []
        else:
            rows = df[["game_date", "ab"]].copy()
            rows["game_date"] = rows["game_date"].astype(str)
            cached[str(pid)] = rows.to_dict("records")
            print(f"  [{i}/{len(missing)}] player_id={pid}: {len(rows)} games fetched")
        GAME_LOG_CACHE.write_text(json.dumps(cached, indent=2))

    return cached


def build_real_ab_lookup(game_logs: dict[str, list[dict]]) -> dict[tuple[int, str], float]:
    """{(player_id, game_date_str): real_10game_rolling_ab_sum}, NaN rows omitted.

    Reproduces mlb_features.py:191's ab_sum = df["ab"].shift(1).rolling(window,
    min_periods=min_periods).sum() exactly (same window/min_periods), since
    that value is never persisted anywhere and must be re-derived here.
    """
    lookup: dict[tuple[int, str], float] = {}
    for pid_str, rows in game_logs.items():
        if not rows:
            continue
        df = pd.DataFrame(rows)
        df["game_date"] = pd.to_datetime(df["game_date"], errors="coerce")
        df = df.dropna(subset=["game_date"]).sort_values("game_date").reset_index(drop=True)
        df["ab"] = pd.to_numeric(df["ab"], errors="coerce").fillna(0)
        ab_sum = df["ab"].shift(1).rolling(ROLL_WINDOW, min_periods=MIN_PERIODS).sum()
        for gd, val in zip(df["game_date"].dt.strftime("%Y-%m-%d"), ab_sum):
            if pd.notna(val):
                lookup[(int(pid_str), gd)] = float(val)
    return lookup


def shrink_real(ba_l10: float, prior: float, k: int, ab_real: float) -> float:
    if k == 0:
        return ba_l10
    return (ab_real * ba_l10 + k * prior) / (ab_real + k)


def recompute_positions_real(
    joined: list[dict], k: int, prior: float, ab_lookup: dict[tuple[int, str], float]
) -> tuple[list, int]:
    """Same recompute as run_t359's recompute_positions(), but shrink() uses
    each row's real ab_sum instead of the fixed AB_WINDOW=37. Rows with no
    live match fall back to AB_WINDOW=37 (tracked and reported, not silently
    dropped)."""
    out = []
    n_fallback = 0
    for r in joined:
        h_so_far = int(r["_gs_h_so_far"] or 0)
        ab_remaining = int(r["_gs_ab_remaining"] or 0)
        ba_raw = float(r["_gs_ba_l10"] if r["_gs_ba_l10"] is not None else 0.25)
        pid = r.get("player_id")
        gdate = str(r.get("game_date", ""))
        ab_real = ab_lookup.get((int(pid), gdate)) if pid is not None else None
        if ab_real is None:
            ab_real = float(FALLBACK_AB_WINDOW)
            n_fallback += 1
        ba_adj = shrink_real(ba_raw, prior, k, ab_real)
        threshold = int(r.get("_thr", 0) or 0)
        p_t4_prime = p_hits_gte_threshold(h_so_far, threshold, ba_adj, ab_remaining)
        fne = t359.corrected_symmetric_vig_edge(r["_dir"], p_t4_prime, r["_mip"], float(r.get("vig", 0.0) or 0.0))
        r2 = dict(r)
        r2["_model_p"] = p_t4_prime
        r2["_fne"] = fne
        out.append(r2)
    return bm.to_mlb_positions(out), n_fallback


def verdict_row(positions, alpha: float = 0.10) -> dict:
    if len(positions) < e17.MIN_N:
        return {"n": len(positions), "verdict": "UNDERPOWERED",
                "reason": f"n={len(positions)} < MIN_N={e17.MIN_N} (GG-098)"}
    return e17.edge_monotonicity(positions, alpha=alpha)


def build_report(t4_ledger: Path, cycle_log: Path, audit_log_path: Path) -> dict:
    clean = t359.load_epoch3_clean(t4_ledger)
    cycle_idx = load_cycle_index(cycle_log)
    joined, misses = t359.join(clean, cycle_idx)

    prior = sum(float(r["_gs_ba_l10"] or 0.25) for r in joined) / len(joined)

    player_ids = {int(r["player_id"]) for r in joined if r.get("player_id") is not None}
    game_logs = fetch_all_game_logs(player_ids, audit_log_path)
    ab_lookup = build_real_ab_lookup(game_logs)

    n_players_fetched = sum(1 for v in game_logs.values() if v)
    n_players_failed = sum(1 for v in game_logs.values() if not v)

    h1_sweep_real: dict = {}
    fallback_counts: dict = {}
    for k in t359.SHRINKAGE_K:
        positions, n_fb = recompute_positions_real(joined, k, prior, ab_lookup)
        h1_sweep_real[k] = verdict_row(positions)
        fallback_counts[k] = n_fb

    baseline = json.loads(BASELINE_JSON.read_text()) if BASELINE_JSON.exists() else None

    return {
        "frozen_epoch": t359.FROZEN_EPOCH,
        "clean_n_epoch3": len(clean),
        "n_joined": len(joined),
        "n_join_misses": misses,
        "ba_l10_cohort_mean_prior": round(prior, 4),
        "n_unique_players": len(player_ids),
        "n_players_game_log_fetched": n_players_fetched,
        "n_players_game_log_fetch_failed": n_players_failed,
        "n_rows_fallback_to_ab_window_37": fallback_counts,
        "H1_shrinkage_sweep_real_ab_sum": h1_sweep_real,
        "H1_shrinkage_sweep_k37_fixed_baseline": (
            baseline["H1_shrinkage_sweep_full_cohort"] if baseline else None
        ),
    }


def _fmt_row(k, v: dict) -> str:
    if v.get("verdict") == "UNDERPOWERED":
        return f"    k={k:<4} n={v['n']:<4} UNDERPOWERED ({v['reason']})"
    return (f"    k={k:<4} n={v['n']:<4} verdict={v['verdict']:<16} "
            f"fisher_p={v['fisher_pvalue']:.4f}  wr_pos={v['winrate_edge_pos']:.3f}  "
            f"wr_neg={v['winrate_edge_neg']:.3f}")


def _print_report(r: dict) -> None:
    print("=" * 100)
    print("T-367 — LIVE AB_WINDOW RE-PULL: REAL PER-ROW AB SUM vs FIXED AB_WINDOW=37")
    print("=" * 100)
    print(f"\nfrozen_epoch={r['frozen_epoch']}  clean_n={r['clean_n_epoch3']}  "
          f"joined={r['n_joined']}  misses={r['n_join_misses']}")
    print(f"unique players={r['n_unique_players']}  fetched={r['n_players_game_log_fetched']}  "
          f"failed={r['n_players_game_log_fetch_failed']}")

    print(f"\n--- H1 sweep, REAL per-row rolling AB sum (full cohort, n={r['n_joined']}) ---")
    for k, v in r["H1_shrinkage_sweep_real_ab_sum"].items():
        n_fb = r["n_rows_fallback_to_ab_window_37"].get(k, 0)
        print(_fmt_row(k, v) + f"  (rows fell back to AB_WINDOW=37: {n_fb})")

    if r["H1_shrinkage_sweep_k37_fixed_baseline"]:
        print(f"\n--- k=37-fixed baseline (T-359, on file) ---")
        for k_str, v in r["H1_shrinkage_sweep_k37_fixed_baseline"].items():
            print(_fmt_row(int(k_str), v))
    print("=" * 100)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--t4-ledger", type=Path, default=DEFAULT_T4_LEDGER)
    p.add_argument("--cycle-log", type=Path, default=DEFAULT_CYCLE_LOG)
    p.add_argument("--out", type=Path, default=OUT_DIR)
    p.add_argument("--audit-log", type=Path, default=OUT_DIR / "c1_audit.jsonl")
    return p


def main(argv=None) -> int:
    args = _build_parser().parse_args(argv)
    if not args.cycle_log.exists():
        print(f"ERROR: cycle log not found at {args.cycle_log}. Pull it first: "
              f"scp prediction-market-vps:/opt/prediction-market-bot/logs/"
              f"t4_mlb_cycle_log.jsonl {args.cycle_log}", file=sys.stderr)
        return 1

    result = build_report(args.t4_ledger, args.cycle_log, args.audit_log)
    args.out.mkdir(parents=True, exist_ok=True)
    out_json = args.out / "ab_window_repull_results.json"
    out_json.write_text(json.dumps(result, indent=2, default=str))
    _print_report(result)
    print(f"\nWrote {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
