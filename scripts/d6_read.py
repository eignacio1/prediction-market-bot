#!/usr/bin/env python3
"""READ-ONLY (W114.2 / B-090): D6 (cells wired through all seven layers) counted on the box against its real logs.

Runs decision_trees/coverage.d6_layers with the box's arm-order log (layers 6 and 7) and the box's own filter data (layer 3),
then prints d6_summary: wired / registered, per sport, cells per layer, every cell missing exactly one layer, and the layer-3
inputs that decide NHL (does exp_output/NHL_EVENTS exist on this host). Layer 7 uses read-only demo GETs for fill status
(in-memory cache); if they are unavailable layer 7 reads 0 and the output says so. Writes nothing: stdout only.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(HERE))
import arm_orders_read as aor  # noqa: E402


def layer3_inputs() -> dict:
    """What layer 3 stands on, per sport, on THIS host."""
    from prediction_market_bot.decision_trees import coverage, filter_supply as fsup
    d = fsup.nhl_store_dir()
    return {"sports_with_filter_data": sorted(coverage.filter_layer_sports()),
            "nhl_store_dir": d, "nhl_store_dir_exists": os.path.isdir(d),
            "nhl_games_parquet": sorted(os.path.basename(p) for p in glob.glob(d + "/games_202[56].parquet"))}


def build(orders: list, fills_for, note: str, source: str, now: Optional[datetime] = None) -> dict:
    from prediction_market_bot.decision_trees import coverage
    cells = coverage.d6_layers(orders=orders, fills_for=fills_for)
    s = coverage.d6_summary(cells)
    s["layer_names"] = list(coverage.LAYER_NAMES)
    return {"source": source, "read_utc": (now or datetime.now(timezone.utc)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "arm_order_rows": len(orders), "fills_note": note or "ok", "d6": s,
            "missing_exactly_one_layer": coverage.missing_one_layer(cells), "layer3_inputs": layer3_inputs(),
            "cells_by_n_layers": {str(n): sum(1 for c in cells if c["n_layers"] == n) for n in range(8)}}


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default=str(aor.LOG))
    ap.add_argument("--no-fills", action="store_true")
    a = ap.parse_args(argv)
    rows = aor.load_rows(Path(a.log))
    fills_for, note = (None, "fills skipped: --no-fills") if a.no_fills else aor.make_fills_for(rows)
    print(json.dumps(build(rows, fills_for, note, a.log), indent=1, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
