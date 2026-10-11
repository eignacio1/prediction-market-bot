"""EXP-039 / W65.1: NBA player-points shadow SETTLEMENT JOIN. Outcome join only -- computes NO Brier, log-loss or
E_net statistic. First row per (market_ticker, band) of exp_output/PREGAME_SHADOW/NBA_NBA_PLAYER_POINTS_T[123].jsonl is
joined to the ESPN box score and appended (idempotently) to settled/<same name>. DNP / scalar settlements are marked
and excluded from scoring. No order, no position, no sizing.

  PYTHONPATH=src:. python3 scripts/run_nba_player_points_shadow_settle.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from prediction_market_bot.c1_signal_ingestion import nba_ingest as N  # noqa: E402
from prediction_market_bot.c1_signal_ingestion import nba_player_ingest as P  # noqa: E402
from prediction_market_bot.c1_signal_ingestion.nba_pregame_features import _dt, et_date  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_player_points_forecaster import parse_market_ticker  # noqa: E402
from prediction_market_bot.pregame_shadow.nba_player_points_settlement import join_row  # noqa: E402
from prediction_market_bot.pregame_shadow.scoring import first_row_per_market  # noqa: E402

SEASONS = (2026, 2027)
GLOB = "NBA_NBA_PLAYER_POINTS_T[123].jsonl"


def box_index(raw: Path) -> dict:
    """(ET date, frozenset(teams)) -> box-score rows of that completed regular-season game."""
    out = {}
    for s in SEASONS:
        games = N.load_season(s, raw)["games"]
        for gid, rec in P.load_players(s, raw)["games"].items():
            g = games.get(gid)
            if g is not None and g["completed"] and g["season_type"] == N.REGULAR:
                out[(et_date(_dt(g["start_time_utc"])).isoformat(), frozenset((g["home"], g["away"])))] = rec["rows"]
    return out


def settle(ledger_dir: Path, boxes: dict, clim: dict) -> dict:
    out_dir = ledger_dir / "settled"
    counts: dict[str, int] = {}
    for path in sorted(ledger_dir.glob(GLOB)):
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
            box = boxes.get((p["game_date"], frozenset((p["home"], p["away"])))) if p else None
            if box is None:
                continue
            j = join_row(r, box, clim)
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
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw" / "nba"))
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW"))
    ap.add_argument("--model", default=str(ROOT / "models" / "nba_player_points_v1.json"))
    a = ap.parse_args(argv)
    clim = json.loads(Path(a.model).read_text())["climatology"]
    print("settled_new:", settle(Path(a.ledger_dir), box_index(Path(a.raw)), clim))
    return 0


if __name__ == "__main__":
    sys.exit(main())
