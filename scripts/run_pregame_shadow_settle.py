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
from prediction_market_bot.pregame_shadow.nfl_settlement import join_row  # noqa: E402
from prediction_market_bot.pregame_shadow.scoring import first_row_per_market  # noqa: E402


def settle(ledger_dir: Path, sched: pd.DataFrame, clim: dict) -> dict:
    finals = {}
    for r in sched[sched.home_score.notna() & sched.away_score.notna()].itertuples():
        finals[(str(r.gameday), frozenset((r.home_team, r.away_team)))] = (
            r.home_team, r.away_team, float(r.home_score), float(r.away_score))
    out_dir = ledger_dir / "settled"
    counts: dict[str, int] = {}
    for path in sorted(ledger_dir.glob("NFL_*_T[123].jsonl")):
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
            if p is None:
                continue
            fin = finals.get((p["game_date"], frozenset((p["home"], p["away"]))))
            if fin is None:
                continue
            j = join_row(r, *fin, clim)
            if j is not None:
                new.append(j)
        if new:
            out_dir.mkdir(parents=True, exist_ok=True)
            with out_path.open("a") as fh:
                for j in new:
                    fh.write(json.dumps(j) + "\n")
        counts[path.stem] = len(new)
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW"))
    ap.add_argument("--model", default=str(ROOT / "models" / "nfl_pregame_v1.json"))
    a = ap.parse_args(argv)
    import run_pregame_shadow as rps
    from datetime import datetime, timezone
    if a.refresh:
        rps.refresh_cache(datetime.now(timezone.utc))
    sched = pd.read_parquet(rps.CACHE / "schedule_extended.parquet")
    clim = json.loads(Path(a.model).read_text())["climatology"]
    print("settled_new:", settle(Path(a.ledger_dir), sched, clim))
    return 0


if __name__ == "__main__":
    sys.exit(main())
