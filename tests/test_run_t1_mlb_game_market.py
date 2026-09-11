"""GG-255/T-538: refusal-path tests for run_t1_mlb_game_market.py.

Mirrors tests/test_run_t1_nfl_game_market.py's structure exactly (this
suite is a port, not an invention) for the five MLB game-market cells:
cell-tier kill switch active, no model available, unparsed markets present
in the fetch snapshot (GG-252/GG-255), and settlement ambiguity. Plus a
fifth test specific to this task's GG-255 DO NOT constraint: the script
must never open, write, or lock paper_portfolio_mlb.json or
paper_portfolio_mlb_t4.json -- the two live MLB paper-trading ledgers
(T1 sameday and T4M-PROJ respectively), which are in active use. A
happy-path-only suite is not acceptable per this session's task brief --
every test here exercises a refusal, not a fill.

Settlement-ambiguity note: game_market_settlement.py's
_SUPPORTED_MARKET_TYPES is NFL-only (NFL_MONEYLINE/NFL_SPREAD/
NFL_GAME_TOTAL/NFL_TEAM_TOTAL) and that file is explicitly out of scope for
this task (DO NOT list: must not modify settle_position() or
game_market_settlement.py). MLB's partial-game markets (KXMLBF3/F5/F7)
carry a real three-way TIE outcome, distinct from NFL's tie-as-50/50-split
semantics -- this module does not implement MLB settlement at all yet. The
correct refusal-path test for this session's scope is therefore that
check_settlement_ambiguity() refuses cleanly (ValueError) for an MLB
market_type rather than silently applying NFL settlement logic to it.
"""
from __future__ import annotations

import builtins
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
from prediction_market_bot.c5_execution.paper_trader import PaperTrader  # noqa: E402
from prediction_market_bot.execution_bands import ExecutionBand  # noqa: E402
from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger  # noqa: E402
from prediction_market_bot import run_t1_mlb_game_market as m  # noqa: E402
from prediction_market_bot.run_t1_mlb_game_market import (  # noqa: E402
    StubMLBGameMarketForecastModel,
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
            model=StubMLBGameMarketForecastModel(fixed_p=0.60),
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
        model=StubMLBGameMarketForecastModel(fixed_p=None),
        engine=None,
        trader=None,
        audit=audit,
    )
    assert outcome == "REFUSED_NO_MODEL"


# ── refusal path 3: market unparsed present in snapshot (GG-252/GG-255) ───

def test_refuses_when_snapshot_has_unparsed_markets(audit):
    mkt = _make_market()
    outcome = evaluate_and_maybe_trade(
        mkt,
        snapshot_unparsed_count=1,
        model=StubMLBGameMarketForecastModel(fixed_p=0.60),
        engine=None,
        trader=None,
        audit=audit,
    )
    assert outcome == "REFUSED_UNPARSED"


# ── refusal path 4: settlement ambiguity -- MLB not wired into
#    game_market_settlement.py, which must refuse rather than guess ───────

def test_check_settlement_ambiguity_refuses_unsupported_mlb_market_type():
    with pytest.raises(ValueError, match="unsupported market_type"):
        check_settlement_ambiguity(MarketType.MLB_MONEYLINE, actual_stat=0, threshold=0)


# ── refusal path 5 (GG-255 DO NOT constraint, MLB-specific addition) ──────
# This script must never open, write, or lock either live MLB ledger.

def test_never_opens_live_mlb_portfolio_files(tmp_path, monkeypatch):
    forbidden = {"paper_portfolio_mlb.json", "paper_portfolio_mlb_t4.json"}
    real_open = builtins.open

    def guarded_open(file, *args, **kwargs):
        try:
            name = Path(file).name
        except TypeError:
            name = ""
        assert name not in forbidden, f"opened forbidden live ledger file: {file}"
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", guarded_open)

    # Module-level constant check: this script's own PORTFOLIO_PATH must
    # never be named after either live ledger.
    assert m.PORTFOLIO_PATH.name not in forbidden
    assert m.AUDIT_LOG_PATH.name not in forbidden

    # Behavioral check: actually exercise the same PaperTrader construction
    # main() performs (with the guard active throughout), redirected into
    # tmp_path so this test never touches real logs/ at all.
    trader = PaperTrader(
        portfolio_path=tmp_path / "paper_portfolio_t1_mlb_game_market.json",
        logger=AuditLogger(tmp_path / "audit_test.jsonl"),
        kalshi_client=None,
    )
    assert trader is not None
