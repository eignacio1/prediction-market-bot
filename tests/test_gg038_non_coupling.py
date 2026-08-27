"""
GG-038 / T-489 — non-coupling verification, by construction.

CLAUDE.md requires: "a band-level kill switch (e.g., T4 budget exhausted)
halts only that band. The system-level kill switch halts everything. Both
tiers must be active simultaneously, independently, and without coupling to
each other."

Three real objects/paths are in play, verified by direct source reading this
session:

  1. MLB T4 band-level switch: a filesystem flag,
     `run_t4_mlb_live.KILL_SWITCH_PATH`, checked via `kill_switch_armed()`.
  2. System-level switch: `c7_monitoring.monitor.SystemMonitor`'s
     `is_kill_switch_active` / `trigger_kill_switch()`.
  3. Risk-engine-level per-evaluation status: `RiskEngine.evaluate_forecast()`
     can return `approval_status == "KILL_SWITCH"` (drawdown breach). Grepped
     handling of this status:
       - T1 MLB (`run_mlb_paper_trade.py` line ~986): checks
         `status == "KILL_SWITCH"` explicitly and sets a local
         `_reserve_halted = True` that skips all remaining evaluations for
         the rest of THAT SAME cron invocation.
       - T4 MLB (`run_t4_mlb_live.py` line ~1364): only checks
         `approval.get("approval_status") != "APPROVED"` and `continue`s to
         the next ticker -- there is no `"KILL_SWITCH"`-specific branch
         anywhere in this file (grepped: zero hits for the literal
         `KILL_SWITCH"` string). A KILL_SWITCH approval is treated
         IDENTICALLY to an ordinary REJECTED approval: skip this one
         ticker, keep evaluating the rest of the cycle, keep looping.

This is a real, concrete non-coupling / asymmetric-halt finding: T1 self-halts
on a risk-engine KILL_SWITCH status; T4 does not. (Currently low-stakes in
dollar terms only because T4M-PROJ's kelly_fraction is zeroed by ADR-0048 --
see test_gg038_t4_mlb_halt_latency.py and the GG-038 write-up for the
evaluations-in-window / stakes discussion. The architectural gap is real
regardless of current sizing.)

Also confirmed: the bare `trigger_kill_switch()` calls appearing in
`risk.py` at lines 224 and 227 are inside the `RiskEngine` class DOCSTRING
(a "Usage (Phase 5+)::" illustrative example, lines 205-235) -- NOT executable
code. risk.py never actually calls `SystemMonitor.trigger_kill_switch()`.
The only real call sites of `trigger_kill_switch(` in the codebase are
`t4_live_runner.py` (NBA, 4 sites), `monitor.py` itself (self-trigger on an
L4 alert breach), and three C2 feature-store files
(`features.py`, `qualitative_amplifier.py`, `qualitative_store.py`) --
none of which are on the MLB T1/T4 hot path for a drawdown-triggered halt.
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_ENV", "paper")  # run_mlb_paper_trade.py hard-requires this at import time

from pathlib import Path
from unittest.mock import MagicMock

from prediction_market_bot.c7_monitoring.monitor import SystemMonitor
from prediction_market_bot.run_t4_mlb_live import kill_switch_armed


def _make_monitor() -> SystemMonitor:
    logger = MagicMock()
    logger.log.return_value = True
    return SystemMonitor(
        logger=logger, snapshot_id="SNAP-GG038-COUPLING", session_id="SES-GG038-COUPLING"
    )


def test_tripping_band_level_flag_does_not_touch_system_monitor(tmp_path: Path) -> None:
    """
    (a) Trip the MLB T4 band-level file flag; assert the completely separate
    SystemMonitor object is untouched. This is expected to trivially pass --
    that IS the finding: the two mechanisms share no variable, no import, no
    call path. Non-coupling here is an accident of separateness, not a
    designed guarantee.
    """
    flag_path = tmp_path / "t4_mlb_kill_switch.flag"
    monitor = _make_monitor()

    assert kill_switch_armed(flag_path) is False
    assert monitor.is_kill_switch_active is False

    flag_path.touch()  # trip the band-level switch

    assert kill_switch_armed(flag_path) is True
    assert monitor.is_kill_switch_active is False  # untouched, as expected


def test_tripping_system_switch_has_no_assertable_effect_on_mlb_pipelines() -> None:
    """
    (b) Trip SystemMonitor.trigger_kill_switch() and assert:
      - is_kill_switch_active becomes True (the mechanism itself works)
      - neither MLB pipeline module exposes any code path that would react
        to it, asserted by the absence of the symbol in each module's
        namespace (there is nothing else to assert against -- no consumer
        exists to exercise).
    This is the honest, unsoftened result: "system switch halts everything"
    does NOT currently hold for the MLB books.
    """
    monitor = _make_monitor()
    assert monitor.is_kill_switch_active is False
    monitor.trigger_kill_switch(reason="GG-038 non-coupling test", operator="test-harness")
    assert monitor.is_kill_switch_active is True

    import prediction_market_bot.run_t4_mlb_live as t4_mlb_module
    import prediction_market_bot.run_mlb_paper_trade as t1_mlb_module

    for module in (t4_mlb_module, t1_mlb_module):
        g = vars(module)
        assert "is_kill_switch_active" not in g, (
            f"{module.__name__} unexpectedly references is_kill_switch_active -- "
            "re-verify the no-consumer finding, it may be stale"
        )


def test_t1_self_halts_on_risk_engine_kill_switch_status_t4_does_not() -> None:
    """
    Concrete asymmetric-response finding, verified by source inspection
    (there is no shared harness to drive both pipelines' full evaluation
    loops in a unit test without substantial fixture infrastructure outside
    this session's scope fence -- so this test asserts the code-level fact
    the report is built on, rather than fabricating an end-to-end run).

    run_mlb_paper_trade.py explicitly branches on the literal string
    "KILL_SWITCH" (T1's self-halt gate). run_t4_mlb_live.py contains no such
    branch anywhere in its source -- confirmed by grepping the live file
    for the exact status-check literal.
    """
    import inspect

    import prediction_market_bot.run_mlb_paper_trade as t1_mlb_module
    import prediction_market_bot.run_t4_mlb_live as t4_mlb_module

    t1_source = inspect.getsource(t1_mlb_module)
    t4_source = inspect.getsource(t4_mlb_module)

    assert '"KILL_SWITCH"' in t1_source, (
        "T1 MLB no longer branches on KILL_SWITCH status -- re-verify, "
        "this test's premise may be stale"
    )
    assert '"KILL_SWITCH"' not in t4_source, (
        "T4 MLB now branches on KILL_SWITCH status -- if true, this is a "
        "FIX to the non-coupling gap this test documents; update the "
        "GG-038 write-up rather than treating this as a test failure to "
        "silence."
    )
