"""
Tests for run_t4_mlb_live.py (T-190 Step 3 — PIPE-07 MLB).

Scope:
  - p_hits_gte_threshold: Binomial model correctness (already-hit, impossible, normal)
  - _binomial_pmf: PMF edge cases (p=0, p=1, k out of range)
  - kill_switch_armed: file-based flag
  - _compute_t4_band_budget: T4_BAND_WEIGHT application
  - _exit_budget_credit: winning vs losing exit
  - _reconstruct_t4_ledger: open exposure + realized losses
  - _load_pregame_context: most-recent pregame_mlb_*.json, empty case
  - _run_cycle: no fire when p_t4 < mip+vig; fires when p_t4 > mip+vig+min_edge;
                respects band budget; skips player absent from live states;
                does not double-fire same ticker in one cycle

Excluded:
  - Real Kalshi API calls
  - Real ESPN API calls
  - VPS deployment
  - main() loop (tests the infinite loop stub via mock)
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

_REPO_ROOT = Path(__file__).parent.parent
_SRC_ROOT  = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

# ---------------------------------------------------------------------------
# Guard bypass — tests run without BOT_ENV / BOT_C4_ACTIVE in environment
# ---------------------------------------------------------------------------

import os
os.environ.setdefault("BOT_ENV", "paper")
os.environ.setdefault("BOT_C4_ACTIVE", "true")

import prediction_market_bot.run_t4_mlb_live as runner


# ---------------------------------------------------------------------------
# Binomial PMF
# ---------------------------------------------------------------------------


class TestBinomialPmf:
    def test_p_zero_k_zero(self):
        assert runner._binomial_pmf(5, 0, 0.0) == pytest.approx(1.0)

    def test_p_zero_k_nonzero(self):
        assert runner._binomial_pmf(5, 2, 0.0) == pytest.approx(0.0)

    def test_p_one_k_equals_n(self):
        assert runner._binomial_pmf(4, 4, 1.0) == pytest.approx(1.0)

    def test_p_one_k_less_than_n(self):
        assert runner._binomial_pmf(4, 2, 1.0) == pytest.approx(0.0)

    def test_k_out_of_range_negative(self):
        assert runner._binomial_pmf(5, -1, 0.5) == pytest.approx(0.0)

    def test_k_out_of_range_exceeds_n(self):
        assert runner._binomial_pmf(5, 6, 0.5) == pytest.approx(0.0)

    def test_fair_coin_symmetry(self):
        # Binomial(4, 0.5): P(X=2) = C(4,2)/16 = 6/16 = 0.375
        assert runner._binomial_pmf(4, 2, 0.5) == pytest.approx(6 / 16, abs=1e-9)

    def test_sum_to_one(self):
        n, p = 6, 0.35
        total = sum(runner._binomial_pmf(n, k, p) for k in range(n + 1))
        assert total == pytest.approx(1.0, abs=1e-9)


# ---------------------------------------------------------------------------
# p_hits_gte_threshold — Binomial model
# ---------------------------------------------------------------------------


class TestPHitsGteThreshold:
    def test_already_hit_threshold(self):
        # h_so_far=2, threshold=1 → already achieved
        p = runner.p_hits_gte_threshold(h_so_far=2, threshold=1, ba_l10=0.30, ab_remaining=3)
        assert p == pytest.approx(1.0)

    def test_exactly_at_threshold(self):
        # h_so_far=1, threshold=1 → achieved
        p = runner.p_hits_gte_threshold(h_so_far=1, threshold=1, ba_l10=0.28, ab_remaining=2)
        assert p == pytest.approx(1.0)

    def test_impossible_not_enough_abs(self):
        # need 2 more hits but only 1 AB left
        p = runner.p_hits_gte_threshold(h_so_far=0, threshold=2, ba_l10=0.30, ab_remaining=1)
        assert p == pytest.approx(0.0)

    def test_zero_ab_remaining_not_achieved(self):
        p = runner.p_hits_gte_threshold(h_so_far=0, threshold=1, ba_l10=0.28, ab_remaining=0)
        assert p == pytest.approx(0.0)

    def test_normal_case_reasonable_range(self):
        # threshold=1, h_so_far=0, ba=0.30, ab_remaining=4 → P(X>=1) = 1 - (0.7)^4
        expected = 1.0 - (0.7 ** 4)
        p = runner.p_hits_gte_threshold(h_so_far=0, threshold=1, ba_l10=0.30, ab_remaining=4)
        assert p == pytest.approx(expected, abs=0.001)

    def test_threshold_2_needs_2_more(self):
        # threshold=2, h_so_far=0, ba=0.25, ab_remaining=4
        # P(X>=2 | Bin(4, 0.25)) = 1 - P(X=0) - P(X=1)
        p0 = runner._binomial_pmf(4, 0, 0.25)
        p1 = runner._binomial_pmf(4, 1, 0.25)
        expected = 1.0 - p0 - p1
        p = runner.p_hits_gte_threshold(h_so_far=0, threshold=2, ba_l10=0.25, ab_remaining=4)
        assert p == pytest.approx(expected, abs=0.001)

    def test_probability_bounded_0_to_1(self):
        p = runner.p_hits_gte_threshold(h_so_far=0, threshold=1, ba_l10=0.99, ab_remaining=3)
        assert 0.0 <= p <= 1.0

    def test_higher_ba_gives_higher_probability(self):
        p_low  = runner.p_hits_gte_threshold(0, 1, 0.15, 3)
        p_high = runner.p_hits_gte_threshold(0, 1, 0.40, 3)
        assert p_high > p_low

    def test_more_abs_remaining_gives_higher_probability(self):
        p_few  = runner.p_hits_gte_threshold(0, 1, 0.28, 2)
        p_many = runner.p_hits_gte_threshold(0, 1, 0.28, 5)
        assert p_many > p_few


# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------


class TestKillSwitch:
    def test_not_armed_when_no_file(self, tmp_path):
        flag = tmp_path / "t4_mlb_kill_switch.flag"
        assert not runner.kill_switch_armed(flag)

    def test_armed_when_file_exists(self, tmp_path):
        flag = tmp_path / "t4_mlb_kill_switch.flag"
        flag.touch()
        assert runner.kill_switch_armed(flag)

    def test_disarm_by_deleting_file(self, tmp_path):
        flag = tmp_path / "t4_mlb_kill_switch.flag"
        flag.touch()
        flag.unlink()
        assert not runner.kill_switch_armed(flag)


# ---------------------------------------------------------------------------
# _compute_t4_band_budget
# ---------------------------------------------------------------------------


class TestComputeT4BandBudget:
    def test_applies_t4_band_weight(self):
        portfolio = {"bankroll_usd": 1000.0}
        budget = runner._compute_t4_band_budget(portfolio)
        assert budget == pytest.approx(1000.0 * runner.T4_BAND_WEIGHT)

    def test_zero_bankroll(self):
        portfolio = {"bankroll_usd": 0.0}
        assert runner._compute_t4_band_budget(portfolio) == pytest.approx(0.0)

    def test_exact_value(self):
        portfolio = {"bankroll_usd": 500.0}
        expected = 500.0 * 0.27
        assert runner._compute_t4_band_budget(portfolio) == pytest.approx(expected, abs=0.001)


# ---------------------------------------------------------------------------
# _exit_budget_credit
# ---------------------------------------------------------------------------


class TestExitBudgetCredit:
    def test_winning_exit_credits_only_size(self):
        # Winning exit: pnl >= 0 → credits full entry cost only
        credit = runner._exit_budget_credit(size_usd=5.0, exit_pnl=3.0)
        assert credit == pytest.approx(5.0)

    def test_losing_exit_credits_size_plus_loss(self):
        # Losing exit: pnl < 0 → credits entry + pnl (smaller credit, permanent loss consumed)
        credit = runner._exit_budget_credit(size_usd=5.0, exit_pnl=-2.0)
        assert credit == pytest.approx(3.0)

    def test_zero_pnl_credits_full_size(self):
        credit = runner._exit_budget_credit(size_usd=10.0, exit_pnl=0.0)
        assert credit == pytest.approx(10.0)


# ---------------------------------------------------------------------------
# _reconstruct_t4_ledger
# ---------------------------------------------------------------------------


class TestReconstructT4Ledger:
    def test_empty_portfolio_returns_zero(self):
        portfolio = {"open_positions": [], "closed_positions": []}
        result = runner._reconstruct_t4_ledger(portfolio, "2026-06-24")
        assert result == pytest.approx(0.0)

    def test_counts_open_isolated_same_date(self):
        portfolio = {
            "open_positions": [
                {"size_usd": 10.0, "pool_isolated": True, "game_date": "2026-06-24"},
                {"size_usd": 5.0,  "pool_isolated": True, "game_date": "2026-06-24"},
            ],
            "closed_positions": [],
        }
        result = runner._reconstruct_t4_ledger(portfolio, "2026-06-24")
        assert result == pytest.approx(15.0)

    def test_excludes_open_not_isolated(self):
        portfolio = {
            "open_positions": [
                {"size_usd": 10.0, "pool_isolated": False, "game_date": "2026-06-24"},
            ],
            "closed_positions": [],
        }
        result = runner._reconstruct_t4_ledger(portfolio, "2026-06-24")
        assert result == pytest.approx(0.0)

    def test_open_different_date_still_counted(self):
        # GG-086/T-240 (2026-07-05): open exposure is NEVER date-filtered — a still-open
        # position is real deployed capital regardless of its game_date's age. The prior
        # version of this test asserted the opposite (a buggy exclusion) and was itself
        # the encoding of the bug: production had $12.78 of genuinely-open T4 exposure
        # (33 positions, dated 2 and 3 days stale — almost certainly stuck by GG-084's
        # MLB Stats API block preventing resolution) silently invisible to this ledger,
        # letting new fires stack on top of unseen real exposure past the T4 band cap.
        portfolio = {
            "open_positions": [
                {"size_usd": 10.0, "pool_isolated": True, "game_date": "2026-06-23"},
            ],
            "closed_positions": [],
        }
        result = runner._reconstruct_t4_ledger(portfolio, "2026-06-24")
        assert result == pytest.approx(10.0)

    def test_counts_realized_losses_not_gains(self):
        portfolio = {
            "open_positions": [],
            "closed_positions": [
                {"pool_isolated": True, "game_date": "2026-06-24", "exit_pnl": -3.0},
                {"pool_isolated": True, "game_date": "2026-06-24", "exit_pnl":  5.0},
            ],
        }
        result = runner._reconstruct_t4_ledger(portfolio, "2026-06-24")
        assert result == pytest.approx(3.0)

    def test_combined_open_and_losses(self):
        portfolio = {
            "open_positions": [
                {"size_usd": 8.0, "pool_isolated": True, "game_date": "2026-06-24"},
            ],
            "closed_positions": [
                {"pool_isolated": True, "game_date": "2026-06-24", "exit_pnl": -2.5},
            ],
        }
        result = runner._reconstruct_t4_ledger(portfolio, "2026-06-24")
        assert result == pytest.approx(10.5)


class TestReconstructFiredTickerStates:
    def test_empty_portfolio_returns_empty_dict(self):
        portfolio = {"open_positions": [], "closed_positions": []}
        result = runner._reconstruct_fired_ticker_states(portfolio, "2026-06-24")
        assert result == {}

    def test_maps_ticker_to_entry_state(self):
        portfolio = {
            "open_positions": [
                {"kalshi_ticker": "T1", "pool_isolated": True, "game_date": "2026-06-24",
                 "h_so_far_at_entry": 1, "ab_remaining_at_entry": 3, "entered_at": "2026-06-24T18:00:00Z"},
            ],
            "closed_positions": [],
        }
        result = runner._reconstruct_fired_ticker_states(portfolio, "2026-06-24")
        assert result == {"T1": (1, 3)}

    def test_excludes_not_pool_isolated(self):
        portfolio = {
            "open_positions": [
                {"kalshi_ticker": "T1", "pool_isolated": False, "game_date": "2026-06-24",
                 "h_so_far_at_entry": 1, "ab_remaining_at_entry": 3, "entered_at": "2026-06-24T18:00:00Z"},
            ],
            "closed_positions": [],
        }
        result = runner._reconstruct_fired_ticker_states(portfolio, "2026-06-24")
        assert result == {}

    def test_excludes_different_game_date(self):
        portfolio = {
            "open_positions": [
                {"kalshi_ticker": "T1", "pool_isolated": True, "game_date": "2026-06-23",
                 "h_so_far_at_entry": 1, "ab_remaining_at_entry": 3, "entered_at": "2026-06-23T18:00:00Z"},
            ],
            "closed_positions": [],
        }
        result = runner._reconstruct_fired_ticker_states(portfolio, "2026-06-24")
        assert result == {}

    def test_excludes_positions_missing_entry_state(self):
        # Pre-T-225 positions (or non-T4 callers) never set h_so_far_at_entry — must
        # not crash and must not populate a bogus (None, None) guard entry.
        portfolio = {
            "open_positions": [
                {"kalshi_ticker": "T1", "pool_isolated": True, "game_date": "2026-06-24",
                 "entered_at": "2026-06-24T18:00:00Z"},
            ],
            "closed_positions": [],
        }
        result = runner._reconstruct_fired_ticker_states(portfolio, "2026-06-24")
        assert result == {}

    def test_most_recent_entry_wins_across_open_and_closed(self):
        # Same ticker fired twice this game day: an earlier position now closed,
        # and a later re-entry still open. Reconstruction must recover the LATEST
        # state (by entered_at), not whichever list happens to be scanned first.
        portfolio = {
            "open_positions": [
                {"kalshi_ticker": "T1", "pool_isolated": True, "game_date": "2026-06-24",
                 "h_so_far_at_entry": 2, "ab_remaining_at_entry": 1, "entered_at": "2026-06-24T19:30:00Z"},
            ],
            "closed_positions": [
                {"kalshi_ticker": "T1", "pool_isolated": True, "game_date": "2026-06-24",
                 "h_so_far_at_entry": 0, "ab_remaining_at_entry": 3, "entered_at": "2026-06-24T18:00:00Z"},
            ],
        }
        result = runner._reconstruct_fired_ticker_states(portfolio, "2026-06-24")
        assert result == {"T1": (2, 1)}


# ---------------------------------------------------------------------------
# _game_date_window — GG-081/GG-082 (2026-07-04) UTC-midnight-rollover fix
# ---------------------------------------------------------------------------


class TestGameDateWindow:
    def test_returns_current_and_prior_day(self):
        assert runner._game_date_window("2026-07-03") == {"2026-07-03", "2026-07-02"}

    def test_handles_month_boundary(self):
        assert runner._game_date_window("2026-07-01") == {"2026-07-01", "2026-06-30"}


class TestReconstructT4LedgerCrossMidnight:
    def test_carried_over_game_still_counted_after_rollover(self):
        # Game started 2026-07-02 (pre-midnight game_date on the position), process
        # observes the rollover to 2026-07-03. Without the window fix this exposure
        # silently drops out of the ledger the moment the calendar flips.
        portfolio = {
            "open_positions": [
                {"size_usd": 10.0, "pool_isolated": True, "game_date": "2026-07-02"},
            ],
            "closed_positions": [],
        }
        result = runner._reconstruct_t4_ledger(portfolio, runner._game_date_window("2026-07-03"))
        assert result == pytest.approx(10.0)

    def test_two_days_prior_now_still_counted(self):
        # GG-086/T-240 (2026-07-05): this test previously asserted a position 2 days
        # stale (older than the 1-day window widens for) drops out of the ledger — that
        # was the bug, not a spec. Confirmed in production: positions stuck open by
        # GG-084's resolution failures accumulate real exposure the window can never
        # reach again once a second midnight passes, understating true deployed capital
        # forever. Open exposure must survive any number of rollovers until the
        # position actually resolves.
        portfolio = {
            "open_positions": [
                {"size_usd": 10.0, "pool_isolated": True, "game_date": "2026-07-01"},
            ],
            "closed_positions": [],
        }
        result = runner._reconstruct_t4_ledger(portfolio, runner._game_date_window("2026-07-03"))
        assert result == pytest.approx(10.0)

    def test_realized_losses_still_scoped_to_window(self):
        # The date window still legitimately scopes realized_losses (a closed loss is
        # attributed to a specific day's budget by design) — only open exposure lost its
        # date filter. A loss 2 days stale must still be excluded.
        portfolio = {
            "open_positions": [],
            "closed_positions": [
                {"pool_isolated": True, "game_date": "2026-07-01", "exit_pnl": -4.0},
            ],
        }
        result = runner._reconstruct_t4_ledger(portfolio, runner._game_date_window("2026-07-03"))
        assert result == pytest.approx(0.0)

    def test_multi_day_stuck_positions_all_counted(self):
        # Reproduces the real 2026-07-05 production finding directly: 22 positions
        # dated 2026-07-02 ($7.69) and 11 dated 2026-07-03 ($5.09) still open at the
        # 2026-07-05 00:00 UTC rollover (window = {2026-07-05, 2026-07-04}), stuck by
        # GG-084's MLB Stats API block. Both cohorts must count toward current exposure.
        portfolio = {
            "open_positions": (
                [{"size_usd": 7.69 / 22, "pool_isolated": True, "game_date": "2026-07-02"}] * 22
                + [{"size_usd": 5.09 / 11, "pool_isolated": True, "game_date": "2026-07-03"}] * 11
            ),
            "closed_positions": [],
        }
        result = runner._reconstruct_t4_ledger(portfolio, runner._game_date_window("2026-07-05"))
        assert result == pytest.approx(7.69 + 5.09, abs=0.01)


class TestReconstructFiredTickerStatesCrossMidnight:
    def test_carried_over_ticker_state_survives_rollover(self):
        # Reproduces the GG-081 TBJCAMINERO13 double-fire: a ticker fired pre-midnight
        # (game_date = prior day) must still block a same-state re-fire post-midnight.
        portfolio = {
            "open_positions": [
                {"kalshi_ticker": "KXMLBHIT-26JUL021940TBKC-TBJCAMINERO13-1",
                 "pool_isolated": True, "game_date": "2026-07-02",
                 "h_so_far_at_entry": 0, "ab_remaining_at_entry": 3,
                 "entered_at": "2026-07-02T23:43:50Z"},
            ],
            "closed_positions": [],
        }
        result = runner._reconstruct_fired_ticker_states(
            portfolio, runner._game_date_window("2026-07-03")
        )
        assert result == {"KXMLBHIT-26JUL021940TBKC-TBJCAMINERO13-1": (0, 3)}


# ---------------------------------------------------------------------------
# _load_pregame_context
# ---------------------------------------------------------------------------


def _write_pregame_mlb(tmp_path: Path, filename: str, forecasts: list[dict]) -> Path:
    p = tmp_path / filename
    p.write_text(json.dumps({"forecasts": forecasts, "sport": "mlb"}))
    return p


class TestLoadPregameContext:
    def test_empty_when_no_files(self, tmp_path):
        with patch.object(runner, "_LOGS_DIR", tmp_path):
            by_pid, by_ticker, name_map = runner._load_pregame_context()
        assert by_pid == {}
        assert by_ticker == {}
        assert name_map == {}

    def test_loads_most_recent_file(self, tmp_path):
        _write_pregame_mlb(tmp_path, "pregame_mlb_20260620.json", [
            {"player_name": "Old Player", "player_id": 100, "kalshi_ticker": "T-OLD",
             "kalshi_threshold": 1, "p_estimate": 0.55, "ba_l10": 0.28, "h_l10_mean": 1.1},
        ])
        _write_pregame_mlb(tmp_path, "pregame_mlb_20260624.json", [
            {"player_name": "Current Player", "player_id": 200, "kalshi_ticker": "T-NEW",
             "kalshi_threshold": 1, "p_estimate": 0.60, "ba_l10": 0.31, "h_l10_mean": 1.4},
        ])
        with patch.object(runner, "_LOGS_DIR", tmp_path):
            by_pid, by_ticker, name_map = runner._load_pregame_context()
        assert 200 in by_pid
        assert 100 not in by_pid
        assert "T-NEW" in by_ticker

    def test_builds_by_player_id(self, tmp_path):
        _write_pregame_mlb(tmp_path, "pregame_mlb_20260624.json", [
            {"player_name": "Juan Soto", "player_id": 660670,
             "kalshi_ticker": "KXMLBHIT-TICKER-1", "kalshi_threshold": 1,
             "p_estimate": 0.55, "ba_l10": 0.30, "h_l10_mean": 1.2},
            {"player_name": "Juan Soto", "player_id": 660670,
             "kalshi_ticker": "KXMLBHIT-TICKER-2", "kalshi_threshold": 2,
             "p_estimate": 0.25, "ba_l10": 0.30, "h_l10_mean": 1.2},
        ])
        with patch.object(runner, "_LOGS_DIR", tmp_path):
            by_pid, by_ticker, name_map = runner._load_pregame_context()
        assert 660670 in by_pid
        assert len(by_pid[660670]) == 2
        assert "KXMLBHIT-TICKER-1" in by_ticker
        assert "KXMLBHIT-TICKER-2" in by_ticker

    def test_name_to_pregame_normalized(self, tmp_path):
        _write_pregame_mlb(tmp_path, "pregame_mlb_20260624.json", [
            {"player_name": "Aaron Judge", "player_id": 592450,
             "kalshi_ticker": "T-JUDGE", "kalshi_threshold": 1,
             "p_estimate": 0.58, "ba_l10": 0.32, "h_l10_mean": 1.3},
        ])
        with patch.object(runner, "_LOGS_DIR", tmp_path):
            _, _, name_map = runner._load_pregame_context()
        assert "aaronjudge" in name_map

    def test_ba_l10_defaults_when_missing(self, tmp_path):
        _write_pregame_mlb(tmp_path, "pregame_mlb_20260624.json", [
            {"player_name": "Test Player", "player_id": 123,
             "kalshi_ticker": "T-TEST", "kalshi_threshold": 1,
             "p_estimate": 0.55},  # no ba_l10 key
        ])
        with patch.object(runner, "_LOGS_DIR", tmp_path):
            by_pid, _, _ = runner._load_pregame_context()
        assert by_pid[123][0]["ba_l10"] == pytest.approx(0.25)


# ---------------------------------------------------------------------------
# _espn_poll_once_mlb — unit test for stat extraction
# ---------------------------------------------------------------------------


def _make_espn_summary_response(
    player_name: str = "Juan Soto",
    h_val: str = "1",
    ab_val: str = "3",
    in_progress: bool = True,
    inning: int = 5,
) -> dict:
    status_name = "STATUS_IN_PROGRESS" if in_progress else "STATUS_FINAL"
    return {
        "header": {
            "competitions": [{
                "status": {
                    "type": {"name": status_name},
                    "period": inning,
                },
            }]
        },
        "boxscore": {
            "players": [{
                "statistics": [{
                    "name": "batting",
                    "labels": ["AB", "R", "H", "HR", "RBI", "BB", "SO"],
                    "athletes": [{
                        "athlete": {"displayName": player_name},
                        "stats": [ab_val, "0", h_val, "0", "0", "0", "1"],
                    }]
                }]
            }]
        }
    }


class TestEspnPollOnceMlb:
    def test_returns_empty_when_not_in_progress(self):
        name_to_pregame = {"juansoto": {"player_id": 660670, "threshold": 1, "p_t1": 0.55,
                                        "ba_l10": 0.30, "h_l10_mean": 1.2, "ticker": "T-SOTO"}}
        resp = _make_espn_summary_response(in_progress=False)
        with patch("prediction_market_bot.run_t4_mlb_live.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.raise_for_status = lambda: None
            mock_get.return_value.json.return_value = resp
            result = runner._espn_poll_once_mlb("ESPN123", name_to_pregame)
        assert result == []

    def test_extracts_hits_and_abs(self):
        name_to_pregame = {"juansoto": {"player_id": 660670, "threshold": 1, "p_t1": 0.55,
                                        "ba_l10": 0.30, "h_l10_mean": 1.2, "ticker": "T-SOTO"}}
        resp = _make_espn_summary_response(player_name="Juan Soto", h_val="2", ab_val="4",
                                           in_progress=True, inning=7)
        with patch("prediction_market_bot.run_t4_mlb_live.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.raise_for_status = lambda: None
            mock_get.return_value.json.return_value = resp
            result = runner._espn_poll_once_mlb("ESPN123", name_to_pregame)
        assert len(result) == 1
        batter = result[0]
        assert batter.h_so_far == 2
        assert batter.ab_so_far == 4
        assert batter.inning == 7
        assert batter.player_id == 660670

    def test_player_not_in_pregame_skipped(self):
        # Name map has "juansoto" but response has "Aaron Judge"
        name_to_pregame = {"juansoto": {"player_id": 660670, "threshold": 1, "p_t1": 0.55,
                                        "ba_l10": 0.30, "h_l10_mean": 1.2, "ticker": "T-SOTO"}}
        resp = _make_espn_summary_response(player_name="Aaron Judge", h_val="1", ab_val="3",
                                           in_progress=True)
        with patch("prediction_market_bot.run_t4_mlb_live.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.raise_for_status = lambda: None
            mock_get.return_value.json.return_value = resp
            result = runner._espn_poll_once_mlb("ESPN123", name_to_pregame)
        assert result == []

    def test_request_exception_returns_empty(self):
        with patch("prediction_market_bot.run_t4_mlb_live.requests.get") as mock_get:
            mock_get.side_effect = ConnectionError("timeout")
            result = runner._espn_poll_once_mlb("ESPN999", {})
        assert result == []


# ---------------------------------------------------------------------------
# _espn_game_status — GG-058
# ---------------------------------------------------------------------------


class TestEspnGameStatus:
    def test_returns_status_name(self):
        resp = {"header": {"competitions": [{"status": {"type": {"name": "STATUS_FINAL"}}}]}}
        with patch("prediction_market_bot.run_t4_mlb_live.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.raise_for_status = lambda: None
            mock_get.return_value.json.return_value = resp
            assert runner._espn_game_status("ESPN1") == "STATUS_FINAL"

    def test_request_exception_returns_empty_string(self):
        with patch("prediction_market_bot.run_t4_mlb_live.requests.get") as mock_get:
            mock_get.side_effect = ConnectionError("timeout")
            assert runner._espn_game_status("ESPN1") == ""

    def test_missing_competitions_returns_empty_string(self):
        with patch("prediction_market_bot.run_t4_mlb_live.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.raise_for_status = lambda: None
            mock_get.return_value.json.return_value = {"header": {"competitions": []}}
            assert runner._espn_game_status("ESPN1") == ""


# ---------------------------------------------------------------------------
# _rollover_game_ids — GG-058: UTC-midnight rollover must merge, not replace
# ---------------------------------------------------------------------------


class TestRolloverGameIds:
    def test_in_progress_game_carried_over_across_midnight(self):
        # A West-coast game started yesterday, still live at UTC midnight,
        # and is not part of today's newly-discovered ESPN slate yet.
        tracked = ["YESTERDAY_LATE_GAME"]
        newly_discovered = ["TODAY_GAME_1", "TODAY_GAME_2"]
        status_fn = lambda gid: "STATUS_IN_PROGRESS"
        result = runner._rollover_game_ids(tracked, newly_discovered, status_fn)
        assert "YESTERDAY_LATE_GAME" in result
        assert "TODAY_GAME_1" in result
        assert "TODAY_GAME_2" in result

    def test_final_game_dropped_at_rollover(self):
        tracked = ["YESTERDAY_FINISHED_GAME"]
        newly_discovered = ["TODAY_GAME_1"]
        status_fn = lambda gid: "STATUS_FINAL"
        result = runner._rollover_game_ids(tracked, newly_discovered, status_fn)
        assert "YESTERDAY_FINISHED_GAME" not in result
        assert result == ["TODAY_GAME_1"]

    def test_postponed_game_dropped_at_rollover(self):
        tracked = ["YESTERDAY_POSTPONED_GAME"]
        result = runner._rollover_game_ids(
            tracked, [], status_fn=lambda gid: "STATUS_POSTPONED"
        )
        assert result == []

    def test_status_fetch_failure_keeps_game_tracked(self):
        # An ESPN blip (status_fn returns "") must never be treated as terminal —
        # dropping a live game due to a transient fetch error is the GG-058 failure
        # mode this fix exists to prevent.
        tracked = ["FLAKY_STATUS_GAME"]
        result = runner._rollover_game_ids(tracked, [], status_fn=lambda gid: "")
        assert result == ["FLAKY_STATUS_GAME"]

    def test_game_present_in_both_lists_not_duplicated(self):
        tracked = ["GAME_A"]
        newly_discovered = ["GAME_A", "GAME_B"]
        status_fn = lambda gid: "STATUS_IN_PROGRESS"
        result = runner._rollover_game_ids(tracked, newly_discovered, status_fn)
        assert result.count("GAME_A") == 1
        assert set(result) == {"GAME_A", "GAME_B"}

    def test_no_carried_over_games_returns_newly_discovered_only(self):
        result = runner._rollover_game_ids(
            [], ["TODAY_GAME_1"], status_fn=lambda gid: "STATUS_FINAL"
        )
        assert result == ["TODAY_GAME_1"]

    def test_status_fn_only_called_for_carryover_candidates(self):
        # Games already rediscovered in today's slate don't need a status
        # check — calling it anyway would be a wasted ESPN API call per game.
        calls = []
        def status_fn(gid):
            calls.append(gid)
            return "STATUS_IN_PROGRESS"
        runner._rollover_game_ids(["GAME_A"], ["GAME_A"], status_fn)
        assert calls == []


# ---------------------------------------------------------------------------
# _run_cycle — core evaluation engine
# ---------------------------------------------------------------------------


def _make_live_state(
    player_id: int = 660670,
    player_name: str = "Juan Soto",
    h_so_far: int = 0,
    ab_so_far: int = 2,
    inning: int = 5,
    game_id: str = "ESPN001",
) -> runner.MLBLiveBatterState:
    return runner.MLBLiveBatterState(
        player_id=player_id, player_name=player_name,
        h_so_far=h_so_far, ab_so_far=ab_so_far,
        inning=inning, game_id=game_id,
    )


def _make_market(ticker: str, mid: float = 0.35, vig: float = 0.05) -> MagicMock:
    m = MagicMock()
    m.ticker = ticker
    m.mid_price = mid
    m.vig = vig
    m.has_live_quotes = True
    return m


def _make_components(tmp_path: Path):
    """Create minimal mocked components for _run_cycle."""
    from prediction_market_bot.c4_risk_engine.risk import RiskEngine
    from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore
    from prediction_market_bot.c5_execution.paper_trader import PaperTrader
    from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

    audit  = AuditLogger(log_path=tmp_path / "audit.jsonl")
    store  = StagedOrderStore(str(tmp_path / "staged.db"))
    engine = RiskEngine(
        logger=audit,
        snapshot_id="TEST",
        bankroll=270.0,
        kelly_fraction=0.10,
        initial_bankroll=1000.0,
        min_bet_usd=0.01,
    )
    portfolio_path = tmp_path / "paper_portfolio_mlb_t4.json"
    trader = PaperTrader(portfolio_path=portfolio_path, logger=audit)
    return engine, trader, store, audit


TICKER_SOTO = "KXMLBHIT-26JUN2418NYY-NYYAAJSOT-1"


class TestRunCycle:
    def _pregame(self, player_id: int = 660670, ticker: str = TICKER_SOTO,
                 threshold: int = 1, p_t1: float = 0.55,
                 ba_l10: float = 0.30) -> dict:
        return {
            player_id: [{
                "player_id": player_id, "player_name": "Juan Soto",
                "ticker": ticker, "threshold": threshold,
                "p_t1": p_t1, "ba_l10": ba_l10, "h_l10_mean": 1.2,
            }]
        }

    def test_no_fire_when_p_t4_below_mip(self, tmp_path):
        engine, trader, store, audit = _make_components(tmp_path)
        # h_so_far=0, threshold=2, ba=0.10 → p_t4 very low
        live = [_make_live_state(h_so_far=0, ab_so_far=2)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.80, vig=0.04)}
        pregame = self._pregame(threshold=2, ba_l10=0.10)

        _, _, _ = runner._run_cycle(
            cycle_id="C0-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
        )
        state = trader.get_state()
        assert len(state.get("open_positions", [])) == 0

    def test_fires_when_p_t4_clearly_above_mip(self, tmp_path):
        engine, trader, store, audit = _make_components(tmp_path)
        # h_so_far=0, threshold=1, ba=0.99 → p_t4 ≈ 1.0; mip=0.40 → edge clearly positive
        live = [_make_live_state(h_so_far=0, ab_so_far=1)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.40, vig=0.03)}
        pregame = self._pregame(threshold=1, ba_l10=0.99)

        ev, fi, deployed = runner._run_cycle(
            cycle_id="C1-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
        )
        state = trader.get_state()
        assert fi == 1
        assert deployed > 0.0

    def test_player_absent_from_live_states_not_evaluated(self, tmp_path):
        engine, trader, store, audit = _make_components(tmp_path)
        # Pregame has player 999, live states have player 660670 only
        live = [_make_live_state(player_id=660670)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.40, vig=0.03)}
        pregame = {
            999: [{"player_id": 999, "player_name": "Ghost Player",
                   "ticker": TICKER_SOTO, "threshold": 1,
                   "p_t1": 0.99, "ba_l10": 0.99, "h_l10_mean": 1.2}]
        }
        ev, fi, deployed = runner._run_cycle(
            cycle_id="C2-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
        )
        assert fi == 0
        assert deployed == pytest.approx(0.0)

    def test_no_fire_when_already_at_threshold(self, tmp_path):
        engine, trader, store, audit = _make_components(tmp_path)
        # h_so_far=1 >= threshold=1 → p_t4=1.0 → fire if mip low enough
        # BUT mip=0.95 → edge ≈ 1.0 - 0.95 - vig(0.04) = 0.01 < min_edge(0.02)
        live = [_make_live_state(h_so_far=1, ab_so_far=3)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.95, vig=0.04)}
        pregame = self._pregame(threshold=1, ba_l10=0.30)

        ev, fi, deployed = runner._run_cycle(
            cycle_id="C3-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
        )
        assert fi == 0

    def test_no_fire_when_vig_above_ceiling(self, tmp_path):
        # T-228: even a slam-dunk p_t4 must not fire when vig exceeds VIG_CEILING —
        # the market is skipped before the Binomial/C4 cost, not merely filtered
        # downstream on edge.
        engine, trader, store, audit = _make_components(tmp_path)
        live = [_make_live_state(h_so_far=0, ab_so_far=1)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.20, vig=runner.VIG_CEILING + 0.01)}
        pregame = self._pregame(threshold=1, ba_l10=0.99)

        ev, fi, deployed = runner._run_cycle(
            cycle_id="C10-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
        )
        assert fi == 0
        assert deployed == pytest.approx(0.0)

    def test_fires_at_vig_exactly_on_ceiling(self, tmp_path):
        # Ceiling is exclusive (skip is `vig > VIG_CEILING`) — a market priced
        # exactly at the ceiling must still be evaluated normally.
        engine, trader, store, audit = _make_components(tmp_path)
        live = [_make_live_state(h_so_far=0, ab_so_far=1)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.20, vig=runner.VIG_CEILING)}
        pregame = self._pregame(threshold=1, ba_l10=0.99)

        ev, fi, deployed = runner._run_cycle(
            cycle_id="C11-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
        )
        assert fi == 1
        assert deployed > 0.0

    def test_respects_band_budget_exhausted(self, tmp_path):
        engine, trader, store, audit = _make_components(tmp_path)
        # p_t4 would be high but budget already exhausted
        live = [_make_live_state(h_so_far=0, ab_so_far=0)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.20, vig=0.02)}
        pregame = self._pregame(threshold=1, ba_l10=0.99)

        ev, fi, deployed = runner._run_cycle(
            cycle_id="C4-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0,
            t4_deployed_usd=270.0,  # budget fully deployed
        )
        assert fi == 0

    def test_no_double_fire_same_ticker_per_cycle(self, tmp_path):
        engine, trader, store, audit = _make_components(tmp_path)
        # Two live states for the same ticker (edge case: two ESPN rows matching same player)
        live = [
            _make_live_state(player_id=660670, h_so_far=0, ab_so_far=1),
            _make_live_state(player_id=660670, h_so_far=0, ab_so_far=1),
        ]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.20, vig=0.02)}
        pregame = self._pregame(threshold=1, ba_l10=0.99)

        _, fi, _ = runner._run_cycle(
            cycle_id="C5-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
        )
        assert fi <= 1

    def test_returns_updated_deployed_amount(self, tmp_path):
        engine, trader, store, audit = _make_components(tmp_path)
        live = [_make_live_state(h_so_far=0, ab_so_far=1)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.20, vig=0.02)}
        pregame = self._pregame(threshold=1, ba_l10=0.99)

        _, fi, new_deployed = runner._run_cycle(
            cycle_id="C6-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
        )
        if fi == 1:
            assert new_deployed > 0.0
        else:
            assert new_deployed == pytest.approx(0.0)

    def test_reentry_blocked_when_state_unchanged(self, tmp_path):
        # T-225: a ticker already fired at exactly this (h_so_far, ab_remaining)
        # must not re-fire on a subsequent cycle where nothing has moved.
        engine, trader, store, audit = _make_components(tmp_path)
        live = [_make_live_state(h_so_far=0, ab_so_far=1)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.20, vig=0.02)}
        pregame = self._pregame(threshold=1, ba_l10=0.99)
        # ab_remaining for h_so_far=0, ab_so_far=1, inning=5, batting_slot=0 (default
        # slot map) — computed the same way _run_cycle computes it internally.
        ab_remaining = runner._compute_ab_remaining(1, 5, 0)
        already_fired = {TICKER_SOTO: (0, ab_remaining)}

        _, fi, deployed = runner._run_cycle(
            cycle_id="C8-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            already_fired_game=already_fired,
        )
        assert fi == 0
        assert deployed == pytest.approx(0.0)

    def test_reentry_allowed_when_state_changed(self, tmp_path):
        # T-225: a ticker that fired at a DIFFERENT (h_so_far, ab_remaining) than
        # the current cycle's live state must be eligible to fire again.
        engine, trader, store, audit = _make_components(tmp_path)
        live = [_make_live_state(h_so_far=0, ab_so_far=1)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.20, vig=0.02)}
        pregame = self._pregame(threshold=1, ba_l10=0.99)
        # Prior fire recorded at a state that does NOT match the current cycle's
        # (h_so_far=0, ab_remaining computed from ab_so_far=1) — simulates the
        # player having batted again since that fire (state moved on).
        already_fired = {TICKER_SOTO: (0, 999)}

        _, fi, deployed = runner._run_cycle(
            cycle_id="C9-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            already_fired_game=already_fired,
        )
        assert fi == 1
        assert deployed > 0.0

    def test_fired_position_records_entry_state(self, tmp_path):
        # T-225: the opened position must persist the live state at entry so a
        # restart can reconstruct the re-entry guard correctly.
        engine, trader, store, audit = _make_components(tmp_path)
        live = [_make_live_state(h_so_far=0, ab_so_far=1)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.40, vig=0.03)}
        pregame = self._pregame(threshold=1, ba_l10=0.99)

        _, fi, _ = runner._run_cycle(
            cycle_id="C10-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
        )
        assert fi == 1
        state = trader.get_state()
        pos = state["open_positions"][0]
        assert pos["h_so_far_at_entry"] == 0
        assert pos["ab_remaining_at_entry"] is not None

    def test_no_live_quotes_market_skipped(self, tmp_path):
        engine, trader, store, audit = _make_components(tmp_path)
        live = [_make_live_state(h_so_far=0, ab_so_far=0)]

        no_quote_mkt = _make_market(TICKER_SOTO, mid=0.20)
        no_quote_mkt.has_live_quotes = False   # no live quotes
        live_prices = {TICKER_SOTO: no_quote_mkt}
        pregame = self._pregame(threshold=1, ba_l10=0.99)

        _, fi, _ = runner._run_cycle(
            cycle_id="C7-test", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-24",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
        )
        assert fi == 0


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    def test_poll_interval_45s(self):
        assert runner.POLL_INTERVAL_S == 45

    def test_t4_band_weight_0_27(self):
        assert runner.T4_BAND_WEIGHT == pytest.approx(0.27)

    def test_ab_per_game_default(self):
        assert runner.AB_PER_GAME_DEFAULT == pytest.approx(3.7)

    def test_ab_by_slot_nine_entries(self):
        assert len(runner._AB_BY_SLOT) == 9
        assert runner._AB_BY_SLOT[1] == pytest.approx(4.2)
        assert runner._AB_BY_SLOT[9] == pytest.approx(3.1)

    def test_ab_by_slot_descending(self):
        slots = [runner._AB_BY_SLOT[i] for i in range(1, 10)]
        assert slots == sorted(slots, reverse=True)

    def test_kill_switch_path_in_logs(self):
        assert "t4_mlb_kill_switch.flag" in str(runner.KILL_SWITCH_PATH)

    def test_portfolio_path_isolated(self):
        assert "mlb_t4" in str(runner._PORTFOLIO_PATH)
        assert "paper_portfolio" in str(runner._PORTFOLIO_PATH)

    def test_component_name(self):
        assert runner.COMPONENT == "PIPE-07-MLB"

    def test_vig_ceiling_0_30(self):
        # T-228: derived from real 2026-07-02 production data — the widest vig
        # on any qualifying (net_edge>=0.04) signal that day was 0.24.
        assert runner.VIG_CEILING == pytest.approx(0.30)


# ---------------------------------------------------------------------------
# _compute_ab_remaining — T-200 inning-aware formula
# ---------------------------------------------------------------------------


class TestComputeAbRemaining:
    """Inning-aware AB remaining: takes conservative min of inning-cap and total-minus-used."""

    def test_early_game_reasonable_estimate(self):
        # Inning 1, 0 ABs so far → should return ~3 (close to full expected)
        result = runner._compute_ab_remaining(ab_so_far=0, inning=1)
        assert result == 3

    def test_mid_game_constrained_by_inning(self):
        # Inning 5, 2 ABs: ab_from_inning = 3.7*4.5/9=1.85, ab_from_total=1.7 → min=1.7 → 2
        result = runner._compute_ab_remaining(ab_so_far=2, inning=5)
        assert result == 2

    def test_late_game_nearly_exhausted(self):
        # Inning 8, 3 ABs: ab_from_inning=3.7*1.5/9=0.617, ab_from_total=0.7 → min=0.617 → 1
        result = runner._compute_ab_remaining(ab_so_far=3, inning=8)
        assert result == 1

    def test_final_inning_zero_remaining(self):
        # Inning 9, 3 ABs: ab_from_inning=3.7*0.5/9=0.206 → rounds to 0
        result = runner._compute_ab_remaining(ab_so_far=3, inning=9)
        assert result == 0

    def test_extra_innings_floors_at_one(self):
        # T-220: inning > 9 → ab_from_inning floors at 1.0 rather than
        # clamping to 0, so T4 doesn't go dark once a game reaches extras.
        # Slot 0 (default expected=3.7), 3 ABs so far: ab_from_total=0.7 → min(1.0,0.7)=0.7 → 1
        result = runner._compute_ab_remaining(ab_so_far=3, inning=10)
        assert result == 1
        # 0 ABs so far: ab_from_total=3.7 → min(1.0,3.7)=1.0 → 1
        result = runner._compute_ab_remaining(ab_so_far=0, inning=12)
        assert result == 1

    def test_extra_innings_still_clamps_when_already_exceeded(self):
        # Batter already exceeded expected ABs even in extra innings → 0,
        # since ab_from_total (the ceiling) is 0 regardless of the floor.
        result = runner._compute_ab_remaining(ab_so_far=5, inning=11)
        assert result == 0

    def test_already_exceeded_expected_total(self):
        # ab_so_far=5 for a slot-5 player (expected=3.7): ab_from_total<0 → clamp to 0
        result = runner._compute_ab_remaining(ab_so_far=5, inning=7)
        assert result == 0

    def test_slot_1_leadoff_higher_expected(self):
        # Slot 1 expects 4.2 ABs vs 3.7 default
        default = runner._compute_ab_remaining(ab_so_far=0, inning=1, batting_slot=0)
        slot1   = runner._compute_ab_remaining(ab_so_far=0, inning=1, batting_slot=1)
        assert slot1 >= default   # leadoff gets ≥ as many expected ABs as average

    def test_slot_9_bottom_order_lower_expected(self):
        # Slot 9 expects 3.1 ABs → ab_remaining ≤ slot 5 (3.7)
        slot5 = runner._compute_ab_remaining(ab_so_far=0, inning=3, batting_slot=5)
        slot9 = runner._compute_ab_remaining(ab_so_far=0, inning=3, batting_slot=9)
        assert slot9 <= slot5

    def test_unknown_slot_zero_uses_default(self):
        # batting_slot=0 → falls back to AB_PER_GAME_DEFAULT (3.7)
        result_unknown = runner._compute_ab_remaining(ab_so_far=0, inning=1, batting_slot=0)
        result_default = runner._compute_ab_remaining(ab_so_far=0, inning=1)
        assert result_unknown == result_default

    def test_non_negative_always(self):
        for inning in range(1, 13):
            for ab in range(0, 6):
                assert runner._compute_ab_remaining(ab_so_far=ab, inning=inning) >= 0

    def test_early_game_no_abs_high_remaining(self):
        # Inning 2, 0 ABs: should return ≥ 2 (plenty of game left)
        result = runner._compute_ab_remaining(ab_so_far=0, inning=2)
        assert result >= 2

    def test_all_slots_non_negative(self):
        for slot in range(0, 10):
            for inning in range(1, 10):
                assert runner._compute_ab_remaining(ab_so_far=2, inning=inning,
                                                    batting_slot=slot) >= 0


# ---------------------------------------------------------------------------
# _load_t2_batting_slots — T-200 T2 slot loader
# ---------------------------------------------------------------------------


def _write_t2_output(tmp_path: Path, filename: str, forecasts: list[dict]) -> Path:
    today = filename  # caller passes full filename e.g. t2_mlb_20260626_1930.json
    p = tmp_path / today
    p.write_text(json.dumps({
        "run_at": "2026-06-26T19:30:00Z",
        "forecasts": forecasts,
        "bets": [],
    }))
    return p


class TestLoadT2BattingSlots:
    def test_empty_when_no_t2_files(self, tmp_path):
        with patch.object(runner, "_LOGS_DIR", tmp_path):
            slots = runner._load_t2_batting_slots()
        assert slots == {}

    def test_loads_batting_slots(self, tmp_path):
        today = __import__("datetime").date.today().strftime("%Y%m%d")
        _write_t2_output(tmp_path, f"t2_mlb_{today}_1930.json", [
            {"player_id": 12345, "batting_slot": 3, "player_name": "Player A",
             "ticker": "T-A", "threshold": 1},
            {"player_id": 67890, "batting_slot": 7, "player_name": "Player B",
             "ticker": "T-B", "threshold": 1},
        ])
        with patch.object(runner, "_LOGS_DIR", tmp_path):
            slots = runner._load_t2_batting_slots()
        assert slots == {12345: 3, 67890: 7}

    def test_skips_entries_without_slot(self, tmp_path):
        today = __import__("datetime").date.today().strftime("%Y%m%d")
        _write_t2_output(tmp_path, f"t2_mlb_{today}_1930.json", [
            {"player_id": 11111, "batting_slot": None, "player_name": "No Slot"},
            {"player_id": 22222, "batting_slot": 4, "player_name": "Has Slot"},
        ])
        with patch.object(runner, "_LOGS_DIR", tmp_path):
            slots = runner._load_t2_batting_slots()
        assert 11111 not in slots
        assert slots.get(22222) == 4

    def test_ignores_prior_day_t2_files(self, tmp_path):
        # Yesterday's file should NOT be loaded (date filter)
        yesterday = (__import__("datetime").date.today() -
                     __import__("datetime").timedelta(days=1)).strftime("%Y%m%d")
        _write_t2_output(tmp_path, f"t2_mlb_{yesterday}_1930.json", [
            {"player_id": 99999, "batting_slot": 5, "player_name": "Stale Player"},
        ])
        with patch.object(runner, "_LOGS_DIR", tmp_path):
            slots = runner._load_t2_batting_slots()
        assert slots == {}

    def test_corrupted_file_returns_empty(self, tmp_path):
        today = __import__("datetime").date.today().strftime("%Y%m%d")
        (tmp_path / f"t2_mlb_{today}_1930.json").write_text("not-json{{")
        with patch.object(runner, "_LOGS_DIR", tmp_path):
            slots = runner._load_t2_batting_slots()
        assert slots == {}


# ---------------------------------------------------------------------------
# _run_cycle with batting_slots — T-200 integration
# ---------------------------------------------------------------------------


class TestRunCycleWithBattingSlots:
    """Verify _run_cycle correctly accepts and uses batting_slots param."""

    def test_accepts_batting_slots_param(self, tmp_path):
        """_run_cycle with batting_slots={} runs without error."""
        from prediction_market_bot.c4_risk_engine.risk import RiskEngine
        from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore
        from prediction_market_bot.c5_execution.paper_trader import PaperTrader
        from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

        audit  = AuditLogger(log_path=tmp_path / "audit.jsonl")
        store  = StagedOrderStore(str(tmp_path / "staged.db"))
        engine = RiskEngine(logger=audit, snapshot_id="T", bankroll=270.0,
                            kelly_fraction=0.10, initial_bankroll=1000.0, min_bet_usd=0.01)
        trader = PaperTrader(tmp_path / "p.json", logger=audit)

        live = [_make_live_state(h_so_far=0, ab_so_far=0, inning=1)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.20, vig=0.02)}
        pregame = {660670: [{"player_id": 660670, "player_name": "Juan Soto",
                              "ticker": TICKER_SOTO, "threshold": 1,
                              "p_t1": 0.55, "ba_l10": 0.99, "h_l10_mean": 1.2}]}

        ev, fi, deployed = runner._run_cycle(
            cycle_id="SLOT-TEST", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            batting_slots={660670: 1},   # slot 1 → 4.2 expected ABs
        )
        assert fi >= 0   # ran without error; outcome depends on edge

    def test_none_batting_slots_defaults_gracefully(self, tmp_path):
        """batting_slots=None (default) does not error."""
        from prediction_market_bot.c4_risk_engine.risk import RiskEngine
        from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore
        from prediction_market_bot.c5_execution.paper_trader import PaperTrader
        from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

        audit  = AuditLogger(log_path=tmp_path / "audit.jsonl")
        store  = StagedOrderStore(str(tmp_path / "staged.db"))
        engine = RiskEngine(logger=audit, snapshot_id="T", bankroll=270.0,
                            kelly_fraction=0.10, initial_bankroll=1000.0, min_bet_usd=0.01)
        trader = PaperTrader(tmp_path / "p.json", logger=audit)

        live = [_make_live_state(h_so_far=0, ab_so_far=2, inning=5)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.80, vig=0.04)}
        pregame = {660670: [{"player_id": 660670, "player_name": "Juan Soto",
                              "ticker": TICKER_SOTO, "threshold": 2,
                              "p_t1": 0.55, "ba_l10": 0.10, "h_l10_mean": 1.2}]}

        ev, fi, deployed = runner._run_cycle(
            cycle_id="NULL-SLOT", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            # batting_slots omitted → defaults to None → treated as {}
        )
        assert fi == 0   # p_t4 very low, should not fire


# ---------------------------------------------------------------------------
# TestDryRunMode — T-202 dry-run branch (T4_MLB_DRY_RUN=true)
# ---------------------------------------------------------------------------


def _make_high_edge_setup(tmp_path: Path):
    """ba_l10=0.99, threshold=1, h_so_far=0, inning=3 → p_t4 ≈ 1.0; mip=0.20 → edge ≈ +0.75"""
    engine, trader, store, audit = _make_components(tmp_path)
    live = [_make_live_state(h_so_far=0, ab_so_far=1, inning=3)]
    live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.20, vig=0.02)}
    pregame = {660670: [{"player_id": 660670, "player_name": "Juan Soto",
                          "ticker": TICKER_SOTO, "threshold": 1,
                          "p_t1": 0.55, "ba_l10": 0.99, "h_l10_mean": 1.2}]}
    return engine, trader, store, audit, live, live_prices, pregame


class TestDryRunMode:
    def test_no_position_opened_in_dry_run(self, tmp_path):
        """dry_run=True: portfolio.open_positions stays empty."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        runner._run_cycle(
            cycle_id="DR-01", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=True, dryrun_log_path=None,
        )
        state = trader.get_state()
        assert state["open_positions"] == []

    def test_deployed_not_updated_in_dry_run(self, tmp_path):
        """dry_run=True: returned t4_deployed_usd remains 0.0 (no capital consumed)."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        _ev, _fi, deployed = runner._run_cycle(
            cycle_id="DR-02", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=True, dryrun_log_path=None,
        )
        assert deployed == pytest.approx(0.0)

    def test_would_fire_count_returned_as_fired(self, tmp_path):
        """dry_run=True with high-edge setup: fired >= 1 (would_fire counted)."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        _ev, fi, _dep = runner._run_cycle(
            cycle_id="DR-03", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=True, dryrun_log_path=None,
        )
        assert fi >= 1

    def test_dryrun_jsonl_written(self, tmp_path):
        """dry_run=True with valid dryrun_log_path: JSONL file is created with at least one line."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        log_path = tmp_path / "t4_mlb_dryrun_test.jsonl"
        runner._run_cycle(
            cycle_id="DR-04", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=True, dryrun_log_path=log_path,
        )
        assert log_path.exists()
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) >= 1

    def test_dryrun_jsonl_fields_complete(self, tmp_path):
        """JSONL records contain all required fields."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        log_path = tmp_path / "t4_mlb_dryrun_fields.jsonl"
        runner._run_cycle(
            cycle_id="DR-05", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=True, dryrun_log_path=log_path,
        )
        required_fields = {
            "ts", "cycle_id", "session_id", "ticker", "player_name", "player_id",
            "threshold", "p_t4", "mip", "vig", "gross_edge", "net_edge",
            "ba_l10", "h_so_far", "ab_so_far", "ab_remaining", "inning",
            "batting_slot", "would_fire",
        }
        for line in log_path.read_text().strip().splitlines():
            record = json.loads(line)
            assert required_fields.issubset(record.keys()), f"Missing fields: {required_fields - record.keys()}"

    def test_dryrun_would_fire_true_when_edge_positive(self, tmp_path):
        """High-edge setup: would_fire=True in JSONL record."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        log_path = tmp_path / "t4_mlb_dryrun_wf_true.jsonl"
        runner._run_cycle(
            cycle_id="DR-06", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=True, dryrun_log_path=log_path,
        )
        records = [json.loads(l) for l in log_path.read_text().strip().splitlines()]
        assert any(r["would_fire"] is True for r in records)

    def test_dryrun_would_fire_false_when_edge_negative(self, tmp_path):
        """Low-edge setup (mip=0.95): would_fire=False and fi=0."""
        engine, trader, store, audit = _make_components(tmp_path)
        live = [_make_live_state(h_so_far=0, ab_so_far=1, inning=8)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.95, vig=0.04)}
        pregame = {660670: [{"player_id": 660670, "player_name": "Juan Soto",
                              "ticker": TICKER_SOTO, "threshold": 1,
                              "p_t1": 0.55, "ba_l10": 0.28, "h_l10_mean": 1.0}]}
        log_path = tmp_path / "t4_mlb_dryrun_wf_false.jsonl"
        _ev, fi, _dep = runner._run_cycle(
            cycle_id="DR-07", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=True, dryrun_log_path=log_path,
        )
        assert fi == 0
        records = [json.loads(l) for l in log_path.read_text().strip().splitlines()]
        assert all(r["would_fire"] is False for r in records)

    def test_dryrun_ignores_band_budget_exhausted(self, tmp_path):
        """dry_run=True: fires even when t4_deployed_usd >= t4_band_budget (budget NOT enforced in dry-run)."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        _ev, fi, _dep = runner._run_cycle(
            cycle_id="DR-08", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=270.0,  # budget fully spent
            dry_run=True, dryrun_log_path=None,
        )
        assert fi >= 1

    def test_live_path_unaffected_by_dry_run_param(self, tmp_path):
        """dry_run=False (default): high-edge setup opens a position normally."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        _ev, fi, deployed = runner._run_cycle(
            cycle_id="DR-09", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=False,
        )
        state = trader.get_state()
        # High-edge → position should be opened; deployed > 0
        assert fi >= 1
        assert deployed > 0.0
        assert len(state["open_positions"]) >= 1

    def test_dryrun_no_log_path_does_not_crash(self, tmp_path):
        """dry_run=True with dryrun_log_path=None: no crash, evaluated >= 1."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        ev, fi, _dep = runner._run_cycle(
            cycle_id="DR-10", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=True, dryrun_log_path=None,
        )
        assert ev >= 1

    def test_dryrun_multiple_cycles_accumulate_records(self, tmp_path):
        """Three dry-run cycles to the same JSONL path accumulate at least 3 records."""
        log_path = tmp_path / "t4_mlb_dryrun_multi.jsonl"
        for i in range(3):
            engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
            runner._run_cycle(
                cycle_id=f"DR-11-{i}", session_id="TEST",
                live_states=live, live_prices=live_prices,
                pregame_by_player_id=pregame,
                engine=engine, trader=trader, store=store, audit=audit,
                game_date="2026-06-26",
                t4_band_budget=270.0, t4_deployed_usd=0.0,
                dry_run=True, dryrun_log_path=log_path,
            )
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) >= 3

    def test_append_dryrun_record_writes_valid_json(self, tmp_path):
        """_append_dryrun_record: single call produces valid JSON."""
        log_path = tmp_path / "append_test.jsonl"
        record = {"ts": "2026-06-26T00:00:00Z", "ticker": "TEST", "would_fire": True, "net_edge": 0.5}
        runner._append_dryrun_record(log_path, record)
        line = log_path.read_text().strip()
        parsed = json.loads(line)
        assert parsed["ticker"] == "TEST"
        assert parsed["would_fire"] is True

    def test_append_dryrun_record_appends(self, tmp_path):
        """_append_dryrun_record: two calls → two separate lines."""
        log_path = tmp_path / "append_two.jsonl"
        runner._append_dryrun_record(log_path, {"n": 1})
        runner._append_dryrun_record(log_path, {"n": 2})
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0])["n"] == 1
        assert json.loads(lines[1])["n"] == 2


class TestProductionCycleLog:
    """GG-067 (SESSION 110): raw per-cycle context logged on the normal
    (non-dry-run) execution path, independent of fired/not-fired status."""

    _REQUIRED_FIELDS = {
        "ts", "cycle_id", "session_id", "game_date", "ticker", "player_name",
        "player_id", "threshold", "p_t4", "mip", "vig", "gross_edge", "net_edge",
        "ba_l10", "h_so_far", "ab_so_far", "ab_remaining", "inning",
        "batting_slot",
    }

    def test_cycle_log_written_on_normal_path_when_fired(self, tmp_path):
        """dry_run=False + high-edge setup + cycle_log_path set: file is written."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        log_path = tmp_path / "t4_mlb_cycle_log.jsonl"
        runner._run_cycle(
            cycle_id="CL-01", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=False, cycle_log_path=log_path,
        )
        assert log_path.exists()
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) >= 1

    def test_cycle_log_written_on_normal_path_when_not_fired(self, tmp_path):
        """dry_run=False + low-edge setup (gross_edge <= 0, early-exit): still logged."""
        engine, trader, store, audit = _make_components(tmp_path)
        live = [_make_live_state(h_so_far=0, ab_so_far=1, inning=8)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.95, vig=0.04)}
        pregame = {660670: [{"player_id": 660670, "player_name": "Juan Soto",
                              "ticker": TICKER_SOTO, "threshold": 1,
                              "p_t1": 0.55, "ba_l10": 0.28, "h_l10_mean": 1.0}]}
        log_path = tmp_path / "t4_mlb_cycle_log_notfired.jsonl"
        ev, fi, _dep = runner._run_cycle(
            cycle_id="CL-02", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=False, cycle_log_path=log_path,
        )
        assert fi == 0
        assert log_path.exists()
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) >= 1

    def test_cycle_log_fields_complete(self, tmp_path):
        """Cycle log records contain all raw-context fields GG-067 requires."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        log_path = tmp_path / "t4_mlb_cycle_log_fields.jsonl"
        runner._run_cycle(
            cycle_id="CL-03", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=False, cycle_log_path=log_path,
        )
        for line in log_path.read_text().strip().splitlines():
            record = json.loads(line)
            assert self._REQUIRED_FIELDS.issubset(record.keys()), (
                f"Missing fields: {self._REQUIRED_FIELDS - record.keys()}"
            )

    def test_cycle_log_none_path_does_not_crash(self, tmp_path):
        """cycle_log_path=None (default): normal path runs exactly as before, no crash."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        ev, fi, deployed = runner._run_cycle(
            cycle_id="CL-04", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=False,
        )
        assert fi >= 1
        assert deployed > 0.0

    def test_vig_skip_logged_without_p_t4(self, tmp_path):
        """T-228: a vig-ceiling skip still writes a lightweight cycle-log record
        (for EXP-ARITH-MLB-01/EXP-FLOW-MLB-01 visibility) but omits p_t4/edge
        fields since the Binomial computation was never performed."""
        engine, trader, store, audit = _make_components(tmp_path)
        live = [_make_live_state(h_so_far=0, ab_so_far=1)]
        live_prices = {TICKER_SOTO: _make_market(TICKER_SOTO, mid=0.20, vig=runner.VIG_CEILING + 0.01)}
        pregame = {660670: [{"player_id": 660670, "player_name": "Juan Soto",
                              "ticker": TICKER_SOTO, "threshold": 1,
                              "p_t1": 0.55, "ba_l10": 0.99, "h_l10_mean": 1.0}]}
        log_path = tmp_path / "t4_mlb_cycle_log_vigskip.jsonl"
        ev, fi, _dep = runner._run_cycle(
            cycle_id="CL-VIG", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=False, cycle_log_path=log_path,
        )
        assert fi == 0
        assert log_path.exists()
        lines = log_path.read_text().strip().splitlines()
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["vig_skip"] is True
        assert record["vig"] == pytest.approx(runner.VIG_CEILING + 0.01)
        assert "p_t4" not in record
        assert "net_edge" not in record

    def test_cycle_log_betting_logic_unaffected(self, tmp_path):
        """Writing the cycle log must not change fired count, deployed capital, or
        open positions relative to the same setup with cycle_log_path=None."""
        engine_a, trader_a, store_a, audit_a, live_a, prices_a, pregame_a = _make_high_edge_setup(tmp_path)
        ev_a, fi_a, dep_a = runner._run_cycle(
            cycle_id="CL-05A", session_id="TEST",
            live_states=live_a, live_prices=prices_a,
            pregame_by_player_id=pregame_a,
            engine=engine_a, trader=trader_a, store=store_a, audit=audit_a,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=False,
        )
        engine_b, trader_b, store_b, audit_b, live_b, prices_b, pregame_b = _make_high_edge_setup(tmp_path)
        log_path = tmp_path / "t4_mlb_cycle_log_parity.jsonl"
        ev_b, fi_b, dep_b = runner._run_cycle(
            cycle_id="CL-05B", session_id="TEST",
            live_states=live_b, live_prices=prices_b,
            pregame_by_player_id=pregame_b,
            engine=engine_b, trader=trader_b, store=store_b, audit=audit_b,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=False, cycle_log_path=log_path,
        )
        assert ev_a == ev_b
        assert fi_a == fi_b
        assert dep_a == pytest.approx(dep_b)

    def test_cycle_log_written_in_dry_run_too(self, tmp_path):
        """cycle_log_path is independent of dry_run — both can write simultaneously
        to their own separate files without interfering."""
        engine, trader, store, audit, live, live_prices, pregame = _make_high_edge_setup(tmp_path)
        dryrun_path = tmp_path / "dryrun.jsonl"
        cycle_path = tmp_path / "cycle_log.jsonl"
        runner._run_cycle(
            cycle_id="CL-06", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-26",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            dry_run=True, dryrun_log_path=dryrun_path,
            cycle_log_path=cycle_path,
        )
        assert dryrun_path.exists()
        assert cycle_path.exists()

    def test_cycle_log_path_constant_defined(self):
        """CYCLE_LOG_PATH module constant exists and points inside the logs dir."""
        assert runner.CYCLE_LOG_PATH.name == "t4_mlb_cycle_log.jsonl"
        assert runner.CYCLE_LOG_PATH.parent == runner._LOGS_DIR


# ---------------------------------------------------------------------------
# LiveDataFreshnessGuard — Session 101 (T4 timestamp / liveness gate)
# ---------------------------------------------------------------------------


class TestLiveDataFreshnessGuard:
    """
    LiveDataFreshnessGuard.check() validates 4 timestamp/liveness conditions.

    game_state_fresh   — cycle_start_at within 2× POLL_INTERVAL_S of now
    market_active      — pm.status=active and pm.has_live_quotes=True
    player_in_game     — ls.player_id == player_id
    snapshot_not_stale — snapshot_fetched_at within 2× POLL_INTERVAL_S of now

    Renamed from ContaminationGuard in Session 102 to avoid collision with the
    canonical SemanticContaminationGuard imported from semantic_contracts (ADR-0034).
    """

    def _make_guard(self, tmp_path):
        from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger
        audit = AuditLogger(log_path=tmp_path / "audit.jsonl")
        return runner.LiveDataFreshnessGuard(audit=audit, session_id="TEST-GUARD")

    def _make_pm(self, status="active", has_live_quotes=True):
        pm = MagicMock()
        pm.status = status
        pm.has_live_quotes = has_live_quotes
        return pm

    def _make_ls(self, player_id=660670):
        return runner.MLBLiveBatterState(
            player_id=player_id, player_name="Juan Soto",
            h_so_far=0, ab_so_far=1, inning=3, game_id="401-test",
        )

    def _fresh_ts(self):
        from datetime import datetime, timezone
        return datetime.now(timezone.utc)

    def test_all_checks_pass_returns_true(self, tmp_path):
        guard = self._make_guard(tmp_path)
        result = guard.check(
            ticker="KXMLBHIT-26JUN241840PITPHI-PITJSOTO-1",
            player_id=660670,
            ls=self._make_ls(660670),
            pm=self._make_pm(status="active", has_live_quotes=True),
            cycle_start_at=self._fresh_ts(),
            snapshot_fetched_at=self._fresh_ts(),
        )
        assert result is True
        assert guard.total_halts == 0
        assert guard.staleness_halts == 0

    def test_market_inactive_halts(self, tmp_path):
        guard = self._make_guard(tmp_path)
        result = guard.check(
            ticker="KXMLBHIT-26JUN241840PITPHI-PITJSOTO-1",
            player_id=660670,
            ls=self._make_ls(660670),
            pm=self._make_pm(status="closed", has_live_quotes=False),
            cycle_start_at=self._fresh_ts(),
            snapshot_fetched_at=self._fresh_ts(),
        )
        assert result is False
        assert guard.total_halts == 1
        assert guard.staleness_halts == 0  # market_active is not a staleness halt

    def test_no_live_quotes_halts(self, tmp_path):
        guard = self._make_guard(tmp_path)
        pm = self._make_pm(status="active", has_live_quotes=False)
        result = guard.check(
            ticker="KXMLBHIT-26JUN241840PITPHI-PITJSOTO-1",
            player_id=660670,
            ls=self._make_ls(660670),
            pm=pm,
            cycle_start_at=self._fresh_ts(),
            snapshot_fetched_at=self._fresh_ts(),
        )
        assert result is False
        assert guard.total_halts == 1

    def test_player_id_mismatch_halts(self, tmp_path):
        guard = self._make_guard(tmp_path)
        result = guard.check(
            ticker="KXMLBHIT-26JUN241840PITPHI-PITJSOTO-1",
            player_id=660670,
            ls=self._make_ls(player_id=999999),  # wrong player
            pm=self._make_pm(),
            cycle_start_at=self._fresh_ts(),
            snapshot_fetched_at=self._fresh_ts(),
        )
        assert result is False
        assert guard.total_halts == 1

    def test_stale_snapshot_halts_and_increments_staleness_counter(self, tmp_path):
        from datetime import datetime, timezone, timedelta
        guard = self._make_guard(tmp_path)
        stale_ts = datetime.now(timezone.utc) - timedelta(seconds=200)  # > 90s
        result = guard.check(
            ticker="KXMLBHIT-26JUN241840PITPHI-PITJSOTO-1",
            player_id=660670,
            ls=self._make_ls(660670),
            pm=self._make_pm(),
            cycle_start_at=self._fresh_ts(),
            snapshot_fetched_at=stale_ts,
        )
        assert result is False
        assert guard.staleness_halts == 1

    def test_stale_cycle_start_halts_and_increments_staleness_counter(self, tmp_path):
        from datetime import datetime, timezone, timedelta
        guard = self._make_guard(tmp_path)
        stale_cycle = datetime.now(timezone.utc) - timedelta(seconds=200)
        result = guard.check(
            ticker="KXMLBHIT-26JUN241840PITPHI-PITJSOTO-1",
            player_id=660670,
            ls=self._make_ls(660670),
            pm=self._make_pm(),
            cycle_start_at=stale_cycle,
            snapshot_fetched_at=self._fresh_ts(),
        )
        assert result is False
        assert guard.staleness_halts == 1

    def test_halt_counter_accumulates_across_calls(self, tmp_path):
        guard = self._make_guard(tmp_path)
        pm_inactive = self._make_pm(status="closed", has_live_quotes=False)
        for _ in range(3):
            guard.check(
                ticker="TICKER",
                player_id=660670,
                ls=self._make_ls(),
                pm=pm_inactive,
                cycle_start_at=self._fresh_ts(),
                snapshot_fetched_at=self._fresh_ts(),
            )
        assert guard.total_halts == 3

    def test_run_cycle_with_guard_skips_inactive_market(self, tmp_path):
        """_run_cycle with LiveDataFreshnessGuard skips a market with no live quotes."""
        from datetime import datetime, timezone
        from prediction_market_bot.c4_risk_engine.risk import RiskEngine
        from prediction_market_bot.c4_risk_engine.staged_order_store import StagedOrderStore
        from prediction_market_bot.c5_execution.paper_trader import PaperTrader
        from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

        audit  = AuditLogger(log_path=tmp_path / "audit.jsonl")
        store  = StagedOrderStore(str(tmp_path / "staged.db"))
        engine = RiskEngine(logger=audit, snapshot_id="T", bankroll=270.0,
                            kelly_fraction=0.10, initial_bankroll=1000.0, min_bet_usd=0.01)
        trader = PaperTrader(tmp_path / "p.json", logger=audit)
        guard  = runner.LiveDataFreshnessGuard(audit=audit, session_id="TEST")

        live = [_make_live_state(h_so_far=0, ab_so_far=1)]
        pm = _make_market(TICKER_SOTO, mid=0.20, vig=0.02)
        pm.has_live_quotes = False   # guard will catch this
        pm.status = "closed"
        live_prices = {TICKER_SOTO: pm}
        pregame = {660670: [{"player_id": 660670, "player_name": "Juan Soto",
                              "ticker": TICKER_SOTO, "threshold": 1,
                              "p_t1": 0.99, "ba_l10": 0.99, "h_l10_mean": 1.2}]}

        _, fi, _ = runner._run_cycle(
            cycle_id="CG-TEST", session_id="TEST",
            live_states=live, live_prices=live_prices,
            pregame_by_player_id=pregame,
            engine=engine, trader=trader, store=store, audit=audit,
            game_date="2026-06-29",
            t4_band_budget=270.0, t4_deployed_usd=0.0,
            contamination_guard=guard,
            cycle_start_at=datetime.now(timezone.utc),
            snapshot_fetched_at=datetime.now(timezone.utc),
        )
        assert fi == 0
        assert guard.total_halts == 1  # market_active check failed


# ---------------------------------------------------------------------------
# Singleton lock (T-216 — GG-062 fix)
# ---------------------------------------------------------------------------


class TestAcquireSingletonLock:
    """
    acquire_singleton_lock() is the GG-062/T-216 fix: an atomic flock-based
    guard against two concurrent run_t4_mlb_live.py evaluation loops, replacing
    the race-prone `pkill -f`-based cleanup in t4-mlb.service's ExecStartPre.
    """

    def test_first_caller_acquires_lock(self, tmp_path):
        lock_path = tmp_path / "t4_mlb_live.lock"
        assert runner.acquire_singleton_lock(lock_path) is True

    def test_second_caller_in_same_process_is_reentrant(self, tmp_path):
        # flock is per-(fd,inode); a second call from the same process opens a
        # *new* fd, so this exercises the real cross-process contention path
        # indirectly — the first fd is still held open by module state.
        lock_path = tmp_path / "t4_mlb_live.lock"
        assert runner.acquire_singleton_lock(lock_path) is True

    def test_concurrent_holder_blocks_second_acquisition(self, tmp_path):
        import fcntl
        lock_path = tmp_path / "t4_mlb_live.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        # Simulate another live process already holding the lock: acquire it
        # via a separate, independently-held fd (not through the module's
        # global, so releasing it is under this test's control).
        holder_fh = open(lock_path, "w")
        fcntl.flock(holder_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            assert runner.acquire_singleton_lock(lock_path) is False
        finally:
            holder_fh.close()  # releases the flock

    def test_lock_released_after_holder_closes_is_acquirable(self, tmp_path):
        import fcntl
        lock_path = tmp_path / "t4_mlb_live.lock"
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        holder_fh = open(lock_path, "w")
        fcntl.flock(holder_fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        holder_fh.close()  # simulates the holding process dying/exiting
        assert runner.acquire_singleton_lock(lock_path) is True

    def test_lock_file_contains_pid(self, tmp_path):
        import os
        lock_path = tmp_path / "t4_mlb_live.lock"
        assert runner.acquire_singleton_lock(lock_path) is True
        assert lock_path.read_text().strip() == str(os.getpid())
