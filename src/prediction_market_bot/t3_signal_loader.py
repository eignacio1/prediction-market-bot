"""
T3 signal loader — reads PIPE-06 output for PIPE-03 momentum overlay.

Isolated module so PIPE-03 and tests can import this without triggering
the BOT_ENV guard in run_paper_trade.py.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

# 15 min staleness guard; matches PIPE-06 cron interval (*/15 21-23 * * *)
T3_MAX_STALENESS_S: int = 900


def load_t3_signals(log_dir: Path, game_date: str) -> dict[str, str]:
    """Return {kalshi_ticker: momentum_signal} from the most recent PIPE-06 report.

    Non-contamination guarantee: returns {} if no report exists, the report is
    stale (run_at older than T3_MAX_STALENESS_S), or any parse error occurs.
    An empty dict causes every mkt.ticker lookup to return "NEUTRAL", leaving
    the T1 edge untouched — identical to a run with no T3 integration.
    """
    candidates = sorted(log_dir.glob(f"t3_{game_date}_*.json"), reverse=True)
    if not candidates:
        return {}
    try:
        report = json.loads(candidates[0].read_text())
        run_at_str = report.get("run_at", "")
        if run_at_str:
            run_at = datetime.fromisoformat(run_at_str.rstrip("Z")).replace(tzinfo=timezone.utc)
            if (datetime.now(timezone.utc) - run_at).total_seconds() > T3_MAX_STALENESS_S:
                return {}
        return {fc["kalshi_ticker"]: fc["momentum_signal"]
                for fc in report.get("forecasts", [])}
    except Exception:
        return {}
