"""EXPLORATORY -- W89.3 Part A: which factors does the closing line NOT price? Close is the target, never an input.

Method (W77.2): close = a + b0*engine + b*term. b = share of the term the line prices. Terms are rolling-origin
out-of-sample (built by W77.2); here b is fit pooled over test seasons and per season, with game-clustered bootstrap.
Applies: a term measured before the close on the same scale as the close. Does not apply: a term whose scale is
unidentified (term SD tiny vs close noise -> CI spans 0..1; reported as UNIDENTIFIED, not as 'unpriced').
"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _fence import safe_out  # noqa: E402

FEE = 0.07 * 0.25  # Kalshi fee per contract at p=0.5 (upper bound on the fee schedule 0.07*p*(1-p))


def _ols(X, y):
    X1 = np.column_stack([np.ones(len(X)), X])
    return np.linalg.lstsq(X1, y, rcond=None)[0]


def share_priced(engine, term, close, cluster, B=2000, seed=20261027, norm=False):
    """b on `term` in close = a + b0*engine + b*term, with cluster bootstrap CI. Returns dict(b, lo, hi, n, p_b_lt_1)."""
    X = np.column_stack([engine, term]); y = np.asarray(close, float); cl = np.asarray(cluster)
    co = _ols(X, y); b = co[2] / (co[1] if norm else 1.0)  # norm (logit close): share = b/b0
    ids, inv = np.unique(cl, return_inverse=True)
    rows = [np.where(inv == k)[0] for k in range(len(ids))]
    rng = np.random.default_rng(seed); bs = np.empty(B)
    for j in range(B):
        pick = rng.integers(0, len(ids), len(ids))
        i = np.concatenate([rows[k] for k in pick])
        bs[j] = _ols(X[i], y[i])[2] / (_ols(X[i], y[i])[1] if norm else 1.0)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    # one-sided p that b<1 (term not fully priced): share of bootstrap draws with b>=1, doubled-safe
    p = float((bs >= 1).mean()) if b < 1 else 1.0
    return dict(b=float(b), lo=float(lo), hi=float(hi), n=int(len(y)), p_unpriced=max(p, 1.0 / (B + 1)))


def unpriced_prob(sd_term, b_hi, slope):
    """Probability-scale size of the unpriced part at 1 SD of the term, using the optimistic-for-pricing bound b_hi."""
    return max(0.0, 1.0 - b_hi) * sd_term * slope


def bh(pvals, q=0.05):
    p = np.asarray(pvals, float); m = len(p); o = np.argsort(p)
    thr = q * (np.arange(1, m + 1) / m); ok = p[o] <= thr
    k = (np.where(ok)[0].max() + 1) if ok.any() else 0
    keep = np.zeros(m, bool); keep[o[:k]] = True
    return keep


def devig(h, a):
    ph = 100 / (h + 100) if h > 0 else -h / (-h + 100); pa = 100 / (a + 100) if a > 0 else -a / (-a + 100)
    return ph / (ph + pa)


def _simulate_check():
    """Known answer: priced share 0.6 by construction."""
    r = np.random.default_rng(1); n = 1500
    e = r.normal(0, 6, n); t = r.normal(0, 2, n)
    c = 1 + 0.8 * e + 0.6 * t + r.normal(0, 1.5, n)
    return share_priced(e, t, c, np.arange(n), B=400)


def main(terms, sched, out):
    t = pd.read_json(terms)
    s = pd.read_parquet(sched)[["game_id", "spread_line", "total_line", "home_moneyline", "away_moneyline"]]
    d = t.merge(s, on="game_id", how="left").dropna(subset=["spread_line", "total_line"]).copy()
    d["p_close"] = [devig(h, a) for h, a in zip(d.home_moneyline, d.away_moneyline)]
    for c in ("c_h", "c_a", "f8_h", "f8_a"):
        d[c + "0"] = d[c].fillna(0.0)
    d["dC"], d["sC"] = d.c_h0 - d.c_a0, d.c_h0 + d.c_a0
    d["d8"], d["s8"] = d.f8_h0 - d.f8_a0, d.f8_h0 + d.f8_a0
    d["has8"] = d.f8_h.notna() & d.f8_a.notna()
    lg = np.log(d.p_close.clip(0.01, 0.99) / (1 - d.p_close.clip(0.01, 0.99)))
    sl_m = 0.399 / d.margin.std(); sl_t = 0.399 / d.total.std()
    sl_ml = 0.25  # d p / d logit at p=.5
    specs = [  # factor, seat, family, engine, term, close, slope-to-prob (per unit of close scale)
        ("F5/F6 coverage x personnel", "N7/N8", "spread", "mu_m", "dC", d.spread_line, sl_m),
        ("F5/F6 coverage x personnel", "N7/N8", "total", "mu_t", "sC", d.total_line, sl_t),
        ("F5/F6 coverage x personnel", "N7/N8", "moneyline", "mu_m", "dC", lg, sl_ml),
        ("F8 availability", "N10", "spread", "mu_m", "d8", d.spread_line, sl_m),
        ("F8 availability", "N10", "total", "mu_t", "s8", d.total_line, sl_t),
        ("F8 availability", "N10", "moneyline", "mu_m", "d8", lg, sl_ml),
    ]
    rows = []
    for fac, seat, fam, eng, term, close, slope in specs:
        m = d.has8 if term in ("d8", "s8") else np.ones(len(d), bool)
        sub = d[m]; cl = np.asarray(close)[np.asarray(m)]
        # joint engine+both terms would be fuller; screen is one term at a time, as in W77.2 (other terms in d are small)
        nm = fam == "moneyline"
        r = share_priced(sub[eng].to_numpy(), sub[term].to_numpy(), cl, sub.game_id.to_numpy(), norm=nm)
        sd = float(sub[term].std())
        r.update(factor=fac, seat=seat, family=fam, term_sd=sd)
        # per-season b (stability)
        r["b_by_season"] = {int(k): round(share_priced(g[eng].to_numpy(), g[term].to_numpy(),
                            np.asarray(close)[np.asarray(m)][(sub.season == k).to_numpy()], g.game_id.to_numpy(), B=300, norm=nm)["b"], 3)
                            for k, g in sub.groupby("season")}
        sl = slope * (1.0 if not nm else 1.0)
        # moneyline: unpriced logit = (1-share)*b0*term ; b0 (logit per engine point) from the same fit
        b0 = float(_ols(np.column_stack([sub[eng], sub[term]]), cl)[1]) if nm else 1.0
        r["unpriced_prob_1sd"] = unpriced_prob(sd * b0, r["hi"], sl)
        r["unpriced_prob_point"] = max(0.0, 1 - r["b"]) * sd * b0 * sl
        r["identified"] = bool((r["hi"] - r["lo"]) < 1.0)
        r["clears_fee"] = bool(r["identified"] and r["unpriced_prob_1sd"] > FEE)
        if not r["identified"]:
            r["p_unpriced"] = 1.0  # unidentified terms cannot be called unpriced
        rows.append(r)
    keep = bh([r["p_unpriced"] for r in rows])
    for r, k in zip(rows, keep):
        r["bh_survives_q05"] = bool(k)
    rows.sort(key=lambda r: -r["unpriced_prob_point"])
    sim = _simulate_check()
    res = {"n_games": int(len(d)), "fee_per_contract": FEE, "known_answer_check_true_b_0.6": sim, "screen": rows}
    safe_out(out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
