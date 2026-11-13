"""W114.4: covariance gap (realised - engine, against realised marginals) by pair class with game-clustered bootstrap CI, 113.3 vs 114.4.
Usage: python3 gap_ci.py <rows_a.csv.gz> <rows_b.csv.gz>"""
import sys
import numpy as np, pandas as pd

CLS = ["PTS x PTS (teammates)", "PTS x AST (teammates)", "REB x REB (teammates)", "WIN x REB",
       "PTS x 3PM (same player)", "PTS x REB (same player)", "PTS x AST (same player)"]


def sums(d):
    g = d.assign(yab=d.y_a * d.y_b, pab=d.p_a * d.p_b).groupby("game")[["yab", "y_a", "y_b", "p_joint", "pab"]].sum()
    return g.values, d.groupby("game").size().values


def gap_from(t, n):
    return t[0] / n - (t[1] / n) * (t[2] / n) - (t[3] / n - t[4] / n)


def run(path, rng):
    df = pd.read_csv(path); out = {}
    for c in CLS:
        s, cnt = sums(df[df.type == c]); n = cnt.sum(); g = len(cnt)
        pt = gap_from(s.sum(0), n); bs = []
        for _ in range(1000):
            i = rng.integers(0, g, g); bs.append(gap_from(s[i].sum(0), cnt[i].sum()))
        out[c] = (n, pt, *np.percentile(bs, [2.5, 97.5]))
    return out


if __name__ == "__main__":
    rng = np.random.default_rng(114)
    a, b = run(sys.argv[1], rng), run(sys.argv[2], rng)
    for c in CLS:
        print(f"{c:26s} n={b[c][0]:5d}  113.3 {a[c][1]:+.4f} [{a[c][2]:+.4f},{a[c][3]:+.4f}]  ->  114.4 {b[c][1]:+.4f} [{b[c][2]:+.4f},{b[c][3]:+.4f}]")
