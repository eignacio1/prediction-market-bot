"""W80P.4: scripts/mlb_season_lookback.py -- composes existing readers; never scores a 2026 MLB game row."""
from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mlb_lookback", REPO / "scripts" / "mlb_season_lookback.py")
lb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lb)
NOW = datetime(2026, 11, 2, tzinfo=timezone.utc)


def test_unreadable_sources_say_unavailable_not_zero():
    txt = lb.render(REPO, {"error": "boom"}, {"error": "no ledger", "sources": "x + y"}, {"error": "no book"}, NOW)
    assert txt.count("UNAVAILABLE") == 3 and "boom" in txt and "no ledger" in txt


def test_sealed_game_cells_show_no_verdict_and_the_2027_look():
    g = {"generated": "t", "cells": [{"cell": "MLB_MONEYLINE_T1", "band": "T1", "rows": 410, "settled_games": 38,
                                     "status": "SEALED (38 of 150)", "verdict": None}]}
    txt = lb.render(REPO, g, {"bands": {}, "sources": "s"}, {"measures": []}, NOW)
    row = next(l for l in txt.splitlines() if l.startswith("| MLB_MONEYLINE_T1"))
    assert "SEALED (38 of 150)" in row and "2026 rows never scored" in row


def test_n_star_reached_is_sample_adequacy_not_an_edge_verdict():
    r = {"status": "COMPUTED", "raw_n": 900, "clean_n": 800, "n_star": 787, "met": True, "mean_pnl_per_bet": -0.26,
         "gap_to_n_star": 0, "eta_weeks": 0}
    line = lb._power_line("T4M-PROJ", r)
    assert "n* REACHED" in line and "not an edge verdict" in line and "-0.260" in line
    r.update(met=False, clean_n=300, gap_to_n_star=487, eta_weeks=12.34)
    assert "below n*" in lb._power_line("T4M-PROJ", r) and "12.3" in lb._power_line("T4M-PROJ", r)


def test_underpowered_band_prints_reason():
    line = lb._power_line("T2", {"status": "UNDERPOWERED", "raw_n": 4, "clean_n": 3, "reason": "clean_n=3 < MIN_N"})
    assert "UNDERPOWERED" in line and "MIN_N" in line


def test_game_cells_reads_engine_without_writing(tmp_path):
    out = lb.game_cells(tmp_path)          # empty repo: no ledgers -> no MLB cells or a reported error, never a crash
    assert "cells" in out or "error" in out
    assert not (tmp_path / "exp_output" / "CALIBRATION").exists()
