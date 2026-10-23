"""W86.2 Part A: market-implied margin/total distribution per game from shadow-ledger ladders.

usage: python part_a.py <shadow_dir> <out_dir>
Reads PREGAME_SHADOW jsonl copies (read-only); writes CSV/JSON under 12_EXPLORATORY/ via safe_out.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import ladder as L  # noqa: E402
from _fence import safe_out  # noqa: E402

MARKETS = {  # file stem -> (sport, kind)
    "NFL_NFL_SPREAD": ("NFL", "margin"), "NFL_NFL_GAME_TOTAL": ("NFL", "total"),
    "NBA_NBA_SPREAD": ("NBA", "margin"), "NBA_NBA_GAME_TOTAL": ("NBA", "total"),
    "MLB_MLB_RUN_LINE": ("MLB", "margin"), "MLB_MLB_GAME_TOTAL": ("MLB", "total"),
}
FIXED = {("NFL", "margin"): 13.2, ("NFL", "total"): 12.8, ("NBA", "total"): 18.5,
         ("MLB", "margin"): 4.4}  # operator-quoted fixed widths (prompt); others not stated
W_GRID = [1.0, 1.15, 1.3, 1.45, 1.6]


def load(shadow_dir: Path):
    out = []
    for stem, (sport, kind) in MARKETS.items():
        for band in ("T1", "T2", "T3"):
            f = shadow_dir / f"{stem}_{band}.jsonl"
            if not f.exists():
                continue
            groups = defaultdict(list)
            for line in open(f):
                r = json.loads(line)
                groups[(r["event_ticker"], r["run_id"])].append(r)
            for (ev, run), rows in groups.items():
                mk = [{"ticker": r["market_ticker"], "bid": r["yes_bid"], "ask": r["yes_ask"]} for r in rows]
                md = [{"ticker": r["market_ticker"], "bid": r["p_yes"], "ask": r["p_yes"]} for r in rows]
                out.append({"sport": sport, "kind": kind, "band": band, "event": ev, "run": run,
                            "h": rows[0]["horizon_hours_to_start"], "rows": rows, "mk": mk, "md": md,
                            "model_id": rows[0]["model_id"]})
    return out


def main(shadow_dir, out_dir):
    snaps = load(Path(shadow_dir))
    res = []
    for s in snaps:
        pk = L.survival_points(s["mk"], s["kind"]); pm = L.survival_points(s["md"], s["kind"])
        fk, fm = L.fit_normal(pk), L.fit_normal(pm)
        if fk is None:
            continue
        rec = {"sport": s["sport"], "kind": s["kind"], "band": s["band"], "event": s["event"], "run": s["run"],
               "h": s["h"], "mu_k": fk["mu"], "sig_k": fk["sigma"], "n_k": fk["n"], "rmse_k": fk["rmse"],
               "mu_m": fm["mu"] if fm else None, "sig_m": fm["sigma"] if fm else None}
        # decomposition on each strike row (shared ordering with rows)
        if fm:
            x = []; pmod = []; mid = []; edge = []
            for r in s["rows"]:
                ev_, team, k = L.parse_ticker(r["market_ticker"])
                teams = sorted({L.parse_ticker(q["market_ticker"])[1] for q in s["rows"]})
                flip = s["kind"] == "margin" and team != teams[0]
                xi = -k if flip else k
                py = 1 - r["p_yes"] if flip else r["p_yes"]; mi = 1 - r["mid"] if flip else r["mid"]
                if not (0.03 <= mi <= 0.97):
                    continue
                x.append(xi); pmod.append(py); mid.append(mi)
                # edge direction in survival space: YES edge on a flipped contract is an edge on 1-S
                edge.append((max(r["e_net_yes_k007"], r["e_net_no_k007"]), 1 if r["e_net_yes_k007"] >= r["e_net_no_k007"] else -1, -1 if flip else 1))
            if len(x) >= 3:
                d = L.decompose(np.array(x), np.array(pmod), np.array(mid), fm, fk)
                rec["dec_n"] = len(x)
                rec["abs_center"] = float(np.mean(np.abs(d["center"]))); rec["abs_width"] = float(np.mean(np.abs(d["width"])))
                rec["abs_resid"] = float(np.mean(np.abs(d["residual"])))
                rec["abs_delta"] = float(np.mean(np.abs(np.array(pmod) - np.array(mid))))
                # edges: rows with positive best net edge; counterfactual removes the width term
                pos = [i for i, (e, _, _f) in enumerate(edge) if e > 0]
                rec["n_edge_rows"] = len(pos)
                surv = 0; sum_e = 0.0; sum_e_w = 0.0
                for i in pos:
                    e, sgn, fl = edge[i]
                    w = d["width_only"][i]   # P_m - D, model-centre/market-width counterfactual shift
                    # w is in survival space; original-contract probability moves by fl*w (fl=-1 on flipped contracts).
                    # YES leg (sgn=+1) loses fl*w of edge, NO leg (sgn=-1) gains it.
                    e_cf = e - sgn * fl * w
                    sum_e += e; sum_e_w += e - e_cf
                    surv += int(e_cf > 0)
                rec["edge_rows_surviving_if_market_width"] = surv
                rec["sum_edge"] = sum_e; rec["sum_edge_from_width"] = sum_e_w
        # key-number NFL margin: fit on market and model ladders at grid weights
        res.append(rec)
    out = safe_out(Path(out_dir) / "part_a_snapshots.json")
    json.dump(res, open(out, "w"))
    print(len(res), "fitted snapshots ->", out)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
