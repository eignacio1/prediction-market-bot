"""W84.3 Part B: does the best Part A factor add to the KXNHLGAME pre-game price beyond frozen nhl_pregame_v1?
Exploratory only. Reads the event store, cached box payloads and the Kalshi history store; no live model is changed.
Verdict rule is fixed in run_w84_3.py's docstring (written before the 2025 look)."""
from __future__ import annotations

import gzip
import json
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parents[1] / "src"))
from _fence import safe_out  # noqa: E402
import run_w84_3 as R  # noqa: E402
from prediction_market_bot.analytics import kalshi_history as kh  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nhl_ingest as ni  # noqa: E402
from prediction_market_bot.c2_feature_store.nhl_features import NhlFeatureStore, parse_ts  # noqa: E402
from prediction_market_bot.c3_forecasting import nhl_pregame as m  # noqa: E402

OUT = R.OUT
FEATS = ["xg_share5", "st_net60", "gsax", "rest"]


def box_games():
    games = []
    for s in R.SEASONS:
        for p in sorted((R.ROOT / "exp_output/NHL_EVENTS/raw/box" / str(s)).glob("*.json.gz")):
            raw = json.load(gzip.open(p, "rt"))
            row = ni.parse_game_row(raw["payload"], raw["_fetched_at_utc"])
            if row:
                games.append(row)
    return games


def frozen_p(games, ids):
    model, sha = m.load_model(R.ROOT / "models/nhl_pregame_v1.json")
    store = NhlFeatureStore(games)
    out = {}
    for g in games:
        if g["game_id"] in ids:
            st = parse_ts(g["start_time_utc"])
            out[g["game_id"]] = model.ladder(store.game_features(g["home"], g["away"], st, st - timedelta(hours=1))).p_home_win()
    return out, sha


def market_p(fr):
    rows = {}
    for t in kh._load("markets", "KXNHLGAME", R.KALSHI):
        pt = m.parse_ticker(t)
        if not pt or pt["team"] != pt["home"]:
            continue
        rows[(pt["game_date"], pt["home"], pt["away"])] = t
    res = []
    for r in fr.itertuples():
        t = rows.get((r.game_date_et, r.home, r.away))
        if not t:
            continue
        q = kh.prevailing_quote(t, parse_ts(r.start_time_utc) - timedelta(hours=1), R.KALSHI)
        s = kh.settlement(t, R.KALSHI)
        if not q or q[0] is None or q[1] is None or s not in ("yes", "no"):
            continue
        res.append((r.game_id, (q[0] + q[1]) / 2, q[1] - q[0], int(s == "yes")))
    return pd.DataFrame(res, columns=["game_id", "mkt", "spread", "mkt_yes"])


def factor_cols(fr):
    d = pd.DataFrame(index=fr.index)
    d["xg_share5"] = fr.h_xg_share5 - fr.a_xg_share5
    d["st_net60"] = fr.h_st_net60 - fr.a_st_net60
    d["gsax"] = fr.h_prev_goalie_gsax10.fillna(0) - fr.a_prev_goalie_gsax10.fillna(0)
    d["rest"] = fr.h_days_since_prev.clip(upper=5) - fr.a_days_since_prev.clip(upper=5)
    return d


def brier(p, y): return float(np.mean((p - y) ** 2))


def main():
    fr = pd.read_parquet(OUT / "factor_frame.parquet")
    fr = fr[(fr.game_type == 2) & (fr.home_score != fr.away_score)].copy()
    fr["y"] = (fr.home_score > fr.away_score).astype(int)
    fc = factor_cols(fr); fr = pd.concat([fr, fc], axis=1).dropna(subset=["xg_share5", "st_net60", "rest"])
    # Factor model: trained on 2022-2024 only (home win ~ factor diffs), applied to 2025 untouched.
    tr = fr[fr.season.isin(R.FACTOR_TRAIN)]; ho = fr[fr.season == R.HOLDOUT].copy()
    mu, sd = tr[FEATS].mean(), tr[FEATS].std()
    b = R.fit_lr(((tr[FEATS] - mu) / sd).values, tr.y.values, l2=1.0)
    ho["f_logit"] = np.column_stack([np.ones(len(ho)), ((ho[FEATS] - mu) / sd).values]) @ b
    ho["f_p"] = 1 / (1 + np.exp(-ho.f_logit))
    games = box_games(); fp, sha = frozen_p(games, set(ho.game_id))
    ho["frozen"] = ho.game_id.map(fp)
    mk = market_p(ho); d = ho.merge(mk, on="game_id").dropna(subset=["frozen"])
    # Market-defined outcome must agree with box outcome
    agree = float((d.mkt_yes == d.y).mean()); d = d[d.mkt_yes == d.y]
    y = d.y.values; lm = R.logit(d.mkt.values); lf = R.logit(d.frozen.values)
    fz = (d.f_logit - ho.f_logit.mean()).values   # centred factor logit
    rng = np.random.default_rng(84); n = len(d)
    def stack(idx):
        X = np.column_stack([lm[idx], fz[idx]]); return R.fit_lr(X, y[idx])
    bs = np.array([stack(rng.integers(0, n, n)) for _ in range(1000)])
    b_hat = stack(np.arange(n))
    ci = np.percentile(bs[:, 2], [2.5, 97.5])
    # 5-fold CV Brier: market alone vs blend
    folds = rng.integers(0, 5, n); pm = d.mkt.values; pb = np.zeros(n); pf2 = np.zeros(n)
    for k in range(5):
        trn, te = folds != k, folds == k
        bb = R.fit_lr(np.column_stack([lm[trn], fz[trn]]), y[trn]); pb[te] = R.predict(bb, np.column_stack([lm[te], fz[te]]))
        b0 = R.fit_lr(lm[trn][:, None], y[trn]); pf2[te] = R.predict(b0, lm[te][:, None])
    dd = (pb - y) ** 2 - (pm - y) ** 2
    dbs = [dd[rng.integers(0, n, n)].mean() for _ in range(2000)]; dci = np.percentile(dbs, [2.5, 97.5])
    # frozen model vs market in same sample, and frozen as extra term
    X3 = lambda idx: np.column_stack([lm[idx], lf[idx] - lm[idx]])
    b3 = np.array([R.fit_lr(X3(i), y[i]) for i in (rng.integers(0, n, n) for _ in range(500))])
    res = {"n": n, "market_outcome_agreement": agree, "frozen_sha256": sha, "median_spread": float(d.spread.median()),
           "brier_market": brier(pm, y), "brier_frozen": brier(d.frozen.values, y), "brier_factor_alone": brier(d.f_p.values, y),
           "brier_cv_market_recal": brier(pf2, y), "brier_cv_blend": brier(pb, y),
           "cv_brier_diff_blend_minus_market": float(dd.mean()), "cv_brier_diff_ci95": [float(dci[0]), float(dci[1])],
           "stack_coef_factor": float(b_hat[2]), "stack_coef_factor_ci95": [float(ci[0]), float(ci[1])],
           "stack_coef_market": float(b_hat[1]),
           "frozen_extra_coef": float(np.median(b3[:, 2])), "frozen_extra_ci95": [float(np.percentile(b3[:, 2], 2.5)), float(np.percentile(b3[:, 2], 97.5))],
           "factor_train_seasons": R.FACTOR_TRAIN, "factor_coefs_std": dict(zip(["const"] + FEATS, map(float, b)))}
    adds = ci[0] > 0 or ci[1] < 0
    res["verdict"] = ("adds" if adds and dci[1] < 0 else "does not add" if (not adds and abs(ci).max() < 0.5) else "too few to tell")
    json.dump(res, open(safe_out(OUT / "part_b.json"), "w"), indent=1); print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
