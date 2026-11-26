"""W129.7 Part B: replay of the NHL in-play arithmetic pricer over recorded 2026-27 games (event store, game-clock time).

Run: python3 replay.py <NHL_EVENTS dir> <out_json>

SCOPE (stated): scores the pricer against OUTCOMES at game-clock checkpoints. It does NOT compare to Kalshi: the event store has
game-clock time only (no wall clock) and the price archive snapshots every ~20 min (W103.3), so a same-timestamp Kalshi
comparison is not possible on a replay; that comes from forward live capture (scripts/nhl_inplay_shadow.py).
Pre-game rates are the walk-forward team attack/defence proxy (W103.3), because the box-only NHL engine inputs are not in this
replay; the pricer code path is the production one (c3_forecasting.nhl_inplay.price_ticker). Score effects not modelled; OT/SO
abstain. Test games = every 2026-27 game with play-by-play, in start-time order; ratings update walk-forward over 2021-22 onward.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.c3_forecasting import nhl_inplay as ip  # noqa: E402
from prediction_market_bot.quant.inplay_nhl import classify_state  # noqa: E402

store, out = Path(sys.argv[1]), Path(sys.argv[2])
G, E = [], []
for yr in range(2021, 2027):
    g = pd.read_parquet(store / f"games_{yr}.parquet")
    e = pd.read_parquet(store / f"events_{yr}.parquet", columns=[
        "game_id", "sort_order", "period", "period_type", "time_in_period_s", "type", "owner_is_home",
        "home_skaters", "away_skaters", "home_goalie", "away_goalie"])
    G.append(g[(g.game_type == 2) & g.has_pbp])
    E.append(e)
G = pd.concat(G).sort_values("start_time_utc").reset_index(drop=True)
E = pd.concat(E)
E = E[E.game_id.isin(G.game_id)].sort_values(["game_id", "period", "sort_order"])
gl = E[(E.type == "goal") & E.period_type.isin(["REG", "OT"])]
reg = gl[gl.period_type == "REG"].groupby(["game_id", "owner_is_home"]).size().unstack(fill_value=0)
reg = reg.rename(columns={True: "reg_h", False: "reg_a", 1: "reg_h", 0: "reg_a"}).reindex(columns=["reg_h", "reg_a"]).fillna(0)
G = G.join(reg, on="game_id")
G[["reg_h", "reg_a"]] = G[["reg_h", "reg_a"]].fillna(0).astype(int)
G["total"] = (gl.groupby("game_id").size().reindex(G.game_id).fillna(0).values).astype(int)
G["home_won"] = (G.home_score > G.away_score).astype(int)
G["margin"] = G.home_score - G.away_score
train = G[G.season < 2026]
mu_h, mu_a, K = train.reg_h.mean(), train.reg_a.mean(), 0.03
att, dfn = defaultdict(float), defaultdict(float)
lam_h, lam_a = [], []
for r in G.itertuples():
    eh, ea = mu_h + att[r.home] + dfn[r.away], mu_a + att[r.away] + dfn[r.home]
    lam_h.append(eh); lam_a.append(ea)
    att[r.home] += K * (r.reg_h - eh); dfn[r.away] += K * (r.reg_h - eh)
    att[r.away] += K * (r.reg_a - ea); dfn[r.home] += K * (r.reg_a - ea)
G["lam_h"], G["lam_a"] = np.clip(lam_h, 1.5, 5.0), np.clip(lam_a, 1.5, 5.0)

CK = {"P1_10m_in": (1, 600), "P1_end": (1, 1200), "P2_10m_in": (2, 600), "P2_end": (2, 1200),
      "P3_10m_left": (3, 600), "P3_5m_left": (3, 900), "P3_2m_left": (3, 1080)}
te = G[G.season == 2026]
ed = {gid: d for gid, d in E.groupby("game_id")}
rows = []
for r in te.itertuples():
    d = ed.get(r.game_id)
    if d is None:
        continue
    for name, (per, sec) in CK.items():
        past = d[(d.period < per) | ((d.period == per) & (d.time_in_period_s <= sec)) & (d.period_type == "REG")]
        past = past[past.period_type == "REG"]
        if past.empty:
            continue
        g_ = past[past.type == "goal"]
        sh, sa = int(g_.owner_is_home.astype(bool).sum()), int((~g_.owner_is_home.astype(bool)).sum())
        last = past.iloc[-1]
        sk = [last.home_skaters, last.away_skaters, last.home_goalie, last.away_goalie]
        strength = "EV" if (sec in (1200,) or pd.isna(sk).any()) else classify_state(*[int(x) for x in sk])
        ml = ((3 - per) * 1200 + (1200 - sec)) / 60.0
        state = dict(minutes_left_reg=ml, strength=strength, score_h=sh, score_a=sa, period_type="REG")
        base = dict(minutes_left_reg=60.0, strength="EV", score_h=0, score_a=0, period_type="REG")
        tick = {"GAME": "KXNHLGAME-26NOV25AAABBB-BBB", "SPREAD": "KXNHLSPREAD-26NOV25AAABBB-BBB2", "TOTAL": "KXNHLTOTAL-26NOV25AAABBB-6"}
        for cell, (fam, y) in {"NHL_MONEYLINE": ("GAME", r.home_won), "NHL_PUCK_LINE": ("SPREAD", int(r.margin >= 2)),
                               "NHL_GAME_TOTAL": ("TOTAL", int(r.total >= 6))}.items():
            p_in = ip.price_state(r.lam_h, r.lam_a, state)
            p0 = ip.price_state(r.lam_h, r.lam_a, base)
            if p_in is None:
                continue
            if fam == "GAME":
                pm, pb = p_in["game_home"], p0["game_home"]
            elif fam == "SPREAD":
                pm = ip.p_win_by_over_reg(sh, sa, ml, r.lam_h, r.lam_a, strength, "home", 1.5)
                pb = ip.p_win_by_over_reg(0, 0, 60.0, r.lam_h, r.lam_a, "EV", "home", 1.5)
            else:
                from prediction_market_bot.quant import inplay_nhl as q
                pm = q.p_total_over(sh, sa, ml, r.lam_h, r.lam_a, 5.5, strength, ip.STATES)
                pb = q.p_total_over(0, 0, 60.0, r.lam_h, r.lam_a, 5.5, "EV", ip.STATES)
            rows.append(dict(game_id=int(r.game_id), cell=cell, ck=name, p=float(np.clip(pm, .001, .999)),
                             p0=float(np.clip(pb, .001, .999)), y=int(y)))
R = pd.DataFrame(rows)
rng = np.random.default_rng(129)
res = {"n_games": int(R.game_id.nunique()), "n_rows": len(R), "cells": {}}
for cell, d in R.groupby("cell"):
    c = {}
    for ck, e in list(d.groupby("ck")) + [("ALL", d)]:
        bm, b0 = float(((e.p - e.y) ** 2).mean()), float(((e.p0 - e.y) ** 2).mean())
        gids = e.game_id.unique()
        per_g = e.assign(dd=(e.p - e.y) ** 2 - (e.p0 - e.y) ** 2).groupby("game_id").dd.agg(["sum", "count"])
        diffs = []
        for _ in range(1000):
            s = per_g.loc[rng.choice(gids, len(gids))]
            diffs.append(s["sum"].sum() / s["count"].sum())
        c[ck] = dict(rows=len(e), games=len(gids), brier_inplay=round(bm, 4), brier_pregame_only=round(b0, 4),
                     delta=round(bm - b0, 4), delta_ci95=[round(float(np.percentile(diffs, 2.5)), 4), round(float(np.percentile(diffs, 97.5)), 4)])
    res["cells"][cell] = c
out.write_text(json.dumps(res, indent=1))
for cell, c in res["cells"].items():
    a = c["ALL"]
    print(f"{cell}: rows {a['rows']} games {a['games']} Brier in-play {a['brier_inplay']} vs pregame-only {a['brier_pregame_only']} delta {a['delta']} CI {a['delta_ci95']}")
