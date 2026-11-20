#!/usr/bin/env python3
"""W121.3 / B-097: dollar CEILING per cell from capacity_read.py output. Offline, pure; writes only the paths it is given.

ceiling $/day = opportunities/day x contracts filled per opportunity x net per contract
  contracts filled = min(contracts the bankroll would buy at SCENARIO_STAKE_FRACTION, cross-touch size measured at submit)
  stake per opportunity is also capped by the demo caps (event / arm day / book day), applied pro rata when they bind.

NOT A SIZING RULE. Kelly stays 0 (execution_bands.py) and no real capital moves. The ranking only orders future wiring.
The stake fraction is a SCENARIO KNOB (there is no bankroll-based sizing in the demo book: stakes are flat); it is printed with the table.
Net per contract is the W117.1 CROSS estimate per arm (game-clustered, real spread, after fees), pooled across sports, with its
interval; every one of them spans 0 today, so every ceiling carries a lower bound below 0 and says so.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional

BANKROLLS = (1_000, 10_000, 100_000)
SCENARIO_STAKE_FRACTION = 0.01
CAPS = {"event_usd": 25.0, "arm_day_usd": 1500.0, "book_day_usd": 2500.0}  # RAISED_CAPS in c4_risk_engine/arm_sizing.py
# W117.1 handoff (box read 2026-11-18T04:52Z, post-epoch, game-clustered): net per contract after fees, crossing the spread.
NET = {"FADE": (0.166, -0.016, 0.348, "105 orders / 20 games"),
       "RIDE": (0.016, -0.057, 0.089, "253 / 22"),
       "MOMENTUM": (0.052, -0.087, 0.191, "96 / 21")}
# MODEL_FADE: 2 settled fills in the W119.3 read; no estimate exists, so no ceiling is stated.


def ceiling_rows(cap: dict, bankroll: float, fraction: float = SCENARIO_STAKE_FRACTION) -> List[dict]:
    rows = []
    for c in cap["orders"]["cells"]:
        net = NET.get(c["arm"])
        cross, entry = c["cross_touch_contracts"], c["entry_price"]["median"]
        base = {"cell": c["cell"], "sport": c["sport"], "market_type": c["market_type"], "band": c["band"], "arm": c["arm"],
                "n_orders": c["n_orders"], "n_cross_depth": cross["n"], "opportunities_per_day": c["opportunities_per_day"],
                "fillable_contracts_median": cross["median"], "fillable_contracts_p25": cross["p25"],
                "fillable_contracts_p75": cross["p75"], "entry_price_median": entry}
        if net is None or not cross["n"] or not entry:
            rows.append({**base, "usd_per_day": None, "why_none": "no net estimate for this arm" if net is None else "no depth or entry logged"})
            continue
        want = max(int(bankroll * fraction / entry), 0)
        stake_cap = int(CAPS["event_usd"] / entry)

        def per_day(depth: Optional[float]) -> float:
            k = min(want, stake_cap, int(depth or 0))
            return c["opportunities_per_day"] * k
        k_pt, k_lo, k_hi = per_day(cross["median"]), per_day(cross["p25"]), per_day(cross["p75"])
        rows.append({**base, "contracts_per_day": round(k_pt, 2), "usd_staked_per_day": round(k_pt * entry, 2),
                     "usd_per_day": round(k_pt * net[0], 2), "usd_per_day_low": round(k_lo * net[1], 2),
                     "usd_per_day_high": round(k_hi * net[2], 2), "net_per_contract": net[0], "net_interval": [net[1], net[2]],
                     "net_source": net[3], "interval_spans_zero": net[1] < 0 < net[2]})
    # book / arm day caps, pro rata
    for arm in {r["arm"] for r in rows if r.get("usd_staked_per_day")}:
        rs = [r for r in rows if r["arm"] == arm and r.get("usd_staked_per_day")]
        tot = sum(r["usd_staked_per_day"] for r in rs)
        if tot > CAPS["arm_day_usd"]:
            f = CAPS["arm_day_usd"] / tot
            for r in rs:
                _scale(r, f)
    allr = [r for r in rows if r.get("usd_staked_per_day")]
    tot = sum(r["usd_staked_per_day"] for r in allr)
    if tot > CAPS["book_day_usd"]:
        for r in allr:
            _scale(r, CAPS["book_day_usd"] / tot)
    return rows


def _scale(r: dict, f: float) -> None:
    for k in ("contracts_per_day", "usd_staked_per_day", "usd_per_day", "usd_per_day_low", "usd_per_day_high"):
        r[k] = round(r[k] * f, 2)
    r["day_cap_scaled"] = round(f, 4)


def build(cap: dict) -> dict:
    out: Dict[str, dict] = {}
    for b in BANKROLLS:
        rows = ceiling_rows(cap, b)
        ranked = sorted([r for r in rows if r.get("usd_per_day") is not None], key=lambda r: -r["usd_per_day"])
        by_arm: Dict[str, dict] = {}
        for r in ranked:
            k = f"{r['arm']}|{r['sport']}"
            a = by_arm.setdefault(k, {"usd_per_day": 0.0, "low": 0.0, "high": 0.0})
            a["usd_per_day"] += r["usd_per_day"]; a["low"] += r["usd_per_day_low"]; a["high"] += r["usd_per_day_high"]
        out[str(b)] = {"cells": rows, "top10": ranked[:10],
                       "by_arm_sport": {k: {x: round(y, 2) for x, y in v.items()} for k, v in sorted(by_arm.items())}}
    return {"as_of_orders": cap.get("as_of_utc"), "stake_fraction": SCENARIO_STAKE_FRACTION, "caps": CAPS,
            "net_inputs": {k: {"point": v[0], "interval": [v[1], v[2]], "n": v[3]} for k, v in NET.items()},
            "bankrolls": out}


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("capacity_json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    cap = json.loads(Path(a.capacity_json).read_text())
    Path(a.out).write_text(json.dumps(build(cap), indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
