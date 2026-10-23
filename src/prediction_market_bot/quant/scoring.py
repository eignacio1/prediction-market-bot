"""Scoring rules. Sign convention for every paired difference: reference minus model, so POSITIVE = model better."""
from __future__ import annotations

import math
from typing import Sequence

LOG_EPS = 1e-6


def brier(p: float, y: float) -> float:
    """Squared error of one probability forecast. Applies to binary outcomes (y in {0, 0.5, 1}; 0.5 = push)."""
    return (p - y) ** 2


def brier_mean(ps: Sequence[float], ys: Sequence[float]) -> float:
    """Mean Brier. Applies to any n >= 1 of independent-enough rows; it is a point estimate, not an interval."""
    return sum(brier(p, y) for p, y in zip(ps, ys)) / len(ps)


def log_loss(p: float, y: float) -> float:
    """Log loss with p clipped to [1e-6, 1-1e-6]. Applies when forecasts are never exactly 0/1; the clip is a convention."""
    p = min(max(p, LOG_EPS), 1 - LOG_EPS)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def log_loss_mean(ps: Sequence[float], ys: Sequence[float]) -> float:
    return sum(log_loss(p, y) for p, y in zip(ps, ys)) / len(ps)


def brier_diff(p_ref: Sequence[float], p_model: Sequence[float], ys: Sequence[float]) -> list[float]:
    """Per-row paired difference Brier(ref) - Brier(model); positive = model beats the reference (e.g. the market).
    Applies only when both forecasts are for the same event at a comparable moment; timing mismatch is a caveat, not a fix."""
    return [brier(r, y) - brier(m, y) for r, m, y in zip(p_ref, p_model, ys)]
