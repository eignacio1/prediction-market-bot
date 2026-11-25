"""The one player-mean function for NBA props and combo legs (W128.2, D-07; EXP-047-C2's rule, PREREG_C2.md section 2).

``c2_means`` takes each rotation player's prior trailing means (``base``: stat -> list), his play probability (0 = listed Out at the
pre-tip cutoff, else 1) and prior three-point attempts, and returns the per-stat means every consumer prices from: the props split
(``NBAEnginePropsC2._mu``), the combo pricer's ``joint.JointRoster.mu`` and so the joint draw. Points use C1's full absorption;
rebounds / assists / threes use the frozen fitted fractions in ``lam``. Nobody Out: ``base`` is returned unchanged, same object.
Pure: no I/O, no clock. Changing the rule is a new pre-registration, not an edit here."""
from __future__ import annotations

from typing import Mapping, Optional, Sequence

from prediction_market_bot.nba_engine.usage_redistribution import absorb, absorb_threes, redistribute


def c2_means(base: Mapping[str, Sequence[float]], p_play: Sequence[float],
             attempts: Optional[Sequence[Optional[float]]], lam: Mapping[str, float]) -> Mapping[str, Sequence[float]]:
    if all(x == 1.0 for x in p_play):
        return base
    out = {"points": redistribute(base["points"], p_play),
           "rebounds": absorb(base["rebounds"], p_play, lam["rebounds"]),
           "assists": absorb(base["assists"], p_play, lam["assists"])}
    if attempts is not None and all(a is not None for a in attempts):
        out["threes"] = absorb_threes(attempts, base["threes"], p_play, lam["threes"])
    else:                                   # attempts missing for someone: absorb on makes (stated fallback, as W126.2)
        out["threes"] = absorb(base["threes"], p_play, lam["threes"])
    return out
