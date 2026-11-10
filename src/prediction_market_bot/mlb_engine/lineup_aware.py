"""Lineup-aware point-in-time inputs for the MLB game model (W106.4 Part A).

RULE (same as pit.py): a value used for a game on date D comes ONLY from pitches / plate appearances /
final scores with game_date STRICTLY BEFORE D. Same-day games (doubleheaders) never feed each other.
Mechanism: per-entity daily sums -> inclusive cumulative -> `merge_asof(allow_exact_matches=False)`.

Factor classes built here (ADR-0075 stage in brackets):
  * platoon: batter wOBA vs the starter's hand, starter wOBA allowed vs the lineup's stand mix  [applied]
  * starter projection: expected batters faced from prior starts -> starter/bullpen innings split  [applied]
  * bullpen: pitches thrown in the previous 1 and 3 calendar days, relief wOBA allowed  [applied]
  * park: home-vs-road run ratio of the home team, shrunk toward 1 (point-in-time)  [applied]

Does NOT apply: weather, umpire, injuries, the POSTED lineup. The lineup is the nine batters AS PLAYED
(first nine distinct batters), so a late scratch leaks. That leak is real, is flagged, and is fixed only by
a posted-lineup feed (next step). Doubleheader game 2 does not see game 1's relievers (strictly earlier date).
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

K_BAT = 200.0       # wOBA PA shrinkage toward league (same family as model.PRIOR_PA)
K_SPLIT = 300.0     # platoon split shrinks toward the player's own overall shrunk wOBA (untuned, set before test)
K_PEN = 300.0       # bullpen wOBA-allowed BF shrinkage toward league
K_START = 4.0       # starts of shrinkage for expected batters faced
BF_START0 = 22.0    # league-typical batters faced by a starter
BF_TEAM = 38.0      # league-typical batters faced by a team's whole staff in a game
K_PARK = 60.0       # games of shrinkage for the park ratio
L_SHARE0 = 0.38     # league share of PA by left-handed stand


# ---------------------------------------------------------------- generic point-in-time helpers

def _cum_inclusive(daily: pd.DataFrame, key: str, cols: List[str]) -> pd.DataFrame:
    d = daily.sort_values([key, "game_date"]).reset_index(drop=True)
    cs = d.groupby(key)[cols].cumsum()
    return pd.concat([d[[key, "game_date"]], cs], axis=1)


def _as_key(s: pd.Series) -> pd.Series:
    return s.astype("int64") if pd.api.types.is_numeric_dtype(s) else s


def asof_prior(left: pd.DataFrame, right_cum: pd.DataFrame, key: str, left_key: str = None) -> pd.DataFrame:
    """For each left row (left_key, game_date) attach the last right_cum row of `key` with date STRICTLY earlier."""
    lk = left_key or key
    l = left.copy()
    r = right_cum.copy()
    l["_k"] = _as_key(l[lk])
    r["_k"] = _as_key(r[key])
    l["_ord"] = np.arange(len(l))
    l = l.sort_values("game_date")
    r = r.drop(columns=[key]).sort_values("game_date")
    m = pd.merge_asof(l, r, on="game_date", by="_k", allow_exact_matches=False)
    return m.sort_values("_ord").drop(columns=["_k", "_ord"]).reset_index(drop=True)


def _fill0(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    df[cols] = df[cols].fillna(0.0)
    return df


# ---------------------------------------------------------------- platoon tables (from plate appearances)

def _pa_num(pa: pd.DataFrame) -> pd.DataFrame:
    d = pa.copy()
    d["num"] = pd.to_numeric(d["woba_value"], errors="coerce").fillna(0.0)
    d["den"] = pd.to_numeric(d["woba_denom"], errors="coerce").fillna(0.0)
    d["one"] = 1.0
    return d


BAT_COLS = ["n", "num", "den", "n_vsL", "num_vsL", "den_vsL", "n_vsR", "num_vsR", "den_vsR", "Lst_vsL", "Lst_vsR"]


def batter_platoon_cum(pa: pd.DataFrame) -> pd.DataFrame:
    """Inclusive cumulative per batter by pitcher hand: counts, wOBA sums and left-stand counts."""
    a = _pa_num(pa)
    hl = (a["p_throws"] == "L").astype(float)
    hr = 1.0 - hl
    isl = (a["stand"] == "L").astype(float)
    a["n"] = 1.0
    for h, m in (("L", hl), ("R", hr)):
        a[f"n_vs{h}"] = m
        a[f"num_vs{h}"] = a["num"] * m
        a[f"den_vs{h}"] = a["den"] * m
        a[f"Lst_vs{h}"] = isl * m
    g = a.groupby(["batter", "game_date"], as_index=False)[BAT_COLS].sum()
    return _cum_inclusive(g, "batter", BAT_COLS)


PIT_COLS = ["bf", "num", "den", "num_L", "den_L", "num_R", "den_R"]


def pitcher_platoon_cum(pa: pd.DataFrame) -> pd.DataFrame:
    """Inclusive cumulative per pitcher by batter stand."""
    a = _pa_num(pa)
    il = (a["stand"] == "L").astype(float)
    a["bf"] = 1.0
    a["num_L"], a["den_L"] = a["num"] * il, a["den"] * il
    a["num_R"], a["den_R"] = a["num"] * (1 - il), a["den"] * (1 - il)
    g = a.groupby(["pitcher", "game_date"], as_index=False)[PIT_COLS].sum()
    return _cum_inclusive(g, "pitcher", PIT_COLS)


def pitcher_hand(pa: pd.DataFrame) -> pd.Series:
    """Throwing hand per pitcher (a fixed attribute): the most common p_throws."""
    return pa.groupby("pitcher")["p_throws"].agg(lambda s: s.value_counts().index[0])


# ---------------------------------------------------------------- starter projection

def starter_proj_cum(games: pd.DataFrame, pa: pd.DataFrame) -> pd.DataFrame:
    """Inclusive cumulative of starts and batters faced by each pitcher WHEN HE STARTED."""
    st = pd.concat([
        games[["game_pk", "game_date", "home_starter"]].rename(columns={"home_starter": "pitcher"}),
        games[["game_pk", "game_date", "away_starter"]].rename(columns={"away_starter": "pitcher"}),
    ]).dropna(subset=["pitcher"])
    bf = pa.groupby(["game_pk", "pitcher"]).size().rename("start_bf").reset_index()
    st = st.merge(bf, on=["game_pk", "pitcher"], how="left").fillna({"start_bf": 0.0})
    st["starts"] = 1.0
    g = st.groupby(["pitcher", "game_date"], as_index=False)[["starts", "start_bf"]].sum()
    return _cum_inclusive(g, "pitcher", ["starts", "start_bf"])


# ---------------------------------------------------------------- bullpen

def _team_long(games: pd.DataFrame) -> pd.DataFrame:
    """(game_pk, game_date, team, starter) for both sides."""
    h = games[["game_pk", "game_date", "home_team", "home_starter"]].rename(columns={"home_team": "team", "home_starter": "starter"})
    a = games[["game_pk", "game_date", "away_team", "away_starter"]].rename(columns={"away_team": "team", "away_starter": "starter"})
    return pd.concat([h, a], ignore_index=True)


def _with_pitching_team(d: pd.DataFrame) -> pd.DataFrame:
    d = d.copy()
    d["team"] = np.where(d["inning_topbot"] == "Top", d["home_team"], d["away_team"])  # home pitches in the Top
    return d


def bullpen_daily(pitches: pd.DataFrame, pa: pd.DataFrame, games: pd.DataFrame) -> pd.DataFrame:
    """Per (team, game_date): relief pitches thrown, relief BF and relief wOBA sums (anyone but the starter)."""
    tl = _team_long(games)[["game_pk", "team", "starter"]]
    p = _with_pitching_team(pitches[["game_pk", "game_date", "pitcher", "inning_topbot", "home_team", "away_team"]])
    p = p.merge(tl, on=["game_pk", "team"], how="left")
    p = p[p["pitcher"] != p["starter"]]
    pg = p.groupby(["team", "game_date"], as_index=False).size().rename(columns={"size": "pen_pitches"})
    a = _pa_num(_with_pitching_team(pa[["game_pk", "game_date", "pitcher", "inning_topbot", "home_team", "away_team",
                                         "woba_value", "woba_denom"]]))
    a = a.merge(tl, on=["game_pk", "team"], how="left")
    a = a[a["pitcher"] != a["starter"]]
    ag = a.groupby(["team", "game_date"], as_index=False)[["one", "num", "den"]].sum().rename(
        columns={"one": "pen_bf", "num": "pen_num", "den": "pen_den"})
    return pg.merge(ag, on=["team", "game_date"], how="outer").fillna(0.0)


def bullpen_features(daily: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """targets: (team, game_date) rows. Adds pen_p1, pen_p3 (previous 1 / 3 calendar days), pen_num/den/bf cum prior."""
    t = targets[["team", "game_date"]].drop_duplicates().reset_index(drop=True)
    for lag in (1, 2, 3):
        s = daily[["team", "game_date", "pen_pitches"]].copy()
        s["game_date"] = s["game_date"] + pd.Timedelta(days=lag)
        t = t.merge(s.rename(columns={"pen_pitches": f"_l{lag}"}), on=["team", "game_date"], how="left")
    t = _fill0(t, ["_l1", "_l2", "_l3"])
    t["pen_p1"] = t["_l1"]
    t["pen_p3"] = t["_l1"] + t["_l2"] + t["_l3"]
    t = t.drop(columns=["_l1", "_l2", "_l3"])
    cum = _cum_inclusive(daily, "team", ["pen_bf", "pen_num", "pen_den"])
    t = asof_prior(t, cum, "team")
    return _fill0(t, ["pen_bf", "pen_num", "pen_den"])


# ---------------------------------------------------------------- park

def park_cum(games: pd.DataFrame) -> pd.DataFrame:
    """Inclusive cumulative per team: runs in home games vs road games (both teams' runs)."""
    tot = (games["home_runs"] + games["away_runs"]).astype(float)
    h = pd.DataFrame({"team": games["home_team"], "game_date": games["game_date"],
                      "h_runs": tot, "h_g": 1.0, "r_runs": 0.0, "r_g": 0.0})
    r = pd.DataFrame({"team": games["away_team"], "game_date": games["game_date"],
                      "h_runs": 0.0, "h_g": 0.0, "r_runs": tot, "r_g": 1.0})
    g = pd.concat([h, r]).groupby(["team", "game_date"], as_index=False)[["h_runs", "h_g", "r_runs", "r_g"]].sum()
    return _cum_inclusive(g, "team", ["h_runs", "h_g", "r_runs", "r_g"])


def park_log_factor(c: pd.DataFrame) -> pd.Series:
    """log( home runs/game over road runs/game ) shrunk by n/(n+K_PARK), n = min(home, road games); 0 if none."""
    hg, rg = c["h_g"].fillna(0.0), c["r_g"].fillna(0.0)
    ok = (hg > 0) & (rg > 0) & (c["h_runs"].fillna(0) > 0) & (c["r_runs"].fillna(0) > 0)
    hr = (c["h_runs"].fillna(0) / hg.where(hg > 0, 1)).where(ok, 1.0)
    rr = (c["r_runs"].fillna(0) / rg.where(rg > 0, 1)).where(ok, 1.0)
    raw = np.log(hr / rr)  # ratio is 1 (log 0) wherever the data is missing; masked again below
    n = np.minimum(hg, rg)
    return pd.Series(np.where(ok, raw * n / (n + K_PARK), 0.0), index=c.index)


# ---------------------------------------------------------------- the design

LINEUP_FEATURES = ["lineup_woba_vsH", "starter_woba_vs_lineup", "starter_share", "pen_woba_allowed",
                   "pen_fatigue", "park_logf", "is_home"]
BASE_FEATURES = ["lineup_woba", "starter_woba_allowed", "is_home"]  # the W105.3 model, for the ablation


def _shrink(num, den, mu, k):
    return (num.fillna(0.0) + k * mu) / (den.fillna(0.0) + k)


def design_lineup(games: pd.DataFrame, lineups: pd.DataFrame, pa: pd.DataFrame, pitches: pd.DataFrame,
                  mu: float) -> pd.DataFrame:
    """One row per (game, batting side) with every lineup-aware input, all point-in-time.

    `mu` is the league wOBA from the TRAINING seasons only. `games` need game_pk, game_date, teams, starters, runs.
    """
    games = games.dropna(subset=["home_starter", "away_starter"]).copy()
    hand = pitcher_hand(pa)
    bcum, pcum = batter_platoon_cum(pa), pitcher_platoon_cum(pa)
    scum = starter_proj_cum(games, pa)
    daily = bullpen_daily(pitches, pa, games)
    pcc = park_cum(games)

    # ---- park factor, one per game (home team's point-in-time ratio)
    gp = asof_prior(games[["game_pk", "game_date", "home_team"]].rename(columns={"home_team": "team"}), pcc, "team")
    gp["park_logf"] = park_log_factor(gp)
    park = gp.set_index("game_pk")["park_logf"]

    # ---- lineup platoon (batters vs the opposing starter's hand)
    lu = lineups.merge(games[["game_pk", "game_date", "home_starter", "away_starter"]], on="game_pk")
    lu["opp_starter"] = np.where(lu["team_side"] == "away", lu["home_starter"], lu["away_starter"])
    lu["H"] = lu["opp_starter"].map(hand)
    lu = asof_prior(lu, bcum, "batter")
    lu = _fill0(lu, BAT_COLS)
    overall = _shrink(lu["num"], lu["den"], mu, K_BAT)
    isL = lu["H"] == "L"
    nH = np.where(isL, lu["num_vsL"], lu["num_vsR"])
    dH = np.where(isL, lu["den_vsL"], lu["den_vsR"])
    lu["bat_vsH"] = (nH + K_SPLIT * overall) / (dH + K_SPLIT)
    paH = np.where(isL, lu["n_vsL"], lu["n_vsR"])
    lH = np.where(isL, lu["Lst_vsL"], lu["Lst_vsR"])
    lu["p_left"] = (lH + 2 * L_SHARE0) / (paH + 2)  # share of his PA vs this hand that came from the left side
    lu["bat_overall"] = overall
    team = lu.groupby(["game_pk", "team_side"], as_index=False).agg(
        lineup_woba_vsH=("bat_vsH", "mean"), lineup_woba=("bat_overall", "mean"),
        lineup_p_left=("p_left", "mean"), n_bat=("bat_vsH", "size"))

    # ---- starter (platoon-adjusted to the lineup's stand mix) and expected share of the game
    rows = []
    for side, st_col, pen_team in (("away", "home_starter", "home_team"), ("home", "away_starter", "away_team")):
        g = games[["game_pk", "game_date", st_col, pen_team, "home_runs", "away_runs"]].rename(
            columns={st_col: "pitcher", pen_team: "team"})
        g["runs"] = g["away_runs"] if side == "away" else g["home_runs"]
        g["team_side"] = side
        g = asof_prior(g, pcum, "pitcher")
        g = _fill0(g, PIT_COLS)
        s_over = _shrink(g["num"], g["den"], mu, K_BAT)
        sL = (g["num_L"] + K_SPLIT * s_over) / (g["den_L"] + K_SPLIT)
        sR = (g["num_R"] + K_SPLIT * s_over) / (g["den_R"] + K_SPLIT)
        g["_sL"], g["_sR"], g["starter_woba_allowed"] = sL, sR, s_over
        g = asof_prior(g, scum, "pitcher")
        g = _fill0(g, ["starts", "start_bf"])
        exp_bf = (g["start_bf"] + K_START * BF_START0) / (g["starts"] + K_START)
        g["starter_share"] = np.clip(exp_bf / BF_TEAM, 0.2, 0.8)
        rows.append(g)
    sd = pd.concat(rows, ignore_index=True)
    sd = sd.merge(team, on=["game_pk", "team_side"], how="inner")
    pl = sd["lineup_p_left"]
    sd["starter_woba_vs_lineup"] = sd["_sL"] * pl + sd["_sR"] * (1 - pl)

    # ---- bullpen of the fielding team (the one the batting side faces after the starter)
    bf = bullpen_features(daily, sd[["team", "game_date"]])
    sd = sd.merge(bf, on=["team", "game_date"], how="left")
    sd = _fill0(sd, ["pen_p1", "pen_p3", "pen_bf", "pen_num", "pen_den"])
    sd["pen_woba_allowed"] = _shrink(sd["pen_num"], sd["pen_den"], mu, K_PEN)
    # fatigue only matters through the share of the game the bullpen pitches: 100 pitches ~ a heavy 3 days
    sd["pen_fatigue"] = (1.0 - sd["starter_share"]) * sd["pen_p3"] / 100.0
    sd["park_logf"] = sd["game_pk"].map(park).fillna(0.0)
    sd["is_home"] = (sd["team_side"] == "home").astype(float)
    sd["game_date"] = pd.to_datetime(sd["game_date"])
    keep = ["game_pk", "game_date", "team_side", "runs", "n_bat", "lineup_woba", "starter_woba_allowed"] + \
           [c for c in LINEUP_FEATURES if c not in ("is_home",)] + ["is_home", "pen_p1", "pen_p3"]
    out = sd[list(dict.fromkeys(keep))]
    return out[out["n_bat"] >= 9].reset_index(drop=True)
