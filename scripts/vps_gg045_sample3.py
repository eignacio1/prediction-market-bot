#!/usr/bin/env python3
"""One-shot VPS runner for GG-045 sample 3 (late-innings depth pull).

Scheduled via systemd-run for ~23:05Z 2026-07-19 so the pull happens even if
the operator session's laptop is asleep (ScheduleWakeup timers are
session-local). ESPN-gates per APR-0029 D2, then does targeted per-ticker
pulls on all open KXMLBHIT markets belonging to live games, using the fixed
orderbook_fp parser in scripts/query_orderbook_depth_mlb.py.

Writes:
  logs/espn_scoreboard_<ts>.json
  logs/orderbook_depth_mlb_<ts>.json  (sample_label sample3_late_innings)
  logs/gg045_sample3_runner.log       (stdout/err via systemd-run capture)
Exit codes: 0 = artifact written; 2 = D2 gate failed (no live games); 1 = error.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))
sys.path.insert(0, str(project_root / "scripts"))

import query_orderbook_depth_mlb as q  # noqa: E402
from prediction_market_bot.c5_execution.kalshi_client import (  # noqa: E402
    KalshiMarketClient,
    SERIES_MLB_PLAYER_HITS,
)

ESPN_URL = "https://site.api.espn.com/apis/site/v2/sports/baseball/mlb/scoreboard"

# ESPN team abbreviations -> Kalshi ticker code fragments. Kalshi concatenates
# away+home codes (e.g. NYM @ PHI -> ...NYMPHI-...). Codes match ESPN's except
# where noted below; extend the map if a game fails to match any market.
ESPN_TO_KALSHI = {"WSH": "WSH", "ATH": "ATH", "CHW": "CHW", "SD": "SD", "KC": "KC",
                  "SF": "SF", "TB": "TB"}


def main() -> int:
    ts = datetime.now(timezone.utc)
    stamp = ts.strftime("%Y%m%d_%H%M%S")
    log_dir = project_root / "logs"

    with urllib.request.urlopen(ESPN_URL, timeout=30) as resp:
        scoreboard = json.load(resp)
    espn_path = log_dir / f"espn_scoreboard_{stamp}.json"
    espn_path.write_text(json.dumps(scoreboard))

    live_games = []
    for ev in scoreboard.get("events", []):
        comp = ev["competitions"][0]
        if comp["status"]["type"]["state"] == "in":
            away = comp["competitors"][1]["team"]["abbreviation"]
            home = comp["competitors"][0]["team"]["abbreviation"]
            # ESPN lists home first in competitors; shortName is "AWY @ HOM"
            short = ev.get("shortName", f"{away} @ {home}")
            a, h = short.split(" @ ")
            code = ESPN_TO_KALSHI.get(a, a) + ESPN_TO_KALSHI.get(h, h)
            detail = comp["status"]["type"].get("shortDetail", "")
            live_games.append({"shortName": short, "code": code, "detail": detail})

    print(f"[{ts.isoformat()}] live games: {len(live_games)} -> {[g['shortName'] for g in live_games]}")
    if not live_games:
        print("D2 gate FAILED: no games in state 'in' — no pull. (Artifact not written.)")
        return 2

    client = KalshiMarketClient.from_env()
    ok, snap = client.fetch_player_points_markets(status="open", series_ticker=SERIES_MLB_PLAYER_HITS)
    if not ok:
        print("ERROR: market fetch failed")
        return 1
    codes = [g["code"] for g in live_games]
    targets = [m for m in snap.markets if any(c in m.ticker for c in codes)]
    print(f"open KXMLBHIT: {len(snap.markets)}; live-game matched: {len(targets)}")

    results = []
    for m in targets:
        raw = q.fetch_orderbook(client, m.ticker)
        if raw is None:
            results.append({"ticker": m.ticker, "status": getattr(m, "status", "unknown"),
                            "metrics": None, "error": True})
            continue
        results.append({
            "ticker": m.ticker,
            "status": getattr(m, "status", "unknown"),
            "close_time": str(getattr(m, "close_time", None)),
            "market_quote": {"yes_bid": getattr(m, "yes_bid", None),
                             "yes_ask": getattr(m, "yes_ask", None),
                             "volume": getattr(m, "volume", None)},
            "metrics": q.compute_depth_metrics(raw),
            "raw_orderbook": raw,
            "error": False,
        })

    audit = {
        "timestamp": ts.isoformat(),
        "task": "T-TBD (Terminal C, GG-045 live-window depth pull)",
        "governance_gap": "GG-045",
        "sample_label": "sample3_late_innings",
        "note": ("Late-innings sample, 2026-07-19 slate, executed on VPS via systemd-run "
                 "one-shot (operator laptop not guaranteed awake). Targeted per-ticker pulls "
                 "on live-game markets. orderbook_fp qty column assumed = contract count."),
        "live_games_espn": live_games,
        "espn_snapshot_file": espn_path.name,
        "live_cap_usd": q.LIVE_CAP_USD,
        "impact_threshold_pct": q.DEPTH_IMPACT_THRESHOLD_PCT,
        "results": results,
    }
    out = log_dir / f"orderbook_depth_mlb_{stamp}.json"
    out.write_text(json.dumps(audit, indent=2))

    vals = sorted(r["metrics"]["combined_depth_usd"] for r in results if r.get("metrics"))
    nz = [v for v in vals if v > 0]
    if nz:
        import statistics
        print(f"sampled {len(vals)} | nonzero {len(nz)} | min ${nz[0]:.2f} med ${statistics.median(nz):.2f} "
              f"mean ${statistics.mean(nz):.2f} max ${nz[-1]:.2f}")
    print(f"artifact: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
