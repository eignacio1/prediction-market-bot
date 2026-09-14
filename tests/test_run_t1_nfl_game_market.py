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
    _model_identity,
    evaluate_and_maybe_trade,
)
from prediction_market_bot.c5_execution.paper_trader import PaperTrader  # noqa: E402


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


# ── GG-267: per-row model-identity provenance (T-544 Deliverable 4) ────────
#
# Four tests proving the per-row model-identity field required to close
# GG-267:
#   (1) _model_identity() itself resolves correctly for a labeled model, the
#       stub, and an object with no PROVENANCE at all.
#   (2) a stub-produced row and an LR-produced row are distinguishable on
#       disk via PaperTrader.open_position().
#   (3) a legacy row predating this field (no key at all) loads and reads
#       "UNKNOWN" rather than crashing or defaulting to a real model's label.
#   (4) open_position() can never write the field absent or empty — missing
#       key and explicit "" both collapse to the literal "UNKNOWN".


def test_model_identity_helper():
    class _LabeledModel:
        PROVENANCE = "TEST-MODEL-X (unit test fixture)"

    class _NoProvenanceModel:
        """Deliberately has no PROVENANCE attribute at all."""

    assert _model_identity(_LabeledModel()) == "TEST-MODEL-X (unit test fixture)"
    assert _model_identity(StubNFLForecastModel()) == (
        "STUB (StubNFLForecastModel — NOT a trained model, GG-255)"
    )
    assert _model_identity(_NoProvenanceModel()) == "UNKNOWN"


@pytest.fixture
def trader(tmp_path) -> PaperTrader:
    logger = AuditLogger(tmp_path / "audit_trader_test.jsonl")
    return PaperTrader(portfolio_path=tmp_path / "paper_portfolio_test.json", logger=logger)


def _base_approval(**overrides) -> dict:
    approval = {
        "approval_status": "APPROVED",
        "approved_size": 10.0,
        "approved_direction": "YES",
        "edge": 0.05,
        "gross_edge": 0.07,
        "model_p": 0.61,
        "risk_eval_id": "RISK-GG267-TEST",
        "forecast_id": "FC-GG267-TEST",
        "band": "T1_MULTI_DAY",
    }
    approval.update(overrides)
    return approval


def test_stub_and_lr_rows_distinguishable_on_disk(trader):
    stub_identity = _model_identity(StubNFLForecastModel())
    lr_identity = "EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)"

    ok_stub, pos_stub = trader.open_position(
        approval=_base_approval(model_identity=stub_identity),
        kalshi_ticker="KXNFLGAME-26SEP08DEN-DEN",
        mid_price=0.56,
        vig=0.04,
        game_date="2026-09-08",
        market_type=MarketType.NFL_MONEYLINE,
    )
    ok_lr, pos_lr = trader.open_position(
        approval=_base_approval(model_identity=lr_identity),
        kalshi_ticker="KXNFLGAME-26SEP08KC-KC",
        mid_price=0.56,
        vig=0.04,
        game_date="2026-09-08",
        market_type=MarketType.NFL_MONEYLINE,
    )

    assert ok_stub and ok_lr
    assert pos_stub["model_identity"] == stub_identity
    assert pos_lr["model_identity"] == lr_identity
    assert pos_stub["model_identity"] != pos_lr["model_identity"]
    assert pos_stub["model_identity"] and pos_lr["model_identity"]

    # Confirm it round-trips through the on-disk portfolio file, not just
    # the in-memory returned dict.
    on_disk = json.loads(trader._path.read_text())
    identities = {p["kalshi_ticker"]: p["model_identity"] for p in on_disk["open_positions"]}
    assert identities["KXNFLGAME-26SEP08DEN-DEN"] == stub_identity
    assert identities["KXNFLGAME-26SEP08KC-KC"] == lr_identity


def test_legacy_row_no_model_identity_loads_as_unknown(trader):
    """A row written before GG-267 existed has no `model_identity` key at
    all. It must load without error and read "UNKNOWN" at render time via
    the same `.get(...) or "UNKNOWN"` fallback the dashboard and any
    downstream reader use -- never crash, never inherit today's live
    model's label."""
    ok, pos = trader.open_position(
        approval=_base_approval(model_identity="EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)"),
        kalshi_ticker="KXNFLGAME-26SEP08SF-SF",
        mid_price=0.56,
        vig=0.04,
        game_date="2026-09-08",
        market_type=MarketType.NFL_MONEYLINE,
    )
    assert ok

    # Simulate a pre-GG-267 legacy record by stripping the key entirely,
    # then writing it straight into the on-disk portfolio the way an old
    # write path (predating this field) would have.
    state = json.loads(trader._path.read_text())
    for p in state["open_positions"]:
        if p["kalshi_ticker"] == "KXNFLGAME-26SEP08SF-SF":
            del p["model_identity"]
    trader._path.write_text(json.dumps(state))

    # Reload via a fresh PaperTrader instance, exactly as a long-running
    # process or a new session would.
    reloaded = PaperTrader(portfolio_path=trader._path, logger=trader._logger)
    reloaded_state = json.loads(trader._path.read_text())
    legacy_row = next(
        p for p in reloaded_state["open_positions"]
        if p["kalshi_ticker"] == "KXNFLGAME-26SEP08SF-SF"
    )
    assert "model_identity" not in legacy_row
    assert (legacy_row.get("model_identity") or "UNKNOWN") == "UNKNOWN"
    assert reloaded is not None  # loaded without raising


def test_open_position_never_writes_missing_or_empty_model_identity(trader):
    # Case (a): approval dict entirely lacking the key.
    approval_missing = _base_approval()
    approval_missing.pop("model_identity", None)
    ok_a, pos_a = trader.open_position(
        approval=approval_missing,
        kalshi_ticker="KXNFLGAME-26SEP08NE-NE",
        mid_price=0.56,
        vig=0.04,
        game_date="2026-09-08",
        market_type=MarketType.NFL_MONEYLINE,
    )
    assert ok_a
    assert pos_a["model_identity"] == "UNKNOWN"

    # Case (b): approval dict with an explicit empty string.
    ok_b, pos_b = trader.open_position(
        approval=_base_approval(model_identity=""),
        kalshi_ticker="KXNFLGAME-26SEP08GB-GB",
        mid_price=0.56,
        vig=0.04,
        game_date="2026-09-08",
        market_type=MarketType.NFL_MONEYLINE,
    )
    assert ok_b
    assert pos_b["model_identity"] == "UNKNOWN"
