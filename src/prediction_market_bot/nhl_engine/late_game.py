"""W98.1 Part B: late-game (last 5 minutes of regulation) scoring table from the event store, with empty-net goals.

Per game: score margin at 5:00 and 2:00 left in the 3rd, goals by side in (5:00,2:00] and (2:00,0:00], and how many of
those were scored into an empty net (the conceding side's goalie flag is 0). Regulation only (period <= 3).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

W1, W2 = 300, 120   # seconds left: window 1 = (300,120], window 2 = (120,0]


def late_table(ev: pd.DataFrame) -> pd.DataFrame:
    g = ev[(ev["type"] == "goal") & (ev["period"] <= 3)].copy()
    g["home_goal"] = g["owner_is_home"].astype(bool)
    # the goalie flag on the event row is the state when the goal was scored; scoring side's opponent has goalie==0 => empty net
    g["en"] = np.where(g["home_goal"], g["away_goalie"] == 0, g["home_goalie"] == 0)
    g["abs_left"] = (3 - g["period"]) * 1200 + g["time_remaining_s"]   # seconds left in regulation
    rows = []
    for gid, d in g.groupby("game_id"):
        hl = d[d.home_goal]; al = d[~d.home_goal]
        def n(df, lo, hi, en=None):
            m = (df.abs_left <= hi) & (df.abs_left > lo)
            if en is not None: m &= df.en == en
            return int(m.sum())
        h5 = int((hl.abs_left > W1).sum()); a5 = int((al.abs_left > W1).sum())
        h2 = h5 + n(hl, W2, W1); a2 = a5 + n(al, W2, W1)
        rows.append(dict(game_id=gid, h_at5=h5, a_at5=a5, h_at2=h2, a_at2=a2,
                         h_w1=n(hl, W2, W1), a_w1=n(al, W2, W1), h_w2=n(hl, -1, W2), a_w2=n(al, -1, W2),
                         h_w2_en=n(hl, -1, W2, True), a_w2_en=n(al, -1, W2, True),
                         h_w1_en=n(hl, W2, W1, True), a_w1_en=n(al, W2, W1, True),
                         h_early=int((hl.abs_left > W1).sum()), a_early=int((al.abs_left > W1).sum()),
                         h_all=len(hl), a_all=len(al), en_all=int(d.en.sum())))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------------------------------------
# v2 simulation: 55:00 of base scoring, then two late windows whose goal rates depend on the score state (empty-net regime).
# Applies when: regulation scoring needs the end-of-game state (leader/trailer pull-the-goalie effects); it does not apply to
# playoff OT. Known answer: with all state multipliers == 1 and no late window mass moved, totals equal the base Poisson.
# ---------------------------------------------------------------------------------------------------------------------
WIN_MIN = (3.0, 2.0)   # minutes in window 1 (5:00->2:00) and window 2 (2:00->0:00)


def _state(d: np.ndarray) -> np.ndarray:
    """margin of the side (own - other) -> 0: down 2+, 1: down 1, 2: tied, 3: up 1, 4: up 2+."""
    return np.clip(d, -2, 2).astype(int) + 2


def fit_late(tab: pd.DataFrame, lam_h: np.ndarray, lam_a: np.ndarray) -> np.ndarray:
    """Goals per (rate-weighted) minute for each window x state, from training games only. Returns array (2, 5).
    Exposure for a side is minutes * lam_side / lam_bar, so team strength is held out of the state effect."""
    lam_bar = float(np.mean(np.r_[lam_h, lam_a]))
    num = np.zeros((2, 5)); den = np.zeros((2, 5))
    for w, (dh, gh, ga) in enumerate(((tab.h_at5 - tab.a_at5, tab.h_w1, tab.a_w1), (tab.h_at2 - tab.a_at2, tab.h_w2, tab.a_w2))):
        dh = dh.to_numpy()
        for d, g, lam in ((dh, gh.to_numpy(), lam_h), (-dh, ga.to_numpy(), lam_a)):
            s = _state(d)
            np.add.at(num[w], s, g)
            np.add.at(den[w], s, WIN_MIN[w] * lam / lam_bar)
    return num / np.maximum(den, 1e-9)


def simulate_v2(lam_h: float, lam_a: float, base: np.ndarray, lam_bar: float, k: float, p_home_ot: float, n: int, seed: int,
                tie_odds: float = 1.0, early_scale: float = 1.0):
    from prediction_market_bot.nhl_engine.goals import GoalSample
    rng = np.random.default_rng(seed)
    g = rng.gamma(k, 1.0 / k, size=n) if np.isfinite(k) else np.ones(n)
    h = rng.poisson(lam_h * g * early_scale * 55.0 / 60.0); a = rng.poisson(lam_a * g * early_scale * 55.0 / 60.0)
    # the 5:00-minute stretch before 55:00 is folded into the first 55 minutes' rate; late windows start at 5:00 left
    # so the first stage covers 0..55 and the late stage 55..60 (window 1 = 55..58, window 2 = 58..60).
    for w in (0, 1):
        sh = _state(h - a); sa = _state(a - h)
        h = h + rng.poisson(base[w][sh] * WIN_MIN[w] * lam_h / lam_bar)
        a = a + rng.poisson(base[w][sa] * WIN_MIN[w] * lam_a / lam_bar)
    if tie_odds != 1.0:
        wgt = np.where(h == a, tie_odds, 1.0)
        idx = rng.choice(n, size=n, p=wgt / wgt.sum()); h, a = h[idx], a[idx]
    tie = h == a
    hw = rng.random(n) < p_home_ot
    return GoalSample(h + (tie & hw), a + (tie & ~hw), h, a)


def early_scale(tab: pd.DataFrame) -> float:
    """Scale on the first-55-minute rate that keeps expected regulation goals equal to the base model's (late windows carry
    their measured share instead of the flat 5/60). From training games only."""
    tot = float((tab.h_all + tab.a_all).mean()); late = float((tab.h_w1 + tab.a_w1 + tab.h_w2 + tab.a_w2).mean())
    return (tot - late) / (tot * 55.0 / 60.0)
