"""EXP-029 runner. Stages: controls (D4, train->validation only) | gate (D3, ONE-SHOT, lock file) + D5.
Implements 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/EXP029_market_gate_PREREGISTRATION_2026-09-30.md.
Run from worktree root with PYTHONPATH=src."""
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "src"); sys.path.insert(0, "scripts")
from prediction_market_bot.c3_forecasting import pregame_hits_model as M
import ab_harness_t4 as H

OUT = Path("exp_output/EXP-029"); stage = sys.argv[1]
C = 10.0                                    # frozen (EXP-028 validation_results.json chosen_C)
df = M.load_population(Path("exp_output/MLB/mlb_feature_matrix.csv"), verify_sha=False)
tr = M.split(df, M.TRAIN); va = M.split(df, M.VALIDATION)
trva = df[(df.game_date >= M.TRAIN[0]) & (df.game_date <= M.VALIDATION[1])]

if stage == "controls":
    res = {"n_train": len(tr), "n_val": len(va)}
    # D4.1 placebo drawn from the SAME filtered population: shift(11) over the filtered per-player sequence
    df = df.sort_values(["player_id", "game_date", "game_id"]).reset_index(drop=True)
    df["y_back_post"] = df.groupby("player_id", sort=False)["y"].shift(M.PLACEBO_LAG)
    va = M.split(df, M.VALIDATION)
    mod = M.PregameHitsModel(C).fit(M.split(df, M.TRAIN))
    p = mod.predict(va); b0 = np.full(len(va), M.split(df, M.TRAIN)["y"].mean())
    fwd = M.paired_delta(b0, p, va["y"].values, va["game_id"].values)
    ok = va["y_back_post"].notna().values; vb = va[ok]
    bwd = M.paired_delta(b0[ok], p[ok], vb["y_back_post"].values, vb["game_id"].values)
    res["forward_vs_B0_validation"] = fwd; res["placebo_backward_postfilter_vs_B0_validation"] = bwd
    fm, bm = fwd["delta_brier"]["mean"], bwd["delta_brier"]["mean"]
    res["placebo_ratio_backward_over_forward"] = bm / fm if fm else None
    # D4.2 permutation null, one-sided criterion (leak only if CI entirely above 0; also |mean|<0.001)
    trp = M.split(df, M.TRAIN).copy(); trp["y"] = M.permute_within_date(trp)
    vap = va.copy(); vap["y"] = M.permute_within_date(va)
    pp = M.PregameHitsModel(C).fit(trp).predict(vap)
    pb = np.full(len(vap), trp["y"].mean())
    perm = M.paired_delta(pb, pp, vap["y"].values, vap["game_id"].values)
    b = perm["delta_brier"]
    perm["leak_declared"] = bool(b["ci_low"] > 0 or abs(b["mean"]) >= 0.001)
    res["permutation_null_onesided"] = perm
    (OUT / "controls_results.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))

elif stage == "gate":
    lock = OUT / "PRICED_WINDOW_SCORED.lock"
    if lock.exists(): sys.exit("priced window already scored; refusing")
    lock.write_text("scored\n")
    mod = M.PregameHitsModel(C).fit(trva)
    rows = [json.loads(l) for l in open(OUT / "joined.jsonl")]
    pm = mod.predict(df.iloc[[r["pop_idx"] for r in rows]])
    pred = {r["ticker"]: float(p) for r, p in zip(rows, pm)}
    res = H.run_gate(rows, lambda train: (lambda r: pred[r["ticker"]]), cutoff="2026-09-01",
                     hypothesis="EXP-029 pre-registered: frozen EXP-028 model (C=10, fit 2024-25) vs "
                                "Kalshi KXMLBHIT pre-first-pitch mid; game-clustered paired dBrier.")
    test = [r for r in rows if r["game_date"] >= "2026-09-01"]
    y = np.array([r["outcome"] for r in test]); pi = np.array([r["p_incumbent"] for r in test])
    pc = np.array([pred[r["ticker"]] for r in test]); g = np.array([r["game_id"] for r in test])
    d = (pi - y) ** 2 - (pc - y) ** 2
    res["brier_market"] = float(np.mean((pi - y) ** 2)); res["brier_model"] = float(np.mean((pc - y) ** 2))
    res["base_rate"] = float(y.mean()); res["mean_p_market"] = float(pi.mean()); res["mean_p_model"] = float(pc.mean())
    res["harness_verdict_label"] = res["verdict"] if res["verdict"] != "INCONCLUSIVE" else "NO DETECTABLE DIFFERENCE"
    # D5: required n, clustered SE
    mean = d.mean(); N = len(d)
    S = pd.Series(d - mean).groupby(g).sum()
    se = float(np.sqrt((S ** 2).sum()) / N)
    ng = len(S)
    res["d5"] = {"delta_mean": float(mean), "se_clustered": se, "n_rows": N, "n_games": ng}
    for name, z in (("80pct_power_alpha05_onesided", 1.645 + 0.8416), ("95pct_power_alpha05_onesided", 1.645 + 1.645)):
        if mean > 0:
            ratio = (se * z / mean) ** 2
            res["d5"][name] = {"rows_needed": float(N * ratio), "games_needed": float(ng * ratio),
                               "multiple_of_current": float(ratio)}
        else:
            res["d5"][name] = "delta_mean <= 0: no positive edge to power for"
    (OUT / "gate_results.json").write_text(json.dumps(res, indent=1, default=float))
    print(json.dumps(res, indent=1, default=float))
