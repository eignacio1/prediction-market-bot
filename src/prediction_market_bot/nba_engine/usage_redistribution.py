"""The one usage-redistribution rule (W125.4, EXP-047-C1; NBA-10 consumers: game lines and player props).

``missing_usage``  share * (1 - p_play): the vacated usage the game-line path (factors_applied.usage_missing) sums per team.
``redistribute``   active players absorb the vacated weight in proportion to their own: w_i -> w_i * p_i * f with
                   f = sum(w) / sum(w * p) = 1 / (1 - V). Parameter-free; the team total is preserved.
With nobody missing (every p == 1) the input is returned unchanged, bit for bit."""
from __future__ import annotations

from typing import Sequence

import numpy as np


def missing_usage(share, p_play):
    """Vacated usage share = share * (1 - p_play). Works on floats, arrays and pandas Series."""
    return share * (1.0 - p_play)


def absorption_factor(weights: Sequence[float], p_play: Sequence[float]) -> float:
    w, p = np.asarray(weights, float), np.asarray(p_play, float)
    kept = float((w * p).sum())
    return float(w.sum()) / kept if kept > 0.0 else 1.0


def redistribute(weights: Sequence[float], p_play: Sequence[float]) -> list[float]:
    """Weights after the missing players' share is absorbed by the others (same length; Out players -> 0)."""
    w = [float(x) for x in weights]
    p = [float(x) for x in p_play]
    if all(x == 1.0 for x in p) or sum(a * b for a, b in zip(w, p)) <= 0.0:
        return w
    f = absorption_factor(w, p)
    return [a * b * f for a, b in zip(w, p)]
