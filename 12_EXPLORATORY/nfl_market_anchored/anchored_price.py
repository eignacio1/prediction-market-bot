"""EXPLORATORY -- W85.1 Part A: the NFL market-anchored price, built offline.
price = anchor (de-vigged market probability) + w * (adjusted - anchor); the adjustment is the UNPRICED part of the
factor terms, term * (1 - share priced), pushed through each strike. Everything is fit on earlier seasons only
(rolling origin); w is the held-out Brier-minimising pull in [0, 1] (never P&L). Frozen arms are not touched.
Usage: anchored_price.py terms.json schedules.parquet out_dir"""
from __future__ import annotations
import json, math, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import norm

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from _fence import safe_out  # noqa: E402

SEED, B = 20261022, 2000
SP_OFF = np.array([-5.5, -2.5, 0.5, 3.5, 6.5])   # strike offsets from the closing line, fixed before any outcome
TT_OFF = np.array([-2.5, 0.5, 3.5])
FAMS = ["ML", "SPREAD", "TOTAL", "TEAMTOTAL"]
WGRID = np.round(np.arange(0, 1.01, 0.1), 2)


def logit(p): return np.log(p / (1 - p))
def expit(x): return 1 / (1 + np.exp(-x))


def ml_prob(h, a):
    with np.errstate(divide="ignore", invalid="ignore"):   # np.where evaluates both branches; the unused one can divide by zero
        ph = np.where(h < 0, -h / (-h + 100), 100 / (h + 100)); pa = np.where(a < 0, -a / (-a + 100), 100 / (a + 100))
    return ph / (ph + pa)


def load(terms_p, sched_p):
    t = pd.DataFrame(json.load(open(terms_p)))
    s = pd.read_parquet(sched_p)[["game_id", "spread_line", "total_line", "home_moneyline", "away_moneyline"]]
    d = t.merge(s, on="game_id", how="inner").dropna(subset=["spread_line", "total_line", "home_moneyline", "away_moneyline"])
    d = d.sort_values(["season", "game_id"]).reset_index(drop=True)
    d["p0"] = ml_prob(d.home_moneyline.to_numpy(float), d.away_moneyline.to_numpy(float))
    d["l0"] = logit(d.p0)
    for k in ("c_h", "c_a", "f8_h", "f8_a"): d[k] = d[k].astype(float).fillna(0.0)
    d["dC"], d["sC"], d["d8"], d["s8"] = d.c_h - d.c_a, d.c_h + d.c_a, d.f8_h - d.f8_a, d.f8_h + d.f8_a
    d["hp"] = (d.total + d.margin) / 2; d["ap"] = (d.total - d.margin) / 2
    return d


def ols(X, y): return np.linalg.lstsq(X, y, rcond=None)[0]


def share(d, target, eng, term, boot=0, rng=None):
    """b = coefficient on `term` in target ~ 1 + eng + term; for ML the share is relative to the engine scale."""
    X = np.column_stack([np.ones(len(d)), d[eng], d[term]]); y = d[target].to_numpy()
    def one(ix):
        c = ols(X[ix], y[ix]); return c[2] / c[1] if target == "l0" else c[2]
    b = one(np.arange(len(d)))
    if not boot: return b
    bs = [one(rng.integers(0, len(d), len(d))) for _ in range(boot)]
    return b, np.quantile(bs, .025), np.quantile(bs, .975)


def fit(d, rng):
    """All parameters from rows `d` (earlier seasons only). No outcomes enter the shares; sigmas use outcomes of PRIOR seasons only."""
    p = {}
    d = d.assign(cm=d.spread_line, ct=d.total_line)
    for tag, tm, ts in (("F8", "d8", "s8"), ("C", "dC", "sC")):
        bsp, lsp, hsp = share(d, "cm", "mu_m", tm, 200, rng)
        btt, ltt, htt = share(d, "ct", "mu_t", ts, 200, rng)
        bml, lml, hml = share(d, "l0", "mu_m", tm, 200, rng)
        p[tag] = dict(b_sp=bsp, b_tot=btt, b_ml=bml, ci_sp=(lsp, hsp), ci_tot=(ltt, htt), ci_ml=(lml, hml))
    p["slope"] = ols(np.column_stack([np.ones(len(d)), d.spread_line]), d.l0.to_numpy())[1]   # market's own logit-per-point
    p["sd_m"] = float(np.std(d.margin - d.spread_line)); p["sd_t"] = float(np.std(d.total - d.total_line))
    mh = (d.total_line + d.spread_line) / 2; ma = (d.total_line - d.spread_line) / 2
    p["sd_tt"] = float(np.std(np.r_[d.hp - mh, d.ap - ma]))
    return p


def eff(p, tag, fam, gate):
    """Effective share priced; with `gate` a share whose CI spans both 0 and 1 gets weight zero ('no reason, no position')."""
    k = {"SP": "sp", "TOT": "tot", "ML": "ml"}[fam]; b = p[tag]["b_" + k]; lo, hi = p[tag]["ci_" + k]
    if gate and lo <= 0 and hi >= 1: return None
    return min(max(b, 0.0), 1.0)


def shifts(p, g, variant):
    """Unpriced shift in margin points / total points / ML points. variant: F8 | PRIMARY (F8 + gated C) | F8+C0 (C at b=0, upper bound)."""
    dm = np.zeros(len(g)); dt = np.zeros(len(g)); dl = np.zeros(len(g))
    for tag, tm, ts, gate, on in (("F8", "d8", "s8", False, True), ("C", "dC", "sC", variant == "PRIMARY", variant != "F8")):
        if not on: continue
        if variant == "F8+C0" and tag == "C": bsp = btt = bml = 0.0
        else:
            bsp, btt, bml = eff(p, tag, "SP", gate), eff(p, tag, "TOT", gate), eff(p, tag, "ML", gate)
        if bsp is not None: dm += (1 - bsp) * g[tm].to_numpy()
        if btt is not None: dt += (1 - btt) * g[ts].to_numpy()
        if bml is not None: dl += (1 - bml) * g[tm].to_numpy()
    return dm, dt, dl


def predict(p, g, variant):
    """-> {family: (anchor_prob, adjusted_prob, outcome)} each shaped (games, strikes)."""
    dm, dt, dl = shifts(p, g, variant); out = {}
    sl = g.spread_line.to_numpy()[:, None]; tl = g.total_line.to_numpy()[:, None]
    out["ML"] = (g.p0.to_numpy()[:, None], expit(g.l0.to_numpy() + p["slope"] * dl)[:, None], g.y.to_numpy()[:, None])
    k = sl + SP_OFF; mar = g.margin.to_numpy()[:, None]
    out["SPREAD"] = (norm.sf((k - sl) / p["sd_m"]), norm.sf((k - sl - dm[:, None]) / p["sd_m"]), (mar > k).astype(float))
    k = tl + SP_OFF; tot = g.total.to_numpy()[:, None]
    out["TOTAL"] = (norm.sf((k - tl) / p["sd_t"]), norm.sf((k - tl - dt[:, None]) / p["sd_t"]), (tot > k).astype(float))
    mh = (tl + sl) / 2; ma = (tl - sl) / 2; kh, ka = mh + TT_OFF, ma + TT_OFF
    hp, ap = g.hp.to_numpy()[:, None], g.ap.to_numpy()[:, None]
    sh, sa = ((dt + dm) / 2)[:, None], ((dt - dm) / 2)[:, None]
    out["TEAMTOTAL"] = (np.c_[norm.sf((kh - mh) / p["sd_tt"]), norm.sf((ka - ma) / p["sd_tt"])],
                        np.c_[norm.sf((kh - mh - sh) / p["sd_tt"]), norm.sf((ka - ma - sa) / p["sd_tt"])],
                        np.c_[(hp > kh).astype(float), (ap > ka).astype(float)])
    return out


def brier(pr, y): return (pr - y) ** 2


def pull(an, ad, w): return an + w * (ad - an)


def run(d, variant, rng):
    """Rolling origin. Returns per test season: fit params, inner held-out w per family, lambda gate, predictions."""
    seasons = sorted(d.season.unique()); res = {}
    for T in seasons[1:]:
        pT = fit(d[d.season < T], rng)
        inner = {f: [] for f in FAMS}
        for S in seasons[1:]:
            if S >= T: break
            pS = fit(d[d.season < S], rng); o = predict(pS, d[d.season == S], variant)
            for f in FAMS: inner[f].append(o[f])
        w, lam = {}, {}
        for f in FAMS:
            if not inner[f]: w[f] = 1.0; lam[f] = None; continue
            an = np.vstack([a for a, _, _ in inner[f]]); ad = np.vstack([b for _, b, _ in inner[f]]); y = np.vstack([c for _, _, c in inner[f]])
            sc = [brier(pull(an, ad, x), y).mean() for x in WGRID]; w[f] = float(WGRID[int(np.argmin(sc))])
            dep = (ad - an).ravel(); r = (y - an).ravel()
            def lm(ix): return float((dep[ix] @ r[ix]) / max(dep[ix] @ dep[ix], 1e-12))
            n = len(dep); bs = [lm(rng.integers(0, n, n)) for _ in range(200)]
            lam[f] = (lm(np.arange(n)), float(np.std(bs)))
        res[T] = dict(p=pT, w=w, lam=lam, pred=predict(pT, d[d.season == T], variant), games=d[d.season == T].reset_index(drop=True))
    return res


def kfee(p): return np.ceil(0.07 * p * (1 - p) * 100) / 100   # Kalshi taker fee per contract, rounded up to the cent


def score(res, use_w, seasons, rng):
    """Per-game paired dBrier (price - anchor) per family; pooled = mean of the four family means; game-clustered bootstrap."""
    per = {f: [] for f in FAMS}; clear = {f: [0, 0] for f in FAMS}; ngame = 0
    for T in seasons:
        r = res[T]; ngame += len(r["games"])
        for f in FAMS:
            an, ad, y = r["pred"][f]; w = r["w"][f] if use_w else 1.0
            pr = pull(an, ad, w); per[f].append((brier(pr, y) - brier(an, y)).mean(axis=1))
            if r["lam"][f] is not None:
                lm, se = r["lam"][f]; edge = np.abs(pr - an) * max(lm - se, 0.0)
                ok = edge > kfee(np.where(ad > an, an, 1 - an)); clear[f][0] += int(ok.sum()); clear[f][1] += int(ok.size)
    per = {f: np.concatenate(v) for f, v in per.items()}; n = len(per["ML"])
    pooled = np.mean([per[f] for f in FAMS], axis=0); out = {}
    ix = [rng.integers(0, n, n) for _ in range(B)]
    for name, v in {**per, "POOLED": pooled}.items():
        bs = np.array([v[i].mean() for i in ix]); out[name] = dict(dBrier=float(v.mean()), lo=float(np.quantile(bs, .025)), hi=float(np.quantile(bs, .975)), sd_game=float(v.std()))
    out["_n_games"] = ngame; out["_clear"] = {f: dict(clearing=c[0], markets=c[1]) for f, c in clear.items()}
    return out


def main(terms_p, sched_p, out_dir):
    d = load(terms_p, sched_p); rng = np.random.default_rng(SEED); out = {"n_games": int(len(d)), "per_season": d.groupby("season").size().to_dict()}
    seasons = sorted(d.season.unique())
    for variant in ("F8", "PRIMARY", "F8+C0"):
        res = run(d, variant, np.random.default_rng(SEED))
        out[variant] = dict(held_out_w=score(res, True, seasons[2:], np.random.default_rng(SEED)),
                            w_equals_1=score(res, False, seasons[1:], np.random.default_rng(SEED)),
                            w_by_season={int(T): res[T]["w"] for T in res},
                            params_last={k: (v if not isinstance(v, dict) else {a: (list(map(float, b)) if isinstance(b, tuple) else float(b)) for a, b in v.items()}) for k, v in res[seasons[-1]]["p"].items()},
                            mean_abs_departure_w1={f: float(np.mean(np.concatenate([np.abs(res[T]['pred'][f][1] - res[T]['pred'][f][0]).ravel() for T in seasons[2:]]))) for f in FAMS},
                            gate_lambda_last={f: res[seasons[-1]]["lam"][f] for f in FAMS})
    safe_out(Path(out_dir) / "results_W85.json").write_text(json.dumps(out, indent=1, default=float)); print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main(*sys.argv[1:4])
