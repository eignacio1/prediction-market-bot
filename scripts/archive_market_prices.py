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
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_PAUSE_S = 0.30          # ~3.3 req/s — matches phase0_market_survey.py
MAX_RETRIES = 4
MAX_PAGES_PER_SERIES = 40       # bound: refuse to paginate forever on a bad cursor

# Fields worth persisting. Kept explicit rather than dumping the whole record so
# the archive stays compact over a full season, and so a schema change upstream
# surfaces as a missing key rather than silently bloating every row.
SNAPSHOT_FIELDS = (
    "ticker", "event_ticker", "status", "yes_bid", "yes_ask", "no_bid", "no_ask",
    "last_price", "previous_price", "volume", "volume_24h", "open_interest",
    "liquidity", "close_time", "expiration_time",
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _snapshot(market: dict[str, Any], series: str, run_ts: str) -> dict[str, Any]:
    row: dict[str, Any] = {"run_ts": run_ts, "series_ticker": series}
    for field in SNAPSHOT_FIELDS:
        if field in market:
            row[field] = market[field]
    # Derived mid, when both sides are quoted. Stored rather than recomputed so a
    # later change to this convention cannot silently rewrite historical meaning.
    yb, ya = market.get("yes_bid"), market.get("yes_ask")
    if isinstance(yb, (int, float)) and isinstance(ya, (int, float)) and ya > yb:
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


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--series", nargs="+", required=True,
                    help="series tickers to archive, e.g. KXMLBGAME KXMLBTOTAL")
    ap.add_argument("--out", default="exp_output/PRICE_ARCHIVE")
    ap.add_argument("--pause", type=float, default=DEFAULT_PAUSE_S,
                    help="seconds between requests; raise, never lower (T4 shares this budget)")
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
    with out_path.open("a") as handle:
        for series in args.series:
            markets = _fetch_series_markets(client, series, args.pause)
            for m in markets:
                handle.write(json.dumps(_snapshot(m, series, run_ts)) + "\n")
            per_series[series] = len(markets)
            total += len(markets)
            print(f"  {series:20s} {len(markets):5d} markets")

    print(f"{run_ts}  wrote {total} snapshots -> {out_path}")

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
