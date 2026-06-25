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

    def test_excludes_open_different_date(self):
        portfolio = {
            "open_positions": [
                {"size_usd": 10.0, "pool_isolated": True, "game_date": "2026-06-23"},
            ],
            "closed_positions": [],
        }
        result = runner._reconstruct_t4_ledger(portfolio, "2026-06-24")
        assert result == pytest.approx(0.0)

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

    def test_kill_switch_path_in_logs(self):
        assert "t4_mlb_kill_switch.flag" in str(runner.KILL_SWITCH_PATH)

    def test_portfolio_path_isolated(self):
        assert "mlb_t4" in str(runner._PORTFOLIO_PATH)
        assert "paper_portfolio" in str(runner._PORTFOLIO_PATH)

    def test_component_name(self):
        assert runner.COMPONENT == "PIPE-07-MLB"
