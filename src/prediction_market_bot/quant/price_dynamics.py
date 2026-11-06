"""Price dynamics of a quoted probability series: big moves, reversion vs follow, calm/jumpy regimes (W103.2, B-045).

A *series* is a time-sorted list of (t_seconds, price) for ONE market (price = yes_mid, in 0..1).
Everything here is descriptive and read-only: no order, no model, no pre-registration is touched.

Sign convention: ``reversion`` of an event = -sign(move) * (later price - price after the move). Positive = the
price gave back part of the move (a fade would have paid); negative = it kept going (a follow would have paid).
The family statistic is the RATIO OF SUMS  R_h = sum(reversion_h) / sum(|move|): the fraction of the big moves
that was given back at horizon h (R = 0.4 means 40% reverted; R = -0.2 means the price ran a further 20%).
"""
from __future__ import annotations

import bisect
import math
import random
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

Series = Sequence[Tuple[float, float]]


def moves(series: Series, max_gap_s: float) -> List[Tuple[float, float, float]]:
    """Consecutive price changes (t_end, delta, dt) kept only when the gap dt <= max_gap_s.
    Applies when snapshots are irregular: a change across a long outage is not one 'move'."""
    out = []
    for (t0, p0), (t1, p1) in zip(series, series[1:]):
        dt = t1 - t0
        if 0 < dt <= max_gap_s:
            out.append((t1, p1 - p0, dt))
    return out


def move_sigma(all_deltas: Sequence[float]) -> float:
    """Standard deviation of the family's own one-step moves (mean not removed: the question is size, not drift).
    Applies to a pooled family sample; do not compute it per market (a market's own sd shrinks after it is quiet)."""
    n = len(all_deltas)
    if n < 2:
        return float("nan")
    return math.sqrt(sum(d * d for d in all_deltas) / n)


def price_at(series: Series, t_target: float, tol_s: float) -> Optional[float]:
    """First observed price at or after t_target within tol_s; None if the series has no such snapshot.
    (No interpolation: an interpolated price is a price nobody could trade at.)"""
    ts = [t for t, _ in series]
    j = bisect.bisect_left(ts, t_target)
    if j < len(ts) and ts[j] - t_target <= tol_s:
        return series[j][1]
    return None


def settle_proxy(series: Series, lo: float = 0.03, hi: float = 0.97) -> Optional[float]:
    """Settlement proxy = the last quoted price, only if it is already within lo of 0 or within 1-hi of 1
    (the market has effectively resolved). Returns None otherwise. The archive carries no result field, so this
    is a proxy: it cannot see a market that was still undecided at its last snapshot (those are excluded, not guessed)."""
    if not series:
        return None
    p = series[-1][1]
    return p if (p <= lo or p >= hi) else None


def big_move_events(series: Series, k: float, sigma: float, max_gap_s: float, refractory_s: float,
                    horizons_s: Sequence[float], tol_s: float, settle: bool = True) -> List[Dict]:
    """Events where |one-step move| > k * sigma. For each: move size, the price after it, and the reversion at each
    horizon (seconds after the move) plus 'settle' (to the settlement proxy). An event is skipped if another accepted
    event on the same series happened within refractory_s before it (overlapping windows would count one episode twice).
    Applies when sigma was fixed from the family BEFORE looking at forward prices; with sigma estimated on these same
    rows the threshold is still not outcome-aware (it uses only one-step moves), but state k first."""
    sp = settle_proxy(series) if settle else None
    out: List[Dict] = []
    last_t = -math.inf
    for t_end, d, _dt in moves(series, max_gap_s):
        if not (abs(d) > k * sigma):
            continue
        if t_end - last_t < refractory_s:
            continue
        p_after = price_at(series, t_end, 0.0)
        if p_after is None:
            continue
        s = 1.0 if d > 0 else -1.0
        ev = {"t": t_end, "move": d, "abs_move": abs(d), "price": p_after, "rev": {}}
        for h in horizons_s:
            pf = price_at(series, t_end + h, tol_s)
            ev["rev"][h] = None if pf is None else -s * (pf - p_after)
        ev["rev"]["settle"] = None if sp is None else -s * (sp - p_after)
        out.append(ev)
        last_t = t_end
    return out


def reversion_fraction(events_by_game: Mapping[str, Sequence[Dict]], h, b: int = 2000, seed: int = 20261105,
                       alpha: float = 0.05) -> Dict:
    """Ratio-of-sums reversion fraction at horizon h with GAME-clustered bootstrap (whole games resampled).
    Returns R, 95% interval, two-sided bootstrap p (floor 1/(b+1)), n_events, n_games.
    Applies when games are independent and events within a game may be dependent; with fewer than ~15 games the
    percentile interval undercovers (reported via n_games, the caller should flag it). Games with no usable event at h drop out."""
    per = []
    for g, evs in events_by_game.items():
        num = sum(e["rev"][h] for e in evs if e["rev"].get(h) is not None)
        den = sum(e["abs_move"] for e in evs if e["rev"].get(h) is not None)
        n = sum(1 for e in evs if e["rev"].get(h) is not None)
        if n:
            per.append((num, den, n))
    if not per or sum(d for _, d, _ in per) <= 0:
        return {"R": float("nan"), "lo": float("nan"), "hi": float("nan"), "p_two_sided": float("nan"),
                "n_events": 0, "n_games": 0}
    R = sum(n_ for n_, _, _ in per) / sum(d for _, d, _ in per)
    rng = random.Random(seed)
    m = len(per)
    boots = []
    for _ in range(b):
        sn = sd = 0.0
        for _ in range(m):
            x = per[rng.randrange(m)]
            sn += x[0]; sd += x[1]
        boots.append(sn / sd if sd > 0 else 0.0)
    boots.sort()
    lo, hi = boots[int(alpha / 2 * b)], boots[int((1 - alpha / 2) * b) - 1]
    le0 = sum(1 for x in boots if x <= 0.0); ge0 = sum(1 for x in boots if x >= 0.0)
    p = min(1.0, 2 * (min(le0, ge0) + 1) / (b + 1))
    return {"R": R, "lo": lo, "hi": hi, "p_two_sided": p, "n_events": sum(n for _, _, n in per), "n_games": m}


def hourly_regimes(series: Series, k: float, sigma: float, max_gap_s: float, bucket_s: float = 3600.0) -> Dict[int, str]:
    """Two-state label per market-hour: 'jumpy' if the hour holds at least one move > k*sigma, else 'calm'.
    Only hours with at least 2 usable one-step moves are labelled (a one-snapshot hour says nothing).
    Applies to labelling the hour that just ended; use ``lagged`` labels to condition anything that happens after
    (an event's own hour is jumpy by construction)."""
    cnt: Dict[int, int] = {}
    jumps: Dict[int, int] = {}
    for t_end, d, _ in moves(series, max_gap_s):
        h = int(t_end // bucket_s)
        cnt[h] = cnt.get(h, 0) + 1
        if abs(d) > k * sigma:
            jumps[h] = jumps.get(h, 0) + 1
    return {h: ("jumpy" if jumps.get(h, 0) >= 1 else "calm") for h, c in cnt.items() if c >= 2}


def regime_transitions(labels: Mapping[int, str]) -> Dict[str, float]:
    """Stability of the regime: P(jumpy next hour | jumpy now) and P(jumpy next | calm now), over adjacent labelled hours.
    A label worth using has p_jj clearly above p_cj; equal values mean the label is noise."""
    c = {("jumpy", "jumpy"): 0, ("jumpy", "calm"): 0, ("calm", "jumpy"): 0, ("calm", "calm"): 0}
    for h, a in labels.items():
        b_ = labels.get(h + 1)
        if b_ is not None:
            c[(a, b_)] += 1
    nj = c[("jumpy", "jumpy")] + c[("jumpy", "calm")]
    nc = c[("calm", "jumpy")] + c[("calm", "calm")]
    return {"p_jumpy_given_jumpy": c[("jumpy", "jumpy")] / nj if nj else float("nan"),
            "p_jumpy_given_calm": c[("calm", "jumpy")] / nc if nc else float("nan"),
            "n_after_jumpy": nj, "n_after_calm": nc}


def lagged_regime(labels: Mapping[int, str], t: float, bucket_s: float = 3600.0) -> Optional[str]:
    """Label of the hour BEFORE the hour containing t (None if unlabelled): known at time t, so no look-ahead."""
    return labels.get(int(t // bucket_s) - 1)
