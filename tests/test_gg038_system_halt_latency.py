"""
GG-038 / T-489 — System-level kill-switch (C7 SystemMonitor) halt-latency
measurement.

Scope: MEASUREMENT ONLY.

`SystemMonitor.trigger_kill_switch()` (c7_monitoring/monitor.py, ~line 837)
sets an in-process `threading.Event` and logs a CRITICAL event. This is a
REAL (not simulated) measurement of that call's own latency -- no mocked
clock is needed since the whole mechanism is in-process Python.

Caveat this file exists to state plainly, not to soften: a fast flag-set
time only matters if something downstream actually reads
`monitor.is_kill_switch_active`. A full-codebase grep
(`grep -rn "is_kill_switch_active" src/`) found it read as a live gating
condition ONLY in `t4_live_runner.py` (NBA's ADR-0029 sub-band runner,
lines ~509/560/717). Neither `run_t4_mlb_live.py` nor `run_mlb_paper_trade.py`
imports `c7_monitoring.monitor` for this purpose at all --
`run_t4_mlb_live.py` does not import `monitor.py` in any form, and
`run_mlb_paper_trade.py` imports `SystemMonitor` only to call
`.check_portfolio_pnl(...)` once, post-hoc, at the end of a run. So: this
test measures a real, fast, sub-millisecond flag-set -- and that speed is
currently meaningless as an MLB halt guarantee, because nothing MLB-side
ever checks the flag.
"""

from __future__ import annotations

import os

os.environ.setdefault("BOT_ENV", "paper")  # run_t4_mlb_live/run_mlb_paper_trade require this at import time

from unittest.mock import MagicMock

import pytest

from prediction_market_bot.c7_monitoring.monitor import (
    KILL_SWITCH_SLA_MS,
    SystemMonitor,
)

N_TRIALS = 150


def _make_monitor() -> SystemMonitor:
    logger = MagicMock()
    logger.log.return_value = True
    return SystemMonitor(
        logger=logger,
        snapshot_id="SNAP-GG038-TEST",
        session_id="SES-GG038-TEST",
    )


def test_trigger_kill_switch_sets_flag_immediately() -> None:
    monitor = _make_monitor()
    assert monitor.is_kill_switch_active is False
    result = monitor.trigger_kill_switch(reason="GG-038 test", operator="test-harness")
    assert monitor.is_kill_switch_active is True
    assert result.passed_sla is True
    assert result.halt_time_ms < KILL_SWITCH_SLA_MS


def test_system_level_halt_latency_distribution() -> None:
    halt_times_ms = []
    for i in range(N_TRIALS):
        monitor = _make_monitor()  # fresh instance per trial -- avoids idempotent-trigger skew
        result = monitor.trigger_kill_switch(
            reason=f"GG-038 trial {i}", operator="test-harness"
        )
        halt_times_ms.append(result.halt_time_ms)

    halt_times_ms.sort()
    n = len(halt_times_ms)
    p50 = halt_times_ms[int(n * 0.50)]
    p90 = halt_times_ms[int(n * 0.90)]
    lo, hi = halt_times_ms[0], halt_times_ms[-1]

    print(
        f"\n[GG-038 system-level (SystemMonitor.trigger_kill_switch) real halt "
        f"latency, n={n} trials]\n"
        f"  min={lo:.4f}ms  p50={p50:.4f}ms  p90={p90:.4f}ms  max={hi:.4f}ms\n"
        f"  NFR-03 / KILL_SWITCH_SLA_MS bar: {KILL_SWITCH_SLA_MS}ms\n"
        f"  CAVEAT: this measures only the in-process flag-set + log call. "
        f"No MLB pipeline (run_t4_mlb_live.py, run_mlb_paper_trade.py) reads "
        f"monitor.is_kill_switch_active -- a fast flag-set here has zero "
        f"enforcement effect on either live MLB process today."
    )

    # The mechanism itself is trivially fast -- sub-millisecond in-process
    # event-set + a mocked logger call. This is expected and is NOT the
    # finding; the finding is the no-consumer caveat above.
    assert hi < KILL_SWITCH_SLA_MS


def test_idempotent_retrigger_does_not_reset_original_state() -> None:
    """trigger_kill_switch() docstring claims idempotency if already triggered."""
    monitor = _make_monitor()
    first = monitor.trigger_kill_switch(reason="first", operator="test-harness")
    second = monitor.trigger_kill_switch(reason="second", operator="test-harness")
    assert monitor.is_kill_switch_active is True
    assert first.passed_sla is True
    assert second.passed_sla is True


def test_reset_kill_switch_clears_flag() -> None:
    monitor = _make_monitor()
    monitor.trigger_kill_switch(reason="GG-038 test", operator="test-harness")
    assert monitor.is_kill_switch_active is True
    monitor.reset_kill_switch(reason="GG-038 test cleanup", operator="test-harness")
    assert monitor.is_kill_switch_active is False


def test_no_mlb_pipeline_imports_monitor_for_gating() -> None:
    """
    Structural assertion backing the caveat above: run_t4_mlb_live.py does
    not import c7_monitoring.monitor at all. This is checked by source
    inspection here (not by attempting a live cross-process integration,
    which the real architecture does not support) because the absence of an
    import is itself the finding -- there is no code path to exercise.
    """
    import prediction_market_bot.run_t4_mlb_live as t4_mlb_module

    module_globals = vars(t4_mlb_module)
    assert "SystemMonitor" not in module_globals
    assert "is_kill_switch_active" not in module_globals
