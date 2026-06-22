"""Tests for scripts/run_t177_edge_monitor.py — T-177 edge inversion monitor.

Verifies the three possible verdicts (ANTI-PREDICTIVE, MONOTONIC, INCONCLUSIVE),
the filtering logic (duplicates, fee_contaminated), and the statistical test.
"""
from __future__ import annotations

import json
import tempfile
import csv
from pathlib import Path

import pytest
import sys, os
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from run_t177_edge_monitor import (
    Position,
    analyse,
    VERDICT_ANTI,
    VERDICT_MONO,
    VERDICT_INC,
    MIN_N,
    DEFAULT_ALPHA,
    _load_portfolio,
    _load_csv,
    _fisher_pvalue,
    _tercile_table,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_positions(n_pos_win: int, n_pos_loss: int, n_neg_win: int, n_neg_loss: int) -> list[Position]:
    """Build a position list from counts of the 2x2 edge×outcome cell."""
    pos = []
    for _ in range(n_pos_win):
        pos.append(Position(fee_net_edge=0.05, win=1, game_date="2026-04-01", direction="YES", pnl=5.0))
    for _ in range(n_pos_loss):
        pos.append(Position(fee_net_edge=0.05, win=0, game_date="2026-04-01", direction="YES", pnl=-5.0))
    for _ in range(n_neg_win):
        pos.append(Position(fee_net_edge=-0.05, win=1, game_date="2026-04-01", direction="YES", pnl=5.0))
    for _ in range(n_neg_loss):
        pos.append(Position(fee_net_edge=-0.05, win=0, game_date="2026-04-01", direction="YES", pnl=-5.0))
    return pos


# ---------------------------------------------------------------------------
# TestVerdicts
# ---------------------------------------------------------------------------

class TestVerdicts:
    def test_anti_predictive_clear_inversion(self):
        # edge>0: 5 win / 20 loss (winrate=0.20); edge<=0: 20 win / 5 loss (winrate=0.80)
        pos = _make_positions(n_pos_win=5, n_pos_loss=20, n_neg_win=20, n_neg_loss=5)
        result = analyse(pos, alpha=DEFAULT_ALPHA)
        assert result["verdict"] == VERDICT_ANTI

    def test_monotonic_clear_signal(self):
        # edge>0: 20 win / 5 loss (winrate=0.80); edge<=0: 5 win / 20 loss (winrate=0.20)
        pos = _make_positions(n_pos_win=20, n_pos_loss=5, n_neg_win=5, n_neg_loss=20)
        result = analyse(pos, alpha=DEFAULT_ALPHA)
        assert result["verdict"] == VERDICT_MONO

    def test_inconclusive_no_difference(self):
        # edge>0: 15 win / 15 loss = 50%; edge<=0: 15 win / 15 loss = 50%
        pos = _make_positions(n_pos_win=15, n_pos_loss=15, n_neg_win=15, n_neg_loss=15)
        result = analyse(pos, alpha=DEFAULT_ALPHA)
        assert result["verdict"] == VERDICT_INC

    def test_inconclusive_below_min_n(self):
        # n < MIN_N → always INCONCLUSIVE regardless of signal
        pos = _make_positions(n_pos_win=1, n_pos_loss=5, n_neg_win=5, n_neg_loss=1)
        assert len(pos) < MIN_N
        result = analyse(pos, alpha=DEFAULT_ALPHA)
        assert result["verdict"] == VERDICT_INC

    def test_inconclusive_small_sample_even_inverted(self):
        # 10 bets, clearly inverted, but n < MIN_N
        pos = _make_positions(n_pos_win=1, n_pos_loss=4, n_neg_win=4, n_neg_loss=1)
        assert len(pos) < MIN_N
        result = analyse(pos)
        assert result["verdict"] == VERDICT_INC

    def test_verdict_matches_nba_finals_pattern(self):
        # Replicate the known Finals finding: edge>0 winrate=0.356, edge<=0 winrate=0.747
        # Use n=158: ~70 edge>0, ~88 edge<=0 (approximate Finals split)
        # 70 * 0.356 = 25 win; 88 * 0.747 = 66 win
        pos = _make_positions(n_pos_win=25, n_pos_loss=45, n_neg_win=66, n_neg_loss=22)
        result = analyse(pos, alpha=0.10)
        assert result["verdict"] == VERDICT_ANTI
        assert result["winrate_edge_pos"] < result["winrate_edge_neg"]


# ---------------------------------------------------------------------------
# TestStatistics
# ---------------------------------------------------------------------------

class TestStatistics:
    def test_fisher_anti_predictive_low_p(self):
        # Strong inversion → low p-value
        pos_pos = [Position(0.05, 1, "", "", 5.0)] * 5 + [Position(0.05, 0, "", "", -5.0)] * 20
        neg_pos = [Position(-0.05, 1, "", "", 5.0)] * 20 + [Position(-0.05, 0, "", "", -5.0)] * 5
        or_, pval = _fisher_pvalue(pos_pos, neg_pos)
        assert pval < 0.10

    def test_fisher_no_difference_high_p(self):
        pos_pos = [Position(0.05, 1, "", "", 5.0)] * 10 + [Position(0.05, 0, "", "", -5.0)] * 10
        neg_pos = [Position(-0.05, 1, "", "", 5.0)] * 10 + [Position(-0.05, 0, "", "", -5.0)] * 10
        or_, pval = _fisher_pvalue(pos_pos, neg_pos)
        assert pval > 0.10

    def test_result_contains_fisher_fields(self):
        pos = _make_positions(10, 10, 10, 10)
        result = analyse(pos)
        assert "fisher_pvalue" in result
        assert "fisher_odds_ratio" in result
        assert 0.0 <= result["fisher_pvalue"] <= 1.0

    def test_overall_winrate_correct(self):
        # 30 win, 30 loss → 0.50
        pos = _make_positions(15, 15, 15, 15)
        result = analyse(pos)
        assert abs(result["overall_winrate"] - 0.5) < 0.01

    def test_result_n_matches_positions(self):
        pos = _make_positions(10, 10, 10, 10)
        result = analyse(pos)
        assert result["n"] == 40


# ---------------------------------------------------------------------------
# TestTercileTable
# ---------------------------------------------------------------------------

class TestTercileTable:
    def test_three_terciles_returned(self):
        pos = [Position(float(i) / 100 - 0.3, 1, "", "", 1.0) for i in range(60)]
        rows = _tercile_table(pos)
        assert len(rows) == 3

    def test_tercile_order_low_to_high(self):
        pos = [Position(float(i) / 100, 1, "", "", 1.0) for i in range(60)]
        rows = _tercile_table(pos)
        assert rows[0]["edge_max"] <= rows[1]["edge_min"] or rows[0]["edge_max"] <= rows[2]["edge_max"]
        assert rows[0]["edge_mean"] < rows[2]["edge_mean"]

    def test_tercile_n_sums_to_total(self):
        pos = [Position(float(i) / 100, 1, "", "", 1.0) for i in range(60)]
        rows = _tercile_table(pos)
        assert sum(r["n"] for r in rows) == 60

    def test_empty_returns_empty(self):
        assert _tercile_table([]) == []


# ---------------------------------------------------------------------------
# TestWindowFilter
# ---------------------------------------------------------------------------

class TestWindowFilter:
    def test_window_limits_sample(self):
        pos = _make_positions(5, 5, 10, 10)
        result_full = analyse(pos)
        result_window = analyse(pos, window=20)
        assert result_window["n"] == 20

    def test_window_larger_than_n_uses_all(self):
        pos = _make_positions(5, 5, 10, 10)
        result = analyse(pos, window=len(pos) + 100)
        assert result["n"] == len(pos)


# ---------------------------------------------------------------------------
# TestPortfolioLoader
# ---------------------------------------------------------------------------

class TestPortfolioLoader:
    def _make_portfolio(self, positions: list[dict]) -> str:
        """Write a temporary portfolio JSON and return its path."""
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump({"bankroll_usd": 1000.0, "closed_positions": positions}, tmp)
        tmp.flush()
        return tmp.name

    def test_loads_clean_positions(self):
        positions = [
            {"fee_net_edge": 0.05, "outcome": "WIN", "direction": "YES",
             "game_date": "2026-04-01", "pnl": 5.0, "duplicate_of": None,
             "fee_contaminated": False},
            {"fee_net_edge": -0.03, "outcome": "LOSS", "direction": "NO",
             "game_date": "2026-04-01", "pnl": -3.0, "duplicate_of": None,
             "fee_contaminated": False},
        ]
        path = self._make_portfolio(positions)
        loaded = _load_portfolio(Path(path))
        assert len(loaded) == 2

    def test_excludes_duplicates_by_default(self):
        positions = [
            {"fee_net_edge": 0.05, "outcome": "WIN", "direction": "YES",
             "game_date": "2026-04-01", "pnl": 5.0, "duplicate_of": "POS-ORIGINAL",
             "fee_contaminated": False},
            {"fee_net_edge": -0.03, "outcome": "LOSS", "direction": "NO",
             "game_date": "2026-04-01", "pnl": -3.0, "duplicate_of": None,
             "fee_contaminated": False},
        ]
        path = self._make_portfolio(positions)
        loaded = _load_portfolio(Path(path), exclude_duplicates=True)
        assert len(loaded) == 1

    def test_includes_duplicates_when_flagged(self):
        positions = [
            {"fee_net_edge": 0.05, "outcome": "WIN", "direction": "YES",
             "game_date": "2026-04-01", "pnl": 5.0, "duplicate_of": "POS-ORIGINAL",
             "fee_contaminated": False},
        ]
        path = self._make_portfolio(positions)
        loaded = _load_portfolio(Path(path), exclude_duplicates=False)
        assert len(loaded) == 1

    def test_excludes_fee_contaminated(self):
        positions = [
            {"fee_net_edge": 0.05, "outcome": "WIN", "direction": "YES",
             "game_date": "2026-04-01", "pnl": 5.0, "duplicate_of": None,
             "fee_contaminated": True},
        ]
        path = self._make_portfolio(positions)
        loaded = _load_portfolio(Path(path), exclude_fee_contaminated=True)
        assert len(loaded) == 0

    def test_skips_unresolved_outcomes(self):
        positions = [
            {"fee_net_edge": 0.05, "outcome": "OPEN", "direction": "YES",
             "game_date": "2026-04-01", "pnl": 0.0, "duplicate_of": None,
             "fee_contaminated": False},
        ]
        path = self._make_portfolio(positions)
        loaded = _load_portfolio(Path(path))
        assert len(loaded) == 0


# ---------------------------------------------------------------------------
# TestCSVLoader
# ---------------------------------------------------------------------------

class TestCSVLoader:
    def _make_csv(self, rows: list[dict]) -> str:
        tmp = tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False)
        if rows:
            writer = csv.DictWriter(tmp, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
        tmp.flush()
        return tmp.name

    def test_loads_basic_csv(self):
        rows = [
            {"fee_net_edge": "0.05", "outcome": "WIN", "direction": "YES",
             "game_date": "2026-04-01", "realized_pnl": "5.0",
             "duplicate_of": "", "is_clean": "True", "contamination": ""},
        ]
        path = self._make_csv(rows)
        loaded = _load_csv(Path(path))
        assert len(loaded) == 1
        assert loaded[0].fee_net_edge == pytest.approx(0.05)

    def test_excludes_fee_contaminated_csv(self):
        rows = [
            {"fee_net_edge": "0.05", "outcome": "WIN", "direction": "YES",
             "game_date": "2026-04-01", "realized_pnl": "5.0",
             "duplicate_of": "", "is_clean": "False", "contamination": "fee_contaminated"},
        ]
        path = self._make_csv(rows)
        loaded = _load_csv(Path(path), exclude_fee_contaminated=True)
        assert len(loaded) == 0

    def test_excludes_duplicate_csv(self):
        rows = [
            {"fee_net_edge": "0.05", "outcome": "WIN", "direction": "YES",
             "game_date": "2026-04-01", "realized_pnl": "5.0",
             "duplicate_of": "POS-ORIGINAL", "is_clean": "True", "contamination": ""},
        ]
        path = self._make_csv(rows)
        loaded = _load_csv(Path(path), exclude_duplicates=True)
        assert len(loaded) == 0


# ---------------------------------------------------------------------------
# TestMainCLI
# ---------------------------------------------------------------------------

class TestMainCLI:
    def test_missing_portfolio_returns_error(self):
        rc = main(["--portfolio", "/tmp/nonexistent_t177_test_abc123.json"])
        assert rc != 0

    def test_ci_mode_anti_predictive_exits_2(self, tmp_path):
        # Build a portfolio JSON with strong anti-predictive signal
        positions = []
        for _ in range(25):
            positions.append({"fee_net_edge": 0.05, "outcome": "LOSS",
                               "direction": "YES", "game_date": "2026-04-01",
                               "pnl": -5.0, "duplicate_of": None, "fee_contaminated": False})
        for _ in range(5):
            positions.append({"fee_net_edge": 0.05, "outcome": "WIN",
                               "direction": "YES", "game_date": "2026-04-01",
                               "pnl": 5.0, "duplicate_of": None, "fee_contaminated": False})
        for _ in range(5):
            positions.append({"fee_net_edge": -0.05, "outcome": "LOSS",
                               "direction": "YES", "game_date": "2026-04-01",
                               "pnl": -5.0, "duplicate_of": None, "fee_contaminated": False})
        for _ in range(25):
            positions.append({"fee_net_edge": -0.05, "outcome": "WIN",
                               "direction": "YES", "game_date": "2026-04-01",
                               "pnl": 5.0, "duplicate_of": None, "fee_contaminated": False})
        portfolio_path = tmp_path / "test_portfolio.json"
        portfolio_path.write_text(json.dumps({
            "bankroll_usd": 1000.0, "closed_positions": positions
        }))
        rc = main(["--portfolio", str(portfolio_path), "--ci"])
        assert rc == 2

    def test_ci_mode_monotonic_exits_0(self, tmp_path):
        # edge>0 wins more → MONOTONIC → exit 0
        positions = []
        for _ in range(25):
            positions.append({"fee_net_edge": 0.05, "outcome": "WIN",
                               "direction": "YES", "game_date": "2026-04-01",
                               "pnl": 5.0, "duplicate_of": None, "fee_contaminated": False})
        for _ in range(5):
            positions.append({"fee_net_edge": 0.05, "outcome": "LOSS",
                               "direction": "YES", "game_date": "2026-04-01",
                               "pnl": -5.0, "duplicate_of": None, "fee_contaminated": False})
        for _ in range(5):
            positions.append({"fee_net_edge": -0.05, "outcome": "WIN",
                               "direction": "YES", "game_date": "2026-04-01",
                               "pnl": 5.0, "duplicate_of": None, "fee_contaminated": False})
        for _ in range(25):
            positions.append({"fee_net_edge": -0.05, "outcome": "LOSS",
                               "direction": "YES", "game_date": "2026-04-01",
                               "pnl": -5.0, "duplicate_of": None, "fee_contaminated": False})
        portfolio_path = tmp_path / "test_portfolio.json"
        portfolio_path.write_text(json.dumps({
            "bankroll_usd": 1000.0, "closed_positions": positions
        }))
        rc = main(["--portfolio", str(portfolio_path), "--ci"])
        assert rc == 0

    def test_ci_mode_insufficient_exits_3(self, tmp_path):
        positions = [
            {"fee_net_edge": 0.05, "outcome": "WIN", "direction": "YES",
             "game_date": "2026-04-01", "pnl": 5.0, "duplicate_of": None,
             "fee_contaminated": False}
        ]
        portfolio_path = tmp_path / "test_portfolio.json"
        portfolio_path.write_text(json.dumps({
            "bankroll_usd": 1000.0, "closed_positions": positions
        }))
        rc = main(["--portfolio", str(portfolio_path), "--ci"])
        assert rc == 3
