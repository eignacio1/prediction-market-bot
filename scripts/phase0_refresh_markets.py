#!/usr/bin/env python3
"""
Phase 0-D — refresh open-market listing for a known set of MLB series tickers.

Purpose: markets_sample.json (Phase 0-A, 2026-07-31) is a frozen capture --
most of its tickers have since resolved. Re-running the `depth` subcommand
against it during a live slate would sample dead markets and reproduce
GG-155's "player props have no depth" result for a spurious reason (empty
books on resolved tickers, not thin real depth). This script re-fetches
CURRENT status=open markets for the same 220 MLB-family series tickers
(the series list itself is stable; only which markets are open changes
day to day), unauthenticated production path, full cursor pagination,
and writes a NEW timestamped file in the same
{"markets_by_series": {series: {"ok":.., "count":.., "markets":[...]}}}
shape phase0_market_survey.py already consumes.

Read-only. Places no orders. Touches no portfolio/ledger/logic_epoch file.
Paced identically to phase0_market_survey.py (REQUEST_PAUSE_S) since T4M-PROJ
shares the same live read budget during its in-play window.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REQUEST_PAUSE_S = 0.30
MAX_RETRIES = 5


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: phase0_refresh_markets.py <series_source.json> <out.json>", file=sys.stderr)
        return 2
    src_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient

    src = json.loads(src_path.read_text())
    series_tickers = sorted(src.get("markets_by_series", {}).keys())
    if not series_tickers:
        raise SystemExit(f"no series tickers found in {src_path}")

    client = KalshiMarketClient.from_env()
    out: dict = {
        "refreshed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_series_list": str(src_path),
        "markets_by_series": {},
    }

    total_open = 0
    for series_ticker in series_tickers:
        all_markets: list[dict] = []
        cursor = None
        ok_overall = True
        while True:
            params = {"limit": 200, "status": "open", "series_ticker": series_ticker}
            if cursor:
                params["cursor"] = cursor
            ok, data = None, None
            for attempt in range(MAX_RETRIES):
                ok, data = client._get("/markets", params=params)
                if ok:
                    break
                time.sleep(REQUEST_PAUSE_S * (2 ** attempt))
            time.sleep(REQUEST_PAUSE_S)
            if not ok:
                ok_overall = False
                break
            page = (data or {}).get("markets", [])
            all_markets.extend(page)
            cursor = (data or {}).get("cursor")
            if not cursor or len(page) < 200:
                break

        out["markets_by_series"][series_ticker] = {
            "ok": ok_overall,
            "count": len(all_markets),
            "markets": all_markets,
        }
        total_open += len(all_markets)
        print(f"{series_ticker:>24}: open={len(all_markets)}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2))
    print(f"wrote {out_path} — {len(series_tickers)} series, {total_open} open markets total")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
