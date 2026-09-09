"""GG-255/T-530: refusal-path tests for run_t1_nfl_game_market.py.

Covers the four required refusal paths for the new T1 NFL game-market run
script (paper-only; see the module docstring in
src/prediction_market_bot/run_t1_nfl_game_market.py for full pipeline
context): cell-tier kill switch active, no model available, unparsed
markets present in the fetch snapshot (GG-252), and ambiguous settlement on
an exact-tie NFL moneyline (GG-257). A happy-path-only suite is not
acceptable per this session's task brief -- every test here exercises a
refusal, not a fill.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

os.environ["BOT_ENV"] = "paper"

from prediction_market_bot.c5_execution.kalshi_client import GameMarket  # noqa: E402
from prediction_market_bot.c5_execution.game_market_settlement import (  # noqa: E402
    SettlementAmbiguityError,
    check_settlement_ambiguity,
)
from prediction_market_bot.c5_execution.market_type_registry import (  # noqa: E402
    MarketType,
    _CELL_KILL_SWITCH_STATE,
    halt_cell,
)
from prediction_market_bot.execution_bands import ExecutionBand  # noqa: E402
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402
from prediction_market_bot.run_t1_nfl_game_market import (  # noqa: E402
    StubNFLForecastModel,
    evaluate_and_maybe_trade,
)


def _make_market(**overrides) -> GameMarket:
    defaults = dict(
        ticker="KXNFLGAME-26SEP08DEN-DEN",
        title="Broncos vs. Raiders — Broncos win",
        market_type="moneyline",
        team_abbr="DEN",
        threshold=None,
        outcome_desc="DEN wins",
        game_date="2026-09-08",
        event_ticker="KXNFLGAME-26SEP08DEN",
        yes_ask=0.58,
        yes_bid=0.54,
        no_ask=0.46,
        no_bid=0.42,
        mid_price=0.56,
        vig=0.04,
        volume=1000.0,
        status="active",
        fetched_at="2026-09-08T12:00:00Z",
    )
    defaults.update(overrides)
    return GameMarket(**defaults)


@pytest.fixture
def audit(tmp_path) -> AuditLogger:
    return AuditLogger(tmp_path / "audit_test.jsonl")


# ── refusal path 1: cell-tier kill switch active (GG-255 Deliverable 3) ───

def test_refuses_when_cell_kill_switch_halted(audit):
    mkt = _make_market()
    halt_cell(
        MarketType.NFL_MONEYLINE, ExecutionBand.T1_MULTI_DAY,
        reason="test: forced halt for refusal-path coverage",
    )
    try:
        outcome = evaluate_and_maybe_trade(
            mkt,
            snapshot_unparsed_count=0,
            model=StubNFLForecastModel(fixed_p=0.60),
            engine=None,
            trader=None,
            audit=audit,
        )
        assert outcome == "REFUSED_KILL_SWITCH"
    finally:
        # Module-level state persists across tests -- restore so this test
        # doesn't leak a HALTED cell into any other test in the suite.
        _CELL_KILL_SWITCH_STATE.pop((MarketType.NFL_MONEYLINE, ExecutionBand.T1_MULTI_DAY), None)


# ── refusal path 2: no model available ─────────────────────────────────────

def test_refuses_when_no_model_prediction(audit):
    mkt = _make_market()
    outcome = evaluate_and_maybe_trade(
        mkt,
        snapshot_unparsed_count=0,
        model=StubNFLForecastModel(fixed_p=None),
        engine=None,
        trader=None,
        audit=audit,
    )
    assert outcome == "REFUSED_NO_MODEL"


# ── refusal path 3: market unparsed present in snapshot (GG-252) ──────────

def test_refuses_when_snapshot_has_unparsed_markets(audit):
    mkt = _make_market()
    outcome = evaluate_and_maybe_trade(
        mkt,
        snapshot_unparsed_count=1,
        model=StubNFLForecastModel(fixed_p=0.60),
        engine=None,
        trader=None,
        audit=audit,
    )
    assert outcome == "REFUSED_UNPARSED"


# ── refusal path 4: ambiguous settlement, exact-tie NFL moneyline (GG-257) ─

def test_check_settlement_ambiguity_raises_on_exact_tie_moneyline():
    with pytest.raises(SettlementAmbiguityError):
        check_settlement_ambiguity(MarketType.NFL_MONEYLINE, actual_stat=0, threshold=0)
