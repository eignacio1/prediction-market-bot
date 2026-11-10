"""W106.4 Part B (market): train 2024+2025, test 2026 games the Kalshi archive priced. PYTHONPATH=src.

usage: python 12_EXPLORATORY/mlb_engine/run_w106_4_market.py [store_root] [archive_glob]
Model p vs naive (train base rate) vs Kalshi last pre-game mid (>=10 min before first pitch, overround removed)
on the same games. Blend view via quant/blend.py (clusters = game date). Writes RESULTS_W106_4_MARKET.json.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.mlb_engine import lineup_aware as la
from prediction_market_bot.mlb_engine import market_line as mk
from prediction_market_bot.mlb_engine import model_lineup as ml
from prediction_market_bot.quant import blend

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "mlb_store"
ARCH = sys.argv[2] if len(sys.argv) > 2 else "exp_output/PRICE_ARCHIVE/prices_*.jsonl"
T = ROOT / "tables"
TEST_FROM = "2026-01-01"


def cmp(name, p, pm, pn, y, dates, out, tight=None):
    """Brier/log loss of model, market, naive on identical rows; model-minus-market gain with game-level CI."""
    r = {"n": int(len(y))}
    for lab, q in (("model", p), ("market", pm), ("naive", pn)):
        r[lab] = {"brier": ml.brier(q, y), "logloss": ml.logloss(q, y)}
    r["gain_vs_market_brier"] = ml.boot_gain(p, pm, y, "brier")
    r["gain_vs_market_ll"] = ml.boot_gain(p, pm, y, "ll")
    r["gain_vs_naive_brier"] = ml.boot_gain(p, pn, y, "brier")
    r["market_vs_naive_brier"] = ml.boot_gain(pm, pn, y, "brier")
    rows = [(str(d), float(a), float(b), float(c)) for d, a, b, c in zip(dates, pm, p, y)]
    r["blend_linear"] = blend.blend_report(rows, "linear")
    r["blend_logit"] = blend.blend_report(rows, "logit")
    out[name] = r
    print(name, "n=", r["n"], "Brier model %.4f market %.4f naive %.4f" % (r["model"]["brier"], r["market"]["brier"], r["naive"]["brier"]),
          "| model-vs-market gain %+.4f [%+.4f,%+.4f]" % r["gain_vs_market_brier"],
          "| w_hat", r["blend_linear"].get("w_hat"), r["blend_linear"].get("w_boot_ci"))


def main():
    t = {k: pd.read_parquet(T / f"{k}.parquet") for k in ("pitches", "pa", "games", "lineups")}
    pa = t["pa"]
    tr = pa["game_date"] < TEST_FROM
    mu = float(pa[tr].woba_value.sum() / pa[tr].woba_denom.sum())
    d = la.design_lineup(t["games"], t["lineups"], pa, t["pitches"], mu)
    train, test = d[d.game_date < TEST_FROM], d[d.game_date >= TEST_FROM]
    base_pr = ml.price(ml.RunModel(["is_home"]).fit(train), train)
    base = {c: float(base_pr[c].mean()) for c in ("home_win", "over", "home_rl")}
    pr_all = {}
    for name, feats in (("base(W105.3)", la.BASE_FEATURES), ("all", la.LINEUP_FEATURES)):
        pr_all[name] = ml.price(ml.RunModel(feats).fit(train), test)
    g = t["games"][["game_pk", "game_date", "home_team", "away_team"]]
    g = g[g.game_date >= TEST_FROM]
    dup = g.duplicated(["game_date", "home_team", "away_team"], keep=False)  # doubleheaders: ambiguous, dropped
    g = g[~dup]
    c = mk.last_pregame(ARCH)
    out = {"mu": mu, "n_test_games_2026": int(test.game_pk.nunique()), "archive_contracts": int(len(c)),
           "dropped_doubleheader_games": int(dup.sum())}
    ml_m = mk.moneyline(c)
    out["moneyline_events_all"] = int(len(ml_m))
    j = ml_m.merge(g, left_on=["game_date", "home", "away"], right_on=["game_date", "home_team", "away_team"])
    out["moneyline_matched"] = int(len(j))
    for arm, pr in pr_all.items():
        x = j.merge(pr[["game_pk", "p_home", "home_win"]], on="game_pk")
        pn = np.full(len(x), base["home_win"])
        cmp(f"moneyline[{arm}]", x.p_home.to_numpy(), x.p_home_mkt.to_numpy(), pn, x.home_win.to_numpy(), x.game_date.dt.strftime("%Y-%m-%d"), out)
        tight = x[x.half_spread <= 0.03]
        if len(tight) >= 30:
            cmp(f"moneyline_tight(hs<=0.03)[{arm}]", tight.p_home.to_numpy(), tight.p_home_mkt.to_numpy(), np.full(len(tight), base["home_win"]),
                tight.home_win.to_numpy(), tight.game_date.dt.strftime("%Y-%m-%d"), out)
    tot = mk.total_rung(c)
    jt = tot.merge(g, left_on=["game_date", "home", "away"], right_on=["game_date", "home_team", "away_team"])
    out["total_matched"] = int(len(jt))
    for arm, pr in pr_all.items():
        x = jt.merge(pr, on="game_pk", suffixes=("", "_m"))
        k = x.k.to_numpy().astype(int)
        p = np.array([x[f"pge{kk}"].iloc[i] if ml.PGE_MIN <= kk <= ml.PGE_MAX else np.nan for i, kk in enumerate(k)])
        ok = ~np.isnan(p)
        y = ((x.home_runs + x.away_runs).to_numpy() >= k).astype(float)
        # naive: train-set frequency of total >= k
        trt = (train.groupby("game_pk").runs.sum()).to_numpy()
        pn = np.array([(trt >= kk).mean() for kk in k])
        cmp(f"total_rung[{arm}]", p[ok], x.p_mkt.to_numpy()[ok], pn[ok], y[ok], x.game_date.dt.strftime("%Y-%m-%d")[ok], out)
    safe_out(Path(__file__).parent / "RESULTS_W106_4_MARKET.json").write_text(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
