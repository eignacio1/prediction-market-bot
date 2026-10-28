"""NBA factor B7 - lineups and on/off, built point-in-time from the play-by-play (W92.3, ADR-0073/0075).

Pipeline: play-by-play + the per-event five-on-floor table -> stints (the ten players on the floor, seconds, possessions,
points each way) -> player-game on-court totals -> player ratings as of each game -> team lineup features.

Rating channels, per 100 possessions on the floor (or per 48 minutes for pace), each measured RELATIVE to the player's own
team over the same games, so the number is the player's lift over his team's mean, i.e. shrinkage to the team mean is a
shrinkage to 0:
  net  = (points for - points against) / possessions * 100        (on/off swing x (1 - on-court share))
  ptot = (points for + points against) / possessions * 100        (what the player does to the total)
  pace = possessions / seconds * 2880
Shrinkage prior (fixed before any result): rel_shrunk = rel * P / (P + K), P = possessions on the floor, K = 1000 (about
15 full games of a rotation player). Prior seasons carry with weight DECAY ** (season gap), DECAY = 0.5, so a new
teammate or a new season starts from what the player did before rather than from zero.

As-of rule: a game G' feeds a rating used for G iff ``tip_latest(G') + COMPLETION_BUFFER <= tip_earliest(G)`` - the same
predicate as ``PointInTime.completed_before`` (nba_factors.rolling_asof evaluates it with a sorted prefix; so does this).

Applies: pre-game team-level features for a regular-season / playoff game with prior games in the store. Does not apply:
a rookie with no prior floor time (rating 0 by construction), a season's first games (no team rotation yet), or any use that
needs the lineup of the game being predicted - that is the 'act' variant, which conditions on who played and is only legal
once the active list is public (~90 min before tip), flagged as availability-known, not point-in-time from the archive.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .nba_data_rules import attach_order_index
from .nba_point_in_time import COMPLETION_BUFFER

K_SHRINK = 1000.0
DECAY = 0.5
ROT_GAMES = 10
CHANNELS = ("net", "ptot", "pace")
SIDES = ("home", "away")


# --------------------------------------------------------------------------------------------- stints
def game_seconds(period: pd.Series, seconds_remaining: pd.Series) -> pd.Series:
    """Elapsed game seconds: 720-second quarters, 300-second overtimes."""
    p = period.astype(float)
    reg = 720.0 * (p - 1) + (720.0 - seconds_remaining)
    ot = 2880.0 + 300.0 * (p - 5) + (300.0 - seconds_remaining)
    return pd.Series(np.where(p <= 4, reg, ot), index=period.index)


def build_stints(pbp: pd.DataFrame, lineups: pd.DataFrame, schedule: pd.DataFrame) -> pd.DataFrame:
    """One row per stint: game_id, home1..5, away1..5 (sorted), sec, poss_h, poss_a, pts_h, pts_a.

    Possessions per side = FGA + 0.44 FTA - ORB + TOV on that side's events within the stint. A stint is a maximal run of
    events with the same ten players in the same period. The lineup table lags a substitution by up to two events at the
    same clock reading, so the seconds mis-attributed are measured against box-score minutes (``validate_minutes``).
    """
    lu = attach_order_index(lineups, pbp)
    cols = ["game_id", "order_index", "period", "seconds_remaining", "team_id", "event_type", "is_field_goal",
            "is_free_throw", "is_rebound", "is_turnover", "shot_result", "score_home", "score_away"]
    ev = pbp[cols].merge(lu.drop(columns=[c for c in ("action_number", "period", "season", "_source", "_as_of") if c in lu]),
                         on=["game_id", "order_index"], how="inner", validate="one_to_one")
    ev["game_id"] = ev["game_id"].astype(str)
    ev = ev.sort_values(["game_id", "order_index"]).reset_index(drop=True)
    sched = schedule.drop_duplicates("game_id", keep="last").set_index(schedule.drop_duplicates("game_id", keep="last")["game_id"].astype(str))
    ev["home_tid"] = ev["game_id"].map(sched["home_team_id"]).astype(float)
    ev["t"] = game_seconds(ev["period"], ev["seconds_remaining"].astype(float))
    g = ev["game_id"]
    nxt = ev.groupby("game_id")["t"].shift(-1)
    ev["dur"] = (nxt - ev["t"]).clip(lower=0).fillna(0.0)
    # scoring: score columns are sparse (blank off scoring events); forward-fill inside the game
    sh = pd.to_numeric(ev["score_home"], errors="coerce")
    sa = pd.to_numeric(ev["score_away"], errors="coerce")
    sh = sh.groupby(g).ffill().fillna(0.0)
    sa = sa.groupby(g).ffill().fillna(0.0)
    ev["pts_h"] = sh.groupby(g).diff().fillna(sh).clip(lower=0)
    ev["pts_a"] = sa.groupby(g).diff().fillna(sa).clip(lower=0)
    # possessions
    is_h = (ev["team_id"].astype(float) == ev["home_tid"]).to_numpy()
    ft = ev["is_free_throw"].astype(float).to_numpy() > 0
    fg = ev["is_field_goal"].astype(float).to_numpy() > 0
    tov = ev["is_turnover"].astype(float).to_numpy() > 0
    miss = (fg & (ev["shot_result"] == "Missed").to_numpy()) | (ft & (ev["shot_result"] == "Missed").to_numpy())
    last_miss_team = pd.Series(np.where(miss, ev["team_id"].astype(float), np.nan)).groupby(g).ffill()
    orb = (ev["is_rebound"].astype(float).to_numpy() > 0) & (ev["team_id"].astype(float).to_numpy() == last_miss_team.to_numpy())
    val = fg * 1.0 + 0.44 * ft - orb * 1.0 + tov * 1.0
    ev["poss_h"] = np.where(is_h, val, 0.0)
    ev["poss_a"] = np.where(~is_h & (ev["team_id"].astype(float) > 0), val, 0.0)
    # stint ids
    hcols, acols = [f"home_player_{i}" for i in range(1, 6)], [f"away_player_{i}" for i in range(1, 6)]
    H = np.sort(ev[hcols].to_numpy(dtype=np.int64), axis=1)
    A = np.sort(ev[acols].to_numpy(dtype=np.int64), axis=1)
    key = np.concatenate([H, A], axis=1)
    chg = np.ones(len(ev), dtype=bool)
    chg[1:] = (key[1:] != key[:-1]).any(axis=1) | (ev["game_id"].to_numpy()[1:] != ev["game_id"].to_numpy()[:-1]) \
        | (ev["period"].to_numpy()[1:] != ev["period"].to_numpy()[:-1])
    sid = np.cumsum(chg) - 1
    agg = pd.DataFrame({"sid": sid, "sec": ev["dur"], "poss_h": ev["poss_h"], "poss_a": ev["poss_a"],
                        "pts_h": ev["pts_h"], "pts_a": ev["pts_a"]}).groupby("sid").sum()
    first = np.flatnonzero(chg)
    out = pd.DataFrame(H[first], columns=[f"home{i}" for i in range(1, 6)])
    for i in range(5):
        out[f"away{i + 1}"] = A[first, i]
    out["game_id"] = ev["game_id"].to_numpy()[first]
    out["period"] = ev["period"].to_numpy()[first]
    for c in ("sec", "poss_h", "poss_a", "pts_h", "pts_a"):
        out[c] = agg[c].to_numpy()
    return out


def clean_games(stints: pd.DataFrame, expected_len: pd.Series | None = None, tol: float = 0.02) -> tuple[set, dict]:
    """Games whose stints can be trusted: ten distinct non-null players in every stint with time, total seconds within
    ``tol`` of the expected length (``expected_len``: game_id -> seconds; else 2880 with overtimes 300 s each and a
    2880 floor). Returns (kept ids, counts of what was dropped and why)."""
    s = stints
    h = s[[f"home{i}" for i in range(1, 6)]].to_numpy()
    a = s[[f"away{i}" for i in range(1, 6)]].to_numpy()
    bad_row = (h <= 0).any(1) | (a <= 0).any(1) | (np.sort(h, 1)[:, 1:] == np.sort(h, 1)[:, :-1]).any(1) \
        | (np.sort(a, 1)[:, 1:] == np.sort(a, 1)[:, :-1]).any(1)
    bad_players = set(s["game_id"][bad_row])
    tot = s.groupby("game_id")["sec"].sum()
    if expected_len is None:
        nper = s.groupby("game_id")["period"].max()
        expected = 2880.0 + 300.0 * (nper - 4).clip(lower=0)
    else:
        expected = expected_len.reindex(tot.index)
    off = ((tot - expected).abs() / expected > tol) | expected.isna()
    bad_len = set(tot.index[off])
    ids = set(tot.index)
    kept = ids - bad_players - bad_len
    return kept, {"games": len(ids), "bad_player_rows": len(bad_players), "bad_length": len(bad_len), "kept": len(kept)}


def player_game_table(stints: pd.DataFrame) -> pd.DataFrame:
    """Per (game, player): sec, poss, pf, pa while on the floor (own-team perspective), plus the team's id side."""
    frames = []
    for side, mine, theirs in (("home", "pts_h", "pts_a"), ("away", "pts_a", "pts_h")):
        pcols = [f"{side}{i}" for i in range(1, 6)]
        base = stints[["game_id", "sec", "poss_h", "poss_a", mine, theirs]].copy()
        base["poss"] = (base["poss_h"] + base["poss_a"]) / 2.0
        base = base.rename(columns={mine: "pf", theirs: "pa"})[["game_id", "sec", "poss", "pf", "pa"]]
        for c in pcols:
            f = base.copy()
            f["person_id"] = stints[c].to_numpy()
            f["side"] = side
            frames.append(f)
    long = pd.concat(frames, ignore_index=True)
    return long.groupby(["game_id", "person_id", "side"], as_index=False)[["sec", "poss", "pf", "pa"]].sum()


def team_game_totals(stints: pd.DataFrame) -> pd.DataFrame:
    """Per (game, side): sec, poss, pf, pa from the same stints (the team's own totals, for the 'team over the same games')."""
    rows = []
    for side, mine, theirs in (("home", "pts_h", "pts_a"), ("away", "pts_a", "pts_h")):
        t = stints.groupby("game_id").agg(sec=("sec", "sum"), ph=("poss_h", "sum"), pa_=("poss_a", "sum"),
                                          pf=(mine, "sum"), pa=(theirs, "sum"))
        t["poss"] = (t["ph"] + t["pa_"]) / 2.0
        t["side"] = side
        rows.append(t.reset_index()[["game_id", "side", "sec", "poss", "pf", "pa"]])
    return pd.concat(rows, ignore_index=True)


def validate_minutes(pg: pd.DataFrame, player_box: pd.DataFrame, tol_min: float = 1.0) -> dict:
    """Stint-derived player minutes against box-score minutes: match rate within ``tol_min`` and median abs error."""
    b = player_box[["game_id", "person_id", "minutes"]].copy()
    b["game_id"] = b["game_id"].astype(str)
    m = b["minutes"].astype(str).str.split(":", expand=True)
    mm = pd.to_numeric(m[0], errors="coerce")
    ss = pd.to_numeric(m[1], errors="coerce") if m.shape[1] > 1 else 0
    b["box_min"] = mm + ss / 60.0
    j = pg.assign(stint_min=pg["sec"] / 60.0).merge(b[["game_id", "person_id", "box_min"]], on=["game_id", "person_id"], how="inner")
    j = j.dropna(subset=["box_min"])
    j = j[j["box_min"] > 0]
    err = (j["stint_min"] - j["box_min"]).abs()
    return {"player_games": int(len(j)), "match_within_tol": float((err <= tol_min).mean()), "median_abs_err_min": float(err.median()),
            "p95_abs_err_min": float(err.quantile(0.95)), "tol_min": tol_min}


# ------------------------------------------------------------------------------------- as-of ratings
def _ratio(num: np.ndarray, den: np.ndarray, scale: float) -> np.ndarray:
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, scale * num / den, np.nan)


def player_asof_ratings(pg: pd.DataFrame, tg: pd.DataFrame, game_meta: pd.DataFrame, k: float = K_SHRINK,
                        decay: float = DECAY) -> pd.DataFrame:
    """Player rating as of every game the player appears in, from games completed before it.

    pg: player_game_table + ``team_id``. tg: team_game_totals keyed (game_id, side). game_meta: index game_id, columns
    season, tip_earliest, tip_latest. Returns one row per (game_id, person_id): P (decayed possessions on floor) and
    rel_<ch> shrunk for ch in CHANNELS, plus swing_net (on minus off, shrunk).
    """
    d = pg.merge(tg.rename(columns={"sec": "t_sec", "poss": "t_poss", "pf": "t_pf", "pa": "t_pa"}), on=["game_id", "side"])
    d = d.join(game_meta[["season", "tip_earliest", "tip_latest"]], on="game_id")
    d = d.dropna(subset=["tip_latest"]).sort_values(["person_id", "tip_latest"]).reset_index(drop=True)
    # per-row additive pieces (on-floor and team over the same game)
    cols = {"sec": d["sec"].to_numpy(float), "poss": d["poss"].to_numpy(float), "pf": d["pf"].to_numpy(float),
            "pa": d["pa"].to_numpy(float), "t_sec": d["t_sec"].to_numpy(float), "t_poss": d["t_poss"].to_numpy(float),
            "t_pf": d["t_pf"].to_numpy(float), "t_pa": d["t_pa"].to_numpy(float)}
    # a player's own team in the games where he was on the floor: time-weighted team totals over his games (all minutes of
    # the team in the games he played), so rel = on-floor rate minus team rate over those games.
    names = list(cols)
    M = np.column_stack([cols[n] for n in names])
    out = np.full((len(d), 5), np.nan)  # P, rel_net, rel_ptot, rel_pace, swing_net
    comp = (d["tip_latest"] + COMPLETION_BUFFER).to_numpy(dtype="datetime64[ns]")
    cut = d["tip_earliest"].to_numpy(dtype="datetime64[ns]")
    seas = d["season"].to_numpy(int)
    pid = d["person_id"].to_numpy()
    starts = np.flatnonzero(np.r_[True, pid[1:] != pid[:-1]])
    ends = np.r_[starts[1:], len(d)]
    for a, b in zip(starts, ends):
        c, sv, Mp, ct = comp[a:b], seas[a:b], M[a:b], cut[a:b]
        kk = np.searchsorted(c, ct, side="right")  # prior completed games form a prefix (comp sorted by tip_latest)
        cs = np.vstack([np.zeros(Mp.shape[1]), np.cumsum(Mp, axis=0)])
        for s in np.unique(sv):
            idx = np.flatnonzero(sv == s)
            # decayed contribution of every earlier-season game that is complete (all of them, by tip order)
            gap_w = np.where(sv[None, :] < s, decay ** (s - sv[None, :]), 0.0)[0]
            prior_all = (gap_w[:, None] * Mp).sum(axis=0) if (gap_w > 0).any() else np.zeros(Mp.shape[1])
            same = (sv == s)
            same_cs = np.vstack([np.zeros(Mp.shape[1]), np.cumsum(np.where(same[:, None], Mp, 0.0), axis=0)])
            for i in idx:
                n = kk[i]
                acc = same_cs[n] + prior_all
                P, sec, pf, pa = acc[1], acc[0], acc[2], acc[3]
                tsec, tposs, tpf, tpa = acc[4], acc[5], acc[6], acc[7]
                if P <= 0:
                    out[a + i] = [0.0, 0.0, 0.0, 0.0, 0.0]
                    continue
                shr = P / (P + k)
                net_on = 100 * (pf - pa) / P
                ptot_on = 100 * (pf + pa) / P
                pace_on = 2880 * P / sec if sec > 0 else np.nan
                net_t, ptot_t = (100 * (tpf - tpa) / tposs, 100 * (tpf + tpa) / tposs) if tposs > 0 else (np.nan, np.nan)
                pace_t = 2880 * tposs / tsec if tsec > 0 else np.nan
                # off-floor: team minus the player's on-floor totals over the same games
                off_poss, off_pf, off_pa = tposs - P, tpf - pf, tpa - pa
                swing = (net_on - 100 * (off_pf - off_pa) / off_poss) if off_poss > 0 else np.nan
                out[a + i] = [P, shr * np.nan_to_num(net_on - net_t), shr * np.nan_to_num(ptot_on - ptot_t),
                              shr * np.nan_to_num(pace_on - pace_t), shr * np.nan_to_num(swing)]
    res = d[["game_id", "person_id", "side"]].copy()
    for j, n in enumerate(["P", "rel_net", "rel_ptot", "rel_pace", "swing_net"]):
        res[n] = out[:, j]
    return res


# --------------------------------------------------------------------------------- team features
def rotation_weights(pg: pd.DataFrame, team_of: pd.DataFrame, game_meta: pd.DataFrame, n_games: int = ROT_GAMES) -> pd.DataFrame:
    """Expected-minutes weights for each (game, team): the team's players weighted by mean floor time over the team's last
    ``n_games`` completed same-season games (a game he did not play counts as 0). Rows: game_id, team_id, person_id, w
    (sums to 1 per game-team). Point-in-time: only games completed before G's earliest tip."""
    d = pg.merge(team_of, on=["game_id", "side"]).join(game_meta[["season", "tip_earliest", "tip_latest"]], on="game_id")
    teams = d[["game_id", "team_id", "season", "tip_earliest", "tip_latest"]].drop_duplicates(["game_id", "team_id"])
    teams = teams.sort_values(["team_id", "tip_latest"]).reset_index(drop=True)
    out = []
    for (tid, s), grp in teams.groupby(["team_id", "season"], sort=False):
        comp = (grp["tip_latest"] + COMPLETION_BUFFER).to_numpy(dtype="datetime64[ns]")
        cut = grp["tip_earliest"].to_numpy(dtype="datetime64[ns]")
        gids = grp["game_id"].to_numpy()
        sec_by_game = d[(d["team_id"] == tid) & (d["season"] == s)].groupby("game_id")
        tab = {g: dict(zip(x["person_id"], x["sec"])) for g, x in sec_by_game}
        kk = np.searchsorted(comp, cut, side="right")
        for i, g in enumerate(gids):
            prior = gids[max(kk[i] - n_games, 0):kk[i]]
            if len(prior) == 0:
                continue
            tot: dict = {}
            for pgid in prior:
                for p, sec in tab.get(pgid, {}).items():
                    tot[p] = tot.get(p, 0.0) + sec
            z = sum(tot.values())
            if z <= 0:
                continue
            for p, sec in tot.items():
                out.append((g, tid, p, sec / z))
    return pd.DataFrame(out, columns=["game_id", "team_id", "person_id", "w"])


def team_lineup_features(rot: pd.DataFrame, ratings: pd.DataFrame, active: pd.DataFrame | None = None) -> pd.DataFrame:
    """Per (game, team): lineup_<ch> = sum over the expected rotation of w * rel_<ch> (and the on/off swing).

    ``rot``: rotation_weights. ``ratings``: player_asof_ratings (as of each game). ``active``: optional (game_id,
    person_id) of players who played in G; if given, adds the *_act variants (weights renormalised to the players who
    played) - availability-known, not archive point-in-time (see module docstring)."""
    r = ratings[["game_id", "person_id", "rel_net", "rel_ptot", "rel_pace", "swing_net"]]
    j = rot.merge(r, on=["game_id", "person_id"], how="left")
    for c in ("rel_net", "rel_ptot", "rel_pace", "swing_net"):
        j[c] = j[c].fillna(0.0)  # no prior floor time -> no rating (0 = the team's mean)
    feats = {}
    for c, name in (("rel_net", "lineup_net"), ("rel_ptot", "lineup_ptot"), ("rel_pace", "lineup_pace"), ("swing_net", "lineup_swing")):
        feats[name] = (j["w"] * j[c]).groupby([j["game_id"], j["team_id"]]).sum()
    out = pd.DataFrame(feats)
    out["rot_n"] = j.groupby(["game_id", "team_id"])["w"].size()
    if active is not None:
        a = active[["game_id", "person_id"]].drop_duplicates().assign(_a=1)
        k = j.merge(a, on=["game_id", "person_id"], how="left")
        k = k[k["_a"] == 1]
        z = k.groupby(["game_id", "team_id"])["w"].transform("sum")
        k = k.assign(w2=k["w"] / z.where(z > 0))
        for c, name in (("rel_net", "lineup_net_act"), ("rel_ptot", "lineup_ptot_act"), ("rel_pace", "lineup_pace_act")):
            out[name] = (k["w2"] * k[c]).groupby([k["game_id"], k["team_id"]]).sum().reindex(out.index)
    return out.reset_index()
