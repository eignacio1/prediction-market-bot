"""GG-255/T-536: refusal-path tests for run_t1_mlb_game_market.py (MLB half
of GG-255, mirroring T-530's NFL precedent, test_run_t1_nfl_game_market.py).

Covers the four required refusal paths for the new T1 MLB game-market run
script (paper-only; see the module docstring in
src/prediction_market_bot/run_t1_mlb_game_market.py for full pipeline
context): cell-tier kill switch active, no model available, unparsed
markets present in the fetch snapshot, and ambiguous settlement. Plus a
fifth test unique to this session's task brief (no NFL precedent): the
script must never open a handle to the live MLB ledgers
(paper_portfolio_mlb.json / paper_portfolio_mlb_t4.json). A happy-path-only
suite is not acceptable per this session's task brief -- every test here
exercises a refusal, not a fill.

Settlement-ambiguity test note: game_market_settlement.py is read-only this
session (concurrency fence) and its _SUPPORTED_MARKET_TYPES covers only the
four NFL game-market types -- zero MLB market types are supported. The
correct, honest test for MLB is therefore not a fabricated ambiguity check;
it is an assertion that the module's existing fail-loud behavior holds for
an unsupported MLB type: check_settlement_ambiguity(MLB_MONEYLINE, ...)
raises ValueError, not SettlementAmbiguityError. This locks in the current
correct refusal and documents the gap (registered separately in
GOVERNANCE_GAP_LOG.md -- MLB game-market settlement derivation is entirely
unimplemented) rather than papering over it.
"""
from __future__ import annotations

import ast
import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

os.environ["BOT_ENV"] = "paper"

from prediction_market_bot.c5_execution.kalshi_client import GameMarket  # noqa: E402
from prediction_market_bot.c5_execution.game_market_settlement import (  # noqa: E402
    check_settlement_ambiguity,
)
from prediction_market_bot.c5_execution.market_type_registry import (  # noqa: E402
    MarketType,
    _CELL_KILL_SWITCH_STATE,
    halt_cell,
)
from prediction_market_bot.execution_bands import ExecutionBand  # noqa: E402
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402
from prediction_market_bot.run_t1_mlb_game_market import (  # noqa: E402
    PORTFOLIO_PATH,
    StubMLBForecastModel,
    evaluate_and_maybe_trade,
)


def _make_market(**overrides) -> GameMarket:
    defaults = dict(
        ticker="KXMLBGAME-26SEP08NYY-NYY",
        title="Yankees vs. Red Sox — Yankees win",
        market_type="moneyline",
        team_abbr="NYY",
        threshold=None,
        outcome_desc="NYY wins",
        game_date="2026-09-08",
        event_ticker="KXMLBGAME-26SEP08NYY",
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
        MarketType.MLB_MONEYLINE, ExecutionBand.T1_MULTI_DAY,
        reason="test: forced halt for refusal-path coverage",
    )
    try:
        outcome = evaluate_and_maybe_trade(
            mkt,
            snapshot_unparsed_count=0,
            model=StubMLBForecastModel(fixed_p=0.60),
            engine=None,
            trader=None,
            audit=audit,
        )
        assert outcome == "REFUSED_KILL_SWITCH"
    finally:
        # Module-level state persists across tests -- restore so this test
        # doesn't leak a HALTED cell into any other test in the suite.
        _CELL_KILL_SWITCH_STATE.pop((MarketType.MLB_MONEYLINE, ExecutionBand.T1_MULTI_DAY), None)


# ── refusal path 2: no model available ─────────────────────────────────────

def test_refuses_when_no_model_prediction(audit):
    mkt = _make_market()
    outcome = evaluate_and_maybe_trade(
        mkt,
        snapshot_unparsed_count=0,
        model=StubMLBForecastModel(fixed_p=None),
        engine=None,
        trader=None,
        audit=audit,
    )
    assert outcome == "REFUSED_NO_MODEL"


# ── refusal path 3: market unparsed present in snapshot ────────────────────

def test_refuses_when_snapshot_has_unparsed_markets(audit):
    mkt = _make_market()
    outcome = evaluate_and_maybe_trade(
        mkt,
        snapshot_unparsed_count=1,
        model=StubMLBForecastModel(fixed_p=0.60),
        engine=None,
        trader=None,
        audit=audit,
    )
    assert outcome == "REFUSED_UNPARSED"


# ── refusal path 4: settlement ambiguity -- MLB has no supported market
#    types in game_market_settlement.py (read-only this session; see module
#    docstring above and GOVERNANCE_GAP_LOG.md) ─────────────────────────────

def test_check_settlement_ambiguity_raises_value_error_for_unsupported_mlb_type():
    with pytest.raises(ValueError):
        check_settlement_ambiguity(MarketType.MLB_MONEYLINE, actual_stat=0, threshold=0)


# ── no-shared-ledger test (GG-255 Deliverable 1 constraint; no NFL
#    precedent -- unique to this session's task brief) ─────────────────────

def test_never_references_live_mlb_ledger_files():
    """The MLB game-market script must never open/write/lock the live T1
    prop ledger (paper_portfolio_mlb.json) or the live T4 ledger
    (paper_portfolio_mlb_t4.json). Verified two ways: (1) this script's own
    configured PORTFOLIO_PATH constant is the isolated T1-game-market file,
    not either live ledger; (2) neither forbidden filename appears as a
    string-literal constant anywhere in the script's *code* (module
    docstring excluded -- the docstring names both forbidden files in prose
    to document this very constraint, which is not a code reference and
    must not fail this check), so no other code path in the file could open
    them either.
    """
    assert PORTFOLIO_PATH.name == "paper_portfolio_t1_mlb_game_market.json"
    assert PORTFOLIO_PATH.name not in (
        "paper_portfolio_mlb.json", "paper_portfolio_mlb_t4.json",
    )

    script_path = _REPO_ROOT / "src" / "prediction_market_bot" / "run_t1_mlb_game_market.py"
    source = script_path.read_text()
    tree = ast.parse(source)

    module_docstring = ast.get_docstring(tree, clean=False)
    forbidden = {"paper_portfolio_mlb.json", "paper_portfolio_mlb_t4.json"}

    code_string_constants = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and node.value != module_docstring
    }
    assert not (forbidden & code_string_constants), (
        f"forbidden ledger filename found as a code string literal: "
        f"{forbidden & code_string_constants}"
    )
