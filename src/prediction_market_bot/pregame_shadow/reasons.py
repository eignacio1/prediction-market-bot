"""W98.3 (GG-1580): the top three reasons behind a pregame decision row -- logging only.

For the ridge-linear arms (NBA, NFL, MLB game markets) a forecast is  mu = intercept + sum(coef_i * z_i),  so each
feature's share is exact: coef_i * z_i, in points of the quantity the market is about (margin or total). This module
READS the frozen artifact and the feature row; it changes no probability, threshold, order or stake and never raises
into the caller (failure -> None, and the row says the arm could not give reasons).

Shape of one reason:  {"factor": plain words, "value": the feature's raw value, "pts": signed contribution to the
quantity the market is about (home margin / total), "toward_yes": signed contribution toward the YES side, in points}
"""
from __future__ import annotations

from typing import Optional

TOP_K = 3
NO_REASONS_NOTE = "this arm's model does not expose per-factor contributions"

_SIDE = {"h": "home", "a": "away"}
_STAT = {"pf10": "points scored per game, last 10", "pa10": "points allowed per game, last 10",
         "pf30": "points scored per game, last 30", "pa30": "points allowed per game, last 30",
         "rest": "days of rest", "b2b": "playing on back-to-back nights (1 = yes)",
         "3in4": "third game in four nights (1 = yes)"}


_WORDS = {
    "off_epa_h": "home offense efficiency (EPA per play)", "def_epa_h": "home defense efficiency (EPA per play allowed)",
    "off_epa_a": "away offense efficiency (EPA per play)", "def_epa_a": "away defense efficiency (EPA per play allowed)",
    "pf_h": "home points scored per game, recent", "pa_h": "home points allowed per game, recent",
    "pf_a": "away points scored per game, recent", "pa_a": "away points allowed per game, recent",
    "rest_diff": "rest-day edge (home minus away)", "rest_short_h": "home team on a short week (1 = yes)",
    "rest_short_a": "away team on a short week (1 = yes)",
    "home_rs": "home runs scored per game", "home_ra": "home runs allowed per game",
    "away_rs": "away runs scored per game", "away_ra": "away runs allowed per game",
    "home_wp": "home win percentage", "away_wp": "away win percentage",
    "home_sp_ra": "home starting pitcher runs allowed", "away_sp_ra": "away starting pitcher runs allowed",
    "league_rpg": "league scoring level (runs per game)",
}


def plain_name(feature: str) -> str:
    """'h_pf10' -> 'home team points scored per game, last 10'; unknown names fall back to the raw name in words."""
    if feature in _WORDS:
        return _WORDS[feature]
    pre, _, rest = feature.partition("_")
    if pre in _SIDE and rest in _STAT:
        return f"{_SIDE[pre]} team {_STAT[rest]}"
    return feature.replace("_", " ")


def _contribs(m: dict, names: list, feats: dict, scale: float = 1.0) -> list:
    return [scale * c * (feats[n] - mu) / sd for n, mu, sd, c in zip(names, m["mean"], m["std"], m["coef"])]


def ridge_reasons(artifact: dict, names: list, feats: dict, market_type: str, *,
                  subject_is_home: Optional[bool] = None, k: int = TOP_K) -> Optional[list]:
    """Top-k contributions by absolute size toward the YES side, or None if anything is missing."""
    try:
        a = float(artifact["platt"]["a"])
        cm = _contribs(artifact["margin"], names, feats, a)
        ct = _contribs(artifact["total"], names, feats)
        mt = market_type.split("_", 1)[1] if "_" in market_type else market_type
        if mt in ("MONEYLINE", "SPREAD", "RUN_LINE"):
            sgn = 1.0 if subject_is_home else -1.0
            pts, toward = cm, [sgn * x for x in cm]
        elif mt == "GAME_TOTAL":
            pts, toward = ct, list(ct)
        elif mt == "TEAM_TOTAL":
            sgn = 1.0 if subject_is_home else -1.0
            pts = [(t + sgn * m) / 2.0 for t, m in zip(ct, cm)]
            toward = list(pts)
        else:
            return None
        order = sorted(range(len(names)), key=lambda i: -abs(toward[i]))[:k]
        return [{"factor": plain_name(names[i]), "value": round(float(feats[names[i]]), 3),
                 "pts": round(pts[i], 3), "toward_yes": round(toward[i], 3)} for i in order]
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None


def reason_text(r: dict, side: str) -> str:
    """One plain sentence for a stored reason, from the point of view of the picked side ('yes' or 'no')."""
    helps = (r["toward_yes"] > 0) == (side == "yes")
    return "%s = %s: %s this pick (%.1f pts)" % (r["factor"], r["value"], "supports" if helps else "works against",
                                                  abs(r["toward_yes"]))
