"""NBA granularity-index filter -- ADR-0075 component 2 for NBA (W109.1 Part A).

Split x rank-vs-history-at-the-same-point-in-the-season x matchup cross x market map, then the filter that lets extremes
and mismatches through and stops the median. The machinery is the sport-agnostic ``nfl_engine.granularity_index``; this
module is the NBA surface of it: the NBA split (rest state, point-in-time by construction), the ``game_no`` clock, the
Kalshi NBA market map, and ``build_entry`` that turns one (team, split) into the dict ``filter_entries`` reads.

Input frame (one row per team-game): ``season, week (= team game number), game_id, team, bucket, margin`` where ``bucket``
is known before tip (``rest_bucket``) and ``margin`` is the team's point margin in that game. ``games=g`` reads each team's
first g games only, so a rank at game g never sees game g+1.
Applies when: deciding whether a team-split deviation (e.g. a team's margin on the second night of a back-to-back) is
extreme and stable enough to move a price, rather than the season-long rating already carrying it.
"""
from __future__ import annotations

from typing import Mapping, Optional

import numpy as np
import pandas as pd

from prediction_market_bot.nfl_engine import granularity_index as gi

SPEC = gi.SplitSpec(unit="team", by="bucket", metric="margin", higher_is_better=True, min_n=8)

# Which Kalshi NBA families a tag should move. Direction is for "team's margin / scoring up". Data, not code.
NBA_MARKET_TAGS: dict = {
    "b2b_margin": [("KXNBAGAME", "team moneyline", "up"), ("KXNBASPREAD", "team side", "up"),
                   ("KXNBATEAMTOTAL", "team total (scoring)", "up")],
    "rested_margin": [("KXNBAGAME", "team moneyline", "up"), ("KXNBASPREAD", "team side", "up")],
    "pace_up": [("KXNBATOTAL", "game total", "up"), ("KXNBATEAMTOTAL", "team total", "up")],
}


def rest_bucket(days_since_last: Optional[float]) -> Optional[str]:
    """Known before tip. None (season opener) is unclassifiable and dropped by the machinery (NaN bucket)."""
    if days_since_last is None or (isinstance(days_since_last, float) and np.isnan(days_since_last)):
        return None
    d = int(days_since_last)
    return "b2b" if d <= 1 else ("one_day" if d == 2 else "rested")


def team_game_frame(games: pd.DataFrame) -> pd.DataFrame:
    """Per-game frame (``game_id, season, date, home, away, home_pts, away_pts``) -> team-game rows with ``week`` = game
    number, ``bucket`` = rest bucket from the team's previous game date, ``margin`` = team points - opponent points."""
    h = pd.DataFrame({"game_id": games.game_id, "season": games.season, "date": pd.to_datetime(games.date), "team": games.home,
                      "margin": games.home_pts - games.away_pts})
    a = pd.DataFrame({"game_id": games.game_id, "season": games.season, "date": pd.to_datetime(games.date), "team": games.away,
                      "margin": games.away_pts - games.home_pts})
    long = pd.concat([h, a], ignore_index=True).sort_values(["season", "team", "date", "game_id"], kind="stable")
    long["week"] = long.groupby(["season", "team"]).cumcount() + 1
    gap = long.groupby(["season", "team"]).date.diff().dt.days
    long["bucket"] = [rest_bucket(x) for x in gap]
    return long.reset_index(drop=True)


def build_entry(frame: pd.DataFrame, team: str, bucket: str, season: int, games: int, tag: str,
                opp_allowed: Optional[Mapping] = None, league_mean: float = 0.0, k: Optional[float] = None) -> dict:
    """One index entry for (team, bucket) through ``games`` games: value, ranks, stability, optional cross delta vs the
    opponent's allowed margin in the same bucket. Keys match ``filter_entries``."""
    t = gi.game_table(frame, SPEC)
    r = gi.rank(frame, SPEC, team, bucket, season, games, table=t)
    if not r["ok"]:
        return {"ok": False, "tag": tag, "team": team, "bucket": bucket, "reason": r["reason"]}
    st = gi.stability(frame, SPEC, bucket, games, table=t)
    e = {**r, "tag": tag, "team": team, "stability": st, "markets": gi.market_map(tag) if tag in gi.MARKET_TAGS else
         [{"family": f, "line": l, "direction": d} for f, l, d in NBA_MARKET_TAGS.get(tag, [])]}
    if opp_allowed is not None:
        kk = k if k is not None else gi.estimate_k(gi.split(frame, SPEC, season=season, games=games, table=t)
                                                   .query("bucket == @bucket"))
        me = (r["n_plays"], r["value"] * r["n_plays"])
        res = gi.cross({bucket: me}, {bucket: opp_allowed[bucket]}, {bucket: league_mean}, {bucket: 1.0}, {bucket: kk},
                       overall=None)
        e["cross_delta"] = res.expected - league_mean
    return e


def filter_nba(entries, tail: float = 0.10, min_n: int = 8, require_trait: bool = True,
               mismatch_min: Optional[float] = None) -> list:
    """The NBA filtering mechanism (min_n in games, not plays). Extremes and mismatches pass; the median fails loudly."""
    return gi.filter_entries(entries, tail=tail, min_n=min_n, require_trait=require_trait, mismatch_min=mismatch_min)
