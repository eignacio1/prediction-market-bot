"""Part A.1: injury-report coverage by month (share of regular-season games with a usable point-in-time snapshot), before vs after the GG-620 fix."""
import json, os, sys, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "20261012_nba_points_minutes"))
import features as F
from prediction_market_bot.c1_signal_ingestion import nba_ingest as N
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import _dt, et_date
RAW = HERE.parent.parent.parent / "nba_raw"
old = F.load_inj(str(HERE.parent / "20261012_nba_points_minutes" / "inj"))
new = F.load_inj(str(HERE / "inj2026"))
merged = dict(old); merged.update({k: v for k, v in new.items() if v})
res = {}
for s in (2023, 2024, 2025, 2026):
    for g in N.load_season(s, RAW)["games"].values():
        if g["season_type"] != 2 or not g["completed"]:
            continue
        st = _dt(g["start_time_utc"]); m = str(et_date(st))[:7]
        r = res.setdefault(m, [0, 0, 0])
        r[0] += 1
        r[1] += F.snapshot(old, st) is not None
        r[2] += F.snapshot(merged, st) is not None
out = {m: {"games": a, "before": b, "after": c} for m, (a, b, c) in sorted(res.items())}
(HERE / "coverage.json").write_text(json.dumps(out, indent=1))
print("month   games  before(W69.3)  after(GG-620 fix)")
for m, v in out.items():
    if m >= "2025-10":
        print(m, v["games"], f'{v["before"]/v["games"]:.1%}', f'{v["after"]/v["games"]:.1%}')
for s, (lo, hi) in {"2023": ("2022-10", "2023-06"), "2024": ("2023-10", "2024-06"), "2025": ("2024-10", "2025-06"), "2026": ("2025-10", "2026-06")}.items():
    a = sum(v["games"] for m, v in out.items() if lo <= m <= hi); c = sum(v["after"] for m, v in out.items() if lo <= m <= hi); b = sum(v["before"] for m, v in out.items() if lo <= m <= hi)
    print("season", s, a, f"{b/a:.1%} -> {c/a:.1%}")
