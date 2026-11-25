"""NHL depth splits: goalie confirmation, referee crew, availability (W128.1, EXP-NHLDEPTH-001; PREREG 12_EXPLORATORY/nhl_depth/PREREG.md).

Layer-2 splits that tag an NHL game with a categorical leaf before routing:
  G ``goalie@game``    -- published starter vs the team's expected one: both_expected / any_backup / unknown.
  R ``officials@game`` -- the crew's shrunk prior total residual (earlier games only) in fit terciles: ref_high / ref_mid / ref_low.
  A ``availability@game`` -- ABSTAINS: the Muse archive has no point-in-time availability family. Always ``unknown``; never imputed.
Point-in-time: a snapshot is usable only if ``snapshot_at_utc <= row ts_utc``; a later one raises ``PITViolation`` when passed explicitly.
No Muse data -> ``unknown``, which is never scored as a leaf. Applies when: tagging an NHL row before routing; shadow only.
Default off: ``nhl_depth_on()`` needs PM_NHL_DEPTH=on. Interface: ``split_leaves(...)`` -> {split_name: leaf}.
"""
from __future__ import annotations

import os
from collections import Counter
from typing import Optional, Sequence

ARCHIVE_REPO = "eignacio1/sports-intel-archive"
ARCHIVE_SHA = "ab9951c37958af812fd170c544399cf75825d561"
SPLIT_NAMES = ("goalie@game", "officials@game", "availability@game")
REF_K = 20.0


class PITViolation(ValueError):
    """An input that was not known before the row's timestamp."""


def nhl_depth_on() -> bool:
    return os.environ.get("PM_NHL_DEPTH", "off").strip().lower() == "on"


def assert_pit(snapshot_at_utc: Optional[str], row_ts_utc: str) -> None:
    """ISO-8601 'Z' strings compare lexically. A snapshot taken after the row is a leak."""
    if snapshot_at_utc and snapshot_at_utc > row_ts_utc:
        raise PITViolation(f"snapshot {snapshot_at_utc} is after row {row_ts_utc}")


def expected_goalie(prior_starters: Sequence[str]) -> Optional[str]:
    """Most-played goalie among the team's last 10 prior starters; None with no history."""
    last = [g for g in prior_starters if g][-10:]
    return Counter(last).most_common(1)[0][0] if last else None


def goalie_team_leaf(published: Optional[str], confirmed: bool, expected: Optional[str]) -> str:
    if not published or not expected:
        return "unknown"
    if not confirmed:
        return "unconfirmed"
    return "confirmed_expected" if published == expected else "confirmed_backup"


def goalie_game_leaf(home: str, away: str) -> str:
    if "unknown" in (home, away):
        return "unknown"
    if "confirmed_backup" in (home, away):
        return "any_backup"
    return "both_expected" if (home, away) == ("confirmed_expected",) * 2 else "unknown"  # unconfirmed on either side is not scored


def crew_prior(prior_residuals: Sequence[float]) -> Optional[float]:
    r = list(prior_residuals)
    return None if not r else sum(r) / (len(r) + REF_K)  # shrunk toward 0 with REF_K pseudo-games


def ref_leaf(prior: Optional[float], cuts: Optional[tuple]) -> str:
    if prior is None or not cuts:
        return "unknown"
    lo, hi = cuts
    return "ref_low" if prior <= lo else "ref_high" if prior >= hi else "ref_mid"


def split_leaves(row_ts_utc: str, goalie_snap: Optional[dict], prior_starters: Optional[dict],
                 crew_prior_value: Optional[float], ref_cuts: Optional[tuple]) -> dict:
    """goalie_snap = one Muse goalies row; prior_starters = {'home': [...], 'away': [...]}; leaves are 'unknown' when an input is missing."""
    gl = "unknown"
    if goalie_snap:
        assert_pit(goalie_snap.get("snapshot_at_utc"), row_ts_utc)
        ps = prior_starters or {}
        h = goalie_team_leaf(goalie_snap.get("home_goalie"), bool(goalie_snap.get("home_confirmed")), expected_goalie(ps.get("home", [])))
        a = goalie_team_leaf(goalie_snap.get("away_goalie"), bool(goalie_snap.get("away_confirmed")), expected_goalie(ps.get("away", [])))
        gl = goalie_game_leaf(h, a)
    return {"goalie@game": gl, "officials@game": ref_leaf(crew_prior_value, ref_cuts), "availability@game": "unknown"}


# ---- row supply: Muse snapshots already fetched (pinned SHA, GitHub API) into a local directory ---------------------------------------
def muse_dir() -> Optional[str]:
    d = os.environ.get("NHL_MUSE_DIR")
    return d if d and os.path.isdir(d) else None


def _read(path: str) -> list:
    import json
    try:
        with open(path) as fh:
            rows = [json.loads(l) for l in fh if l.strip()]
        return [r for r in rows if r.get("game_id")]  # fetch-failure and NO_GAMES marker rows carry no game: skipped, never imputed
    except OSError:
        return []


def _parse_event(event_ticker: str):
    import re
    m = re.search(r"-(\d\d)([A-Z]{3})(\d\d)([A-Z]+)$", event_ticker or "")
    months = "JAN FEB MAR APR MAY JUN JUL AUG SEP OCT NOV DEC".split()
    if not m or m.group(2) not in months:
        return None
    return f"20{m.group(1)}-{months.index(m.group(2)) + 1:02d}-{m.group(3)}", m.group(4)


def leaves_for_row(row: dict, directory: Optional[str] = None) -> Optional[dict]:
    """Split leaves for an NHL shadow row from the Muse goalie snapshots in ``directory`` (default NHL_MUSE_DIR). None when there is no
    Muse data, no row timestamp, or the game is not in the snapshots: the split abstains, nothing is imputed. The officials leaf stays
    ``unknown`` here (the crew prior needs settled totals; the scoring script supplies it offline)."""
    d = directory or muse_dir()
    p = _parse_event(str(row.get("event_ticker") or ""))
    ts = row.get("ts_utc")
    if not d or not p or not ts:
        return None
    day, teams = p
    snaps = [r for r in _read(os.path.join(d, f"goalies-{day}.jsonl")) if (r.get("snapshot_at_utc") or "~") <= ts]
    abbr = lambda gid: set(str(gid).split("-")[:2])  # Muse game_id is HOME-AWAY-YYYY-MM-DD
    game = [r for r in snaps if all(a in teams for a in abbr(r["game_id"]))]
    if not game:
        return None
    snap = max(game, key=lambda r: r["snapshot_at_utc"])  # latest snapshot not after the row
    home_abbr, away_abbr = str(snap["game_id"]).split("-")[:2]
    prior = {"home": [], "away": []}
    import glob
    for f in sorted(glob.glob(os.path.join(d, "goalies-*.jsonl"))):
        if os.path.basename(f) >= f"goalies-{day}.jsonl":
            continue
        latest = {}
        for r in _read(f):
            latest[r["game_id"]] = r
        for r in latest.values():
            for side in ("home", "away"):
                if r.get(f"{side}_confirmed"):
                    key = "home" if str(r["game_id"]).split("-")[0 if side == "home" else 1] == home_abbr else (
                        "away" if str(r["game_id"]).split("-")[0 if side == "home" else 1] == away_abbr else None)
                    if key:
                        prior[key].append(r.get(f"{side}_goalie"))
    return split_leaves(ts, snap, prior, None, None)
