"""T-581 -- EXP-027 EPA-splits CANDIDATE, offline evaluation only.

Incumbent (unchanged, stays default): 6 features (aggregate off_epa /
def_epa_allowed per side + rest).  Candidate: same pipeline (StandardScaler +
CalibratedClassifierCV sigmoid cv=3 over LogisticRegression C=1 balanced,
random_state 42 -- ADR-0004 model class NOT redesigned) with the passing/rushing
EPA splits added.  The candidate is wired into NO run path.

Feature sets
  incumbent : 6  (agg off/def per side + rest)
  candidate : 14 (incumbent 6 + pass/rush/def_pass/def_rush per side)  PRIMARY
  splits_only: 10 (8 splits + rest; drops the aggregates) -- collinearity
               ablation, since off_epa = passing_epa + rushing_epa exactly.

Evaluation: PRIMARY = train 2015-2024, hold out season 2025 (temporal, same
split as the incumbent's pre-registered backtest).  SECONDARY = rolling-origin,
train 2015..s-1, test s, for s in 2020..2025.  Paired bootstrap over games.
CLOSING LINE = 2026 Kalshi KXNFLGAME archive only (small n).  The 42
quarantined NFL T1 rows (GG-302) are not read here.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

WORKTREE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKTREE / "src"))
# Import the worktree package FIRST so the incumbent script's MAIN_TREE
# sys.path insert cannot shadow it (sys.modules caches the worktree copy).
import prediction_market_bot.c1_signal_ingestion.nfl_team_stats_store as _store_mod  # noqa: E402,F401

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import brier_score_loss  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "exp027_incumbent", WORKTREE / "scripts" / "exp027_hyp012_nfl_moneyline_backtest.py")
inc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inc)

from prediction_market_bot.c1_signal_ingestion.nfl_ingestion import NFLIngestionClient  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nfl_team_stats_store import (  # noqa: E402
    DEFAULT_DECAY, DEFAULT_WINDOW, MIN_PERIODS, NFLTeamStatsStore)
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402

OUT = WORKTREE / "exp_output" / "NFL"
CACHE = OUT / "cache_t581"
CACHE.mkdir(parents=True, exist_ok=True)

INCUMBENT_FEATURES = list(inc.FEATURES)
SPLIT_FEATURES = [f"{k}_{s}" for s in ("home", "away")
                  for k in ("pass_epa", "rush_epa", "def_pass_epa_allowed", "def_rush_epa_allowed")]
CANDIDATE_FEATURES = INCUMBENT_FEATURES + SPLIT_FEATURES
SPLITS_ONLY_FEATURES = SPLIT_FEATURES + ["home_rest", "away_rest"]
SETS = {"incumbent": INCUMBENT_FEATURES, "candidate": CANDIDATE_FEATURES,
        "splits_only": SPLITS_ONLY_FEATURES}
N_BOOT = 2000
SEED = 20260929


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    sp, ts = CACHE / "schedule.parquet", CACHE / "team_stats_splits.parquet"
    logger = AuditLogger(str(CACHE / "ingest.jsonl"), min_severity="INFO")
    client = NFLIngestionClient(logger=logger, snapshot_id="T581-EPA-SPLITS")
    if sp.exists():
        sched = pd.read_parquet(sp)
    else:
        ok, sched = client.fetch_schedule()
        if not ok:
            raise RuntimeError("fetch_schedule failed")
        sched.to_parquet(sp)
    if ts.exists():
        stats = pd.read_parquet(ts)
    else:
        ok, stats = client.fetch_team_stats_bulk(inc.STATS_SEASONS, include_splits=True)
        if not ok:
            raise RuntimeError("fetch_team_stats_bulk failed")
        stats.to_parquet(ts)
    return sched, stats


def build_rows(sched: pd.DataFrame, store: NFLTeamStatsStore) -> pd.DataFrame:
    kw = dict(window=DEFAULT_WINDOW, min_periods=MIN_PERIODS, decay=DEFAULT_DECAY)
    seasons = set(range(2015, 2027))
    rows = []
    for _, g in sched[sched["season"].isin(seasons)].iterrows():
        as_of = str(g["gameday"])
        r = {"game_id": g["game_id"], "season": g["season"], "gameday": g["gameday"],
             "home_team": g["home_team"], "away_team": g["away_team"],
             "home_rest": g["home_rest"], "away_rest": g["away_rest"]}
        for side, team in (("home", g["home_team"]), ("away", g["away_team"])):
            r[f"off_epa_{side}"] = store.get_off_epa(team, as_of, **kw)
            r[f"def_epa_allowed_{side}"] = store.get_def_epa_allowed(team, as_of, **kw)
            r[f"pass_epa_{side}"] = store.get_pass_epa(team, as_of, **kw)
            r[f"rush_epa_{side}"] = store.get_rush_epa(team, as_of, **kw)
            r[f"def_pass_epa_allowed_{side}"] = store.get_def_pass_epa_allowed(team, as_of, **kw)
            r[f"def_rush_epa_allowed_{side}"] = store.get_def_rush_epa_allowed(team, as_of, **kw)
        hs, as_ = g["home_score"], g["away_score"]
        r["label"] = (1 if hs > as_ else 0) if (pd.notnull(hs) and pd.notnull(as_) and hs != as_) else None
        rows.append(r)
    return pd.DataFrame(rows)


def fit_predict(train: pd.DataFrame, test: pd.DataFrame, feats: list[str]) -> np.ndarray:
    Xtr = inc._impute(train[feats].to_numpy(dtype=float))
    # impute test with TRAIN medians (no test-set leakage into imputation)
    med = np.nanmedian(train[feats].to_numpy(dtype=float), axis=0)
    med = np.where(np.isnan(med), 0.0, med)
    Xte = test[feats].to_numpy(dtype=float)
    idx = np.where(np.isnan(Xte))
    Xte[idx] = np.take(med, idx[1])
    model = inc._fit_lr(Xtr, train["label"].to_numpy(dtype=int))
    return model.predict_proba(Xte)[:, 1]


def metrics(y: np.ndarray, p: np.ndarray) -> dict:
    return {"accuracy": float(np.mean((p >= 0.5) == y)),
            "brier": float(brier_score_loss(y, p)),
            "ece": float(inc._ece(y, p))}


def calib_curve(y: np.ndarray, p: np.ndarray) -> list[dict]:
    bins = np.linspace(0, 1, 6)  # 5 bins: n is small, 10 is mostly empty
    out = []
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (p >= lo) & ((p < hi) if hi < 1 else (p <= hi))
        out.append({"bin": f"[{lo:.1f},{hi:.1f})", "n": int(m.sum()),
                    "mean_pred": float(p[m].mean()) if m.any() else None,
                    "obs_rate": float(y[m].mean()) if m.any() else None})
    return out


def boot_ci(y, pa, pb, rng) -> dict:
    """Bootstrap 95% CI: each model's metric and the paired diff (b - a)."""
    n = len(y)
    res = {k: [] for k in ("a_acc", "a_brier", "a_ece", "b_acc", "b_brier", "b_ece")}
    for _ in range(N_BOOT):
        i = rng.integers(0, n, n)
        ma, mb = metrics(y[i], pa[i]), metrics(y[i], pb[i])
        for k, m in (("a", ma), ("b", mb)):
            res[f"{k}_acc"].append(m["accuracy"]); res[f"{k}_brier"].append(m["brier"]); res[f"{k}_ece"].append(m["ece"])
    ci = lambda v: [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]
    out = {}
    for m in ("acc", "brier", "ece"):
        a, b = np.array(res[f"a_{m}"]), np.array(res[f"b_{m}"])
        out[m] = {"incumbent_ci": ci(a), "other_ci": ci(b), "diff_other_minus_incumbent_ci": ci(b - a),
                  "diff_mean": float((b - a).mean())}
    return out


def compare(train, test, name_b, rng) -> dict:
    y = test["label"].to_numpy(dtype=int)
    pa = fit_predict(train, test, SETS["incumbent"])
    pb = fit_predict(train, test, SETS[name_b])
    return {"n_train": int(len(train)), "n_test": int(len(test)),
            "incumbent": metrics(y, pa), name_b: metrics(y, pb),
            "bootstrap": boot_ci(y, pa, pb, rng),
            "calibration_incumbent": calib_curve(y, pa), f"calibration_{name_b}": calib_curve(y, pb)}


def closing_line(labeled_all: pd.DataFrame, feat_all: pd.DataFrame) -> dict:
    """2026 only: train 2015-2025, score labeled 2026 games that have a Kalshi
    closing snapshot; compare model Brier against the market's closing price."""
    try:
        closing = inc.load_nfl_closing_prices()
        joined = inc.join_market_to_prospective(closing, feat_all[feat_all["season"] == 2026])
    except Exception as e:  # archive lives in MAIN_TREE (gitignored)
        return {"available": False, "reason": repr(e)}
    mk = {m["game_id"]: m for m in joined}
    test = labeled_all[(labeled_all["season"] == 2026) & labeled_all["game_id"].isin(mk)].reset_index(drop=True)
    train = labeled_all[labeled_all["season"] <= 2025].reset_index(drop=True)
    if test.empty:
        return {"available": True, "n": 0}
    y = test["label"].to_numpy(dtype=int)
    pm = np.array([mk[g]["yes_mid_home"] for g in test["game_id"]])
    out = {"available": True, "n": int(len(test)), "market_closing": {"brier": float(brier_score_loss(y, pm)),
           "accuracy": float(np.mean((pm >= 0.5) == y))}}
    for name in ("incumbent", "candidate"):
        p = fit_predict(train, test, SETS[name])
        out[name] = {"brier": float(brier_score_loss(y, p)), "accuracy": float(np.mean((p >= 0.5) == y))}
    out["caveat"] = "n is a handful of 2026 games; the interval on any Brier difference at this n spans zero -- informational only."
    return out


def main() -> int:
    rng = np.random.default_rng(SEED)
    sched, stats = load_data()
    coverage = {"rows": int(len(stats)), "seasons": sorted(int(s) for s in stats["season"].unique()),
                "split_nan": {c: int(stats[c].isna().sum()) for c in ("passing_epa", "rushing_epa")},
                "max_abs_agg_minus_sum": float((stats["off_epa"] - stats["passing_epa"] - stats["rushing_epa"]).abs().max())}
    store = NFLTeamStatsStore.build_from_team_stats(stats, sched)
    assert len(store) > 0 and store.get_pass_epa("KC", "2025-11-01") is not None, "store empty/inert"
    feat = build_rows(sched, store)
    labeled = feat[feat["label"].notnull()].copy()
    labeled["label"] = labeled["label"].astype(int)

    train = labeled[labeled["season"].between(2015, 2024)].reset_index(drop=True)
    hold = labeled[labeled["season"] == 2025].reset_index(drop=True)
    result = {"coverage": coverage, "seeds": {"bootstrap": SEED, "n_boot": N_BOOT},
              "feature_sets": SETS,
              "primary_holdout_2025": {nm: compare(train, hold, nm, rng) for nm in ("candidate", "splits_only")}}

    rolling = []
    for s in range(2020, 2026):
        tr = labeled[labeled["season"].between(2015, s - 1)].reset_index(drop=True)
        te = labeled[labeled["season"] == s].reset_index(drop=True)
        rolling.append({"test_season": s, **compare(tr, te, "candidate", rng)})
    result["rolling_origin"] = rolling
    result["closing_line_2026"] = closing_line(labeled, feat)

    (OUT / "exp027_epa_splits_candidate_result.json").write_text(json.dumps(result, indent=2, default=str))
    print(json.dumps({k: result[k] for k in ("coverage", "closing_line_2026")}, indent=2, default=str))
    for nm, r in result["primary_holdout_2025"].items():
        print(nm, "n_test", r["n_test"], "inc", r["incumbent"], "cand", r[nm])
        print("  brier diff CI", r["bootstrap"]["brier"]["diff_other_minus_incumbent_ci"],
              "acc diff CI", r["bootstrap"]["acc"]["diff_other_minus_incumbent_ci"])
    for r in rolling:
        print(r["test_season"], r["n_test"], "brier inc/cand", round(r["incumbent"]["brier"], 4),
              round(r["candidate"]["brier"], 4), "diff CI", r["bootstrap"]["brier"]["diff_other_minus_incumbent_ci"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
