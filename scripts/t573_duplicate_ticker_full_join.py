#!/usr/bin/env python3
"""T-573 Deliverable 1b/2: full local join to characterize the duplicate-ticker
pattern across the 731 NOT_RETRIEVABLE rows and the 35 FILLED rows.

No API calls -- pure comparison of ledger kalshi_ticker strings. Reproduces and
extends the earlier API-scoped 9-row finding, and reconciles the overlap between:
  (a) NR rows that share a ticker with a FILLED row ("FILLED-collision")
  (b) NR rows that share a ticker with another NR row ("NR-internal duplicate")
  (c) rows that are BOTH -- i.e. a ticker with 1 FILLED + >=2 NR rows.

Writes a durable per-row JSON artifact plus the full bucket table for
Deliverable 2. Run on the VPS.
"""
import json
import sys
from collections import defaultdict

sys.path.insert(0, "src")
from prediction_market_bot import logic_epoch as le  # noqa: E402


def main():
    portfolio = json.load(open("logs/paper_portfolio_mlb_t4.json"))
    closed = portfolio.get("closed_positions", [])
    by_pid = {
        p["position_id"]: p for p in closed
        if p.get("band") == "T4M-PROJ" and le.is_clean_for_band(p.get("logic_epoch"), "T4M-PROJ")
    }
    verif = json.load(open("/tmp/t571_kalshi_verification_results.json"))
    results = verif["results"]
    filled = [r for r in results if r["verdict"] == "FILLED"]
    nr = [r for r in results if r["verdict"] == "NOT_RETRIEVABLE"]

    filled_tickers = defaultdict(list)
    for r in filled:
        row = by_pid.get(r["position_id"], {})
        t = row.get("kalshi_ticker")
        if t:
            filled_tickers[t].append(r["position_id"])

    nr_tickers = defaultdict(list)
    for r in nr:
        row = by_pid.get(r["position_id"], {})
        t = row.get("kalshi_ticker")
        if t:
            nr_tickers[t].append(r["position_id"])

    # (a) NR rows colliding with a FILLED ticker
    filled_collision_tickers = {t for t in nr_tickers if t in filled_tickers}
    filled_collision_nr_pids = {pid for t in filled_collision_tickers for pid in nr_tickers[t]}

    # (b) tickers shared by >1 NR row (regardless of FILLED collision)
    nr_internal_dupe_tickers = {t: pids for t, pids in nr_tickers.items() if len(pids) > 1}
    nr_internal_dupe_pids = {pid for pids in nr_internal_dupe_tickers.values() for pid in pids}

    # (c) 3-way: ticker has 1 FILLED AND >=2 NR (subset of both a and b)
    three_way_tickers = {t for t in filled_collision_tickers if t in nr_internal_dupe_tickers}

    # reconciliation: partition all 731 NR rows into exclusive buckets
    only_filled_collision = filled_collision_nr_pids - nr_internal_dupe_pids
    only_nr_internal = nr_internal_dupe_pids - filled_collision_nr_pids
    both = filled_collision_nr_pids & nr_internal_dupe_pids
    neither = {r["position_id"] for r in nr} - filled_collision_nr_pids - nr_internal_dupe_pids

    print(f"n_nr_total={len(nr)}")
    print(f"filled_collision_tickers={len(filled_collision_tickers)} -> nr_pids={len(filled_collision_nr_pids)}")
    print(f"nr_internal_dupe_tickers={len(nr_internal_dupe_tickers)} -> nr_pids={len(nr_internal_dupe_pids)}")
    print(f"three_way_tickers (1 FILLED + >=2 NR)={len(three_way_tickers)}")
    print()
    print("=== EXCLUSIVE PARTITION of the 731 NR rows ===")
    print(f"  A) FILLED-collision only (ticker matches a FILLED row, no NR sibling): {len(only_filled_collision)}")
    print(f"  B) NR-internal-duplicate only (no FILLED collision):                  {len(only_nr_internal)}")
    print(f"  C) BOTH (3-way: ticker has 1 FILLED + >=2 NR):                        {len(both)}")
    print(f"  D) Neither (unique ticker within NR, no FILLED collision):            {len(neither)}")
    print(f"  TOTAL: {len(only_filled_collision) + len(only_nr_internal) + len(both) + len(neither)} (should equal {len(nr)})")

    # group-size distribution for NR-internal dupes
    from collections import Counter
    size_dist = Counter(len(pids) for pids in nr_internal_dupe_tickers.values())
    print(f"\nNR-internal dupe group sizes: {dict(sorted(size_dist.items()))}")

    if three_way_tickers:
        print(f"\n3-way collision examples (ticker: filled_pid + nr_pids):")
        for t in list(three_way_tickers)[:10]:
            print(f"  {t}: FILLED={filled_tickers[t]} NR={nr_tickers[t]}")

    out = {
        "n_nr_total": len(nr),
        "n_filled_total": len(filled),
        "filled_collision_tickers": sorted(filled_collision_tickers),
        "nr_internal_dupe_group_count": len(nr_internal_dupe_tickers),
        "nr_internal_dupe_group_size_dist": dict(size_dist),
        "three_way_tickers": sorted(three_way_tickers),
        "partition": {
            "A_filled_collision_only": sorted(only_filled_collision),
            "B_nr_internal_only": sorted(only_nr_internal),
            "C_both_three_way": sorted(both),
            "D_neither_unique": sorted(neither),
        },
        "nr_internal_dupe_groups": {t: pids for t, pids in nr_internal_dupe_tickers.items()},
    }
    with open("/tmp/t573_duplicate_ticker_full_join_results.json", "w") as f:
        json.dump(out, f, indent=2, default=str)
    print("\nwrote /tmp/t573_duplicate_ticker_full_join_results.json")


if __name__ == "__main__":
    main()
