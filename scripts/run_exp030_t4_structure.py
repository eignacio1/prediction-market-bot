#!/usr/bin/env python3
"""EXP-030 (T-598) runner. Two stages; the validate stage never loads holdout dates.
    --stage validate : select C on validation + permutation control (dates < CUTOFF only)
    --stage holdout  : run T-583's unmodified run_gate ONCE (requires --c from the validate stage)
Pre-registration: 05_RESEARCH_EXPERIMENTS/EXP030_T4_STRUCTURE_PREREGISTRATION_2026-09-30.md
"""
import argparse, json, sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ab_harness_t4 as H  # noqa: E402
from prediction_market_bot.c3_forecasting import t4_structure_model as M  # noqa: E402
from prediction_market_bot.c5_execution.market_type_registry import derive_game_date  # noqa: E402
from prediction_market_bot.logic_epoch import epoch_for_timestamp  # noqa: E402
from prediction_market_bot.run_t4_mlb_live import p_hits_gte_threshold as incumbent  # noqa: E402

START, VAL_START, CUTOFF, END = "2026-07-18", "2026-07-22", "2026-07-25", "2026-07-30"
HYPOTHESIS = ("EXP-030: residual-logit structure over the incumbent improves paired Brier on the sealed "
              "holdout 2026-07-25..07-30 (pre-registered 2026-09-30)")


def load_rows(data_dir: Path, holdout: bool) -> list:
    out = {}
    for f in ("outcome_T421.jsonl", "outcome_T503.jsonl"):
        for line in open(data_dir / f):
            r = json.loads(line)
            if r.get("resolved"):
                out[r["ticker"]] = r
    man = set(json.load(open(H.MANIFEST_PATH))["tickers"])
    hi = END if holdout else "2026-07-24"
    rows = []
    for line in open(data_dir / "cycle.jsonl"):
        r = json.loads(line)
        t = r["ticker"]
        d = derive_game_date(t)
        if not (START <= d <= hi) or t in man or t not in out:
            continue
        if r.get("ba_l10_shrunk") is None or r.get("ab_remaining") is None:
            continue
        p = incumbent(r["h_so_far"], r["threshold"], r["ba_l10_shrunk"], r["ab_remaining"])
        if not (0 < p < 1):
            continue
        o = out[t]
        rows.append({**r, "game_date": d, "game_id": t.split("-")[1], "p_incumbent": p,
                     "outcome": int(o["actual_hits"] >= r["threshold"]),
                     "resolution_source": "boxscore_rederived", "cohort_band": "T4M-PROJ",
                     "logic_epoch": epoch_for_timestamp(r["ts"])})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=("validate", "holdout"), required=True)
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--c", type=float)
    a = ap.parse_args()
    if a.stage == "validate":
        rows = load_rows(a.data_dir, holdout=False)
        tr = [r for r in rows if r["game_date"] < VAL_START]
        va = [r for r in rows if r["game_date"] >= VAL_START]
        C, gains = M.select_c(tr, va)
        perm = M.permutation_control(tr, va, C)
        real = gains[C]
        print(json.dumps({"n_train_rows": len(tr), "n_val_rows": len(va), "val_gain_by_C": gains,
                          "chosen_C": C, "real_val_gain": real,
                          "perm_p95": float(np.percentile(perm, 95)), "perm_mean": float(perm.mean()),
                          "perm_frac_ge_real": float((perm >= real).mean()),
                          "passes_control": bool(real > np.percentile(perm, 95))}, indent=1))
    else:
        if a.c is None or a.c not in M.C_GRID:
            sys.exit("--c must be the C chosen in the validate stage")
        rows = load_rows(a.data_dir, holdout=True)
        try:
            res = H.run_gate(rows, M.make_candidate(CUTOFF, a.c), cutoff=CUTOFF, hypothesis=HYPOTHESIS)
            print(json.dumps(res, indent=1, default=float))
        except H.T4HarnessRefusal as e:
            print(f"HARNESS REFUSAL {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
