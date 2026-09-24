#!/usr/bin/env python3
"""
T-567 — Efficiency-gradient ranking, per the pre-registration at
05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T567_EFFICIENCY_GRADIENT_PREREGISTRATION_2026-09-23.md

Read-only. Reads exp_output/PRICE_ARCHIVE/{prices,depth}_*.jsonl, writes one
aggregated JSON report to --out. Does not touch any portfolio, ledger, config,
or the vig module. Intended to run once against the VPS archive in place
(the archive is ~1GB; this avoids a large network transfer) and have only its
JSON output pulled back.

Methodology (fixed by the pre-registration, not decided here):
  - family = series_ticker
  - TIGHTNESS: median 2*half_spread/yes_mid over price rows with
    0.05 <= yes_mid <= 0.95. Lower = more efficient.
  - DEPTH: median within_5c_usd_min_side over usable=true depth rows.
    Higher = more efficient.
  - PARTICIPATION: per-market max(volume), max(open_interest); family median
    of each; rank-average the two into one participation rank.
    Higher = more efficient.
  - ERI = mean of the three per-dimension ranks (1 = most efficient).
  - Uncertainty: bootstrap resample MARKETS (not rows) with replacement,
    2000 iterations, report median ERI + 90% percentile interval.
  - Tie: overlapping 90% ERI intervals.
  - Diagnostics only (not in ERI): price-discovery variance approaching
    close; open-window drift (first vs last observed yes_mid).
"""

from __future__ import annotations

import argparse
import glob
import json
import multiprocessing as mp
import os
import random
import statistics
import sys
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

N_BOOTSTRAP = 2000
TIGHTNESS_MID_LO, TIGHTNESS_MID_HI = 0.05, 0.95


def _iter_jsonl(pattern: str):
    """Stream rows one at a time across all matching files, in filename (date) order.
    Never materializes the full row set — the prior version built one ~1.8M-element
    list of parsed dicts before aggregating, which OOM-killed the VPS (961Mi total
    RAM, ~582Mi available at run time). Kept as a generator for that reason."""
    for path in sorted(glob.glob(pattern)):
        with open(path) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def _median(xs: list[float]) -> float | None:
    return statistics.median(xs) if xs else None


# Reservoir cap: a per-market safety ceiling on retained tightness/mid samples,
# not expected to bind in practice (observed avg ~24 rows/market; live VPS
# ticker-cardinality check 2026-09-23 found 33,285 max unique tickers in one
# series, all well under this cap in per-market row count) but bounds worst-case
# memory if a single market is polled unusually often.
RESERVOIR_CAP = 500


def _reservoir_add(state: dict[str, Any], key: str, value: Any) -> None:
    seen = state["_seen_" + key] = state.get("_seen_" + key, 0) + 1
    buf = state[key]
    if len(buf) < RESERVOIR_CAP:
        buf.append(value)
    else:
        j = random.randint(0, seen - 1)
        if j < RESERVOIR_CAP:
            buf[j] = value


def _load_price_data(price_dir: Path) -> dict[str, dict[str, Any]]:
    """Returns per-series_ticker: dict with per-market aggregates needed downstream.
    Streams rows; per-market state uses reservoir sampling for the two sample
    lists so memory stays bounded regardless of total row count."""
    by_series: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "n_rows": 0, "dates": set(), "per_market": defaultdict(lambda: {
            "tightness_samples": [], "volume_max": 0.0, "oi_max": 0.0,
            "mid_recent": deque(maxlen=5), "mid_first": None, "mid_last": None,
        }),
    })
    for row in _iter_jsonl(str(price_dir / "prices_*.jsonl")):
        series = row.get("series_ticker")
        if not series:
            continue
        d = by_series[series]
        d["n_rows"] += 1
        run_ts = row.get("run_ts") or ""
        if len(run_ts) >= 10:
            d["dates"].add(run_ts[:10])
        ticker = row.get("ticker") or "?"
        m = d["per_market"][ticker]
        yes_mid = row.get("yes_mid")
        half_spread = row.get("half_spread")
        if (
            isinstance(yes_mid, (int, float))
            and isinstance(half_spread, (int, float))
            and TIGHTNESS_MID_LO <= yes_mid <= TIGHTNESS_MID_HI
            and yes_mid > 0
        ):
            _reservoir_add(m, "tightness_samples", 2.0 * half_spread / yes_mid)
        vol = row.get("volume")
        if isinstance(vol, (int, float)):
            m["volume_max"] = max(m["volume_max"], vol)
        oi = row.get("open_interest")
        if isinstance(oi, (int, float)):
            m["oi_max"] = max(m["oi_max"], oi)
        if isinstance(yes_mid, (int, float)):
            if m["mid_first"] is None:
                m["mid_first"] = (run_ts, yes_mid)
            m["mid_last"] = (run_ts, yes_mid)
            m["mid_recent"].append((run_ts, yes_mid))
    return by_series


def _load_depth_data(price_dir: Path) -> dict[str, dict[str, Any]]:
    by_series: dict[str, dict[str, Any]] = defaultdict(lambda: {
        "n_rows": 0, "dates": set(), "depth_samples": [], "family": None,
    })
    for row in _iter_jsonl(str(price_dir / "depth_*.jsonl")):
        series = row.get("series_ticker")
        if not series:
            continue
        d = by_series[series]
        d["n_rows"] += 1
        d["family"] = row.get("family")
        run_ts = row.get("run_ts") or ""
        if len(run_ts) >= 10:
            d["dates"].add(run_ts[:10])
        if row.get("usable") and isinstance(row.get("within_5c_usd_min_side"), (int, float)):
            d["depth_samples"].append(row["within_5c_usd_min_side"])
    return by_series


def _diagnostics(per_market: dict[str, Any]) -> dict[str, float | None]:
    """Diagnostic-only stats: price-discovery variance near close, open-window drift.
    Not part of ERI (pre-registration Section 4). Uses only bounded per-market state
    (first/last observed mid, last-5 deque) accumulated during the streaming load —
    never a full per-row history — to keep memory bounded on the VPS."""
    late_diffs: list[float] = []
    drifts: list[float] = []
    for m in per_market.values():
        if m["mid_first"] is not None and m["mid_last"] is not None:
            drifts.append(m["mid_last"][1] - m["mid_first"][1])
        recent = sorted(m["mid_recent"], key=lambda t: t[0])
        mids = [v for _, v in recent]
        if len(mids) >= 2:
            diffs = [abs(mids[i + 1] - mids[i]) for i in range(len(mids) - 1)]
            late_diffs.extend(diffs)
    return {
        "price_discovery_late_diff_variance": (
            statistics.pvariance(late_diffs) if len(late_diffs) >= 2 else None
        ),
        "open_window_drift_median_abs": (
            _median([abs(d) for d in drifts]) if drifts else None
        ),
    }


def _family_stats(price_data: dict, depth_data: dict) -> dict[str, dict[str, Any]]:
    families = sorted(set(price_data) | set(depth_data))
    out: dict[str, dict[str, Any]] = {}
    for fam in families:
        pd = price_data.get(fam, {"n_rows": 0, "dates": set(), "per_market": {}})
        dd = depth_data.get(fam, {"n_rows": 0, "dates": set(), "depth_samples": []})
        per_market = pd["per_market"]
        tightness_all = [v for m in per_market.values() for v in m["tightness_samples"]]
        vol_maxes = [m["volume_max"] for m in per_market.values()]
        oi_maxes = [m["oi_max"] for m in per_market.values()]
        out[fam] = {
            "family_group": dd.get("family"),
            "n_price_rows": pd["n_rows"],
            "n_markets": len(per_market),
            "price_date_span": (
                [min(pd["dates"]), max(pd["dates"])] if pd["dates"] else None
            ),
            "n_price_dates": len(pd["dates"]),
            "n_depth_rows": dd["n_rows"],
            "n_depth_usable": len(dd["depth_samples"]),
            "depth_date_span": (
                [min(dd["dates"]), max(dd["dates"])] if dd["dates"] else None
            ),
            "tightness_median": _median(tightness_all),
            "tightness_n": len(tightness_all),
            "depth_median_usd": _median(dd["depth_samples"]),
            "volume_max_median": _median(vol_maxes),
            "oi_max_median": _median(oi_maxes),
            "diagnostics": _diagnostics(per_market),
            "_per_market": per_market,
            "_depth_samples": dd["depth_samples"],
        }
    return out


def _rank(values: dict[str, float | None], higher_is_better: bool) -> dict[str, float]:
    """Average-rank (ties share the mean rank), 1 = most efficient. Families with
    None are excluded from that dimension's ranking entirely (not penalized)."""
    present = [(k, v) for k, v in values.items() if v is not None]
    present.sort(key=lambda kv: kv[1], reverse=higher_is_better)
    ranks: dict[str, float] = {}
    i = 0
    n = len(present)
    while i < n:
        j = i
        while j + 1 < n and present[j + 1][1] == present[i][1]:
            j += 1
        avg_rank = (i + 1 + j + 1) / 2.0
        for k in range(i, j + 1):
            ranks[present[k][0]] = avg_rank
        i = j + 1
    return ranks


def _compute_eri(stats: dict[str, dict[str, Any]]) -> dict[str, float | None]:
    tightness_rank = _rank({f: s["tightness_median"] for f, s in stats.items()}, higher_is_better=False)
    depth_rank = _rank({f: s["depth_median_usd"] for f, s in stats.items()}, higher_is_better=True)
    vol_rank = _rank({f: s["volume_max_median"] for f, s in stats.items()}, higher_is_better=True)
    oi_rank = _rank({f: s["oi_max_median"] for f, s in stats.items()}, higher_is_better=True)
    participation_rank: dict[str, float] = {}
    for f in stats:
        parts = [r[f] for r in (vol_rank, oi_rank) if f in r]
        if parts:
            participation_rank[f] = sum(parts) / len(parts)
    eri: dict[str, float | None] = {}
    for f in stats:
        dims = [r[f] for r in (tightness_rank, depth_rank, participation_rank) if f in r]
        eri[f] = (sum(dims) / len(dims)) if dims else None
    return eri, tightness_rank, depth_rank, participation_rank


# Set by _bootstrap_eri right before forking workers. Fork-based multiprocessing
# gives each worker a copy-on-write view of this at fork time, so the (large)
# per-market/per-depth sample data is never pickled or sent over a pipe — only
# the small (n_iters, seed) task tuple is. Not meaningful outside a forked
# worker's lifetime; do not read this from the main process after forking.
_STATS_GLOBAL: dict[str, dict[str, Any]] = {}


def _bootstrap_worker(task: tuple[int, int]) -> dict[str, list[float]]:
    """Runs `n_iters` bootstrap iterations against _STATS_GLOBAL (inherited via
    fork, not pickled) and returns this worker's partial per-family ERI lists.
    Each iteration still calls _compute_eri across ALL families jointly, exactly
    as the single-threaded version did — only the outer iteration loop is split
    across workers, never the per-iteration cross-family ranking itself."""
    n_iters, seed = task
    rng = random.Random(seed)
    families = list(_STATS_GLOBAL.keys())
    boot_eris: dict[str, list[float]] = defaultdict(list)

    for _ in range(n_iters):
        resampled: dict[str, dict[str, Any]] = {}
        for fam in families:
            s = _STATS_GLOBAL[fam]
            markets = list(s["_per_market"].items())
            if markets:
                sample_m = [rng.choice(markets) for _ in range(len(markets))]
                tightness_all = [v for _, m in sample_m for v in m["tightness_samples"]]
                vol_maxes = [m["volume_max"] for _, m in sample_m]
                oi_maxes = [m["oi_max"] for _, m in sample_m]
            else:
                tightness_all, vol_maxes, oi_maxes = [], [], []
            depth_samples = s["_depth_samples"]
            depth_resample = (
                [rng.choice(depth_samples) for _ in range(len(depth_samples))]
                if depth_samples else []
            )
            resampled[fam] = {
                "tightness_median": _median(tightness_all),
                "depth_median_usd": _median(depth_resample),
                "volume_max_median": _median(vol_maxes),
                "oi_max_median": _median(oi_maxes),
            }
        eri, *_ = _compute_eri(resampled)
        for fam, val in eri.items():
            if val is not None:
                boot_eris[fam].append(val)

    return dict(boot_eris)


def _bootstrap_eri(
    stats: dict[str, dict[str, Any]], seed: int = 20260923, n_workers: int | None = None
) -> dict[str, dict[str, Any]]:
    """Distributes the fixed N_BOOTSTRAP=2000 total iterations across n_workers
    forked processes (chunked by worker, not by iteration, so each worker is
    handed one task and the large `stats` structure is inherited via
    copy-on-write rather than pickled per-iteration). Total iteration count,
    the per-iteration resampling logic, and the joint cross-family call into
    _compute_eri are all unchanged from the single-threaded version — this is
    an engineering/performance change, not a methodology change, and the
    pre-registration's immutability constraint applies to methodology, not to
    how the fixed 2000 iterations are scheduled across cores."""
    global _STATS_GLOBAL
    _STATS_GLOBAL = stats

    if n_workers is None:
        n_workers = max(1, min(6, (os.cpu_count() or 1)))

    base, rem = divmod(N_BOOTSTRAP, n_workers)
    chunk_sizes = [base + (1 if i < rem else 0) for i in range(n_workers)]
    tasks = [(n, seed + i) for i, n in enumerate(chunk_sizes) if n > 0]
    print(
        f"Bootstrap: {N_BOOTSTRAP} iterations across {len(tasks)} forked workers "
        f"(chunk sizes {chunk_sizes})...",
        file=sys.stderr,
    )

    if len(tasks) == 1:
        partials = [_bootstrap_worker(tasks[0])]
    else:
        ctx = mp.get_context("fork")
        with ctx.Pool(processes=len(tasks)) as pool:
            partials = pool.map(_bootstrap_worker, tasks)

    boot_eris: dict[str, list[float]] = defaultdict(list)
    for partial in partials:
        for fam, vals in partial.items():
            boot_eris[fam].extend(vals)

    out: dict[str, dict[str, Any]] = {}
    for fam, vals in boot_eris.items():
        vals_sorted = sorted(vals)
        n = len(vals_sorted)
        lo = vals_sorted[int(0.05 * n)] if n else None
        hi = vals_sorted[min(n - 1, int(0.95 * n))] if n else None
        out[fam] = {
            "median": statistics.median(vals_sorted) if vals_sorted else None,
            "ci90_lo": lo,
            "ci90_hi": hi,
            "n_bootstrap_valid": n,
        }
    return out


def _detect_ties(boot: dict[str, dict[str, Any]]) -> list[list[str]]:
    fams = [f for f, b in boot.items() if b["ci90_lo"] is not None]
    fams.sort(key=lambda f: boot[f]["median"])
    groups: list[list[str]] = []
    for f in fams:
        placed = False
        for g in groups:
            if any(
                not (boot[f]["ci90_hi"] < boot[g_f]["ci90_lo"] or boot[f]["ci90_lo"] > boot[g_f]["ci90_hi"])
                for g_f in g
            ):
                g.append(f)
                placed = True
                break
        if not placed:
            groups.append([f])
    return groups


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--price-dir", default="exp_output/PRICE_ARCHIVE")
    ap.add_argument("--out", default="exp_output/EFFICIENCY_GRADIENT/eri_report.json")
    args = ap.parse_args()

    price_dir = Path(args.price_dir)
    print(f"Loading price rows from {price_dir}/prices_*.jsonl ...", file=sys.stderr)
    price_data = _load_price_data(price_dir)
    print(f"Loading depth rows from {price_dir}/depth_*.jsonl ...", file=sys.stderr)
    depth_data = _load_depth_data(price_dir)

    stats = _family_stats(price_data, depth_data)
    eri, tightness_rank, depth_rank, participation_rank = _compute_eri(stats)
    print("Running bootstrap (2000 iterations, resampling markets)...", file=sys.stderr)
    boot = _bootstrap_eri(stats)
    ties = _detect_ties(boot)

    for fam, s in stats.items():
        s.pop("_per_market", None)
        s.pop("_depth_samples", None)
        s["tightness_rank"] = tightness_rank.get(fam)
        s["depth_rank"] = depth_rank.get(fam)
        s["participation_rank"] = participation_rank.get(fam)
        s["eri_point"] = eri.get(fam)
        s["eri_bootstrap"] = boot.get(fam)

    report = {
        "n_families": len(stats),
        "families": stats,
        "tie_groups_most_to_least_efficient": ties,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
    print(f"Wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
