import re
from pathlib import Path

from prediction_market_bot.c5_execution.market_type_registry import MARKET_TYPE_REGISTRY
from prediction_market_bot.decision_trees import coverage as cv


def test_every_registered_cell_has_a_row():
    rows = cv.cell_rows()
    assert len(rows) == len(MARKET_TYPE_REGISTRY)
    assert all("NO_BET" in r["branches_with_evidence"] for r in rows)


def test_inplay_bands_never_routed_and_stripped():
    for r in cv.cell_rows():
        if r["class"] == "inplay":
            assert not r["routed_today"] and r["depth"] == "stripped"


def test_depth_follows_horizon():
    assert cv.DEPTH["T1"] == "deep" and cv.DEPTH["T3"] == "shallow"


def test_board_series_matches_runner():
    src = (Path(__file__).resolve().parent.parent / "scripts" / "run_ride_board.py").read_text()
    m = re.search(r"DEFAULT_SERIES = \(([^)]*)\)", src, re.S)
    assert set(re.findall(r'"(KX\w+)"', m.group(1))) == set(cv.BOARD_SERIES)


def test_summary_counts_consistent():
    s = cv.summarize(cv.cell_rows())
    assert s["pregame_registered"] + s["inplay_registered"] == s["registered"]
    assert s["routed"] <= s["pregame_registered"]
