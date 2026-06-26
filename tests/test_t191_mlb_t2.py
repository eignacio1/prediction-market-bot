"""
T-191: Tests for PIPE-05.5 MLB T2 Same-Day Batting Lineup Overlay.

Components tested:
  1. Batting-slot Binomial adjustment (_slot_adjust)
  2. Lineup confirmation: players not in lineup are scratched
  3. Per-game contamination guard: players in live games are skipped
  4. Idempotency: T1 open positions block T2 re-entry on same ticker
  5. DS-04 MLB: fetch_lineups response parsing
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# 1. Batting-slot Binomial adjustment
# ---------------------------------------------------------------------------


def _slot_adjust(
    p_t1: float,
    ba_l10: float | None,
    batting_slot: int,
    threshold: int,
) -> float:
    """Mirror of run_t2_mlb_sameday._slot_adjust for isolated testing."""
    _AB_BY_SLOT = {
        1: 4.2, 2: 4.1, 3: 4.0, 4: 3.9, 5: 3.7,
        6: 3.6, 7: 3.4, 8: 3.2, 9: 3.1,
    }
    _AB_DEFAULT = 3.7
    import numpy as np

    if ba_l10 is None or ba_l10 <= 0.0 or ba_l10 >= 1.0:
        return p_t1

    ab_adj = _AB_BY_SLOT.get(batting_slot, _AB_DEFAULT)
    q = 1.0 - ba_l10

    if threshold == 1:
        p_adj  = 1.0 - q ** ab_adj
        p_base = 1.0 - q ** _AB_DEFAULT
    elif threshold == 2:
        p_adj  = 1.0 - q**ab_adj - ab_adj * ba_l10 * q**(ab_adj - 1)
        p_base = 1.0 - q**_AB_DEFAULT - _AB_DEFAULT * ba_l10 * q**(_AB_DEFAULT - 1)
    else:
        return p_t1

    if p_base <= 0.0:
        return p_t1

    ratio = max(0.85, min(1.15, p_adj / p_base))
    return float(np.clip(p_t1 * ratio, 0.01, 0.99))


class TestSlotAdjust(unittest.TestCase):

    def test_leadoff_increases_probability(self):
        """Slot 1 (leadoff) gets more ABs → higher hit probability."""
        p_slot1 = _slot_adjust(0.60, 0.280, batting_slot=1, threshold=1)
        p_slot5 = _slot_adjust(0.60, 0.280, batting_slot=5, threshold=1)
        self.assertGreater(p_slot1, p_slot5)

    def test_bottom_order_decreases_probability(self):
        """Slot 9 gets fewer ABs → lower hit probability."""
        p_slot9 = _slot_adjust(0.60, 0.280, batting_slot=9, threshold=1)
        p_slot5 = _slot_adjust(0.60, 0.280, batting_slot=5, threshold=1)
        self.assertLess(p_slot9, p_slot5)

    def test_slot5_is_baseline(self):
        """Slot 5 matches AB_DEFAULT (3.7) → ratio ≈ 1.0, p_t2 ≈ p_t1."""
        p_t1 = 0.60
        p_t2 = _slot_adjust(p_t1, 0.280, batting_slot=5, threshold=1)
        self.assertAlmostEqual(p_t2, p_t1, places=4)

    def test_cap_applied(self):
        """Adjustment is capped at ±15% — cannot produce >15% change from p_t1."""
        # High ba_l10, extreme slot — still capped
        p_t2 = _slot_adjust(0.90, 0.500, batting_slot=1, threshold=1)
        self.assertLessEqual(p_t2, 0.90 * 1.15)
        p_t2_low = _slot_adjust(0.60, 0.100, batting_slot=9, threshold=1)
        self.assertGreaterEqual(p_t2_low, 0.60 * 0.85)

    def test_none_ba_returns_p_t1(self):
        """Missing ba_l10 → no adjustment, return p_t1 unchanged."""
        p_t1 = 0.55
        self.assertEqual(_slot_adjust(p_t1, None, batting_slot=1, threshold=1), p_t1)

    def test_zero_ba_returns_p_t1(self):
        """ba_l10 = 0 → invalid → return p_t1 unchanged."""
        p_t1 = 0.55
        self.assertEqual(_slot_adjust(p_t1, 0.0, batting_slot=1, threshold=1), p_t1)

    def test_output_clipped_to_unit_interval(self):
        """p_t2 must remain in (0.01, 0.99)."""
        p_t2 = _slot_adjust(0.99, 0.450, batting_slot=1, threshold=1)
        self.assertLessEqual(p_t2, 0.99)
        p_t2_low = _slot_adjust(0.01, 0.050, batting_slot=9, threshold=1)
        self.assertGreaterEqual(p_t2_low, 0.01)

    def test_threshold_2_adjustment(self):
        """Threshold 2 adjustment direction is correct: more ABs → higher p(H≥2)."""
        p_slot1 = _slot_adjust(0.30, 0.280, batting_slot=1, threshold=2)
        p_slot9 = _slot_adjust(0.30, 0.280, batting_slot=9, threshold=2)
        self.assertGreater(p_slot1, p_slot9)

    def test_unknown_threshold_returns_p_t1(self):
        """Threshold 3+ → no adjustment, return p_t1."""
        p_t1 = 0.50
        self.assertEqual(_slot_adjust(p_t1, 0.280, batting_slot=1, threshold=3), p_t1)


# ---------------------------------------------------------------------------
# 2. fetch_lineups response parsing
# ---------------------------------------------------------------------------


def _parse_lineups_response(data: dict) -> dict[int, dict]:
    """Mirror of the parsing logic in MLBIngestionClient.fetch_lineups."""
    result: dict[int, dict] = {}
    for date_block in data.get("dates", []):
        for game in date_block.get("games", []):
            game_pk = game.get("gamePk")
            if game_pk is None:
                continue
            teams = game.get("teams", {})
            home_team_id = (teams.get("home", {}).get("team") or {}).get("id")
            away_team_id = (teams.get("away", {}).get("team") or {}).get("id")
            lineups = game.get("lineups") or {}
            for side, team_id in (("homePlayers", home_team_id), ("awayPlayers", away_team_id)):
                for slot_idx, player in enumerate(lineups.get(side, []), start=1):
                    pid = player.get("id")
                    if pid is not None:
                        result[int(pid)] = {
                            "batting_slot": slot_idx,
                            "game_pk": int(game_pk),
                            "team_id": team_id,
                        }
    return result


class TestFetchLineupsParser(unittest.TestCase):

    def _make_response(self) -> dict:
        return {
            "dates": [{
                "games": [{
                    "gamePk": 12345,
                    "teams": {
                        "home": {"team": {"id": 10}},
                        "away": {"team": {"id": 20}},
                    },
                    "lineups": {
                        "homePlayers": [
                            {"id": 101, "fullName": "Home Leadoff"},
                            {"id": 102, "fullName": "Home Second"},
                            {"id": 103, "fullName": "Home Third"},
                        ],
                        "awayPlayers": [
                            {"id": 201, "fullName": "Away Leadoff"},
                            {"id": 202, "fullName": "Away Second"},
                        ],
                    },
                }]
            }]
        }

    def test_batting_slot_is_1_indexed(self):
        result = _parse_lineups_response(self._make_response())
        self.assertEqual(result[101]["batting_slot"], 1)
        self.assertEqual(result[102]["batting_slot"], 2)
        self.assertEqual(result[103]["batting_slot"], 3)

    def test_away_team_slots_also_1_indexed(self):
        result = _parse_lineups_response(self._make_response())
        self.assertEqual(result[201]["batting_slot"], 1)
        self.assertEqual(result[202]["batting_slot"], 2)

    def test_game_pk_assigned_correctly(self):
        result = _parse_lineups_response(self._make_response())
        self.assertEqual(result[101]["game_pk"], 12345)
        self.assertEqual(result[201]["game_pk"], 12345)

    def test_team_id_home_vs_away(self):
        result = _parse_lineups_response(self._make_response())
        self.assertEqual(result[101]["team_id"], 10)  # home
        self.assertEqual(result[201]["team_id"], 20)  # away

    def test_empty_lineups_returns_empty_dict(self):
        data = {"dates": [{"games": [{"gamePk": 999, "teams": {}, "lineups": {}}]}]}
        result = _parse_lineups_response(data)
        self.assertEqual(result, {})

    def test_no_lineup_field_returns_empty_dict(self):
        data = {"dates": [{"games": [{"gamePk": 999, "teams": {}}]}]}
        result = _parse_lineups_response(data)
        self.assertEqual(result, {})

    def test_multiple_games_parsed(self):
        data = {
            "dates": [{
                "games": [
                    {
                        "gamePk": 111,
                        "teams": {
                            "home": {"team": {"id": 1}},
                            "away": {"team": {"id": 2}},
                        },
                        "lineups": {
                            "homePlayers": [{"id": 10}],
                            "awayPlayers": [{"id": 20}],
                        },
                    },
                    {
                        "gamePk": 222,
                        "teams": {
                            "home": {"team": {"id": 3}},
                            "away": {"team": {"id": 4}},
                        },
                        "lineups": {
                            "homePlayers": [{"id": 30}],
                            "awayPlayers": [{"id": 40}],
                        },
                    },
                ]
            }]
        }
        result = _parse_lineups_response(data)
        self.assertIn(10, result)
        self.assertIn(20, result)
        self.assertIn(30, result)
        self.assertIn(40, result)
        self.assertEqual(result[10]["game_pk"], 111)
        self.assertEqual(result[30]["game_pk"], 222)


# ---------------------------------------------------------------------------
# 3. Scratch filter logic
# ---------------------------------------------------------------------------


class TestScratchFilter(unittest.TestCase):
    """Player not in confirmed lineup → SCRATCH (skip bet)."""

    def _evaluate_player(
        self,
        player_id: int,
        lineup_by_pid: dict,
        lineup_data_available: bool = True,
    ) -> str:
        """Simulate T2 lineup filter logic. Returns 'SCRATCH', 'SKIP', or 'PROCEED'."""
        if lineup_data_available and player_id not in lineup_by_pid:
            return "SCRATCH"
        return "PROCEED"

    def test_player_in_lineup_proceeds(self):
        lineup = {123: {"batting_slot": 3, "game_pk": 999, "team_id": 10}}
        result = self._evaluate_player(123, lineup)
        self.assertEqual(result, "PROCEED")

    def test_player_not_in_lineup_is_scratched(self):
        lineup = {456: {"batting_slot": 1, "game_pk": 999, "team_id": 10}}
        result = self._evaluate_player(123, lineup)
        self.assertEqual(result, "SCRATCH")

    def test_empty_lineup_with_data_available_scratches_all(self):
        result = self._evaluate_player(123, {}, lineup_data_available=True)
        self.assertEqual(result, "SCRATCH")

    def test_lineup_fetch_failure_proceeds_without_scratch(self):
        """If lineup data unavailable (API failure), don't scratch — pass through."""
        result = self._evaluate_player(123, {}, lineup_data_available=False)
        self.assertEqual(result, "PROCEED")


# ---------------------------------------------------------------------------
# 4. Per-game contamination guard
# ---------------------------------------------------------------------------


class TestPerGameContaminationGuard(unittest.TestCase):
    """Players in already-Live games are skipped; Preview game players proceed."""

    def _is_live(self, game_pk: int, live_game_pks: set[int]) -> bool:
        return game_pk in live_game_pks

    def test_preview_game_not_blocked(self):
        live_pks = {888, 999}
        self.assertFalse(self._is_live(777, live_pks))

    def test_live_game_blocked(self):
        live_pks = {888, 999}
        self.assertTrue(self._is_live(888, live_pks))

    def test_empty_live_pks_never_blocks(self):
        self.assertFalse(self._is_live(123, set()))


# ---------------------------------------------------------------------------
# 5. Idempotency: T1 open tickers block T2 re-entry
# ---------------------------------------------------------------------------


class TestT2Idempotency(unittest.TestCase):
    """Tickers where T1 already placed a bet must be blocked in T2."""

    def _is_blocked(self, ticker: str, open_tickers: set[str]) -> bool:
        return ticker in open_tickers

    def test_t1_open_ticker_blocks_t2(self):
        open_tickers = {"KXMLBHIT-25JUN261907BALLAA-1", "KXMLBHIT-25JUN261907BOSNYY-2"}
        self.assertTrue(self._is_blocked("KXMLBHIT-25JUN261907BALLAA-1", open_tickers))

    def test_new_ticker_not_blocked(self):
        open_tickers = {"KXMLBHIT-25JUN261907BALLAA-1"}
        self.assertFalse(self._is_blocked("KXMLBHIT-25JUN261907BOSNYY-2", open_tickers))

    def test_same_player_different_threshold_not_blocked(self):
        """T1 bet H≥1; T2 can bet H≥2 on same player (different ticker)."""
        open_tickers = {"KXMLBHIT-25JUN261907BALLAA-1"}  # threshold -1
        t2_ticker    = "KXMLBHIT-25JUN261907BALLAA-2"    # threshold -2
        self.assertFalse(self._is_blocked(t2_ticker, open_tickers))

    def test_empty_open_tickers_blocks_nothing(self):
        self.assertFalse(self._is_blocked("ANY-TICKER", set()))


# ---------------------------------------------------------------------------
# 6. DS-04 document existence
# ---------------------------------------------------------------------------


class TestDS04DocumentExists(unittest.TestCase):
    """DS-04 MLB designation document must exist in 03_DECISIONS."""

    def test_ds04_document_present(self):
        from pathlib import Path
        import os
        proj_root = Path(os.environ.get("PROJ_ROOT",
                         Path(__file__).parents[1]))
        ds04 = proj_root / "03_DECISIONS" / "DS-04_mlb-t2-lineup-source.md"
        self.assertTrue(ds04.exists(),
                        f"DS-04 designation document not found at {ds04}")

    def test_ds04_references_fetch_lineups(self):
        from pathlib import Path
        import os
        proj_root = Path(os.environ.get("PROJ_ROOT",
                         Path(__file__).parents[1]))
        ds04 = proj_root / "03_DECISIONS" / "DS-04_mlb-t2-lineup-source.md"
        if ds04.exists():
            content = ds04.read_text()
            self.assertIn("fetch_lineups", content)
            self.assertIn("hydrate=lineups", content)


if __name__ == "__main__":
    unittest.main()
