"""W82.3 Part B: coverage / pressure tendency x QB production against it -> stability, cross, application.

Usage: python3 part_b.py <dir with w2018..w2025.parquet + sched.parquet> <dir with read-only frozen passyds model files>

PRE-STATED (before any number was computed):
  * Stability gate: split-half (defense games 1-6 vs 7+, per defense-season) Pearson r across defense-seasons, team-season
    bootstrap 95% CI; TRAIT iff CI lower bound > 0, else NOISE. Metrics: man share of classified coverage, pressure rate, 5+ rusher rate.
  * Cross (point-in-time, only games strictly before the target game, 3-season look-back, shrunk with FIXED pseudo-counts
    K_DEF=300 dropbacks, K_QB=150 dropbacks per side):
        d_man   = (defense man-share deviation from league) x (QB EPA/dropback vs man minus vs zone, deviation from league gap)
        d_press = (defense pressure-rate deviation)        x (QB EPA/dropback pressured minus clean, deviation from league gap)
  * Application: frozen passyds_strike_v1 (not modified; sha256-checked), held out 2024-2025 QB-games. Residual = actual passing yards -
    model mean. Slope of residual on standardized d, game-cluster bootstrap 95% CI (2000 draws). Supported iff CI excludes 0.
    Otherwise 'too few to tell' / 'no gain'. Nothing after 2025 is read.
"""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "12_EXPLORATORY"))
from _fence import safe_out  # noqa: E402

RAW = REPO / "exp_output" / "NFL_EVENTS" / "raw"
K_DEF, K_QB = 300.0, 150.0
RNG = np.random.default_rng(82_003)


def load_plays():
    fr = []
    for s in range(2015 + 3, 2026):
        p = pd.read_parquet(RAW / "pbp" / f"pbp_{s}.parquet",
                            columns=["game_id", "play_id", "season", "week", "season_type", "game_date", "defteam",
                                     "posteam", "qb_dropback", "epa", "passer_player_id"])
        p = p[(p.season_type == "REG") & (p.qb_dropback == 1)]
        pf = RAW / "participation" / f"participation_{s}.parquet"
        part = pd.read_parquet(pf, columns=["game_id", "play_id", "defense_man_zone_type", "number_of_pass_rushers",
                                            "was_pressure"])
        d = p.merge(part, on=["game_id", "play_id"], how="left")
        d["man"] = d.defense_man_zone_type.map({"MAN_COVERAGE": 1.0, "ZONE_COVERAGE": 0.0})
        d["press"] = d.was_pressure.map(lambda v: np.nan if pd.isna(v) else float(bool(v)))
        d["blitz5"] = np.where(d.number_of_pass_rushers.notna(), (d.number_of_pass_rushers >= 5).astype(float), np.nan)
        d["gameday"] = pd.to_datetime(d.game_date)
        fr.append(d[["game_id", "season", "week", "gameday", "defteam", "posteam", "passer_player_id", "epa", "man",
                     "press", "blitz5"]])
    return pd.concat(fr, ignore_index=True).sort_values("gameday").reset_index(drop=True)


def boot_r(x, y, n=2000):
    r = float(np.corrcoef(x, y)[0, 1])
    idx = RNG.integers(0, len(x), (n, len(x)))
    rs = [np.corrcoef(x[i], y[i])[0, 1] for i in idx]
    return r, float(np.nanpercentile(rs, 2.5)), float(np.nanpercentile(rs, 97.5))


def stability(plays):
    out = {}
    for metric in ["man", "press", "blitz5"]:
        for label, seasons in [("2018-2025 (fill >= 0.88)", range(2018, 2026)), ("2023-2025 (fill ~1.0)", range(2023, 2026))]:
            d = plays[plays.season.isin(list(seasons)) & plays[metric].notna()]
            a = d[d.week <= 6].groupby(["season", "defteam"])[metric].agg(["mean", "size"])
            b = d[d.week > 6].groupby(["season", "defteam"])[metric].agg(["mean", "size"])
            j = a.join(b, lsuffix="_a", rsuffix="_b", how="inner")
            j = j[(j.size_a >= 100) & (j.size_b >= 100)]
            r, lo, hi = boot_r(j.mean_a.to_numpy(), j.mean_b.to_numpy())
            # year-to-year: season s vs s+1 on full-season value
            f = d.groupby(["season", "defteam"])[metric].mean().unstack(0)
            f = f - f.mean()  # remove the league-level season shift (source vintage) before pairing
            pairs = [(s, s + 1) for s in seasons if s + 1 in f.columns and s in f.columns]
            xs = np.concatenate([f[s].dropna().reindex(f[t].dropna().index).dropna().to_numpy() for s, t in pairs])
            ys = np.concatenate([f[t].dropna().reindex(f[s].dropna().index).dropna().to_numpy() for s, t in pairs])
            r2, lo2, hi2 = boot_r(xs, ys)
            out[f"{metric} | {label}"] = {"split_half_r": r, "ci": [lo, hi], "n_def_seasons": int(len(j)),
                                          "trait" if lo > 0 else "noise": True, "year_to_year_r": r2,
                                          "y2y_ci": [lo2, hi2], "y2y_n": int(len(xs))}
    return out


def window_stats(df, key_col, val_col, cond_col):
    """Return (n_hi, mean_hi, n_lo, mean_lo) of val where cond==1 / cond==0."""
    h, l = df[df[cond_col] == 1.0][val_col], df[df[cond_col] == 0.0][val_col]
    return len(h), (h.mean() if len(h) else 0.0), len(l), (l.mean() if len(l) else 0.0)


def build_cross(plays, qg, model, pm):
    rows = []
    for r in qg[qg.gameday >= "2024-01-01"].itertuples():
        lo = r.gameday - pd.Timedelta(days=3 * 365)
        pri = plays[(plays.gameday < r.gameday) & (plays.gameday >= lo)]
        pq, pd_ = pm.league_priors(qg, DG, r.gameday)
        f = pm.features_for(qg, DG, r.name_key, r.opponent_team, r.home, r.gameday, pq, pd_)
        if f is None:
            continue
        qp = pri[pri.passer_player_id == r.player_id]
        dp = pri[pri.defteam == r.opponent_team]
        lg = pri
        L_man, L_press = lg.man.mean(), lg.press.mean()
        # defense deviations (shrunk toward league, fixed pseudo-count)
        def dev(df, col, league):
            x = df[col].dropna()
            return (x.sum() + K_DEF * league) / (len(x) + K_DEF) - league
        dm, dpr = dev(dp, "man", L_man), dev(dp, "press", L_press)
        # QB response gaps (EPA vs man minus vs zone; pressured minus clean), deviation from league gap, shrunk
        def gap(df, col):
            n1, m1, n0, m0 = window_stats(df.dropna(subset=[col, "epa"]), None, "epa", col)
            return m1 - m0, min(n1, n0)
        lg_man_gap, _ = gap(lg, "man")
        lg_press_gap, _ = gap(lg, "press")
        qm, qn = gap(qp, "man")
        qpr, qn2 = gap(qp, "press")
        qdev_m = (qm - lg_man_gap) * qn / (qn + K_QB) if qn else 0.0
        qdev_p = (qpr - lg_press_gap) * qn2 / (qn2 + K_QB) if qn2 else 0.0
        rows.append({"game_id": r.game_id, "player_id": r.player_id, "season": r.season, "week": r.week,
                     "y": r.passing_yards, "mu": model.mean(f), "def_man_dev": dm, "def_press_dev": dpr,
                     "qb_man_gap_dev": qdev_m, "qb_press_gap_dev": qdev_p,
                     "d_man": dm * qdev_m, "d_press": dpr * qdev_p, "n_def": int(len(dp.man.dropna())),
                     "n_qb_man": int(qn), "n_qb_press": int(qn2)})
    return pd.DataFrame(rows)


def slope_boot(x, y, groups, n=2000):
    x = (x - x.mean()) / x.std()
    def sl(ix):
        xx, yy = x[ix], y[ix]
        return np.cov(xx, yy)[0, 1] / np.var(xx, ddof=1)
    full = sl(np.arange(len(x)))
    ug, inv = np.unique(groups, return_inverse=True)
    members = [np.where(inv == i)[0] for i in range(len(ug))]
    bs = []
    for _ in range(n):
        pick = RNG.integers(0, len(ug), len(ug))
        bs.append(sl(np.concatenate([members[i] for i in pick])))
    return float(full), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))


def main():
    global DG
    ws_dir, fro = Path(sys.argv[1]), Path(sys.argv[2])
    spec = importlib.util.spec_from_file_location("passyds_model", fro / "passyds_model.py")
    pm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pm)
    sha = hashlib.sha256((fro / "passyds_strike_v1.json").read_bytes()).hexdigest()
    assert sha == (fro / "passyds_strike_v1.sha256").read_text().split()[0], "frozen model hash mismatch"
    model = pm.StrikeModel(json.loads((fro / "passyds_strike_v1.json").read_text()))
    ws = pd.concat([pd.read_parquet(ws_dir / f"w{y}.parquet") for y in range(2018, 2026)], ignore_index=True)
    ws = ws[ws.season_type == "REG"]
    sched = pd.read_parquet(ws_dir / "sched.parquet")
    sched = sched[sched.season <= 2025]
    qg, DG = pm.qb_games(ws, sched), pm.defense_games(ws, sched)

    plays = load_plays()
    res = {"frozen_sha256": sha, "stability": stability(plays)}
    for k, v in res["stability"].items():
        print(k, {a: (round(b, 3) if isinstance(b, float) else b) for a, b in v.items() if a != "ci" and a != "y2y_ci"}, [round(x, 3) for x in v["ci"]])

    cr = build_cross(plays, qg, model, pm)
    cr["resid"] = cr.y - cr.mu
    cr.to_csv(safe_out(HERE / "results" / "part_b_cross_games.csv"), index=False)
    res["n_games"] = int(len(cr))
    res["resid_sd"] = float(cr.resid.std())
    res["application"] = {}
    for col in ["d_man", "d_press"]:
        sl_, lo, hi = slope_boot(cr[col].to_numpy(float), cr.resid.to_numpy(float), cr.game_id.to_numpy())
        res["application"][col] = {"sd_d": float(cr[col].std()), "slope_yds_per_sd": sl_, "ci": [lo, hi],
                                   "supported": bool(lo > 0 or hi < 0), "n": int(len(cr)),
                                   "n_games": int(cr.game_id.nunique())}
    # rank of 2025 defenses vs 2018-2025 team-seasons at full season
    d = plays[plays.season.between(2018, 2025)]
    ts = d.groupby(["season", "defteam"]).agg(man=("man", "mean"), press=("press", "mean"), blitz5=("blitz5", "mean")).reset_index()
    for m in ["man", "press", "blitz5"]:
        ts[m + "_pct"] = ts[m].rank(pct=True)
    ts[ts.season == 2025].sort_values("press", ascending=False).to_csv(safe_out(HERE / "results" / "part_b_rank_2025.csv"), index=False)
    res["rank_2025_top_press"] = ts[ts.season == 2025].sort_values("press", ascending=False).head(3)[["defteam", "press", "press_pct"]].to_dict("records")
    res["rank_2025_top_man"] = ts[ts.season == 2025].sort_values("man", ascending=False).head(3)[["defteam", "man", "man_pct"]].to_dict("records")
    safe_out(HERE / "results" / "part_b_verdict.json").write_text(json.dumps(res, indent=1, default=str))
    print(json.dumps(res["application"], indent=1)); print(res["rank_2025_top_press"], res["rank_2025_top_man"])


if __name__ == "__main__":
    main()
