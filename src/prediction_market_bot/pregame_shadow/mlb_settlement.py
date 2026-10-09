"""MLB settlement join (EXP-037 / GG-472). READ-ONLY: final scores in, y per market out. No scoring.

Kalshi MLB grammar (see mlb_forecaster.parse_market_ticker): strike = N - 0.5, so a push is impossible and
MLB has no ties. YES means: moneyline -> subject wins; run line -> subject wins by more than strike;
game total -> combined runs > strike; team total -> subject's runs > strike.
Games are matched on (home, away, ET game date; nearest start breaks doubleheader ties) via mlb_forecaster.match_game.
A game is final only when status == 'Final' and both scores are present; anything else stays unsettled.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.mlb_game_pregame_features import canon
from prediction_market_bot.pregame_shadow.mlb_forecaster import match_game, parse_market_ticker


def final_games(games: pd.DataFrame) -> pd.DataFrame:
    g = games[(games.status == "Final") & games.home_score.notna() & games.away_score.notna()
              & games.start_utc.notna()].copy()
    g["_h"] = g.home.map(canon)
    g["_a"] = g.away.map(canon)
    g["_t"] = pd.to_datetime(g.start_utc, utc=True)
    return g


def find_final(finals: pd.DataFrame, parsed: dict) -> Optional[tuple[float, float]]:
    """(home_score, away_score) of the single final game matching the ticker, else None."""
    r, _ = match_game(finals, parsed["home"], parsed["away"], parsed["start_utc"])
    if r is None:
        return None
    return float(r.home_score), float(r.away_score)


def join_row(row: dict, home_score: float, away_score: float) -> Optional[dict]:
    parsed = parse_market_ticker(row["market_ticker"])
    if parsed is None:
        return None
    mt, strike, subj = parsed["market_type"], parsed["strike"], parsed["subject"]
    own, opp = (home_score, away_score) if subj == parsed["home"] else (away_score, home_score)
    if mt == "MLB_MONEYLINE":
        if home_score == away_score:
            return None
        y = 1.0 if own > opp else 0.0
    elif mt == "MLB_RUN_LINE":
        y = 1.0 if own - opp > strike else 0.0
    elif mt == "MLB_GAME_TOTAL":
        y = 1.0 if home_score + away_score > strike else 0.0
    elif mt == "MLB_TEAM_TOTAL":
        y = 1.0 if own > strike else 0.0
    else:
        return None
    out = dict(row)
    out.update(y=y, game_key=f"{parsed['start_utc'].date().isoformat()}:{parsed['away']}@{parsed['home']}",
               final_home=home_score, final_away=away_score)
    return out
