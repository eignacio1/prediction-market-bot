"""W126.3 Part B stage 3: the plate-appearance outcome model (ADR-0073, ADR-0075).

Applies: for one batter against one pitcher, a probability over seven PA outcomes (K, BB/HBP, 1B, 2B, 3B, HR, in-play
out) built from point-in-time counts: the batter's own record against that pitcher's hand and the pitcher's own record
against that batter's side, each shrunk to the league rate for the stand/throws matchup, then combined by the
odds-ratio (generalised log5) rule  p_c ~ lg_c * (b_c/lg_c) * (p_c/lg_c)  and renormalised.
Point-in-time: every count is the cumulative sum over game dates STRICTLY before the game (`asof_prior`). League rates are
a frozen fit on the training window only (Hard Rule 4: no retraining in production).
Does not apply: park and weather (stated, not corrected), fielder / umpire effects, in-game fatigue and times-through-order,
batter-pitcher pair history, and a lineup other than the one handed in (the backtest hands in the as-played nine, a known
small leak that the live path replaces with the posted lineup). Shrinkage constants are set before the held-out look.
"""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

from prediction_market_bot.mlb_engine.lineup_aware import BF_START0, K_START, asof_prior

CLASSES = ("K", "BB", "1B", "2B", "3B", "HR", "OUT")
NC = len(CLASSES)
HIT = np.array([0, 0, 1, 1, 1, 1, 0], bool)
K_B = 150.0      # PA of shrinkage, batter vs a pitcher hand, toward the league rate for that matchup
K_P = 300.0      # BF of shrinkage, pitcher vs a batter side
K_PEN = 600.0    # BF of shrinkage, a team's relief corps toward the league relief rate
PEN_R_SHARE = 0.72   # league share of relief BF thrown right-handed (fixed prior, set before the look)
_EV = {"strikeout": 0, "strikeout_double_play": 0, "walk": 1, "intent_walk": 1, "hit_by_pitch": 1, "catcher_interf": 1,
       "single": 2, "double": 3, "triple": 4, "home_run": 5}
_CC = [f"c{i}" for i in range(NC)]


def classify(events: pd.Series) -> pd.Series:
    """PA outcome class 0..6 (everything not named is an in-play out, incl. errors, sacs, DP); truncated PAs are NaN."""
    c = events.map(lambda e: _EV.get(e, 6))
    return c.where(events != "truncated_pa")


def _hand(s: pd.Series) -> np.ndarray:
    return (s.to_numpy() == "R").astype(np.int64)        # L = 0, R = 1


def prep(pa: pd.DataFrame) -> pd.DataFrame:
    """PA frame with class, batter-side / pitcher-hand codes and the fielding team."""
    d = pa.copy()
    d["cls"] = classify(d["events"])
    d = d[d["cls"].notna()].copy()
    d["cls"] = d["cls"].astype(int)
    d["sh"] = _hand(d["stand"])
    d["th"] = _hand(d["p_throws"])
    d["fld"] = np.where(d["inning_topbot"] == "Top", d["home_team"], d["away_team"])
    return d


def fit_league(d: pd.DataFrame) -> np.ndarray:
    """league[stand, throws, class] rates from the training PA (frozen)."""
    out = np.zeros((2, 2, NC))
    for s in (0, 1):
        for t in (0, 1):
            m = d[(d.sh == s) & (d.th == t)]["cls"].to_numpy()
            c = np.bincount(m, minlength=NC) + 1.0
            out[s, t] = c / c.sum()
    return out


def _cum(d: pd.DataFrame, key: str, kcol: str) -> pd.DataFrame:
    """Inclusive per-date cumulative class counts for (key, hand) -> composite integer key `kh`."""
    g = d.assign(kh=d[key].astype("int64") * 2 + d[kcol]).groupby(["kh", "game_date", "cls"]).size().unstack(fill_value=0)
    g = g.reindex(columns=range(NC), fill_value=0)
    g.columns = _CC
    g = g.reset_index().sort_values(["kh", "game_date"])
    g[_CC] = g.groupby("kh")[_CC].cumsum()
    return g


def _cum_team(d: pd.DataFrame, pen: pd.DataFrame) -> pd.DataFrame:
    g = pen.groupby(["fld", "game_date", "cls"]).size().unstack(fill_value=0).reindex(columns=range(NC), fill_value=0)
    g.columns = _CC
    g = g.reset_index().sort_values(["fld", "game_date"])
    g[_CC] = g.groupby("fld")[_CC].cumsum()
    return g


class PAHistory:
    """Cumulative count tables built once from all PA through the last date you will ask about."""

    def __init__(self, pa: pd.DataFrame, games: pd.DataFrame):
        d = prep(pa)
        self.stand_mode = d.groupby(["batter", "th"])["sh"].agg(lambda s: int(s.mean() >= 0.5))
        self.throws = pa.groupby("pitcher")["p_throws"].agg(lambda s: int(s.value_counts().index[0] == "R"))
        self.bat = _cum(d, "batter", "th")          # batter vs pitcher hand
        self.pit = _cum(d, "pitcher", "sh")         # pitcher vs batter side
        st = pd.concat([games[["game_pk", "home_starter"]].rename(columns={"home_starter": "pitcher"}),
                        games[["game_pk", "away_starter"]].rename(columns={"away_starter": "pitcher"})])
        st["is_st"] = True
        pen = d.merge(st, on=["game_pk", "pitcher"], how="left")
        self.pen = _cum_team(d, pen[pen.is_st.isna()])
        s = pd.concat([games[["game_pk", "game_date", "home_starter"]].rename(columns={"home_starter": "pitcher"}),
                       games[["game_pk", "game_date", "away_starter"]].rename(columns={"away_starter": "pitcher"})])
        bf = d.groupby(["game_pk", "pitcher"]).size().rename("bf").reset_index()
        s = s.merge(bf, on=["game_pk", "pitcher"], how="left").fillna({"bf": 0.0})
        s["starts"] = 1.0
        g = s.groupby(["pitcher", "game_date"], as_index=False)[["starts", "bf"]].sum().sort_values(["pitcher", "game_date"])
        g[["starts", "bf"]] = g.groupby("pitcher")[["starts", "bf"]].cumsum()
        self.start = g


def _counts(left: pd.DataFrame, cum: pd.DataFrame, key: str, lkey: str) -> np.ndarray:
    m = asof_prior(left[[lkey, "game_date"]], cum, key, left_key=lkey)
    return m[_CC].fillna(0.0).to_numpy()


def combine(b_cnt, p_cnt, lg, k_b=K_B, k_p=K_P) -> np.ndarray:
    """Odds-ratio combination of two shrunk rate vectors against the league rate (rows = matchups)."""
    rb = (b_cnt + k_b * lg) / (b_cnt.sum(1, keepdims=True) + k_b)
    rp = (p_cnt + k_p * lg) / (p_cnt.sum(1, keepdims=True) + k_p)
    w = lg * (rb / lg) * (rp / lg)
    return w / w.sum(1, keepdims=True)


def game_inputs(games: pd.DataFrame, lineups: pd.DataFrame, hist: PAHistory, league: np.ndarray) -> Dict[str, np.ndarray]:
    """Per game: P[g, bat_side, ptype, slot, class] (bat_side 0 = away bats, ptype 0 = opposing starter, 1 = relief),
    bf_mean[g, bat_side] (expected batters faced by the opposing starter) and the nine batter ids. Games lacking a full
    lineup or a starter on either side are dropped (listed in `game_pk`)."""
    lu = lineups[lineups.slot.between(1, 9)]
    ok = lu.groupby(["game_pk", "team_side"]).size().unstack().reindex(columns=["away", "home"]).eq(9).all(axis=1)
    g = games[games.game_pk.isin(ok[ok].index) & games.home_starter.notna() & games.away_starter.notna()].reset_index(drop=True)
    G = len(g)
    rows = []
    for s, side in enumerate(("away", "home")):
        opp_pit = g["home_starter" if side == "away" else "away_starter"]
        opp_team = g["home_team" if side == "away" else "away_team"]
        l = lu[lu.team_side == side].merge(g[["game_pk", "game_date"]].assign(pit=opp_pit, fld=opp_team), on="game_pk")
        l["bs"] = s
        rows.append(l)
    r = pd.concat(rows, ignore_index=True)
    r["th"] = r["pit"].astype("int64").map(hist.throws).fillna(1).astype(int)
    r["sh"] = [hist.stand_mode.get((b, t), 1) for b, t in zip(r.batter, r.th)]
    r["kh_bat"] = r.batter.astype("int64") * 2 + r.th
    r["kh_batL"], r["kh_batR"] = r.batter.astype("int64") * 2, r.batter.astype("int64") * 2 + 1
    r["kh_pit"] = r.pit.astype("int64") * 2 + r.sh
    b_main = _counts(r, hist.bat, "kh", "kh_bat")
    b_pen = PEN_R_SHARE * _counts(r, hist.bat, "kh", "kh_batR") + (1 - PEN_R_SHARE) * _counts(r, hist.bat, "kh", "kh_batL")
    p_cnt = _counts(r, hist.pit, "kh", "kh_pit")
    t_cnt = _counts(r, hist.pen, "fld", "fld")
    lg = league[r.sh.to_numpy(), r.th.to_numpy()]
    lg_pen = PEN_R_SHARE * league[r.sh.to_numpy(), 1] + (1 - PEN_R_SHARE) * league[r.sh.to_numpy(), 0]
    p_start = combine(b_main, p_cnt, lg)
    p_pen = combine(b_pen, t_cnt, lg_pen, k_p=K_PEN)
    # expected batters faced by the opposing starter, shrunk to a league starter
    sc = asof_prior(r[["pit", "game_date"]].rename(columns={"pit": "pitcher"}), hist.start, "pitcher")
    bf_mean = ((sc["bf"].fillna(0.0) + K_START * BF_START0) / (sc["starts"].fillna(0.0) + K_START)).to_numpy()
    P = np.zeros((G, 2, 2, 9, NC))
    gi = {pk: i for i, pk in enumerate(g.game_pk)}
    ix, sl = r.game_pk.map(gi).to_numpy(), (r.slot.to_numpy() - 1)
    P[ix, r.bs.to_numpy(), 0, sl] = p_start
    P[ix, r.bs.to_numpy(), 1, sl] = p_pen
    bf = np.zeros((G, 2))
    bf[ix, r.bs.to_numpy()] = bf_mean
    ids = np.zeros((G, 2, 9), dtype=np.int64)
    ids[ix, r.bs.to_numpy(), sl] = r.batter.to_numpy()
    return {"game_pk": g.game_pk.to_numpy(), "game_date": g.game_date.to_numpy(), "P": P, "bf_mean": bf, "batter_id": ids}
