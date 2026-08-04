"""Tests for scripts/phase0_market_survey.py -- GG-155/T-411/T-412.

Covers the two root causes behind GG-155's false "PLAYER_PROP illiquid"
finding: (1) `cmd_depth`'s sampler took `group[:per_family]`, a head-slice
with no per-series balancing, so a single series sorted first in the raw
dump could consume an entire family's sample budget while sibling series
were never measured; (2) `FAMILY_PATTERNS`' bare "HIT" substring matched
KXLEADERMLBHITS (a season leaderboard) as PLAYER_PROP, so the one series
that did dominate the head-slice wasn't even a per-game prop market.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).parent.parent / "scripts"
_SRC = Path(__file__).parent.parent / "src"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from phase0_market_survey import FAMILY_PATTERNS, _balanced_sample, _classify  # noqa: E402


def test_balanced_sample_round_robins_across_series() -> None:
    # One series has far more markets than the others. A head-slice sampler
    # (the pre-T-412 bug) would fill the entire budget from this one series
    # alone; round-robin must spread the budget across all three.
    series_groups = {
        "KXMLBHIT": [{"ticker": f"KXMLBHIT-{i}"} for i in range(50)],
        "KXMLBPTS": [{"ticker": f"KXMLBPTS-{i}"} for i in range(3)],
        "KXMLBRBI": [{"ticker": f"KXMLBRBI-{i}"} for i in range(3)],
    }
    picked = _balanced_sample(series_groups, limit=9)

    assert len(picked) == 9
    counts: dict[str, int] = {}
    for ticker, _m in picked:
        counts[ticker] = counts.get(ticker, 0) + 1

    # All three series must appear -- the defect this guards against is
    # exactly "one series ate the whole budget, siblings got zero".
    assert set(counts) == {"KXMLBHIT", "KXMLBPTS", "KXMLBRBI"}
    # Balanced within 1 of each other (9 / 3 series == 3 each).
    assert max(counts.values()) - min(counts.values()) <= 1


def test_balanced_sample_exhausts_small_series_without_starving_others() -> None:
    # A series with fewer markets than its round-robin share should be fully
    # drained, with the leftover budget flowing to the remaining series
    # rather than being dropped.
    series_groups = {
        "KXMLBHIT": [{"ticker": f"KXMLBHIT-{i}"} for i in range(10)],
        "KXMLBPTS": [{"ticker": "KXMLBPTS-0"}],
    }
    picked = _balanced_sample(series_groups, limit=6)

    assert len(picked) == 6
    counts: dict[str, int] = {}
    for ticker, _m in picked:
        counts[ticker] = counts.get(ticker, 0) + 1
    assert counts["KXMLBPTS"] == 1  # fully drained, no more available
    assert counts["KXMLBHIT"] == 5  # absorbed the remaining budget


def test_balanced_sample_caps_at_total_available() -> None:
    series_groups = {
        "KXMLBHIT": [{"ticker": "KXMLBHIT-0"}],
        "KXMLBPTS": [{"ticker": "KXMLBPTS-0"}],
    }
    picked = _balanced_sample(series_groups, limit=20)
    assert len(picked) == 2


def test_season_leaderboard_not_classified_as_player_prop() -> None:
    # GG-155's actual root cause: KXLEADERMLBHITS is a season-long
    # leaderboard, not a per-game prop, but bare "HIT" matched it into
    # PLAYER_PROP before the SEASON_AWARD pattern was added.
    assert _classify("KXLEADERMLBHITS", FAMILY_PATTERNS, "UNCLASSIFIED") == "SEASON_AWARD"


def test_real_player_prop_still_classifies_correctly() -> None:
    # The SEASON_AWARD fix must not regress genuine per-game props.
    assert _classify("KXMLBHIT", FAMILY_PATTERNS, "UNCLASSIFIED") == "PLAYER_PROP"
