"""EXP-037 / T-608: NFL pregame SHADOW evaluator. EVALUATE-AND-LOG ONLY.

Read-only Kalshi list reads (<=1 req/s, halved on 429) -> frozen model -> append rows to
exp_output/PREGAME_SHADOW/<sport>_<market_type>_<band>.jsonl. Opens no position, submits no
order, creates no paper fill, touches no sizing. Idempotent per (run_id, market_ticker).

  PYTHONPATH=src:. python3 scripts/run_pregame_shadow.py [--refresh] [--dry-run]
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot.c1_signal_ingestion.nfl_pregame_features import NFLPregameFeatureBuilder  # noqa: E402
from prediction_market_bot.pregame_shadow.nfl_forecaster import (  # noqa: E402
    NFLForecaster, NFLScheduleIndex, parse_market_ticker)
from prediction_market_bot.pregame_shadow.nfl_model import NFLPregameModel  # noqa: E402
from prediction_market_bot.pregame_shadow.runner import run_once  # noqa: E402

CELLS = [("NFL_MONEYLINE", "KXNFLGAME"), ("NFL_SPREAD", "KXNFLSPREAD"),
         ("NFL_GAME_TOTAL", "KXNFLTOTAL"), ("NFL_TEAM_TOTAL", "KXNFLTEAMTOTAL")]
CACHE = ROOT / "exp_output" / "NFL" / "cache_w47"
FIRST_SEASON = 2015


def code_sha() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def refresh_cache(now: datetime) -> None:
    """Re-pull nflverse schedule (extended: gametime) + team stats. Read-only public data."""
    from prediction_market_bot.c1_signal_ingestion.nfl_ingestion import NFLIngestionClient
    from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
    CACHE.mkdir(parents=True, exist_ok=True)
    cl = NFLIngestionClient(logger=AuditLogger(str(CACHE / "ingest_audit.jsonl"), min_severity="INFO"),
                            snapshot_id="EXP037-PREGAME")
    seasons = list(range(FIRST_SEASON, now.year + 1))
    ok, sched = cl.fetch_schedule(seasons=seasons, include_extended=True)
    if not ok or "gametime" not in sched.columns:
        raise SystemExit("schedule refresh failed or lacks gametime -- refusing to run on stale/partial data")
    ok, stats = cl.fetch_team_stats_bulk(seasons)
    if not ok:
        raise SystemExit("team stats refresh failed -- refusing to run on partial data")
    sched.to_parquet(CACHE / "schedule_extended.parquet")
    stats.to_parquet(CACHE / "team_stats.parquet")


def make_adapter():
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
    from prediction_market_bot.c5_execution.venue_adapter import KalshiVenueAdapter
    try:
        return KalshiVenueAdapter.from_env()
    except Exception:
        # Market list reads are public/unauthenticated; no key and no private key => no order path.
        return KalshiVenueAdapter(KalshiMarketClient("public-read-only-no-auth"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW"))
    ap.add_argument("--model", default=str(ROOT / "models" / "nfl_pregame_v1.json"))
    ap.add_argument("--bands", default="", help="comma list of T1,T2,T3 to evaluate (default: all in-window)")
    ap.add_argument("--now", help="ISO UTC override (testing only)")
    ap.add_argument("--dry-run", action="store_true", help="evaluate into a throwaway ledger dir")
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if a.refresh:
        refresh_cache(now)
    sp = CACHE / "schedule_extended.parquet"
    if not sp.exists():
        raise SystemExit(f"{sp} missing -- run with --refresh")
    sched = pd.read_parquet(sp)
    stats = pd.read_parquet(CACHE / "team_stats.parquet")
    model = NFLPregameModel.load(a.model)           # sha256 verified on load
    index = NFLScheduleIndex(sched)
    fc = NFLForecaster(model, NFLPregameFeatureBuilder(stats, sched), index)
    ad = make_adapter()
    ledger_dir = Path(a.ledger_dir)
    if a.dry_run:
        import tempfile
        ledger_dir = Path(tempfile.mkdtemp(prefix="pregame_dry_"))

    def raw_filter(m: dict) -> bool:                # strike in ticker must equal floor_strike
        p = parse_market_ticker(m.get("ticker", ""))
        if p is None:
            return False
        if p["strike"] is None:
            return True
        try:
            return abs(float(m.get("floor_strike")) - p["strike"]) < 1e-9
        except (TypeError, ValueError):
            return False

    run_id = now.strftime("%Y%m%dT%H%M%SZ")
    res = run_once(forecaster=fc, cells=CELLS, list_markets=ad.list_series_markets_raw,
                   kickoff_for=index.kickoff_for_event, ledger_dir=ledger_dir, run_id=run_id,
                   now_utc=now, code_sha=code_sha(), raw_filter=raw_filter,
                   only_bands=({b.strip() for b in a.bands.split(",") if b.strip()} or None))
    print(f"run_id={run_id} ledger_dir={ledger_dir}")
    print("written:", res["written"])
    print("skipped:", res["skipped"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
