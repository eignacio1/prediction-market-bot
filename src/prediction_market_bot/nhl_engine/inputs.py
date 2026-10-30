"""NHL engine inputs (W97.4 Part A): point-in-time team strength from the shot store.

Every number a game's row carries is read BEFORE that game's own outcome is folded in (sequential pass over each team's
games in puck-drop order), so a game's features cannot contain the game. Per team: even-strength (5v5) expected goals
for/against per 60 (shot location and type -> xG, the xG model fit on EARLIER seasons only), power-play and penalty-kill
xG rates and the expected power-play time, the previous starter's goals-saved-above-expected, rest, and home ice.

Stage per factor (ADR-0075): 5v5 xG rates, special teams: applied (they enter a price). Goalie: interpreted (proxy only,
see ``GOALIE_STARTER_NOTE``). Rest: applied. Venue/officials/scratches/injuries: not built.

Applies to regular-season and playoff games with a play-by-play. Does not apply to the first ~10 games of a team's
first season in the store (the rates are the league mean until games accumulate: shrinkage, by design).
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd

GOALIE_STARTER_NOTE = (
    "The probable starter is NOT in the shot store before puck drop (GG-1010; the NHL confirms starters on game day, "
    "outside this store). The proxy is the goalie who started the team's previous game, and only his past games are used. "
    "A confirmed-starter feed is the registered gap; the factor is 'interpreted', not 'applied'.")

SHOT_TYPES = ("wrist", "snap", "slap", "backhand", "tip-in", "deflected", "wrap-around", "bat")
FENWICK = ("shot-on-goal", "goal", "missed-shot")
NET_X = 89.0


# ---------------------------------------------------------------- shots -> xG (fit on earlier seasons only)
def shots(ev: pd.DataFrame) -> pd.DataFrame:
    """Unblocked, non-shootout, non-empty-net attempts with geometry and the shooter's strength state."""
    s = ev[ev["type"].isin(FENWICK) & (ev["period_type"] != "SO") & ev["x"].notna() & ev["y"].notna()].copy()
    faced = np.where(s["owner_is_home"], s["away_goalie"], s["home_goalie"])
    s = s[faced == 1].copy()
    ax = s["x"].abs().astype(float)
    s["dist"] = np.hypot(NET_X - ax, s["y"].astype(float))
    s["angle"] = np.degrees(np.arctan2(s["y"].abs().astype(float), np.maximum(NET_X - ax, 0.5)))
    s["own_sk"] = np.where(s["owner_is_home"], s["home_skaters"], s["away_skaters"]).astype(float)
    s["opp_sk"] = np.where(s["owner_is_home"], s["away_skaters"], s["home_skaters"]).astype(float)
    s["state"] = np.select([(s.own_sk == 5) & (s.opp_sk == 5), s.own_sk > s.opp_sk, s.own_sk < s.opp_sk],
                           ["5v5", "pp", "pk"], "even_other")
    s["goal"] = (s["type"] == "goal").astype(int)
    return s


def design(s: pd.DataFrame) -> np.ndarray:
    st = s["shot_type"].fillna("other")
    cols = [s["dist"], s["dist"] ** 2 / 100, s["angle"], np.log1p(s["dist"]), (s["own_sk"] - s["opp_sk"]).clip(-2, 2)]
    cols += [(st == t).astype(float) for t in SHOT_TYPES]
    return np.column_stack(cols)


def xg_by_season(s: pd.DataFrame, first_test: int) -> pd.DataFrame:
    """Out-of-time xG: shots of season t scored by a model fit on seasons < t. Seasons before ``first_test`` are the
    burn-in (training only)."""
    from sklearn.linear_model import LogisticRegression
    out = []
    for t in sorted(s["season"].unique()):
        if t < first_test:
            continue
        m = LogisticRegression(C=1.0, max_iter=500).fit(design(s[s["season"] < t]), s.loc[s["season"] < t, "goal"])
        part = s[s["season"] == t].copy()
        part["xg"] = m.predict_proba(design(part))[:, 1]
        out.append(part)
    return pd.concat(out, ignore_index=True)


def state_seconds(ev: pd.DataFrame) -> pd.DataFrame:
    """Seconds each team spent at 5v5 / power play / short-handed per game (gaps between consecutive events in a
    period are attributed to the earlier event's skater counts; unbiased across teams, which is what a denominator needs)."""
    e = ev[ev["period_type"] != "SO"].sort_values(["game_id", "sort_order"]).copy()
    e["dt"] = (e.groupby(["game_id", "period"])["time_in_period_s"].shift(-1) - e["time_in_period_s"]).clip(0, 120)
    e = e[e["dt"].notna() & e["home_skaters"].notna()]
    out = []
    for side in ("home", "away"):
        own = e[f"{side}_skaters"]
        opp = e["away_skaters" if side == "home" else "home_skaters"]
        st = np.select([(own == 5) & (opp == 5), own > opp, own < opp], ["s5v5", "spp", "spk"], "sother")
        out.append(pd.DataFrame({"game_id": e["game_id"], "is_home": side == "home", "st": st, "dt": e["dt"]}))
    t = pd.concat(out).groupby(["game_id", "is_home", "st"])["dt"].sum().unstack(fill_value=0).reset_index()
    for c in ("s5v5", "spp", "spk"):
        if c not in t:
            t[c] = 0.0
    return t


def team_game_table(g: pd.DataFrame, sx: pd.DataFrame, ev: pd.DataFrame, bx: Optional[pd.DataFrame] = None) -> pd.DataFrame:
    """One row per (game, team): that game's xG for/against by state, seconds by state, regulation goals, rest context.
    ``g`` is the games table (games, regulation goals come from the play-by-play so overtime/shootout never leak in)."""
    a = sx.groupby(["game_id", "owner_is_home", "state"]).agg(xg=("xg", "sum")).reset_index()
    p = a.pivot_table(index=["game_id", "owner_is_home"], columns="state", values="xg", fill_value=0).reset_index()
    p = p.rename(columns={"owner_is_home": "is_home"})
    for c in ("5v5", "pp", "pk"):
        if c not in p:
            p[c] = 0.0
    p["is_home"] = p["is_home"].astype(bool)
    own = p.rename(columns={"5v5": "xf5", "pp": "xfpp", "pk": "xfpk"})[["game_id", "is_home", "xf5", "xfpp", "xfpk"]]
    opp = own.assign(is_home=~own["is_home"]).rename(columns={"xf5": "xa5", "xfpp": "xapk_", "xfpk": "xapp_"})
    # opponent's power-play xG is our penalty-kill xG against; opponent's short-handed xG is our power-play xG against
    opp = opp.rename(columns={"xapk_": "xa_on_our_pk", "xapp_": "xa_on_our_pp"})
    sec = state_seconds(ev)
    gg = g.copy()
    gg["game_id"] = gg["game_id"].astype("int64")
    base = pd.concat([gg.assign(is_home=True, team=gg["home"], team_id=gg["home_team_id"], opp=gg["away"]),
                      gg.assign(is_home=False, team=gg["away"], team_id=gg["away_team_id"], opp=gg["home"])])
    base = base[["game_id", "season", "game_type", "start_time_utc", "is_home", "team", "team_id", "opp"]]
    d = base.merge(sec, on=["game_id", "is_home"], how="inner").merge(own, on=["game_id", "is_home"], how="left") \
            .merge(opp, on=["game_id", "is_home"], how="left")
    reg = ev[(ev["type"] == "goal") & (ev["period_type"] == "REG")].groupby(["game_id", "owner_is_home"]).size().rename("reg_goals").reset_index()
    reg = reg.rename(columns={"owner_is_home": "is_home"})
    reg["is_home"] = reg["is_home"].astype(bool)
    d = d.merge(reg, on=["game_id", "is_home"], how="left")
    d["reg_goals"] = d["reg_goals"].fillna(0)
    d["start"] = pd.to_datetime(d["start_time_utc"], utc=True)
    for c in ("xf5", "xfpp", "xfpk", "xa5", "xa_on_our_pk", "xa_on_our_pp"):
        d[c] = d[c].fillna(0)
    return d.sort_values(["start", "game_id", "is_home"]).reset_index(drop=True)


# ---------------------------------------------------------------- the point-in-time, shrunk, decayed rates
def decayed_shrunk_rates(team: np.ndarray, num: np.ndarray, den: np.ndarray, half_life: float, prior_den: float,
                         league_rate: float) -> np.ndarray:
    """For each row, the team's rate over ITS EARLIER rows only: exponentially decayed sums (half-life in games),
    shrunk to ``league_rate`` with ``prior_den`` of prior weight: (sum num + prior*league) / (sum den + prior).
    Rows must be in chronological order. The row's own num/den are folded in only AFTER its rate is read."""
    decay = 0.5 ** (1.0 / half_life)
    sn: dict = {}
    sd: dict = {}
    out = np.empty(len(team))
    for i, t in enumerate(team):
        a, b = sn.get(t, 0.0), sd.get(t, 0.0)
        lg = league_rate[i] if isinstance(league_rate, np.ndarray) else league_rate
        out[i] = (a + prior_den * lg) / (b + prior_den)
        sn[t] = a * decay + num[i]
        sd[t] = b * decay + den[i]
    return out


def league_rate_prior(num: np.ndarray, den: np.ndarray, season: np.ndarray, first_season_rate: float) -> np.ndarray:
    """League rate used as the shrinkage target: the rate over ALL earlier seasons (seasons strictly before the row's),
    or ``first_season_rate`` if none (burn-in, supplied from data of the same earlier period by the caller)."""
    out = np.full(len(num), first_season_rate)
    for s in np.unique(season):
        m = season < s
        if m.any() and den[m].sum() > 0:
            out[season == s] = num[m].sum() / den[m].sum()
    return out


def previous_starter_gsax(g: pd.DataFrame, bx: pd.DataFrame, sx: pd.DataFrame, prior_shots: float = 400.0,
                          half_life: float = 40.0) -> pd.DataFrame:
    """Per (game, team): the goalie who started the team's PREVIOUS game and his decayed, shrunk goals-saved-above-
    expected per shot (only games before this puck drop). See ``GOALIE_STARTER_NOTE``."""
    gl = bx[(bx["group"] == "goalies") & (bx["starter"] == True)][["game_id", "team_id", "player_id", "goals_against", "shots_against"]]  # noqa: E712
    gl = gl.drop_duplicates(["game_id", "team_id"]).copy()
    gl["game_id"] = gl["game_id"].astype("int64")
    faced = sx.assign(team_is_home=~sx["owner_is_home"].astype(bool)).groupby(["game_id", "team_is_home"])["xg"].sum().reset_index()
    gm = g[["game_id", "start_time_utc", "home_team_id", "away_team_id"]].copy()
    gm["game_id"] = gm["game_id"].astype("int64")
    gm["start"] = pd.to_datetime(gm["start_time_utc"], utc=True)
    long = pd.concat([gm.assign(team_id=gm["home_team_id"], team_is_home=True), gm.assign(team_id=gm["away_team_id"], team_is_home=False)])
    long = long.merge(faced, on=["game_id", "team_is_home"], how="left").merge(gl, on=["game_id", "team_id"], how="left")
    long = long.sort_values(["start", "game_id"]).reset_index(drop=True)
    # per-goalie decayed (xG faced - goals against) per shot, read before each of his games
    prev_goalie = long.groupby("team_id")["player_id"].shift(1)
    saved = (long["xg"] - long["goals_against"]).fillna(0.0).to_numpy()
    shots_a = long["shots_against"].fillna(0.0).to_numpy()
    gk = long["player_id"].fillna(-1).to_numpy()
    decay = 0.5 ** (1.0 / half_life)
    sn: dict = {}
    sd: dict = {}
    gsax_prev = np.full(len(long), np.nan)
    for i in range(len(long)):
        pg = prev_goalie.iloc[i]
        if pd.notna(pg):
            a, b = sn.get(pg, 0.0), sd.get(pg, 0.0)
            gsax_prev[i] = a / (b + prior_shots)           # shrunk to 0 (league mean GSAx per shot is 0 by construction)
        # fold this game's goalie in only after the row is read; a goalie's game finished before his next puck drop
        if gk[i] != -1:
            sn[gk[i]] = sn.get(gk[i], 0.0) * decay + saved[i]
            sd[gk[i]] = sd.get(gk[i], 0.0) * decay + shots_a[i]
    long["prev_gsax_per_shot"] = gsax_prev
    return long[["game_id", "team_id", "prev_gsax_per_shot"]]


def game_features(tg: pd.DataFrame, gsax: pd.DataFrame, half_life: float = 40.0, prior_sec: float = 3 * 3600.0,
                  first_rates: Optional[dict] = None) -> pd.DataFrame:
    """One row per game (home view): point-in-time team strengths and the expected-goals ingredients.

    Columns (all read before the game): for each side s in (h, a): ``f5_s`` / ``a5_s`` (5v5 xG for/against per 60),
    ``pp_s`` / ``pk_s`` (PP xG for per 60 of PP time, PK xG against per 60 of PK time), ``ppt_s`` / ``sht_s`` (own PP and
    short-handed seconds per game), ``rest_s`` (days since own previous game, capped), ``gs_s`` (previous starter GSAx/shot),
    and the league rates the shrinkage targeted. The model layer (``expected_goals``) turns them into lam_h, lam_a.
    """
    t = tg.sort_values(["start", "game_id", "is_home"]).reset_index(drop=True)
    team = t["team_id"].to_numpy()
    sec5 = t["s5v5"].to_numpy(float)
    spp = t["spp"].to_numpy(float)
    spk = t["spk"].to_numpy(float)
    season = t["season"].to_numpy()
    fr = first_rates or {}
    lr = {}
    for name, num, den, dflt in (("f5", t["xf5"], sec5, fr.get("f5", 2.2 / 3600)), ("pp", t["xfpp"], spp, fr.get("pp", 6.5 / 3600)),
                                 ("pk", t["xa_on_our_pk"], spk, fr.get("pk", 6.5 / 3600))):
        lr[name] = league_rate_prior(num.to_numpy(float), den, season, dflt)
    out = pd.DataFrame({"game_id": t["game_id"], "is_home": t["is_home"], "team_id": team, "season": season, "start": t["start"]})
    out["f5"] = decayed_shrunk_rates(team, t["xf5"].to_numpy(float), sec5, half_life, prior_sec, lr["f5"]) * 3600
    out["a5"] = decayed_shrunk_rates(team, t["xa5"].to_numpy(float), sec5, half_life, prior_sec, lr["f5"]) * 3600
    out["pp"] = decayed_shrunk_rates(team, t["xfpp"].to_numpy(float), spp, half_life, 1800.0, lr["pp"]) * 3600
    out["pk"] = decayed_shrunk_rates(team, t["xa_on_our_pk"].to_numpy(float), spk, half_life, 1800.0, lr["pk"]) * 3600
    ones = np.ones(len(t))
    out["ppt"] = decayed_shrunk_rates(team, spp, ones, half_life, 8.0, league_rate_prior(spp, ones, season, fr.get("ppt", 300.0)))
    out["sht"] = decayed_shrunk_rates(team, spk, ones, half_life, 8.0, league_rate_prior(spk, ones, season, fr.get("sht", 300.0)))
    out["sec5"] = league_rate_prior(sec5, ones, season, fr.get("sec5", 3000.0))   # earlier seasons only, never the future
    out["lg_f5"] = lr["f5"] * 3600          # the shrinkage target actually used for this row (earlier seasons only)
    out["lg_pp"] = lr["pp"] * 3600
    prev_start = t.groupby("team_id")["start"].shift(1)
    out["rest"] = ((t["start"] - prev_start).dt.total_seconds() / 86400).clip(upper=7).fillna(7.0)
    out = out.merge(gsax.rename(columns={"prev_gsax_per_shot": "gs"}), on=["game_id", "team_id"], how="left")
    out["gs"] = out["gs"].fillna(0.0)
    h = out[out["is_home"]].drop(columns=["is_home"]).add_suffix("_h").rename(columns={"game_id_h": "game_id", "season_h": "season", "start_h": "start"})
    a = out[~out["is_home"]].drop(columns=["is_home", "season", "start"]).add_suffix("_a").rename(columns={"game_id_a": "game_id"})
    return h.merge(a, on="game_id", how="inner").sort_values(["start", "game_id"]).reset_index(drop=True)


def expected_xg(row, side: str) -> float:
    """Multiplicative matchup cross for one side: even-strength + power play + short-handed expected goals, each the
    team's rate times the opponent's rate over the league rate. ``row`` is a ``game_features`` row (or dict)."""
    o = "a" if side == "h" else "h"
    e5 = row["sec5_h"] / 3600.0 * row[f"f5_{side}"] * row[f"a5_{o}"] / max(row["lg_f5_h"], 1e-9)
    # expected PP time for this side: mean of own PP seconds/game and the opponent's short-handed seconds/game
    ppt = 0.5 * (row[f"ppt_{side}"] + row[f"sht_{o}"])
    epp = ppt / 3600.0 * row[f"pp_{side}"] * row[f"pk_{o}"] / max(row["lg_pp_h"], 1e-9)
    return float(e5 + epp)
