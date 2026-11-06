"""W105.1 Part A: plan power and calendar dates from power_nba.json.  usage: run_calendar.py <power_nba.json> <out.md>"""
from __future__ import annotations

import datetime as dt
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parent)]
from _fence import safe_out  # noqa: E402
from prediction_market_bot.quant import blend_power as bp  # noqa: E402

START = dt.date(2026, 11, 5)
NIGHTS = {"7/night": 7.0, "9/night": 9.0, "12/night": 12.0}
NMAX = {"v1": 400, "v2": 400, "v3": 100}
FR = [0.25, 0.5, 0.75, 1.0]


def main(src, out):
    d = json.load(open(src))
    lines = ["| cell | cov | n so far | n_max | power w=.25 | power w=.5 | look dates @ 9/night |", "|---|---|---|---|---|---|---|"]
    bnd = bp.gs_boundaries(FR, 0.05)
    plan = []
    for c in d["cells"]:
        nm = NMAX[c["engine"]]
        pw = {}
        for w in ("w0.25", "w0.5"):
            th = c[w]["mu"] * math.sqrt(nm) / c[w]["sigma"]
            pw[w] = bp.gs_power(FR, bnd, th)
        rate = 9.0 * c["coverage_of_finals"]
        dates = []
        for f in FR:
            need = max(0.0, f * nm - c["n_games"])
            dates.append((START + dt.timedelta(days=math.ceil(need / rate))).isoformat())
        plan.append({"engine": c["engine"], "family": c["family"], "n_max": nm, "power_w25": pw["w0.25"],
                     "power_w50": pw["w0.5"], "dates_9": dates, "coverage": c["coverage_of_finals"]})
        lines.append(f"| {c['engine']} {c['family']} | {c['coverage_of_finals']:.2f} | {c['n_games']} | {nm} | "
                     f"{pw['w0.25']:.2f} | {pw['w0.5']:.2f} | {' / '.join(x[5:] for x in dates)} |")
    open(safe_out(out), "w").write("\n".join(lines) + "\n\nboundaries (z, one-sided, 4 looks OBF): "
                                   + ", ".join(f"{b:.3f}" for b in bnd) + "\n")
    json.dump(plan, open(safe_out(out.replace(".md", ".json")), "w"), indent=1)
    print("\n".join(lines))


if __name__ == "__main__":
    main(*sys.argv[1:3])
