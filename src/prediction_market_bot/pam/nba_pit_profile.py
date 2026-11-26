"""NBA point-in-time production profiles from the event store (W130.4 Part A).

Shows HOW a player produces a stat, not only how much: for rebounds the offensive/defensive split, chances on the
floor vs conversion and share of team rebounds; usage and creation; shot zones; defensive events and a rim-deterrence
proxy. Everything is per 100 possessions on the floor (possessions table, ``count_as_possession``).

Point-in-time rule: ``profile_as_of(games, season, as_of)`` uses only games with ``game_date < as_of`` (strictly earlier
calendar day) in that season. The cumulative table is built game by game and read by date, so no later game can enter.

Not derivable from the event store, stated here so nothing downstream pretends otherwise:
* contested vs uncontested rebounds (play-by-play has no contest flag),
* player height / wingspan (opponent-size context uses a *role proxy*: share of opposing on-floor players whose
  trailing rebound+block rate puts them in the big role; see ``opp_big_share``),
* catch-and-shoot, post-up, transition and screen-navigation splits (no tracking data).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

VERSION = "pit-profile-w130.4-v1"
RIM_FT = 4.0  # shot_distance (ft) <= this is a rim attempt

COUNT_COLS = [
    "poss_off", "poss_def", "minutes",
    "oreb", "dreb", "oreb_chances", "dreb_chances",
    "team_oreb_on", "team_dreb_on",
    "fga", "fta", "tov", "ast", "stl", "blk",
    "rim_fga", "mid_fga", "three_fga", "rim_fgm", "three_fgm",
    "opp_rim_fga", "opp_rim_fgm", "opp_fga_on", "opp_big_sum", "opp_big_n",
]


def _melt_on_court(df: pd.DataFrame, prefix: str, keep: list[str]) -> pd.DataFrame:
    cols = [f"{prefix}_player_{i}" for i in range(1, 6)]
    m = df[keep + cols].melt(id_vars=keep, value_vars=cols, value_name="pid").dropna(subset=["pid"])
    m["pid"] = m["pid"].astype("int64")
    return m.drop(columns="variable")


def game_table(pbp: pd.DataFrame, poss: pd.DataFrame, box: pd.DataFrame, sched: pd.DataFrame) -> pd.DataFrame:
    """One row per (game_id, player) of event counts. Pure over the supplied frames (one or more seasons)."""
    out: dict[str, pd.DataFrame] = {}

    def add(name: str, s: pd.Series) -> None:
        out[name] = s

    # --- possessions on the floor
    p = poss[poss["count_as_possession"] == 1]
    po = _melt_on_court(p, "off", ["game_id"]).groupby(["game_id", "pid"]).size().rename("poss_off")
    pdf = _melt_on_court(p, "def", ["game_id"]).groupby(["game_id", "pid"]).size().rename("poss_def")
    base = pd.concat([po, pdf], axis=1).fillna(0)

    # --- rebounds (player rows only; team rebounds carry person_id == team_id)
    reb = pbp[pbp["is_rebound"]].copy()
    reb["is_team"] = reb["person_id"].astype("int64") == reb["team_id"].astype("int64")
    # chances: every rebound event while on floor, split by whether the player's team shot (off) or defended (def)
    ro = _melt_on_court(reb, "off", ["game_id", "order_index"]).groupby(["game_id", "pid"]).size().rename("oreb_chances")
    rd = _melt_on_court(reb, "def", ["game_id", "order_index"]).groupby(["game_id", "pid"]).size().rename("dreb_chances")
    pr = reb[~reb["is_team"]].copy()
    offsets = pr[["off_player_%d" % i for i in range(1, 6)]].to_numpy()
    pr["is_off"] = (offsets == pr["person_id"].to_numpy()[:, None]).any(axis=1)
    oreb = pr[pr["is_off"]].groupby(["game_id", "person_id"]).size().rename("oreb")
    dreb = pr[~pr["is_off"]].groupby(["game_id", "person_id"]).size().rename("dreb")
    oreb.index.names = dreb.index.names = ["game_id", "pid"]
    # team rebounds the player's side won while he was on the floor (share of team rebounds when on floor)
    reb["off_won"] = False
    won_off = pr[pr["is_off"]][["game_id", "order_index"]].assign(w=1)
    reb = reb.merge(won_off, on=["game_id", "order_index"], how="left")
    reb["off_won"] = reb["w"].fillna(0).astype(bool)

    # --- shots from pbp (carry on-court sets): own attempts and opponent attempts while on floor as defender
    sh = pbp[pbp["is_field_goal"] == 1].copy() if "is_field_goal" in pbp else pbp[pbp["is_field_goal"]].copy()
    sh["made"] = sh["is_made_shot"].astype(int)
    sh["zone"] = np.where(sh["shot_value"] == 3, "three", np.where(sh["shot_distance"] <= RIM_FT, "rim", "mid"))
    own = sh.groupby(["game_id", "person_id", "zone"]).agg(a=("made", "size"), m=("made", "sum")).unstack("zone").fillna(0)
    own.columns = [f"{'fga' if a == 'a' else 'fgm'}_{z}" for a, z in own.columns]
    own.index.names = ["game_id", "pid"]
    dsh = _melt_on_court(sh, "def", ["game_id", "zone", "made"])
    dr = dsh[dsh["zone"] == "rim"].groupby(["game_id", "pid"]).agg(opp_rim_fga=("made", "size"), opp_rim_fgm=("made", "sum"))
    da = dsh.groupby(["game_id", "pid"]).size().rename("opp_fga_on")

    # --- box: minutes, fta, tov, ast, stl, blk
    b = box.copy()
    b["pid"] = b["person_id"].astype("int64")
    def mins(x):
        x = str(x)
        if ":" in x:
            m, s = x.split(":")[:2]
            return int(m) + int(s) / 60
        try:
            return float(x)
        except ValueError:
            return 0.0
    b["minutes"] = b["minutes"].map(mins)
    b = b.set_index(["game_id", "pid"])[["team_id", "position", "minutes", "free_throws_attempted", "turnovers",
                                          "assists", "steals", "blocks", "field_goals_attempted"]]
    b = b.rename(columns={"free_throws_attempted": "fta", "turnovers": "tov", "assists": "ast",
                          "steals": "stl", "blocks": "blk"})

    g = b.join([base, ro, rd, oreb, dreb, own, dr, da], how="left")
    for c in COUNT_COLS + ["fga_rim", "fga_mid", "fga_three", "fgm_rim", "fgm_three"]:
        if c in g:
            g[c] = g[c].fillna(0)
    g = g.rename(columns={"fga_rim": "rim_fga", "fga_mid": "mid_fga", "fga_three": "three_fga",
                          "fgm_rim": "rim_fgm", "fgm_three": "three_fgm"})
    for c in COUNT_COLS:
        if c not in g:
            g[c] = 0.0
    g["fga"] = g[["rim_fga", "mid_fga", "three_fga"]].sum(axis=1)
    g = g.reset_index().merge(sched[["game_id", "game_date", "season"]], on="game_id", how="left")
    g["game_date"] = pd.to_datetime(g["game_date"]).dt.normalize()
    return g[g["poss_off"] + g["poss_def"] > 0]


def profile_as_of(games: pd.DataFrame, season: int, as_of, *, min_poss: float = 0.0) -> pd.DataFrame:
    """Per-player profile from games of ``season`` with game_date strictly before ``as_of``. Rates per 100 possessions
    on the floor (offense for usage/zones, defense for stl/blk/rim deterrence, all for rebounds)."""
    as_of = pd.Timestamp(as_of).normalize()
    g = games[(games["season"] == season) & (games["game_date"] < as_of)]
    s = g.groupby("pid")[COUNT_COLS].sum()
    s["gp"] = g.groupby("pid").size()
    s["last_game"] = g.groupby("pid")["game_date"].max()
    s["position"] = g.groupby("pid")["position"].agg(lambda x: next((v for v in x if isinstance(v, str) and v), ""))
    o, d = s["poss_off"].clip(lower=1), s["poss_def"].clip(lower=1)
    a = (s["poss_off"] + s["poss_def"]).clip(lower=1)
    f = pd.DataFrame(index=s.index)
    f["gp"], f["poss"], f["minutes"], f["last_game"], f["position"] = s["gp"], a, s["minutes"], s["last_game"], s["position"]
    f["usage_per100"] = 100 * (s["fga"] + 0.44 * s["fta"] + s["tov"]) / o
    f["ast_per100"] = 100 * s["ast"] / o
    f["tov_per100"] = 100 * s["tov"] / o
    f["fta_rate"] = s["fta"] / s["fga"].clip(lower=1)
    f["rim_share"] = s["rim_fga"] / s["fga"].clip(lower=1)
    f["mid_share"] = s["mid_fga"] / s["fga"].clip(lower=1)
    f["three_share"] = s["three_fga"] / s["fga"].clip(lower=1)
    f["rim_fg"] = s["rim_fgm"] / s["rim_fga"].clip(lower=1)
    f["three_fg"] = s["three_fgm"] / s["three_fga"].clip(lower=1)
    f["oreb_per100"] = 100 * s["oreb"] / o
    f["dreb_per100"] = 100 * s["dreb"] / d
    f["oreb_share"] = s["oreb"] / s["oreb_chances"].clip(lower=1)   # of the team's misses while on floor
    f["dreb_share"] = s["dreb"] / s["dreb_chances"].clip(lower=1)   # of opponent misses while on floor
    f["oreb_mix"] = s["oreb"] / (s["oreb"] + s["dreb"]).clip(lower=1)
    f["stl_per100"] = 100 * s["stl"] / d
    f["blk_per100"] = 100 * s["blk"] / d
    f["opp_rim_rate_on"] = s["opp_rim_fga"] / s["opp_fga_on"].clip(lower=1)   # rim-deterrence proxy: lower is better
    f["opp_rim_fg_on"] = s["opp_rim_fgm"] / s["opp_rim_fga"].clip(lower=1)
    f["opp_rim_per100"] = 100 * s["opp_rim_fga"] / d
    f["n_off_poss"], f["n_def_poss"] = s["poss_off"], s["poss_def"]
    return f[f["poss"] >= min_poss]
