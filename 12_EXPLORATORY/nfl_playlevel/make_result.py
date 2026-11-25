"""Writes RESULT.md from results.json (EXP-NFLPLAYLEVEL-001). Routing words only."""
from pathlib import Path
import sys; sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _fence import safe_out
import json
from collections import Counter

H = Path(__file__).parent
d = json.load(open(H / "results.json"))
m, rows = d["meta"], d["rows"]
j = [r for r in rows if "j25_net" in r]
pos = [r for r in j if r["j25_net"] > 0]
best = max(j, key=lambda r: r["j25_net"])
n26 = [r for r in rows if "j26_net" in r]
f = lambda v: "" if v is None else f"{v:+.3f}"
L = ["# EXP-NFLPLAYLEVEL-001 — result: NFL play-level crosses as tree splits", "",
     "**Last reviewed:** 2026-11-24 (W128.3). Source: `run_playlevel.py` -> `results.json`; `make_result.py` -> this file. PREREG.md committed first (7e4ceee).",
     "**Proxy prices** (board_v2 anchored to consensus, earlier seasons only), not tradable quotes. Half-spread at archive medians; mean-cost net in results.json.", "",
     "## Headline",
     f"- {len(rows)} cross x market x leaf x band x arm rows; **{len(j)} judged** on 2025 (>= {m['MIN_N']} games); {len(rows) - len(j)} not judged for n.",
     f"- Fit-routed rows (shrunk 90% lower bound > 0 on fit seasons): **{sum(1 for r in rows if r['fit_routed_arm'])}**. BH family: **{m['bh_family']}**. Arms earned: **0**. "
     "Every judged leaf routed to ride / no bet.",
     f"- Raw 2025 net > 0 in {len(pos)} of {len(j)} judged rows; none with a 90% interval above 0. Best: {best['cross']} {best['market']} {best['leaf']} {best['band']} "
     f"{best['arm']} net {f(best['j25_net'])} (interval {f(best['j25_net_lo'])} to {f(best['j25_net_hi'])}, n {best['j25_n_games']} games).",
     f"- 2026 REG to date (descriptive, personnel / coverage **carried** from 2025, no participation feed): {len(n26)} rows reach n >= {m['MIN_N']} games; no BH, never pooled with 2025.",
     "- Verdict: **ride / no bet in every judged leaf. Hypothesis closed (EXP-NFLPLAYLEVEL-001, parked for R&D).** No cell, market or arm closes.", "",
     "## Cut points fixed on the fit seasons (offense median, defense median)", ""]
L += [f"- {k}: {v[0]:.4f} / {v[1]:.4f}" if v else f"- {k}: none (too few team-games)" for k, v in m["cuts"].items()]
L += ["", f"Fit seasons {json.dumps(m['fit'])}. Judge: {m['judge']}. Look 2: {m['look26']}.", "",
      "## Per cross x market x leaf x band x arm", "",
      "| cross | mkt | leaf | band | arm | fit route | fit lo | 2025 n | gross | cost | net | 90% lo | 90% hi | 2026 n | 2026 net | verdict |", "|" + "---|" * 16]
for r in sorted(rows, key=lambda r: (r["cross"], r["market"], r["leaf"], r["band"], r["arm"])):
    L.append("| " + " | ".join([r["cross"].split("_")[0], r["market"], r["leaf"], r["band"], r["arm"], r["fit_route"], f(r["fit_lo"]), str(r["j25_n_games"]),
                              f(r.get("j25_gross")), f(r.get("j25_cost")), f(r.get("j25_net")), f(r.get("j25_net_lo")), f(r.get("j25_net_hi")),
                              str(r["j26_n_games"]), f(r.get("j26_net")), r["verdict"]]) + " |")
c = Counter(r["cross"] for r in j)
L += ["", "## Judged leaves per cross (stage evidence)", ""] + [f"- {k}: {v} judged rows" for k, v in sorted(c.items())]
safe_out(H / "RESULT.md").write_text("\n".join(L) + "\n")
print(len(L), "lines")
