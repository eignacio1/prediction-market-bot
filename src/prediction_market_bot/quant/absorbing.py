"""W89.4: absorbing discrete-time Markov chain algebra (fundamental matrix, absorption, expected reward, exponential tilt).

WHEN IT APPLIES: a process that moves through a finite set of transient states and ends in one of a few absorbing
outcomes (a football drive: play-state -> touchdown / field goal / punt / turnover ...), where each transient row of
transition probabilities is estimated from many observed visits and the next state depends on the current state only
(first-order Markov). It does NOT apply when the next state depends on history the state omits (score, clock,
fatigue), or when rows are estimated from a handful of visits (use the caller's back-off first).

Q is the transient->transient block (S x S), R the transient->absorbing block (S x A); every row of [Q | R] sums to 1.
"""
from __future__ import annotations

import numpy as np


def fundamental(Q: np.ndarray) -> np.ndarray:
    """N = (I - Q)^-1; N[i, j] = expected visits to transient j starting from transient i."""
    return np.linalg.inv(np.eye(Q.shape[0]) - Q)


def absorption_probs(Q: np.ndarray, R: np.ndarray) -> np.ndarray:
    """B = N R; B[i, a] = P(absorbed in a | start i). Rows sum to 1 when the chain is absorbing."""
    return np.linalg.solve(np.eye(Q.shape[0]) - Q, R)


def expected_steps(Q: np.ndarray) -> np.ndarray:
    """Expected number of transitions before absorption from each transient state (hitting time of the absorbing set)."""
    return np.linalg.solve(np.eye(Q.shape[0]) - Q, np.ones(Q.shape[0]))


def expected_reward(Q: np.ndarray, R: np.ndarray, absorbing_reward: np.ndarray) -> np.ndarray:
    """Expected reward collected on absorption, from each transient state."""
    return absorption_probs(Q, R) @ np.asarray(absorbing_reward, float)


def exp_tilt(Q: np.ndarray, R: np.ndarray, g_trans: np.ndarray, g_abs: np.ndarray, theta: float):
    """Exponentially tilt every row of [Q | R] by exp(theta * g(destination)) and renormalise.

    g_trans[j] / g_abs[a] score each destination (e.g. the state's expected reward). theta=0 returns the input;
    theta>0 shifts mass toward higher-scored destinations. Rows keep their support (zeros stay zero)."""
    W = np.hstack([Q * np.exp(theta * np.asarray(g_trans, float))[None, :],
                   R * np.exp(theta * np.asarray(g_abs, float))[None, :]])
    W = W / W.sum(axis=1, keepdims=True)
    S = Q.shape[0]
    return W[:, :S], W[:, S:]
