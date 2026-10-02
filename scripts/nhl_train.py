#!/usr/bin/env python3
"""Train + freeze the NHL pregame model (T-607 / EXP-036 D2). Offline only (Hard Rule 4).

Seasons by start year: GLM fit on <=2023 (alpha chosen on 2022->2023), calibration layer
(total scale + Platt on moneyline) fit on 2024, held-out 2025 (2025-26) scored ONCE, last,
and never fed back into any choice. Usage: python3 scripts/nhl_train.py [--root data/raw/nhl]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from prediction_market_bot.c1_signal_ingestion import nhl_ingest as ni  # noqa: E402
from prediction_market_bot.c2_feature_store.nhl_features import NhlFeatureStore, parse_ts  # noqa: E402
from prediction_market_bot.c3_forecasting import nhl_pregame as m  # noqa: E402

TRAIN_END, CAL_SEASON, HOLDOUT = 2023, 2024, 2025
AS_OF_BEFORE_START = timedelta(hours=1)


def reg_scores(g: dict) -> tuple[int, int]:
    """Regulation score. OT: the winner's final goal was the OT goal; SO: already tied."""
    h, a = g["home_score_ex_so"], g["away_score_ex_so"]
    if g["end_period_type"] == "OT":
        return (h - 1, a) if h > a else (h, a - 1)
    return h, a


def build_rows(games: list[dict]) -> list[dict]:
    store = NhlFeatureStore(games)
    rows = []
    for g in games:
        st = parse_ts(g["start_time_utc"])
        f = store.game_features(g["home"], g["away"], st, st - AS_OF_BEFORE_START)
        rh, ra = reg_scores(g)
        rows.append({**f, "season_year": ni.season_start_year(g["season"]), "reg_h": rh, "reg_a": ra,
                     "tied": int(rh == ra), "home_win": int(g["home_score"] > g["away_score"])})
    return rows


def design(rows: list[dict]) -> tuple[np.ndarray, np.ndarray]:
    X, y = [], []
    for r in rows:
        X.append(m.side_vector(r, "h", "a", 1)); y.append(r["reg_h"])
        X.append(m.side_vector(r, "a", "h", 0)); y.append(r["reg_a"])
    return np.array(X), np.array(y, dtype=float)


def fit_glm(rows: list[dict], alpha: float):
    from sklearn.linear_model import PoissonRegressor
    X, y = design(rows)
    mu, sd = X.mean(0), X.std(0) + 1e-9
    reg = PoissonRegressor(alpha=alpha, max_iter=1000).fit((X - mu) / sd, y)
    return {"mu": mu.tolist(), "sd": sd.tolist(), "coef": reg.coef_.tolist(), "intercept": float(reg.intercept_)}


def poisson_dev(params: dict, rows: list[dict]) -> float:
    mod = m.NhlGoalsModel({"glm": params})
    tot = 0.0
    for r in rows:
        lh, la = mod.lambdas(r)
        for lam, y in ((lh, r["reg_h"]), (la, r["reg_a"])):
            tot += lam - y * math.log(lam)
    return tot / (2 * len(rows))


def fit_c(rows: list[dict], glm: dict) -> float:
    mod = m.NhlGoalsModel({"glm": glm})
    lam = [mod.lambdas(r) for r in rows]
    best, bc = -1e18, 0.0
    for c in np.arange(0.0, 0.31, 0.02):
        ll = 0.0
        for (lh, la), r in zip(lam, rows):
            ll += math.log(max(m.joint_pmf(lh, la, float(c))[r["reg_h"], r["reg_a"]], 1e-12)) if max(r["reg_h"], r["reg_a"]) < m.GRID else 0.0
        if ll > best:
            best, bc = ll, float(c)
    return bc


def fit_logit(xs, ys, iters=200):
    """1-D logistic regression (Platt): P(y=1)=sigmoid(a+b x), Newton."""
    xs, ys = np.array(xs), np.array(ys, dtype=float)
    a, b = 0.0, 1.0
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(a + b * xs)))
        w = p * (1 - p) + 1e-9
        g = np.array([np.sum(ys - p), np.sum((ys - p) * xs)])
        H = np.array([[np.sum(w), np.sum(w * xs)], [np.sum(w * xs), np.sum(w * xs * xs)]]) + 1e-9 * np.eye(2)
        step = np.linalg.solve(H, g)
        a, b = a + step[0], b + step[1]
        if np.abs(step).max() < 1e-9:
            break
    return float(a), float(b)


def brier(p, y):
    p, y = np.array(p), np.array(y, dtype=float)
    return float(np.mean((p - y) ** 2))


def reliability(p, y, bins=10):
    p, y = np.array(p), np.array(y, dtype=float)
    order = np.argsort(p)
    out = []
    for idx in np.array_split(order, bins):
        if len(idx):
            out.append((float(p[idx].mean()), float(y[idx].mean()), int(len(idx))))
    ece = sum(n * abs(a - b) for a, b, n in out) / len(p)
    return out, float(ece)


def evaluate(model: m.NhlGoalsModel, rows: list[dict]) -> dict:
    series = {"ML_home": ([], []), "PL_home_1.5": ([], []), "PL_away_1.5": ([], []),
              "PL_home_2.5": ([], []), "PL_away_2.5": ([], []), "TOT_5.5": ([], []), "TOT_6.5": ([], [])}
    for r in rows:
        lad = model.ladder(r)
        tie = r["reg_h"] == r["reg_a"]
        fin_tot = r["reg_h"] + r["reg_a"] + (1 if tie else 0)
        mg = r["reg_h"] - r["reg_a"]
        vals = {"ML_home": (lad.p_home_win(), r["home_win"]),
                "PL_home_1.5": (lad.p_win_by_over("home", 1.5), int(mg >= 2)),
                "PL_away_1.5": (lad.p_win_by_over("away", 1.5), int(-mg >= 2)),
                "PL_home_2.5": (lad.p_win_by_over("home", 2.5), int(mg >= 3)),
                "PL_away_2.5": (lad.p_win_by_over("away", 2.5), int(-mg >= 3)),
                "TOT_5.5": (lad.p_total_over(5.5), int(fin_tot > 5.5)),
                "TOT_6.5": (lad.p_total_over(6.5), int(fin_tot > 6.5))}
        for k, (p, y) in vals.items():
            series[k][0].append(p); series[k][1].append(y)
    res = {}
    for k, (p, y) in series.items():
        rel, ece = reliability(p, y)
        base = float(np.mean(y))
        res[k] = {"n": len(y), "brier": brier(p, y), "brier_climatology_in_sample": brier([base] * len(y), y),
                  "base_rate": base, "ece": ece, "reliability": rel}
    return res


def svg_plot(res: dict, path: Path) -> None:
    W = 420
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*2}" height="{W*2}" font-family="sans-serif" font-size="11">']
    for i, k in enumerate(["ML_home", "PL_home_1.5", "TOT_5.5", "TOT_6.5"]):
        ox, oy = (i % 2) * W, (i // 2) * W
        parts.append(f'<rect x="{ox+40}" y="{oy+30}" width="{W-80}" height="{W-80}" fill="none" stroke="#888"/>')
        parts.append(f'<line x1="{ox+40}" y1="{oy+W-50}" x2="{ox+W-40}" y2="{oy+30}" stroke="#bbb" stroke-dasharray="4"/>')
        parts.append(f'<text x="{ox+40}" y="{oy+20}">{k} held-out 2025-26 (n={res[k]["n"]}, ECE={res[k]["ece"]:.3f})</text>')
        for pm, ym, n in res[k]["reliability"]:
            x = ox + 40 + pm * (W - 80); y = oy + W - 50 - ym * (W - 80)
            parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#1f6feb"/>')
        parts.append(f'<text x="{ox+40}" y="{oy+W-30}">predicted p (x) vs observed freq (y)</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ni.RAW_DIR))
    ap.add_argument("--out", default="models/nhl_pregame_v1.json")
    a = ap.parse_args()
    games = ni.load_games(Path(a.root))
    rows = build_rows(games)
    by = lambda lo, hi: [r for r in rows if lo <= r["season_year"] <= hi]
    train, cal, hold = by(0, TRAIN_END), by(CAL_SEASON, CAL_SEASON), by(HOLDOUT, 9999)
    if not train or not cal:
        print("insufficient training/calibration data", file=sys.stderr); return 2
    sel_train, sel_val = by(0, TRAIN_END - 1), by(TRAIN_END, TRAIN_END)
    alpha = min([0.0, 1e-4, 1e-3, 1e-2, 1e-1],
                key=lambda al: poisson_dev(fit_glm(sel_train, al), sel_val))
    glm = fit_glm(train, alpha)
    c = fit_c(train, glm)
    tiny = m.NhlGoalsModel({"glm": glm})
    # tie-break logistic on tied training games: P(home wins tie) vs log(lam_h/lam_a)
    xs, ys = [], []
    for r in train:
        if r["tied"]:
            lh, la = tiny.lambdas(r); xs.append(math.log(lh / la)); ys.append(int(r["home_win"]))
    ta, tb = fit_logit(xs, ys)
    params = {"model_id": m.MODEL_ID, "sport": "NHL", "glm": glm, "glm_alpha": alpha, "glm_features": m.GLM_FEATURES,
              "bivariate_c": c, "tiebreak": {"a": ta, "b": tb},
              "calibration": {"total_scale": 1.0, "platt_a": 0.0, "platt_b": 1.0},
              "split": {"glm_train_through_start_year": TRAIN_END, "calibration_start_year": CAL_SEASON,
                        "holdout_start_year": HOLDOUT, "n_train": len(train), "n_calibration": len(cal)},
              "as_of_rule": "start_time - 1h, projected starter = last start",
              "settlement": "OT/SO winner credited +1 goal; total counts reg+OT goals + SO winner goal"}
    mod = m.NhlGoalsModel(params)
    # --- calibration fold (2024 only)
    pred_tot = sum(sum(mod.lambdas(r)) for r in cal)
    params["calibration"]["total_scale"] = float(sum(r["reg_h"] + r["reg_a"] for r in cal) / pred_tot)
    mod = m.NhlGoalsModel(params)
    xs, ys = [], []
    for r in cal:
        p = min(max(mod.raw_ladder(r)[0].p_home_win(), 1e-6), 1 - 1e-6)
        xs.append(math.log(p / (1 - p))); ys.append(r["home_win"])
    pa, pb = fit_logit(xs, ys)
    params["calibration"].update({"platt_a": pa, "platt_b": pb})
    params["sha256"] = m.artifact_sha256(params)
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(params, sort_keys=True, indent=1))
    frozen, sha = m.load_model(out)
    print("artifact sha256", sha, "alpha", alpha, "c", c, "platt", pa, pb, "scale", params["calibration"]["total_scale"])
    # --- held-out, scored once, after freezing
    if hold:
        res = evaluate(frozen, hold)
        # in-sample reference: climatology = TRAIN base rate (not the holdout's own)
        base = float(np.mean([r["home_win"] for r in train]))
        res["ML_home"]["brier_climatology_train_rate"] = brier([base] * len(hold), [r["home_win"] for r in hold])
        # ADR-0004 baseline: plain LR (+Platt-equivalent) on feature differences, same split
        from sklearn.linear_model import LogisticRegression
        fx = lambda rs: np.array([[r["h_gf_ew"] - r["a_gf_ew"], r["h_ga_ew"] - r["a_ga_ew"], r["h_sf_ew"] - r["a_sf_ew"],
                                   r["h_sa_ew"] - r["a_sa_ew"], r["h_goalie_svp"] - r["a_goalie_svp"],
                                   r["h_b2b"] - r["a_b2b"]] for r in rs])
        lr = LogisticRegression(C=1.0, max_iter=500).fit(fx(train + cal), [r["home_win"] for r in train + cal])
        res["ML_home"]["brier_LR_baseline"] = brier(lr.predict_proba(fx(hold))[:, 1], [r["home_win"] for r in hold])
        md = Path("models/nhl_pregame_v1_heldout_reliability.md")
        lines = [f"# NHL pregame v1 — held-out 2025-26 reliability (model sha256 {sha})", "",
                 "Scored once after freezing; nothing tuned on this season.", "",
                 "| market | n | Brier | climatology Brier (in-sample rate) | ECE |", "|---|---|---|---|---|"]
        for k, v in res.items():
            lines.append(f"| {k} | {v['n']} | {v['brier']:.4f} | {v['brier_climatology_in_sample']:.4f} | {v['ece']:.3f} |")
        lines += ["", f"ML Brier vs TRAIN-rate climatology: {res['ML_home']['brier_climatology_train_rate']:.4f}; "
                  f"LR baseline (ADR-0004): {res['ML_home']['brier_LR_baseline']:.4f}", ""]
        for k in ("ML_home", "TOT_5.5", "PL_home_1.5"):
            lines += [f"## {k} reliability (equal-count deciles)", "", "| mean predicted | observed | n |", "|---|---|---|"]
            lines += [f"| {pm:.3f} | {ym:.3f} | {n} |" for pm, ym, n in res[k]["reliability"]] + [""]
        md.write_text("\n".join(lines))
        Path("models/nhl_pregame_v1_heldout.json").write_text(json.dumps(res, indent=1))
        svg_plot(res, Path("models/nhl_pregame_v1_heldout_reliability.svg"))
        print(md.read_text())
    else:
        print("no 2025 held-out games available yet; held-out evaluation NOT run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
