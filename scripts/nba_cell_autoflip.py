#!/usr/bin/env python3
"""W69.2 / EXP-038: flip NBA game cells NOT_IMPLEMENTED -> SHADOW by itself once valid regular-season rows exist.

Daily cron. For each cell with >=1 valid row (predicate shared with w59_3_nba_flip_check.valid: frozen model sha,
0<p_yes<1, a quote, start_time_source, not preseason) append ONE record to exp_output/PREGAME_SHADOW/nba_promotions.jsonl;
market_type_registry applies the file at import. Idempotent (a cell already recorded is skipped). Evaluate-and-log only:
no order, stake or kelly. Refuses to run before 2026-10-20 so preseason/fixture data can never flip a cell.
Usage: python3 scripts/nba_cell_autoflip.py [--ledger-dir DIR] [--out FILE] [--today YYYY-MM-DD]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from w59_3_nba_flip_check import BAND, MT, ROOT, frozen_model_sha, valid  # noqa: E402

NOT_BEFORE = date(2026, 10, 20)
BAND_ENUM = {"T1": "T1_MULTI_DAY", "T2": "T2_SAME_DAY", "T3": "T3_PRE_TIP"}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW"))
    ap.add_argument("--out", default=None)
    ap.add_argument("--today", default=None)
    a = ap.parse_args(argv)
    today = date.fromisoformat(a.today) if a.today else datetime.now(timezone.utc).date()
    if today < NOT_BEFORE:
        print(f"AUTOFLIP: {today} < {NOT_BEFORE}, no-op")
        return 0
    led = Path(a.ledger_dir)
    out = Path(a.out) if a.out else led / "nba_promotions.jsonl"
    sha = frozen_model_sha()
    done = set()
    if out.exists():
        for l in out.read_text().splitlines():
            try:
                r = json.loads(l)
                done.add((r["market_type"], r["band"]))
            except (ValueError, KeyError):
                pass
    new = []
    for m, mt in MT.items():
        for b, bd in BAND.items():
            key = (mt.lower(), bd)
            p = led / f"NBA_{mt}_{b}.jsonl"
            rows = []
            if p.exists():
                for l in p.read_text().splitlines():
                    try:
                        rows.append(json.loads(l))
                    except ValueError as exc:
                        # W77.3/GG-764 sweep: a torn cell-ledger row shrinks n
                        # that decides the flip; report, never silent.
                        print(f"[CORRUPT_READ] {p.name}: torn row skipped ({exc})", file=sys.stderr)
            n = sum(valid(r, sha) for r in rows)
            if n and key not in done:
                new.append({"ts_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "market_type": key[0],
                            "band": bd, "valid_rows": n, "superseding_reference": "EXP-038"})
    if new:
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("a") as f:
            for r in new:
                f.write(json.dumps(r) + "\n")
    print(f"AUTOFLIP: {len(new)} new promotion(s), {len(done)} already recorded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
