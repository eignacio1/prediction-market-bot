"""
EXP-022 -- HYP-010 Phase 2, boxes 2.2 + 2.3 -- team run-total NB/Poisson model
and gate 2.3 (revised EV gate) backtest.

T-487 / GG-207. Scope-fenced to 05_RESEARCH_EXPERIMENTS/ and scripts/ (no src/
edits, no kelly_fraction, no cell registry, no live ledger, no activation).

Reads PRICE_ARCHIVE and the outcome store from the MAIN repo tree (both are
gitignored local-disk artifacts that do not exist in an isolated worktree --
see MAIN_TREE below). Writes only into this worktree.

Reuses MLBTeamStatsStore.get_opp_runs_scored / get_opp_runs_allowed (LL-009:
no new C2 matrix, no new ingestion module -- the only network call this
script makes is MLBIngestionClient.fetch_completed_games(), the same
already-existing C1 method used by scripts/generate_mlb_features.py, to fill
the 2026-07-18..2026-08-25 gap the cached parquet does not cover).
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

MAIN_TREE = Path("/Users/earlignacio/Documents/Claude/Projects/Prediction Markets")
WORKTREE = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(MAIN_TREE / "src"))

from prediction_market_bot.c1_signal_ingestion.mlb_ingestion import (  # noqa: E402
    DEFAULT_REQUEST_DELAY_S,
    MLBIngestionClient,
)
from prediction_market_bot.c1_signal_ingestion.mlb_team_stats_store import (  # noqa: E402
    MLBTeamStatsStore,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402

CACHE_DIR = WORKTREE / "exp_output" / "MLB" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
GAP_CACHE = CACHE_DIR / "exp022_gap_games_2026-07-15_2026-08-25.parquet"
LOG_PATH = WORKTREE / "exp_output" / "MLB" / "exp022_ingestion.jsonl"

EDGE_THRESHOLD = 0.010
Z_ALPHA_05 = 1.6448536269514722  # one-sided alpha=.05
Z_POWER_95 = 1.6448536269514722  # power=.95 -> z_(1-beta)=z_.95


# ---------------------------------------------------------------------------
# Step 1a -- team game log (existing cache + gap-fill fetch, LL-009 compliant)
# ---------------------------------------------------------------------------

def load_team_games() -> pd.DataFrame:
    base = pd.read_parquet(MAIN_TREE / "exp_output" / "MLB" / "cache" / "completed_games_2026.parquet")
    print(f"[games] base cache: {len(base)} rows, {base['game_date'].min()} .. {base['game_date'].max()}")

    if GAP_CACHE.exists():
        gap = pd.read_parquet(GAP_CACHE)
        print(f"[games] gap cache hit: {len(gap)} rows")
    else:
        logger = AuditLogger(str(LOG_PATH), min_severity="INFO")
        client = MLBIngestionClient(
            logger=logger, snapshot_id="EXP022-GAPFILL", request_delay=DEFAULT_REQUEST_DELAY_S
        )
        ok, gap = client.fetch_completed_games("2026-07-15", "2026-08-25")
        print(f"[games] gap fetch ok={ok} rows={len(gap) if gap is not None else 0}")
        if gap is not None and not gap.empty:
            gap.to_parquet(GAP_CACHE)

    combined = pd.concat([base, gap], ignore_index=True).drop_duplicates(subset=["game_id"])
    combined["game_date"] = pd.to_datetime(combined["game_date"]).dt.date.astype(str)
    combined = combined.sort_values("game_date").reset_index(drop=True)
    print(f"[games] combined: {len(combined)} rows, {combined['game_date'].min()} .. {combined['game_date'].max()}")
    return combined


# ---------------------------------------------------------------------------
# Step 1b -- verify get_opp_runs_scored / get_opp_runs_allowed on real data
# ---------------------------------------------------------------------------

def verify_store(store: MLBTeamStatsStore) -> None:
    print(f"[store] teams loaded: {len(store)} -> {store.teams_loaded[:5]}...")
    checks = [("NYY", "2026-08-15"), ("LAD", "2026-08-10"), ("BOS", "2026-08-20"), ("HOU", "2026-08-05")]
    ok = 0
    for team, d in checks:
        rs = store.get_opp_runs_scored(team, d)
        ra = store.get_opp_runs_allowed(team, d)
        print(f"[store] {team} as_of {d}: runs_scored_l10={rs} runs_allowed_l10={ra}")
        if rs is not None and ra is not None:
            ok += 1
    if ok == 0:
        raise RuntimeError("get_opp_runs_scored/get_opp_runs_allowed returned None on every sample check -- "
                            "store is not usable, aborting per task Step 1 instruction.")
    print(f"[store] VERIFIED: {ok}/{len(checks)} sample checks returned usable series.")


# ---------------------------------------------------------------------------
# Step 0(b) -- pregame filter + Step 0(a) -- closing-snapshot benchmark
# ---------------------------------------------------------------------------

def parse_ticker(ticker: str, event_ticker: str) -> tuple[str, str, str] | None:
    # event_ticker: KXMLBTOTAL-26AUGDDHHMMAWAYHOME  (AWAY/HOME = 3-letter codes, concatenated)
    suffix = ticker[len(event_ticker):]  # "-14"
    if not suffix.startswith("-"):
        return None
    n_str = suffix[1:]
    if not n_str.isdigit():
        return None
    core = event_ticker[len("KXMLBTOTAL-"):]  # 26AUGDDHHMM + AWAYHOME
    if len(core) < 11 + 6:
        return None
    teams = core[11:]
    if len(teams) != 6:
        return None
    away, home = teams[:3], teams[3:]
    return away, home, n_str


def load_totals_rows() -> list[dict]:
    files = sorted((MAIN_TREE / "exp_output" / "PRICE_ARCHIVE").glob("prices_2026-08-*.jsonl"))
    files = [f for f in files if f.suffix == ".jsonl"]  # drop .BROKEN_FIRSTRUN
    total_kxmlbtotal_rows = 0
    dropped_postgame = 0
    kept_rows: list[dict] = []
    for fp in files:
        with fp.open() as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("series_ticker") != "KXMLBTOTAL":
                    continue
                total_kxmlbtotal_rows += 1
                parsed = parse_ticker(r["ticker"], r["event_ticker"])
                if parsed is None:
                    continue
                away, home, n_str = parsed
                try:
                    close_time = datetime.strptime(r["close_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    run_ts = datetime.strptime(r["run_ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                except (KeyError, ValueError):
                    continue
                game_start = close_time - timedelta(hours=72)
                if run_ts >= game_start:
                    dropped_postgame += 1
                    continue
                kept_rows.append({
                    "run_ts": run_ts,
                    "event_ticker": r["event_ticker"],
                    "ticker": r["ticker"],
                    "away": away,
                    "home": home,
                    "n": int(n_str),
                    "floor_strike": int(n_str) - 0.5,
                    "game_start": game_start,
                    "game_date": game_start.date().isoformat(),
                    "yes_mid": r.get("yes_mid"),
                    "status": r.get("status"),
                })
    print(f"[filter] KXMLBTOTAL rows total={total_kxmlbtotal_rows} "
          f"dropped(run_ts>=game_start-filter)={dropped_postgame} "
          f"kept(pregame)={len(kept_rows)}")

    # Step 0(a): benchmark = closing pregame snapshot per (ticker) -> max run_ts among kept rows.
    latest: dict[str, dict] = {}
    for row in kept_rows:
        k = row["ticker"]
        if k not in latest or row["run_ts"] > latest[k]["run_ts"]:
            latest[k] = row
    closing_rows = list(latest.values())
    print(f"[filter] distinct (event,threshold) tickers with a closing pregame snapshot: {len(closing_rows)}")
    return closing_rows, total_kxmlbtotal_rows, dropped_postgame


# ---------------------------------------------------------------------------
# Outcome store join
# ---------------------------------------------------------------------------

def load_outcomes() -> dict[str, dict]:
    path = MAIN_TREE / "logs" / "t4_mlb_totals_outcome_store.jsonl"
    out: dict[str, dict] = {}
    with path.open() as fh:
        for line in fh:
            rec = json.loads(line)
            if rec.get("resolved"):
                out[rec["event_ticker"]] = rec
    print(f"[outcomes] resolved events: {len(out)}")
    return out


# ---------------------------------------------------------------------------
# Poisson model (mean-only blend of team offense L10 / opponent defense L10)
# ---------------------------------------------------------------------------

def poisson_pmf(k: int, mu: float) -> float:
    if mu <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-mu) * mu**k / math.factorial(k)


def poisson_p_ge(n_min: int, mu: float, cap: int = 40) -> float:
    return 1.0 - sum(poisson_pmf(k, mu) for k in range(0, n_min))


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
        model_p = poisson_p_ge(row["n"], mu_total)
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

    # ---- Gate 2.3: selected subset, EV per bet, aggregated to GAME level ----
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
    print(f"[gate2.3] qualifying bets (row-level)={n_bets} qualifying GAMES (independent unit)={clean_n}")

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

    print(f"[gate2.3] mean P&L/bet(game-level)={mu} sd={sigma} n*={n_star} clean_n={clean_n}")
    print(f"[gate2.3] VERDICT = {verdict}")

    # ---- Secondary: paired per-game delta-Brier (descriptive, not a gate) ----
    # One line per game: the closest-to-money line at closing.
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
        deltas.append(market_brier - model_brier)  # positive = model better

    if len(deltas) >= 2:
        d_mean = statistics.mean(deltas)
        d_sd = statistics.stdev(deltas)
        se = d_sd / math.sqrt(len(deltas))
        ci_lo, ci_hi = d_mean - 1.96 * se, d_mean + 1.96 * se
        power = _normal_power(d_mean, d_sd, len(deltas), alpha=0.05)
        print(f"[secondary] paired delta-Brier n={len(deltas)} mean={d_mean:.5f} "
              f"95%CI=({ci_lo:.5f},{ci_hi:.5f}) measured_power={power:.3f}")
    else:
        print(f"[secondary] insufficient games for delta-Brier: n={len(deltas)}")

    result = {
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
        "secondary_delta_brier_n": len(deltas),
        "secondary_delta_brier_mean": statistics.mean(deltas) if len(deltas) >= 2 else None,
        "secondary_delta_brier_ci": [ci_lo, ci_hi] if len(deltas) >= 2 else None,
        "secondary_measured_power": power if len(deltas) >= 2 else None,
    }
    out_path = WORKTREE / "exp_output" / "MLB" / "exp022_gate23_result.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, default=str))
    print(f"[out] wrote {out_path}")
    return 0


def _blend(a: float | None, b: float | None) -> float | None:
    if a is None or b is None:
        return None
    return (a + b) / 2.0


def _normal_power(mean: float, sd: float, n: int, alpha: float = 0.05) -> float:
    if sd <= 0:
        return 1.0 if mean > 0 else 0.0
    se = sd / math.sqrt(n)
    z = mean / se
    z_crit = Z_ALPHA_05
    # power = P(Z > z_crit - z) under standard normal
    from math import erf
    def norm_cdf(x: float) -> float:
        return 0.5 * (1 + erf(x / math.sqrt(2)))
    return 1 - norm_cdf(z_crit - z)


if __name__ == "__main__":
    raise SystemExit(main())
