"""NBA depth splits from the sports-intel archive (W118.2, EXP-NBADEPTH-001; PREREG 12_EXPLORATORY/nba_depth_splits/PREREG.md).

Five factor classes, each a layer-3 split (ADR-0075) that tags an NBA row with categorical leaves before routing it to an arm:
  S1 ``pace_prod@total`` / ``net_rating@side``  -- 2025-26 team pace and net rating (r025 team advanced).
  S2 ``shotzone_matchup@total`` / ``@side``     -- offence zone mix x opponent allowed FG% by zone, points per shot.
  S3 ``lineup_status``                          -- confirmed vs projected lineups, rotation players OUT (daily snapshot).
  S4 ``home_road_gap@side``                     -- home team's home win% vs away team's road win%.
  S5 ``ref_crew@total``                         -- assigned crew's 2025-26 points / FTA per game (referee register).
Point-in-time: team / referee values are PRIOR COMPLETED season only (``PRIOR_SEASON`` = 2025, i.e. 2025-26; a profile whose season
is not strictly before the row's season is refused); snapshot values are used only when ``status_at_utc`` / ``snapshot_at_utc`` <=
the row's ``ts_utc``. Values come from the archive pinned at ``ARCHIVE_SHA`` (read-only). Unjoined inputs give leaf ``unknown``,
which is never scored. Interface: ``depth_filters(...)`` -> {filter_name: leaf}. Not wired into ``filter_supply.py`` (118.3 owns it).
Applies when: tagging an NBA row with depth leaves before routing; profiles come from ``build_profiles(Archive)`` (cached JSON).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping, Optional

from prediction_market_bot.archive_intake.archive import Archive, _read_jsonl
from prediction_market_bot.nba_engine import filters as nf

ARCHIVE_SHA = "bafaeef4de9596fd7a69941b36ca16a34af2f344"
PRIOR_SEASON = 2025  # archive season label 2025 = 2025-26, completed before any 2026-27 row
MIN_REF_GAMES = 20
ZONES = ("restricted area", "in the paint (non-ra)", "mid-range", "corner 3", "above the break 3")
ZONE_POINTS = {"restricted area": 2, "in the paint (non-ra)": 2, "mid-range": 2, "corner 3": 3, "above the break 3": 3}
LEAVES_LINEUP = ("confirmed", "mixed", "projected_clean", "projected_rotation_out")
SPLIT_NAMES = ("pace_prod@total", "net_rating@side", "shotzone_matchup@total", "shotzone_matchup@side",
               "lineup_status", "home_road_gap@side", "ref_crew@total")


class PITViolation(RuntimeError):
    pass


def _utc(s) -> Optional[datetime]:
    if not s:
        return None
    d = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def assert_prior_season(profile_season: int, row_season: int) -> None:
    if profile_season >= row_season:
        raise PITViolation(f"profile season {profile_season} is not before row season {row_season}")


# ---------------------------------------------------------------- build (archive -> profiles) ----------------------------------
def _zone_of(metric: str) -> Optional[str]:
    m = metric.lower()
    if m.startswith(("left corner", "right corner")):
        return None  # the aggregate 'corner 3' row is used; left/right would double count
    for z in ZONES:
        if m.startswith(z):
            return z
    return None


def build_profiles(archive: Archive) -> dict:
    """Stream the pinned archive once and return {teams, refs, edges, provenance}. Prior completed season only."""
    S = str(PRIOR_SEASON)
    teams: dict = {}
    name2abbr: dict = {}
    refs: dict = {}
    t = lambda ab: teams.setdefault(ab, {})  # noqa: E731

    for p in archive.split_files("nba"):
        n = p.name
        if n.startswith("referees-2025-26"):
            for r in _read_jsonl(p):
                v = _f(r.get("value"))
                if v is None or str(r.get("season")) != S:
                    continue
                m = r["metric"]
                d = refs.setdefault(r["subject"], {})
                if m.startswith("games worked"):
                    d["games"] = v
                elif m.startswith("total points per game"):
                    d["pts"] = v
                elif m.startswith("free-throw attempts per game"):
                    d["fta"] = v
            continue
        if n.startswith("r025-team-advanced-season"):
            for r in _read_jsonl(p):
                if str(r.get("season")) != S:
                    continue
                ab = r.get("team")
                name2abbr[r["subject"]] = ab
                v = _f(r.get("value"))
                if r["metric"].startswith("pace"):
                    t(ab)["pace"] = v
                elif r["metric"].startswith("net rating"):
                    t(ab)["net_rating"] = v
            continue
        key = {"C-001": "wp_home", "C-006": "wp_road", "C-076": "zone_off_home", "C-081": "zone_off_road",
               "C-688": "zone_def"}.get(n.split(".")[0])
        if key is None:
            continue
        for r in _read_jsonl(p):
            if str(r.get("season")) != S:
                continue
            ab = r.get("team")
            name2abbr[r["subject"]] = ab
            v = _f(r.get("value"))
            m = r["metric"].lower().split(" (nba")[0]
            if key.startswith("zone_off") and "attempt" in m:
                z = _zone_of(m)
                if z:
                    d = t(ab).setdefault(key, {})
                    d[z] = d.get(z, 0.0) + (v or 0.0)
            elif key == "zone_def" and "percentage" in m:
                z = _zone_of(m.replace("opponent field goal percentage, ", ""))
                if z:
                    t(ab).setdefault("zone_def_fg", {})[z] = v
            elif key in ("wp_home", "wp_road") and "win percentage" in m:
                t(ab)["home_wp" if key == "wp_home" else "road_wp"] = v

    for ab, d in teams.items():  # normalise offence mix over home + road
        mix: dict = {}
        for k in ("zone_off_home", "zone_off_road"):
            for z, a in d.pop(k, {}).items():
                mix[z] = mix.get(z, 0.0) + a
        tot = sum(mix.values())
        if tot > 0:
            d["zone_off_share"] = {z: a / tot for z, a in mix.items()}
    prof = {"archive_sha": ARCHIVE_SHA, "season": PRIOR_SEASON, "teams": teams, "name2abbr": name2abbr,
            "refs": {k: v for k, v in refs.items() if v.get("games", 0) >= MIN_REF_GAMES and "pts" in v and "fta" in v}}
    prof["edges"] = _edges(prof)
    return prof


def _f(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------- derived scalars ----------------------------------------------
def matchup_value(off: Mapping, dfn: Mapping) -> Optional[float]:
    """Points per shot of offence ``off`` against defence ``dfn`` (zone mix x allowed FG% x zone points); None if either is missing."""
    share, fg = off.get("zone_off_share"), dfn.get("zone_def_fg")
    if not share or not fg or any(z not in share or fg.get(z) is None for z in ZONES):
        return None
    # allowed FG% may be stored as percent or fraction; normalise
    return sum(share[z] * (fg[z] / 100.0 if fg[z] > 1.0 else fg[z]) * ZONE_POINTS[z] for z in ZONES)


def _pct_rank(values: list, x: float) -> float:
    srt = sorted(values)
    lo = sum(1 for v in srt if v < x)
    eq = sum(1 for v in srt if v == x)
    return (lo + 0.5 * eq) / len(srt)


def _edges(prof: dict) -> dict:
    teams = prof["teams"]
    # side edge = outer thirds of (home value - away value) over all ordered home/away team pairs
    side = []
    for h in teams:
        for a in teams:
            if h == a:
                continue
            vh, va = matchup_value(teams[h], teams[a]), matchup_value(teams[a], teams[h])
            if vh is not None and va is not None:
                side.append(vh - va)
    tot = []
    for h in teams:
        for a in teams:
            if h != a:
                vh, va = matchup_value(teams[h], teams[a]), matchup_value(teams[a], teams[h])
                if vh is not None and va is not None:
                    tot.append((vh + va) / 2)
    e = {"pairs_n": len(side)}
    if side:
        s, t_ = sorted(side), sorted(tot)
        e["matchup_side"] = [s[int(len(s) / 3)], s[int(2 * len(s) / 3)]]
        e["matchup_total"] = [t_[int(len(t_) / 3)], t_[int(2 * len(t_) / 3)]]
    return e


def _tercile(p: Optional[float]) -> str:
    if p is None:
        return "unknown"
    return "high" if p > nf.HIGH else "low" if p < nf.LOW else "mid"


def _side_from_pct(ph: Optional[float], pa: Optional[float]) -> str:
    if ph is None or pa is None:
        return "unknown"
    d = ph - pa
    return "home_edge" if d > nf.SIDE_EDGE else "away_edge" if d < -nf.SIDE_EDGE else "neutral"


def _team_pcts(prof: dict, key: str) -> dict:
    vals = {ab: d[key] for ab, d in prof["teams"].items() if d.get(key) is not None}
    v = list(vals.values())
    return {ab: _pct_rank(v, x) for ab, x in vals.items()}


# ---------------------------------------------------------------- snapshot classes ------------------------------------------------
def lineup_leaf(snap: Optional[Mapping], ts_utc, rotation: Mapping[str, set]) -> str:
    """Latest snapshot record for the game with status_at_utc <= ts_utc. ``rotation`` = {side: names seen at >=20 min}."""
    if not snap:
        return "unknown"
    st, ts = _utc(snap.get("status_at_utc")), _utc(ts_utc)
    if st is None or ts is None:
        return "unknown"
    if st > ts:
        raise PITViolation(f"lineup snapshot {st} is after row time {ts}")
    a, h = str(snap.get("away_status")), str(snap.get("home_status"))
    if a == "Confirmed" and h == "Confirmed":
        return "confirmed"
    if a == "Confirmed" or h == "Confirmed":
        return "mixed"
    out = snap.get("out_list") or {}
    for side in ("away", "home"):
        names = {s.split(",")[0].strip() for s in out.get(side, [])}
        if names & rotation.get(side, set()):
            return "projected_rotation_out"
    return "projected_clean"


def ref_leaf(prof: dict, crew: list, snap_at_utc, ts_utc) -> str:
    if not crew:
        return "unknown"
    sa, ts = _utc(snap_at_utc), _utc(ts_utc)
    if sa is None or ts is None:
        return "unknown"
    if sa > ts:
        raise PITViolation(f"refs snapshot {sa} is after row time {ts}")
    refs = prof["refs"]
    pts = [r["pts"] for r in refs.values()]
    fta = [r["fta"] for r in refs.values()]
    got = [refs[n] for n in crew if n in refs]
    if len(got) < 2:
        return "unknown"
    p = (sum(_pct_rank(pts, g["pts"]) for g in got) / len(got) + sum(_pct_rank(fta, g["fta"]) for g in got) / len(got)) / 2
    return _tercile(p)


# ---------------------------------------------------------------- the interface -------------------------------------------------
def depth_filters(home: str, away: str, prof: dict, *, row_season: int, lineup_snap=None, rotation=None,
                  crew=None, refs_snap_at=None, ts_utc=None) -> dict:
    """{filter_name: leaf} for one game. ``home``/``away`` are team abbreviations; every input is point-in-time by construction."""
    assert_prior_season(prof["season"], row_season)
    T = prof["teams"]
    h, a = T.get(home, {}), T.get(away, {})
    out = {}
    pace = _team_pcts(prof, "pace")
    out["pace_prod@total"] = _tercile(None if home not in pace or away not in pace else (pace[home] + pace[away]) / 2)
    net = _team_pcts(prof, "net_rating")
    out["net_rating@side"] = _side_from_pct(net.get(home), net.get(away))
    vh, va = matchup_value(h, a), matchup_value(a, h)
    e = prof.get("edges", {})
    if vh is None or va is None or "matchup_side" not in e:
        out["shotzone_matchup@total"] = out["shotzone_matchup@side"] = "unknown"
    else:
        lo, hi = e["matchup_total"]
        m = (vh + va) / 2
        out["shotzone_matchup@total"] = "high" if m > hi else "low" if m < lo else "mid"
        lo, hi = e["matchup_side"]
        d = vh - va
        out["shotzone_matchup@side"] = "home_edge" if d > hi else "away_edge" if d < lo else "neutral"
    out["lineup_status"] = lineup_leaf(lineup_snap, ts_utc, rotation or {}) if lineup_snap else "unknown"
    hw, rw = _team_pcts(prof, "home_wp"), _team_pcts(prof, "road_wp")
    out["home_road_gap@side"] = _side_from_pct(hw.get(home), rw.get(away))
    out["ref_crew@total"] = ref_leaf(prof, crew or [], refs_snap_at, ts_utc) if crew else "unknown"
    return out
