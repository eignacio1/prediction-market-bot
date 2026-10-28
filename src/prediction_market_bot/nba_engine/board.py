"""Price the whole board from one GameSample: ML, spread ladder, total ladder, team totals, parlay pairs (W93.3)."""
from __future__ import annotations

from . import engine as E


def price_board(s: E.GameSample, margins, totals, team_totals) -> dict:
    """``margins``/``totals``/``team_totals`` are integer strike lists N (strike N-0.5). Every number is a sample frequency."""
    return {
        "moneyline_home": E.p_moneyline_home(s),
        "home_margin_ge": {n: E.p_margin_ge(s, n) for n in margins},
        "away_margin_ge": {n: E.p_away_margin_ge(s, n) for n in margins},
        "total_ge": {n: E.p_total_ge(s, n) for n in totals},
        "home_pts_ge": {n: E.p_team_total_ge(s, "home", n) for n in team_totals},
        "away_pts_ge": {n: E.p_team_total_ge(s, "away", n) for n in team_totals},
        "score_corr": E.score_corr(s),
    }
