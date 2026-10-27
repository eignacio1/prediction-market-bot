import numpy as np

from prediction_market_bot.quant import absorbing as A


def _walk(n, p):
    """Gambler's ruin on 0..n: transient 1..n-1, absorbing {0 (ruin), n (win)}."""
    S = n - 1
    Q, R = np.zeros((S, S)), np.zeros((S, 2))
    for i in range(1, n):
        for step, pr in ((1, p), (-1, 1 - p)):
            j = i + step
            if j == 0:
                R[i - 1, 0] += pr
            elif j == n:
                R[i - 1, 1] += pr
            else:
                Q[i - 1, j - 1] += pr
    return Q, R


def test_fair_gamblers_ruin_known_answers():
    n = 10
    Q, R = _walk(n, 0.5)
    B = A.absorption_probs(Q, R)
    assert np.allclose(B.sum(1), 1.0)
    assert np.allclose(B[:, 1], np.arange(1, n) / n)              # P(win from i) = i/n
    assert np.allclose(A.expected_steps(Q), np.arange(1, n) * (n - np.arange(1, n)))  # i(n-i)


def test_biased_gamblers_ruin_and_reward():
    n, p = 8, 0.6
    Q, R = _walk(n, p)
    r = (1 - p) / p
    want = (1 - r ** np.arange(1, n)) / (1 - r ** n)
    assert np.allclose(A.absorption_probs(Q, R)[:, 1], want)
    assert np.allclose(A.expected_reward(Q, R, [0.0, 5.0]), 5.0 * want)


def test_tilt_identity_monotone_and_row_sums():
    Q, R = _walk(10, 0.5)
    g_t, g_a = np.arange(1, 10, dtype=float), np.array([0.0, 10.0])
    Q0, R0 = A.exp_tilt(Q, R, g_t, g_a, 0.0)
    assert np.allclose(Q0, Q) and np.allclose(R0, R)
    wins = [A.absorption_probs(*A.exp_tilt(Q, R, g_t, g_a, th))[4, 1] for th in (-0.3, 0.0, 0.3)]
    assert wins[0] < wins[1] < wins[2]
    Qt, Rt = A.exp_tilt(Q, R, g_t, g_a, 0.3)
    assert np.allclose(Qt.sum(1) + Rt.sum(1), 1.0)
