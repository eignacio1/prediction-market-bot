#!/usr/bin/env python3
"""
T-566 — vig grounding from the price archive.

Two subcommands, one script (scope-fenced to "exactly one new analysis
script" per the T-566 task brief):

  spread          Deliverable 2 — measure the real distribution of
                   half_spread and full spread (yes_ask - yes_bid) per
                   series_ticker from the live price archive, and how each
                   moves with yes_mid and time-to-close.

  flip-analysis   Deliverable 3 (headline finding) — re-run the T4M-PROJ
                   epoch-12 clean cohort's gate decisions with each
                   position's real vig_at_entry replaced by an archive-
                   measured value (bucketed by yes_mid at entry), and count
                   how many flip from approved to rejected under
                   MIN_EDGE_TO_APPROVE. Requires a "spread" run's output
                   JSON as input (--spread-summary).

WHY THIS EXISTS
---------------
T-566's core question is whether the vig/cost terms hardcoded or assumed in
the C4 gate path (risk.py, run_t4_mlb_live.py, run_t2_mlb_sameday.py,
run_t1_mlb_game_market.py, run_t1_nfl_game_market.py, execution_bands.py —
see Deliverable 1) are grounded in the market's actual observed spread
behavior, and how many live gate decisions would change if a code-side
assumption were replaced by an archive-measured value. This script reads
scripts/archive_market_prices.py's daily output
(exp_output/PRICE_ARCHIVE/prices_YYYY-MM-DD.jsonl, VPS-only, gitignored,
~1.8M rows as of 2026-09-22) for the "spread" subcommand, and a pulled copy
of paper_portfolio_mlb_t4.json (also VPS-only, not committed — see
--portfolio-path) for "flip-analysis".

This script makes NO changes to any vig/cost/spread/gating constant in src/,
performs no writes to the archive, the live portfolio, or any running
service. Read-only throughout.

.BROKEN_FIRSTRUN EXCLUSION (spread subcommand)
------------------------------------------------
prices_2026-08-01.jsonl.BROKEN_FIRSTRUN (2,162 rows) is excluded. This is
not merely a filename convention — direct row inspection confirms it is
missing every price/spread field (yes_bid, yes_ask, yes_mid, half_spread,
etc.), carrying only static market metadata (ticker, series_ticker, status,
close_time). It represents an aborted first invocation of the archiver on
2026-08-01 that was superseded by a normal prices_2026-08-01.jsonl covering
the same date. The glob below (prices_*.jsonl, no further suffix) already
excludes it structurally since the file does not end in ".jsonl" — this is
stated explicitly here so the exclusion is documented, not just incidental.

USAGE
-----
    python3 measure_archive_spread_by_series.py spread \
        --archive-dir /opt/prediction-market-bot/exp_output/PRICE_ARCHIVE \
        --out exp_output/T566-VIG-GROUNDING/spread_summary.json

    python3 measure_archive_spread_by_series.py flip-analysis \
        --portfolio-path /opt/prediction-market-bot/logs/paper_portfolio_mlb_t4.json \
        --spread-summary exp_output/T566-VIG-GROUNDING/spread_summary.json \
        --band T4M-PROJ \
        --out exp_output/T566-VIG-GROUNDING/flip_analysis.json
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics
import sys
from collections import defaultdict
from datetime import datetime, timezone


def parse_ts(s):
    if not s:
        return None
    try:
        s2 = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s2)
    except (ValueError, TypeError):
        return None


def to_float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def percentile(sorted_vals, pct):
    if not sorted_vals:
        return None
    n = len(sorted_vals)
    if n == 1:
        return sorted_vals[0]
    k = (n - 1) * pct
    f = int(k)
    c = min(f + 1, n - 1)
    if f == c:
        return sorted_vals[f]
    d = k - f
    return sorted_vals[f] + (sorted_vals[c] - sorted_vals[f]) * d


def mid_bucket(mid):
    if mid is None:
        return "unknown"
    if mid < 0.10:
        return "0.00-0.10"
    if mid < 0.30:
        return "0.10-0.30"
    if mid < 0.70:
        return "0.30-0.70"
    if mid < 0.90:
        return "0.70-0.90"
    return "0.90-1.00"


def ttc_bucket(hours):
    if hours is None:
        return "unknown"
    if hours < 0:
        return "past_close"
    if hours < 1:
        return "0-1h"
    if hours < 6:
        return "1-6h"
    if hours < 24:
        return "6-24h"
    return ">24h"


def summarize(vals):
    if not vals:
        return None
    sv = sorted(vals)
    return {
        "n": len(sv),
        "median": statistics.median(sv),
        "p25": percentile(sv, 0.25),
        "p75": percentile(sv, 0.75),
        "p90": percentile(sv, 0.90),
        "min": sv[0],
        "max": sv[-1],
    }


# --------------------------------------------------------------------------
# Deliverable 2 — spread subcommand
# --------------------------------------------------------------------------

def run_spread(args):
    pattern = os.path.join(args.archive_dir, "prices_*.jsonl")
    files = sorted(glob.glob(pattern))
    # Defensive: exclude anything whose name doesn't end exactly in .jsonl
    # (catches .BROKEN_FIRSTRUN and any similar future quarantine suffix
    # even though glob("*.jsonl") already excludes it structurally).
    files = [f for f in files if f.endswith(".jsonl")]

    print(f"Found {len(files)} archive files matching prices_*.jsonl", flush=True)

    per_series_half = defaultdict(list)
    per_series_full = defaultdict(list)
    per_series_dates = defaultdict(set)
    per_series_mid_bucket_half = defaultdict(lambda: defaultdict(list))
    per_series_ttc_bucket_half = defaultdict(lambda: defaultdict(list))

    total_rows = 0
    skipped_no_quotes = 0
    skipped_parse_error = 0
    skipped_missing_fields = 0

    for fpath in files:
        fname = os.path.basename(fpath)
        file_date = fname[len("prices_"):-len(".jsonl")]
        with open(fpath, "r") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                total_rows += 1
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    skipped_parse_error += 1
                    continue

                series = row.get("series_ticker")
                if not series:
                    skipped_missing_fields += 1
                    continue

                yes_bid = to_float(row.get("yes_bid"))
                yes_ask = to_float(row.get("yes_ask"))
                if yes_bid is None or yes_ask is None:
                    skipped_missing_fields += 1
                    continue
                if yes_bid <= 0 or yes_ask <= 0:
                    skipped_no_quotes += 1
                    continue

                full_spread = yes_ask - yes_bid
                half_spread = to_float(row.get("half_spread"))
                if half_spread is None:
                    half_spread = full_spread / 2.0

                yes_mid = to_float(row.get("yes_mid"))
                if yes_mid is None:
                    yes_mid = (yes_ask + yes_bid) / 2.0

                run_ts = parse_ts(row.get("run_ts"))
                close_time = parse_ts(row.get("close_time"))
                ttc_hours = None
                if run_ts is not None and close_time is not None:
                    ttc_hours = (close_time - run_ts).total_seconds() / 3600.0

                per_series_half[series].append(half_spread)
                per_series_full[series].append(full_spread)
                per_series_dates[series].add(file_date)
                per_series_mid_bucket_half[series][mid_bucket(yes_mid)].append(half_spread)
                per_series_ttc_bucket_half[series][ttc_bucket(ttc_hours)].append(half_spread)

    print(
        f"total_rows={total_rows} skipped_no_quotes={skipped_no_quotes} "
        f"skipped_parse_error={skipped_parse_error} "
        f"skipped_missing_fields={skipped_missing_fields}",
        flush=True,
    )

    result = {
        "meta": {
            "archive_dir": args.archive_dir,
            "files_read": len(files),
            "total_rows_seen": total_rows,
            "skipped_no_quotes": skipped_no_quotes,
            "skipped_parse_error": skipped_parse_error,
            "skipped_missing_fields": skipped_missing_fields,
            "broken_firstrun_excluded": True,
            "broken_firstrun_exclusion_reason": (
                "prices_2026-08-01.jsonl.BROKEN_FIRSTRUN (2162 rows) lacks all "
                "price/spread fields entirely (confirmed by direct row inspection); "
                "excluded structurally by the prices_*.jsonl glob + explicit .jsonl "
                "suffix filter, not just by convention."
            ),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "per_series": {},
    }

    for series in sorted(per_series_half.keys()):
        dates = sorted(per_series_dates[series])
        entry = {
            "n": len(per_series_half[series]),
            "date_span": {"first": dates[0], "last": dates[-1], "n_distinct_days": len(dates)},
            "half_spread": summarize(per_series_half[series]),
            "full_spread": summarize(per_series_full[series]),
            "half_spread_by_yes_mid_bucket": {
                b: summarize(v) for b, v in sorted(per_series_mid_bucket_half[series].items())
            },
            "half_spread_by_time_to_close_bucket": {
                b: summarize(v) for b, v in sorted(per_series_ttc_bucket_half[series].items())
            },
        }
        result["per_series"][series] = entry

    os.makedirs(os.path.dirname(args.out), exist_ok=True) if os.path.dirname(args.out) else None
    with open(args.out, "w") as fh:
        json.dump(result, fh, indent=2, default=str)

    print(f"Wrote summary to {args.out}", flush=True)
    for series, entry in result["per_series"].items():
        hs = entry["half_spread"]
        print(
            f"{series}: n={entry['n']} days={entry['date_span']['n_distinct_days']} "
            f"({entry['date_span']['first']}..{entry['date_span']['last']}) "
            f"half_spread median={hs['median']:.4f} p25={hs['p25']:.4f} "
            f"p75={hs['p75']:.4f} p90={hs['p90']:.4f}",
            flush=True,
        )


# --------------------------------------------------------------------------
# Deliverable 3 — flip-analysis subcommand
# --------------------------------------------------------------------------

def kalshi_fee(mid):
    """ADR-0016. mid = mid_price_at_entry (0-1)."""
    return 0.07 * mid * (1.0 - mid)


def directional_net_edge(model_p, mid, vig, direction):
    fee = kalshi_fee(mid)
    if direction == "YES":
        gross = (model_p - mid) - vig
    else:
        gross = (mid - model_p) - vig
    return gross - fee


def run_flip_analysis(args):
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, os.path.join(repo_root, "src"))
    from prediction_market_bot import logic_epoch as le  # noqa: E402

    with open(args.portfolio_path) as fh:
        portfolio = json.load(fh)
    with open(args.spread_summary) as fh:
        spread = json.load(fh)

    series_stats = spread["per_series"].get(args.series)
    if series_stats is None:
        raise SystemExit(f"series {args.series!r} not found in {args.spread_summary}")
    by_mid_bucket = series_stats["half_spread_by_yes_mid_bucket"]

    rows = []
    for p in portfolio.get("closed_positions", []):
        if p.get("band") != args.band:
            continue
        if not le.is_clean_for_band(p.get("logic_epoch"), args.band):
            continue
        rows.append(p)

    print(f"clean {args.band} cohort n={len(rows)} (source: {args.portfolio_path})", flush=True)

    result = {
        "meta": {
            "band": args.band,
            "series": args.series,
            "portfolio_path": args.portfolio_path,
            "spread_summary": args.spread_summary,
            "min_edge_to_approve": args.min_edge,
            "min_bucket_n": args.min_bucket_n,
            "clean_cohort_n": len(rows),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "runs": {},
    }

    for pct_label, use_p90 in [("median", False), ("p90", True)]:
        flips = 0
        unchanged = 0
        n_evaluated = 0
        n_skipped_thin_bucket = 0
        deltas = []
        for p in rows:
            mid = p["mid_price_at_entry"]
            model_p = p["model_p"]
            direction = p["direction"]
            fee_net_edge_stored = p["fee_net_edge"]
            b = mid_bucket(mid)
            bucket_stat = by_mid_bucket.get(b)
            if bucket_stat is None or bucket_stat["n"] < args.min_bucket_n:
                n_skipped_thin_bucket += 1
                continue
            measured_half = bucket_stat["p90"] if use_p90 else bucket_stat["median"]
            measured_vig = 2 * measured_half
            new_net = directional_net_edge(model_p, mid, measured_vig, direction)
            was_approved = fee_net_edge_stored >= args.min_edge  # all rows are closed_positions => fired historically
            now_approved = new_net >= args.min_edge
            n_evaluated += 1
            deltas.append(new_net - fee_net_edge_stored)
            if was_approved and not now_approved:
                flips += 1
            else:
                unchanged += 1
        avg_delta = sum(deltas) / len(deltas) if deltas else None
        flip_pct = 100 * flips / n_evaluated if n_evaluated else None
        print(
            f"--- vig substitute = archive {pct_label} of {args.series} half_spread, bucketed by yes_mid at entry ---",
            flush=True,
        )
        print(
            f"  n_evaluated={n_evaluated}  n_skipped_thin_bucket={n_skipped_thin_bucket}  "
            f"flip_to_reject={flips} ({flip_pct:.1f}%)  unchanged={unchanged}",
            flush=True,
        )
        print(f"  avg net_edge delta (measured - stored) = {avg_delta:.4f}", flush=True)
        result["runs"][pct_label] = {
            "n_evaluated": n_evaluated,
            "n_skipped_thin_bucket": n_skipped_thin_bucket,
            "flip_to_reject": flips,
            "flip_to_reject_pct": flip_pct,
            "unchanged": unchanged,
            "avg_net_edge_delta": avg_delta,
        }

    os.makedirs(os.path.dirname(args.out), exist_ok=True) if os.path.dirname(args.out) else None
    with open(args.out, "w") as fh:
        json.dump(result, fh, indent=2, default=str)
    print(f"Wrote flip-analysis summary to {args.out}", flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp_spread = sub.add_parser("spread", help="Deliverable 2 — per-series spread distributions from the price archive")
    sp_spread.add_argument("--archive-dir", required=True)
    sp_spread.add_argument("--out", required=True)
    sp_spread.set_defaults(func=run_spread)

    sp_flip = sub.add_parser("flip-analysis", help="Deliverable 3 — re-run clean-cohort gate decisions under measured vig")
    sp_flip.add_argument("--portfolio-path", required=True)
    sp_flip.add_argument("--spread-summary", required=True)
    sp_flip.add_argument("--band", default="T4M-PROJ")
    sp_flip.add_argument("--series", default="KXMLBHIT")
    sp_flip.add_argument("--min-edge", type=float, default=0.04, help="MIN_EDGE_TO_APPROVE, ADR-0020")
    sp_flip.add_argument("--min-bucket-n", type=int, default=5, help="skip rows whose yes_mid bucket has too few archive observations to trust")
    sp_flip.add_argument("--out", required=True)
    sp_flip.set_defaults(func=run_flip_analysis)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
