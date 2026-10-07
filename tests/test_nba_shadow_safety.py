"""W58.2: NBA shadow runner/settle/cron are evaluate-and-log only; cron block is additive and well-formed."""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from prediction_market_bot.c1_signal_ingestion import nba_ingest as N

ROOT = Path(__file__).resolve().parent.parent
FORBIDDEN = ("submit_order", "open_position", "exit_position", "settle_position", "place_order", "PaperTrader",
             "kelly_fraction", "evaluate_forecast", "c4_risk_engine", "paper_trader", "venue_router", "get_band_config")
SCRIPTS = ("run_nba_pregame_shadow.py", "run_nba_pregame_shadow_settle.py", "nba_backfill.py")
CONF = (ROOT / "deploy" / "cron.nba_shadow").read_text()


def test_scripts_have_no_order_or_sizing_path():
    for s in SCRIPTS:
        txt = (ROOT / "scripts" / s).read_text()
        for tok in FORBIDDEN:
            assert tok not in txt, f"{s} mentions {tok}"


def _jobs():
    return [l for l in CONF.splitlines() if l.strip() and not l.startswith("#")]


def test_cron_block_markers_and_scripts_only_nba():
    assert CONF.splitlines()[0] == "# BEGIN EXP-038 NBA" and CONF.rstrip().splitlines()[-1] == "# END EXP-038 NBA"
    for j in _jobs():
        assert re.search(r"scripts/(run_nba_pregame_shadow(_settle)?|nba_backfill)\.py", j), j
        assert "kelly" not in j and ".env" not in j


def test_cron_minutes_off_00_30_and_unique_to_other_sports():
    for j in _jobs():
        for m in (int(x) for x in j.split()[0].split(",")):
            assert m not in (0, 30), j
    t1 = [int(j.split()[0]) for j in _jobs() if "--bands T1" in j]
    assert t1 == [11]


def test_backfill_lookahead_fetches_future_dates_and_refetches(tmp_path):
    seen = []
    def fetch(d, th):
        seen.append(d)
        return []
    today = date(2026, 10, 6)
    N.backfill_season(2027, None, tmp_path, today=today, fetch=fetch, lookahead_days=3)
    assert max(seen) == date(2026, 10, 9)
    seen.clear()
    N.backfill_season(2027, None, tmp_path, today=today, fetch=fetch, lookahead_days=3)
    assert date(2026, 10, 9) in seen and date(2026, 10, 1) not in seen   # future refetched, old skipped
