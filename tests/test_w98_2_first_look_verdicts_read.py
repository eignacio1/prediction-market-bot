"""W98.2 Part A: the verdict reader prints only released verdicts and never a sealed cell's score."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("flv", ROOT / "scripts/first_look_verdicts_read.py")
flv = importlib.util.module_from_spec(spec)
sys.modules["flv"] = flv
spec.loader.exec_module(flv)


def _cell(name, verdict=None, lo=-0.02, hi=0.01):
    c = {"cell": name, "status": "JUDGED", "judged_n": 60, "projection": {"date": "2026-12-21", "note": None}}
    if verdict:
        c["verdict"] = {"n": 60, "verdict": verdict, "rule": "CI spans zero",
                        "delta_brier_vs_market": {"mean": -0.005, "ci95": [lo, hi]},
                        "delta_brier_vs_climatology": {"mean": 0.02, "ci95": [0.0, 0.04]},
                        "e_net_entry_k007": -0.01, "e_net_entry_kmult": -0.02}
        c["release"] = {"look": 60, "games": ["g"], "digest": "a" * 64, "frozen": False}
    return c


def test_only_released_cells_print_and_tally():
    res = {"generated": "t", "summary": {"cells": 3}, "cells": [_cell("A", "SHADOW"), _cell("B", "RULED_OUT", hi=-0.001), _cell("SEALED")]}
    out = flv.render(res, "x.json")
    assert "released verdict: 2 of 3" in out
    assert "SEALED" not in out.split("tally")[0].split("cell |")[1]
    assert '"RULED_OUT": 1' in out and '"SHADOW": 1' in out
    assert "-0.0200, +0.0100" in out


def test_latest_file_and_missing(tmp_path):
    assert flv.latest_engine_json(tmp_path) is None
    (tmp_path / "engine_20261101T000000Z.json").write_text("{}")
    (tmp_path / "engine_20261102T135056Z.json").write_text(json.dumps({"cells": []}))
    assert flv.latest_engine_json(tmp_path).name == "engine_20261102T135056Z.json"
    assert flv.main(["--dir", str(tmp_path)]) == 0
    assert flv.main(["--dir", str(tmp_path / "none")]) == 1
