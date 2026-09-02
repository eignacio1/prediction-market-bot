"""T-509 (ADR-0054(a) SS8 item 4, PRIORITY) -- regression coverage for
scripts/replay_harness_t427.py's market_type handling.

Before this fix, replay_one() called trader.open_position() without a
market_type= kwarg at all. open_position() silently defaults a missing
market_type to MLB_PLAYER_PROP_HITS (GG-184), so every replayed position --
regardless of what MarketType its stored record actually carried -- was
silently re-attributed to MLB_PLAYER_PROP_HITS. That is confidently wrong
output, not a visible error (ADR-0054 SS9).

test_replay_preserves_non_default_market_type is the discriminating case:
it builds a stored-position fixture with market_type=MLB_MONEYLINE (NOT the
default) and asserts the replayed record's market_type matches. Against the
pre-fix code (which never passed market_type= to open_position() at all)
this assertion fails, because the replay would have come back
MLB_PLAYER_PROP_HITS regardless of what was stored -- it does not merely
happen to pass by coincidence of a shared default.

test_resolve_market_type_rejects_missing_field and
test_resolve_market_type_rejects_unrecognized_value cover the harness-local
guard (resolve_market_type()) directly: raising loudly is the "go further"
mechanism this harness uses in place of a required open_position() kwarg,
which the SCOPE FENCE (nothing else under src/) rules out -- 6 of
open_position()'s 7 call sites live under src/.
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import replay_harness_t427 as rh  # noqa: E402
from prediction_market_bot.c5_execution.market_type_registry import MarketType  # noqa: E402


def _base_position(**overrides) -> dict:
    pos = {
        "position_id": "POS-TESTFX0001",
        "player_name": "Test Fixture Player",
        "player_id": -2000,
        "kalshi_ticker": "TEST-FIXTURE",
        "kalshi_threshold": 1,
        "direction": "NO",
        "mid_price_at_entry": 0.42,
        "vig_at_entry": 0.03,
        "size_usd": 25.0,
        "game_date": "2026-08-14",
        "entered_at": rh.pt_module._utc_now(),
        "risk_eval_id": "TEST-FIXTURE-RISK",
        "forecast_id": "TEST-FIXTURE-FORECAST",
        "band": "T1",
        "logic_epoch": rh.pt_module.CURRENT_LOGIC_EPOCH,
        "approval_commit": rh.pt_module.CURRENT_APPROVAL_COMMIT,
        "status": "OPEN",
        "pool_isolated": False,
        "kalshi_order_id": None,
        "kalshi_order_status": "local_only",
        "kalshi_contracts": None,
        "model_p": 0.43,
        "gross_edge": 0.05,
        "fee_per_contract": 0.017052,
        "fee_net_edge": -0.097052,
        "fee_contaminated": True,
        "probable_injury_signal": False,
        "t3_signal": "NEUTRAL",
        "t1_edge": 0.05,
        "h_so_far_at_entry": None,
        "ab_remaining_at_entry": None,
        "market_type": MarketType.MLB_PLAYER_PROP_HITS.value,
    }
    pos.update(overrides)
    return pos


@pytest.mark.unit
def test_replay_preserves_non_default_market_type():
    """Discriminating case: a stored record with a NON-default market_type
    must replay back with that same market_type -- not silently coerced to
    the open_position() default (MLB_PLAYER_PROP_HITS). This is exactly the
    assertion that would have failed against the pre-fix replay_one(), which
    never passed market_type= at all."""
    pos = _base_position(market_type=MarketType.MLB_MONEYLINE.value)
    with tempfile.TemporaryDirectory(prefix="t427_test_") as tmp:
        trader = rh.build_trader("test_non_default_market_type", Path(tmp))
        replayed = rh.replay_one(trader, pos)
    assert replayed["market_type"] == MarketType.MLB_MONEYLINE.value
    assert replayed["market_type"] != MarketType.MLB_PLAYER_PROP_HITS.value


@pytest.mark.unit
def test_replay_preserves_default_market_type_too():
    """Control case: the default market_type still round-trips correctly
    now that it is passed explicitly rather than falling through to
    open_position()'s own default."""
    pos = _base_position(market_type=MarketType.MLB_PLAYER_PROP_HITS.value)
    with tempfile.TemporaryDirectory(prefix="t427_test_") as tmp:
        trader = rh.build_trader("test_default_market_type", Path(tmp))
        replayed = rh.replay_one(trader, pos)
    assert replayed["market_type"] == MarketType.MLB_PLAYER_PROP_HITS.value


@pytest.mark.unit
def test_resolve_market_type_rejects_missing_field():
    """A stored record with no market_type field at all must raise, not
    silently default -- this is the GG-184 failure mode made structurally
    loud within the harness's own scope."""
    pos = _base_position()
    del pos["market_type"]
    with pytest.raises(ValueError, match="no market_type field"):
        rh.resolve_market_type(pos)


@pytest.mark.unit
def test_resolve_market_type_rejects_unrecognized_value():
    pos = _base_position(market_type="not_a_real_market_type")
    with pytest.raises(ValueError, match="not a recognized MarketType"):
        rh.resolve_market_type(pos)


@pytest.mark.unit
def test_resolve_market_type_accepts_every_registered_member():
    for member in MarketType:
        pos = _base_position(market_type=member.value)
        assert rh.resolve_market_type(pos) is member


@pytest.mark.unit
def test_replay_one_surfaces_missing_market_type_via_evaluate_positions():
    """End-to-end: evaluate_positions() must report a resolve_market_type()
    ValueError as an error (n_error/first_errors), not let it propagate
    uncaught or get swallowed -- this is the reporting path replay_one()
    relies on to make the guard visible in the harness's own output."""
    pos = _base_position()
    del pos["market_type"]
    with tempfile.TemporaryDirectory(prefix="t427_test_") as tmp:
        trader = rh.build_trader("test_missing_market_type_e2e", Path(tmp))
        result = rh.evaluate_positions("missing-market-type-fixture", [pos], trader)
    assert result["n_error"] == 1
    assert result["n_pass"] == 0
    assert result["n_fail"] == 0
    assert any("no market_type field" in e for e in result["first_errors"])


@pytest.mark.unit
def test_build_synthetic_fixtures_all_carry_market_type():
    """T-509 side effect: OPEN_POSITION_FIELDS now includes market_type and
    resolve_market_type() hard-raises on a missing field, so every T-450
    synthetic fixture must carry an explicit market_type or it would error
    out of build_synthetic_fixtures()'s own downstream replay."""
    fixtures = rh.build_synthetic_fixtures()
    assert len(fixtures) >= 4
    for fx in fixtures:
        assert fx.get("market_type") == MarketType.MLB_PLAYER_PROP_HITS.value


@pytest.mark.unit
def test_market_type_is_compared_field():
    """OPEN_POSITION_FIELDS must include market_type, or compare() would
    never actually check it even after replay_one() started passing it."""
    assert "market_type" in rh.OPEN_POSITION_FIELDS
