"""W101.1 Part C: pre-registered spread-shrink challenger vs model_pit (and merged), held out 2023-2025.
Spec: NHL_TOTALS_CHALLENGER_PREREGISTRATION_2026-11-05.md. Usage: python3 run_w101_1.py <frame.parquet> <out_json (relative to 12_EXPLORATORY)>"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src")); sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fence import safe_out
from prediction_market_bot.nhl_engine import model, model_pit, spread_shrink as SS
from run_w97_4 import outcomes, probs, TEST

def main(frame, out):
    fr = pd.read_parquet(frame)
    fr = fr[(fr.game_type == 2) & fr.reg_h.notna() & fr.home_score.notna()].reset_index(drop=True)
    fr = model_pit.with_pit_denominators(fr.sort_values("start").reset_index(drop=True))
    rows, per = [], {}
    for S in TEST:
        tr = fr[fr.season < S].reset_index(drop=True); te = fr[fr.season == S].reset_index(drop=True)
        hw = (tr.home_score > tr.away_score).to_numpy()
        m0 = model.fit(tr, tr.reg_h.to_numpy(), tr.reg_a.to_numpy(), hw); m1 = SS.fit_pit(tr)
        s, mbar, ntr = SS.crossfit_slope(tr, SS.fit_pit)
        r0 = model.level_adjust(te, *m0.rates(te), te.reg_h.to_numpy(), te.reg_a.to_numpy())
        r1 = model.level_adjust(te, *m1.rates(te), te.reg_h.to_numpy(), te.reg_a.to_numpy())
        r2 = SS.challenger_rates(te, m1, mbar, s)
        P = [probs(model.price_games(m, te, n_sim=12000, seed=S, rates=r)) for m, r in ((m0, r0), (m1, r1), (m1, r2))]
        ot = outcomes(te)
        for key in P[0]:
            rows.append(pd.DataFrame({"game_id": te.game_id, "season": S, "family": key[0], "y": ot[key],
                                      "p_merged": P[0][key], "p_pit": P[1][key], "p_chal": P[2][key]}))
        act = (te.reg_h + te.reg_a).to_numpy()
        slope = lambda r: SS.ols_slope(r[0] + r[1], act)
        per[S] = {"n": len(te), "s_used": s, "m_used": mbar, "n_train_for_s": ntr, "actual_reg_total": float(act.mean()),
                  "bias": {k: float((r[0] + r[1]).mean() - act.mean()) for k, r in (("merged", r0), ("pit", r1), ("chal", r2))},
                  "slope_actual_on_pred": {k: slope(r) for k, r in (("merged", r0), ("pit", r1), ("chal", r2))}}
    d = pd.concat(rows); rng = np.random.default_rng(0); fam = {}
    for f, x in d.groupby("family"):
        x = x.assign(bm=(x.p_merged - x.y) ** 2, bp=(x.p_pit - x.y) ** 2, bc=(x.p_chal - x.y) ** 2)
        g = x.groupby("game_id")[["bm", "bp", "bc"]].mean(); n = len(g)
        def ci(diff):
            v = diff.to_numpy(); bs = [rng.choice(v, n).mean() for _ in range(2000)]
            return [float(v.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        fam[f] = {"n_games": n, "brier_merged": float(g.bm.mean()), "brier_pit": float(g.bp.mean()), "brier_chal": float(g.bc.mean()),
                  "chal_minus_pit": ci(g.bc - g.bp), "chal_minus_merged": ci(g.bc - g.bm)}
    allact = pd.concat([fr[fr.season == S] for S in TEST]); pooled = {}
    for k in ("merged", "pit", "chal"):
        pooled[k] = float(np.mean([per[S]["bias"][k] * per[S]["n"] for S in TEST]) * len(TEST) / sum(per[S]["n"] for S in TEST))
    o = {"per_season": per, "pooled_bias": pooled, "families": fam}
    safe_out(out).write_text(json.dumps(o, indent=1)); print(json.dumps(o, indent=1))

if __name__ == "__main__":
    main(*sys.argv[1:3])
