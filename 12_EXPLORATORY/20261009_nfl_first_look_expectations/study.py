"""EXPLORATORY -- variance / MDE inputs for the EXP-037 NFL first look (W62.2 Part B). Not a verdict.

Pre-2026 only: 2025 REG (the frozen model's held-out season). No 2026 row, sealed result or 2026 score is read.
Sign convention = EXP-037 section 2: delta = Brier(X) - Brier(model); positive = model better.
Reads: nflverse schedule/team-stats copies, nflverse games.csv (spread_line/total_line, used ONLY to place a
representative ladder strike), frozen models/nfl_pregame_v1.json, 2025 KXNFLGAME candles. Writes via safe_out().
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent / "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import NFLPregameFeatureBuilder  # noqa: E402
from prediction_market_bot.pregame_shadow.nfl_model import NFLPregameModel, _phi  # noqa: E402

KMAP = {"JAX": "JAX", "LA": "LA", "LAR": "LA", "WAS": "WAS", "WSH": "WAS", "LV": "LV", "OAK": "LV"}
B, SEED = 2000, 20261009
HORIZONS_H = {"T1~24h": 24.0, "T2~6h": 6.0, "T3~0.5h": 0.5}   # hours before kickoff, fixed a priori
Z95, Z80 = 1.959964, 0.841621


def norm(t):
    return KMAP.get(t, t)


def boot(d, B=B, seed=SEED):
    rng = np.random.default_rng(seed)
    m = d[rng.integers(0, len(d), (B, len(d)))].mean(1)
    return dict(n=int(len(d)), mean=float(d.mean()), sd=float(d.std(ddof=1)),
                lo95=float(np.percentile(m, 2.5)), hi95=float(np.percentile(m, 97.5)))


def half(x):
    return math.floor(x) + 0.5


def split_ticker(tk, teams):
    """-> (away, home, side, datecode) or None. datecode like '25SEP07'."""
    ev, side = tk.rsplit("-", 1)
    code = ev.split("-")[1][:7]
    body = ev.split("-")[1][7:]
    for i in (2, 3):
        a, h = body[:i], body[i:]
        if norm(a) in teams and norm(h) in teams:
            return norm(a), norm(h), norm(side), code
    return None


def mid_at(sets, tk, t_target):
    """Mid of the latest quoted candle at or before t_target: 1m if <=60min stale, else 60m if <=120min stale."""
    for per, cap in ((1, 3600), (60, 7200)):
        cs = sets.get((tk, per)) or []
        cand = [c for c in cs if c["t"] <= t_target and c["ask"]["close"] is not None and c["bid"]["close"] is not None]
        if cand and t_target - cand[-1]["t"] <= cap:
            return (cand[-1]["ask"]["close"] + cand[-1]["bid"]["close"]) / 2.0
    return None


def mde(sd, n):
    return (Z95 + Z80) * sd / math.sqrt(n)


def verdict_probs(mu, sd, n):
    """P(rule) under a normal approximation to the game-cluster bootstrap; true delta = mu (EXP-037 sign)."""
    se = sd / math.sqrt(n)
    p_out = _phi((-Z95 * se - mu) / se)        # upper CI bound < 0
    p_cand = 1.0 - _phi((Z95 * se - mu) / se)  # lower CI bound > 0 (E_net condition ignored: an upper bound)
    return dict(RULED_OUT=p_out, KEEP_ACCRUING=1 - p_out - p_cand, CANDIDATE_upper_bound=p_cand)


def main():
    ap = argparse.ArgumentParser()
    for k in ("schedule", "team-stats", "model", "candles", "markets", "games-csv"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    sched, stats = pd.read_parquet(a.schedule), pd.read_parquet(a.team_stats)
    model = NFLPregameModel.load(a.model)
    clim = model.a["climatology"]
    fb = NFLPregameFeatureBuilder(stats, sched)
    gl = pd.read_csv(a.games_csv, usecols=["game_id", "spread_line", "total_line", "gametime"]).set_index("game_id")
    reg = sched[(sched.game_type == "REG") & sched.home_score.notna() & (sched.season == 2025)]
    rows = []
    for r in reg.itertuples():
        as_of = datetime(*map(int, str(r.gameday).split("-")), tzinfo=timezone.utc)
        out = fb.row(r.home_team, r.away_team, as_of, r.home_rest, r.away_rest)
        if out is None or r.game_id not in gl.index or pd.isna(gl.loc[r.game_id, "spread_line"]):
            continue
        d = model.distribution(out["features"])
        mg, tot = r.home_score - r.away_score, r.home_score + r.away_score
        s_k, t_k = half(-float(gl.loc[r.game_id, "spread_line"])), half(float(gl.loc[r.game_id, "total_line"]))
        # nflverse spread_line > 0 = home favoured; "home wins by more than s" with s = -spread_line
        rows.append(dict(
            game_id=r.game_id, week=r.week, home=norm(r.home_team), away=norm(r.away_team),
            gameday=str(r.gameday), gametime=str(gl.loc[r.game_id, "gametime"]),
            y_ml=1.0 if mg > 0 else (0.5 if mg == 0 else 0.0),
            p_ml=NFLPregameModel.p_moneyline_home(d), c_ml=clim["home_win_rate_ex_ties"],
            y_sp=1.0 if mg > s_k else 0.0, p_sp=NFLPregameModel.p_spread_home_covers(d, s_k),
            c_sp=1 - _phi((s_k - clim["mean_margin"]) / clim["sd_margin"]),
            y_to=1.0 if tot > t_k else 0.0, p_to=NFLPregameModel.p_total_over(d, t_k),
            c_to=1 - _phi((t_k - clim["mean_total"]) / clim["sd_total"])))
    df = pd.DataFrame(rows)
    res = {"season": 2025, "n_games": int(len(df)), "vs_climatology": {}, "vs_market_mid": {}, "mde_and_verdicts": {}}
    for k, nm in (("ml", "moneyline"), ("sp", "spread@sportsbook-line-strike"), ("to", "game_total@sportsbook-line-strike")):
        d = (((df["c_" + k] - df["y_" + k]) ** 2) - ((df["p_" + k] - df["y_" + k]) ** 2)).to_numpy()
        res["vs_climatology"][nm] = boot(d)

    teams = set(df.home) | set(df.away)
    sets = {}
    for l in open(a.candles):
        r = json.loads(l)
        # FENCE: only 2025-season tickers (kickoff Sep-2025..Jan-2026). 2026-season markets are never parsed.
        if not (r["ticker"].split("-")[1][:5] in ("25AUG", "25SEP", "25OCT", "25NOV", "25DEC", "26JAN")):
            continue
        if r.get("candles"):
            sets[(r["ticker"], r["period_min"])] = r["candles"]
    mres = {}
    tks = {k[0] for k in sets}
    for l in open(a.markets):
        r = json.loads(l)
        if r["ticker"] not in tks:
            continue
        mres[r["ticker"]] = r.get("result")
    et = ZoneInfo("America/New_York")
    home_tk = {}
    for (tk, per) in sets:
        sp = split_ticker(tk, teams)
        if sp and sp[2] == sp[1]:
            home_tk[(sp[1], sp[0], sp[3])] = tk
    mk = {h: [] for h in HORIZONS_H}
    for g in df.itertuples():
        dt = datetime(*map(int, g.gameday.split("-")))
        tk = home_tk.get((g.home, g.away, dt.strftime("%y%b%d").upper()))
        if not tk or mres.get(tk) not in ("yes", "no"):
            continue
        ko = datetime(*map(int, g.gameday.split("-")), *map(int, g.gametime.split(":")[:2]), tzinfo=et).timestamp()
        for h, hrs in HORIZONS_H.items():
            m = mid_at(sets, tk, ko - hrs * 3600)
            if m is not None:
                mk[h].append(dict(week=g.week, y=1.0 if mres[tk] == "yes" else 0.0, p=g.p_ml, c=g.c_ml, mid=m,
                                  ym=g.y_ml))
    for h, lst in mk.items():
        m = pd.DataFrame(lst)
        if len(m) < 10:
            res["vs_market_mid"][h] = {"n": int(len(m))}
            continue
        dm = (((m.mid - m.y) ** 2) - ((m.p - m.y) ** 2)).to_numpy()
        dc = (((m.c - m.y) ** 2) - ((m.p - m.y) ** 2)).to_numpy()
        res["vs_market_mid"][h] = {"model_vs_mid": boot(dm), "model_vs_clim_same_games": boot(dc),
                                   "brier_mid": float(((m.mid - m.y) ** 2).mean()),
                                   "brier_model": float(((m.p - m.y) ** 2).mean()),
                                   "weeks_covered": sorted(set(int(w) for w in m.week))}
    # MDE + verdict probabilities. SD: market comparison uses the measured SD per horizon; clim uses measured SDs.
    for h, v in res["vs_market_mid"].items():
        if "model_vs_mid" not in v:
            continue
        sd, est = v["model_vs_mid"]["sd"], v["model_vs_mid"]["mean"]
        res["mde_and_verdicts"][h] = {
            "sd_assumed_in_prereg": 0.07, "sd_measured": sd,
            "MDE_n60_measured": mde(sd, 60), "MDE_n150_measured": mde(sd, 150),
            "MDE_n60_prereg_sd": mde(0.07, 60), "MDE_n150_prereg_sd": mde(0.07, 150),
            "verdict_probs_n60": {f"true_delta={mu:+.4f}": verdict_probs(mu, sd, 60)
                                  for mu in (est, -0.02, -0.01, 0.0, 0.01, 0.02)},
            "verdict_probs_n150": {f"true_delta={mu:+.4f}": verdict_probs(mu, sd, 150)
                                   for mu in (est, -0.02, -0.01, 0.0, 0.01, 0.02)}}
    for nm, v in res["vs_climatology"].items():
        res["mde_and_verdicts"]["clim_" + nm] = {"sd_measured": v["sd"], "MDE_n60": mde(v["sd"], 60),
                                                 "MDE_n150": mde(v["sd"], 150),
                                                 "P_CI_excludes_zero_at_estimate_n60": 1 - verdict_probs(-v["mean"], v["sd"], 60)["KEEP_ACCRUING"]}
    outp = safe_out(HERE / "results.json")
    outp.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
