"""EXP-NFLPLAYLEVEL-001 retrospective runner (PREREG.md s1-5). Usage: run_playlevel.py <games.csv> [out_dir]
Reads team_game_playlevel.csv (part_a.py). Fit 2020-2024 (X2: 2023-2024), judge 2025 REG (BH q 0.10), descriptive 2026 REG to date (carried).
Proxy prices from board_v2 (earlier seasons only). Writes results.json."""
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out
import json
from collections import defaultdict

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.decision_trees.filters import nfl_playlevel as PL  # noqa: E402
from prediction_market_bot.nfl_engine import board_v2 as B2  # noqa: E402
from prediction_market_bot.quant import costs, inference, variance  # noqa: E402

HERE = Path(__file__).parent
MIN_N = 40
HS = {"AS": 0.005, "AT": 0.010, "TT": 0.015}
HS_MEAN = {"AS": 0.0155, "AT": 0.0248, "TT": 0.0222}
SERIES = {"AS": "KXNFLSPREAD", "AT": "KXNFLTOTAL", "TT": "KXNFLTEAMTOTAL"}
OFFS = {"TT": (-6, -3, 0, 3, 6), "AS": (-7, -3, 0, 3, 7), "AT": (-7, -3, 0, 3, 7)}
FIT = {"x1_personnel_shell": (2020, 2024), "x2_motion_man": (2023, 2024), "x3_success_shell": (2020, 2024)}
JUDGE, LOOK26, LAST_DATA_SEASON = 2025, 2026, 2025


def load(path):
    g = pd.read_csv(path)
    g = g[g.game_type == "REG"].copy()
    g["gameday"] = pd.to_datetime(g.gameday)
    return g.sort_values(["gameday", "game_id"]).reset_index(drop=True)


def tendencies(g):
    """{(game_id, team): {'o1','d1','o2','d2','o3': value or None}} from games strictly before the game day (PL.trailing_ratio)."""
    t = pd.read_csv(HERE / "team_game_playlevel.csv")
    t = t.merge(g[["game_id", "gameday"]], on="game_id", how="inner")
    spec = {  # name: (numerator, denominator, data-present column, prior, k)
        "o1": ("off_p11", "off_plays", "off_part", 0.0, 0.0), "d1": ("def_two_high", "def_cov", "def_cov", 0.0, 0.0),
        "o2": ("off_motion", "off_ftn", "off_ftn", 0.0, 0.0), "d2": ("def_man", "def_cov", "def_cov", 0.0, 0.0),
        "o3": ("off_epa_vs2", "off_vs2", "off_vs2", 0.0, PL.EPA_K)}
    hist = {k: defaultdict(list) for k in spec}
    last_season = {k: {} for k in spec}
    for r in t.sort_values("gameday").itertuples():
        for k, (n, d, pres, _, _) in spec.items():
            if getattr(r, pres) > 0 and getattr(r, d) > 0:
                hist[k][r.team].append((r.gameday.date(), float(getattr(r, n)), float(getattr(r, d))))
                last_season[k][r.team] = r.season
    out = {}
    for r in g.itertuples():
        for team in (r.home_team, r.away_team):
            v = {}
            for k, (_, _, _, prior, kk) in spec.items():
                h = [x for x in hist[k][team] if x[0] < r.gameday.date()]
                v[k] = PL.trailing_ratio(h, r.gameday.date(), prior, kk)
            out[(r.game_id, team)] = v
    return out


def bets(g, tend, cuts):
    done = g[g.home_score.notna() & g.spread_line.notna() & g.total_line.notna() & g.season.between(2019, LOOK26)]
    rows = []
    for s in range(2019, LOOK26 + 1):
        lib = B2.build_library(g, before_season=s)
        for r in done[done.season == s].itertuples():
            bd = B2.price_board(lib, float(r.spread_line), float(r.total_line))
            m, t = int(r.home_score - r.away_score), int(r.home_score + r.away_score)
            th, ta = tend[(r.game_id, r.home_team)], tend[(r.game_id, r.away_team)]
            hv = {"x1_personnel_shell": (th["o1"], ta["d1"]), "x2_motion_man": (th["o2"], ta["d2"]), "x3_success_shell": (th["o3"], ta["d1"])}
            av = {"x1_personnel_shell": (ta["o1"], th["d1"]), "x2_motion_man": (ta["o2"], th["d2"]), "x3_success_shell": (ta["o3"], th["d1"])}
            lv = {}
            for c in PL.CROSS_NAMES:
                h, a = PL.cross_leaf(*hv[c], cuts.get(c)), PL.cross_leaf(*av[c], cuts.get(c))
                lv[c] = dict(H=h, A=a, AS=PL.game_leaf_spread(h, a), AT=PL.game_leaf_total(h, a))
            ch, ca = (r.total_line + r.spread_line) / 2, (r.total_line - r.spread_line) / 2
            for mk in ("TT", "AS", "AT"):
                for off in OFFS[mk]:
                    if mk == "TT":
                        for home, cons, pts in ((True, ch, r.home_score), (False, ca, r.away_score)):
                            k = int(round(cons)) + off
                            rows.append((r.game_id, s, mk, off, bd.p_team_ge(home, k + 1), int(pts >= k + 1),
                                         *[lv[c]["H" if home else "A"] for c in PL.CROSS_NAMES]))
                    elif mk == "AS":
                        k = int(round(r.spread_line)) + off + 1
                        rows.append((r.game_id, s, mk, off, bd.p_margin_ge(k), int(m >= k), *[lv[c]["AS"] for c in PL.CROSS_NAMES]))
                    else:
                        k = int(round(r.total_line)) + off + 1
                        rows.append((r.game_id, s, mk, off, bd.p_total_ge(k), int(t >= k), *[lv[c]["AT"] for c in PL.CROSS_NAMES]))
    return pd.DataFrame(rows, columns=["game", "season", "mk", "off", "p", "y", *PL.CROSS_NAMES])


def fit_cuts(g, tend):
    """Median offense / defense tendency over FIT-season team-games per cross (PREREG s3)."""
    pairs = {"x1_personnel_shell": ("o1", "d1"), "x2_motion_man": ("o2", "d2"), "x3_success_shell": ("o3", "d1")}
    cuts = {}
    for c, (o, d) in pairs.items():
        lo, hi = FIT[c]
        oo, dd = [], []
        for r in g[g.season.between(lo, hi)].itertuples():
            for team, opp in ((r.home_team, r.away_team), (r.away_team, r.home_team)):
                a, b = tend[(r.game_id, team)][o], tend[(r.game_id, opp)][d]
                if a is not None and b is not None:
                    oo.append(a); dd.append(b)
        cuts[c] = (float(np.median(oo)), float(np.median(dd))) if len(oo) >= 100 else None
    return cuts


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


def look(x, arm):
    ng = int(x.game.nunique())
    rec = dict(n_games=ng)
    if ng >= MIN_N:
        cm = variance.clustered_mean(x[f"n_{arm}_median"].tolist(), x.game.tolist(), 0.90)
        rec.update(gross=float(x[f"g_{arm}"].mean()), cost=float(x[f"c_{arm}_median"].mean()), net=cm["mean"], net_lo=cm["lo"], net_hi=cm["hi"],
                   net_mean_cost=float(x[f"n_{arm}_mean"].mean()))
    return rec


def main(path, out_dir=str(HERE)):
    g = load(path)
    tend = tendencies(g)
    cuts = fit_cuts(g, tend)
    df = bets(g, tend, cuts)
    df["band"] = np.where((df.p >= 0.25) & (df.p <= 0.75), "mid", "wing")
    for tag, hs in (("median", HS), ("mean", HS_MEAN)):
        a = arms(df, hs)
        for arm in a:
            df[f"g_{arm}"], df[f"c_{arm}_{tag}"] = a[arm]
            df[f"n_{arm}_{tag}"] = df[f"g_{arm}"] - df[f"c_{arm}_{tag}"]
    final, fam = [], []
    for cr in PL.CROSS_NAMES:
        flo, fhi = FIT[cr]
        for mk in ("TT", "AS", "AT"):
            sub = df[(df.mk == mk) & (df[cr] != "unknown")]
            unk = int(((df.mk == mk) & (df[cr] == "unknown") & df.season.isin([JUDGE])).sum())
            cells = sorted(set(zip(sub[cr], sub.band)))
            by = defaultdict(dict)
            for arm in ("RIDE", "FADE"):
                fit_cells = {}
                for c in cells:
                    x = sub[(sub[cr] == c[0]) & (sub.band == c[1]) & sub.season.between(flo, fhi)]
                    if x.game.nunique() >= 30:
                        cm = variance.clustered_mean(x[f"n_{arm}_median"].tolist(), x.game.tolist(), 0.90)
                        if cm["se"] == cm["se"] and cm["se"] > 0:
                            fit_cells[c] = (cm["mean"], cm["se"])
                pooled = variance.partial_pool(fit_cells)["cells"] if len(fit_cells) >= 2 else []
                shr = {c: o for c, o in zip(fit_cells, pooled)}
                for c in cells:
                    q = (sub[cr] == c[0]) & (sub.band == c[1])
                    rec = dict(cross=cr, market=mk, leaf=c[0], band=c[1], arm=arm, n_unknown_2025=unk,
                               fit_n_games=int(sub[q & sub.season.between(flo, fhi)].game.nunique()),
                               fit_shrunk=shr[c]["shrunk"] if c in shr else None, fit_lo=shr[c]["lo"] if c in shr else None)
                    j = look(sub[q & (sub.season == JUDGE)], arm)
                    rec.update({f"j25_{k}": v for k, v in j.items()})
                    k26 = look(sub[q & (sub.season == LOOK26)], arm)
                    rec.update({f"j26_{k}": v for k, v in k26.items()})
                    by[(c[0], c[1])][arm] = (rec, sub[q & (sub.season == JUDGE)])
            for key, d in by.items():
                best = max(d, key=lambda a: (d[a][0]["fit_shrunk"] if d[a][0]["fit_shrunk"] is not None else -9))
                routed = d[best][0]["fit_lo"] is not None and d[best][0]["fit_lo"] > 0
                for arm, (rec, x) in d.items():
                    rec["fit_route"] = best if (routed and arm == best) else ("NO BET" if not routed else "other arm")
                    rec["fit_routed_arm"] = bool(routed and arm == best)
                    if rec["fit_routed_arm"] and "j25_net" in rec:
                        pt = inference.pooled_cluster_test(list(zip(x.game, x[f"n_{arm}_median"])), b=2000)
                        rec["p_one_sided"] = pt["p"] if "p" in pt else pt.get("p_one_sided")
                        _, lo, hi = inference.cluster_bootstrap({k: v.tolist() for k, v in x.groupby("game")[f"n_{arm}_median"]}, b=2000, alpha=0.10)
                        rec["boot_lo"], rec["boot_hi"] = lo, hi
                        fam.append(rec)
                    final.append(rec)
    if fam:
        for r, f in zip(fam, inference.benjamini_hochberg([r["p_one_sided"] for r in fam], q=0.10)):
            r["bh_sig"] = bool(f)
    for r in final:
        if "j25_net" not in r:
            r["verdict"] = f"not judged: n below MIN_N (n={r['j25_n_games']})"
        elif r.get("bh_sig") and r["j25_net"] > 0 and r["boot_lo"] > 0:
            r["verdict"] = "arm earned in this leaf"
        else:
            r["verdict"] = "routed to ride / no bet in this leaf"
    meta = dict(fit=FIT, judge="2025 REG", look26="2026 REG to date (descriptive, carried personnel/coverage)", MIN_N=MIN_N, hs_median=HS, hs_mean=HS_MEAN,
                bh_family=len(fam), cuts=cuts, bets=int(len(df)), games=int(df.game.nunique()))
    safe_out(Path(out_dir, "results.json")).write_text(json.dumps({"meta": meta, "rows": final}, indent=1, default=float))
    print(json.dumps(meta, default=float))
    print(len(final), "rows;", sum(1 for r in final if "j25_net" in r), "judged;", len(fam), "in BH family;",
          sum(1 for r in final if r["verdict"] == "arm earned in this leaf"), "earned")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else str(HERE))
