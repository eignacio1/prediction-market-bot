"""
EXP-025 -- HYP-010 Phase 2, NB refit of box 2.3 (revised EV gate) backtest.

T-500 / GG-221. Pre-registered in
05_RESEARCH_EXPERIMENTS/EXP025_HYP010_NB_PREREGISTRATION_2026-08-28.md
BEFORE this file was written -- read that document for the locked
methodology (dispersion estimator, subset-rule interpretation, verdict
states, effect band, multiplicity disclosure). Do not change any constant
here without updating that document first and re-committing it.

Reuses exp022_totals_backtest.py's data pipeline verbatim (same functions,
same files, same filters) -- the ONLY change is the distributional model
feeding model_p: NB1(mu, phi=2.33) in place of Poisson(mu). mu_total itself
(the L10 offense/defense blend) is unchanged.

Scope-fenced identically to EXP-022: 05_RESEARCH_EXPERIMENTS/ and scripts/
only. No src/ edits, no kelly_fraction, no cell registry, no live ledger,
no activation.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from scipy.stats import nbinom

sys.path.insert(0, str(Path(__file__).resolve().parent))

from exp022_totals_backtest import (  # noqa: E402
    load_team_games,
    verify_store,
    load_totals_rows,
    load_outcomes,
    _blend,
    _normal_power,
    EDGE_THRESHOLD,
    Z_ALPHA_05,
    Z_POWER_95,
)
from prediction_market_bot.c1_signal_ingestion.mlb_team_stats_store import (  # noqa: E402
    MLBTeamStatsStore,
)

WORKTREE = Path(__file__).resolve().parent.parent

# Pre-registered, fixed -- method-of-moments, taken verbatim from T-487's own
# disclosed measurement (var/mean=2.33 on n=3,954 real 2026 team-game runs).
# NOT re-estimated here, NOT tuned against this run's outcome.
PHI = 2.33
P_NB = 1.0 / PHI  # constant across all games


def nb_p_ge(n_min: int, mu: float) -> float:
    """P(total_runs >= n_min) under NB1(mu, PHI): r = mu/(PHI-1), p = 1/PHI."""
    if mu <= 0:
        return 1.0 if n_min <= 0 else 0.0
    r = mu / (PHI - 1.0)
    # sf(k) = P(X > k); we want P(X >= n_min) = P(X > n_min - 1) = sf(n_min - 1)
    return float(nbinom.sf(n_min - 1, r, P_NB))


def main() -> int:
    games_df = load_team_games()
    store = MLBTeamStatsStore.build_from_games(games_df)
    verify_store(store)

    closing_rows, total_rows, dropped_rows = load_totals_rows()
    outcomes = load_outcomes()

    scored: list[dict] = []
    skipped_no_outcome = 0
    skipped_no_stats = 0
    for row in closing_rows:
        oc = outcomes.get(row["event_ticker"])
        if oc is None:
            skipped_no_outcome += 1
            continue
        as_of = row["game_date"]
        mu_home = _blend(store.get_opp_runs_scored(row["home"], as_of),
                          store.get_opp_runs_allowed(row["away"], as_of))
        mu_away = _blend(store.get_opp_runs_scored(row["away"], as_of),
                          store.get_opp_runs_allowed(row["home"], as_of))
        if mu_home is None or mu_away is None:
            skipped_no_stats += 1
            continue
        mu_total = mu_home + mu_away
        model_p = nb_p_ge(row["n"], mu_total)
        yes_mid = row["yes_mid"]
        if yes_mid is None:
            continue
        actual = oc["total_runs"]
        scored.append({
            **row,
            "mu_total": mu_total,
            "model_p": model_p,
            "actual_total_runs": actual,
            "outcome_yes": 1 if actual >= row["n"] else 0,
        })

    print(f"[join] scored rows={len(scored)} skipped_no_outcome={skipped_no_outcome} "
          f"skipped_no_stats={skipped_no_stats}")

    # ---- Gate 2.3 (NB): identical rule, applied to NB's own model_p ----
    per_game_pnls: dict[str, list[float]] = defaultdict(list)
    n_bets = 0
    for r in scored:
        edge = r["model_p"] - r["yes_mid"]
        if abs(edge) <= EDGE_THRESHOLD:
            continue
        n_bets += 1
        if edge > 0:  # buy YES
            pnl = r["outcome_yes"] - r["yes_mid"]
        else:  # buy NO
            no_mid = 1.0 - r["yes_mid"]
            pnl = (1 - r["outcome_yes"]) - no_mid
        per_game_pnls[r["event_ticker"]].append(pnl)

    game_level_pnl = [statistics.mean(v) for v in per_game_pnls.values()]
    clean_n = len(game_level_pnl)
    print(f"[gate2.3-NB] qualifying bets (row-level)={n_bets} "
          f"qualifying GAMES (independent unit)={clean_n}")

    if clean_n >= 2:
        mu = statistics.mean(game_level_pnl)
        sigma = statistics.stdev(game_level_pnl)
    elif clean_n == 1:
        mu = game_level_pnl[0]
        sigma = float("nan")
    else:
        mu = float("nan")
        sigma = float("nan")

    if sigma and sigma > 0 and mu != 0:
        n_star = ((Z_ALPHA_05 + Z_POWER_95) * sigma / abs(mu)) ** 2
    else:
        n_star = float("inf")

    if clean_n >= n_star and mu > 0:
        verdict = "PASS"
    elif clean_n >= n_star and mu <= 0:
        verdict = "FALSIFIED"
    else:
        verdict = "INCONCLUSIVE-EXTEND ARCHIVE"

    print(f"[gate2.3-NB] mean P&L/bet(game-level)={mu} sd={sigma} n*={n_star} clean_n={clean_n}")
    print(f"[gate2.3-NB] VERDICT = {verdict}")

    # ---- Dispersion reconciliation: measured var/mean of NB's own scored mu_total sample ----
    # Not a re-fit of phi -- phi stays fixed at 2.33 per pre-registration.
    # This just reports whether the *outcome* sample's own var/mean is in the
    # neighborhood of the fixed phi used to model it, as a diagnostic.
    actuals = [r["actual_total_runs"] for r in scored]
    if len(actuals) >= 2:
        obs_mean = statistics.mean(actuals)
        obs_var = statistics.variance(actuals)
        obs_ratio = obs_var / obs_mean if obs_mean > 0 else float("nan")
    else:
        obs_mean = obs_var = obs_ratio = float("nan")
    print(f"[dispersion] observed total_runs: n={len(actuals)} mean={obs_mean:.4f} "
          f"var={obs_var:.4f} var/mean={obs_ratio:.4f} (fixed phi used=2.33)")

    # ---- Secondary: paired per-game delta-Brier (descriptive, not a gate) ----
    by_game: dict[str, dict] = {}
    for r in scored:
        g = r["event_ticker"]
        dist = abs(r["yes_mid"] - 0.5)
        if g not in by_game or dist < by_game[g]["_dist"]:
            r2 = dict(r)
            r2["_dist"] = dist
            by_game[g] = r2

    deltas = []
    for r in by_game.values():
        y = r["outcome_yes"]
        model_brier = (r["model_p"] - y) ** 2
        market_brier = (r["yes_mid"] - y) ** 2
        deltas.append(market_brier - model_brier)

    ci_lo = ci_hi = power = None
    if len(deltas) >= 2:
        d_mean = statistics.mean(deltas)
        d_sd = statistics.stdev(deltas)
        se = d_sd / math.sqrt(len(deltas))
        ci_lo, ci_hi = d_mean - 1.96 * se, d_mean + 1.96 * se
        power = _normal_power(d_mean, d_sd, len(deltas), alpha=0.05)
        print(f"[secondary-NB] paired delta-Brier n={len(deltas)} mean={d_mean:.5f} "
              f"95%CI=({ci_lo:.5f},{ci_hi:.5f}) measured_power={power:.3f}")
    else:
        print(f"[secondary-NB] insufficient games for delta-Brier: n={len(deltas)}")

    # ---- n*-vs-effect-size table, using NB's own measured sd (not simulated) ----
    effect_sizes = [0.005, 0.010, 0.015, 0.020, 0.025, 0.030]
    print("[n*-table] using NB's own measured sd = "
          f"{sigma if (sigma and sigma == sigma) else 'n/a'}:")
    n_star_table = []
    if sigma and sigma > 0:
        for es in effect_sizes:
            ns = ((Z_ALPHA_05 + Z_POWER_95) * sigma / es) ** 2
            short = max(0.0, ns - clean_n)
            n_star_table.append({"effect_size": es, "n_star": ns, "clean_n": clean_n, "short_by": short})
            print(f"[n*-table] effect={es:+.3f} n*={ns:.1f} clean_n={clean_n} short_by={short:.1f}")
    else:
        print("[n*-table] sd unavailable (clean_n<2) -- table not computable")

    result = {
        "model": "NB1(phi=2.33 fixed, method-of-moments per T-487)",
        "kxmlbtotal_rows_total": total_rows,
        "dropped_postgame_rows": dropped_rows,
        "closing_tickers": len(closing_rows),
        "scored_rows": len(scored),
        "skipped_no_outcome": skipped_no_outcome,
        "skipped_no_stats": skipped_no_stats,
        "qualifying_bets_row_level": n_bets,
        "clean_n_games": clean_n,
        "mean_pnl_per_bet_game_level": mu,
        "sd_pnl_per_bet_game_level": sigma,
        "n_star": n_star,
        "verdict": verdict,
        "phi_used_fixed": PHI,
        "observed_total_runs_mean": obs_mean,
        "observed_total_runs_var": obs_var,
        "observed_total_runs_var_over_mean": obs_ratio,
        "secondary_delta_brier_n": len(deltas),
        "secondary_delta_brier_mean": statistics.mean(deltas) if len(deltas) >= 2 else None,
        "secondary_delta_brier_ci": [ci_lo, ci_hi] if len(deltas) >= 2 else None,
        "secondary_measured_power": power,
        "n_star_effect_size_table": n_star_table,
    }
    out_path = WORKTREE / "exp_output" / "MLB" / "exp025_gate23_nb_result.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, default=str))
    print(f"[out] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
