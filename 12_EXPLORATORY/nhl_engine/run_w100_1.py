"""W100.1 Part A: merged model vs same-vintage-denominator model (model_pit), held out 2023-2025.
Paired Brier per Kalshi family, game-clustered bootstrap; regulation-total bias after level_adjust. Exploratory; merged model unchanged.
Usage: python3 run_w100_1.py <frame.parquet> <out_json>"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src")); sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fence import safe_out
from prediction_market_bot.nhl_engine import model, model_pit
from run_w97_4 import outcomes, probs, TEST

def main(frame, out):
    fr = pd.read_parquet(frame)
    fr = fr[(fr.game_type == 2) & fr.reg_h.notna() & fr.home_score.notna()].reset_index(drop=True)
    fr = model_pit.with_pit_denominators(fr.sort_values("start").reset_index(drop=True))   # trailing-only: leak-free on the whole frame
    rows, bias = [], {}
    for S in TEST:
        tr = fr[fr.season < S].reset_index(drop=True); te = fr[fr.season == S].reset_index(drop=True)
        hw = (tr.home_score > tr.away_score).to_numpy()
        m0 = model.fit(tr, tr.reg_h.to_numpy(), tr.reg_a.to_numpy(), hw)
        m1 = model_pit.fit_pit(tr, tr.reg_h.to_numpy(), tr.reg_a.to_numpy(), hw)
        r0 = model.level_adjust(te, *m0.rates(te), te.reg_h.to_numpy(), te.reg_a.to_numpy())
        r1 = model.level_adjust(te, *m1.rates(te), te.reg_h.to_numpy(), te.reg_a.to_numpy())
        b0 = model.price_games(m0, te, n_sim=12000, seed=S, rates=r0); b1 = model.price_games(m1, te, n_sim=12000, seed=S, rates=r1)
        ot, otr = outcomes(te), outcomes(tr); p0, p1 = probs(b0), probs(b1)
        for key in p0:
            rows.append(pd.DataFrame({"game_id": te.game_id, "season": S, "family": key[0], "y": ot[key], "p_0": p0[key], "p_1": p1[key], "p_c": float(otr[key].mean())}))
        act = (te.reg_h + te.reg_a).to_numpy()
        bias[S] = {"n": len(te), "actual_reg_total": float(act.mean()),
                   "bias_merged": float((r0[0] + r0[1]).mean() - act.mean()), "bias_pit": float((r1[0] + r1[1]).mean() - act.mean())}
    d = pd.concat(rows); rng = np.random.default_rng(0); res = {}
    for fam, x in d.groupby("family"):
        x = x.assign(b0=(x.p_0 - x.y) ** 2, b1=(x.p_1 - x.y) ** 2, bc=(x.p_c - x.y) ** 2)
        g = x.groupby("game_id")[["b0", "b1", "bc"]].mean(); diff = (g.b1 - g.b0).to_numpy()
        bs = [rng.choice(diff, len(diff)).mean() for _ in range(2000)]
        res[fam] = {"n_games": len(g), "brier_merged": float(g.b0.mean()), "brier_pit": float(g.b1.mean()), "brier_clim": float(g.bc.mean()),
                    "pit_minus_merged": [float(diff.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}
    o = {"families": res, "bias_by_season": bias}; safe_out(out).write_text(json.dumps(o, indent=1)); print(json.dumps(o, indent=1))

if __name__ == "__main__":
    main(*sys.argv[1:3])
