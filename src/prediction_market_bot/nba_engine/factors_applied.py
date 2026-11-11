"""NBA factors interpreted -> applied, through the 109.1 decision tree (W110.2 / B-068, ADR-0075).

Four factor groups, each a tested path from a fact to a price (the 109.1 tree + engine_v3 shifts, fit on training games only):
  geometry   B12 travel / density / altitude / late-body          class "venue"      known from the schedule (always)
  officials  B13 crew pace / FTA / fouls tendency (shrunk, prior)  class "officials"  crew posts ~9h before tip (UNVERIFIED, GG-1390)
  usage      B10/B11 expected missing usage + creator-out cross    class "lineup"     lands with the injury report, ~1.5h
  pam        PAM archetype / modifier availability flags          class "qualitative" known when the record is (see pam_flags)

``register()`` adds the names to ``decision_tree.FACTOR_CLASS`` and ``engine_v3.FACTORS``; ``price`` is the 109.1 ``price`` with one
addition the tree's BANDS table does not carry: the "officials" class is permitted at T2 and T3 (the crew is known by then),
nowhere deeper because it is not yet knowable at T1 (>= 12h). decision_tree.py itself is not edited.

Applies when: pricing an NBA pre-game market whose factor values were computed point-in-time. Does not apply when the value uses
information after the decision time (the tree refuses it: ``skipped``).
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Mapping, Optional, Tuple

import numpy as np
import pandas as pd

from prediction_market_bot.nba_engine import decision_tree as D
from prediction_market_bot.nba_engine import engine_v2 as V
from prediction_market_bot.nba_engine import engine_v3 as V3

# name -> (target, class, hours-to-tip at/below which knowable, granularity-index id, description)
GROUPS: Dict[str, Tuple[str, ...]] = {
    "geometry": ("d_miles", "d_g_last4", "d_road_run", "alt_gain_a", "d_late_body", "venue_alt", "s_late_body", "s_g_last4"),
    "officials": ("s_crew_pace", "s_crew_fta", "s_crew_fouls"),
    "usage": ("d_usage_missing", "s_usage_missing", "d_creator_out", "s_creator_out"),
    "pam": ("d_pam_creator", "s_pam_creator", "d_pam_mod", "s_pam_mod"),
}
OFFICIALS_HOURS = 9.0  # NBA posts crew assignments ~9h before tip; archive carries no timestamp (GG-1390) -> upper bound
SPEC: Dict[str, Tuple[str, str, float, str]] = {
    "d_miles": ("margin", "venue", D.ALWAYS, "home - away miles travelled for this game (thousands)"),
    "d_g_last4": ("margin", "venue", D.ALWAYS, "home - away games in the last 4 days"),
    "d_road_run": ("margin", "venue", D.ALWAYS, "home - away consecutive road games before tip"),
    "alt_gain_a": ("margin", "venue", D.ALWAYS, "away team altitude gain vs its previous venue (km)"),
    "d_late_body": ("margin", "venue", D.ALWAYS, "home - away body-clock lateness (tz shift x late tip)"),
    "venue_alt": ("total", "venue", D.ALWAYS, "venue altitude (km)"),
    "s_late_body": ("total", "venue", D.ALWAYS, "home + away body-clock lateness"),
    "s_g_last4": ("total", "venue", D.ALWAYS, "home + away games in the last 4 days"),
    "s_crew_pace": ("total", "officials", OFFICIALS_HOURS, "crew shrunk pace deviation vs league, prior games only"),
    "s_crew_fta": ("total", "officials", OFFICIALS_HOURS, "crew shrunk free-throw-attempt deviation, prior games only"),
    "s_crew_fouls": ("total", "officials", OFFICIALS_HOURS, "crew shrunk personal-foul deviation, prior games only"),
    "d_usage_missing": ("margin", "lineup", 1.5, "home - away expected missing usage share (rotation x status)"),
    "s_usage_missing": ("total", "lineup", 1.5, "home + away expected missing usage share"),
    "d_creator_out": ("margin", "lineup", 1.5, "home - away top-usage player's missing probability x his usage share"),
    "s_creator_out": ("total", "lineup", 1.5, "home + away top-usage player's missing probability x his usage share"),
    "d_pam_creator": ("margin", "qualitative", D.ALWAYS, "home - away availability-weighted PRF-1/PRF-2 creator weight in rotation"),
    "s_pam_creator": ("total", "qualitative", D.ALWAYS, "home + away availability-weighted PRF-1/PRF-2 creator weight"),
    "d_pam_mod": ("margin", "qualitative", D.ALWAYS, "home - away availability-weighted PAM modifier count in rotation"),
    "s_pam_mod": ("total", "qualitative", D.ALWAYS, "home + away availability-weighted PAM modifier count"),
}
# classes the 109.1 BANDS table does not carry, by band (decision_tree.py is not edited)
EXTRA_CLASSES: Dict[str, Tuple[str, ...]] = {"T1": (), "T2": ("officials",), "T3": ("officials",)}


def register() -> None:
    """Idempotent: make the tree and engine_v3 aware of the new factor names."""
    for f, (target, cls, hrs, _) in SPEC.items():
        D.FACTOR_CLASS[f] = (cls, hrs)
        V3.FACTORS[f] = (target, f, SPEC[f][3])


def usable(x: Mapping[str, float], hours_to_tip: float) -> Tuple[Dict[str, float], Dict[str, str]]:
    """109.1 ``usable_factors`` plus the extra classes; same rule: permitted class AND already knowable."""
    band = D.band_for(hours_to_tip)
    ok = set(D.permitted_classes(band)) | set(EXTRA_CLASSES.get(band, ()))
    use, skip = {}, {}
    for f, v in x.items():
        cls, avail = D.FACTOR_CLASS.get(f, ("unknown", float("inf")))
        if cls not in ok:
            skip[f] = f"class {cls} not permitted at {band}"
        elif hours_to_tip > avail:
            skip[f] = f"not knowable until {avail}h before tip"
        else:
            use[f] = v
    return use, skip


def price(p: V.V2Params, family: str, mu_h: float, mu_a: float, x: Mapping[str, float], hours_to_tip: float, n: int = 1,
          calibrate: bool = True) -> D.TreeResult:
    """109.1 ``price`` with this module's ``usable``."""
    band = D.band_for(hours_to_tip)
    if band == "T4":
        raise ValueError("in play: use decision_tree.price_inplay")
    use, skip = usable(x, hours_to_tip)
    m, t = V.game_means(p, mu_h, mu_a, use)
    raw = V.raw_prob(p, family, m, t, n)
    q = V.calibrated(p, family, raw) if calibrate else raw
    cls = set(D.permitted_classes(band)) | set(EXTRA_CLASSES.get(band, ()))
    path = [f"band={band}", f"classes={','.join(sorted(cls))}", f"factors={','.join(sorted(use)) or 'none'}", f"family={family}"]
    return D.TreeResult(q, raw, band, m, t, sorted(use), skip, path)


# ---------------------------------------------------------------- pure builders (point-in-time; unit-tested on known answers)
def usage_events(fga, fta, tov):
    """Possession-ending usage events of one player-game: FGA + 0.44 FTA + TOV."""
    return np.asarray(fga, float) + 0.44 * np.asarray(fta, float) + np.asarray(tov, float)


def usage_shares_asof(rows: pd.DataFrame, window: int = 10) -> pd.DataFrame:
    """Each player's share of his team's usage events over the team's previous ``window`` games (strictly earlier; same season).

    ``rows``: game_id, team_id, person_id, season, order (sortable game order within a team-season; unique per team game), ue.
    Returns rows with ``share`` (NaN when the team has no earlier game). A player absent from a game counts 0 for it."""
    out = []
    for (tid, s), grp in rows.groupby(["team_id", "season"], sort=False):
        piv = grp.pivot_table(index="order", columns="person_id", values="ue", aggfunc="sum").sort_index().fillna(0.0)
        prior = piv.shift(1).rolling(window, min_periods=1).sum()
        tot = prior.sum(axis=1)
        share = prior.div(tot.where(tot > 0), axis=0)
        gid = grp.drop_duplicates("order").set_index("order")["game_id"]
        sh = share.stack(future_stack=True) if hasattr(share, "stack") else share
        sh = sh.rename("share").reset_index()
        sh.columns = ["order", "person_id", "share"]
        sh["game_id"] = sh["order"].map(gid)
        sh["team_id"] = tid
        out.append(sh[["game_id", "team_id", "person_id", "share"]])
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame(columns=["game_id", "team_id", "person_id", "share"])


def usage_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Per (game, team): ``usage_missing`` = sum share*(1-p_play); ``creator_out`` = (1-p_play) of the top-share player x share.

    ``df``: game_id, team_id, share, p_play (probability the listed status plays). The B11 cross: a creator absence moves more
    than the same share spread over several absorbers."""
    d = df.dropna(subset=["share", "p_play"]).copy()
    d["miss"] = d["share"] * (1.0 - d["p_play"])
    g = d.groupby(["game_id", "team_id"])
    top = d.loc[g["share"].idxmax()].assign(creator_out=lambda x: x["share"] * (1.0 - x["p_play"]))
    res = g["miss"].sum().rename("usage_missing").to_frame()
    res["creator_out"] = top.set_index(["game_id", "team_id"])["creator_out"]
    return res.reset_index()


def pam_player_table(records: Iterable[dict]) -> pd.DataFrame:
    """PAM records -> person_id, recorded_at, effective_from, creator (max weight of PRF-1/PRF-2 archetypes), n_mod."""
    rows = []
    for r in records:
        pid = (r.get("id_map") or {}).get("nba_person_id")
        if pid is None:
            continue
        cw = max([a.get("weight", 0.0) for a in r.get("archetypes", []) if a.get("id") in ("PRF-1", "PRF-2")] or [0.0])
        rows.append(dict(person_id=str(pid), recorded_at=pd.Timestamp(r["recorded_at"]),
                         effective_from=pd.Timestamp(r["effective_from"]), creator=float(cw), n_mod=len(r.get("modifiers", []))))
    return pd.DataFrame(rows, columns=["person_id", "recorded_at", "effective_from", "creator", "n_mod"])


def pam_flags(df: pd.DataFrame, pam: pd.DataFrame, game_date: Mapping[str, pd.Timestamp], point_in_time: bool = True) -> pd.DataFrame:
    """Per (game, team): rotation weight x p_play x PAM creator weight / modifier count.

    ``df``: game_id, team_id, person_id, w (rotation weight), p_play. A record applies to a game when effective_from <= game date
    and, if ``point_in_time``, recorded_at <= game date (a record written after the game is hindsight). The latest applicable
    record per person wins."""
    if pam.empty or df.empty:
        return pd.DataFrame(columns=["game_id", "team_id", "pam_creator", "pam_mod", "pam_cover"])
    d = df.copy()
    d["person_id"] = d["person_id"].astype(str)
    d["date"] = d["game_id"].map(game_date)
    j = d.merge(pam, on="person_id", how="inner")
    ok = j["effective_from"] <= j["date"]
    if point_in_time:
        ok &= j["recorded_at"] <= j["date"]
    j = j[ok].sort_values("recorded_at").drop_duplicates(["game_id", "team_id", "person_id"], keep="last")
    j["c"] = j["w"] * j["p_play"] * j["creator"]
    j["m"] = j["w"] * j["p_play"] * j["n_mod"]
    j["cov"] = j["w"]
    g = j.groupby(["game_id", "team_id"])
    return pd.concat([g["c"].sum().rename("pam_creator"), g["m"].sum().rename("pam_mod"), g["cov"].sum().rename("pam_cover")],
                     axis=1).reset_index()


def home_away_columns(team_rows: pd.DataFrame, home_team: Mapping[str, str], cols: Iterable[str]) -> pd.DataFrame:
    """Per-team columns -> game-level d_<c> (home - away) and s_<c> (home + away). Missing side -> NaN (the tree uses the centre)."""
    t = team_rows.copy()
    t["is_home"] = t["team_id"].astype(str).to_numpy() == t["game_id"].map(home_team).astype(str).to_numpy()
    h, a = t[t.is_home].set_index("game_id"), t[~t.is_home].set_index("game_id")
    idx = h.index.union(a.index)
    out = pd.DataFrame(index=idx)
    for c in cols:
        hv, av = h[c].reindex(idx), a[c].reindex(idx)
        out["d_" + c], out["s_" + c] = hv - av, hv + av
    return out
