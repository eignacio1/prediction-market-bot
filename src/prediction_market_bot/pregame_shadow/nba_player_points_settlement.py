"""NBA player-points settlement join (EXP-039). READ-ONLY: box-score points in, y per market out.
y = 1 if recorded points >= n else 0. A player who did not play settles to a fair price (scalar) on Kalshi:
those rows get ``y=None, settlement='dnp_scalar'`` (excluded from scoring, counted). A player that cannot be found
in the game's box score at all gets ``settlement='unmatched_player'`` (also excluded, counted separately so a
name-matching failure is never silently scored as a DNP)."""
from __future__ import annotations

from typing import Any, Optional

from prediction_market_bot.pregame_shadow.nba_player_points_forecaster import (
    _initial, _norm_surname, parse_market_ticker)


def find_player(parsed: dict, game_rows: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    cands = [r for r in game_rows if r["team"] == parsed["team"]
             and _initial(r["name"]) == parsed["initial"] and _norm_surname(r["name"]) == parsed["surname"]]
    if len(cands) > 1:
        cands = [r for r in cands if r.get("jersey") == parsed["jersey"]]
    return cands[0] if len(cands) == 1 else None


def join_row(row: dict, game_rows: list[dict[str, Any]], clim: dict[str, float]) -> Optional[dict]:
    parsed = parse_market_ticker(row["market_ticker"])
    if parsed is None:
        return None
    out = dict(row)
    out.update(p_clim=clim[str(parsed["points_threshold"])],
               game_key=f"{parsed['game_date']}:{parsed['away']}@{parsed['home']}",
               player_key=f"{parsed['team']}{parsed['initial']}{parsed['surname']}{parsed['jersey']}")
    pl = find_player(parsed, game_rows)
    if pl is None:
        out.update(y=None, settlement="unmatched_player")
    elif pl["dnp"]:
        out.update(y=None, settlement="dnp_scalar", points=0.0)
    else:
        out.update(y=1.0 if pl["points"] >= parsed["points_threshold"] else 0.0, settlement="played",
                   points=pl["points"])
    return out
