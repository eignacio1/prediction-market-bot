"""W71.3 evaluation. Run ONCE after the README plan commit. Writes results.json via _fence.safe_out()."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import games_features as G  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_ingest as N  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import FEATURE_NAMES, NBAFeatureBuilder, _dt  # noqa: E402
from prediction_market_bot.pregame_shadow.nfl_model import _phi  # noqa: E402

LAMBDA, SEED, B = 100.0, 71303, 20000
OFFSETS = [-6.0, -3.0, 0.0, 3.0, 6.0]
FOLDS = {"A": dict(train=lambda s: 2016 <= s <= 2023, cal=2024, test=2025), "B": dict(train=lambda s: 2016 <= s <= 2024, cal=2025, test=2026)}
FAMS = ["moneyline", "spread", "total"]
RAW_G = HERE.parents[1].parent / "nba_raw"
RAW_P = HERE.parents[1].parent / "_w65_data"
INJ = [str(HERE.parent / "20261012_nba_points_minutes" / "inj"), str(HERE / "inj2026")]


def frame():
    games = []
    for s in range(2015, 2027):
        games += list(N.load_season(s, RAW_G)["games"].values())
    extra = G.build_extra(RAW_G, RAW_P, INJ)
    fb = NBAFeatureBuilder(games)
    rows = []
    for g in games:
        if not (g["completed"] and g["season_type"] == 2 and g["home_score"] is not None):
            continue
        start = _dt(g["start_time_utc"])
        out = fb.row(g["home"], g["away"], start, start)
        if out is None:
            continue
        e = extra.get(g["game_id"])
        has = e is not None
        e = e or {"h_out_min": 0.0, "a_out_min": 0.0, "d_out_min": 0.0, "h_inj_missing": 1.0, "a_inj_missing": 1.0}
        rows.append({"gid": g["game_id"], "season": g["season"], "margin": g["home_score"] - g["away_score"],
                     "total": g["home_score"] + g["away_score"], "has_players": has, **out["features"], **e})
    return rows


def arr(rows, keys):
    return np.array([[r[k] for k in keys] for r in rows], float)


def ridge(X, y):
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return float(y.mean()), w, mu, sd


def lin(m, X):
    b0, w, mu, sd = m
    return b0 + ((X - mu) / sd) @ w


def phi(x):
    return np.array([_phi(float(v)) for v in np.atleast_1d(x)])


def fit(tr, ca, keys):
    mm = ridge(arr(tr, keys), np.array([r["margin"] for r in tr], float))
    tm = ridge(arr(tr, keys), np.array([r["total"] for r in tr], float))
    Xc = arr(ca, keys)
    rm = np.array([r["margin"] for r in ca], float) - lin(mm, Xc)
    rt = np.array([r["total"] for r in ca], float) - lin(tm, Xc)
    sm, st = float(rm.std(ddof=1)), float(rt.std(ddof=1))
    rho = float(np.corrcoef(rm, rt)[0, 1])
    z = lin(mm, Xc) / sm
    y = np.array([1.0 if r["margin"] > 0 else 0.0 for r in ca])
    a, b = 1.0, 0.0
    for _ in range(50):
        eta = a * z + b
        p = np.clip(phi(eta), 1e-6, 1 - 1e-6)
        pdf = np.exp(-0.5 * eta ** 2) / math.sqrt(2 * math.pi)
        wg = pdf ** 2 / (p * (1 - p))
        gr = (y - p) * pdf / (p * (1 - p))
        Xd = np.column_stack([z, np.ones_like(z)])
        step = np.linalg.solve(Xd.T @ (Xd * wg[:, None]) + 1e-9 * np.eye(2), Xd.T @ gr)
        a, b = a + step[0], b + step[1]
    return dict(mm=mm, tm=tm, sm=sm, st=st, rho=rho, a=float(a), b=float(b), keys=keys)


def dist(M, te):
    X = arr(te, M["keys"])
    return M["a"] * lin(M["mm"], X) + M["b"] * M["sm"], lin(M["tm"], X)


def briers(te, ctrl, chal):
    """Per-game mean Brier per family for both arms; strike grid from the CONTROL means."""
    mc, tc = dist(ctrl, te)
    mx, tx = dist(chal, te)
    marg = np.array([r["margin"] for r in te], float)
    tot = np.array([r["total"] for r in te], float)
    out = {}
    def br(p, y): return (p - y) ** 2
    y = (marg > 0).astype(float)
    out["moneyline"] = (br(1 - phi((0.5 - mc) / ctrl["sm"]), y), br(1 - phi((0.5 - mx) / chal["sm"]), y))
    for fam, mu_c, mu_x, sc, sx, res in (("spread", mc, mx, ctrl["sm"], chal["sm"], marg), ("total", tc, tx, ctrl["st"], chal["st"], tot)):
        c, x = [], []
        for off in OFFSETS:
            k = np.round(mu_c * 2) / 2 + off
            yy = (res > k).astype(float)
            c.append(br(1 - phi((k - mu_c) / sc), yy))
            x.append(br(1 - phi((k - mu_x) / sx), yy))
        out[fam] = (np.mean(c, 0), np.mean(x, 0))
    return out


def boot(d, rng, q):
    n = len(d)
    idx = rng.integers(0, n, size=(B, n))
    m = d[idx].mean(1)
    return float(np.percentile(m, 100 * q[0])), float(np.percentile(m, 100 * q[1]))


def main():
    rows = frame()
    cov = {}
    for s in sorted({r["season"] for r in rows}):
        rs = [r for r in rows if r["season"] == s]
        cov[s] = {"n": len(rs), "has_players": sum(r["has_players"] for r in rs),
                  "snap_both": sum(1 for r in rs if r["has_players"] and not r["h_inj_missing"] and not r["a_inj_missing"])}
    keys_c, keys_x = FEATURE_NAMES, FEATURE_NAMES + G.EXTRA
    q = (0.5 * (100 - 98.33) / 100, 1 - 0.5 * (100 - 98.33) / 100)
    rng = np.random.default_rng(SEED)
    res, pooled = {"coverage": cov, "folds": {}, "pooled": {}}, {f: [] for f in FAMS}
    for name, fd in FOLDS.items():
        tr = [r for r in rows if fd["train"](r["season"])]
        ca = [r for r in rows if r["season"] == fd["cal"]]
        te = [r for r in rows if r["season"] == fd["test"]]
        C, X = fit(tr, ca, keys_c), fit(tr, ca, keys_x)
        bs = briers(te, C, X)
        res["folds"][name] = {"n_train": len(tr), "n_cal": len(ca), "n_test": len(te),
                              "ctrl_platt": [C["a"], C["b"]], "chal_platt": [X["a"], X["b"]]}
        ym = np.array([1.0 if r["margin"] > 0 else 0.0 for r in te])
        mc, _ = dist(C, te)
        res["folds"][name]["ctrl_moneyline_brier"] = float(np.mean((1 - phi((0.5 - mc) / C["sm"]) - ym) ** 2))
        for f in FAMS:
            c, x = bs[f]
            d = x - c
            pooled[f].append(d)
            lo, hi = boot(d, rng, q)
            res["folds"][name][f] = {"brier_ctrl": float(c.mean()), "brier_chal": float(x.mean()),
                                     "delta": float(d.mean()), "ci98.33": [lo, hi]}
    for f in FAMS:
        d = np.concatenate(pooled[f])
        lo, hi = boot(d, rng, q)
        fav = all(res["folds"][k][f]["delta"] < 0 for k in FOLDS)
        res["pooled"][f] = {"n": len(d), "delta": float(d.mean()), "ci98.33": [lo, hi],
                            "favourable_both_seasons": fav, "beats_frozen": bool(hi < 0 and fav)}
    from _fence import safe_out
    safe_out(HERE / "results.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
