"""EXPLORATORY (W110.1 Part C): do point-in-time weather and unit-vs-unit matchup crosses move the engine's price vs the market line?

Base = the closing line (spread_line = expected home margin, total_line), so any difference from arm M is purely the factor.
Rolling origin: betas/effects fitted on seasons < T, scored on season T (2020-2025). Engine = 12_EXPLORATORY/nfl_engine/engine.py.
Arms: M market only | W_obs observed weather (LEAK upper bound, never priceable) | W_fc forecast weather (priceable)
      | X matchup crosses | WX_fc both (priceable). Ladders: strikes = line + {-7,-3,0,3,7}, spread and total.
Usage: python3 study.py <games.csv> <pbp_dir>   (writes results.json via safe_out)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(HERE.parent / "nfl_engine")); sys.path.insert(0, str(ROOT / "src"))
from _fence import safe_out  # noqa: E402
import engine as E  # noqa: E402
from prediction_market_bot.nfl_engine import matchup_cross as MX, weather_factor as WF  # noqa: E402

OFFS = [-7, -3, 0, 3, 7]
NSIM = 8000
SEED = 20261111
B = 2000
TEST = range(2020, 2026)
ARMS = ["M", "W_obs", "W_fc", "X", "WX_fc"]


def canon_roof(r):
    return r if isinstance(r, str) else None


def load(games_csv, pbp_dir):
    g = pd.read_csv(games_csv)
    g = g[(g.game_type == "REG") & g.spread_line.notna() & g.total_line.notna() & g.home_score.notna() & (g.season >= 2012)].copy()
    g["mu_h"] = (g.total_line + g.spread_line) / 2.0
    g["mu_a"] = (g.total_line - g.spread_line) / 2.0
    frames = []
    for y in range(2011, 2026):
        p = pd.read_parquet(Path(pbp_dir) / f"play_by_play_{y}.parquet",
                            columns=["season", "week", "game_id", "season_type", "posteam", "defteam", "play_type", "epa", "success", "sack", "qb_hit"])
        frames.append(MX.build_team_games(p))
    return g.reset_index(drop=True), MX.MatchupBook(pd.concat(frames, ignore_index=True))


def forecasts():
    fc = json.load(open(HERE.parent / "20261011_nfl_totals_venue_weather" / "forecast_kickoff.json"))
    pr_path = HERE / "precip_kickoff.json"
    pr = json.load(open(pr_path)) if pr_path.exists() else {}
    return fc, pr


def ctx_obs(r):
    return WF.WeatherContext("realised", canon_roof(r.roof), r.temp, r.wind, None, None)


def ctx_fc(r, fc, pr):
    f = fc.get(r.game_id)
    if f is None:
        return WF.WeatherContext("none")
    p = pr.get(r.game_id, {})
    return WF.WeatherContext("forecast", canon_roof(r.roof), f.get("temp_f"), f.get("wind_mph"), p.get("precip_mm"), f.get("lead_h"))


def exp_vec(ctxs):
    ex = [WF.exposure(c) for c in ctxs]
    return [np.array([e[k] for e in ex]) for k in ("wind", "cold", "precip")]


def shape(train):
    sd_m = float((train.result - train.spread_line).std()); sd_t = float((train.total - train.total_line).std())
    lg = float(train.total_line.mean()); best = None
    for r in (0.3, 0.45, 0.6, 0.8, 1.0):
        for sn in (0.0, 1.0, 2.0, 3.0):
            s = E.simulate(lg / 2, lg / 2, 20000, 12345, r, sn, delta=E.ot_delta(lg / 2, 100_000, 1, r, sn))
            e = (s.margin.std() - sd_m) ** 2 + (s.total.std() - sd_t) ** 2
            if best is None or e < best[0]:
                best = (e, r, sn)
    return best[1], best[2]


def score(s, row):
    out = []
    for kind, line, x in (("spread", row.spread_line, row.result), ("total", row.total_line, row.total)):
        for o in OFFS:
            k = line + o; v = s.margin if kind == "spread" else s.total
            p = float((v > k).mean() + 0.5 * (v == k).mean()); y = float(x > k) + 0.5 * float(x == k)
            out.append((kind, o, (p - y) ** 2))
    return out


def boot(d, seed=20261014):
    rng = np.random.default_rng(seed); n = len(d); idx = rng.integers(0, n, (B, n))
    m = d[idx].mean(1)
    return float(d.mean()), float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def verdict(hi):
    return "BEATS" if hi < 0 else "MATCHES" if hi < 0.001 else "NO"


def main():
    g, book = load(sys.argv[1], sys.argv[2])
    fc, pr = forecasts()
    # terms (PIT) for every game
    T = [book.terms(r.season, r.week, r.home_team, r.away_team) for r in g.itertuples()]
    Ta = [book.terms(r.season, r.week, r.away_team, r.home_team) for r in g.itertuples()]
    th = np.array([[t.pass_, t.rush, t.pressure] for t in T]); ta = np.array([[t.pass_, t.rush, t.pressure] for t in Ta])
    obs = exp_vec([ctx_obs(r) for r in g.itertuples()]); fcx = exp_vec([ctx_fc(r, fc, pr) for r in g.itertuples()])
    res_t = (g.total - g.total_line).to_numpy()
    res_h = (g.home_score - g.mu_h).to_numpy(); res_a = (g.away_score - g.mu_a).to_numpy()
    rows = []; meta = {"test": {}, "effects": {}, "betas": {}, "mu_shift": {}}
    for T_ in TEST:
        tr = (g.season < T_).to_numpy(); te = (g.season == T_).to_numpy()
        eff_obs = WF.fit_effects(obs[0][tr], obs[1][tr], np.zeros(tr.sum()), res_t[tr])
        # forecast arm uses effects fitted on observed exposure (forecasts only exist 2021+); precip effect fitted where fetched
        pr_ok = np.isfinite(fcx[2]) & (g.season >= 2021).to_numpy() & tr
        eff_fc = eff_obs
        if pr_ok.sum() > 200:
            e3 = WF.fit_effects(fcx[0][pr_ok], fcx[1][pr_ok], fcx[2][pr_ok], res_t[pr_ok]); eff_fc = WF.WeatherEffects(eff_obs.wind, eff_obs.cold, e3.precip)
        X = np.vstack([th[tr], ta[tr]]); y = np.concatenate([res_h[tr], res_a[tr]])
        beta = np.linalg.solve(X.T @ X + 1e-6 * np.eye(3), X.T @ y)
        meta["effects"][T_] = dict(obs=eff_obs.__dict__, fc=eff_fc.__dict__); meta["betas"][T_] = dict(zip(["pass", "rush", "pressure"], map(float, beta)))
        r_, sn = shape(g[tr]); delta = E.ot_delta(g.total_line[tr].mean() / 2, 100_000, 1, r_, sn)
        meta["test"][T_] = dict(n=int(te.sum()), r=r_, s_n=sn)
        for i in np.where(te)[0]:
            row = g.iloc[i]; sh = {}
            sh["M"] = (0.0, 0.0)
            w_obs = WF.total_shift(ctx_obs(row), eff_obs, pricing=False); w_fc = WF.total_shift(ctx_fc(row, fc, pr), eff_fc)
            xh, xa = float(th[i] @ beta), float(ta[i] @ beta)
            for arm, (dh, da) in {"M": (0, 0), "W_obs": (w_obs / 2, w_obs / 2), "W_fc": (w_fc / 2, w_fc / 2), "X": (xh, xa),
                                  "WX_fc": (w_fc / 2 + xh, w_fc / 2 + xa)}.items():
                s = E.simulate(max(row.mu_h + dh, 1.0), max(row.mu_a + da, 1.0), NSIM, SEED + i, r_, sn, delta=delta)
                for kind, o, bs in score(s, row):
                    rows.append((row.game_id, int(row.season), arm, kind, o, bs))
            meta["mu_shift"].setdefault("abs_x", []).append(abs(xh) + abs(xa)); meta["mu_shift"].setdefault("abs_w_fc", []).append(abs(w_fc)); meta["mu_shift"].setdefault("abs_w_obs", []).append(abs(w_obs))
        print("season", T_, "done", flush=True)
    df = pd.DataFrame(rows, columns=["game", "season", "arm", "kind", "off", "bs"])
    gm = df.groupby(["game", "season", "arm", "kind"], as_index=False).bs.mean()
    out = {"meta": {k: (v if k != "mu_shift" else {a: float(np.mean(b)) for a, b in v.items()}) for k, v in meta.items()}, "arms": {}}
    for kind in ("spread", "total", "both"):
        sub = gm if kind == "both" else gm[gm.kind == kind]
        pv = sub.groupby(["game", "season", "arm"], as_index=False).bs.mean().pivot(index=["game", "season"], columns="arm", values="bs").reset_index()
        for arm in ARMS:
            d = (pv[arm] - pv["M"]).to_numpy(); mean, lo, hi = boot(d)
            out["arms"].setdefault(kind, {})[arm] = dict(n=int(len(d)), brier=float(pv[arm].mean()), d_brier=mean, lo=lo, hi=hi, verdict=("BASE" if arm == "M" else verdict(hi)),
                                                          by_season={int(s): float((pv[arm] - pv["M"])[pv.season == s].mean()) for s in sorted(pv.season.unique())})
    # subset: games where forecast weather is non-trivial (wind/cold exposure > 0)
    wx = pd.DataFrame({"game": g.game_id, "exposed": (fcx[0] + fcx[1] + np.nan_to_num(fcx[2])) > 0})
    pvt = gm[gm.kind == "total"].pivot(index="game", columns="arm", values="bs").join(wx.set_index("game"))
    sub = pvt[pvt.exposed]; d = (sub["W_fc"] - sub["M"]).to_numpy()
    if len(d) > 20:
        mean, lo, hi = boot(d); out["arms"]["total_forecast_exposed_only"] = dict(W_fc=dict(n=int(len(d)), d_brier=mean, lo=lo, hi=hi, verdict=verdict(hi)))
    safe_out(HERE / "results.json").write_text(json.dumps(out, indent=1, default=float))
    print(json.dumps(out["arms"], indent=1, default=float))


if __name__ == "__main__":
    main()
