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
    UNKNOWN_MODEL_IDENTITY,
    StubNFLForecastModel,
    _resolve_model_identity,
    evaluate_and_maybe_trade,
    model_identity_of_position,
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


# ── GG-267: per-row model-identity field ───────────────────────────────────
#
# Deliverable 3's three required proofs:
#   (a) a stub-produced row and an LR-produced row are distinguishable on disk
#   (b) a legacy row with no field loads and reads UNKNOWN
#   (c) no code path can write a row with the field absent or empty


class _NoIdentityModel:
    """A model with no PROVENANCE attribute at all -- must resolve UNKNOWN."""

    def predict_proba(self, market, features):
        return 0.5


class _BlankIdentityModel:
    """A model whose PROVENANCE is present but empty -- must resolve UNKNOWN,
    not the empty string (an empty PROVENANCE is not a valid identity)."""

    PROVENANCE = ""

    def predict_proba(self, market, features):
        return 0.5


def test_resolve_model_identity_stub_is_explicit_and_not_unknown():
    identity = _resolve_model_identity(StubNFLForecastModel(fixed_p=0.6))
    assert identity == StubNFLForecastModel.PROVENANCE
    assert identity != UNKNOWN_MODEL_IDENTITY
    assert "STUB" in identity


def test_resolve_model_identity_never_returns_none_or_empty():
    # (c) -- every model, including pathological ones, resolves to a
    # non-empty string. This is the structural guarantee that no code path
    # downstream (audit payload, forecast_id, position row) can end up with
    # an absent or blank model_identity.
    for model in (_NoIdentityModel(), _BlankIdentityModel()):
        identity = _resolve_model_identity(model)
        assert identity == UNKNOWN_MODEL_IDENTITY
        assert identity  # never "", never None


def test_model_identity_of_position_backward_compatible():
    # (b) -- a legacy row written before GG-267 has no key at all.
    legacy_row = {"position_id": "POS-LEGACY01", "status": "OPEN"}
    assert model_identity_of_position(legacy_row) == UNKNOWN_MODEL_IDENTITY

    # A row with the key present but explicitly blank must also read UNKNOWN
    # -- .get(key) or UNKNOWN, not .get(key, UNKNOWN), is required for this.
    blank_row = {"model_identity": "", "status": "OPEN"}
    assert model_identity_of_position(blank_row) == UNKNOWN_MODEL_IDENTITY

    real_row = {"model_identity": "EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)"}
    assert model_identity_of_position(real_row) == real_row["model_identity"]


def test_stub_and_lr_rows_distinguishable_on_disk(tmp_path):
    # (a) -- exercise the real, on-disk PaperTrader position row (not a
    # mock), proving the field written by paper_trader.py's open_position()
    # actually differs between a stub-sourced approval and an
    # LR-identity-sourced approval, and that a caller supplying neither
    # lands on the same explicit UNKNOWN a legacy row would read.
    audit = AuditLogger(tmp_path / "audit.jsonl")
    trader = PaperTrader(
        portfolio_path=tmp_path / "portfolio.json", logger=audit, kalshi_client=None,
    )

    base_approval = {
        "approved_size": 10.0,
        "approved_direction": "YES",
        "risk_eval_id": "RISK-1",
        "forecast_id": "FC-1",
        "band": "T1_MULTI_DAY",
        "model_p": 0.6,
        "gross_edge": 0.04,
    }

    ok_stub, pos_stub = trader.open_position(
        approval={**base_approval, "model_identity": StubNFLForecastModel.PROVENANCE},
        kalshi_ticker="KXNFLGAME-26SEP08DEN-DEN",
        mid_price=0.56, vig=0.04, game_date="2026-09-08",
        pool_isolated=True,
    )
    assert ok_stub
    assert pos_stub["model_identity"] == StubNFLForecastModel.PROVENANCE

    lr_identity = "EXP-027 LR (T-531, HYP-012, verdict UNDERPOWERED)"
    ok_lr, pos_lr = trader.open_position(
        approval={**base_approval, "forecast_id": "FC-2", "model_identity": lr_identity},
        kalshi_ticker="KXNFLGAME-26SEP08DEN-DEN",
        mid_price=0.56, vig=0.04, game_date="2026-09-08",
        pool_isolated=True,
    )
    assert ok_lr
    assert pos_lr["model_identity"] == lr_identity
    assert pos_lr["model_identity"] != pos_stub["model_identity"]

    # A caller that never resolves/sets model_identity at all (every
    # pre-existing MLB/NBA call site) must not silently inherit either
    # model's label -- it reads the explicit UNKNOWN marker.
    ok_bare, pos_bare = trader.open_position(
        approval={**base_approval, "forecast_id": "FC-3"},
        kalshi_ticker="KXNFLGAME-26SEP08DEN-DEN",
        mid_price=0.56, vig=0.04, game_date="2026-09-08",
        pool_isolated=True,
    )
    assert ok_bare
    assert pos_bare["model_identity"] == UNKNOWN_MODEL_IDENTITY

    # Re-read straight off disk (not the in-memory return value) -- proves
    # the field is actually persisted, not just present on the returned dict.
    on_disk = json.loads((tmp_path / "portfolio.json").read_text())
    disk_identities = {p["forecast_id"]: p["model_identity"] for p in on_disk["open_positions"]}
    assert disk_identities["FC-1"] == StubNFLForecastModel.PROVENANCE
    assert disk_identities["FC-2"] == lr_identity
    assert disk_identities["FC-3"] == UNKNOWN_MODEL_IDENTITY
