"""W65.3: NFL QB-shrunk CHALLENGER shadow. EVALUATE-AND-LOG ONLY (pre-registration ACCEPTED 2026-10-10).

Same KXNFLGAME moneyline markets, same T1 timing as the frozen EXP-037 NFL runner, frozen challenger artifact
(models/nfl_qb_challenger_v1.json). Rows go to their own ledger dir tagged sport=NFLQB; no frozen row is read for
writing or altered. Opens no position, submits no order, touches no sizing. Reads the cache the frozen runner's
--refresh maintains (this runner never refreshes it, so both see the same data).

  PYTHONPATH=src:. python3 scripts/run_nfl_qb_challenger_shadow.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import run_pregame_shadow as rps  # noqa: E402  (cache path, code_sha, adapter, strike filter logic reused)
from prediction_market_bot.c1_signal_ingestion.nfl_qb_features import NFLQBFeatureBuilder  # noqa: E402
from prediction_market_bot.pregame_shadow.nfl_forecaster import NFLScheduleIndex, parse_market_ticker  # noqa: E402
from prediction_market_bot.pregame_shadow.nfl_qb_forecaster import NFLQBChallengerForecaster  # noqa: E402
from prediction_market_bot.pregame_shadow.nfl_qb_model import NFLQBChallengerModel  # noqa: E402
from prediction_market_bot.pregame_shadow.runner import run_once  # noqa: E402

CELLS = [("NFL_MONEYLINE", "KXNFLGAME")]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW_NFLQB"))
    ap.add_argument("--model", default=str(ROOT / "models" / "nfl_qb_challenger_v1.json"))
    ap.add_argument("--bands", default="T1")
    ap.add_argument("--now", help="ISO UTC override (testing only)")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    sp = rps.CACHE / "schedule_extended.parquet"
    if not sp.exists():
        raise SystemExit(f"{sp} missing -- the frozen runner's --refresh maintains it")
    sched = pd.read_parquet(sp)
    stats = pd.read_parquet(rps.CACHE / "team_stats.parquet")
    model = NFLQBChallengerModel.load(a.model)       # sha256 verified on load
    index = NFLScheduleIndex(sched)
    fc = NFLQBChallengerForecaster(model, NFLQBFeatureBuilder(stats, sched), index)
    ad = rps.make_adapter()
    ledger_dir = Path(a.ledger_dir)
    if a.dry_run:
        import tempfile
        ledger_dir = Path(tempfile.mkdtemp(prefix="nflqb_dry_"))

    def raw_filter(m: dict) -> bool:
        p = parse_market_ticker(m.get("ticker", ""))
        return p is not None and p["strike"] is None

    run_id = now.strftime("%Y%m%dT%H%M%SZ")
    res = run_once(forecaster=fc, cells=CELLS, list_markets=ad.list_series_markets_raw,
                   kickoff_for=index.kickoff_for_event, ledger_dir=ledger_dir, run_id=run_id,
                   now_utc=now, code_sha=rps.code_sha(), raw_filter=raw_filter,
                   only_bands={b.strip() for b in a.bands.split(",") if b.strip()} or None)
    print(f"run_id={run_id} ledger_dir={ledger_dir}")
    print("written:", res["written"])
    print("skipped:", res["skipped"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
