"""EXP-038 / W58.2: NBA pregame shadow SETTLEMENT JOIN. Outcome join only -- computes NO Brier, log-loss or
E_net statistic. First row per (market_ticker, band) of exp_output/PREGAME_SHADOW/NBA_*_T[123].jsonl is joined
to the ESPN final score and appended (idempotently) to settled/<same name>. No order, no position, no sizing.

  PYTHONPATH=src:. python3 scripts/run_nba_pregame_shadow_settle.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot.c1_signal_ingestion import nba_ingest as N  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import et_date, _dt  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_forecaster import parse_market_ticker  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_settlement import join_row, typed_join  # noqa: E402
from prediction_market_bot.pregame_shadow.settle_result import FINAL, LOOKUP_FAILED  # noqa: E402
from prediction_market_bot.pregame_shadow.scoring import first_row_per_market  # noqa: E402

SEASONS = (2026, 2027)


def finals_index(raw: Path) -> dict:
    out = {}
    for s in SEASONS:
        for g in N.completed_regular(N.load_season(s, raw)):
            key = (et_date(_dt(g["start_time_utc"])).isoformat(), frozenset((g["home"], g["away"])))
            out[key] = (g["home"], g["away"], float(g["home_score"]), float(g["away_score"]))
    return out


def settle(ledger_dir: Path, finals: dict, clim: dict, alarms: "list | None" = None, now=None) -> dict:
    out_dir = ledger_dir / "settled"
    counts: dict[str, int] = {}
    for path in sorted(ledger_dir.glob("NBA_*_T[123].jsonl")):
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
                if alarms is not None:
                    alarms.append({"cell": path.stem, "market_ticker": r["market_ticker"], "reason": "unparseable_ticker"})
                continue
            fin = finals.get((p["game_date"], frozenset((p["home"], p["away"]))))
            res = typed_join(r, p["game_date"], fin, clim, now)
            if res.status == FINAL:
                new.append(res.outcome)
            elif res.status == LOOKUP_FAILED and alarms is not None:
                alarms.append({"cell": path.stem, "market_ticker": r["market_ticker"], "reason": res.reason})
        if new:
            out_dir.mkdir(parents=True, exist_ok=True)
            with out_path.open("a") as fh:
                for j in new:
                    fh.write(json.dumps(j) + "\n")
        counts[path.stem] = len(new)
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw" / "nba"))
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW"))
    ap.add_argument("--model", default=str(ROOT / "models" / "nba_pregame_v1.json"))
    a = ap.parse_args(argv)
    clim = json.loads(Path(a.model).read_text())["climatology"]
    alarms: list = []
    print("settled_new:", settle(Path(a.ledger_dir), finals_index(Path(a.raw)), clim, alarms))
    for al in alarms:
        print("ALARM LOOKUP_FAILED:", json.dumps(al), file=sys.stderr)
    return 3 if alarms else 0


if __name__ == "__main__":
    sys.exit(main())
