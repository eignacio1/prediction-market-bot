"""EXP-039 / W65.1: NBA player-points pregame SHADOW evaluator. EVALUATE-AND-LOG ONLY.

Read-only Kalshi list reads (<=1 req/s, series KXNBAPTS) -> frozen model (models/nba_player_points_v1.json,
sha256 verified at load) -> rows appended to exp_output/PREGAME_SHADOW/NBA_NBA_PLAYER_POINTS_<band>.jsonl.
Opens no position, submits no order, creates no paper fill, touches no sizing. Schedule and box scores come from
the ESPN stores at data/raw/nba (kept fresh by scripts/nba_backfill.py and scripts/nba_player_box_backfill.py;
this script makes no ESPN call itself).

  PYTHONPATH=src:. python3 scripts/run_nba_player_points_shadow.py [--bands T1] [--preseason] [--dry-run]
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot.c1_signal_ingestion import nba_ingest as N  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_player_ingest as P  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_player_features import PlayerFeatureBuilder  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_forecaster import NBAScheduleIndex  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_player_points_forecaster import (  # noqa: E402
    MARKET_TYPE, SERIES, NBAPlayerPointsForecaster, kickoff_for_event, parse_market_ticker)
from prediction_market_bot.pregame_shadow.nba_player_points_model import NBAPlayerPointsModel  # noqa: E402
from prediction_market_bot.c5_execution.shadow_flat_stake import make_on_row  # noqa: E402
from prediction_market_bot.pregame_shadow.runner import run_once  # noqa: E402

CELLS = [(MARKET_TYPE, SERIES)]
PRESEASON_DIR = "PREGAME_SHADOW_PRESEASON"
PRESEASON_LABEL = {"season_phase": "preseason", "excluded_from_judged_n": True}
SEASONS = (2026, 2027)       # ESPN season year = the year the season ends; 2026 = 2025-26 history, 2027 = 2026-27


def code_sha() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def make_adapter():
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
    from prediction_market_bot.c5_execution.venue_adapter import KalshiVenueAdapter
    try:
        return KalshiVenueAdapter.from_env()
    except Exception:
        return KalshiVenueAdapter(KalshiMarketClient("public-read-only-no-auth"))


def raw_filter(m: dict) -> bool:                    # strike in ticker must equal floor_strike (= n - 0.5)
    p = parse_market_ticker(m.get("ticker", ""))
    if p is None:
        return False
    try:
        return abs(float(m.get("floor_strike")) - p["strike"]) < 1e-9
    except (TypeError, ValueError):
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw" / "nba"))
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW"))
    ap.add_argument("--model", default=str(ROOT / "models" / "nba_player_points_v1.json"))
    ap.add_argument("--bands", default="", help="comma list of T1,T2,T3 (default: all in-window)")
    ap.add_argument("--preseason", action="store_true",
                    help="evaluate PRESEASON games into exp_output/PREGAME_SHADOW_PRESEASON (rows labelled "
                         "excluded_from_judged_n; never mixed into the judged ledgers)")
    ap.add_argument("--now", help="ISO UTC override (testing only)")
    ap.add_argument("--dry-run", action="store_true", help="evaluate into a throwaway ledger dir")
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    raw = Path(a.raw)
    games = [g for s in SEASONS for g in N.load_season(s, raw)["games"].values()]
    if not games:
        raise SystemExit(f"no NBA games under {a.raw} -- run scripts/nba_backfill.py first")
    stores = [P.load_players(s, raw) for s in SEASONS]
    model = NBAPlayerPointsModel.load(a.model)       # sha256 verified on load
    index = NBAScheduleIndex(games, season_types=(1,) if a.preseason else (2,))
    fc = NBAPlayerPointsForecaster(model, PlayerFeatureBuilder(games, stores), index, lambda g: g["season"])
    ledger_dir = Path(a.ledger_dir)
    extra = None
    if a.preseason:
        if a.ledger_dir == str(ROOT / "exp_output" / "PREGAME_SHADOW"):
            ledger_dir = ROOT / "exp_output" / PRESEASON_DIR
        if ledger_dir.name == "PREGAME_SHADOW":
            raise SystemExit("--preseason must not write into the judged PREGAME_SHADOW ledgers")
        extra = dict(PRESEASON_LABEL)
    if a.dry_run:
        import tempfile
        ledger_dir = Path(tempfile.mkdtemp(prefix="nba_pts_dry_"))
    ad = make_adapter()
    run_id = now.strftime("%Y%m%dT%H%M%SZ")
    res = run_once(forecaster=fc, cells=CELLS, list_markets=ad.list_series_markets_raw,
                   kickoff_for=lambda ev: kickoff_for_event(index, ev), ledger_dir=ledger_dir, run_id=run_id,
                   now_utc=now, code_sha=code_sha(), raw_filter=raw_filter,
                   only_bands=({b.strip() for b in a.bands.split(",") if b.strip()} or None),
                   on_row=None if (a.preseason or a.dry_run) else make_on_row(ad),   # preseason/dry-run rows never stake
                   ledger_extra=extra)
    print(f"run_id={run_id} ledger_dir={ledger_dir}")
    print("written:", dict(res["written"]))
    print("skipped:", dict(res["skipped"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
