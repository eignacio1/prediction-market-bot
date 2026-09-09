"""Tests for T-531/GG-258: EXP-027/HYP-012 NFL moneyline LR backtest script.

Coverage:
  - KXNFLGAME ticker parsing (parse_event_teams / parse_event_date) --
    reimplemented locally from scripts/apply_resolved_nfl_game_markets.py's
    algorithm, so its correctness must be verified independently here.
  - Kalshi-vs-nflverse team-code translation (_translate).
  - Primary-gate arithmetic (compute_primary_gate) on small synthetic
    inputs -- pay-the-ask/pay-the-bid fill-cost convention, edge-threshold
    bet selection, per-game aggregation, UNDERPOWERED-when-insufficient-n
    verdict logic.

No live HTTP calls, no dependency on the real KXNFLGAME price archive or a
fitted model -- compute_primary_gate is exercised with a stub model object.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "scripts" / "exp027_hyp012_nfl_moneyline_backtest.py"
_spec = importlib.util.spec_from_file_location("exp027_hyp012_nfl_moneyline_backtest", SCRIPT_PATH)
exp027 = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = exp027
_spec.loader.exec_module(exp027)


# ---------------------------------------------------------------------------
# Ticker parsing
# ---------------------------------------------------------------------------

def test_parse_event_teams_finds_known_pair():
    assert exp027.parse_event_teams("26SEP21NYGLAR") == ("NYG", "LAR")


def test_parse_event_teams_returns_none_for_unknown_codes():
    assert exp027.parse_event_teams("26SEP21ZZZQQQ") is None


def test_parse_event_teams_handles_three_letter_both_sides():
    assert exp027.parse_event_teams("26SEP07KCLAC") == ("KC", "LAC")


def test_parse_event_date_roundtrip():
    d = exp027.parse_event_date("26SEP21")
    assert (d.year, d.month, d.day) == (2026, 9, 21)


# ---------------------------------------------------------------------------
# Team-code translation
# ---------------------------------------------------------------------------

def test_translate_maps_kalshi_codes_to_nflverse():
    assert exp027._translate("LAR") == "LA"
    assert exp027._translate("WSH") == "WAS"


def test_translate_is_identity_for_unmapped_codes():
    assert exp027._translate("KC") == "KC"
    assert exp027._translate("BUF") == "BUF"


# ---------------------------------------------------------------------------
# Primary gate arithmetic
# ---------------------------------------------------------------------------

def _stub_model(probs: list[float]) -> MagicMock:
    """Returns a model whose predict_proba yields successive probs on each call."""
    model = MagicMock()
    it = iter(probs)

    def _predict_proba(X):
        p = next(it)
        return np.array([[1 - p, p]])

    model.predict_proba.side_effect = _predict_proba
    return model


def _resolved_row(game_id: str, label: int) -> dict:
    return {
        "game_id": game_id,
        **{f: 0.0 for f in exp027.FEATURES},
        "label": label,
    }


def test_gate_underpowered_with_few_games():
    # Two qualifying bets, both winners -- clean_n=2 is nowhere near n* at
    # realistic variance, so the verdict must be UNDERPOWERED, not PASS.
    prospective = pd.DataFrame([_resolved_row("g1", 1), _resolved_row("g2", 1)])
    model = _stub_model([0.70, 0.70])  # edge = 0.70-0.30=0.40 > EDGE_THRESHOLD
    market_rows = [
        {"event_ticker": "g1", "game_id": "g1", "yes_mid_home": 0.30, "half_spread": 0.01},
        {"event_ticker": "g2", "game_id": "g2", "yes_mid_home": 0.30, "half_spread": 0.01},
    ]
    result = exp027.compute_primary_gate(model, prospective, market_rows)
    assert result["clean_n_games"] == 2
    assert result["verdict"] == "UNDERPOWERED"


def test_gate_skips_games_below_edge_threshold():
    prospective = pd.DataFrame([_resolved_row("g1", 1)])
    model = _stub_model([0.505])  # edge = 0.005 < EDGE_THRESHOLD (0.010)
    market_rows = [{"event_ticker": "g1", "game_id": "g1", "yes_mid_home": 0.50, "half_spread": 0.01}]
    result = exp027.compute_primary_gate(model, prospective, market_rows)
    assert result["qualifying_bets_row_level"] == 0
    assert result["clean_n_games"] == 0
    assert result["verdict"] == "UNDERPOWERED"


def test_gate_net_pnl_subtracts_half_spread():
    # model_p=0.80 > yes_mid=0.50 -> bet YES; home wins (label=1) -> gross = 1-0.50 = 0.50
    # net = 0.50 - half_spread(0.02) = 0.48
    prospective = pd.DataFrame([_resolved_row("g1", 1)])
    model = _stub_model([0.80])
    market_rows = [{"event_ticker": "g1", "game_id": "g1", "yes_mid_home": 0.50, "half_spread": 0.02}]
    result = exp027.compute_primary_gate(model, prospective, market_rows)
    assert result["mean_pnl_per_bet_net_of_fill_cost_game_level"] == pytest.approx(0.48)


def test_gate_no_side_bet_and_fill_cost():
    # model_p=0.20 < yes_mid=0.60 -> bet NO; home wins (label=1) so NO loses:
    # gross = (1-label) - no_mid = 0 - 0.40 = -0.40; net = -0.40 - half_spread(0.01) = -0.41
    prospective = pd.DataFrame([_resolved_row("g1", 1)])
    model = _stub_model([0.20])
    market_rows = [{"event_ticker": "g1", "game_id": "g1", "yes_mid_home": 0.60, "half_spread": 0.01}]
    result = exp027.compute_primary_gate(model, prospective, market_rows)
    assert result["mean_pnl_per_bet_net_of_fill_cost_game_level"] == pytest.approx(-0.41)


def test_gate_reports_brier_vs_market_for_all_resolved_games_regardless_of_edge_filter():
    # Both games resolved & matched, but only one qualifies as a bet --
    # model_brier_vs_market must still cover both (it is descriptive, not gated).
    prospective = pd.DataFrame([_resolved_row("g1", 1), _resolved_row("g2", 0)])
    model = _stub_model([0.505, 0.10])  # g1: edge=0.005 (skipped); g2: edge=-0.40 (bet)
    market_rows = [
        {"event_ticker": "g1", "game_id": "g1", "yes_mid_home": 0.50, "half_spread": 0.01},
        {"event_ticker": "g2", "game_id": "g2", "yes_mid_home": 0.50, "half_spread": 0.01},
    ]
    result = exp027.compute_primary_gate(model, prospective, market_rows)
    assert result["n_scored_vs_market"] == 2
    assert result["qualifying_bets_row_level"] == 1
