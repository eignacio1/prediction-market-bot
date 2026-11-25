"""W126.3 Part B stage 4: one MLB game simulation whose draws price the whole board (ADR-0073).

Applies: plate-appearance by plate-appearance play of a game for N draws at once. Each draw cycles the nine-man lineups,
samples every PA from the `pa_model` probabilities (opposing starter until his sampled batters-faced limit, then the
relief corps), moves runners with the fixed transition table below, ends a half-inning at three outs, skips the bottom of
the 9th when the home side leads, stops a bottom-9th-or-later half-inning on a walk-off, starts extra innings with the
automatic runner on second, and breaks a tie after 15 innings with a coin flip worth one run. Team runs and every batter's
hits come from the SAME draw index, so moneyline, run line, total, team totals and batter props share one dependence
structure that is an output, never an input (`quant/sgp.py`).
Does not apply: pinch hitters / defensive changes, steals, wild pitches, errors beyond a plain out, batter fatigue, park.
Runner advancement constants are fixed priors from the usual league rates, set before the held-out look.
"""
from __future__ import annotations

from typing import Dict

import numpy as np

K_, BB_, S_, D_, T_, HR_, OUT_ = range(7)
P_SECOND_SCORES_ON_SINGLE = 0.60
P_FIRST_SCORES_ON_DOUBLE = 0.40
P_THIRD_SCORES_ON_OUT = 0.30     # sac fly / ground-out RBI with fewer than two outs
P_DOUBLE_PLAY = 0.12             # in-play out with a runner on first and fewer than two outs
BF_SD = 4.5
BF_MIN, BF_MAX = 9, 32
MAX_INNINGS = 15


def simulate(P: np.ndarray, bf_mean: np.ndarray, n: int, seed: int = 0) -> Dict[str, np.ndarray]:
    """P[bat_side, ptype, slot, class] (bat_side 0 = away bats, ptype 0 = starter / 1 = relief); bf_mean[bat_side] is the
    opposing starter's expected batters faced. Returns arrays over n draws: home_runs, away_runs, hits (n, 2, 9), innings."""
    rng = np.random.default_rng(seed)
    cum = np.cumsum(P, axis=-1)
    cum[..., -1] = 1.0
    bf_lim = np.clip(np.rint(rng.normal(bf_mean[None, :], BF_SD, size=(n, 2))), BF_MIN, BF_MAX).astype(np.int64)
    ptr = np.zeros((n, 2), np.int64)         # next batter slot, per batting side
    pas = np.zeros((n, 2), np.int64)         # PA so far, per batting side (limits the opposing starter)
    runs = np.zeros((n, 2), np.int64)
    hits = np.zeros((n, 2, 9), np.int64)
    done = np.zeros(n, bool)
    inn_played = np.zeros(n, np.int64)
    away_runs_9 = np.zeros(n, np.int64)
    ar = np.arange(n)
    for inn in range(1, MAX_INNINGS + 1):
        for s in (0, 1):                               # 0 = away bats (top), 1 = home bats (bottom)
            live = ~done
            if s == 1 and inn >= 9:                    # bottom of 9th+: home already ahead -> game over after the top
                end = live & (runs[:, 1] > runs[:, 0])
                done |= end
                live = ~done
            if not live.any():
                continue
            inn_played[live] = inn
            outs = np.zeros(n, np.int64)
            outs[~live] = 3
            b1 = np.zeros(n, bool)
            b2 = np.full(n, inn >= 10) & live          # automatic runner on second in extras
            b3 = np.zeros(n, bool)
            while True:
                act = outs < 3
                if not act.any():
                    break
                slot = ptr[:, s]
                ptype = (pas[:, s] >= bf_lim[:, s]).astype(np.int64)
                u = rng.random(n)
                cls = (u[:, None] > cum[s][ptype, slot]).sum(1)
                cls = np.minimum(cls, OUT_)
                m = act
                add = np.zeros(n, np.int64)
                n1, n2, n3 = b1.copy(), b2.copy(), b3.copy()
                dp_u, adv_u, adv2_u = rng.random(n), rng.random(n), rng.random(n)
                # strikeout
                k = m & (cls == K_)
                outs[k] += 1
                # in-play out
                o = m & (cls == OUT_)
                dp = o & b1 & (outs < 2) & (dp_u < P_DOUBLE_PLAY)
                sac = o & ~dp & b3 & (outs < 2) & (adv_u < P_THIRD_SCORES_ON_OUT)
                outs[o] += 1
                outs[dp] += 1
                add[sac] += 1
                n3[sac] = False
                n1[dp] = False
                # walk
                w = m & (cls == BB_)
                add[w & b1 & b2 & b3] += 1
                n3[w] = (b3 | (b1 & b2))[w]
                n2[w] = (b2 | b1)[w]
                n1[w] = True
                # single
                s1 = m & (cls == S_)
                sc2 = s1 & b2 & (adv2_u < P_SECOND_SCORES_ON_SINGLE)
                add[s1 & b3] += 1
                add[sc2] += 1
                n3[s1] = (b2 & ~sc2)[s1]
                n2[s1] = b1[s1]
                n1[s1] = True
                # double
                d2 = m & (cls == D_)
                sc1 = d2 & b1 & (adv2_u < P_FIRST_SCORES_ON_DOUBLE)
                add[d2] += (b3.astype(np.int64) + b2.astype(np.int64))[d2]
                add[sc1] += 1
                n3[d2] = (b1 & ~sc1)[d2]
                n2[d2] = True
                n1[d2] = False
                # triple
                t3 = m & (cls == T_)
                add[t3] += (b1.astype(np.int64) + b2.astype(np.int64) + b3.astype(np.int64))[t3]
                n3[t3], n2[t3], n1[t3] = True, False, False
                # home run
                h = m & (cls == HR_)
                add[h] += (b1.astype(np.int64) + b2.astype(np.int64) + b3.astype(np.int64))[h] + 1
                n1[h] = n2[h] = n3[h] = False
                hit = m & (cls >= S_) & (cls <= HR_)
                hits[ar[hit], s, slot[hit]] += 1
                runs[:, s] += add
                b1, b2, b3 = np.where(m, n1, b1), np.where(m, n2, b2), np.where(m, n3, b3)
                ptr[m, s] = (slot[m] + 1) % 9
                pas[m, s] += 1
                if s == 1 and inn >= 9:                # walk-off: the half-inning ends the moment the home side leads
                    outs[m & (runs[:, 1] > runs[:, 0])] = 3
        if inn == 9:
            away_runs_9 = runs[:, 0].copy()      # the away side always bats a full 9th: exact regulation runs
        if inn >= 9:
            tied = (~done) & (runs[:, 0] == runs[:, 1])
            done |= (~done) & ~tied
    tie = runs[:, 0] == runs[:, 1]                     # still level after 15 innings: coin flip worth one run
    flip = rng.random(n) < 0.5
    runs[tie & flip, 1] += 1
    runs[tie & ~flip, 0] += 1
    return {"away_runs": runs[:, 0], "home_runs": runs[:, 1], "hits": hits, "innings": inn_played, "tie_break": tie, "away_runs_9": away_runs_9}
