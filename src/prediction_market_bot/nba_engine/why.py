"""W99.3 (GG-1630): the top three reasons behind an NBA engine price -- logging only.

The engines (v1 Monte Carlo, v2 closed form, v3 = v2 + injury/rotation factors) are not linear, so a per-feature share is
not exact. The reason is a COUNTERFACTUAL: re-price the same ticker with ONE input replaced by its league average (v3
factors: by their training centre) and report how far the price moved toward YES. ``pts`` is in percentage points of
probability. Nothing here changes a price, threshold, order or stake; any failure returns None and the caller logs a
``reasons_note`` instead (the row is never lost).

Known-answer property (tested): if the price is  p = f(x1..xn)  and replacing xi by its baseline changes p by d, the
reason for xi is exactly d * 100 points toward YES.
"""
from __future__ import annotations

from typing import Callable, Iterable, Optional

from prediction_market_bot.pregame_shadow.reasons import TOP_K

CF_NOTE = "engine reasons: not computed (%s)"

_TEAM_STAT = {"pace": "pace (possessions per game)", "ortg": "offense (points per 100 possessions)",
              "drtg": "defense (points allowed per 100 possessions)"}
STATS = ("pace", "ortg", "drtg")


def league_means(tg, season: int) -> dict:
    """Prior-season league average of each team stat (the baseline a rating shrinks toward)."""
    prev = tg[tg["season"] == season - 1]
    return {c: float(prev[c].mean()) for c in STATS}


def team_label(side: str, stat: str) -> str:
    return "%s team %s vs league average" % (side, _TEAM_STAT[stat])


def factor_label(name: str) -> str:
    """An injury/rotation factor name in words, with the baseline made plain."""
    return "%s (vs its normal level)" % name.replace("_", " ")


def top_reasons(p_base: float, counterfactuals: Iterable, k: int = TOP_K) -> Optional[list]:
    """counterfactuals: (label, value, p_with_input_at_baseline). Top-k by |move| toward YES, or None if empty/invalid."""
    out = []
    for label, value, p_cf in counterfactuals:
        if p_cf is None:
            continue
        d = (float(p_base) - float(p_cf)) * 100.0
        out.append({"factor": label, "value": round(float(value), 3), "pts": round(d, 3), "toward_yes": round(d, 3)})
    if not out:
        return None
    out.sort(key=lambda r: -abs(r["toward_yes"]))
    return out[:k]


def attach(row: dict, build: Callable[[], Optional[list]]) -> dict:
    """Add ``reasons`` to a row, or ``reasons`` None + ``reasons_note`` when the computation fails. Never raises."""
    try:
        got = build()
    except Exception as e:  # noqa: BLE001 - logging only; a reasons failure must never cost the decision row
        got, why = None, "%s: %s" % (type(e).__name__, e)
    else:
        why = "no counterfactual available"
    if got:
        row["reasons"] = got
    else:
        row["reasons"], row["reasons_note"] = None, CF_NOTE % why
    return row
