#!/usr/bin/env python3
"""READ-ONLY (W120.2): count the box's shadow rows that carry candidate-map arms (router v2, +nba_depth, nhl_v2) beside v1.

Per sport and per candidate: rows carrying the candidate, its arm mix, ERROR count, the map versions / SHAs seen, and how many
of those rows' v1 arm equals the candidate's arm. Also the sport's total rows in the window. Writes nothing: stdout only."""
from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
import arm_orders_read as aor  # noqa: E402


def files(repo: Path = REPO):
    base = Path(os.environ.get("PM_SHADOW_DIR", str(repo / "exp_output" / "PREGAME_SHADOW")))
    return sorted(base.glob("*.jsonl")) + sorted((repo / "data" / "shadow" / "nhl").glob("*_T[123].jsonl"))


def rows(since: datetime, repo: Path = REPO):
    for f in files(repo):
        try:
            fh = f.open("r", encoding="utf-8", errors="ignore")
        except OSError:
            continue
        with fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                ts = aor.parse_ts(r.get("ts_utc")) if isinstance(r, dict) else None
                if ts is not None and ts >= since:
                    yield r


def count(it) -> dict:
    tot: Counter = Counter()
    d: dict = defaultdict(lambda: {"rows": 0, "arms": Counter(), "errors": 0, "same_as_v1": 0, "versions": set(), "shas": set()})
    for r in it:
        sp = str(r.get("sport") or "?").upper()
        tot[sp] += 1
        c = r.get("router_candidates")
        if not isinstance(c, dict):
            continue
        v1 = (r.get("router") or {}).get("arm")
        for name, rec in c.items():
            x = d[(sp, name)]
            x["rows"] += 1
            x["arms"][rec.get("arm")] += 1
            x["errors"] += rec.get("arm") == "ERROR"
            x["same_as_v1"] += rec.get("arm") == v1
            x["versions"].add(rec.get("map_version"))
            x["shas"].add((rec.get("map_sha256") or "")[:12])
    return {"rows_in_window": dict(tot),
            "candidates": {f"{sp}|{n}": {"rows": x["rows"], "arms": dict(x["arms"]), "errors": x["errors"],
                                         "same_as_v1": x["same_as_v1"], "map_versions": sorted(map(str, x["versions"])),
                                         "sha12": sorted(x["shas"])} for (sp, n), x in sorted(d.items())}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=72)
    a = ap.parse_args()
    now = datetime.now(timezone.utc)
    out = count(rows(now - timedelta(hours=a.hours)))
    out.update(read_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"), window_hours=a.hours)
    print(json.dumps(out, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
