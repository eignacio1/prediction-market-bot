"""NFL play callers (N11): who called the plays, and what each caller tends to do, point-in-time.

Stage: interpreted (W94.2 Part C). Nothing here is wired to a model, runner, order or registry cell.

Caller of record
    The offensive coordinator of record from Muse R-019 (``sports-intel-archive``
    ``L3-split/nfl/coordinators.claims.jsonl``, REPORTED, secondary source Pro Football History),
    attributed per team-season (and from a stated week when a season is split). The archive holds NO
    play-caller records ("the bulk source never states who calls plays"), so the OC of record is a
    proxy: ``OC of record != confirmed play caller``. Where a team-season has no OC record the
    game's head coach (nflverse ``home_coach``/``away_coach``) is the caller, keyed ``HC:<name>``.

Tendencies (residual form, so the league mean is 0 by construction)
    pass_oe  pass over expected, by down / distance / score / clock
    go4_oe   fourth-down go rate over expected, by distance / field position / score / clock
    pace     seconds per play, situation-neutral (qtr 1-3, score within 7, not in the 2-min drill,
             prior play an in-bounds run), minus the league mean of earlier seasons
    lead_oe  pass over expected when leading by 1-16 in the fourth quarter (lead protection)

Shrinkage and reset rule
    estimate = S / (n + k): S is the caller's summed residual over earlier plays, n the plays, k a
    per-tendency prior weight fitted on 2016-2019 only. The prior is the league mean (residual 0), so
    a caller with no history is exactly 0. State is keyed by PERSON, not team: a caller who moves keeps
    his own history and a new caller starts at the prior. Between seasons the state decays by
    ``season_decay`` per elapsed season. A team's coordinator change therefore resets that team's
    tendency toward the prior because the new caller's key has no history.

Point-in-time: ``CallerLedger.estimate`` reads only games passed to ``update`` before it; the expected
models for season s are fit on seasons strictly before s.
"""
from __future__ import annotations

import json
import re
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

FEATURES: Tuple[str, ...] = ("pass_oe", "go4_oe", "pace", "lead_oe")

SLUG_ABBR: Dict[str, str] = {
    "arizona-cardinals": "ARI", "atlanta-falcons": "ATL", "baltimore-ravens": "BAL", "buffalo-bills": "BUF",
    "carolina-panthers": "CAR", "chicago-bears": "CHI", "cincinnati-bengals": "CIN", "cleveland-browns": "CLE",
    "dallas-cowboys": "DAL", "denver-broncos": "DEN", "detroit-lions": "DET", "green-bay-packers": "GB",
    "houston-texans": "HOU", "indianapolis-colts": "IND", "jacksonville-jaguars": "JAX",
    "kansas-city-chiefs": "KC", "las-vegas-raiders": "LV", "los-angeles-chargers": "LAC",
    "los-angeles-rams": "LA", "miami-dolphins": "MIA", "minnesota-vikings": "MIN",
    "new-england-patriots": "NE", "new-orleans-saints": "NO", "new-york-giants": "NYG",
    "new-york-jets": "NYJ", "philadelphia-eagles": "PHI", "pittsburgh-steelers": "PIT",
    "san-francisco-49ers": "SF", "seattle-seahawks": "SEA", "tampa-bay-buccaneers": "TB",
    "tennessee-titans": "TEN", "washington-commanders": "WAS",
}
# nflverse normalizes relocated franchises in pbp from 2016 (LV, LAC, LA); older codes mapped for safety.
CANON = {"OAK": "LV", "SD": "LAC", "STL": "LA", "LAR": "LA", "JAC": "JAX", "WSH": "WAS"}


def canon(abbr: str) -> str:
    return CANON.get(abbr, abbr)


# ---------------------------------------------------------------------------------------- caller of record
def parse_start_week(claim: str) -> int:
    """Week a split-season record starts ("from Week 11 onward" -> 11); 1 when the record covers the season."""
    m = re.search(r"from Week (\d+)", claim or "")
    return int(m.group(1)) if m else 1


OcTable = Dict[Tuple[str, int], List[Tuple[int, str]]]


def load_oc_table(rows: Iterable[dict]) -> OcTable:
    """(team abbr, season) -> [(start_week, name)] sorted by start_week, offensive coordinators only."""
    out: OcTable = {}
    for r in rows:
        if "-r019-oc-" not in r.get("id", "") or not r.get("player"):
            continue
        abbr = SLUG_ABBR.get(r["team"])
        if abbr is None:
            continue
        out.setdefault((abbr, int(r["season"])), []).append((parse_start_week(r.get("claim", "")), r["player"]))
    for v in out.values():
        v.sort()
    return out


def read_oc_jsonl(path: str) -> OcTable:
    with open(path) as fh:
        return load_oc_table(json.loads(line) for line in fh if line.strip())


def caller_for(oc: OcTable, team: str, season: int, week: int, head_coach: Optional[str]) -> Tuple[Optional[str], str]:
    """(caller key, source). Source is 'R-019 OC' or 'HC fallback'; key None when neither is known."""
    recs = oc.get((canon(team), season))
    if recs:
        name = recs[0][1]
        for start, who in recs:
            if start <= week:
                name = who
        return "OC:" + name, "R-019 OC"
    if head_coach:
        return "HC:" + head_coach, "HC fallback"
    return None, "none"


# ---------------------------------------------------------------------------------------- shrinkage ledger
def shrunk(s: float, n: float, k: float) -> float:
    """Residual mean shrunk to the prior (0). n=0 -> exactly 0."""
    return s / (n + k) if (n + k) > 0 else 0.0


class CallerLedger:
    """Running per-person tallies. ``estimate`` sees only what ``update`` has been given."""

    def __init__(self, k: Dict[str, float], season_decay: float = 1.0):
        self.k = dict(k)
        self.decay = season_decay
        self._st: Dict[str, Dict[str, List[float]]] = {}  # key -> feat -> [s, n, last_season]

    def _decayed(self, key: str, feat: str, season: int) -> Tuple[float, float]:
        s, n, last = self._st.get(key, {}).get(feat, (0.0, 0.0, season))
        f = self.decay ** max(season - int(last), 0)
        return s * f, n * f

    def estimate(self, key: Optional[str], season: int) -> Dict[str, float]:
        if key is None:
            return {f: 0.0 for f in FEATURES}
        return {f: shrunk(*self._decayed(key, f, season), self.k[f]) for f in FEATURES}

    def plays(self, key: Optional[str], season: int) -> Dict[str, float]:
        if key is None:
            return {f: 0.0 for f in FEATURES}
        return {f: self._decayed(key, f, season)[1] for f in FEATURES}

    def update(self, key: Optional[str], season: int, sums: Dict[str, Tuple[float, float]]) -> None:
        if key is None:
            return
        for f, (s, n) in sums.items():
            s0, n0 = self._decayed(key, f, season)
            self._st.setdefault(key, {})[f] = [s0 + s, n0 + n, season]


# ---------------------------------------------------------------------------------------- expected models
def _score_bucket(sd: pd.Series) -> pd.Series:
    return pd.cut(sd, [-np.inf, -8.5, -0.5, 0.5, 8.5, np.inf], labels=False)


def _clock_bucket(qtr: pd.Series, gsr: pd.Series, hsr: pd.Series) -> pd.Series:
    late = ((qtr == 4) & (gsr <= 300)) | ((qtr == 2) & (hsr <= 120))
    return np.where(late, 5, qtr.clip(1, 4) - 1).astype(int)


def fit_expected(train: pd.DataFrame, y: str, fine: Sequence[str], coarse: Sequence[str], m: float = 20.0):
    """Cell-mean model with two shrinkage levels (fine -> coarse -> global). Returns predict(df) -> ndarray."""
    g = float(train[y].mean())
    c = train.groupby(list(coarse))[y].agg(["sum", "count"])
    c["est"] = (c["sum"] + m * g) / (c["count"] + m)
    f = train.groupby(list(fine))[y].agg(["sum", "count"])

    def predict(df: pd.DataFrame) -> np.ndarray:
        ce = df[list(coarse)].merge(c[["est"]], left_on=list(coarse), right_index=True, how="left")["est"].fillna(g)
        fi = df[list(fine)].merge(f, left_on=list(fine), right_index=True, how="left")
        n = fi["count"].fillna(0).to_numpy()
        s = fi["sum"].fillna(0).to_numpy()
        return (s + m * ce.to_numpy()) / (n + m)

    return predict


def prep_plays(pbp: pd.DataFrame) -> pd.DataFrame:
    """Add the situation buckets and the pass/go indicators; keep only scrimmage calls and fourth-down decisions."""
    d = pbp[pbp["posteam"].notna() & (pbp["season_type"] == "REG")].copy()
    d["posteam"] = d["posteam"].map(canon)
    d["defteam"] = d["defteam"].map(canon)
    d["sb"] = _score_bucket(d["score_differential"].fillna(0))
    d["cb"] = _clock_bucket(d["qtr"].clip(1, 4), d["game_seconds_remaining"].fillna(0), d["half_seconds_remaining"].fillna(0))
    d["yb"] = pd.cut(d["ydstogo"], [-np.inf, 2, 6, 10, np.inf], labels=False)
    d["yb4"] = pd.cut(d["ydstogo"], [-np.inf, 1, 2, 4, 7, 10, np.inf], labels=False)
    d["fb"] = pd.cut(d["yardline_100"], [-np.inf, 35, 50, 65, np.inf], labels=False)
    return d


def scrimmage(d: pd.DataFrame) -> pd.DataFrame:
    s = d[d["play_type"].isin(["pass", "run"]) & (d["qb_kneel"] != 1) & (d["qb_spike"] != 1)
          & (d["two_point_attempt"] != 1) & d["down"].isin([1, 2, 3, 4])].copy()
    s["is_pass"] = (s["play_type"] == "pass").astype(float)
    return s


def fourth(d: pd.DataFrame) -> pd.DataFrame:
    s = d[(d["down"] == 4) & d["play_type"].isin(["pass", "run", "punt", "field_goal"])].copy()
    s["go"] = s["play_type"].isin(["pass", "run"]).astype(float)
    return s


def neutral_pace(d: pd.DataFrame) -> pd.DataFrame:
    """Snap-to-snap seconds after an in-bounds, un-penalized run, in neutral game state."""
    d = d.sort_values(["game_id", "play_id"]) if "play_id" in d.columns else d
    g = d.groupby(["game_id", "drive", "posteam"], sort=False)
    prev_t = g["game_seconds_remaining"].shift(1)
    prev_run = g["play_type"].shift(1) == "run"
    prev_oob = g["out_of_bounds"].shift(1).fillna(0) == 1
    prev_pen = g["penalty"].shift(1).fillna(0) == 1
    prev_to = g["timeout"].shift(1).fillna(0) == 1
    prev_q = g["qtr"].shift(1)
    out = d.assign(elapsed=prev_t - d["game_seconds_remaining"])
    keep = (prev_run & ~prev_oob & ~prev_pen & ~prev_to & (prev_q == d["qtr"]) & d["play_type"].isin(["pass", "run"])
            & (d["qtr"] <= 3) & (d["score_differential"].abs() <= 7) & (d["half_seconds_remaining"] > 120)
            & (d["penalty"].fillna(0) != 1) & out["elapsed"].between(5, 45))
    return out[keep]


def team_game_sums(seasons: Dict[int, pd.DataFrame], first: int) -> pd.DataFrame:
    """One row per (season, game, team) with per-feature (sum of residual, play count).

    ``seasons`` maps year -> raw pbp. Expected models for year y are fit on years < y present in ``seasons``.
    """
    rows = []
    prepped = {y: prep_plays(df) for y, df in seasons.items()}
    for y in sorted(prepped):
        if y < first:
            continue
        past = [prepped[p] for p in sorted(prepped) if p < y]
        if not past:
            continue
        tr = pd.concat(past)
        sc_tr, f4_tr = scrimmage(tr), fourth(tr)
        pass_pred = fit_expected(sc_tr, "is_pass", ["down", "yb", "sb", "cb"], ["down", "yb"])
        go_pred = fit_expected(f4_tr, "go", ["yb4", "fb", "sb", "cb"], ["yb4", "fb"])
        pace_mean = float(neutral_pace(tr)["elapsed"].mean())
        cur = prepped[y]
        sc, f4, pc = scrimmage(cur), fourth(cur), neutral_pace(cur)
        sc["r"] = sc["is_pass"] - pass_pred(sc)
        f4["r"] = f4["go"] - go_pred(f4)
        pc = pc.assign(r=pc["elapsed"] - pace_mean)
        lead = sc[(sc["qtr"] == 4) & sc["score_differential"].between(1, 16)]
        keys = ["game_id", "posteam"]
        parts = {"pass_oe": sc, "go4_oe": f4, "pace": pc, "lead_oe": lead}
        agg = None
        for f, df in parts.items():
            a = df.groupby(keys)["r"].agg(["sum", "count"]).rename(columns={"sum": f + "_s", "count": f + "_n"})
            agg = a if agg is None else agg.join(a, how="outer")
        agg = agg.fillna(0.0).reset_index()
        meta = cur.groupby("game_id").agg(season=("season", "first"), week=("week", "first"), date=("game_date", "first"),
                                          home=("home_team", "first"), away=("away_team", "first"),
                                          home_coach=("home_coach", "first"), away_coach=("away_coach", "first")).reset_index()
        meta["home"] = meta["home"].map(canon)
        meta["away"] = meta["away"].map(canon)
        m = agg.merge(meta, on="game_id")
        m["team"] = m["posteam"]
        m["coach"] = np.where(m["team"] == m["home"], m["home_coach"], m["away_coach"])
        m["opp"] = np.where(m["team"] == m["home"], m["away"], m["home"])
        m["is_home"] = (m["team"] == m["home"]).astype(int)
        rows.append(m.drop(columns=["posteam", "home_coach", "away_coach"]))
    return pd.concat(rows, ignore_index=True)


def replay(tg: pd.DataFrame, oc: OcTable, k: Dict[str, float], season_decay: float = 1.0) -> pd.DataFrame:
    """As-of caller tendencies for every team-game: estimate first, then update. Returns tg + est_<f>, n_<f>, caller, source."""
    led = CallerLedger(k, season_decay)
    tg = tg.sort_values(["season", "week", "date", "game_id", "team"]).reset_index(drop=True)
    est = {f: [] for f in FEATURES}
    npl = {f: [] for f in FEATURES}
    callers, sources = [], []
    for r in tg.itertuples(index=False):
        key, src = caller_for(oc, r.team, int(r.season), int(r.week), r.coach)
        e, n = led.estimate(key, int(r.season)), led.plays(key, int(r.season))
        for f in FEATURES:
            est[f].append(e[f])
            npl[f].append(n[f])
        callers.append(key)
        sources.append(src)
        led.update(key, int(r.season), {f: (getattr(r, f + "_s"), getattr(r, f + "_n")) for f in FEATURES})
    out = tg.copy()
    for f in FEATURES:
        out["est_" + f] = est[f]
        out["n_" + f] = npl[f]
    out["caller"] = callers
    out["source"] = sources
    return out
