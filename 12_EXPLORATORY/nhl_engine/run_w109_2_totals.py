"""W109.2 Part C: one applied path for NHL TOTALS, end to end, held out 2023-2025.

factor (rest-state split of regulation goals) -> filter (stability gate + min_n) -> tree (depth 3, shift added to the
level-adjusted rates with a training-fit weight) -> price (TOTAL 4.5/5.5/6.5 over, one Poisson/NB simulation).
Also: held-out Brier by tree depth (0..3) for the same TOTAL lines.

Exploratory; no orders, no registry cells. Walk-forward: every fit, the stability gate and the shift weight use seasons
BEFORE the test season only. Scored against results (there is no market price history for 2023-2025: no 'net' exists).
Usage: python3 run_w109_2_totals.py <frame.parquet> <out_json relative to 12_EXPLORATORY>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src")); sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _fence import safe_out  # noqa: E402
from prediction_market_bot.nhl_engine import decision_tree as dt, granularity_index as gi, model, temporal_evolution as te  # noqa: E402
from run_w97_4 import TEST, outcomes, probs  # noqa: E402

LINES = [4.5, 5.5, 6.5]


def _total_p(m, fr, rates, seed):
    return probs(model.price_games(m, fr, n_sim=12000, seed=seed, rates=rates))


def _brier_game(p, o):
    return np.mean([(p[("TOTAL", x)] - o[("TOTAL", x)]) ** 2 for x in LINES], axis=0)


def _ci(v, rng, n_boot=2000):
    v = np.asarray(v, float); n = len(v)
    bs = [rng.choice(v, n).mean() for _ in range(n_boot)]
    return [float(v.mean()), float(np.percentile(bs, 2.5)), float(np.percentile(bs, 97.5))]


def main(frame, out):
    fr = pd.read_parquet(frame)
    fr = fr[(fr.game_type == 2) & fr.reg_h.notna() & fr.home_score.notna()].sort_values("start").reset_index(drop=True)
    tg = gi.team_games(fr)
    sp_gf, sp_ga = gi.asof_split(tg, "gf"), gi.asof_split(tg, "ga")
    cross = gi.game_cross(fr, sp_gf, sp_ga).set_index("game_id")
    rng = np.random.default_rng(0)
    per, rows = {}, []
    for S in TEST:
        tr = fr[fr.season < S].reset_index(drop=True); tst = fr[fr.season == S].reset_index(drop=True)
        hw = (tr.home_score > tr.away_score).to_numpy()
        m = model.fit(tr, tr.reg_h.to_numpy(), tr.reg_a.to_numpy(), hw)
        means = dt.training_means(tr)
        # --- stability gate (training seasons only) and the training-fit shift weight
        st = gi.stability(tg[tg.season < S], "gf")
        stable = bool(st["lo"] > 0)
        ctr = cross.loc[tr.game_id]
        tl = model.level_adjust(tr, *m.rates(tr), tr.reg_h.to_numpy(), tr.reg_a.to_numpy())
        keep_tr = gi.filter_entries(ctr.reset_index(), True, min_n=5.0).game_id
        ix = tr.game_id.isin(keep_tr).to_numpy()
        w = gi.fit_shift_weight(np.concatenate([ctr.shift_h.to_numpy()[ix], ctr.shift_a.to_numpy()[ix]]),
                                np.concatenate([(tr.reg_h.to_numpy() - tl[0])[ix], (tr.reg_a.to_numpy() - tl[1])[ix]]))
        # --- test: tree depth ladder (all level-adjusted point-in-time) and the applied path
        o = outcomes(tst); res = {"game_id": tst.game_id.to_numpy(), "season": S}
        for d in range(4):
            r = model.level_adjust(tst, *dt.rates_at_depth(m, tst, d, means), tst.reg_h.to_numpy(), tst.reg_a.to_numpy())
            res[f"d{d}"] = _brier_game(_total_p(m, tst, r, S), o)
            if d == 3:
                base_r = r
        cte = cross.loc[tst.game_id]
        passed = gi.filter_entries(cte.reset_index(), stable, min_n=5.0).game_id
        pm = tst.game_id.isin(passed).to_numpy()
        sh_h = np.where(pm, cte.shift_h.to_numpy(), 0.0); sh_a = np.where(pm, cte.shift_a.to_numpy(), 0.0)
        ar = gi.apply_shift(base_r[0], base_r[1], sh_h, sh_a, w)
        res["applied"] = _brier_game(_total_p(m, tst, ar, S), o)
        pu = gi.filter_entries(cte.reset_index(), True, min_n=5.0).game_id   # gate forced open: what the gate protects against
        pmu = tst.game_id.isin(pu).to_numpy()
        ur = gi.apply_shift(base_r[0], base_r[1], np.where(pmu, cte.shift_h.to_numpy(), 0.0), np.where(pmu, cte.shift_a.to_numpy(), 0.0), w)
        res["ungated"] = _brier_game(_total_p(m, tst, ur, S), o)
        act = (tst.reg_h + tst.reg_a).to_numpy()
        per[S] = {"n": len(tst), "stable_gate": stable, "stability": st, "shift_weight": w, "share_games_shifted": float(pm.mean()),
                  "bias_base": float((base_r[0] + base_r[1]).mean() - act.mean()),
                  "bias_applied": float((ar[0] + ar[1]).mean() - act.mean())}
        rows.append(pd.DataFrame(res))
    d = pd.concat(rows, ignore_index=True)
    o = {"per_season": per, "n_games": int(len(d)),
         "brier_total_by_depth": {f"d{k}": float(d[f"d{k}"].mean()) for k in range(4)},
         "depth_step": {f"d{k}_minus_d{k-1}": _ci((d[f"d{k}"] - d[f"d{k-1}"]).to_numpy(), rng) for k in range(1, 4)},
         "applied_brier": float(d.applied.mean()), "base_brier": float(d.d3.mean()),
         "applied_minus_base": _ci((d.applied - d.d3).to_numpy(), rng),
         "ungated_brier": float(d.ungated.mean()), "ungated_minus_base": _ci((d.ungated - d.d3).to_numpy(), rng),
         "market_comparison": "unavailable: no market price history for 2023-2025; no 'net' computed (engine-vs-Kalshi n=33 games is W99.1)"}
    # temporal evolution on the same data (cross-season stability of the regulation-goal level)
    for met in ("gf",):
        lg = te.team_game_long(tg[tg.season.isin([2022, 2023, 2024, 2025])], met)
        o[f"temporal_{met}"] = {"within_season_slope": te.within_season_slope(lg),
                                "reliability_gap": te.reliability_gap(lg),
                                "blend_weight": te.nhl_blend_weight(lg)}
    safe_out(out).write_text(json.dumps(o, indent=1, default=float)); print(json.dumps(o, indent=1, default=float))


if __name__ == "__main__":
    main(*sys.argv[1:3])
