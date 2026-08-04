#!/usr/bin/env python3
"""
Forward price archiver — Kalshi market snapshots, append-only.

Why this exists
---------------
As of 2026-08-01 this project has NO historical price archive for any market
family. The only price history that exists anywhere is `mid_price_at_entry` /
`vig_at_entry` embedded in ledger rows -- i.e. prices for markets the bot
actually bet on, at the instant it bet on them. That is a selection-biased
sample of a single family (KXMLBHIT), and it cannot answer "what did the market
say at times we did not bet."

Phase 2's gate (MARKET_EXPANSION_ACTION_PLAN.md 2.7/2.8) is "score the team-level
model offline against historical Kalshi prices." For KXMLBGAME / KXMLBSPREAD /
KXMLBTOTAL that data does not exist and CANNOT BE BACKFILLED. MLB's regular
season ends in early October. Every day this is not running is a day of
permanently lost input to that gate.

Status: read-only. Places no orders. Writes only to --out. Never touches any
        portfolio, ledger, logic_epoch register, or live config.

Usage
-----
    python3 scripts/archive_market_prices.py \\
        --series KXMLBGAME KXMLBSPREAD KXMLBTOTAL KXMLBTEAMTOTAL \\
                 KXMLBF3 KXMLBF5 KXMLBF7 KXMLBF5SPREAD KXMLBF5TOTAL KXMLBHIT \\
        --out exp_output/PRICE_ARCHIVE

Writes one JSONL file per UTC day (prices_YYYY-MM-DD.jsonl), one line per
market per run. Re-running the same day appends; it never rewrites history.

Cron guidance
-------------
Every 15-30 min during 22:00-05:00Z covers the MLB slate. Pacing defaults are
deliberately conservative because T4M-PROJ shares the same production read
budget during exactly that window (Phase 0-C safety directive) -- the live
trading cohort outranks this archive. Raise --pause, never lower it, if T4
shows any degradation.

Depth capture (Phase 0-H / T-412)
----------------------------------
GG-155 was a measurement artifact from hand-sampling depth as a one-off point
estimate (`phase0_market_survey.py depth`, run three times by hand). T-411
found depth swings 14x in 14 minutes on a single series and 67x between two
TEAM_TOTAL reads -- a point estimate cannot distinguish "structurally thin"
from "sampled at a bad moment." `--depth-sample-per-family N` folds a small,
balanced (round-robin across series, reusing phase0_market_survey.py's
`_balanced_sample` so a single series can never dominate a family's sample --
the GG-155 root cause) orderbook sample into every cron run instead, so depth
becomes a genuine time series: N samples/family/run x runs/day accumulates
toward the 200+ observations/family target within about a week without any
further hand-sampling. Depth rows are additive requests on top of the
--series price fetch and share the same --pause floor and T4M-PROJ read-budget
priority -- keep N small (2-3) rather than raising request volume to hit the
target faster.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from phase0_market_survey import (  # noqa: E402
    FAMILY_PATTERNS, _balanced_sample, _book_metrics, _classify, _normalize_book,
)
from typing import Any

DEFAULT_PAUSE_S = 0.30          # ~3.3 req/s — matches phase0_market_survey.py
MAX_RETRIES = 4
MAX_PAGES_PER_SERIES = 40       # bound: refuse to paginate forever on a bad cursor

# Fields worth persisting. Kept explicit rather than dumping the whole record so
# the archive stays compact over a full season, and so a schema change upstream
# surfaces as a missing key rather than silently bloating every row.
#
# Kalshi's /markets response uses the "*_dollars" (decimal-string) / "*_fp"
# convention confirmed live 2026-08-01 (KXMLBHIT sample) -- there is no plain
# "yes_bid" key on the raw record. Archive under stable plain names anyway;
# (source_key, archived_key) pairs make the rename explicit at the one place
# it happens rather than requiring readers to know both conventions.
SNAPSHOT_FIELDS = (
    ("ticker", "ticker"),
    ("event_ticker", "event_ticker"),
    ("status", "status"),
    ("yes_bid_dollars", "yes_bid"),
    ("yes_ask_dollars", "yes_ask"),
    ("no_bid_dollars", "no_bid"),
    ("no_ask_dollars", "no_ask"),
    ("last_price_dollars", "last_price"),
    ("previous_price_dollars", "previous_price"),
    ("volume_fp", "volume"),
    ("volume_24h_fp", "volume_24h"),
    ("open_interest_fp", "open_interest"),
    ("liquidity_dollars", "liquidity"),
    ("close_time", "close_time"),
    ("expiration_time", "expiration_time"),
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _snapshot(market: dict[str, Any], series: str, run_ts: str) -> dict[str, Any]:
    row: dict[str, Any] = {"run_ts": run_ts, "series_ticker": series}
    for src_field, out_field in SNAPSHOT_FIELDS:
        if src_field in market:
            row[out_field] = market[src_field]
    # Derived mid, when both sides are quoted. Stored rather than recomputed so a
    # later change to this convention cannot silently rewrite historical meaning.
    yb, ya = _to_float(market.get("yes_bid_dollars")), _to_float(market.get("yes_ask_dollars"))
    if yb is not None and ya is not None and ya > yb:
        row["yes_mid"] = round((yb + ya) / 2.0, 4)
        row["half_spread"] = round((ya - yb) / 2.0, 4)
    return row


def _fetch_series_markets(client: Any, series: str, pause: float) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    cursor: str | None = None
    for _ in range(MAX_PAGES_PER_SERIES):
        params: dict[str, Any] = {"series_ticker": series, "status": "open", "limit": 200}
        if cursor:
            params["cursor"] = cursor
        data = None
        for attempt in range(MAX_RETRIES):
            ok, resp = client._get("/markets", params=params)
            if ok:
                data = resp
                break
            time.sleep(pause * (2 ** attempt))
        time.sleep(pause)
        if data is None:
            print(f"  {series}: fetch failed, stopping this series", file=sys.stderr)
            break
        page = data.get("markets") or []
        out.extend(m for m in page if isinstance(m, dict))
        cursor = data.get("cursor") or None
        if not cursor or not page:
            break
    return out


def _sample_depth(
    client: Any,
    markets_by_series: dict[str, list[dict[str, Any]]],
    per_family: int,
    pause: float,
    run_ts: str,
) -> list[dict[str, Any]]:
    """Balanced (round-robin across series) orderbook sample, tagged by family.

    Reuses phase0_market_survey.py's classifier and sampler so the family
    taxonomy and the GG-155 fix (no single series may dominate a family's
    sample) have exactly one implementation, not two that can drift apart.
    """
    by_family: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for series, markets in markets_by_series.items():
        family = _classify(series, FAMILY_PATTERNS, "UNCLASSIFIED")
        by_family.setdefault(family, {})[series] = markets

    rows: list[dict[str, Any]] = []
    for family, series_groups in sorted(by_family.items()):
        selection = _balanced_sample(series_groups, per_family)
        n_usable = 0
        for series_ticker, m in selection:
            ticker = m.get("ticker")
            if not ticker:
                continue
            book = None
            for attempt in range(MAX_RETRIES):
                ok, data = client._get(f"/markets/{ticker}/orderbook")
                if ok:
                    book = _normalize_book(data or {})
                    break
                time.sleep(pause * (2 ** attempt))
            time.sleep(pause)
            row: dict[str, Any] = {
                "run_ts": run_ts, "family": family, "series_ticker": series_ticker,
                "ticker": ticker,
            }
            if book is None:
                row.update({"usable": False, "reason": "fetch_failed"})
            else:
                row.update(_book_metrics(book))
                if row.get("usable"):
                    n_usable += 1
            rows.append(row)
        print(f"  depth {family:>18}: sampled {len(selection)} across "
              f"{len(series_groups)} series, usable {n_usable}")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--series", nargs="+", required=True,
                    help="series tickers to archive, e.g. KXMLBGAME KXMLBTOTAL")
    ap.add_argument("--out", default="exp_output/PRICE_ARCHIVE")
    ap.add_argument("--pause", type=float, default=DEFAULT_PAUSE_S,
                    help="seconds between requests; raise, never lower (T4 shares this budget)")
    ap.add_argument("--depth-sample-per-family", type=int, default=0,
                    help="opt-in: balanced orderbook sample size per family per run "
                         "(0 = disabled). Additive request volume -- keep small (2-3); "
                         "see 'Depth capture' in this file's module docstring.")
    args = ap.parse_args()

    if args.pause < DEFAULT_PAUSE_S:
        raise SystemExit(
            f"--pause {args.pause} is below the {DEFAULT_PAUSE_S}s floor. T4M-PROJ shares this "
            "read budget during the in-play window; the live cohort outranks this archive."
        )

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from prediction_market_bot.c5_execution.kalshi_client import (  # noqa: E402
        KalshiMarketClient,
    )

    client = KalshiMarketClient.from_env()
    run_ts = _utc_now_iso()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"prices_{run_ts[:10]}.jsonl"

    total = 0
    per_series: dict[str, int] = {}
    markets_by_series: dict[str, list[dict[str, Any]]] = {}
    with out_path.open("a") as handle:
        for series in args.series:
            markets = _fetch_series_markets(client, series, args.pause)
            for m in markets:
                handle.write(json.dumps(_snapshot(m, series, run_ts)) + "\n")
            per_series[series] = len(markets)
            markets_by_series[series] = markets
            total += len(markets)
            print(f"  {series:20s} {len(markets):5d} markets")

    print(f"{run_ts}  wrote {total} snapshots -> {out_path}")

    if args.depth_sample_per_family > 0:
        depth_rows = _sample_depth(
            client, markets_by_series, args.depth_sample_per_family, args.pause, run_ts
        )
        depth_path = out_dir / f"depth_{run_ts[:10]}.jsonl"
        with depth_path.open("a") as handle:
            for row in depth_rows:
                handle.write(json.dumps(row) + "\n")
        print(f"{run_ts}  wrote {len(depth_rows)} depth samples -> {depth_path}")

    # A run that finds zero open markets across every series is indistinguishable
    # from a broken auth/route/schema path unless it is called out. Off-slate that
    # is legitimate; mid-slate it is a defect. Say so rather than exiting silently
    # clean -- a silent no-op cron is the GG-049 failure shape.
    if total == 0:
        print("WARNING: zero markets returned across all series. Legitimate off-slate; "
              "a defect if games are live. Verify before trusting this run.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
