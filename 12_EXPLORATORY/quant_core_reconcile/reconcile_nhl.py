"""W86.1 Part B(1): recompute the 6 PRELIMINARY NHL cells through quant/ and compare with the 2026-10-22 engine output.
Read-only. Usage: reconcile_nhl.py <box_copy_dir> <out_json>   (box_copy_dir holds engine_*.json and data_shadow/nhl/)"""
import json, sys
from pathlib import Path
from prediction_market_bot.pregame_shadow import calibration_engine as ce
from prediction_market_bot.quant import scoring as qs, calibration as qc, inference as qi

box, out = Path(sys.argv[1]), Path(sys.argv[2])
eng = json.loads(next(box.glob("engine_*.json")).read_text())
res = []
for c in eng["cells"]:
    if c["status"] != ce.STATUS_PRELIM:
        continue
    cell = {"cell": c["cell"], "sport": "NHL", "band": c["band"],
            "ledger": box / "data_shadow/nhl" / f"{c['cell']}.jsonl",
            "settled": box / "data_shadow/nhl/settled" / f"{c['cell']}.jsonl"}
    pol = ce.PREREG["NHL"]
    rows = [r for r in ce.first_row_per_unit(ce.load_settled(cell)) if ce.eligible(pol, r)]
    use = set(ce._games_in_order(rows, pol)[:pol.looks[0]])
    rows = [r for r in rows if r["game_key"] in use]
    ps, ms, ys = [r["p_yes"] for r in rows], [r["mid"] for r in rows], [r["y"] for r in rows]
    d = qs.brier_diff(ms, ps, ys)
    by = {}
    for r, v in zip(rows, d):
        by.setdefault(r["game_key"], []).append(v)
    by = {g: [sum(v) / len(v)] for g, v in by.items()}     # EXP-036 per-game mean
    m, lo, hi = qi.cluster_bootstrap(by, 10_000, 20261002)
    mu = qc.murphy(ps, ys)
    e = c["scores"]
    res.append({"cell": c["cell"], "n_rows": [e["n_rows"], len(rows)], "n_games": [e["n_games"], len(by)],
                "brier_model": [e["brier_model"], qs.brier_mean(ps, ys)],
                "brier_market": [e["brier_market"], qs.brier_mean(ms, ys)],
                "logloss_model": [e["logloss_model"], qs.log_loss_mean(ps, ys)],
                "delta_mean": [e["delta_brier_vs_market"]["mean"], m],
                "delta_lo": [e["delta_brier_vs_market"]["ci95"][0], lo],
                "delta_hi": [e["delta_brier_vs_market"]["ci95"][1], hi],
                "murphy_reliability": [e["brier_decomposition"]["reliability"], mu["reliability"]],
                "murphy_resolution": [e["brier_decomposition"]["resolution"], mu["resolution"]],
                "murphy_uncertainty": [e["brier_decomposition"]["uncertainty"], mu["uncertainty"]],
                "ece": [None, qc.ece(ps, ys)], "slope_intercept": [None, list(qc.slope_intercept(ps, ys))]})
out.write_text(json.dumps(res, indent=1))
for r in res:
    print(r["cell"], {k: (v[0], round(v[1], 6) if isinstance(v[1], float) else v[1]) for k, v in r.items() if k != "cell" and v[0] is not None and isinstance(v[1], (int, float))})
