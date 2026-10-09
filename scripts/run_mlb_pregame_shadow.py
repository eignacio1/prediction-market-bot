"""EXP-037 / T-608: MLB pregame SHADOW evaluator. EVALUATE-AND-LOG ONLY.

12 cells: MLB_MONEYLINE / MLB_RUN_LINE / MLB_GAME_TOTAL / MLB_TEAM_TOTAL x T1/T2/T3. Read-only Kalshi list
reads (<=1 req/s) -> frozen model -> rows in exp_output/PREGAME_SHADOW/MLB_<market_type>_<band>.jsonl.
Opens no position, submits no order, creates no paper fill, touches no sizing, flips no registry status.
Idempotent per (run_id, market_ticker).

  PYTHONPATH=src:. python3 scripts/run_mlb_pregame_shadow.py [--refresh] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from prediction_market_bot.c1_signal_ingestion.mlb_game_pregame_features import MLBGameFeatureBuilder  # noqa: E402
from prediction_market_bot.pregame_shadow.mlb_forecaster import (  # noqa: E402
    MLBForecaster, MLBScheduleIndex, parse_market_ticker)
from prediction_market_bot.pregame_shadow.mlb_model import MLBPregameModel  # noqa: E402
from prediction_market_bot.c5_execution.shadow_flat_stake import make_on_row  # noqa: E402
from prediction_market_bot.pregame_shadow.runner import run_once  # noqa: E402
from run_pregame_shadow import code_sha, make_adapter  # noqa: E402

CELLS = [("MLB_MONEYLINE", "KXMLBGAME"), ("MLB_RUN_LINE", "KXMLBSPREAD"),
         ("MLB_GAME_TOTAL", "KXMLBTOTAL"), ("MLB_TEAM_TOTAL", "KXMLBTEAMTOTAL")]
CACHE = ROOT / "exp_output" / "MLB_GAME" / "cache_w47"
MAX_CACHE_AGE_H = 26      # W55.3b: Stats API 406s the VPS (GG-470); the cache is refreshed off-box and synced in


def assert_cache_fresh(cur: Path, now: datetime, max_age_h: float = MAX_CACHE_AGE_H) -> None:
    """Fail closed: without --refresh, a games cache with no stamp or an old stamp means stale results and
    probable starters would be logged as features. Raises SystemExit."""
    meta = cur.with_name(cur.stem + ".meta.json")
    try:
        ts = datetime.fromisoformat(json.loads(meta.read_text())["refreshed_at"].replace("Z", "+00:00"))
    except (OSError, ValueError, KeyError) as e:
        raise SystemExit(f"{meta} missing/unreadable ({e!r}) -- run scripts/sync_mlb_games_cache.sh; refusing stale cache")
    if now - ts > timedelta(hours=max_age_h):
        raise SystemExit(f"games cache refreshed {ts.isoformat()} is >{max_age_h}h old -- run "
                         "scripts/sync_mlb_games_cache.sh; refusing to log on stale data")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="re-pull Stats API games (results + probable starters)")
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW"))
    ap.add_argument("--model", default=str(ROOT / "models" / "mlb_game_pregame_v1.json"))
    ap.add_argument("--bands", default="")
    ap.add_argument("--now", help="ISO UTC override (testing only)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if a.refresh:
        from fetch_mlb_game_history import main as fetch_main
        if fetch_main(["--recent", "--season", str(now.year), "--today", now.date().isoformat(),
                       "--base", str(CACHE / "games.parquet"), "--out", str(CACHE / "games_current.parquet")]):
            raise SystemExit("games refresh failed -- refusing to run on stale data")
    if not a.refresh:
        assert_cache_fresh(CACHE / "games_current.parquet", now)
    gp = CACHE / "games.parquet"
    if not gp.exists():
        raise SystemExit(f"{gp} missing -- run scripts/fetch_mlb_game_history.py")
    games = pd.read_parquet(gp)
    cur = CACHE / "games_current.parquet"
    if cur.exists():                      # current-season refresh supersedes the history rows for that season
        c = pd.read_parquet(cur)
        games = pd.concat([games[~games.season.isin(c.season.unique())], c], ignore_index=True)
    model = MLBPregameModel.load(a.model)           # sha256 verified on load
    index = MLBScheduleIndex(games)
    fc = MLBForecaster(model, MLBGameFeatureBuilder(games), index)
    ad = make_adapter()
    ledger_dir = Path(tempfile.mkdtemp(prefix="pregame_dry_")) if a.dry_run else Path(a.ledger_dir)

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
                   kickoff_for=index.kickoff_for_event, kickoff_miss_reason=index.miss_reason_for_event, ledger_dir=ledger_dir, run_id=run_id,
                   now_utc=now, code_sha=code_sha(), raw_filter=raw_filter,
                   only_bands=({b.strip() for b in a.bands.split(",") if b.strip()} or None),
                   on_row=make_on_row(ad))
    print(f"run_id={run_id} ledger_dir={ledger_dir}")
    print("written:", res["written"])
    print("skipped:", res["skipped"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
