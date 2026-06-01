"""Tests for cohort.py — canonical player cohort registry."""
import pytest
from prediction_market_bot.cohort import (
    COHORT,
    cohort_summary,
    get_all_player_ids,
    get_player_ids_v1,
    get_player_ids_v2,
    get_player_name,
    get_players_by_team,
)


class TestCohortIntegrity:
    def test_no_duplicate_player_ids(self):
        ids = get_all_player_ids()
        assert len(ids) == len(set(ids)), "Duplicate player IDs in cohort"

    def test_v1_cohort_has_50_players(self):
        assert len(get_player_ids_v1()) == 50

    def test_v2_cohort_larger_than_v1(self):
        assert len(get_player_ids_v2()) > len(get_player_ids_v1())

    def test_all_entries_have_required_fields(self):
        for pid, entry in COHORT.items():
            assert "name" in entry, f"Player {pid} missing name"
            assert "team" in entry, f"Player {pid} missing team"
            assert "position" in entry, f"Player {pid} missing position"
            assert "cohort_version" in entry, f"Player {pid} missing cohort_version"

    def test_cohort_version_values_are_valid(self):
        for pid, entry in COHORT.items():
            assert entry["cohort_version"] in (1, 2, 3), \
                f"Player {pid} has invalid cohort_version {entry['cohort_version']}"

    def test_known_player_ids_present(self):
        known = {
            2544:    "LeBron James",
            201939:  "Stephen Curry",
            203999:  "Nikola Jokic",
            1628983: "Shai Gilgeous-Alexander",
            1629029: "Luka Doncic",
        }
        for pid, name in known.items():
            assert pid in COHORT, f"{name} ({pid}) not in cohort"
            assert COHORT[pid]["name"] == name

    def test_team_abbreviations_are_3_chars(self):
        for pid, entry in COHORT.items():
            assert len(entry["team"]) <= 3, \
                f"Player {pid} team '{entry['team']}' too long"

    def test_position_values_are_valid(self):
        valid = {"G", "G-F", "F", "F-C", "C"}
        for pid, entry in COHORT.items():
            assert entry["position"] in valid, \
                f"Player {pid} position '{entry['position']}' invalid"


class TestCohortAccessors:
    def test_get_player_name_known(self):
        assert get_player_name(2544) == "LeBron James"

    def test_get_player_name_unknown_returns_str(self):
        result = get_player_name(9999999)
        assert result == "9999999"

    def test_get_players_by_team_okc(self):
        okc = get_players_by_team("OKC")
        assert 1628983 in okc  # SGA

    def test_get_players_by_team_case_insensitive(self):
        assert get_players_by_team("okc") == get_players_by_team("OKC")

    def test_get_players_by_team_unknown_empty(self):
        assert get_players_by_team("XYZ") == []


class TestCohortSummary:
    def test_summary_has_required_keys(self):
        s = cohort_summary()
        assert "total" in s
        assert "v1_original" in s
        assert "v2_additions" in s
        assert "teams" in s

    def test_summary_total_matches_cohort(self):
        s = cohort_summary()
        assert s["total"] == len(COHORT)

    def test_summary_v1_is_50(self):
        assert cohort_summary()["v1_original"] == 50

    def test_summary_covers_multiple_teams(self):
        assert cohort_summary()["teams"] >= 15
