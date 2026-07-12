"""
T-326 (Workstream C2) — golden-replay harness on the bet-approval path.

Freezes a small, hand-verified set of forecast/market-state fixtures
(tests/golden/*.json) with expected RiskEngine.evaluate_forecast() and
PaperTrader.open_position() output -- direction, edge, approve/reject/
kill-switch, and size -- and replays them against the real, live approval
path on every run.

Unlike test_approval_path_invariants.py (T-325), which asserts general
properties across randomized inputs, this suite pins concrete, literal
expected values for a curated set of scenarios, each chosen to be either a
plain control case or a direct replay of the GG-077/GG-087 bug mechanics.
Any drift in approval output -- from either the RiskEngine sizing/gating
logic or the paper_trader.py fee/direction logic -- fails with a value
diff against the frozen fixture, not just a boolean pass/fail.

Governing principle (ITERATION_PLAN_calibration_hardening.md): a test is
not done until it is reproducible from a clean checkout and leaves an
audit trail. Fixtures are plain JSON so a diff on this directory in a PR
review is a direct, human-readable statement of what approval behavior
changed and why.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

os.environ.setdefault("BOT_ENV", "paper")

from prediction_market_bot.c4_risk_engine.risk import RiskEngine
from prediction_market_bot.c5_execution.paper_trader import PaperTrader

_GOLDEN_DIR = Path(__file__).parent / "golden"
_FIXTURE_PATHS = sorted(_GOLDEN_DIR.glob("*.json"))


def _load_fixtures() -> list[dict[str, Any]]:
    return [json.loads(p.read_text()) for p in _FIXTURE_PATHS]


def _make_risk_logger() -> MagicMock:
    logger = MagicMock()
    logger.log.return_value = True
    return logger


def _make_paper_logger() -> MagicMock:
    logger = MagicMock()
    logger.info.return_value = True
    logger.warning.return_value = True
    logger.error.return_value = True
    logger.log.return_value = True
    return logger


def _run_risk_engine(fixture: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    re_cfg = fixture["risk_engine"]
    engine = RiskEngine(
        logger=_make_risk_logger(),
        snapshot_id="SNAP-GOLDEN",
        bankroll=re_cfg["bankroll"],
        kelly_fraction=re_cfg["kelly_fraction"],
        initial_bankroll=re_cfg.get("initial_bankroll"),
        min_bet_usd=re_cfg.get("min_bet_usd"),
    )
    os.environ["BOT_C4_ACTIVE"] = "true"
    try:
        return engine.evaluate_forecast(
            forecast_record=fixture["forecast_record"],
            **fixture["evaluate_forecast_kwargs"],
        )
    finally:
        os.environ.pop("BOT_C4_ACTIVE", None)


def _open_position(approval: dict[str, Any], pt_cfg: dict[str, Any]) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as d:
        trader = PaperTrader(Path(d) / "portfolio.json", _make_paper_logger())
        ok, pos = trader.open_position(
            approval=approval,
            player_name=pt_cfg["player_name"],
            player_id=pt_cfg["player_id"],
            kalshi_ticker=pt_cfg["kalshi_ticker"],
            kalshi_threshold=pt_cfg["kalshi_threshold"],
            mid_price=pt_cfg["mid_price"],
            vig=pt_cfg["vig"],
            game_date=pt_cfg["game_date"],
            pool_isolated=pt_cfg.get("pool_isolated", False),
        )
        assert ok, "open_position() C6 write failed unexpectedly for a golden fixture"
        return pos


def _assert_approval_matches(approval: dict[str, Any], expected: dict[str, Any]) -> None:
    assert approval["approval_status"] == expected["approval_status"]
    assert approval["rejection_reason"] == expected["rejection_reason"]
    assert approval["approved_direction"] == expected["approved_direction"]
    assert approval["approved_size"] == pytest.approx(expected["approved_size"], abs=1e-4)


def _assert_position_matches(pos: dict[str, Any], expected: dict[str, Any]) -> None:
    assert pos != {}, "expected a position to open but open_position() returned {}"
    assert pos["direction"] == expected["direction"]
    assert pos["size_usd"] == pytest.approx(expected["size_usd"], abs=1e-4)
    assert pos["gross_edge"] == pytest.approx(expected["gross_edge"], abs=1e-6)
    assert pos["fee_per_contract"] == pytest.approx(expected["fee_per_contract"], abs=1e-6)
    assert pos["fee_net_edge"] == pytest.approx(expected["fee_net_edge"], abs=1e-6)
    assert pos["fee_contaminated"] == expected["fee_contaminated"]


@pytest.mark.golden
@pytest.mark.unit
@pytest.mark.parametrize("fixture", _load_fixtures(), ids=[f["scenario"] for f in _load_fixtures()])
def test_golden_replay(fixture: dict[str, Any]) -> None:
    flow = fixture["flow"]
    ok, approval = _run_risk_engine(fixture)
    assert ok, "RiskEngine C6 write failed unexpectedly for a golden fixture"
    _assert_approval_matches(approval, fixture["expected_approval"])

    if flow == "reject_only" or flow == "kill_switch_only":
        # No position should ever open off a REJECTED/KILL_SWITCH approval --
        # approved_size is 0.0, which open_position() must treat as a no-op.
        pos = _open_position(
            approval,
            {
                "player_name": "Golden No-Op", "player_id": 0,
                "kalshi_ticker": "KXMLBHIT-NOOP", "kalshi_threshold": 1,
                "mid_price": 0.50, "vig": 0.0, "game_date": "2026-05-30",
            },
        )
        assert pos == {}
        return

    # Both real callers (run_mlb_paper_trade.py:946-951 for T1, and
    # run_t4_mlb_live.py:1069-1071 for T4) merge model_p/edge/gross_edge from
    # the forecast record into the RiskEngine approval dict before calling
    # open_position() -- RiskEngine's own approval dict does not carry these
    # forecast-side fields. Replicate that merge here or gross_edge/fee_net_edge
    # silently read as 0.0 regardless of what the fixture pins.
    fc = fixture["forecast_record"]
    approval = {
        **approval,
        "model_p": float(fc["p_estimate"]),
        "edge": float(fc["edge"]),
        "gross_edge": float(fc["gross_edge"]),
    }

    if flow == "t1_direct":
        pos = _open_position(approval, fixture["paper_trader"])
        _assert_position_matches(pos, fixture["expected_position"])
        return

    if flow == "t4_override":
        # run_t4_mlb_live.py's paper-mode sizing: RiskEngine's Kelly-derived
        # approved_size is discarded post-approval in favor of a flat
        # single-contract-at-market-price size. Pinning this formula here
        # (not just importing it) is intentional -- see T-325's source-drift
        # pin (test_approval_path_invariants.py) for the direction-derivation
        # block; this is the sibling formula for T4's size-override line.
        override_cfg = fixture["t4_size_override"]
        mip = override_cfg["market_implied_prob"]
        direction = approval["approved_direction"]
        override_size = mip if direction == "YES" else (1.0 - mip)
        assert override_size == pytest.approx(override_cfg["expected_override_size"], abs=1e-6)

        overridden_approval = {**approval, "approved_size": override_size}
        pos = _open_position(overridden_approval, fixture["paper_trader"])
        _assert_position_matches(pos, fixture["expected_position"])
        return

    raise AssertionError(f"unknown fixture flow: {flow!r}")


def test_golden_fixture_directory_is_not_empty() -> None:
    # A silently-empty golden/ directory (e.g. a bad glob after a rename)
    # would make test_golden_replay's parametrize collect zero cases and
    # report as passing -- this guards against that failure mode.
    assert len(_FIXTURE_PATHS) >= 6, (
        f"expected at least 6 golden fixtures, found {len(_FIXTURE_PATHS)} "
        f"in {_GOLDEN_DIR}"
    )
