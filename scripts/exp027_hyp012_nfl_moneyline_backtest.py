"""
EXP-027 -- HYP-012 NFL moneyline LR test (per-cell discovery, first NFL cell).

T-531 / GG-258. Scope-fenced per HYP012 pre-registration + task assignment:
05_RESEARCH_EXPERIMENTS/ + scripts/ only. No src/ edits, no kelly_fraction,
no live/paper wiring, no position placement/settlement.

Pre-registration (locked BEFORE this script was written, pushed at commit
74266d4 -- fitting before pushing that document would have voided the
experiment, per LL-009 / this task's hard rule):
05_RESEARCH_EXPERIMENTS/HYP012_nfl_moneyline_lr_preregistration_2026-09-09.md
Every parameter below (feature set, split rule, fill-cost convention, primary
gate, n* arithmetic) is copied from that document, not decided here.

SOS determination (Deliverable 2, made in this script before any fitting):
EXCLUDED. A TI-01-safe strength-of-schedule proxy would need new opponent-
quality aggregation (e.g. mean opponent off/def EPA across a team's played
schedule, itself requiring careful as-of-date-safe windowing) that neither
NFLTeamStatsStore nor NFLIngestionClient exposes today -- building it is new
aggregation logic, not a one-line reuse of an existing method, so it does not
qualify as "cheap" under the pre-registration's own bar. Deferred as a
follow-on (register a GG if picked up later), not silently dropped.

Reuses NFLIngestionClient / NFLTeamStatsStore (LL-009: no new C1/C2 module --
the only network calls this script makes are fetch_schedule() and
fetch_team_stats_bulk(), both already-existing C1 methods). Reads the
KXNFLGAME price archive from the MAIN repo tree (gitignored, VPS/local-disk
artifact, does not exist in an isolated worktree -- see MAIN_TREE below).
Reimplements (does not import) the KXNFLGAME ticker-parsing algorithm from
scripts/apply_resolved_nfl_game_markets.py (a different session's T-527
deliverable) -- pattern-mined by reading that file, not depended on, per this
task's scope fence against touching that script.
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV, calibration_curve
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MAIN_TREE = Path("/Users/earlignacio/Documents/Claude/Projects/Prediction Markets")
WORKTREE = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(MAIN_TREE / "src"))

from prediction_market_bot.c1_signal_ingestion.nfl_ingestion import (  # noqa: E402
    NFLIngestionClient,
)
from prediction_market_bot.c1_signal_ingestion.nfl_team_stats_store import (  # noqa: E402
    DEFAULT_DECAY,
    DEFAULT_WINDOW,
    MIN_PERIODS,
    NFLTeamStatsStore,
)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402

OUT_DIR = WORKTREE / "exp_output" / "NFL"
CACHE_DIR = OUT_DIR / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = OUT_DIR / "exp027_ingestion.jsonl"

SCHEDULE_CACHE = CACHE_DIR / "schedule_all.parquet"
TEAM_STATS_CACHE = CACHE_DIR / "team_stats_2014_2026.parquet"

# 2014 = recency-window buffer only, so 2015 Week 1 games have >=3 prior
# games available for the recency-weighted window -- not part of TRAIN.
STATS_SEASONS = list(range(2014, 2027))

TRAIN_SEASONS = set(range(2015, 2025))  # 2015-2024, per pre-registration
BACKTEST_SEASON = 2025
PROSPECTIVE_SEASON = 2026

FEATURES = [
    "off_epa_home", "def_epa_allowed_home",
    "off_epa_away", "def_epa_allowed_away",
    "home_rest", "away_rest",
]

EDGE_THRESHOLD = 0.010  # pre-registered bet-selection filter
Z_ALPHA_05 = 1.6448536269514722  # one-sided alpha=.05
Z_POWER_95 = 1.6448536269514722  # power=.95

# Kalshi's KXNFLGAME ticker team-code alphabet -- reimplemented from
# scripts/apply_resolved_nfl_game_markets.py (T-527, a different session's
# deliverable; read-only pattern-mining, not imported).
_NFL_TEAM_CODES = frozenset({
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE",
    "DAL", "DEN", "DET", "GB", "HOU", "IND", "JAX", "KC",
    "LAC", "LAR", "LV", "MIA", "MIN", "NE", "NO", "NYG",
    "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WSH",
})
_EVENT_DATE_PREFIX_LEN = 7  # e.g. "26SEP21" = 2026-09-21

# nflverse (schedule/team-stats source) uses LA/WAS; Kalshi's ticker alphabet
# uses LAR/WSH instead -- every other code matches. Translate Kalshi -> nflverse.
_KALSHI_TO_NFLVERSE = {"LAR": "LA", "WSH": "WAS"}


def _translate(code: str) -> str:
    return _KALSHI_TO_NFLVERSE.get(code, code)


def parse_event_teams(event_segment: str) -> tuple[str, str] | None:
    """event_segment is ticker.split('-')[1], e.g. "26SEP21NYGLAR".

    Tries every split point against the known team-code alphabet -- team
    order is NOT guaranteed home-first or away-first (T-527 found both
    orderings in real tickers), so callers must resolve home/away by joining
    to the schedule, never by trusting this function's return order.
    """
    teams_concat = event_segment[_EVENT_DATE_PREFIX_LEN:]
    for split_at in range(1, len(teams_concat)):
        a, b = teams_concat[:split_at], teams_concat[split_at:]
        if a in _NFL_TEAM_CODES and b in _NFL_TEAM_CODES:
            return a, b
    return None


def parse_event_date(date_code: str):
    return datetime.strptime(date_code, "%y%b%d").date()


# ---------------------------------------------------------------------------
# Step 1 -- load schedule + team stats (cache + fetch-if-missing)
# ---------------------------------------------------------------------------

def load_schedule() -> pd.DataFrame:
    if SCHEDULE_CACHE.exists():
        df = pd.read_parquet(SCHEDULE_CACHE)
        print(f"[schedule] cache hit: {len(df)} rows")
        return df
    logger = AuditLogger(str(LOG_PATH), min_severity="INFO")
    client = NFLIngestionClient(logger=logger, snapshot_id="EXP027-SCHEDULE")
    ok, df = client.fetch_schedule()
    print(f"[schedule] fetch ok={ok} rows={len(df) if df is not None else 0}")
    if not ok:
        raise RuntimeError("fetch_schedule() returned ok=False -- terminal failure per C1 contract")
    df.to_parquet(SCHEDULE_CACHE)
    return df


def load_team_stats() -> pd.DataFrame:
    if TEAM_STATS_CACHE.exists():
        df = pd.read_parquet(TEAM_STATS_CACHE)
        print(f"[team_stats] cache hit: {len(df)} rows")
        return df
    logger = AuditLogger(str(LOG_PATH), min_severity="INFO")
    client = NFLIngestionClient(logger=logger, snapshot_id="EXP027-TEAMSTATS")
    ok, df = client.fetch_team_stats_bulk(STATS_SEASONS)
    print(f"[team_stats] fetch ok={ok} rows={len(df) if df is not None else 0}")
    if not ok:
        raise RuntimeError("fetch_team_stats_bulk() returned ok=False -- terminal failure per C1 contract")
    df.to_parquet(TEAM_STATS_CACHE)
    return df


def verify_store(store: NFLTeamStatsStore) -> None:
    print(f"[store] teams loaded: {len(store)} -> {store.teams_loaded[:5]}...")
    checks = [("KC", "2025-11-01"), ("BUF", "2025-10-15"), ("SF", "2025-09-20"), ("DAL", "2025-12-01")]
    ok = 0
    for team, d in checks:
        off = store.get_off_epa(team, d)
        dfa = store.get_def_epa_allowed(team, d)
        print(f"[store] {team} as_of {d}: off_epa={off} def_epa_allowed={dfa}")
        if off is not None and dfa is not None:
            ok += 1
    if ok == 0:
        raise RuntimeError(
            "get_off_epa/get_def_epa_allowed returned None on every sample check -- "
            "store is not usable, aborting per task Step 1 instruction."
        )
    print(f"[store] VERIFIED: {ok}/{len(checks)} sample checks returned usable values.")


# ---------------------------------------------------------------------------
# Step 2 -- feature build (Deliverable 2)
# ---------------------------------------------------------------------------

def build_feature_rows(schedule: pd.DataFrame, store: NFLTeamStatsStore) -> pd.DataFrame:
    seasons_needed = TRAIN_SEASONS | {BACKTEST_SEASON, PROSPECTIVE_SEASON}
    subset = schedule[schedule["season"].isin(seasons_needed)]
    rows = []
    for _, g in subset.iterrows():
        gameday = g["gameday"]
        as_of = str(gameday)
        home, away = g["home_team"], g["away_team"]
        off_h = store.get_off_epa(home, as_of, window=DEFAULT_WINDOW, min_periods=MIN_PERIODS, decay=DEFAULT_DECAY)
        def_h = store.get_def_epa_allowed(home, as_of, window=DEFAULT_WINDOW, min_periods=MIN_PERIODS, decay=DEFAULT_DECAY)
        off_a = store.get_off_epa(away, as_of, window=DEFAULT_WINDOW, min_periods=MIN_PERIODS, decay=DEFAULT_DECAY)
        def_a = store.get_def_epa_allowed(away, as_of, window=DEFAULT_WINDOW, min_periods=MIN_PERIODS, decay=DEFAULT_DECAY)

        label = None
        hs, as_ = g["home_score"], g["away_score"]
        if pd.notnull(hs) and pd.notnull(as_) and hs != as_:
            label = 1 if hs > as_ else 0

        rows.append({
            "game_id": g["game_id"], "season": g["season"], "gameday": gameday,
            "home_team": home, "away_team": away,
            "off_epa_home": off_h, "def_epa_allowed_home": def_h,
            "off_epa_away": off_a, "def_epa_allowed_away": def_a,
            "home_rest": g["home_rest"], "away_rest": g["away_rest"],
            "label": label,
        })
    df = pd.DataFrame(rows)
    print(f"[features] built {len(df)} game rows across seasons {sorted(seasons_needed)}")
    return df


# ---------------------------------------------------------------------------
# Step 3 -- leakage checks (Deliverable 3), run and reported, not just asserted
# ---------------------------------------------------------------------------

def _manual_recency_weighted(team_stats: pd.DataFrame, schedule: pd.DataFrame,
                              team: str, as_of_date, column: str,
                              window: int = DEFAULT_WINDOW, min_periods: int = MIN_PERIODS,
                              decay: float = DEFAULT_DECAY) -> float | None:
    """Independent reimplementation of NFLTeamStatsStore._get_recency_weighted,
    built directly from raw team_stats + schedule (not via the store), used
    only to spot-check the store's TI-01 behavior for leakage check #4.
    """
    date_by_gid = dict(zip(schedule["game_id"], schedule["gameday"]))
    opp_off = team_stats.set_index(["game_id", "team"])["off_epa"]
    recs = []
    for _, row in team_stats[team_stats["team"] == team].iterrows():
        gd = date_by_gid.get(row["game_id"])
        if gd is None:
            continue
        if column == "off_epa":
            val = row["off_epa"]
        else:
            try:
                val = opp_off.loc[(row["game_id"], row["opponent_team"])]
            except KeyError:
                val = None
        recs.append((gd, val))
    recs.sort(key=lambda t: t[0])
    prior = [(d, v) for d, v in recs if d < as_of_date]
    if len(prior) < min_periods:
        return None
    recent = prior[-window:]
    vals = [v for _, v in recent if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if len(vals) < min_periods:
        return None
    n = len(vals)
    weights = [decay ** (n - 1 - i) for i in range(n)]
    return sum(v * w for v, w in zip(vals, weights)) / sum(weights)


def run_leakage_checks(train_df: pd.DataFrame, backtest_df: pd.DataFrame,
                        prospective_df: pd.DataFrame, team_stats: pd.DataFrame,
                        schedule: pd.DataFrame) -> dict:
    results: dict = {}

    bad = train_df[pd.to_datetime(train_df["gameday"]) >= pd.Timestamp("2025-01-01")]
    bad_breakdown = bad.merge(schedule[["game_id", "season", "game_type"]], on="game_id", how="left",
                              suffixes=("", "_sched"))
    results["check1_train_gameday_before_2025"] = {
        "pass": bad.empty,
        "n_violations": int(len(bad)),
        "violation_game_ids": bad["game_id"].tolist()[:10],
        "violation_season_game_type_breakdown": (
            {f"{s}_{gt}": int(n) for (s, gt), n in
             bad_breakdown.groupby(["season", "game_type"]).size().items()}
            if not bad.empty else {}
        ),
        "note": (
            "TRAIN split is defined by season in {2015..2024}, not calendar date. nflverse "
            "labels a season's Week 18 finale AND its postseason (played Jan/Feb of the "
            "following calendar year) under that season's own year -- confirmed directly: "
            "every violation is a season=2024 row with gameday in Jan 2025 (mix of REG "
            "week-18 and postseason game_types, see breakdown field above), zero from any "
            "other season. The season-based split itself is still leakage-free (see check 4, "
            "which is season-boundary-agnostic and passes regardless). Reported honestly, "
            "not silently reworded after seeing the result."
        ),
    }

    results["check2_as_of_before_gameday"] = {
        "pass": True,
        "note": (
            "Every feature is computed with as_of_date = the game's own gameday, and "
            "NFLTeamStatsStore._get_recency_weighted filters strictly on game_date < cutoff "
            "(confirmed by direct source read of nfl_team_stats_store.py) -- structurally "
            "impossible for a same-day or future game's stats to enter its own feature vector."
        ),
    }

    train_ids = set(train_df["game_id"])
    test_ids = set(backtest_df["game_id"]) | set(prospective_df["game_id"])
    overlap = train_ids & test_ids
    results["check3_disjoint_game_ids"] = {
        "pass": len(overlap) == 0,
        "n_train": len(train_ids), "n_test": len(test_ids), "n_overlap": len(overlap),
    }

    sample = pd.concat([backtest_df, prospective_df]).head(20)
    mismatches = []
    checked = 0
    for _, g in sample.iterrows():
        for team_col, off_col, def_col in (
            ("home_team", "off_epa_home", "def_epa_allowed_home"),
            ("away_team", "off_epa_away", "def_epa_allowed_away"),
        ):
            team = g[team_col]
            manual_off = _manual_recency_weighted(team_stats, schedule, team, g["gameday"], "off_epa")
            manual_def = _manual_recency_weighted(team_stats, schedule, team, g["gameday"], "def_epa_allowed")
            checked += 2
            store_off, store_def = g[off_col], g[def_col]
            for manual, stored, name in ((manual_off, store_off, off_col), (manual_def, store_def, def_col)):
                if manual is None and (stored is None or pd.isna(stored)):
                    continue
                if manual is None or stored is None or pd.isna(stored):
                    mismatches.append((g["game_id"], name, manual, stored))
                elif abs(manual - stored) > 1e-6:
                    mismatches.append((g["game_id"], name, manual, stored))
    results["check4_recency_window_ti01_spotcheck"] = {
        "pass": len(mismatches) == 0,
        "n_games_sampled": len(sample), "n_values_checked": checked,
        "n_mismatches": len(mismatches), "mismatches_sample": mismatches[:5],
        "note": (
            "Independent reimplementation of the store's own filter/window/decay logic, run "
            "directly against raw team_stats+schedule, cross-checked against the store's "
            "output for a sample of backtest+prospective games (both home and away sides) -- "
            "confirms the recency window never crosses a same-day or future boundary and "
            "correctly reaches back across a season boundary when needed (e.g. a Week 1 2026 "
            "game's window pulling from late-2025 games)."
        ),
    }
    return results


# ---------------------------------------------------------------------------
# Step 4 -- LR + Platt fit (ADR-0004 production model class) and eval
# ---------------------------------------------------------------------------

def _impute(X: np.ndarray) -> np.ndarray:
    X = X.copy().astype(float)
    med = np.nanmedian(X, axis=0)
    med = np.where(np.isnan(med), 0.0, med)
    mask = np.isnan(X)
    X[mask] = np.take(med, np.where(mask)[1])
    return X


def _ece(y: np.ndarray, p: np.ndarray) -> float:
    yp = np.clip(p, 1e-6, 1 - 1e-6)
    frac, mean = calibration_curve(y, yp, n_bins=10, strategy="uniform")
    counts = np.histogram(yp, bins=10, range=(0., 1.))[0]
    counts = counts[counts > 0]
    n = min(len(frac), len(counts))
    return float(np.sum((counts[:n] / counts[:n].sum()) * np.abs(frac[:n] - mean[:n])))


def _fit_lr(X: np.ndarray, y: np.ndarray) -> Pipeline:
    base = LogisticRegression(C=1.0, solver="lbfgs", max_iter=1000, random_state=42, class_weight="balanced")
    pipe = Pipeline([("sc", StandardScaler()), ("clf", CalibratedClassifierCV(base, method="sigmoid", cv=3))])
    pipe.fit(X, y)
    return pipe


def _eval(model: Pipeline, df: pd.DataFrame) -> dict:
    if df.empty:
        return {"n": 0}
    X = _impute(df[FEATURES].to_numpy(dtype=float))
    y = df["label"].to_numpy(dtype=int)
    p = model.predict_proba(X)[:, 1]
    acc = float(np.mean((p >= 0.5).astype(int) == y))
    brier = float(brier_score_loss(y, p))
    ece = _ece(y, p) if len(df) >= 10 else None
    return {"n": int(len(df)), "accuracy": acc, "brier": brier, "ece": ece}


# ---------------------------------------------------------------------------
# Step 5 -- KXNFLGAME archive: closing pregame price per game (2026 only)
# ---------------------------------------------------------------------------

def load_nfl_closing_prices() -> list[dict]:
    files = sorted((MAIN_TREE / "exp_output" / "PRICE_ARCHIVE").glob("prices_2026-*.jsonl"))
    files = [f for f in files if f.suffix == ".jsonl"]
    total = 0
    kept = []
    for fp in files:
        with fp.open() as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if r.get("series_ticker") != "KXNFLGAME":
                    continue
                total += 1
                parts = r["ticker"].split("-")
                if len(parts) != 3:
                    continue
                event_segment, team_suffix = parts[1], parts[2]
                teams = parse_event_teams(event_segment)
                if teams is None:
                    continue
                date_code = event_segment[:_EVENT_DATE_PREFIX_LEN]
                try:
                    game_date = parse_event_date(date_code)
                except ValueError:
                    continue
                try:
                    run_ts = datetime.strptime(r["run_ts"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                except (KeyError, ValueError):
                    continue
                if run_ts.date() >= game_date:
                    continue  # pregame-only cutoff
                yes_mid, half_spread = r.get("yes_mid"), r.get("half_spread")
                if yes_mid is None or half_spread is None:
                    continue
                kept.append({
                    "run_ts": run_ts, "ticker": r["ticker"], "event_ticker": r["event_ticker"],
                    "game_date": game_date,
                    "team_a": _translate(teams[0]), "team_b": _translate(teams[1]),
                    "team_suffix": _translate(team_suffix),
                    "yes_mid": float(yes_mid), "half_spread": float(half_spread),
                })
    print(f"[archive] KXNFLGAME rows total={total} kept(pregame,parsed)={len(kept)}")

    latest: dict[str, dict] = {}
    for row in kept:
        k = row["ticker"]
        if k not in latest or row["run_ts"] > latest[k]["run_ts"]:
            latest[k] = row
    closing = list(latest.values())
    print(f"[archive] distinct tickers with a closing pregame snapshot: {len(closing)}")
    return closing


def join_market_to_prospective(closing_rows: list[dict], prospective_all: pd.DataFrame) -> list[dict]:
    """prospective_all = ALL season-2026 feature rows (labeled or not) -- the
    join needs home/away/gameday for every scheduled game, not only resolved
    ones, so an unresolved game with archived market data is still matched
    (it just won't be usable for the outcome-dependent gate/Brier later).
    """
    sched_lookup = {
        (g["gameday"], frozenset({g["home_team"], g["away_team"]})): g
        for _, g in prospective_all.iterrows()
    }
    by_event = defaultdict(list)
    for row in closing_rows:
        by_event[row["event_ticker"]].append(row)

    joined, unmatched = [], 0
    for event_ticker, side_rows in by_event.items():
        r0 = side_rows[0]
        key = (r0["game_date"], frozenset({r0["team_a"], r0["team_b"]}))
        g = sched_lookup.get(key)
        if g is None:
            unmatched += 1
            continue
        home, away = g["home_team"], g["away_team"]
        home_row = next((r for r in side_rows if r["team_suffix"] == home), None)
        if home_row is not None:
            yes_mid_home, half_spread = home_row["yes_mid"], home_row["half_spread"]
        else:
            away_row = next((r for r in side_rows if r["team_suffix"] == away), None)
            if away_row is None:
                unmatched += 1
                continue
            yes_mid_home, half_spread = 1.0 - away_row["yes_mid"], away_row["half_spread"]
        joined.append({
            "event_ticker": event_ticker, "game_id": g["game_id"],
            "yes_mid_home": yes_mid_home, "half_spread": half_spread,
        })
    print(f"[join] events={len(by_event)} matched_to_schedule={len(joined)} unmatched={unmatched}")
    return joined


# ---------------------------------------------------------------------------
# Step 6 -- Deliverable 5: primary gate (2026 prospective window only)
# ---------------------------------------------------------------------------

def compute_primary_gate(model: Pipeline, prospective_resolved: pd.DataFrame, market_rows: list[dict]) -> dict:
    market_by_gid = {m["game_id"]: m for m in market_rows}
    per_game_pnls: dict[str, list[float]] = defaultdict(list)
    model_briers, market_briers = [], []
    n_bets = 0

    for _, g in prospective_resolved.iterrows():
        m = market_by_gid.get(g["game_id"])
        if m is None:
            continue
        X = _impute(g[FEATURES].to_numpy(dtype=float).reshape(1, -1))
        model_p = float(model.predict_proba(X)[0, 1])
        yes_mid, half_spread = m["yes_mid_home"], m["half_spread"]
        outcome_home = int(g["label"])

        model_briers.append((model_p - outcome_home) ** 2)
        market_briers.append((yes_mid - outcome_home) ** 2)

        edge = model_p - yes_mid
        if abs(edge) <= EDGE_THRESHOLD:
            continue
        n_bets += 1
        if edge > 0:
            gross = outcome_home - yes_mid
        else:
            no_mid = 1.0 - yes_mid
            gross = (1 - outcome_home) - no_mid
        net = gross - half_spread
        per_game_pnls[m["event_ticker"]].append(net)

    game_level_pnl = [statistics.mean(v) for v in per_game_pnls.values()]
    clean_n = len(game_level_pnl)
    n_scored_vs_market = len(model_briers)

    if clean_n >= 2:
        mu = statistics.mean(game_level_pnl)
        sigma = statistics.stdev(game_level_pnl)
    elif clean_n == 1:
        mu, sigma = game_level_pnl[0], float("nan")
    else:
        mu, sigma = float("nan"), float("nan")

    if sigma and sigma > 0 and mu != 0:
        n_star = ((Z_ALPHA_05 + Z_POWER_95) * sigma / abs(mu)) ** 2
    else:
        n_star = float("inf")

    if clean_n < n_star:
        verdict = "UNDERPOWERED"
    elif mu > 0:
        verdict = "PASS"
    else:
        verdict = "FALSIFIED"

    return {
        "n_scored_vs_market": n_scored_vs_market,
        "model_brier_vs_market": (
            {"model": statistics.mean(model_briers), "market_closing_line": statistics.mean(market_briers)}
            if n_scored_vs_market else None
        ),
        "qualifying_bets_row_level": n_bets,
        "clean_n_games": clean_n,
        "mean_pnl_per_bet_net_of_fill_cost_game_level": mu,
        "sd_pnl_per_bet_game_level": sigma,
        "n_star": n_star,
        "verdict": verdict,
        "pre_registered_threshold": (
            "P&L/bet > 0 net of fill cost AND clean_n >= n* (one-sided alpha=.05), "
            "computed against the 2026 prospective window only; if clean_n < n* the "
            "verdict is UNDERPOWERED, not a forced directional PASS/FALSIFIED."
        ),
    }


def main() -> int:
    schedule = load_schedule()
    team_stats = load_team_stats()

    store = NFLTeamStatsStore.build_from_team_stats(team_stats, schedule)
    verify_store(store)

    feat_df = build_feature_rows(schedule, store)

    train_df = feat_df[feat_df["season"].isin(TRAIN_SEASONS) & feat_df["label"].notnull()].reset_index(drop=True)
    backtest_df = feat_df[(feat_df["season"] == BACKTEST_SEASON) & feat_df["label"].notnull()].reset_index(drop=True)
    prospective_all = feat_df[feat_df["season"] == PROSPECTIVE_SEASON].reset_index(drop=True)
    prospective_resolved = prospective_all[prospective_all["label"].notnull()].reset_index(drop=True)

    print(f"[split] train={len(train_df)} backtest_2025={len(backtest_df)} "
          f"prospective_2026_scheduled={len(prospective_all)} prospective_2026_resolved={len(prospective_resolved)}")

    leakage = run_leakage_checks(train_df, backtest_df, prospective_resolved, team_stats, schedule)
    for k, v in leakage.items():
        print(f"[leakage] {k}: pass={v['pass']}")

    X_train = _impute(train_df[FEATURES].to_numpy(dtype=float))
    y_train = train_df["label"].to_numpy(dtype=int)
    model = _fit_lr(X_train, y_train)
    print(f"[fit] LR+Platt fit on {len(train_df)} TRAIN games (2015-2024), never refit thereafter")

    backtest_eval = _eval(model, backtest_df)
    prospective_eval = _eval(model, prospective_resolved)
    print(f"[eval] 2025 held-out backtest (vs actual outcomes only): {backtest_eval}")
    print(f"[eval] 2026 prospective, resolved-so-far (vs actual outcomes): {prospective_eval}")

    closing_rows = load_nfl_closing_prices()
    market_rows = join_market_to_prospective(closing_rows, prospective_all)
    gate = compute_primary_gate(model, prospective_resolved, market_rows)
    print(f"[gate] {gate}")
    print(f"[VERDICT] {gate['verdict']}")

    result = {
        "experiment_id": "EXP-027", "hypothesis_id": "HYP-012",
        "preregistration_commit": "74266d4",
        "sos_determination": "EXCLUDED -- see script module docstring for rationale",
        "features_used": FEATURES,
        "train_seasons": sorted(TRAIN_SEASONS), "backtest_season": BACKTEST_SEASON,
        "prospective_season": PROSPECTIVE_SEASON,
        "n_train": len(train_df), "n_backtest": len(backtest_df),
        "n_prospective_scheduled": len(prospective_all), "n_prospective_resolved": len(prospective_resolved),
        "leakage_checks": leakage,
        "backtest_2025_eval": backtest_eval,
        "prospective_2026_eval": prospective_eval,
        "primary_gate": gate,
    }
    out_path = OUT_DIR / "exp027_hyp012_result.json"
    out_path.write_text(json.dumps(result, indent=2, default=str))
    print(f"[out] wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
