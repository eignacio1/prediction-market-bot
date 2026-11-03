#!/usr/bin/env python3
"""W98.2 Part A: READ-ONLY. Prints the released first-look verdicts from a saved calibration-engine JSON.

Reads one engine_<UTC>.json (default: the latest in exp_output/CALIBRATION) and prints, per cell that carries a
released `verdict`, the fields the engine already wrote: n, delta-Brier vs market and vs climatology with 95% CIs,
the verdict and its rule, E_net, the release digest, and the next-look projection. It never re-scores, never reads a
ledger, writes nothing, and prints nothing for a sealed or counts-only cell (those carry no score keys).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def latest_engine_json(d: Path) -> Path | None:
    files = sorted(d.glob("engine_*.json"))
    return files[-1] if files else None


def _ci(d) -> str:
    if not isinstance(d, dict):
        return "unavailable"
    lo, hi = d["ci95"]
    return f"{d['mean']:+.4f} [{lo:+.4f}, {hi:+.4f}]"


def released(res: dict) -> list[dict]:
    return [c for c in res.get("cells", []) if c.get("verdict") and c.get("release")]


def render(res: dict, src: str) -> str:
    cells = released(res)
    L = [f"engine file: {src}  generated: {res.get('generated')}", f"summary: {json.dumps(res.get('summary'))}",
         f"cells with a released verdict: {len(cells)} of {len(res.get('cells', []))}", ""]
    L.append("cell | n | d-Brier vs market [95% CI] | d-Brier vs climatology [95% CI] | verdict | next look")
    tally: dict[str, int] = {}
    for c in cells:
        v = c["verdict"]
        tally[v["verdict"]] = tally.get(v["verdict"], 0) + 1
        pj = c.get("projection") or {}
        nxt = pj.get("date") or pj.get("note") or "-"
        flag = "  [MODEL WORSE THAN CLIMATOLOGY]" if v.get("model_failure_vs_climatology") else ""
        L.append(f"{c['cell']} | {v['n']} | {_ci(v['delta_brier_vs_market'])} | {_ci(v['delta_brier_vs_climatology'])} | "
                 f"{v['verdict']}{flag} | {nxt}")
    L += ["", f"tally: {json.dumps(tally, sort_keys=True)}", ""]
    for c in cells:
        v = c["verdict"]
        L.append(f"- {c['cell']}: rule: {v['rule']}; E_net k007 {v['e_net_entry_k007']:+.4f} kmult {v['e_net_entry_kmult']:+.4f}; "
                 f"look {c['release']['look']}, digest {c['release']['digest'][:16]}, frozen={c['release']['frozen']}; "
                 f"next-look projection {json.dumps(c.get('projection'))}")
    return "\n".join(L) + "\n"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dir", default=str(REPO / "exp_output/CALIBRATION"))
    ap.add_argument("--file", default=None, help="a specific engine_<UTC>.json (default: the latest)")
    ap.add_argument("--report", action="store_true", help="also print FIRST_LOOK_REPORT.md if present")
    a = ap.parse_args(argv)
    p = Path(a.file) if a.file else latest_engine_json(Path(a.dir))
    if p is None or not p.exists():
        print("no engine_*.json found", file=sys.stderr)
        return 1
    print(render(json.loads(p.read_text()), p.name))
    if a.report:
        r = Path(a.dir) / "FIRST_LOOK_REPORT.md"
        print("--- FIRST_LOOK_REPORT.md" + ("" if r.exists() else " (absent)"))
        if r.exists():
            print(r.read_text())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
