"""W126.3 Part B stage 5: the whole MLB board from ONE set of simulation draws (ADR-0073, W110.4 `quant/sgp.py`).

Applies: every Kalshi MLB rung (moneyline, run-line ladder, total ladder, team totals) AND each starter's batter-hits
ladder (>=1, >=2) priced from the same draws, column names identical to `board.price_board` so the existing scorers read
it unchanged. Because the legs share the draw index, same-game parlays price from the draws (`joint_leg`).
Rung units follow Kalshi: KXMLBTOTAL k = total >= k; KXMLBSPREAD k = win by >= k; KXMLBTEAMTOTAL k = team runs >= k.
Does not apply: anything the draws do not carry (see `sim.py`). Monte Carlo error is sqrt(p(1-p)/n) and is reported.
"""
from __future__ import annotations

from typing import Dict

import numpy as np

from prediction_market_bot.mlb_engine.board import SPREAD_RUNGS, TEAM_RUNGS, TOTAL_RUNGS
from prediction_market_bot.mlb_engine.sim import simulate
from prediction_market_bot.quant import sgp

HIT_RUNGS = (1, 2)


def price_draws(draws: Dict[str, np.ndarray]) -> Dict[str, float]:
    hr, ar = draws["home_runs"], draws["away_runs"]
    margin, tot = hr - ar, hr + ar
    out: Dict[str, float] = {"p_home_ml": float(np.mean(margin > 0))}   # ties are resolved inside the sim (no half-credit)
    for k in TOTAL_RUNGS:
        out[f"ge_total_{k}"] = float(np.mean(tot >= k))
    for k in SPREAD_RUNGS:
        out[f"home_by_ge_{k}"] = float(np.mean(margin >= k))
        out[f"away_by_ge_{k}"] = float(np.mean(-margin >= k))
    for k in TEAM_RUNGS:
        out[f"home_runs_ge_{k}"] = float(np.mean(hr >= k))
        out[f"away_runs_ge_{k}"] = float(np.mean(ar >= k))
    h = draws["hits"]
    for s, side in enumerate(("away", "home")):
        for slot in range(9):
            for k in HIT_RUNGS:
                out[f"{side}_slot{slot + 1}_hits_ge_{k}"] = float(np.mean(h[:, s, slot] >= k))
    return out


def joint_leg(draws: Dict[str, np.ndarray], *legs) -> float:
    """P(all legs) from the draws. A leg is (kind, side, k): ('ml','home'), ('total', None, k), ('spread','home',k),
    ('team','home',k), ('hits','home:3',k) meaning the home slot-3 batter has >= k hits."""
    arrs = []
    hr, ar = draws["home_runs"], draws["away_runs"]
    for kind, side, *k in legs:
        if kind == "ml":
            arrs.append(hr > ar if side == "home" else ar > hr)
        elif kind == "total":
            arrs.append(sgp.leg(hr + ar, "ge", k[0]))
        elif kind == "spread":
            arrs.append(sgp.leg(hr - ar if side == "home" else ar - hr, "ge", k[0]))
        elif kind == "team":
            arrs.append(sgp.leg(hr if side == "home" else ar, "ge", k[0]))
        elif kind == "hits":
            sd, slot = side.split(":")
            arrs.append(sgp.leg(draws["hits"][:, 1 if sd == "home" else 0, int(slot) - 1], "ge", k[0]))
        else:
            raise ValueError(kind)
    return sgp.joint(*arrs)


def price_games(inputs: Dict[str, np.ndarray], n: int = 4000, seed: int = 0):
    """DataFrame, one row per game, from `pa_model.game_inputs`."""
    import pandas as pd
    rows = []
    for i, pk in enumerate(inputs["game_pk"]):
        d = simulate(inputs["P"][i], inputs["bf_mean"][i], n, seed + int(pk))
        r = price_draws(d)
        r["game_pk"], r["game_date"] = int(pk), inputs["game_date"][i]
        r["exp_home_runs"], r["exp_away_runs"] = float(d["home_runs"].mean()), float(d["away_runs"].mean())
        rows.append(r)
    return pd.DataFrame(rows)
