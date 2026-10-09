"""EXPLORATORY -- NFL QB-shrunk challenger vs frozen EXP-037 (W64.1 Part B). Not a verdict. Plan: README.md (frozen before fitting).

Reads public nflverse copies + archived 2025 KXNFLGAME candles. Pre-2026 only. Writes only via safe_out().
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent.parent / "src"))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import (  # noqa: E402
    FEATURE_NAMES, NFLPregameFeatureBuilder,
)
from qb_features import EB_K, ChallengerFeatures, _d  # noqa: E402

B, SEED = 2000, 20261009
TESTS = list(range(2019, 2026))
M = 8
ALPHA = 0.05 / M
KMAP = {"JAX": "JAX", "LA": "LA", "LAR": "LA", "WAS": "WAS", "WSH": "WAS", "LV": "LV", "OAK": "LV"}
RATES = ["off_epa_h", "def_epa_h", "off_epa_a", "def_epa_a", "pf_h", "pa_h", "pf_a", "pa_a"]
REST = ["rest_diff", "rest_short_h", "rest_short_a"]
ARMS = {
    "frozen": FEATURE_NAMES,
    "full": FEATURE_NAMES + ["qb_epa_h", "qb_epa_a"],
    "qb_only": FEATURE_NAMES + ["qb_epa_h", "qb_epa_a"],
    "eb_only": FEATURE_NAMES,
    "full_oracle": FEATURE_NAMES + ["qbo_epa_h", "qbo_epa_a"],
}
SRC = {"frozen": ("raw", "raw"), "full": ("eb", "eb"), "qb_only": ("raw", "raw"), "eb_only": ("eb", "eb"),
       "full_oracle": ("eb", "eb")}
QBCOL = {"frozen": None, "full": "qb", "qb_only": "qb", "eb_only": None, "full_oracle": "qbo"}


def norm(t):
    return KMAP.get(t, t)


def phi(z):
    return 0.5 * (1.0 + np.vectorize(math.erf)(np.asarray(z, float) / math.sqrt(2.0)))


def ridge(X, y, lam):
    mu, sd = X.mean(0), X.std(0)
    sd[sd == 0] = 1.0
    Z = (X - mu) / sd
    w = np.linalg.solve(Z.T @ Z + lam * np.eye(Z.shape[1]), Z.T @ (y - y.mean()))
    return y.mean(), w, mu, sd


def pred(m, X):
    b0, w, mu, sd = m
    return b0 + ((X - mu) / sd) @ w


def platt(z, y):
    a, b = 1.0, 0.0
    for _ in range(50):
        eta = a * z + b
        p = np.clip(phi(eta), 1e-6, 1 - 1e-6)
        pdf = np.exp(-0.5 * eta**2) / math.sqrt(2 * math.pi)
        w = pdf**2 / (p * (1 - p))
        g = (y - p) * pdf / (p * (1 - p))
        X = np.column_stack([z, np.ones_like(z)])
        s = np.linalg.solve(X.T @ (X * w[:, None]) + 1e-9 * np.eye(2), X.T @ g)
        a, b = a + s[0], b + s[1]
    return a, b


def boot(d, level=0.95, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(d)
    m = d[rng.integers(0, n, (B, n))].mean(1)
    lo, hi = (1 - level) / 2 * 100, (1 + level) / 2 * 100
    return dict(mean=float(d.mean()), lo=float(np.percentile(m, lo)), hi=float(np.percentile(m, hi)), level=level)


def build(sched, ext, stats):
    cf = ChallengerFeatures(stats, sched, ext)
    fb = NFLPregameFeatureBuilder(stats, sched)
    exq = ext.set_index("game_id")
    reg = sched[(sched.game_type == "REG") & sched.home_score.notna() & (sched.season >= 2015) & (sched.season <= 2025)]
    rows = []
    for r in reg.itertuples():
        as_of = datetime(*map(int, str(r.gameday).split("-")), tzinfo=timezone.utc)
        out = fb.row(r.home_team, r.away_team, as_of, r.home_rest, r.away_rest)
        if out is None:
            continue
        d = _d(r.gameday)
        eh, ea = cf.team_rates(r.home_team, d, EB_K), cf.team_rates(r.away_team, d, EB_K)
        if eh is None or ea is None:
            continue
        f = out["features"]
        row = {"game_id": r.game_id, "season": r.season, "week": r.week, "home": norm(r.home_team),
               "away": norm(r.away_team), "gameday": str(r.gameday), "gametime": str(exq.gametime.get(r.game_id)) if r.game_id in exq.index else "",
               "margin": r.home_score - r.away_score}
        row["y"] = 1.0 if row["margin"] > 0 else (0.5 if row["margin"] == 0 else 0.0)
        for k in FEATURE_NAMES:
            row[f"raw_{k}"] = f[k]
        for k in REST:
            row[f"eb_{k}"] = f[k]
        for sfx, e in (("h", eh), ("a", ea)):
            row[f"eb_off_epa_{sfx}"], row[f"eb_def_epa_{sfx}"] = e["off_epa"], e["def_epa"]
            row[f"eb_pf_{sfx}"], row[f"eb_pa_{sfx}"] = e["pf"], e["pa"]
        ph, pa = cf.projected_starter(r.home_team, d), cf.projected_starter(r.away_team, d)
        row["qb_epa_h"], row["qb_epa_a"] = cf.qb_epa(ph, d), cf.qb_epa(pa, d)
        ah = exq.home_qb_id.get(r.game_id) if r.game_id in exq.index else None
        aa = exq.away_qb_id.get(r.game_id) if r.game_id in exq.index else None
        ah = None if pd.isna(ah) else ah
        aa = None if pd.isna(aa) else aa
        row["qbo_epa_h"], row["qbo_epa_a"] = cf.qb_epa(ah, d), cf.qb_epa(aa, d)
        row["qb_changed"] = float((ah is not None and ph is not None and ah != ph) or (aa is not None and pa is not None and aa != pa))
        rows.append(row)
    return pd.DataFrame(rows)


def cols(arm):
    src = SRC[arm][0]
    base = [f"{src}_{k}" for k in FEATURE_NAMES]
    q = QBCOL[arm]
    return base + ([f"{q}_epa_h", f"{q}_epa_a"] if q else [])


def split_ticker(tk, teams):
    ev, side = tk.rsplit("-", 1)[0], tk.rsplit("-", 1)[1]
    body = ev.split("-")[1][7:]
    for i in (2, 3):
        a, h = body[:i], body[i:]
        if norm(a) in teams and norm(h) in teams:
            return norm(a), norm(h), norm(side)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--schedule", required=True)
    ap.add_argument("--schedule-ext", required=True)
    ap.add_argument("--team-stats", required=True)
    ap.add_argument("--candles", required=True)
    ap.add_argument("--markets", required=True)
    a = ap.parse_args()
    sched, ext, stats = pd.read_parquet(a.schedule), pd.read_parquet(a.schedule_ext), pd.read_parquet(a.team_stats)
    df = build(sched, ext, stats)
    print("rows", len(df), file=sys.stderr)
    P = {k: [] for k in ARMS}
    meta = []
    for T in TESTS:
        tr, ca, te = df[df.season <= T - 2], df[df.season == T - 1], df[df.season == T]
        for k in ARMS:
            c = cols(k)
            m = ridge(tr[c].to_numpy(float), tr.margin.to_numpy(float), 100.0)
            rc = pred(m, ca[c].to_numpy(float))
            sm = float(np.std(ca.margin.to_numpy(float) - rc, ddof=1))
            nt = (ca.margin != 0).to_numpy()
            aa, bb = platt(rc[nt] / sm, ca.y.to_numpy()[nt])
            P[k].append(phi(aa * pred(m, te[c].to_numpy(float)) / sm + bb))
        meta.append(te)
    te = pd.concat(meta)
    y = te.y.to_numpy()
    Pa = {k: np.concatenate(v) for k, v in P.items()}
    seas, wk, qbc = te.season.to_numpy(), te.week.to_numpy(), te.qb_changed.to_numpy()
    res = {"n_games": int(len(y)), "tests": TESTS, "m": M, "alpha": ALPHA, "brier": {k: float(((p - y) ** 2).mean()) for k, p in Pa.items()},
           "frozen_2025_brier": float(((Pa["frozen"] - y) ** 2)[seas == 2025].mean()), "arms": {}}
    for k in ARMS:
        if k == "frozen":
            continue
        d = (Pa[k] - y) ** 2 - (Pa["frozen"] - y) ** 2
        ps = {str(T): float(d[seas == T].mean()) for T in TESTS}
        res["arms"][k] = {"delta_vs_frozen_ci95": boot(d), "delta_vs_frozen_ci_bonf": boot(d, 1 - ALPHA),
                          "per_season_delta": ps, "per_game_sd": float(d.std(ddof=1)), "seasons_better": int(sum(v < 0 for v in ps.values())),
                          "early_wk1_4": boot(d[wk <= 4]) | {"n": int((wk <= 4).sum())},
                          "qb_changed_games": boot(d[qbc == 1]) | {"n": int((qbc == 1).sum())}}
    f = res["arms"]["full"]
    res["verdict_full_beats_frozen"] = bool(f["delta_vs_frozen_ci_bonf"]["hi"] < 0 and f["seasons_better"] >= 5)

    # ---- 2025 market-mid subset ----
    ho = te[te.season == 2025].assign(p_frozen=Pa["frozen"][seas == 2025], p_full=Pa["full"][seas == 2025])
    teams = set(df.home) | set(df.away)
    sets = {}
    for l in open(a.candles):
        if '"KXNFLGAME-25' not in l and '"KXNFLGAME-26JAN' not in l and '"KXNFLGAME-26FEB' not in l:
            continue
        r = json.loads(l)
        if r.get("period_min") == 1 and r.get("candles"):
            sets[r["ticker"]] = r["candles"]
    mres = {}
    for l in open(a.markets):
        if '"KXNFLGAME-25' not in l and '"KXNFLGAME-26' not in l:
            continue
        r = json.loads(l)
        mres[r["ticker"]] = r.get("result")
    et = ZoneInfo("America/New_York")
    mk = []
    for tk, cs in sets.items():
        sp = split_ticker(tk, teams)
        if not sp:
            continue
        away, home, side = sp
        if side != home:
            continue
        g = ho[(ho.home == home) & (ho.away == away)]
        if len(g) != 1:
            continue
        g = g.iloc[0]
        ko = datetime(*map(int, g.gameday.split("-")), *map(int, g.gametime.split(":")[:2]), tzinfo=et).timestamp()
        cand = [c for c in cs if c["t"] <= ko - 1800 and c["ask"]["close"] is not None and c["bid"]["close"] is not None]
        if not cand or mres.get(tk) not in ("yes", "no"):
            continue
        c = cand[-1]
        if ko - 1800 - c["t"] > 3600:
            continue
        mk.append(dict(p_frozen=g.p_frozen, p_full=g.p_full, mid=(c["ask"]["close"] + c["bid"]["close"]) / 2,
                       y=1.0 if mres[tk] == "yes" else 0.0))
    m = pd.DataFrame(mk)
    ms = {"n": int(len(m))}
    if len(m) >= 10:
        for k in ("p_frozen", "p_full", "mid"):
            ms[f"brier_{k}"] = float(((m[k] - m.y) ** 2).mean())
        for k in ("p_frozen", "p_full"):
            ms[f"{k}_minus_mid"] = boot((((m[k] - m.y) ** 2) - ((m.mid - m.y) ** 2)).to_numpy())
        ms["full_minus_frozen"] = boot((((m.p_full - m.y) ** 2) - ((m.p_frozen - m.y) ** 2)).to_numpy())
    res["market_subset_2025"] = ms
    p = safe_out(HERE / "results.json")
    p.write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))


if __name__ == "__main__":
    main()
