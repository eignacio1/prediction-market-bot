"""Smoke tests for the W83.2 Part B script (pure helpers only; the event store is not in CI)."""
import importlib.util
import math
from pathlib import Path

_p = Path(__file__).resolve().parents[1] / "12_EXPLORATORY" / "20261020_nba_lineup_cross" / "playtype_absorption.py"
_s = importlib.util.spec_from_file_location("playtype_absorption", _p)
pa = importlib.util.module_from_spec(_s)
_s.loader.exec_module(pa)


def test_mins_parses_clock_and_blank():
    assert pa.mins("45:15") == 45.25
    assert pa.mins("") == 0.0
    assert pa.mins(None) == 0.0


def test_norm_strips_accents_and_punctuation():
    assert pa.norm("Luka Dončić") == pa.norm("luka doncic")
    assert pa.norm("P.J. Washington") == "pjwashington"


def test_spearman_monotone_and_inverse():
    assert math.isclose(pa.spearman([1, 2, 3, 4], [10, 20, 30, 50]), 1.0)
    assert math.isclose(pa.spearman([1, 2, 3, 4], [4, 3, 2, 1]), -1.0)
    assert math.isnan(pa.spearman([1, 2], [1, 2]))
