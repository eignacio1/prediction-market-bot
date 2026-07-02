"""Tests for scripts/reconstruct_mlb_score_diff.py — F-FLOW-01 retrospective
score_diff/inning reconstruction supporting EXP-FLOW-MLB-01.

Covers: KXMLBHIT ticker parsing, per-half-inning score_diff reconstruction
from ESPN-style linescore arrays (pure logic, no network calls), and the
ticker+inning -> score_diff join used by the (not-yet-built) EXP-FLOW-MLB-01
backtest runner.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("BOT_ENV", "paper")

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from reconstruct_mlb_score_diff import (
    parse_mlb_ticker,
    reconstruct_score_diff_table,
    score_diff_for_cycle,
)


# ── parse_mlb_ticker ──────────────────────────────────────────────────────────

class TestParseMlbTicker:
    def test_parses_real_live_ticker_pit_phi(self):
        result = parse_mlb_ticker("KXMLBHIT-26JUL021235PITPHI-PITMOZUNA24-1")
        assert result == ("PIT", "PHI", "PIT")

    def test_parses_real_live_ticker_cin_mil(self):
        result = parse_mlb_ticker("KXMLBHIT-26JUL021410CINMIL-MILWCONTRERAS24-2")
        assert result == ("CIN", "MIL", "MIL")

    def test_parses_kalshi_client_docstring_example(self):
        result = parse_mlb_ticker("KXMLBHIT-26JUN241607BALLAA-LAAJADELL7-4")
        assert result == ("BAL", "LAA", "LAA")

    def test_returns_none_on_too_few_segments(self):
        assert parse_mlb_ticker("KXMLBHIT-26JUN241607BALLAA") is None

    def test_returns_none_on_malformed_segment1(self):
        assert parse_mlb_ticker("KXMLBHIT-garbage-LAAJADELL7-4") is None


# ── reconstruct_score_diff_table ──────────────────────────────────────────────

class TestReconstructScoreDiffTable:
    def test_scoreless_game_all_zero_diff(self):
        rows = reconstruct_score_diff_table("CHW", "BAL", [0, 0, 0], [0, 0, 0])
        assert len(rows) == 6
        assert all(r["score_diff"] == 0 for r in rows)
        assert all(r["is_batting_team_leading"] is False for r in rows)

    def test_away_run_in_first_carries_into_bottom_first(self):
        # Away scores 1 in top 1; home has not yet batted.
        rows = reconstruct_score_diff_table("CHW", "BAL", [1, 0], [0, 0])
        bottom1 = next(r for r in rows if r["inning"] == 1 and r["half"] == "bottom")
        assert bottom1["batting_team_abbr"] == "BAL"
        assert bottom1["score_diff"] == -1
        assert bottom1["is_batting_team_leading"] is False

        top2 = next(r for r in rows if r["inning"] == 2 and r["half"] == "top")
        assert top2["batting_team_abbr"] == "CHW"
        assert top2["score_diff"] == 1
        assert top2["is_batting_team_leading"] is True

    def test_top_of_first_is_always_zero_diff(self):
        rows = reconstruct_score_diff_table("CHW", "BAL", [3, 0], [5, 0])
        top1 = next(r for r in rows if r["inning"] == 1 and r["half"] == "top")
        assert top1["score_diff"] == 0

    def test_home_run_lead_reflected_entering_next_top(self):
        # Home scores 4 in bottom 1 -> away trails by 4 entering top 2.
        rows = reconstruct_score_diff_table("CHW", "BAL", [0, 0], [4, 0])
        top2 = next(r for r in rows if r["inning"] == 2 and r["half"] == "top")
        assert top2["score_diff"] == -4
        assert top2["is_batting_team_leading"] is False

    def test_uneven_linescores_home_no_bottom_ninth_when_winning(self):
        # Away team's linescore array can be one inning longer than home's
        # (walk-off / home team already ahead, no bottom-9th played).
        away_runs = [0, 0, 0, 0, 0, 0, 0, 0, 1]
        home_runs = [1, 0, 0, 0, 0, 0, 0, 0]
        rows = reconstruct_score_diff_table("CHW", "BAL", away_runs, home_runs)
        assert not any(r["inning"] == 9 and r["half"] == "bottom" for r in rows)
        top9 = next(r for r in rows if r["inning"] == 9 and r["half"] == "top")
        assert top9["defense_team_abbr"] == "BAL"


# ── score_diff_for_cycle (ticker + inning join) ───────────────────────────────

class TestScoreDiffForCycle:
    def _lookup(self):
        rows = reconstruct_score_diff_table("PIT", "PHI", [0, 1, 0], [1, 0, 2])
        return {("PIT", "PHI", r["inning"], r["half"]): r for r in rows}

    def test_away_team_player_resolves_to_top_half(self):
        lookup = self._lookup()
        row = score_diff_for_cycle("KXMLBHIT-26JUL021235PITPHI-PITMOZUNA24-1", inning=2, lookup=lookup)
        assert row is not None
        assert row["half"] == "top"
        assert row["batting_team_abbr"] == "PIT"

    def test_home_team_player_resolves_to_bottom_half(self):
        lookup = self._lookup()
        # PHI has no player in this fixture ticker set; construct one directly.
        row = score_diff_for_cycle("KXMLBHIT-26JUL021235PITPHI-PHISCHWARBER12-1", inning=1, lookup=lookup)
        assert row is not None
        assert row["half"] == "bottom"
        assert row["batting_team_abbr"] == "PHI"

    def test_returns_none_for_unparseable_ticker(self):
        lookup = self._lookup()
        assert score_diff_for_cycle("not-a-ticker", inning=1, lookup=lookup) is None

    def test_returns_none_when_inning_beyond_lookup(self):
        lookup = self._lookup()
        row = score_diff_for_cycle(
            "KXMLBHIT-26JUL021235PITPHI-PITMOZUNA24-1", inning=15, lookup=lookup
        )
        assert row is None
