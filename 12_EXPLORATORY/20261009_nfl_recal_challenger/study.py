"""EXPLORATORY -- NFL recalibration challenger vs frozen EXP-037 (W61.3 Part B). Not a verdict.

Reads: public nflverse copies (schedule/team_stats parquet), models/nfl_pregame_v1.json (frozen,
read-only), archived 2025 KXNFLGAME candles. Pre-2026 seasons only. Writes only via safe_out().
Challenger: walk-forward probit-Platt refit; week w of 2025 uses 2024 + 2025 weeks < w.
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
from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import (  # noqa: E402
    FEATURE_NAMES, NFLPregameFeatureBuilder,
)
from prediction_market_bot.pregame_shadow.nfl_model import NFLPregameModel, _phi  # noqa: E402

KMAP = {"JAX": "JAX", "LA": "LA", "LAR": "LA", "WAS": "WAS", "WSH": "WAS", "LV": "LV", "OAK": "LV"}
B, SEED = 2000, 20261009


def norm(t: str) -> str:
    return KMAP.get(t, t)


def fit_platt(z, y, a0=1.0, b0=0.0):
    a, b = a0, b0
    for _ in range(50):
        eta = a * z + b
        p = np.clip(np.array([_phi(e) for e in eta]), 1e-6, 1 - 1e-6)
        pdf = np.exp(-0.5 * eta**2) / math.sqrt(2 * math.pi)
        w = pdf**2 / (p * (1 - p))
        g = (y - p) * pdf / (p * (1 - p))
        X = np.column_stack([z, np.ones_like(z)])
        step = np.linalg.solve(X.T @ (X * w[:, None]) + 1e-9 * np.eye(2), X.T @ g)
        a, b = a + step[0], b + step[1]
    return a, b


def boot(d, B=B, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(d)
    m = d[rng.integers(0, n, (B, n))].mean(1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def split_ticker(tk, teams):
    ev, side = tk.rsplit("-", 1)[0], tk.rsplit("-", 1)[1]
    body = ev.split("-")[1][7:]  # strip yyMONdd
    for i in (2, 3):
        a, h = body[:i], body[i:]
        if norm(a) in teams and norm(h) in teams:
            return norm(a), norm(h), norm(side)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", required=True)
    ap.add_argument("--team-stats", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--candles", required=True)
    ap.add_argument("--markets", required=True)
    a = ap.parse_args()
    sched, stats = pd.read_parquet(a.schedule), pd.read_parquet(a.team_stats)
    model = NFLPregameModel.load(a.model)
    sm = model.a["sigma_margin"]
    fb = NFLPregameFeatureBuilder(stats, sched)
    reg = sched[(sched.game_type == "REG") & sched.home_score.notna() & sched.season.isin([2024, 2025])]
    rows = []
    for r in reg.itertuples():
        as_of = datetime(*map(int, str(r.gameday).split("-")), tzinfo=timezone.utc)
        out = fb.row(r.home_team, r.away_team, as_of, r.home_rest, r.away_rest)
        if out is None:
            continue
        f = out["features"]
        raw = model._lin("margin", f)
        mg = r.home_score - r.away_score
        rows.append(dict(game_id=r.game_id, season=r.season, week=r.week, home=norm(r.home_team),
                         away=norm(r.away_team), gameday=str(r.gameday), gametime=str(r.gametime),
                         z=raw / sm, y=1.0 if mg > 0 else (0.5 if mg == 0 else 0.0),
                         p_frozen=NFLPregameModel.p_moneyline_home(model.distribution(f))))
    df = pd.DataFrame(rows)
    clim = model.a["climatology"]["home_win_rate_ex_ties"]
    cal = df[df.season == 2024]
    ho = df[df.season == 2025].assign()
    pc = []
    for w, g in ho.groupby("week"):
        prior = pd.concat([cal, ho[ho.week < w]])
        prior = prior[prior.y != 0.5]
        aa, bb = fit_platt(prior.z.to_numpy(), prior.y.to_numpy(), model.a["platt"]["a"], model.a["platt"]["b"])
        pc += [(i, _phi(aa * z + bb)) for i, z in zip(g.index, g.z)]
    ho["p_chal"] = pd.Series(dict(pc))
    ho["p_clim"] = clim
    res = {"n_games_2025": int(len(ho)), "brier": {}, "delta_vs_frozen": {}}
    for k in ("p_frozen", "p_chal", "p_clim"):
        res["brier"][k] = float(((ho[k] - ho.y) ** 2).mean())
    d = (((ho.p_chal - ho.y) ** 2) - ((ho.p_frozen - ho.y) ** 2)).to_numpy()
    res["delta_vs_frozen"]["chal_minus_frozen_brier"] = dict(zip(("mean", "lo95", "hi95"), boot(d)))
    res["late_season_wk10plus"] = None
    late = ho[ho.week >= 10]
    dl = (((late.p_chal - late.y) ** 2) - ((late.p_frozen - late.y) ** 2)).to_numpy()
    res["late_season_wk10plus"] = dict(n=int(len(late)), **dict(zip(("mean", "lo95", "hi95"), boot(dl))))

    # ---- market subset: 2025 KXNFLGAME candles, price at kickoff-30min ----
    teams = set(df.home) | set(df.away)
    sets = {}
    for l in open(a.candles):
        r = json.loads(l)
        if r.get("period_min") == 1 and r.get("candles"):
            sets[r["ticker"]] = r["candles"]
    mres = {}
    for l in open(a.markets):
        r = json.loads(l)
        mres[r["ticker"]] = r.get("result")
    mk = []
    et = ZoneInfo("America/New_York")
    for tk, cs in sets.items():
        sp = split_ticker(tk, teams)
        if not sp:
            continue
        away, home, side = sp
        if side != home:
            continue
        g = ho[(ho.home == home) & (ho.away == away)]
        if len(g) != 1:
            continue
        g = g.iloc[0]
        ko = datetime(*map(int, str(g.gameday).split("-")), *map(int, str(g.gametime).split(":")[:2]), tzinfo=et).timestamp()
        cand = [c for c in cs if c["t"] <= ko - 1800 and c["ask"]["close"] is not None and c["bid"]["close"] is not None]
        if not cand or mres.get(tk) not in ("yes", "no"):
            continue
        c = cand[-1]
        if ko - 1800 - c["t"] > 3600:
            continue
        mk.append(dict(game_id=g.game_id, p_frozen=g.p_frozen, p_chal=g.p_chal, ask=c["ask"]["close"],
                       bid=c["bid"]["close"], y=1.0 if mres[tk] == "yes" else 0.0))
    m = pd.DataFrame(mk)
    res["market_subset"] = {"n": int(len(m))}
    if len(m) >= 10:
        m["mid"] = (m.ask + m.bid) / 2
        for k in ("p_frozen", "p_chal", "mid"):
            res["market_subset"][f"brier_{k}"] = float(((m[k] - m.y) ** 2).mean())
        for k in ("p_frozen", "p_chal"):
            dd = (((m[k] - m.y) ** 2) - ((m.mid - m.y) ** 2)).to_numpy()
            res["market_subset"][f"{k}_minus_mid"] = dict(zip(("mean", "lo95", "hi95"), boot(dd)))
        dd = (((m.p_chal - m.y) ** 2) - ((m.p_frozen - m.y) ** 2)).to_numpy()
        res["market_subset"]["chal_minus_frozen"] = dict(zip(("mean", "lo95", "hi95"), boot(dd)))
        # net-of-cost: buy the side where model_p exceeds ask (or 1-model_p exceeds 1-bid) by > 0 edge
        for k in ("p_frozen", "p_chal"):
            pnl, nb = 0.0, 0
            for r in m.itertuples():
                p = getattr(r, k)
                if p > r.ask:
                    cost, win = r.ask, r.y
                elif (1 - p) > (1 - r.bid):
                    cost, win = 1 - r.bid, 1 - r.y
                else:
                    continue
                fee = 0.07 * cost * (1 - cost)
                pnl += win - cost - fee
                nb += 1
            res["market_subset"][f"{k}_flat1_net_pnl_k007"] = dict(bets=nb, per_bet=pnl / nb if nb else None)
    outp = safe_out(HERE / "results.json")
    outp.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
