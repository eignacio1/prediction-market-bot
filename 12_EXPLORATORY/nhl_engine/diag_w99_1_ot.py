"""W99.1 Part C diagnostic: where does the merged model's totals bias live - regulation goals, tie rate, or OT/SO credit?
Exploratory. Usage: python3 diag_w99_1_ot.py <frame.parquet> <out_json>"""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src")); sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out
from prediction_market_bot.nhl_engine import model, goals

def main(frame, out):
    fr = pd.read_parquet(frame)
    fr = fr[(fr.game_type == 2) & fr.reg_h.notna() & fr.home_score.notna()].reset_index(drop=True)
    res = {}
    for S in (2023, 2024, 2025):
        tr = fr[fr.season < S].reset_index(drop=True); te = fr[fr.season == S].reset_index(drop=True)
        m = model.fit(tr, tr.reg_h.to_numpy(), tr.reg_a.to_numpy(), (tr.home_score > tr.away_score).to_numpy())
        lh, la = model.level_adjust(te, *m.rates(te), te.reg_h.to_numpy(), te.reg_a.to_numpy())
        reg, tie, settled, hot = [], [], [], []
        for i, (h, a) in enumerate(zip(lh, la)):
            s = goals.simulate(float(h), float(a), m.k, m.p_home_ot, 8000, S + i, m.tie_odds)
            reg.append(float(np.mean(s.reg_home + s.reg_away))); tie.append(float(np.mean(s.reg_home == s.reg_away)))
            settled.append(float(np.mean(s.home + s.away)))
        reg, tie, settled = map(np.array, (reg, tie, settled))
        ar = (te.reg_h + te.reg_a).to_numpy(); at = (te.reg_h == te.reg_a).to_numpy(); ast = (te.home_score + te.away_score).to_numpy()
        tg = te[at]; hw = float((tg.home_score > tg.away_score).mean())
        res[S] = {"n": len(te), "bias_settled": float(settled.mean() - ast.mean()), "bias_reg_total": float(reg.mean() - ar.mean()),
                  "pred_tie": float(tie.mean()), "act_tie": float(at.mean()), "bias_tie_credit": float(tie.mean() - at.mean()),
                  "k": float(m.k), "tie_odds": float(m.tie_odds), "p_home_ot_fit": float(m.p_home_ot), "p_home_ot_test": hw,
                  "n_ties_test": int(at.sum())}
    safe_out(out).write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))

if __name__ == "__main__":
    main(*sys.argv[1:3])
