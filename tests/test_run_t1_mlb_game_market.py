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
import json
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
from prediction_market_bot.c4_risk_engine.risk import RiskEngine  # noqa: E402
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


# ── GG-282/T-551: min_bet_usd floor fix (Deliverable 3) ────────────────────
#
# Mirrors tests/test_run_t1_nfl_game_market.py's analogous pair exactly (this
# suite is a port, not an invention). The RiskEngine construction in main()
# previously omitted min_bet_usd, inheriting the live MIN_BET_USD=10.0 floor
# (risk.py) against this script's $1.00 ADR-0050 flat measurement stake
# (T1_MEASUREMENT_STAKE_USD) -- every approval-path evaluation was
# structurally guaranteed to be rejected "min_bet_floor". Two tests: (1) the
# fix (min_bet_usd=1.0, matching main()'s actual construction) lets a $1.00
# measurement stake clear end-to-end, and (2) the live floor (no override --
# the global MIN_BET_USD default) still refuses a $1.00 stake
# "min_bet_floor", proving this fix does not touch the live floor itself
# (Hard Rule: DO NOT change MIN_BET_USD).


def test_fixed_measurement_stake_not_refused_with_paper_floor_override(tmp_path):
    """Mirrors main()'s actual RiskEngine construction (min_bet_usd=1.0).
    A $1.00 ADR-0050 measurement stake must clear the risk gate end-to-end
    (outcome OPENED), not be rejected "min_bet_floor"."""
    audit = AuditLogger(tmp_path / "audit_floor_fix_test.jsonl")
    engine = RiskEngine(
        logger=audit, snapshot_id="SNAP-TEST-FLOOR-FIX", bankroll=1000.0,
        min_bet_usd=1.0,  # matches main()'s post-fix construction verbatim
    )
    trader = PaperTrader(portfolio_path=tmp_path / "paper_portfolio_floor_fix_test.json", logger=audit)
    mkt = _make_market()

    outcome = evaluate_and_maybe_trade(
        mkt,
        snapshot_unparsed_count=0,
        # fixed_p=0.65 -> edge = 0.65-0.56 = 0.09, comfortably above both this
        # script's EDGE_THRESHOLD and RiskEngine's own MIN_EDGE gate -- the
        # point of this test is the min_bet_floor fix, not the edge gate, so
        # the edge margin is deliberately generous.
        model=StubMLBGameMarketForecastModel(fixed_p=0.65),
        engine=engine,
        trader=trader,
        audit=audit,
    )
    assert outcome == "OPENED"


def test_fixed_measurement_stake_still_refused_min_bet_floor_on_live_default(tmp_path):
    """Without the min_bet_usd override -- i.e. RiskEngine's live default --
    the same $1.00 flat measurement stake must still be refused
    "min_bet_floor". Proves the fix is a paper-mode override, not a change
    to the live MIN_BET_USD floor itself (Hard Rule: DO NOT change
    MIN_BET_USD)."""
    audit = AuditLogger(tmp_path / "audit_live_floor_test.jsonl")
    engine = RiskEngine(
        logger=audit, snapshot_id="SNAP-TEST-LIVE-FLOOR", bankroll=1000.0,
        # no min_bet_usd override -- inherits the live MIN_BET_USD=10.0 floor
    )
    forecast_record = {
        "forecast_id": "FCST-TEST-FLOOR-LIVE",
        "p_estimate": 0.65,
        "market_implied_prob": 0.56,
        "edge": 0.09,  # comfortably above RiskEngine's own MIN_EDGE gate
        "recommended_direction": "YES",
    }
    ok, approval = engine.evaluate_forecast(
        forecast_record=forecast_record,
        session_id="TEST-LIVE-FLOOR",
        pool_isolated=True,
        fixed_stake_usd=1.00,  # same $1.00 ADR-0050 flat measurement stake
    )
    assert ok
    assert approval.get("approval_status") != "APPROVED"
    assert approval.get("rejection_reason") == "min_bet_floor"


# ── GG-291: kalshi_threshold write-path fix ────────────────────────────────
#
# Mirrors tests/test_run_t1_nfl_game_market.py's analogous three tests
# exactly (this suite is a port, not an invention). 42 real T1 NFL moneyline
# positions were opened with kalshi_threshold=null because open_position()
# was never passed the argument. This script (run_t1_mlb_game_market.py) is
# dark/unused in production (no cron entry, isolated from the two live MLB
# ledgers -- see test_never_opens_live_mlb_portfolio_files above) but shares
# the identical open_position() call-site defect, so it received the
# identical fix: derive_kalshi_threshold() at the call site, refusing
# (REFUSED_NO_THRESHOLD) rather than writing null. MLB's own
# _GAME_MARKET_TYPE_MAP additionally maps "partial_game" (KXMLBF3/F5/F7),
# which -- like moneyline -- legitimately has threshold=None and must
# resolve to 0.0, not refuse.


def test_moneyline_position_carries_zero_threshold(tmp_path):
    audit = AuditLogger(tmp_path / "audit_gg291_moneyline_test.jsonl")
    engine = RiskEngine(
        logger=audit, snapshot_id="SNAP-TEST-GG291-ML", bankroll=1000.0,
        min_bet_usd=1.0,
    )
    trader = PaperTrader(
        portfolio_path=tmp_path / "paper_portfolio_gg291_ml_test.json", logger=audit,
    )
    mkt = _make_market()  # defaults: market_type="moneyline", threshold=None

    outcome = evaluate_and_maybe_trade(
        mkt,
        snapshot_unparsed_count=0,
        model=StubMLBGameMarketForecastModel(fixed_p=0.65),
        engine=engine,
        trader=trader,
        audit=audit,
    )
    assert outcome == "OPENED"

    on_disk = json.loads(trader._path.read_text())
    pos = next(p for p in on_disk["open_positions"] if p["kalshi_ticker"] == mkt.ticker)
    assert pos["kalshi_threshold"] == 0.0
    assert isinstance(pos["kalshi_threshold"], float)


def test_run_line_position_carries_real_floor_strike(tmp_path):
    """MLB's spread-equivalent (run_line) must carry GameMarket.threshold
    verbatim and unrounded -- never 0.0, never re-derived from the ticker's
    strike-suffix digits."""
    audit = AuditLogger(tmp_path / "audit_gg291_runline_test.jsonl")
    engine = RiskEngine(
        logger=audit, snapshot_id="SNAP-TEST-GG291-RUNLINE", bankroll=1000.0,
        min_bet_usd=1.0,
    )
    trader = PaperTrader(
        portfolio_path=tmp_path / "paper_portfolio_gg291_runline_test.json", logger=audit,
    )
    mkt = _make_market(
        ticker="KXMLBSPREAD-26SEP08NYY-NYY15",
        market_type="run_line",
        threshold=1.5,
    )

    outcome = evaluate_and_maybe_trade(
        mkt,
        snapshot_unparsed_count=0,
        model=StubMLBGameMarketForecastModel(fixed_p=0.65),
        engine=engine,
        trader=trader,
        audit=audit,
    )
    assert outcome == "OPENED"

    on_disk = json.loads(trader._path.read_text())
    pos = next(p for p in on_disk["open_positions"] if p["kalshi_ticker"] == mkt.ticker)
    assert pos["kalshi_threshold"] == 1.5
    assert isinstance(pos["kalshi_threshold"], float)


def test_partial_game_position_carries_zero_threshold(tmp_path):
    """MLB's partial_game (KXMLBF3/F5/F7) is the second market_type -- along
    with moneyline -- where GameMarket.threshold is legitimately None; must
    resolve to 0.0, not refuse."""
    audit = AuditLogger(tmp_path / "audit_gg291_partialgame_test.jsonl")
    engine = RiskEngine(
        logger=audit, snapshot_id="SNAP-TEST-GG291-PARTIAL", bankroll=1000.0,
        min_bet_usd=1.0,
    )
    trader = PaperTrader(
        portfolio_path=tmp_path / "paper_portfolio_gg291_partial_test.json", logger=audit,
    )
    mkt = _make_market(
        ticker="KXMLBF5-26SEP08NYY-NYY",
        market_type="partial_game",
        threshold=None,
    )

    outcome = evaluate_and_maybe_trade(
        mkt,
        snapshot_unparsed_count=0,
        model=StubMLBGameMarketForecastModel(fixed_p=0.65),
        engine=engine,
        trader=trader,
        audit=audit,
    )
    assert outcome == "OPENED"

    on_disk = json.loads(trader._path.read_text())
    pos = next(p for p in on_disk["open_positions"] if p["kalshi_ticker"] == mkt.ticker)
    assert pos["kalshi_threshold"] == 0.0
    assert isinstance(pos["kalshi_threshold"], float)


def test_refuses_when_no_derivable_threshold(tmp_path):
    """Defensive path: real Kalshi run_line markets always carry a
    floor_strike, so this shape should not occur against live data -- but if
    it ever does, derive_kalshi_threshold() must raise and the run script
    must refuse (REFUSED_NO_THRESHOLD) rather than write a null threshold
    into a settleable position (the exact GG-291 defect). No position may be
    written to disk."""
    audit = AuditLogger(tmp_path / "audit_gg291_norefuse_test.jsonl")
    engine = RiskEngine(
        logger=audit, snapshot_id="SNAP-TEST-GG291-NOTHRESH", bankroll=1000.0,
        min_bet_usd=1.0,
    )
    trader = PaperTrader(
        portfolio_path=tmp_path / "paper_portfolio_gg291_nothresh_test.json", logger=audit,
    )
    mkt = _make_market(
        ticker="KXMLBSPREAD-26SEP08NYY-NYY15",
        market_type="run_line",
        threshold=None,
    )

    outcome = evaluate_and_maybe_trade(
        mkt,
        snapshot_unparsed_count=0,
        model=StubMLBGameMarketForecastModel(fixed_p=0.65),
        engine=engine,
        trader=trader,
        audit=audit,
    )
    assert outcome == "REFUSED_NO_THRESHOLD"

    if trader._path.exists():
        on_disk = json.loads(trader._path.read_text())
        assert on_disk.get("open_positions", []) == []
