"""W84.3 NHL engine, Part A: three point-in-time factor classes from the event store only.

Shot quality (xG per shot, fit on EARLIER seasons only), goalie workload (previous-game starter only, GG-1010),
special teams. Everything a game's row carries is computed from games that finished before that game's puck drop
(``nhl_point_in_time``); ``assert_pit`` re-checks a sample against the contract.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from prediction_market_bot.c1_signal_ingestion import nhl_point_in_time as pit  # noqa: E402

STORE = ROOT / "exp_output" / "NHL_EVENTS"
SHOT_TYPES = ("wrist", "snap", "slap", "backhand", "tip-in", "deflected", "wrap-around", "bat")
FENWICK = ("shot-on-goal", "goal", "missed-shot")   # unblocked attempts; blocked shots have no valid release point
NET_X = 89.0
WINDOW = 20   # games in the rolling team window


def load(seasons):
    """(games, events, box_players) for regular-season and playoff games with a play-by-play."""
    rd = lambda n: pd.concat([pd.read_parquet(STORE / f"{n}_{s}.parquet") for s in seasons if (STORE / f"{n}_{s}.parquet").exists()],
                             ignore_index=True)
    return rd("games"), rd("events"), rd("box_players")


def shots(ev: pd.DataFrame) -> pd.DataFrame:
    """Unblocked, non-shootout, non-empty-net attempts with geometry and the shooter's strength state."""
    s = ev[ev["type"].isin(FENWICK) & (ev["period_type"] != "SO") & ev["x"].notna() & ev["y"].notna()].copy()
    own_g = np.where(s["owner_is_home"], s["away_goalie"], s["home_goalie"])    # the goalie the shot faces
    s = s[own_g == 1].copy()                                                     # drop empty-net attempts
    ax = s["x"].abs().astype(float)
    s["dist"] = np.hypot(NET_X - ax, s["y"].astype(float))
    s["angle"] = np.degrees(np.arctan2(s["y"].abs().astype(float), np.maximum(NET_X - ax, 0.5)))
    s["own_sk"] = np.where(s["owner_is_home"], s["home_skaters"], s["away_skaters"]).astype(float)
    s["opp_sk"] = np.where(s["owner_is_home"], s["away_skaters"], s["home_skaters"]).astype(float)
    s["state"] = np.select([(s.own_sk == 5) & (s.opp_sk == 5), s.own_sk > s.opp_sk, s.own_sk < s.opp_sk], ["5v5", "pp", "pk"], "even_other")
    s["goal"] = (s["type"] == "goal").astype(int)
    return s


def design(s: pd.DataFrame) -> np.ndarray:
    st = s["shot_type"].fillna("other")
    cols = [np.ones(len(s)), s["dist"], s["dist"] ** 2 / 100, s["angle"], np.log1p(s["dist"]),
            (s["own_sk"] - s["opp_sk"]).clip(-2, 2)] + [(st == t).astype(float) for t in SHOT_TYPES]
    return np.column_stack(cols)


def fit_xg(s: pd.DataFrame):
    from sklearn.linear_model import LogisticRegression
    X = design(s)[:, 1:]
    m = LogisticRegression(C=1.0, max_iter=500).fit(X, s["goal"])
    return m


def xg_by_season(s: pd.DataFrame, first_test: int) -> pd.DataFrame:
    """Out-of-time xG: shots of season t scored by a model fit on seasons < t. The first season has no earlier
    fit, so it is dropped (burn-in); that is the price of point-in-time."""
    out = []
    for t in sorted(s["season"].unique()):
        if t < first_test:
            continue
        m = fit_xg(s[s["season"] < t])
        part = s[s["season"] == t].copy()
        part["xg"] = m.predict_proba(design(part)[:, 1:])[:, 1]
        out.append(part)
    return pd.concat(out, ignore_index=True)


def state_seconds(ev: pd.DataFrame) -> pd.DataFrame:
    """Seconds each team spent in {5v5, pp, pk} per game, attributing each gap between consecutive events (same
    period) to the earlier event's skater counts. Approximate (play stops are inside the gaps) but unbiased across
    teams and games, which is what a rate denominator needs."""
    e = ev[ev["period_type"] != "SO"].sort_values(["game_id", "sort_order"]).copy()
    e["dt"] = (e.groupby(["game_id", "period"])["time_in_period_s"].shift(-1) - e["time_in_period_s"]).clip(0, 120)
    e = e[e["dt"].notna() & e["home_skaters"].notna()]
    out = []
    for side in ("home", "away"):
        own = e[f"{side}_skaters"]; opp = e["away_skaters" if side == "home" else "home_skaters"]
        st = np.select([(own == 5) & (opp == 5), own > opp, own < opp], ["s5v5", "spp", "spk"], "sother")
        out.append(pd.DataFrame({"game_id": e["game_id"], "is_home": side == "home", "st": st, "dt": e["dt"]}))
    t = pd.concat(out).groupby(["game_id", "is_home", "st"])["dt"].sum().unstack(fill_value=0).reset_index()
    return t


def team_games(g: pd.DataFrame, sx: pd.DataFrame, ev: pd.DataFrame) -> pd.DataFrame:
    """One row per (game, team) with that game's xG for/against by state and time in state."""
    a = sx.groupby(["game_id", "owner_is_home", "state"]).agg(xg=("xg", "sum"), n=("xg", "size"), goals=("goal", "sum")).reset_index()
    p = a.pivot_table(index=["game_id", "owner_is_home"], columns="state", values=["xg", "n", "goals"], fill_value=0)
    p.columns = [f"{x}_{y}" for x, y in p.columns]
    p = p.reset_index()
    p.columns = ["is_home" if c == "owner_is_home" else c for c in p.columns]
    sec = state_seconds(ev)
    base = pd.concat([g.assign(is_home=True, team=g["home"], opp=g["away"]), g.assign(is_home=False, team=g["away"], opp=g["home"])])
    base = base[["game_id", "season", "game_type", "start_time_utc", "is_home", "team", "opp"]]
    base["game_id"] = base["game_id"].astype("int64")
    d = base.merge(sec, on=["game_id", "is_home"], how="left")
    own = d.merge(p, on=["game_id", "is_home"], how="left")
    opp = p.assign(is_home=~p["is_home"].astype(bool)).add_prefix("a_")
    opp.columns = [c[2:] if c in ("a_game_id", "a_is_home") else c for c in opp.columns]
    out = own.merge(opp, on=["game_id", "is_home"], how="left")
    for c in out.columns:
        if c.startswith(("xg_", "n_", "goals_", "a_xg_", "a_n_", "a_goals_", "s")) and c not in ("season", "start_time_utc"):
            if out[c].dtype.kind in "fiu":
                out[c] = out[c].fillna(0)
    out["start"] = pd.to_datetime(out["start_time_utc"], utc=True)
    return out.sort_values(["team", "start"]).reset_index(drop=True)


def rolling(tg: pd.DataFrame, window: int = WINDOW) -> pd.DataFrame:
    """Rolling-window sums over each team's PREVIOUS ``window`` games (shift(1): the current game is excluded, and a
    team's previous game always finished before its next puck drop)."""
    f = tg.copy()
    f["xgf5"] = f.get("xg_5v5", 0); f["xga5"] = f.get("a_xg_5v5", 0)
    f["ppxg"] = f.get("xg_pp", 0); f["pkxga"] = f.get("a_xg_pp", 0)   # opponent's PP xG is our PK xG against
    f["pp_s"] = f.get("spp", 0); f["pk_s"] = f.get("spk", 0)
    f["sec5"] = f.get("s5v5", 0)
    cols = ["xgf5", "xga5", "ppxg", "pkxga", "pp_s", "pk_s", "sec5"]
    g = f.groupby("team")
    for c in cols:
        f[f"r_{c}"] = g[c].transform(lambda x: x.shift(1).rolling(window, min_periods=8).sum())
    f["n_prior"] = g.cumcount()
    f["xg_share5"] = f["r_xgf5"] / (f["r_xgf5"] + f["r_xga5"])
    f["xgd5_60"] = (f["r_xgf5"] - f["r_xga5"]) / f["r_sec5"] * 3600
    f["pp_xg60"] = f["r_ppxg"] / f["r_pp_s"] * 3600
    f["pk_xga60"] = f["r_pkxga"] / f["r_pk_s"] * 3600
    f["st_net60"] = f["pp_xg60"] - f["pk_xga60"]
    return f


def goalie_workload(g: pd.DataFrame, bx: pd.DataFrame, sx: pd.DataFrame) -> pd.DataFrame:
    """Per (game, team): the goalie who STARTED THAT TEAM'S PREVIOUS game, his rest days, his starts in the last 7
    days, and his rolling goals-saved-above-expected per game. Nothing about this game's own goalie (GG-1010)."""
    gl = bx[(bx["group"] == "goalies") & (bx["starter"] == True)][["game_id", "team_id", "player_id", "shots_against", "goals_against"]]  # noqa: E712
    gl = gl.drop_duplicates(["game_id", "team_id"])
    st = g[["game_id", "start_time_utc", "home_team_id", "away_team_id"]].copy()
    st["start"] = pd.to_datetime(st["start_time_utc"], utc=True)
    long = pd.concat([st.assign(team_id=st["home_team_id"]), st.assign(team_id=st["away_team_id"])])[["game_id", "team_id", "start"]]
    long["game_id"] = long["game_id"].astype("int64")
    gl["game_id"] = gl["game_id"].astype("int64")
    xga = sx.groupby(["game_id", "owner_is_home"])["xg"].sum().reset_index()
    xga["goalie_side_home"] = ~xga["owner_is_home"].astype(bool)
    hid = g.set_index(g["game_id"].astype("int64"))
    xga["team_id"] = np.where(xga["goalie_side_home"], hid.loc[xga["game_id"], "home_team_id"].values, hid.loc[xga["game_id"], "away_team_id"].values)
    long = long.merge(gl, on=["game_id", "team_id"], how="left").merge(xga[["game_id", "team_id", "xg"]], on=["game_id", "team_id"], how="left")
    long["gsax"] = long["xg"] - long["goals_against"]          # + = saved more than expected
    long = long.sort_values(["team_id", "start"]).reset_index(drop=True)
    long["prev_goalie"] = long.groupby("team_id")["player_id"].shift(1)
    long["prev_start"] = long.groupby("team_id")["start"].shift(1)
    long["days_since_prev"] = (long["start"] - long["prev_start"]).dt.total_seconds() / 86400
    # the previous starter's starts in the 7 days before THIS puck drop (counting his previous game), and his rolling GSAx
    hist = long.dropna(subset=["player_id"])[["team_id", "player_id", "start", "gsax", "shots_against"]]
    by_pl = {k: v.sort_values("start") for k, v in hist.groupby("player_id")}
    s7, gs10, back = [], [], []
    for r in long.itertuples(index=False):
        h = by_pl.get(r.prev_goalie) if pd.notna(r.prev_goalie) else None
        if h is None:
            s7.append(np.nan); gs10.append(np.nan); back.append(np.nan); continue
        prior = h[h["start"] < r.start - pd.Timedelta(hours=4)]
        s7.append(int((prior["start"] >= r.start - pd.Timedelta(days=7)).sum()))
        gs10.append(float(prior["gsax"].tail(10).mean()) if len(prior) >= 3 else np.nan)
        back.append(float((prior["start"].iloc[-2:].diff().dt.total_seconds().iloc[-1] / 86400) if len(prior) >= 2 else np.nan))
    long["prev_goalie_starts7"] = s7; long["prev_goalie_gsax10"] = gs10; long["prev_goalie_b2b"] = back
    long["prev_goalie_b2b"] = (long["prev_goalie_b2b"] < 1.5).astype(float).where(long["prev_goalie_b2b"].notna())
    return long[["game_id", "team_id", "prev_goalie", "days_since_prev", "prev_goalie_starts7", "prev_goalie_gsax10", "prev_goalie_b2b"]]


def assert_pit(g: pd.DataFrame, tg: pd.DataFrame, sample: int = 200, seed: int = 0) -> int:
    """For a sample of games: every game in each team's rolling window finished before this puck drop."""
    pt = pit.PointInTime(pit.start_table(g))
    rng = np.random.default_rng(seed)
    n = 0
    for gid in rng.choice(tg["game_id"].unique(), size=min(sample, tg["game_id"].nunique()), replace=False):
        done = pt.completed_before(int(gid))
        for _, r in tg[tg["game_id"] == gid].iterrows():
            prev = tg[(tg["team"] == r["team"]) & (tg["start"] < r["start"])].tail(WINDOW)
            if not set(int(x) for x in prev["game_id"]) <= done:
                raise pit.LeakError(f"game {gid} window contains a game not finished before puck drop")
        n += 1
    return n
