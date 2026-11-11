"""EXP-047 / W109.3 (B-070): NBA engine player rebounds/assists/threes pregame SHADOW evaluator. EVALUATE-AND-LOG ONLY.

Public ESPN scoreboard/summary GETs (incremental box-score store + upcoming tip times) and read-only Kalshi list
reads (series KXNBAREB/KXNBAAST/KXNBA3PT) -> nba_engine_v2 draws -> props split -> rows appended to
exp_output/PREGAME_SHADOW_EXP047/NBAENG_<MARKET_TYPE>_<band>.jsonl. No order, no position, no fill, no sizing
(there is no ``on_row``). Pre-registration: 05_RESEARCH_EXPERIMENTS/EXP047_*.md.

  PYTHONPATH=src:. python3 scripts/run_nba_engine_props_shadow.py [--bands T1] [--no-refresh] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot.c1_signal_ingestion.nba_ingest import kalshi_code  # noqa: E402
from prediction_market_bot.pregame_shadow import nba_engine_props_forecaster as F  # noqa: E402
from prediction_market_bot.pregame_shadow.runner import run_once  # noqa: E402

CELLS = [("NBA_PLAYER_REBOUNDS", "KXNBAREB"), ("NBA_PLAYER_ASSISTS", "KXNBAAST"), ("NBA_PLAYER_THREES", "KXNBA3PT")]
SEASON_START = date(2026, 10, 20)
SB = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates="
SUM = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/summary?event="


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


def _get(url: str):
    for i in range(3):
        try:
            return json.load(urllib.request.urlopen(url, timeout=25))
        except Exception:
            time.sleep(1 + i)
    return None


def refresh(store: Path, tips_path: Path, now: datetime) -> None:
    """Incremental: add newly completed games' box scores; rewrite tip times for today..today+2 (ET-ish dates)."""
    box = json.loads(store.read_text()) if store.exists() else {}
    d, today = SEASON_START, (now - timedelta(hours=5)).date()
    tips = {}
    while d <= today + timedelta(days=2):
        sb = _get(SB + d.strftime("%Y%m%d"))
        for e in (sb or {}).get("events", []):
            comp = e["competitions"][0]["competitors"]
            if e["status"]["type"]["completed"] and e["id"] not in box:
                s = _get(SUM + e["id"])
                time.sleep(0.5)
                if s:
                    box[e["id"]] = {"date": d.isoformat(), "box": s["boxscore"], "hdr": [
                        c["team"]["abbreviation"] + ":" + str(c.get("homeAway")) + ":" + str(c.get("score")) for c in comp]}
            elif not e["status"]["type"]["completed"] and d >= today:
                k = d.isoformat() + "|" + "|".join(sorted(kalshi_code(c["team"]["abbreviation"]) for c in comp))
                tips[k] = e["date"]
        d += timedelta(days=1)
    store.parent.mkdir(parents=True, exist_ok=True)
    store.write_text(json.dumps(box))
    tips_path.write_text(json.dumps(tips))


def load_tips(path: Path) -> dict:
    out = {}
    if path.exists():
        for k, v in json.loads(path.read_text()).items():
            ds, a, b = k.split("|")
            t = datetime.fromisoformat(v.replace("Z", "+00:00"))
            out[(ds, frozenset((a, b)))] = t if t.tzinfo else t.replace(tzinfo=timezone.utc)
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw" / "nba_props"))
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW_EXP047"))
    ap.add_argument("--bands", default="", help="comma list of T1,T2,T3 (default: all in-window)")
    ap.add_argument("--no-refresh", action="store_true", help="use the stores as they are (no ESPN calls)")
    ap.add_argument("--now", help="ISO UTC override (testing only)")
    ap.add_argument("--dry-run", action="store_true", help="evaluate into a throwaway ledger dir")
    a = ap.parse_args(argv)
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    raw = Path(a.raw)
    store, tips_path = raw / "box.json", raw / "tips.json"
    if not a.no_refresh:
        refresh(store, tips_path, now)
    if not store.exists():
        raise SystemExit(f"no box-score store at {store} -- run without --no-refresh once")
    games, pl = F.parse_box(json.loads(store.read_text()))
    fc = F.NBAEngineProps(games, pl, load_tips(tips_path))
    ledger_dir = Path(a.ledger_dir)
    if a.dry_run:
        import tempfile
        ledger_dir = Path(tempfile.mkdtemp(prefix="nba_engprops_dry_"))
    ad = make_adapter()
    run_id = now.strftime("%Y%m%dT%H%M%SZ")

    res = run_once(forecaster=fc, cells=CELLS, list_markets=ad.list_series_markets_raw,
                   kickoff_for=lambda ev: fc.kickoff_for_event(ev), ledger_dir=ledger_dir, run_id=run_id,
                   now_utc=now, code_sha=code_sha(),
                   raw_filter=lambda m: F.parse_market_ticker(m.get("ticker", "")) is not None,
                   only_bands=({b.strip() for b in a.bands.split(",") if b.strip()} or None), on_row=None)
    print(f"run_id={run_id} ledger_dir={ledger_dir}")
    print("written:", dict(res["written"]))
    print("skipped:", dict(res["skipped"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
