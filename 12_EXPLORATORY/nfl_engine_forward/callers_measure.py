"""W94.2 Part C measurement: N11 play-caller tendencies, point-in-time. Reads pbp + schedules from args; writes JSON.

k and season decay are fitted on 2016-2019 only; 2020-2025 is held out. Intervals are game-level bootstrap (seed 94).
"""
import argparse, json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "src")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out
from prediction_market_bot.c1_signal_ingestion import nfl_play_callers as pc

COLS = ["game_id", "season", "season_type", "week", "game_date", "home_team", "away_team", "home_coach", "away_coach", "posteam",
        "defteam", "play_type", "down", "ydstogo", "yardline_100", "score_differential", "qtr", "game_seconds_remaining",
        "half_seconds_remaining", "qb_kneel", "qb_spike", "two_point_attempt", "drive", "penalty", "timeout", "out_of_bounds",
        "play_id", "epa"]
FIT, HELD = (2016, 2019), (2020, 2025)
MIN_PRIOR = {"pass_oe": 500, "go4_oe": 30, "pace": 100, "lead_oe": 100}  # prior plays (as-of) before an estimate is scored
MIN_GAME = {"pass_oe": 20, "go4_oe": 2, "pace": 10, "lead_oe": 5}      # plays in the scored game


def boot(x, B=2000, seed=94):
    x = np.asarray(x, float); rng = np.random.default_rng(seed)
    m = np.array([x[rng.integers(0, len(x), len(x))].mean() for _ in range(B)])
    return float(x.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def fit_k(tg, oc):
    """Pick (k, decay) per feature minimising weighted squared error of as-of estimate vs the team-game residual mean."""
    best = {}
    for f in pc.FEATURES:
        res = []
        for k in (50, 100, 200, 400, 800, 1600, 3200):
            for dec in (1.0, 0.8, 0.6):
                r = pc.replay(tg, oc, {g: float(k) for g in pc.FEATURES}, dec)
                r = r[(r.season >= FIT[0]) & (r.season <= FIT[1]) & (r[f + "_n"] > 0)]
                y = r[f + "_s"] / r[f + "_n"]; w = r[f + "_n"]
                res.append((float((w * (y - r["est_" + f]) ** 2).sum() / w.sum()), k, dec))
        best[f] = min(res)
    return best


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--pbp", required=True); a.add_argument("--oc", required=True); a.add_argument("--sched", required=True)
    a.add_argument("--out", required=True)
    a = a.parse_args()
    seasons = {y: pd.read_parquet(f"{a.pbp}/play_by_play_{y}.parquet", columns=COLS) for y in range(2015, 2027)}
    oc = pc.read_oc_jsonl(a.oc)
    tg = pc.team_game_sums(seasons, first=2016)
    best = fit_k(tg, oc)
    k = {f: float(best[f][1]) for f in pc.FEATURES}; dec = float(np.median([best[f][2] for f in pc.FEATURES]))
    rp = pc.replay(tg, oc, k, dec)
    out = {"fit": {f: {"k": best[f][1], "decay": best[f][2], "wmse": best[f][0]} for f in pc.FEATURES}, "decay_used": dec,
           "caller_source_share_2016_2025": rp[rp.season <= 2025].source.value_counts(normalize=True).round(4).to_dict()}
    # 1. trait or noise: does the as-of estimate predict the NEXT game's own residual on held-out seasons?
    h = rp[(rp.season >= HELD[0]) & (rp.season <= HELD[1])]
    out["predict_own_next_game"] = {}
    for f in pc.FEATURES:
        d = h[(h["n_" + f] >= MIN_PRIOR[f]) & (h[f + "_n"] >= MIN_GAME[f])]
        y = (d[f + "_s"] / d[f + "_n"]).to_numpy(); e = d["est_" + f].to_numpy()
        rng = np.random.default_rng(94); idx = [rng.integers(0, len(y), len(y)) for _ in range(2000)]
        rs = [np.corrcoef(e[i], y[i])[0, 1] for i in idx]
        out["predict_own_next_game"][f] = {"n_team_games": int(len(y)), "corr": float(np.corrcoef(e, y)[0, 1]),
                                           "ci": [float(np.percentile(rs, 2.5)), float(np.percentile(rs, 97.5))],
                                           "sd_est": float(e.std()), "range_est": [float(e.min()), float(e.max())]}
    # 2. beyond the line and N1-N3: held-out totals / team totals
    s = pd.read_parquet(a.sched); s = s[(s.game_type == "REG")]
    s["gid"] = s.game_id
    # baseline team form as of each game: EW points for/against and EPA, strictly before
    ev = []
    for y, df in seasons.items():
        d = df[(df.season_type == "REG") & df.posteam.notna() & df.epa.notna()]
        ev.append(d.assign(off=d.posteam.map(pc.canon), de=d.defteam.map(pc.canon)))
    ev = pd.concat(ev)
    eo = ev.groupby(["game_id", "off"]).epa.mean().rename("epa_off")
    ed = ev.groupby(["game_id", "de"]).epa.mean().rename("epa_def")
    long = []
    for r in s.itertuples():
        for side, t, o, pf, pa, rest in (("h", r.home_team, r.away_team, r.home_score, r.away_score, r.home_rest),
                                          ("a", r.away_team, r.home_team, r.away_score, r.home_score, r.away_rest)):
            long.append(dict(game_id=r.game_id, season=r.season, week=r.week, date=r.gameday, side=side, team=pc.canon(t), pf=pf, pa=pa, rest=rest))
    L = pd.DataFrame(long).sort_values(["date", "game_id"])
    L = L.join(eo, on=["game_id", "team"]).join(ed, on=["game_id", "team"])
    alpha = 0.2
    st, feats = {}, []
    for r in L.itertuples():
        e = st.setdefault(r.team, dict(pf=22.5, pa=22.5, eo=0.0, ed=0.0))
        feats.append((e["pf"], e["pa"], e["eo"], e["ed"]))
        if not np.isnan(r.pf):
            e["pf"] += alpha * (r.pf - e["pf"]); e["pa"] += alpha * (r.pa - e["pa"])
        if not np.isnan(r.epa_off): e["eo"] += alpha * (r.epa_off - e["eo"])
        if not np.isnan(r.epa_def): e["ed"] += alpha * (r.epa_def - e["ed"])
    L[["ew_pf", "ew_pa", "ew_eo", "ew_ed"]] = feats
    L = L.set_index(["game_id", "side"])
    est_cols = ["est_" + f for f in pc.FEATURES]
    rr = rp.set_index(["game_id", "team"])[est_cols]
    G = s.set_index("game_id")
    rows = []
    for gid, r in G.iterrows():
        if (gid, "h") not in L.index or r.season > 2025 or pd.isna(r.total_line) or pd.isna(r.home_score): continue
        h, aw = L.loc[(gid, "h")], L.loc[(gid, "a")]
        try: eh, ea = rr.loc[(gid, pc.canon(r.home_team))], rr.loc[(gid, pc.canon(r.away_team))]
        except KeyError: continue
        rows.append(dict(gid=gid, season=r.season, line=r.total_line, spread=r.spread_line, hs=r.home_score, as_=r.away_score,
                         h_pf=h.ew_pf, h_pa=h.ew_pa, h_eo=h.ew_eo, h_ed=h.ew_ed, a_pf=aw.ew_pf, a_pa=aw.ew_pa, a_eo=aw.ew_eo, a_ed=aw.ew_ed,
                         h_rest=r.home_rest, a_rest=r.away_rest, **{"h_" + c: eh[c] for c in est_cols}, **{"a_" + c: ea[c] for c in est_cols}))
    D = pd.DataFrame(rows).dropna().reset_index(drop=True)
    base_t = ["line", "h_pf", "h_pa", "a_pf", "a_pa", "h_eo", "h_ed", "a_eo", "a_ed", "h_rest", "a_rest"]
    call_t = [p + c for p in ("h_", "a_") for c in est_cols]

    def ridge(Xtr, ytr, Xte, lam=50.0):
        mu, sd = Xtr.mean(0), Xtr.std(0) + 1e-9
        A = (Xtr - mu) / sd; ym = ytr.mean()
        w = np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ (ytr - ym))
        return ym + ((Xte - mu) / sd) @ w

    def run(target, Xb, Xc, name):
        pb, pcl, ys = [], [], []
        for y in range(HELD[0], HELD[1] + 1):
            tr, te = D[D.season < y], D[D.season == y]
            ytr, yte = target(tr), target(te)
            pb.append(ridge(tr[Xb].to_numpy(float), ytr, te[Xb].to_numpy(float)))
            pcl.append(ridge(tr[Xb + Xc].to_numpy(float), ytr, te[Xb + Xc].to_numpy(float)))
            ys.append(yte)
        pb, pcl, ys = map(np.concatenate, (pb, pcl, ys))
        d_cb = (ys - pb) ** 2 - (ys - pcl) ** 2  # >0 means callers help
        d_b0 = ys ** 2 - (ys - pb) ** 2          # >0 means baseline beats the line alone
        return {"n": int(len(ys)), "mse_line_only": float((ys ** 2).mean()),
                "base_vs_line_mse_gain": boot(d_b0), "callers_add_mse_gain": boot(d_cb)}

    tot = lambda d: (d.hs + d.as_ - d.line).to_numpy(float)
    out["totals_heldout"] = run(tot, base_t, call_t, "total")
    # team totals: stack home and away rows, own-team and opponent tendencies
    T = []
    for side, o in (("h", "a"), ("a", "h")):
        t = D.copy(); t["y"] = (t.hs - (t.line + t.spread) / 2) if side == "h" else (t.as_ - (t.line - t.spread) / 2)
        ren = {f"{side}_{c}": f"o_{c}" for c in ["pf", "pa", "eo", "ed", "rest"] + est_cols}
        ren.update({f"{o}_{c}": f"x_{c}" for c in ["pf", "pa", "eo", "ed", "rest"] + est_cols})
        t = t.rename(columns=ren); t["tl"] = (t.line + t.spread) / 2 if side == "h" else (t.line - t.spread) / 2; T.append(t)
    D2 = pd.concat(T, ignore_index=True)
    bt = ["tl", "o_pf", "o_pa", "x_pf", "x_pa", "o_eo", "o_ed", "x_eo", "x_ed", "o_rest", "x_rest"]
    ct = ["o_" + c for c in est_cols] + ["x_" + c for c in est_cols]
    Dsave, D = D, D2
    out["team_totals_heldout"] = run(lambda d: d.y.to_numpy(float), bt, ct, "team")
    D = Dsave
    # per-feature: does adding ONE tendency (own + opponent) help the team-total model?
    D = D2
    out["team_totals_one_feature"] = {f: run(lambda d: d.y.to_numpy(float), bt, ["o_est_" + f, "x_est_" + f], f)["callers_add_mse_gain"] for f in pc.FEATURES}
    json.dump(out, open(safe_out(a.out), "w"), indent=1, default=float)
    rp.to_parquet(safe_out(a.out.replace(".json", "_asof.parquet")))
    print(json.dumps(out, indent=1, default=float))


main()
