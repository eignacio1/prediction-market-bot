"""W99.1 Part C: does the tie-odds knob (the only OT/SO-related fitted parameter) matter? merged (fitted tie_odds) vs tie_odds=1.0,
held out 2023-2025, paired Brier per Kalshi family with game-clustered bootstrap CI. Exploratory; merged model unchanged.
Usage: python3 run_w99_1_ot.py <frame.parquet> <out_json>"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src")); sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fence import safe_out
from prediction_market_bot.nhl_engine import model, goals
from run_w97_4 import outcomes, probs, TEST

def main(frame, out):
    fr = pd.read_parquet(frame)
    fr = fr[(fr.game_type == 2) & fr.reg_h.notna() & fr.home_score.notna()].reset_index(drop=True)
    rows, bias = [], {}
    for S in TEST:
        tr = fr[fr.season < S].reset_index(drop=True); te = fr[fr.season == S].reset_index(drop=True)
        m = model.fit(tr, tr.reg_h.to_numpy(), tr.reg_a.to_numpy(), (tr.home_score > tr.away_score).to_numpy())
        lh, la = model.level_adjust(te, *m.rates(te), te.reg_h.to_numpy(), te.reg_a.to_numpy())
        b_m = model.price_games(m, te, n_sim=12000, seed=S, rates=(lh, la))
        m1 = model.Fitted(m.coef, m.k, m.p_home_ot, 1.0)
        b_1 = model.price_games(m1, te, n_sim=12000, seed=S, rates=(lh, la))
        ot, otr = outcomes(te), outcomes(tr)
        p_m, p_1 = probs(b_m), probs(b_1)
        for key in p_m:
            rows.append(pd.DataFrame({"game_id": te.game_id, "season": S, "family": key[0], "y": ot[key], "p_m": p_m[key], "p_1": p_1[key], "p_c": float(otr[key].mean())}))
        act = (te.home_score + te.away_score).to_numpy()
        # expected settled total from the TOTAL ladder is not needed; use mean of simulated totals at 3 strikes' implied mean via sums of ladder
        em = np.array([sum(b["total_over"].values()) for b in b_m]); e1 = np.array([sum(b["total_over"].values()) for b in b_1])
        bias[S] = {"tie_odds": m.tie_odds, "ladder_mass_diff_mean": float((e1 - em).mean())}
    d = pd.concat(rows); rng = np.random.default_rng(0); res = {}
    for fam, x in d.groupby("family"):
        x = x.assign(bm=(x.p_m - x.y) ** 2, b1=(x.p_1 - x.y) ** 2, bc=(x.p_c - x.y) ** 2)
        g = x.groupby("game_id")[["bm", "b1", "bc"]].mean(); diff = (g.b1 - g.bm).to_numpy()
        bs = [rng.choice(diff, len(diff)).mean() for _ in range(2000)]
        res[fam] = {"n_games": len(g), "brier_merged": float(g.bm.mean()), "brier_tie1": float(g.b1.mean()), "brier_clim": float(g.bc.mean()),
                    "tie1_minus_merged": [float(diff.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]}
    o = {"families": res, "by_season": bias}; safe_out(out).write_text(json.dumps(o, indent=1)); print(json.dumps(o, indent=1))

if __name__ == "__main__":
    main(*sys.argv[1:3])
