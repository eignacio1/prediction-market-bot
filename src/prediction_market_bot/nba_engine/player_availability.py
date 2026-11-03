"""NBA engine player layer, availability step (W97.1 Part C, B-009): who is likely to play, known before tip.

W96.1 found that normalising a player's share over the teammates who PLAYED is post-game information. Here the share's
denominator is the expected points weight of the pre-tip candidate set, each teammate weighted by the probability the
injury report implies he plays. New module; v1/v2/v3 and player_layer are untouched. Research use only.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Iterable, Mapping, Sequence

UNLISTED = "Unlisted"          # candidate with no entry in the report
NO_REPORT = "NoReport"         # no report existed at the cutoff for that game day
MAX_SHARE = 0.95


class LeakError(ValueError):
    """An input carries a timestamp later than the pre-tip cutoff."""


def fit_play_rates(statuses: Sequence[str], played: Sequence[int], prior_n: float = 5.0) -> Dict[str, float]:
    """P(plays | status), each shrunk toward the pooled rate with ``prior_n`` pseudo-games.

    Fit on training seasons only; ``played`` is the post-game label, which is legitimate as a training target."""
    if len(statuses) != len(played):
        raise ValueError("statuses and played differ in length")
    pooled = (sum(played) + 0.5) / (len(played) + 1.0)
    n: Dict[str, int] = {}
    k: Dict[str, int] = {}
    for s, y in zip(statuses, played):
        n[s] = n.get(s, 0) + 1
        k[s] = k.get(s, 0) + int(y)
    rates = {s: (k[s] + prior_n * pooled) / (n[s] + prior_n) for s in n}
    rates.setdefault(UNLISTED, pooled)
    rates.setdefault(NO_REPORT, pooled)
    return rates


def conditional_shares(mu_j: float, others_mu: Sequence[float], others_p: Sequence[float], rest_share: float) -> float:
    """Expected share of team points for player j given he plays: (1-rest) * mu_j / (mu_j + sum_i p_i mu_i), capped.

    Applies when the candidate set and p_i are known before tip; does not apply once the game's actual roster is used."""
    if len(others_mu) != len(others_p):
        raise ValueError("others_mu and others_p differ in length")
    mu_j = max(float(mu_j), 1e-6)
    denom = mu_j + sum(max(float(m), 0.0) * min(max(float(p), 0.0), 1.0) for m, p in zip(others_mu, others_p))
    return min((1.0 - rest_share) * mu_j / denom, MAX_SHARE)


def assert_pretip(stamps: Iterable[datetime], tip: datetime, lead: timedelta) -> None:
    """Raise LeakError if any input timestamp is later than ``tip - lead``."""
    cutoff = tip - lead
    for s in stamps:
        if s is not None and s > cutoff:
            raise LeakError("input stamped {} is after the pre-tip cutoff {}".format(s.isoformat(), cutoff.isoformat()))
