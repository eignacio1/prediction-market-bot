#!/usr/bin/env python3
"""W59.3: READ-ONLY check run on/after 2026-10-21 -- may the NBA cells flip NOT_IMPLEMENTED -> SHADOW?

A cell qualifies when exp_output/PREGAME_SHADOW/NBA_<MARKET>_<BAND>.jsonl holds >=1 valid row: model_sha256 equals
the frozen model's, 0<p_yes<1, a quote present, start_time_source set. Preseason rows live in a different directory
and never count. Prints the exact registry lines to add (promote_cell_status ... superseding_reference="EXP-038");
it does NOT edit the registry, and flips nothing. Exit 0 = all qualifying cells listed, 1 = no cell qualifies.
Usage: python3 scripts/w59_3_nba_flip_check.py [--ledger-dir DIR]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MT = {"MONEYLINE": "NBA_MONEYLINE", "SPREAD": "NBA_SPREAD", "GAME_TOTAL": "NBA_GAME_TOTAL", "TEAM_TOTAL": "NBA_TEAM_TOTAL"}
BAND = {"T1": "T1_MULTI_DAY", "T2": "T2_SAME_DAY", "T3": "T3_PRE_TIP"}


def valid(r: dict, sha: str) -> bool:
    return (r.get("model_sha256") == sha and isinstance(r.get("p_yes"), (int, float)) and 0 < r["p_yes"] < 1
            and r.get("mid") is not None and bool(r.get("start_time_source")) and not r.get("excluded_from_judged_n"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ledger-dir", default=str(ROOT / "exp_output" / "PREGAME_SHADOW"))
    a = ap.parse_args(argv)
    sha = hashlib.sha256((ROOT / "models" / "nba_pregame_v1.json").read_bytes()).hexdigest()
    ok = 0
    for m, mt in MT.items():
        for b, bd in BAND.items():
            p = Path(a.ledger_dir) / f"NBA_{m}_{b}.jsonl"
            rows = [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []
            n = sum(valid(r, sha) for r in rows)
            if n:
                ok += 1
                print(f"FLIP-OK  {mt}/{bd}: {n}/{len(rows)} valid rows -> "
                      f'promote_cell_status(MarketType.{mt}, ExecutionBand.{bd}, CellStatus.SHADOW, superseding_reference="EXP-038")')
            else:
                print(f"NO-ROWS  {mt}/{bd}: {len(rows)} rows, 0 valid -> leave NOT_IMPLEMENTED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
