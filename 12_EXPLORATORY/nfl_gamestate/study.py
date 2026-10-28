"""EXPLORATORY -- W89.4 study: NFL game-state chain -> full-game simulation -> whole board vs market (held-out seasons).

Pre-registered in PLAN.md. Train = seasons strictly before the test season; ratings are point-in-time (games strictly earlier).
Usage: python3 study.py --pbp-dir DIR --schedule FILE [--sims 2000] [--tests 2024,2025]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "src"))
sys.path.insert(0, str(HERE.parent))
import chain as C  # noqa: E402
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant import scoring as SC  # noqa: E402

THETAS = np.linspace(-0.14, 0.14, 15)
KEYS = [1, 2, 3, 4, 6, 7, 10, 14]
NOMINAL_PTS = {"TD": 6.95, "FG": 3.0, "SAF": -2.0, "OPP_TD": -6.95}


def drive_table(plays: pd.DataFrame) -> pd.DataFrame:
    p = plays[plays.fixed_drive.notna() & plays.posteam.notna() & (plays.season_type == "REG")]
    d = p.groupby(["game_id", "fixed_drive"], sort=False).agg(
        season=("season", "first"), off=("posteam", "first"), deff=("defteam", "first"), res=("fixed_drive_result", "first"),
        date=("game_date", "first")).reset_index()
    d["cls"] = d.res.map(C.RESULT_MAP)
    d = d[d.cls.notna()]                                   # drops End of half (censored)
    d["pts"] = d.cls.map(NOMINAL_PTS).fillna(0.0)
    return d


def team_games(d: pd.DataFrame, sched: pd.DataFrame) -> pd.DataFrame:
    g = d.groupby(["game_id", "off", "deff"]).agg(n=("pts", "size"), pts=("pts", "sum")).reset_index()
    return g.merge(sched[["game_id", "gameday", "home_team"]], on="game_id")


class Ratings:
    """Point-in-time off/def points-per-drive ratings: exponentially decayed means shrunk to the league."""

    def __init__(self, tg: pd.DataFrame, halflife_days=365.0, prior_drives=80.0):
        self.tg = tg.assign(t=pd.to_datetime(tg.gameday)).sort_values("t")
        self.hl, self.k = halflife_days, prior_drives

    def _side(self, team, col_team, when, league):
        x = self.tg[(self.tg[col_team] == team) & (self.tg.t < when)]
        if x.empty:
            return 0.0
        w = 0.5 ** ((when - x.t).dt.days.to_numpy() / self.hl)
        num = (w * x.pts).sum() - league * 0.0
        den = (w * x.n).sum()
        return (num + self.k * league) / (den + self.k) - league

    def league(self, when):
        x = self.tg[self.tg.t < when]
        return float(x.pts.sum() / max(x.n.sum(), 1))

    def get(self, home, away, when):
        L = self.league(when)
        o = {t: self._side(t, "off", when, L) for t in (home, away)}
        # defence: points allowed per drive = rows where the team is the defence
        dd = {t: self._side(t, "deff", when, L) for t in (home, away)}
        return L, o, dd


def theta_for(target, epd):
    return float(np.interp(target, epd, THETAS))


def hfa_fit(tg: pd.DataFrame, cutoff: pd.Timestamp) -> float:
    x = tg[pd.to_datetime(tg.gameday) < cutoff]
    h = x[x.off == x.home_team]
    a = x[x.off != x.home_team]
    return float(h.pts.sum() / h.n.sum() - a.pts.sum() / a.n.sum())


def devig(odds_a, odds_b):
    def imp(o):
        o = np.asarray(o, float)
        return np.where(o < 0, -o / (-o + 100.0), 100.0 / (o + 100.0))
    a, b = imp(odds_a), imp(odds_b)
    return a / (a + b)


def boot(diff, groups, B=2000, seed=0):
    """Game-cluster bootstrap of a mean paired difference. Returns (mean, lo, hi)."""
    rng = np.random.default_rng(seed)
    df = pd.DataFrame({"d": diff, "g": groups}).groupby("g").d.agg(["sum", "count"])
    s, c = df["sum"].to_numpy(), df["count"].to_numpy()
    idx = rng.integers(0, len(s), (B, len(s)))
    m = s[idx].sum(1) / c[idx].sum(1)
    return float(s.sum() / c.sum()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def run_season(test, plays, sched, sims, seed):
    tr = plays[plays.season < test]
    ch = C.estimate_chain(tr)
    banks, epd = C.build_banks(ch, THETAS, 1500, seed)
    d = drive_table(plays[plays.season <= test])
    tg = team_games(d, sched)
    tg["home_team"] = tg.home_team
    R = Ratings(tg)
    hfa = hfa_fit(tg, pd.Timestamp(f"{test}-08-01"))
    games = sched[(sched.season == test) & (sched.game_type == "REG") & sched.home_score.notna() & sched.spread_line.notna()].copy()
    rows, sim_margin_all, sim_total_all, pit = [], [], [], []
    for i, g in enumerate(games.itertuples()):
        when = pd.Timestamp(g.gameday)
        L, o, dd = R.get(g.home_team, g.away_team, when)
        ph = L + o[g.home_team] + dd[g.away_team] + hfa / 2
        pa = L + o[g.away_team] + dd[g.home_team] - hfa / 2
        th_h, th_a = theta_for(ph, epd), theta_for(pa, epd)
        r = C.simulate_games(ch, banks, THETAS, th_h, th_a, sims, seed + i)
        m = r["home"] - r["away"]
        t = r["home"] + r["away"]
        rows.append(dict(game_id=g.game_id, season=test, week=g.week, spread=g.spread_line, total_line=g.total_line,
                         h_ml=g.home_moneyline, a_ml=g.away_moneyline, hs_odds=g.home_spread_odds, as_odds=g.away_spread_odds,
                         ov_odds=g.over_odds, un_odds=g.under_odds, ot_flag=float(g.overtime == 1), home_pts=g.home_score, away_pts=g.away_score,
                         sim_margin_mean=float(m.mean()), sim_total_mean=float(t.mean()), margin=m.astype(np.int16),
                         total=t.astype(np.int16), home_sim=r["home"].astype(np.int16), away_sim=r["away"].astype(np.int16),
                         ot_rate=float(r["ot"].mean()), drives=float(r["n_drives"].mean())))
    return ch, epd, hfa, pd.DataFrame(rows)


def cover_prob(samples, line, side):
    """P(outcome) at a strike, pushes excluded by caller; side 'gt' => samples > line."""
    return float((samples > line).mean()) if side == "gt" else float((samples < line).mean())


def board(df):
    out = {}
    act_m = (df.home_pts - df.away_pts).to_numpy()
    act_t = (df.home_pts + df.away_pts).to_numpy()
    # moneyline: ties half
    simml = np.array([((m > 0).mean() + 0.5 * (m == 0).mean()) for m in df.margin])
    y_ml = np.where(act_m > 0, 1.0, np.where(act_m == 0, 0.5, 0.0))
    mkt_ml = devig(df.h_ml, df.a_ml)
    out["moneyline"] = (simml, mkt_ml, y_ml, np.ones(len(df), bool))
    # spread: home covers if margin > spread_line
    simsp = np.array([float((m > s).mean() + 0.5 * (m == s).mean()) for m, s in zip(df.margin, df.spread)])
    keep = act_m != df.spread.to_numpy()
    y_sp = (act_m > df.spread.to_numpy()).astype(float)
    mkt_sp = devig(df.hs_odds.fillna(-110), df.as_odds.fillna(-110))
    out["spread"] = (simsp, mkt_sp, y_sp, keep)
    simtt = np.array([float((t > l).mean() + 0.5 * (t == l).mean()) for t, l in zip(df.total, df.total_line)])
    keep = act_t != df.total_line.to_numpy()
    y_tt = (act_t > df.total_line.to_numpy()).astype(float)
    mkt_tt = devig(df.ov_odds.fillna(-110), df.un_odds.fillna(-110))
    out["total"] = (simtt, mkt_tt, y_tt, keep)
    return out


def gaussian_p(mean, sd, line, side="gt"):
    from math import erf, sqrt
    z = (line - mean) / sd
    p_le = 0.5 * (1 + erf(z / sqrt(2)))
    return 1 - p_le if side == "gt" else p_le


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pbp-dir", required=True)
    ap.add_argument("--schedule", required=True)
    ap.add_argument("--sims", type=int, default=2000)
    ap.add_argument("--tests", default="2024,2025")
    ap.add_argument("--first-train", type=int, default=2016)
    ap.add_argument("--out", default=str(HERE / "results.json"))
    a = ap.parse_args()
    tests = [int(x) for x in a.tests.split(",")]
    last = max(tests)
    paths = {s: f"{a.pbp_dir}/pbp_{s}.parquet" for s in range(a.first_train, last + 1) if Path(f"{a.pbp_dir}/pbp_{s}.parquet").exists()}
    plays = C.load_plays(paths)
    sched = pd.read_parquet(a.schedule)
    sched = sched.sort_values("_as_of").drop_duplicates("game_id", keep="last") if "_as_of" in sched.columns else sched
    res = {"sims": a.sims, "seasons": {}}
    for k, test in enumerate(tests):
        ch, epd, hfa, df = run_season(test, plays, sched, a.sims, 1000 * (k + 1))
        # --- Part A: key numbers + EP-at-first-and-ten check on held-out season
        act_m = np.abs((df.home_pts - df.away_pts).to_numpy())
        sim_m = np.abs(np.concatenate(df.margin.to_list()))
        keynum = {int(kk): dict(sim=float((sim_m == kk).mean()), actual=float((act_m == kk).mean()), n_games=len(df)) for kk in KEYS}
        # EP check on held-out plays
        pp = C._prep(plays[(plays.season == test) & (plays.season_type == "REG")])
        d = drive_table(plays[(plays.season == test)])
        fr = pp[(pp.down == 1) & (pp.ydstogo == 10)].merge(d[["game_id", "fixed_drive", "pts"]], on=["game_id", "fixed_drive"])
        V = C.values(ch)
        fr["v"] = V[fr.state.astype(int).to_numpy()]
        mean_d, lo, hi = boot((fr.pts - fr.v).to_numpy(), fr.game_id.to_numpy())
        ep = dict(n_first_and_10=int(len(fr)), observed=float(fr.pts.mean()), chain=float(fr.v.mean()), diff=mean_d, ci=[lo, hi])
        # --- Part B: board vs market
        bd = board(df)
        fam = {}
        gid = df.game_id.to_numpy()
        # Gaussian comparator sd from TRAIN seasons residual vs market line
        tr = sched[(sched.season < test) & (sched.game_type == "REG") & sched.spread_line.notna() & sched.home_score.notna()]
        sd_m = float(((tr.home_score - tr.away_score) - tr.spread_line).std())
        sd_t = float(((tr.home_score + tr.away_score) - tr.total_line).std())
        gauss = {"moneyline": None}
        for name, (ps, pm, y, keep) in bd.items():
            k_ = keep
            if name == "moneyline":
                pg = np.array([gaussian_p(m, sd_m, 0.0) for m in df.sim_margin_mean])   # P(margin>0)
            elif name == "spread":
                pg = np.array([gaussian_p(m, sd_m, s) for m, s in zip(df.sim_margin_mean, df.spread)])
            else:
                pg = np.array([gaussian_p(m, sd_t, l) for m, l in zip(df.sim_total_mean, df.total_line)])
            b_sim = (ps - y) ** 2
            b_mkt = (pm - y) ** 2
            b_g = (pg - y) ** 2
            e = {}
            for lab, other in (("sim_vs_market", b_mkt), ("sim_vs_gauss_same_mean", b_g), ("gauss_vs_market", b_mkt)):
                base = b_sim if lab.startswith("sim") else b_g
                m_, lo_, hi_ = boot((base - other)[k_], gid[k_])
                e[lab] = dict(brier_diff=m_, ci=[lo_, hi_])
            e.update(n=int(k_.sum()), brier_sim=float(b_sim[k_].mean()), brier_market=float(b_mkt[k_].mean()),
                     brier_gauss=float(b_g[k_].mean()))
            # shape-only: recentre sim to the market centre
            fam[name] = e
        # shape-only (recentre sim distribution on the market line): spread-ladder at off-line strikes
        offs = [-10, -7, -6.5, -3.5, -3, -2.5, -0.5, 0.5, 2.5, 3, 3.5, 6.5, 7, 10]
        lad = {}
        act_mg = (df.home_pts - df.away_pts).to_numpy()
        for off in offs:
            p_s, p_c, p_mk, yy = [], [], [], []
            for r_, m in zip(df.itertuples(), df.margin):
                strike = r_.spread + off
                if (r_.home_pts - r_.away_pts) == strike:
                    continue
                p_s.append(float((m - m.mean() + r_.spread > strike).mean()))
                p_mk.append(gaussian_p(r_.spread, sd_m, strike))
                p_c.append(float((m > strike).mean()))
                yy.append(float((r_.home_pts - r_.away_pts) > strike))
            ys, ps_, pm_, pc_ = map(np.array, (yy, p_s, p_mk, p_c))
            lad[str(off)] = dict(n=len(ys), brier_shape_only_minus_gauss_at_market=float(((ps_ - ys) ** 2 - (pm_ - ys) ** 2).mean()),
                                 brier_full_sim_minus_gauss_at_market=float(((pc_ - ys) ** 2 - (pm_ - ys) ** 2).mean()))
        # team-total PIT (descriptive)
        pit_h = [float((hs < r_.home_pts).mean() + 0.5 * (hs == r_.home_pts).mean()) for hs, r_ in zip(df.home_sim, df.itertuples())]
        pit_h = np.array(pit_h)
        pit_hist = np.histogram(pit_h, bins=5, range=(0, 1))[0].tolist()
        res["seasons"][str(test)] = dict(
            n_games=len(df), hfa_ppd=hfa, chain=dict(plays=ch.n_plays, drives=ch.n_drives, td_mix=ch.td_pts.tolist()),
            sim=dict(drives_per_game=float(df.drives.mean()), ot_rate=float(df.ot_rate.mean()),
                     mean_total=float(df.sim_total_mean.mean()), mean_margin_minus_line=float((df.sim_margin_mean - df.spread).mean()),
                     total_minus_line=float((df.sim_total_mean - df.total_line).mean())),
            actual=dict(mean_total=float((df.home_pts + df.away_pts).mean()), ot_rate=float(df.ot_flag.mean())),
            keynum=keynum, ep_first_and_10=ep, families=fam, ladder=lad, team_total_pit_5bin_home=pit_hist,
            sd_margin_train=sd_m, sd_total_train=sd_t)
        print(test, "done", len(df), flush=True)
    safe_out(a.out).write_text(json.dumps(res, indent=1))
    print("wrote", a.out)


if __name__ == "__main__":
    main()
