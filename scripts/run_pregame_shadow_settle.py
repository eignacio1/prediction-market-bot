"""EXP-037 / T-608: NFL pregame shadow SETTLEMENT JOIN. Outcome join only -- computes NO Brier,
log-loss or E_net statistic (pre-registration: no scoring before a cell reaches its judged n).

Reads exp_output/PREGAME_SHADOW/NFL_*_{T1,T2,T3}.jsonl, takes the FIRST row per (market_ticker, band),
and for every game with a final score in the nflverse schedule appends the row + y + p_clim + game_key
to exp_output/PREGAME_SHADOW/settled/<same name>.jsonl (idempotent per (market_ticker, band)).
Opens no position, submits no order, touches no pool or sizing. Read-only public data.

  PYTHONPATH=src:. python3 scripts/run_pregame_shadow_settle.py [--refresh]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from prediction_market_bot.pregame_shadow.nfl_forecaster import (  # noqa: E402
    NFLScheduleIndex, parse_market_ticker)
from prediction_market_bot.pregame_shadow.nfl_settlement import join_row, typed_join  # noqa: E402
from prediction_market_bot.pregame_shadow.settle_result import FINAL, LOOKUP_FAILED  # noqa: E402
from prediction_market_bot.pregame_shadow.scoring import first_row_per_market  # noqa: E402


def _alarm(alarms, cell: str, row: dict, reason: str) -> None:
    """GG-751: a LOOKUP_FAILED is surfaced, never waited on."""
    if alarms is not None:
        alarms.append({"cell": cell, "market_ticker": row.get("market_ticker"), "reason": reason})


def sweep_nfl_positions() -> int:
    """GG-746: close NFL game-market paper positions whose Kalshi market has settled (ADR-0071).
    No cron resolved this book; it rides the existing daily settle cron. Missing portfolio -> skipped."""
    pf = ROOT / "logs" / "paper_portfolio_t1_nfl_game_market.json"
    if not pf.exists():
        print("position_sweep: portfolio not found, skipped")
        return 0
    from prediction_market_bot.position_sweep import sweep_open_positions
    rep = sweep_open_positions(pf, ROOT / "logs" / "audit_t1_nfl_game_market.jsonl", apply=True)
    print("position_sweep:", json.dumps({k: rep[k] for k in ("open_before", "booked", "open_after")}))
    for a in rep["alarms"]:
        print("ALARM LOOKUP_FAILED position:", json.dumps(a), file=sys.stderr)
    return len(rep["alarms"])


def settle(ledger_dir: Path, sched: pd.DataFrame, clim: dict, prefix: str = "NFL",
           alarms: "list | None" = None, now=None) -> dict:
    finals = {}
    for r in sched[sched.home_score.notna() & sched.away_score.notna()].itertuples():
        finals[(str(r.gameday), frozenset((r.home_team, r.away_team)))] = (
            r.home_team, r.away_team, float(r.home_score), float(r.away_score))
    out_dir = ledger_dir / "settled"
    counts: dict[str, int] = {}
    for path in sorted(ledger_dir.glob(f"{prefix}_*_T[123].jsonl")):
        rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        out_path = out_dir / path.name
        have = set()
        if out_path.exists():
            have = {(j["market_ticker"], j["band"]) for j in
                    (json.loads(x) for x in out_path.read_text().splitlines() if x.strip())}
        new = []
        for r in first_row_per_market(rows):
            if (r["market_ticker"], r["band"]) in have:
                continue
            p = parse_market_ticker(r["market_ticker"])
            if p is None:                      # GG-751: unparseable is an alarm, not a silent skip
                _alarm(alarms, path.stem, r, "unparseable_ticker")
                continue
            fin = finals.get((p["game_date"], frozenset((p["home"], p["away"]))))
            res = typed_join(r, p["game_date"], fin, clim, now)
            if res.status == FINAL:
                new.append(res.outcome)
            elif res.status == LOOKUP_FAILED:
                _alarm(alarms, path.stem, r, res.reason)
        if new:
            out_dir.mkdir(parents=True, exist_ok=True)
            with out_path.open("a") as fh:
                for j in new:
                    fh.write(json.dumps(j) + "\n")
        counts[path.stem] = len(new)
    return counts


def settle_mlb(ledger_dir: Path, games: pd.DataFrame, alarms: "list | None" = None, now=None) -> dict:
    """GG-472: MLB outcome join from the games cache. Same idempotent first-row-per-(market, band) contract."""
    from prediction_market_bot.pregame_shadow import mlb_settlement as ms
    from prediction_market_bot.pregame_shadow.mlb_forecaster import parse_market_ticker as mlb_parse
    finals = ms.final_games(games)
    out_dir = ledger_dir / "settled"
    counts: dict[str, int] = {}
    for path in sorted(ledger_dir.glob("MLB_*_T[123].jsonl")):
        rows = [json.loads(x) for x in path.read_text().splitlines() if x.strip()]
        out_path = out_dir / path.name
        have = set()
        if out_path.exists():
            have = {(j["market_ticker"], j["band"]) for j in
                    (json.loads(x) for x in out_path.read_text().splitlines() if x.strip())}
        new = []
        for r in first_row_per_market(rows):
            if (r["market_ticker"], r["band"]) in have:
                continue
            res = ms.typed_join(r, finals, now)
            if res.status == FINAL:
                new.append(res.outcome)
            elif res.status == LOOKUP_FAILED:
                _alarm(alarms, path.stem, r, res.reason)
        if new:
            out_dir.mkdir(parents=True, exist_ok=True)
            with out_path.open("a") as fh:
                for j in new:
                    fh.write(json.dumps(j) + "\n")
        counts[path.stem] = len(new)
    return counts


def load_mlb_games() -> pd.DataFrame:
    cache = ROOT / "exp_output" / "MLB_GAME" / "cache_w47"
    games = pd.read_parquet(cache / "games.parquet")
    cur = cache / "games_current.parquet"
    if cur.exists():                      # current-season refresh supersedes the history rows for that season
        c = pd.read_parquet(cur)
        games = pd.concat([games[~games.season.isin(c.season.unique())], c], ignore_index=True)
    return games


def _report_alarms(alarms: list, extra: int = 0) -> int:
    for al in alarms:
        print("ALARM LOOKUP_FAILED:", json.dumps(al), file=sys.stderr)
    return 3 if (alarms or extra) else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sport", choices=("nfl", "mlb"), default="nfl")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW"))
    ap.add_argument("--prefix", default="NFL", help="ledger file prefix (NFLQB for the W65.3 challenger)")
    ap.add_argument("--model", default=str(ROOT / "models" / "nfl_pregame_v1.json"))
    a = ap.parse_args(argv)
    alarms: list = []
    if a.sport == "mlb":     # cache is kept fresh off-box (GitHub Actions sync); no network here
        print("settled_new:", settle_mlb(Path(a.ledger_dir), load_mlb_games(), alarms))
        return _report_alarms(alarms)
    import run_pregame_shadow as rps
    from datetime import datetime, timezone
    if a.refresh:
        rps.refresh_cache(datetime.now(timezone.utc))
    sched = pd.read_parquet(rps.CACHE / "schedule_extended.parquet")
    clim = json.loads(Path(a.model).read_text())["climatology"]
    print("settled_new:", settle(Path(a.ledger_dir), sched, clim, a.prefix, alarms))
    n_pos_alarms = sweep_nfl_positions() if a.prefix == "NFL" else 0
    return _report_alarms(alarms, n_pos_alarms)


if __name__ == "__main__":
    sys.exit(main())
