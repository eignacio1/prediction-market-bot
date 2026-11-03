"""W98.1 Part B: NHL engine v2 (end-of-game state model) vs the merged model, held out 2023-2025. Exploratory.
Usage: python3 run_w98_1.py <frame.parquet> <late_table.parquet> <out_dir>"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src")); sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fence import safe_out
from prediction_market_bot.nhl_engine import model, goals
from prediction_market_bot.nhl_engine import late_game as LG
from run_w97_4 import outcomes, probs, TEST

def board_v2(s):
    return goals.price_board(s)

def main(frame, late, out):
    fr = pd.read_parquet(frame); lt = pd.read_parquet(late).drop(columns=["season", "reg_h", "reg_a"])
    fr = fr[(fr.game_type == 2) & fr.reg_h.notna() & fr.home_score.notna()].merge(lt, on="game_id").reset_index(drop=True)
    rows, summ, EXP = [], {}, []
    for S in TEST:
        tr = fr[fr.season < S].reset_index(drop=True); te = fr[fr.season == S].reset_index(drop=True)
        hw = (tr.home_score > tr.away_score).to_numpy()
        m = model.fit(tr, tr.reg_h.to_numpy(), tr.reg_a.to_numpy(), hw)
        trh, tra = m.rates(tr)
        base = LG.fit_late(tr, trh, tra); lam_bar = float(np.mean(np.r_[trh, tra])); ES = LG.early_scale(tr)
        lh, la = model.level_adjust(te, *m.rates(te), te.reg_h.to_numpy(), te.reg_a.to_numpy())
        b1 = model.price_games(m, te, n_sim=20000, seed=S, rates=(lh, la))
        b2 = [goals.price_board(goals.__dict__.get("_x", None) or LG.simulate_v2(float(h), float(a), base, lam_bar, m.k, m.p_home_ot, 20000, S + i, m.tie_odds, ES))
              for i, (h, a) in enumerate(zip(lh, la))]
        ot, otr = outcomes(te), outcomes(tr)
        # expected total goals per game from the same samples (bias): re-simulate cheaply with fewer sims
        e1 = np.array([float(np.mean(goals.simulate(float(h), float(a), m.k, m.p_home_ot, 4000, S + i, m.tie_odds).home + goals.simulate(float(h), float(a), m.k, m.p_home_ot, 4000, S + i, m.tie_odds).away)) for i, (h, a) in enumerate(zip(lh, la))])
        e2 = np.array([float(np.mean((lambda s: s.home + s.away)(LG.simulate_v2(float(h), float(a), base, lam_bar, m.k, m.p_home_ot, 4000, S + i, m.tie_odds, ES)))) for i, (h, a) in enumerate(zip(lh, la))])
        act = (te.home_score + te.away_score).to_numpy()
        summ[S] = {"n": len(te), "bias_merged": float(e1.mean() - act.mean()), "bias_v2": float(e2.mean() - act.mean()),
                   "base_late": base.round(4).tolist(), "early_scale": ES}
        p1, p2 = probs(b1), probs(b2)
        for key in p1:
            y = ot[key]; clim = float(otr[key].mean())
            rows.append(pd.DataFrame({"game_id": te.game_id, "season": S, "family": key[0], "strike": key[1] if key[1] is not None else np.nan,
                                      "y": y, "p_merged": p1[key], "p_v2": p2[key], "p_clim": clim}))
    d = pd.concat(rows); d.to_parquet(safe_out(Path(out) / "w98_1_heldout.parquet"))
    rng = np.random.default_rng(0); res = {}
    for fam, x in d.groupby("family"):
        x = x.assign(b_m=(x.p_merged - x.y) ** 2, b_v=(x.p_v2 - x.y) ** 2, b_c=(x.p_clim - x.y) ** 2)
        g = x.groupby("game_id")[["b_m", "b_v", "b_c"]].mean()
        def ci(a, b):
            diff = (g[a] - g[b]).to_numpy(); bs = [rng.choice(diff, len(diff)).mean() for _ in range(2000)]
            return [float(diff.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]
        res[fam] = {"n_games": len(g), "brier_merged": float(g.b_m.mean()), "brier_v2": float(g.b_v.mean()), "brier_clim": float(g.b_c.mean()),
                    "v2_minus_merged": ci("b_v", "b_m"), "v2_minus_clim": ci("b_v", "b_c")}
    summ["families"] = res
    safe_out(Path(out) / "w98_1_summary.json").write_text(json.dumps(summ, indent=1))
    print(json.dumps(summ, indent=1))

if __name__ == "__main__":
    main(*sys.argv[1:4])
