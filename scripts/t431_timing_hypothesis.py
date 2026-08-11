#!/usr/bin/env python3
"""T-431 Task 1 — test the source-drift/backfill-timing hypothesis for the
B5 disagreement (GG-166 update): does hits-disagreement rate track the gap
between the ledger's original resolved_at and the outcome store's fetch
timestamp (first_attempted_at)? Read-only; reuses task1_agreement_check's
exact join logic from run_t426_shadow_power_calc.py, adds timing fields.
"""
from __future__ import annotations

import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from prediction_market_bot.logic_epoch import is_clean_for_band  # noqa: E402

LEDGER = _REPO_ROOT / "logs" / "t4_mlb_resolved_ledger.jsonl"
STORE = _REPO_ROOT / "logs" / "t4_mlb_outcome_store.jsonl"
BAND = "T4M-PROJ"


def load_jsonl(path: Path) -> list[dict]:
    out = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


def parse_ts(s: str) -> datetime:
    s = s.replace("Z", "+00:00")
    return datetime.fromisoformat(s)


def main() -> None:
    ledger = load_jsonl(LEDGER)
    resolved = [r for r in ledger if r.get("outcome") in ("WIN", "LOSS") and r.get("model_p") is not None]
    clean = [r for r in resolved if is_clean_for_band(r.get("logic_epoch"), BAND)]

    store = {r["ticker"]: r for r in load_jsonl(STORE)}

    rows = []
    for r in clean:
        ticker = r.get("kalshi_ticker", "")
        srec = store.get(ticker)
        if srec is None or not srec.get("resolved"):
            continue
        resolved_at_raw = r.get("resolved_at")
        fetched_at_raw = srec.get("first_attempted_at")
        if not resolved_at_raw or not fetched_at_raw:
            continue
        try:
            resolved_at = parse_ts(resolved_at_raw)
            fetched_at = parse_ts(fetched_at_raw)
        except ValueError:
            continue
        gap_hours = (fetched_at - resolved_at).total_seconds() / 3600.0

        ledger_hits = r.get("actual_hits")
        store_hits = srec.get("actual_hits")
        agree = (
            ledger_hits is not None
            and store_hits is not None
            and float(ledger_hits) == float(store_hits)
        )
        rows.append({
            "position_id": r.get("position_id"),
            "ticker": ticker,
            "resolved_at": resolved_at_raw,
            "fetched_at": fetched_at_raw,
            "gap_hours": gap_hours,
            "gap_days": gap_hours / 24.0,
            "ledger_hits": ledger_hits,
            "store_hits": store_hits,
            "agree": agree,
            "resolution_source": srec.get("resolution_source"),
        })

    n = len(rows)
    print(f"total matched+resolved rows analyzed: {n}")

    agree_gaps = [x["gap_days"] for x in rows if x["agree"]]
    disagree_gaps = [x["gap_days"] for x in rows if not x["agree"]]
    print(f"agree n={len(agree_gaps)}  mean_gap_days={statistics.mean(agree_gaps):.3f}  median={statistics.median(agree_gaps):.3f}  stdev={statistics.stdev(agree_gaps):.3f}")
    print(f"disagree n={len(disagree_gaps)}  mean_gap_days={statistics.mean(disagree_gaps):.3f}  median={statistics.median(disagree_gaps):.3f}  stdev={statistics.stdev(disagree_gaps):.3f}" if len(disagree_gaps) >= 2 else f"disagree n={len(disagree_gaps)} gaps={disagree_gaps}")

    # Bin by gap_days and report disagreement rate per bin
    bins = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7), (7, 999)]
    print("\ngap_days_bin -> n, disagree, rate")
    for lo, hi in bins:
        bucket = [x for x in rows if lo <= x["gap_days"] < hi]
        if not bucket:
            continue
        dis = sum(1 for x in bucket if not x["agree"])
        print(f"  [{lo},{hi}) -> n={len(bucket)} disagree={dis} rate={dis/len(bucket):.1%}")

    # Distinct gap_days values (since resolution likely batches — check discreteness)
    distinct_gaps = sorted({round(x["gap_days"], 1) for x in rows})
    print(f"\ndistinct gap_days (rounded to 0.1d), n={len(distinct_gaps)}: {distinct_gaps[:30]}")

    # Correlation: point-biserial between gap_days (continuous) and disagree (binary)
    if n >= 3:
        gaps_all = [x["gap_days"] for x in rows]
        disagree_flags = [0 if x["agree"] else 1 for x in rows]
        mean_gap = statistics.mean(gaps_all)
        mean_flag = statistics.mean(disagree_flags)
        cov = sum((g - mean_gap) * (f - mean_flag) for g, f in zip(gaps_all, disagree_flags)) / n
        sd_gap = statistics.pstdev(gaps_all)
        sd_flag = statistics.pstdev(disagree_flags)
        corr = cov / (sd_gap * sd_flag) if sd_gap > 0 and sd_flag > 0 else None
        print(f"\npoint-biserial correlation (gap_days vs disagree): {corr}")

    # resolution_source breakdown for disagreements
    print("\nresolution_source breakdown, disagreements only:")
    src_counts: dict[str, int] = {}
    for x in rows:
        if not x["agree"]:
            src_counts[x["resolution_source"]] = src_counts.get(x["resolution_source"], 0) + 1
    print(src_counts)
    print("resolution_source breakdown, ALL matched rows:")
    src_counts_all: dict[str, int] = {}
    for x in rows:
        src_counts_all[x["resolution_source"]] = src_counts_all.get(x["resolution_source"], 0) + 1
    print(src_counts_all)

    out_path = _REPO_ROOT / "logs" / "t431_timing_analysis.json"
    with open(out_path, "w") as f:
        json.dump(rows, f, indent=2, default=str)
    print(f"\nfull row dump written to {out_path}")


if __name__ == "__main__":
    main()
