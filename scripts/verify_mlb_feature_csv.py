"""Fail-closed gate for the off-box MLB feature CSV refresh (W57.1 / GG-489).

Runs the SAME MLB_FEATURE_CSV_CONTRACT that PIPE-05/PIPE-06pre enforce (nothing relaxed) against a
freshly generated CSV, plus a floor on player count. Exit 0 only if the CSV would pass the live
pipelines. The GitHub Actions job pushes to the VPS only after this exits 0.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone

import pandas as pd

from prediction_market_bot.c1_signal_ingestion.data_contracts import MLB_FEATURE_CSV_CONTRACT
from prediction_market_bot.c1_signal_ingestion.validators import validate

MIN_PLAYERS = 300  # a throttled/partial fetch yielded 121 players; a full roster is ~470-575


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("--meta-out", required=True)
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    result = validate(df, MLB_FEATURE_CSV_CONTRACT)
    halts = [f for f in result.failures if getattr(f.severity, "name", str(f.severity)).upper() == "HALT"]
    players = int(df["player_id"].nunique())
    max_date = str(df["game_date"].astype(str).max())
    for f in result.failures:
        print(f"contract: {f.check_type} [{getattr(f.severity, 'name', f.severity)}] {f.reason}")
    if halts:
        print(f"REFUSE: {len(halts)} HALT-severity contract failure(s); VPS CSV left untouched", file=sys.stderr)
        return 1
    if players < MIN_PLAYERS:
        print(f"REFUSE: only {players} players (< {MIN_PLAYERS}); partial fetch; VPS CSV left untouched", file=sys.stderr)
        return 1
    meta = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rows": len(df),
        "players": players,
        "max_game_date": max_date,
        "source": "github-actions mlb_features_sync.yml",
    }
    with open(args.meta_out, "w") as fh:
        json.dump(meta, fh)
    print(f"OK {meta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
