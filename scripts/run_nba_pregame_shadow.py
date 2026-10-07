"""EXP-038 / W58.2: NBA pregame SHADOW evaluator. EVALUATE-AND-LOG ONLY.

Read-only Kalshi list reads (<=1 req/s) -> frozen model (models/nba_pregame_v1.json, sha256 verified at load)
-> append rows to exp_output/PREGAME_SHADOW/NBA_<market_type>_<band>.jsonl. Opens no position, submits no
order, creates no paper fill, touches no sizing. Schedule/scores come from the ESPN store at data/raw/nba
(kept fresh by scripts/nba_backfill.py; this script makes no ESPN call itself).

  PYTHONPATH=src:. python3 scripts/run_nba_pregame_shadow.py [--bands T1] [--dry-run]
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
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import NBAFeatureBuilder  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_forecaster import (  # noqa: E402
    NBAForecaster, NBAScheduleIndex, parse_market_ticker)
from prediction_market_bot.pregame_shadow.nba_model import NBAPregameModel  # noqa: E402
from prediction_market_bot.pregame_shadow.runner import run_once  # noqa: E402

CELLS = [("NBA_MONEYLINE", "KXNBAGAME"), ("NBA_SPREAD", "KXNBASPREAD"),
         ("NBA_GAME_TOTAL", "KXNBATOTAL"), ("NBA_TEAM_TOTAL", "KXNBATEAMTOTAL")]
SEASONS = (2026, 2027)       # ESPN season year = the year the season ends; 2026 = 2025-26 history, 2027 = 2026-27


def code_sha() -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def load_games(root: Path) -> list[dict]:
    games: list[dict] = []
    for s in SEASONS:
        games.extend(N.load_season(s, root)["games"].values())
    return games


def make_adapter():
    from prediction_market_bot.c5_execution.kalshi_client import KalshiMarketClient
    from prediction_market_bot.c5_execution.venue_adapter import KalshiVenueAdapter
    try:
        return KalshiVenueAdapter.from_env()
    except Exception:
        return KalshiVenueAdapter(KalshiMarketClient("public-read-only-no-auth"))


def raw_filter(m: dict) -> bool:                    # strike in ticker must equal floor_strike
    p = parse_market_ticker(m.get("ticker", ""))
    if p is None:
        return False
    if p["strike"] is None:
        return True
    try:
        return abs(float(m.get("floor_strike")) - p["strike"]) < 1e-9
    except (TypeError, ValueError):
        return False


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw" / "nba"))
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW"))
    ap.add_argument("--model", default=str(ROOT / "models" / "nba_pregame_v1.json"))
    ap.add_argument("--bands", default="", help="comma list of T1,T2,T3 (default: all in-window)")
    ap.add_argument("--now", help="ISO UTC override (testing only)")
    ap.add_argument("--dry-run", action="store_true", help="evaluate into a throwaway ledger dir")
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    games = load_games(Path(a.raw))
    if not games:
        raise SystemExit(f"no NBA games under {a.raw} -- run scripts/nba_backfill.py first")
    model = NBAPregameModel.load(a.model)           # sha256 verified on load
    index = NBAScheduleIndex(games)
    fc = NBAForecaster(model, NBAFeatureBuilder(games), index)
    ledger_dir = Path(a.ledger_dir)
    if a.dry_run:
        import tempfile
        ledger_dir = Path(tempfile.mkdtemp(prefix="nba_pregame_dry_"))
    ad = make_adapter()
    run_id = now.strftime("%Y%m%dT%H%M%SZ")
    res = run_once(forecaster=fc, cells=CELLS, list_markets=ad.list_series_markets_raw,
                   kickoff_for=index.kickoff_for_event, ledger_dir=ledger_dir, run_id=run_id,
                   now_utc=now, code_sha=code_sha(), raw_filter=raw_filter,
                   only_bands=({b.strip() for b in a.bands.split(",") if b.strip()} or None))
    print(f"run_id={run_id} ledger_dir={ledger_dir}")
    print("written:", dict(res["written"]))
    print("skipped:", dict(res["skipped"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
