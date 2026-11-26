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
    last = [norm_name(g) for g in prior_starters if g][-10:]
    return Counter(last).most_common(1)[0][0] if last else None


def norm_name(name) -> str:
    """Accent-folded lower-case alphanumerics: 'Jesper Wallstedt' == 'jesper wallstedt', 'Stützle' == 'stutzle'. Muse and the NHL store spell alike
    except for case / accents / punctuation."""
    import re
    import unicodedata
    t = unicodedata.normalize("NFKD", str(name or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()


def goalie_team_leaf(published: Optional[str], confirmed: bool, expected: Optional[str]) -> str:
    """unknown = no expected starter (no history); unconfirmed = no published confirmed starter yet (the prior alone speaks)."""
    if not expected:
        return "unknown"
    if not published or not confirmed:
        return "unconfirmed"
    return "confirmed_expected" if norm_name(published) == norm_name(expected) else "confirmed_backup"


def goalie_game_leaf(home: str, away: str) -> str:
    """both_expected / any_backup need a confirmed starter; ``prior_only`` = an expected starter exists for both teams but at least one start is
    not confirmed at the snapshot (or there is no snapshot): logged, never scored as a leaf. ``unknown`` only when a team has no starts on record."""
    if "unknown" in (home, away):
        return "unknown"
    if "confirmed_backup" in (home, away):
        return "any_backup"
    return "both_expected" if (home, away) == ("confirmed_expected",) * 2 else "prior_only"


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
    """goalie_snap = one Muse goalies row or None; prior_starters = {'home': [...], 'away': [...]} (chronological, strictly before the game).
    With no snapshot the event-store prior alone still gives each team an expected starter (leaf ``prior_only``); ``unknown`` only when a team
    has no starts on record."""
    ps = prior_starters or {}
    snap = goalie_snap or {}
    if goalie_snap:
        assert_pit(goalie_snap.get("snapshot_at_utc"), row_ts_utc)
    h = goalie_team_leaf(snap.get("home_goalie"), bool(snap.get("home_confirmed")), expected_goalie(ps.get("home", [])))
    a = goalie_team_leaf(snap.get("away_goalie"), bool(snap.get("away_confirmed")), expected_goalie(ps.get("away", [])))
    return {"goalie@game": goalie_game_leaf(h, a), "officials@game": ref_leaf(crew_prior_value, ref_cuts), "availability@game": "unknown"}


def expectation(prior: Sequence[str], season_prior: Optional[Sequence[str]] = None) -> dict:
    """The expected starter and how firm it is: last-10 modal goalie (the PREREG definition), his share of those 10, his share of the team's
    starts this season, and how many starts are on record. All from starts strictly before the game."""
    exp = expected_goalie(prior)
    last = [norm_name(g) for g in prior if g][-10:]
    sp = [norm_name(g) for g in (season_prior if season_prior is not None else prior) if g]
    return {"goalie": exp, "last10_share": round(last.count(exp) / len(last), 3) if exp else None,
            "season_share": round(sp.count(exp) / len(sp), 3) if exp and sp else None, "n_prior": len([g for g in prior if g])}


# ---- expected starters from the NHL event store (W129.1) ----------------------------------------------------------------------------
class StarterStore:
    """Who started in goal for each team, per game, from the compiled NHL event store (box_players goalies + rosters names), plus the schedule
    so a row's game resolves to its home / away abbreviations without any Muse file."""

    def __init__(self, games: Sequence[dict], starts: Sequence[dict]):
        self.games = {(g["date"], g["home"], g["away"]) for g in games}
        self.by_team: dict = {}
        for s in sorted(starts, key=lambda r: (r["date"], str(r.get("game_id", "")))):
            self.by_team.setdefault(s["team"], []).append(s)
        self.last_date = max((s["date"] for s in starts), default=None)

    def prior(self, team: str, day: str) -> list:
        return [s for s in self.by_team.get(team, []) if s["date"] < day]

    def find_game(self, day: str, teams: str) -> Optional[tuple]:
        """(home, away) for the schedule game on ``day`` whose abbreviations fill the Kalshi suffix ``teams`` (AWAYHOME), or None."""
        for (d, h, a) in self.games:
            if d == day and (_kalshi(a) + _kalshi(h) == teams or a + h == teams):
                return h, a
        return None


_KALSHI = {"LAK": "LA", "NJD": "NJ", "TBL": "TB", "SJS": "SJ"}  # store abbreviation -> Kalshi two-letter code


def _kalshi(abbr: str) -> str:
    return _KALSHI.get(abbr, abbr)


def starts_from_tables(games, box, rosters) -> list:
    """Starter per (game, team) from pandas frames: the goalie flagged ``starter`` in the box score, else the one with the most TOI.
    Names come from the game roster. Rows: {game_id, date, team (abbr), goalie (normalized), season}."""
    gl = box[box["group"] == "goalies"]
    names = {(r.game_id, r.player_id): norm_name(f"{r.first} {r.last}") for r in rosters.itertuples()}
    g = {r.game_id: r for r in games.itertuples()}
    out = []
    for (gid, tid), grp in gl.groupby(["game_id", "team_id"]):
        if gid not in g:
            continue
        grp = grp.assign(_s=grp["starter"].fillna(False).astype(bool).astype(int), _t=grp["toi_s"].fillna(0))
        top = grp.sort_values(["_s", "_t"], ascending=False).iloc[0]
        nm = names.get((gid, top["player_id"]))
        gm = g[gid]
        team = gm.home if tid == gm.home_team_id else gm.away if tid == gm.away_team_id else None
        if nm and team:
            out.append({"game_id": int(gid), "date": str(gm.game_date_et), "team": team, "goalie": nm, "season": int(gm.season)})
    return out


_STORE: dict = {}


def default_store(directory: Optional[str] = None) -> Optional[StarterStore]:
    """The starter store from the compiled event store directory (NHL_EVENT_STORE or exp_output/NHL_EVENTS), cached until a file changes.
    None when the store is absent: the split then abstains to the Muse-confirmed history alone."""
    import glob
    try:
        from prediction_market_bot.decision_trees.filter_supply import nhl_store_dir
        d = directory or nhl_store_dir()
        files = sorted(glob.glob(os.path.join(d, "*.parquet")))
        key = (os.path.abspath(d), max([os.path.getmtime(f) for f in files] or [0]))
        if _STORE.get("key") == key:
            return _STORE["v"]
        import pandas as pd
        from prediction_market_bot.c1_signal_ingestion.nhl_event_store import store_seasons
        games, starts = [], []
        for y in store_seasons():
            pg, pb, pr = (os.path.join(d, f"{k}_{y}.parquet") for k in ("games", "box_players", "rosters"))
            if not (os.path.exists(pg) and os.path.exists(pb) and os.path.exists(pr)):
                continue
            g = pd.read_parquet(pg, columns=["game_id", "season", "game_date_et", "home", "away", "home_team_id", "away_team_id"])
            g = g.drop_duplicates("game_id", keep="last")
            games += [{"date": str(r.game_date_et), "home": r.home, "away": r.away} for r in g.itertuples()]
            b = pd.read_parquet(pb, columns=["game_id", "team_id", "player_id", "group", "toi_s", "starter"])
            r_ = pd.read_parquet(pr, columns=["game_id", "player_id", "first", "last", "position"])
            r_ = r_[r_["position"] == "G"]
            starts += starts_from_tables(g, b, r_)
        v = StarterStore(games, starts) if games else None
    except Exception:  # noqa: BLE001  -- a broken store abstains; it never blocks a row
        v = None
        key = None
    _STORE.clear()
    _STORE.update(key=key, v=v)
    return v


# ---- row supply: Muse snapshots already fetched (pinned SHA, GitHub API) into a local directory ---------------------------------------
def muse_dir() -> Optional[str]:
    # NHL_MUSE_DIR, else the directory nhl_muse_fetch.py writes by default (exp_output/NHL_MUSE under the repo root)
    d = os.environ.get("NHL_MUSE_DIR") or os.path.join(os.path.dirname(os.path.abspath(__file__)), *[".."] * 4, "exp_output", "NHL_MUSE")
    d = os.path.normpath(d)
    return d if os.path.isdir(d) else None


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


def _muse_confirmed_starts(d: str, day: str, after: Optional[str]) -> dict:
    """{team abbr: [(date, goalie)]} from Muse's last snapshot per game on days in (after, day): confirmed starters only. Fills the days the
    event store has not compiled yet (its refresh lags the slate by a day or more)."""
    import glob
    out: dict = {}
    for f in sorted(glob.glob(os.path.join(d, "goalies-*.jsonl"))):
        fday = os.path.basename(f)[len("goalies-"):-len(".jsonl")]
        if fday >= day or (after is not None and fday <= after):
            continue
        latest = {}
        for r in _read(f):
            if r.get("snapshot_at_utc", "") >= latest.get(r["game_id"], {}).get("snapshot_at_utc", ""):
                latest[r["game_id"]] = r
        for r in latest.values():
            parts = str(r["game_id"]).split("-")
            for side, abbr in (("home", parts[0]), ("away", parts[1])):
                if r.get(f"{side}_confirmed") and r.get(f"{side}_goalie"):
                    out.setdefault(abbr, []).append((fday, r[f"{side}_goalie"]))
    return out


def depth_for_row(row: dict, directory: Optional[str] = None, store: Optional[StarterStore] = None) -> Optional[tuple]:
    """(split_leaves, expected_starters) for an NHL shadow row, or None when neither the event store nor Muse knows the game.
    Expected starter = the store's starts strictly before the game date, topped up with Muse-confirmed starts on days the store lacks;
    Muse's latest snapshot taken at or before the row's timestamp supplies the published starter. The officials leaf stays ``unknown``
    here (the crew prior needs settled totals; scoring supplies it offline)."""
    d = directory or muse_dir()
    store = store if store is not None else default_store()
    p = _parse_event(str(row.get("event_ticker") or ""))
    ts = row.get("ts_utc")
    if not p or not ts or (not d and store is None):
        return None
    day, teams = p
    snap = None
    if d:
        snaps = [r for r in _read(os.path.join(d, f"goalies-{day}.jsonl")) if (r.get("snapshot_at_utc") or "~") <= ts]
        game = [r for r in snaps if _same_game(str(r["game_id"]), teams)]
        snap = max(game, key=lambda r: r["snapshot_at_utc"]) if game else None
    if snap:
        home_abbr, away_abbr = str(snap["game_id"]).split("-")[:2]
    else:
        g = store.find_game(day, teams) if store else None
        if not g:
            return None
        home_abbr, away_abbr = g
    prior, season_prior, src = {}, {}, "muse"
    for side, abbr in (("home", home_abbr), ("away", away_abbr)):
        st = store.prior(abbr, day) if store else []
        extra = [g for _, g in _muse_confirmed_starts(d, day, store.last_date if store else None).get(abbr, [])] if d else []
        prior[side] = [s["goalie"] for s in st] + extra
        season = day[:4] if day[5:7] >= "09" else str(int(day[:4]) - 1)
        season_prior[side] = [s["goalie"] for s in st if s["season"] == int(season)] + extra
        if st:
            src = "store" if not extra else "store+muse"
    leaves = split_leaves(ts, snap, prior, None, None)
    exp = {side: expectation(prior[side], season_prior[side]) for side in ("home", "away")}
    exp.update(source=src, snapshot_at_utc=(snap or {}).get("snapshot_at_utc"))
    return leaves, exp


def _same_game(muse_game_id: str, teams: str) -> bool:
    """Muse game_id is HOME-AWAY-YYYY-MM-DD with store abbreviations; the Kalshi suffix is AWAYHOME with two-letter LA / NJ / TB / SJ."""
    h, a = muse_game_id.split("-")[:2]
    return _kalshi(a) + _kalshi(h) == teams or a + h == teams


def leaves_for_row(row: dict, directory: Optional[str] = None, store: Optional[StarterStore] = None) -> Optional[dict]:
    """Split leaves only (see ``depth_for_row``); None when nothing knows the game: the split abstains, nothing is imputed."""
    r = depth_for_row(row, directory, store)
    return r[0] if r else None
