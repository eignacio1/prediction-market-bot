"""EXP-NFLSPLITS-001 retrospective runner (PREREG.md sections 1-3, 8). Usage: run_splits.py <games.csv> [out_dir]
Fit 2019-2024, judge 2025 REG, proxy prices from board_v2 (earlier seasons only). Writes results.json."""
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out
from __future__ import annotations

import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.decision_trees.filters import nfl_splits as NS  # noqa: E402
from prediction_market_bot.nfl_engine import board_v2 as B2  # noqa: E402
from prediction_market_bot.nfl_engine.matchup_cross import MatchupBook  # noqa: E402
from prediction_market_bot.nfl_engine.weather_factor import WeatherContext  # noqa: E402
from prediction_market_bot.quant import costs, inference, variance  # noqa: E402

FD = ROOT / "src/prediction_market_bot/decision_trees/filter_data"
FIT_MAX, JUDGE = 2024, 2025
MIN_N = 40
HS = {"AS": 0.005, "AT": 0.010, "TT": 0.015}          # archive medians, PREREG s2
HS_MEAN = {"AS": 0.0155, "AT": 0.0248, "TT": 0.0222}  # sensitivity
SERIES = {"AS": "KXNFLSPREAD", "AT": "KXNFLTOTAL", "TT": "KXNFLTEAMTOTAL"}
OFFS = {"TT": (-6, -3, 0, 3, 6), "AS": (-7, -3, 0, 3, 7), "AT": (-7, -3, 0, 3, 7)}
SPLITS = ("qb", "rest", "officials", "weather", "matchup")


def load(path):
    g = pd.read_csv(path)
    g = g[g.game_type == "REG"].copy()
    g["gameday"] = pd.to_datetime(g.gameday)
    return g.sort_values(["gameday", "game_id"]).reset_index(drop=True)


def features(g):
    """Per game PIT features (history from all seasons in the file)."""
    last_qb, last_day, ref_res = {}, {}, defaultdict(list)
    sch = pd.read_csv(FD / "nfl_schedule.csv")[["season", "week", "home", "away", "stadium_id", "kickoff_utc"]]
    wx = pd.read_csv(FD / "nfl_weather_backfill.csv")
    wxk = {(r.stadium_id, r.kickoff_utc): r for r in wx.itertuples()}
    skey = {(r.season, r.week, r.home, r.away): (r.stadium_id, r.kickoff_utc) for r in sch.itertuples()}
    tg = pd.read_csv(FD / "nfl_team_games.csv")
    mb = MatchupBook(tg)
    feats = {}
    for day, grp in g.groupby("gameday", sort=True):
        pending = []
        for r in grp.itertuples():
            h, a = r.home_team, r.away_team
            f = {"home_prev_qb": last_qb.get(h), "away_prev_qb": last_qb.get(a), "prev_home": last_day.get(h), "prev_away": last_day.get(a)}
            res = ref_res.get(r.referee) if isinstance(r.referee, str) else None
            f["ref_prior"] = NS.ref_prior(res) if res else None
            wxr = None
            k = skey.get((r.season, r.week, h, a))
            if k and k in wxk:
                w = wxk[k]
                wxr = WeatherContext(source="forecast", roof=r.roof, temp_f=w.temp_f, wind_mph=w.wind_mph, lead_h=w.lead_h)
            f["weather"] = wxr
            if r.season >= 2022:
                th, ta = mb.terms(r.season, r.week, h, a), mb.terms(r.season, r.week, a, h)
                f["mu_h"] = th.pass_ + th.rush - th.pressure
                f["mu_a"] = ta.pass_ + ta.rush - ta.pressure
            else:
                f["mu_h"] = f["mu_a"] = None
            feats[r.game_id] = f
            pending.append(r)
        for r in pending:  # update history only after the whole day, so same-day games never see each other
            if isinstance(r.home_qb_id, str):
                last_qb[r.home_team] = r.home_qb_id
            if isinstance(r.away_qb_id, str):
                last_qb[r.away_team] = r.away_qb_id
            last_day[r.home_team] = last_day[r.away_team] = day.date()
            if isinstance(r.referee, str) and pd.notna(r.home_score) and pd.notna(r.total_line):
                ref_res[r.referee].append(float(r.home_score + r.away_score - r.total_line))
    return feats


def cuts_of(vals):
    v = [x for x in vals if x is not None]
    return (float(np.percentile(v, 100 / 3)), float(np.percentile(v, 200 / 3))) if len(v) >= 30 else None


def bets(g, feats):
    done = g[g.home_score.notna() & g.spread_line.notna() & g.total_line.notna() & g.season.between(2019, JUDGE)]
    rows = []
    for s in range(2019, JUDGE + 1):
        lib = B2.build_library(g, before_season=s)
        for r in done[done.season == s].itertuples():
            bd = B2.price_board(lib, float(r.spread_line), float(r.total_line))
            m, t = int(r.home_score - r.away_score), int(r.home_score + r.away_score)
            f = feats[r.game_id]
            ch = (r.total_line + r.spread_line) / 2
            ca = (r.total_line - r.spread_line) / 2
            for mk in ("TT", "AS", "AT"):
                for off in OFFS[mk]:
                    if mk == "TT":
                        for home, cons, pts in ((True, ch, r.home_score), (False, ca, r.away_score)):
                            k = int(round(cons)) + off
                            rows.append((r.game_id, s, mk, off, "H" if home else "A", bd.p_team_ge(home, k + 1), int(pts >= k + 1)))
                    elif mk == "AS":
                        k = int(round(r.spread_line)) + off + 1
                        rows.append((r.game_id, s, mk, off, "G", bd.p_margin_ge(k), int(m >= k)))
                    else:
                        k = int(round(r.total_line)) + off + 1
                        rows.append((r.game_id, s, mk, off, "G", bd.p_total_ge(k), int(t >= k)))
    return pd.DataFrame(rows, columns=["game", "season", "mk", "off", "side", "p", "y"]), done


def leaves_for(df, done, feats, ref_cuts, mu_cuts):
    d = done.set_index("game_id")
    out = {s: [] for s in SPLITS}
    for r in df.itertuples():
        gm, f = d.loc[r.game], feats[r.game]
        gday = gm.gameday.date()
        hq = NS.qb_leaf(f["home_prev_qb"], gm.home_qb_id if isinstance(gm.home_qb_id, str) else None)
        aq = NS.qb_leaf(f["away_prev_qb"], gm.away_qb_id if isinstance(gm.away_qb_id, str) else None)
        hr, ar = gm.home_rest, gm.away_rest
        if r.mk == "TT":
            q, rs = (hq if r.side == "H" else aq), NS.rest_leaf(hr if r.side == "H" else ar)
            mu = f["mu_h"] if r.side == "H" else f["mu_a"]
        else:
            q, rs = NS.game_qb_leaf(hq, aq), NS.rest_diff_leaf(hr, ar)
            mu = None if f["mu_h"] is None else (f["mu_h"] - f["mu_a"] if r.mk == "AS" else f["mu_h"] + f["mu_a"])
        cut = mu_cuts.get(("TT" if r.mk == "TT" else r.mk))
        try:
            w = NS.weather_leaf(f["weather"])
        except NS.PITViolation:
            w = "unknown"
        out["qb"].append(q); out["rest"].append(rs)
        out["officials"].append(NS.referee_leaf(f["ref_prior"], ref_cuts))
        out["weather"].append(w)
        out["matchup"].append(NS.matchup_leaf(mu, cut))
    for s in SPLITS:
        df[s] = out[s]
    return df


def mu_values(df, done, feats):
    d = done.set_index("game_id")
    v = defaultdict(list)
    for r in df[df.season.between(2022, FIT_MAX)].itertuples():
        f = feats[r.game]
        if f["mu_h"] is None:
            continue
        v[r.mk].append(f["mu_h"] if (r.mk == "TT" and r.side == "H") else f["mu_a"] if r.mk == "TT" else
                       (f["mu_h"] - f["mu_a"] if r.mk == "AS" else f["mu_h"] + f["mu_a"]))
    return {k: cuts_of(x) for k, x in v.items()}


def arms(df, hs):
    p, y = df.p.to_numpy(), df.y.to_numpy()
    yes = p >= 0.5
    out = {}
    for arm in ("RIDE", "FADE"):
        buy_yes = yes if arm == "RIDE" else ~yes
        px = np.where(buy_yes, p, 1 - p)
        gross = np.where(buy_yes, y - p, p - y)
        cost = np.array([costs.taker_entry_cost(SERIES[m], float(q), hs[m]) for m, q in zip(df.mk, px)])
        out[arm] = (gross, cost)
    return out


def main(path, out_dir="."):
    g = load(path)
    feats = features(g)
    df, done = bets(g, feats)
    fitmask = df.season <= FIT_MAX
    ref_cuts = cuts_of([feats[x]["ref_prior"] for x in done[done.season.between(2019, FIT_MAX)].game_id])
    mu_cuts = mu_values(df, done, feats)
    df = leaves_for(df, done, feats, ref_cuts, mu_cuts)
    df["band"] = np.where((df.p >= 0.25) & (df.p <= 0.75), "mid", "wing")
    for tag, hs in (("median", HS), ("mean", HS_MEAN)):
        a = arms(df, hs)
        for arm in a:
            df[f"g_{arm}"], df[f"c_{arm}_{tag}"] = a[arm]
            df[f"n_{arm}_{tag}"] = df[f"g_{arm}"] - df[f"c_{arm}_{tag}"]
    rows, fam = [], []
    for sp in SPLITS:
        for mk in ("TT", "AS", "AT"):
            sub = df[(df.mk == mk) & (df[sp] != "unknown")]
            unk = int(((df.mk == mk) & (df[sp] == "unknown")).sum())
            cells = sorted(set(zip(sub[sp], sub.band)))
            for arm in ("RIDE", "FADE"):
                fit_cells = {}
                for c in cells:
                    x = sub[(sub[sp] == c[0]) & (sub.band == c[1]) & (sub.season <= FIT_MAX)]
                    if x.game.nunique() >= 30:
                        cm = variance.clustered_mean(x[f"n_{arm}_median"].tolist(), x.game.tolist(), 0.90)
                        if cm["se"] == cm["se"] and cm["se"] > 0:
                            fit_cells[c] = (cm["mean"], cm["se"])
                pooled = variance.partial_pool(fit_cells)["cells"] if len(fit_cells) >= 2 else []
                shr = {c: o for c, o in zip(fit_cells, pooled)}
                for c in cells:
                    x = sub[(sub[sp] == c[0]) & (sub.band == c[1]) & (sub.season == JUDGE)]
                    ng = int(x.game.nunique())
                    rec = dict(split=sp, market=mk, leaf=c[0], band=c[1], arm=arm, n_judge_games=ng, n_unknown_market_rows=unk,
                               fit_shrunk=shr[c]["shrunk"] if c in shr else None, fit_lo=shr[c]["lo"] if c in shr else None,
                               fit_n_games=int(sub[(sub[sp] == c[0]) & (sub.band == c[1]) & (sub.season <= FIT_MAX)].game.nunique()))
                    if ng >= MIN_N:
                        cm = variance.clustered_mean(x[f"n_{arm}_median"].tolist(), x.game.tolist(), 0.90)
                        rec.update(gross=float(x[f"g_{arm}"].mean()), cost=float(x[f"c_{arm}_median"].mean()), net=cm["mean"],
                                   net_lo=cm["lo"], net_hi=cm["hi"], net_mean_cost=float(x[f"n_{arm}_mean"].mean()))
                    rows.append((rec, x))
            # fit routing per (leaf, band)
        for rec, x in rows:
            pass
    # routing: per (split, market, leaf, band) the better fit arm, only if its shrunk lower bound > 0
    by = defaultdict(dict)
    for rec, x in rows:
        by[(rec["split"], rec["market"], rec["leaf"], rec["band"])][rec["arm"]] = (rec, x)
    final = []
    for key, d in by.items():
        best = max(d, key=lambda a: (d[a][0]["fit_shrunk"] if d[a][0]["fit_shrunk"] is not None else -9))
        br = d[best][0]
        routed = br["fit_lo"] is not None and br["fit_lo"] > 0
        for arm, (rec, x) in d.items():
            rec["fit_route"] = best if (routed and arm == best) else ("NO BET" if not routed else "other arm")
            rec["fit_routed_arm"] = bool(routed and arm == best)
            if rec["fit_routed_arm"] and "net" in rec:
                pt = inference.pooled_cluster_test(list(zip(x.game, x[f"n_{arm}_median"])), b=2000)
                rec["p_one_sided"] = pt["p"] if "p" in pt else pt.get("p_one_sided")
                _, lo, hi = inference.cluster_bootstrap({k: v.tolist() for k, v in x.groupby("game")[f"n_{arm}_median"]}, b=2000, alpha=0.10)
                rec["boot_lo"], rec["boot_hi"] = lo, hi
                fam.append(rec)
            final.append(rec)
    if fam:
        flags = inference.benjamini_hochberg([r["p_one_sided"] for r in fam], q=0.10)
        for r, f in zip(fam, flags):
            r["bh_sig"] = bool(f)
    for r in final:
        if "net" not in r:
            r["verdict"] = f"not judged: n below MIN_N (n={r['n_judge_games']})"
        elif r.get("bh_sig") and r["net"] > 0 and r["boot_lo"] > 0:
            r["verdict"] = "arm earned in this leaf"
        else:
            r["verdict"] = "routed to ride / no bet in this leaf"
    meta = dict(fit_seasons="2019-2024", judge="2025 REG", MIN_N=MIN_N, hs_median=HS, hs_mean=HS_MEAN, bh_family=len(fam),
                ref_cuts=ref_cuts, mu_cuts=mu_cuts, bets=int(len(df)), games=int(df.game.nunique()))
    safe_out(Path(out_dir, "results.json")).write_text(json.dumps({"meta": meta, "rows": final}, indent=1, default=float))
    print(json.dumps(meta, default=float)); print(len(final), "rows;", sum(1 for r in final if "net" in r), "judged;", len(fam), "in BH family;",
          sum(1 for r in final if r["verdict"] == "arm earned in this leaf"), "earned")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else str(Path(__file__).parent))
