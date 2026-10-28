"""NBA point-in-time availability (W93.1): the last official injury-report status published before tip, the measured
P(played | status), and lineup features built from *expected* availability instead of who actually played.

W92.3's ``*_act`` lineup variants renormalise the rotation over the players who played - an upper bound, because that is
not known at price time (GG-985). Here each rotation player is weighted by p = P(played | last pre-tip status) and the
weights are renormalised, so the feature uses only what was published before tip.

Pure functions; no I/O, no network. Reports are ``{slot "HH:MM" (ET): {norm_name: status}}`` as cached by
``nba_injury_reports`` (``inj_{date}_{HHMM}.json``); the slot label is the publish time.

When it applies: a team-game with at least one report published at or before ``tip - lead`` on the game's ET date.
When it does not: no report that day (``slot_ts`` is None -> the player gets the ``UNREPORTED`` rate, flagged
``has_report=False``), and players the report cannot be matched to by name."""
from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

ET = ZoneInfo("America/New_York")
STATUSES = ("Out", "Doubtful", "Questionable", "Probable", "Available")
UNREPORTED = "Unreported"  # rotation player the report does not list (NBA lists only players with an issue)
PLAYED_SEC = 60.0  # "played" = at least a minute of floor time (92.3's player_game_table seconds)


class AvailabilityLeakError(AssertionError):
    """A report published after tip would have been used."""


def slot_ts(day, slot: str) -> datetime:
    """UTC instant of a report slot ``"HH:MM"`` (ET wall clock) on ET date ``day``."""
    h, m = (int(x) for x in slot.split(":"))
    return datetime(day.year, day.month, day.day, h, m, tzinfo=ET).astimezone(timezone.utc)


def last_report_before_tip(reports: dict[str, dict[str, str]], day, tip_utc: datetime, lead_min: float = 0.0):
    """Latest slot on ET date ``day`` published at or before ``tip - lead``. Returns (slot_utc, {name: status}) or
    (None, {}). Never returns a report published after the cutoff (asserted)."""
    cutoff = tip_utc.timestamp() - lead_min * 60.0
    best = None
    for slot in reports:
        ts = slot_ts(day, slot)
        if ts.timestamp() <= cutoff and (best is None or ts > best[0]):
            best = (ts, slot)
    if best is None:
        return None, {}
    if best[0].timestamp() > cutoff:
        raise AvailabilityLeakError(f"slot {best[1]} after cutoff")
    return best[0], reports[best[1]]


def status_table(rot: pd.DataFrame, names: pd.DataFrame, gm: pd.DataFrame, inj: dict, lead_min: float = 0.0) -> pd.DataFrame:
    """Per (game, team, person): last pre-tip status. ``rot``: rotation_weights (game_id, team_id, person_id, w).
    ``names``: person_id -> norm_name. ``gm``: game_meta indexed by game_id with ``tip_earliest`` (UTC) and ``day``
    (ET date). ``inj``: {ET date: reports}. Output adds status (UNREPORTED if not listed), slot_utc, has_report."""
    j = rot.merge(names, on="person_id", how="left").join(gm[["tip_earliest", "day"]], on="game_id")
    status, slot_out = [], []
    cache: dict = {}
    for gid, nm, tip, day in zip(j["game_id"], j["norm_name"], j["tip_earliest"], j["day"]):
        if gid not in cache:
            cache[gid] = last_report_before_tip(inj.get(day, {}), day, tip.to_pydatetime(), lead_min)
        ts, rep = cache[gid]
        status.append(rep.get(nm, UNREPORTED) if ts is not None else UNREPORTED)
        slot_out.append(ts)
    j["status"] = status
    j["slot_utc"] = slot_out
    j["has_report"] = j["slot_utc"].notna()
    j["leak"] = [pd.notna(ts) and ts.timestamp() > t.timestamp() for ts, t in zip(j["slot_utc"], j["tip_earliest"])]
    if j["leak"].any():
        raise AvailabilityLeakError(f"{int(j['leak'].sum())} rows use a post-tip report")
    return j.drop(columns=["leak"])


def play_rates(obs: pd.DataFrame, by: str | None = None) -> pd.DataFrame:
    """P(played | status): ``obs`` has ``status`` and ``played`` (0/1), optional grouping column ``by`` (e.g. season).
    Returns n, k, rate, Wilson 95% interval."""
    keys = ["status"] if by is None else [by, "status"]
    g = obs.groupby(keys)["played"].agg(n="size", k="sum").reset_index()
    z = 1.96
    p = g["k"] / g["n"]
    den = 1 + z * z / g["n"]
    c = (p + z * z / (2 * g["n"])) / den
    h = z * np.sqrt(p * (1 - p) / g["n"] + z * z / (4 * g["n"] ** 2)) / den
    g["rate"], g["lo"], g["hi"] = p, c - h, c + h
    return g


def rate_map(rates: pd.DataFrame, min_n: int = 20, fallback: dict | None = None) -> dict[str, float]:
    """status -> rate; statuses with fewer than ``min_n`` observations fall back to ``fallback`` (or the pooled mean)."""
    fb = fallback or {}
    out = {}
    for s, n, k in zip(rates["status"], rates["n"], rates["k"]):
        out[s] = float(k / n) if n >= min_n else fb.get(s, float(rates["k"].sum() / rates["n"].sum()))
    return out


def expected_lineup_features(st: pd.DataFrame, ratings: pd.DataFrame, rates: dict[str, float]) -> pd.DataFrame:
    """Per (game, team): lineup_*_exp = sum of w*p*rel / sum of w*p, p = rates[status] (pre-tip knowledge only), plus
    ``exp_missing`` = sum of w*(1-p) (expected share of rotation minutes absent) and ``cover`` = share of rotation
    minutes held by players the report lists (how much of the rotation the report speaks to)."""
    r = ratings[["game_id", "person_id", "rel_net", "rel_ptot", "rel_pace"]]
    j = st.merge(r, on=["game_id", "person_id"], how="left")
    for c in ("rel_net", "rel_ptot", "rel_pace"):
        j[c] = j[c].fillna(0.0)
    j["p"] = j["status"].map(rates).fillna(rates.get(UNREPORTED, 1.0))
    j["wp"] = j["w"] * j["p"]
    key = [j["game_id"], j["team_id"]]
    z = j["wp"].groupby(key).sum()
    out = pd.DataFrame(index=z.index)
    for c, name in (("rel_net", "lineup_net_exp"), ("rel_ptot", "lineup_ptot_exp"), ("rel_pace", "lineup_pace_exp")):
        out[name] = (j["wp"] * j[c]).groupby(key).sum() / z.where(z > 0)
    out["exp_missing"] = (j["w"] * (1 - j["p"])).groupby(key).sum()
    out["cover"] = (j["w"] * (j["status"] != UNREPORTED)).groupby(key).sum()
    return out.reset_index()
