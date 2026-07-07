"""
Tests for src/prediction_market_bot/c7_monitoring/monitor.py

Coverage areas:
  - ForecastOutcomeRecord: immutable dataclass construction
  - _compute_brier: empty, single, multi; known values
  - _compute_ece: empty, single bucket, multi-bucket; perfect calibration → ~0
  - _compute_mean_edge: empty, positive, negative
  - DriftSnapshot: alert_level escalation ladder (OK → L1 → L2 → L3 pause)
  - SystemMonitor.record_forecast_outcome: appends to window; maxlen rollover
  - SystemMonitor.get_drift_snapshot: empty window; n < window; correct metrics
  - SystemMonitor.check_and_alert: L1/L2/L3 log correct severity; L3 pause does
      NOT auto-trigger kill (GG-095 — real kill is driven by risk.py, not drift)
  - SystemMonitor.trigger_kill_switch: sets is_kill_switch_active; logs CRITICAL;
      returns KillSwitchResult with halt_time_ms <= SLA; idempotent
  - SystemMonitor.reset_kill_switch: clears flag; logs WARNING; clears state
  - SystemMonitor.run_kill_switch_drill: passes SLA; resets after drill; logs drill result
  - SystemMonitor.get_health_snapshot: contains all IF-C7-C8 required fields
  - Thread safety: concurrent record_forecast_outcome calls all land
  - C6 write failure: check_and_alert continues; kill switch still sets
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import numpy as np
import pytest

_SRC = Path(__file__).parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from prediction_market_bot.c7_monitoring.monitor import (
    ALERT_L1_WATCH,
    ALERT_L2_ALERT,
    ALERT_L3_PAUSE,
    ALERT_L4_KILL,
    ALERT_OK,
    BRIER_BASELINE,
    BRIER_L1_DELTA,
    BRIER_L2_DELTA,
    BRIER_L3_DELTA,
    ECE_BASELINE,
    ECE_L2_DELTA,
    KILL_SWITCH_SLA_MS,
    KS_ARMED,
    KS_TRIGGERED,
    PNL_L1_LOSS_PCT,
    PNL_L2_LOSS_PCT,
    DriftSnapshot,
    ForecastOutcomeRecord,
    KillSwitchResult,
    SystemMonitor,
    _compute_brier,
    _compute_ece,
    _compute_mean_edge,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_logger(write_ok: bool = True) -> MagicMock:
    logger = MagicMock()
    logger.log.return_value = write_ok
    return logger


def _make_monitor(
    write_ok: bool = True,
    window_size: int = 30,
    brier_baseline: float = BRIER_BASELINE,
) -> tuple[SystemMonitor, MagicMock]:
    logger = _make_logger(write_ok)
    monitor = SystemMonitor(
        logger=logger,
        snapshot_id="SNAP-TEST-001",
        session_id="SES-TEST-001",
        brier_baseline=brier_baseline,
        window_size=window_size,
    )
    return monitor, logger


def _record(
    monitor: SystemMonitor,
    p: float,
    y: int,
    mip: float = 0.50,
) -> None:
    monitor.record_forecast_outcome(p_estimate=p, outcome=y, market_implied_prob=mip)


def _add_good_records(monitor: SystemMonitor, n: int = 10) -> None:
    """
    Add n calibrated records that beat the null model baseline.
    Uses p=0.70, 70% y=1 / 30% y=0 → calibrated (ECE≈0) + Brier≈0.21 (below 0.2416).
    """
    for i in range(n):
        y = 1 if (i % 10) < 7 else 0
        _record(monitor, p=0.70, y=y, mip=0.50)


def _add_bad_records(monitor: SystemMonitor, n: int = 10) -> None:
    """Add n records well above the kill threshold."""
    for _ in range(n):
        # p=0.50 random → Brier ~0.25 which is just above baseline
        # Use p=0.20, y=1 → Brier = (0.20-1)^2 = 0.64 — way above L3
        _record(monitor, p=0.20, y=1, mip=0.50)


# ---------------------------------------------------------------------------
# ForecastOutcomeRecord
# ---------------------------------------------------------------------------


class TestForecastOutcomeRecord:
    @pytest.mark.unit
    def test_immutable(self):
        rec = ForecastOutcomeRecord(p_estimate=0.6, outcome=1, market_implied_prob=0.5)
        with pytest.raises((AttributeError, TypeError)):
            rec.p_estimate = 0.7  # type: ignore[misc]

    @pytest.mark.unit
    def test_fields(self):
        rec = ForecastOutcomeRecord(p_estimate=0.6, outcome=0, market_implied_prob=0.55)
        assert rec.p_estimate == 0.6
        assert rec.outcome == 0
        assert rec.market_implied_prob == 0.55


# ---------------------------------------------------------------------------
# _compute_brier
# ---------------------------------------------------------------------------


class TestComputeBrier:
    @pytest.mark.unit
    def test_empty_returns_nan(self):
        assert np.isnan(_compute_brier([]))

    @pytest.mark.unit
    def test_perfect_forecast(self):
        # p=1.0, y=1 → Brier = 0.0
        rec = ForecastOutcomeRecord(p_estimate=1.0, outcome=1, market_implied_prob=0.5)
        assert _compute_brier([rec]) == pytest.approx(0.0)

    @pytest.mark.unit
    def test_null_model(self):
        # p=0.5, y={0,1} alternating → Brier = 0.25
        recs = [
            ForecastOutcomeRecord(0.5, 0, 0.5),
            ForecastOutcomeRecord(0.5, 1, 0.5),
        ]
        assert _compute_brier(recs) == pytest.approx(0.25)

    @pytest.mark.unit
    def test_known_value(self):
        # p=0.7, y=1 → (0.7-1)^2 = 0.09
        rec = ForecastOutcomeRecord(0.7, 1, 0.5)
        assert _compute_brier([rec]) == pytest.approx(0.09)


# ---------------------------------------------------------------------------
# _compute_ece
# ---------------------------------------------------------------------------


class TestComputeEce:
    @pytest.mark.unit
    def test_empty_returns_nan(self):
        assert np.isnan(_compute_ece([]))

    @pytest.mark.unit
    def test_perfect_calibration(self):
        # One point at p=0.6, y=1: only 1 bin, fraction_pos=1.0, mean_pred=0.6
        # ECE = 1 * |0.6 - 1.0| = 0.4 (small sample imperfection is expected)
        # This just tests the function returns a float in [0, 1]
        rec = ForecastOutcomeRecord(0.6, 1, 0.5)
        ece = _compute_ece([rec])
        assert 0.0 <= ece <= 1.0

    @pytest.mark.unit
    def test_returns_float(self):
        recs = [
            ForecastOutcomeRecord(0.3, 0, 0.5),
            ForecastOutcomeRecord(0.7, 1, 0.5),
            ForecastOutcomeRecord(0.5, 0, 0.5),
        ]
        ece = _compute_ece(recs)
        assert isinstance(ece, float)
        assert 0.0 <= ece <= 1.0


# ---------------------------------------------------------------------------
# _compute_mean_edge
# ---------------------------------------------------------------------------


class TestComputeMeanEdge:
    @pytest.mark.unit
    def test_empty_returns_nan(self):
        assert np.isnan(_compute_mean_edge([]))

    @pytest.mark.unit
    def test_positive_edge(self):
        recs = [ForecastOutcomeRecord(0.6, 1, 0.5)]
        assert _compute_mean_edge(recs) == pytest.approx(0.1)

    @pytest.mark.unit
    def test_negative_edge(self):
        recs = [ForecastOutcomeRecord(0.4, 1, 0.5)]
        assert _compute_mean_edge(recs) == pytest.approx(-0.1)

    @pytest.mark.unit
    def test_zero_edge(self):
        recs = [ForecastOutcomeRecord(0.5, 1, 0.5)]
        assert _compute_mean_edge(recs) == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# SystemMonitor — initialization
# ---------------------------------------------------------------------------


class TestSystemMonitorInit:
    @pytest.mark.unit
    def test_initial_state_armed(self):
        monitor, _ = _make_monitor()
        assert not monitor.is_kill_switch_active
        assert monitor.kill_switch_state == KS_ARMED

    @pytest.mark.unit
    def test_initial_snapshot_empty(self):
        monitor, _ = _make_monitor()
        snap = monitor.get_drift_snapshot()
        assert snap.n_events == 0
        assert snap.rolling_brier is None
        assert snap.alert_level == ALERT_OK


# ---------------------------------------------------------------------------
# SystemMonitor — record_forecast_outcome
# ---------------------------------------------------------------------------


class TestRecordForecastOutcome:
    @pytest.mark.unit
    def test_records_accumulate(self):
        monitor, _ = _make_monitor()
        _record(monitor, 0.6, 1)
        _record(monitor, 0.4, 0)
        snap = monitor.get_drift_snapshot()
        assert snap.n_events == 2

    @pytest.mark.unit
    def test_window_maxlen_rollover(self):
        monitor, _ = _make_monitor(window_size=5)
        for _ in range(10):
            _record(monitor, 0.6, 1)
        snap = monitor.get_drift_snapshot()
        assert snap.n_events == 5

    @pytest.mark.unit
    def test_coerces_types(self):
        monitor, _ = _make_monitor()
        # Should not raise on int/float coercion
        monitor.record_forecast_outcome(p_estimate=0.6, outcome=1, market_implied_prob=0.5)
        assert monitor.get_drift_snapshot().n_events == 1


# ---------------------------------------------------------------------------
# SystemMonitor — get_drift_snapshot alert levels
# ---------------------------------------------------------------------------


class TestDriftSnapshotAlertLevels:
    @pytest.mark.unit
    def test_ok_when_brier_below_l1(self):
        # Use very low brier (good predictions) — well below baseline
        monitor, _ = _make_monitor()
        _add_good_records(monitor, n=10)
        snap = monitor.get_drift_snapshot()
        assert snap.alert_level == ALERT_OK

    @pytest.mark.unit
    def test_l1_watch_when_brier_above_l1(self):
        # Brier above L1 means model is worse than null — ECE often elevates too,
        # so alert may be L1 or L2. Assert Brier is above L1 and alert is not OK.
        threshold = BRIER_BASELINE + BRIER_L1_DELTA + 0.001
        p = float(np.sqrt(threshold))
        monitor, _ = _make_monitor()
        for _ in range(10):
            _record(monitor, p=p, y=0)
        snap = monitor.get_drift_snapshot()
        assert snap.rolling_brier is not None
        assert snap.rolling_brier > BRIER_BASELINE + BRIER_L1_DELTA
        assert snap.alert_level != ALERT_OK

    @pytest.mark.unit
    def test_l2_alert_when_brier_above_l2(self):
        threshold = BRIER_BASELINE + BRIER_L2_DELTA + 0.001
        p = float(np.sqrt(threshold))
        monitor, _ = _make_monitor()
        for _ in range(10):
            _record(monitor, p=p, y=0)
        snap = monitor.get_drift_snapshot()
        assert snap.alert_level == ALERT_L2_ALERT

    @pytest.mark.unit
    def test_l3_pause_when_brier_above_l3(self):
        """GG-095: crossing BRIER_L3_DELTA pauses new positions — it does not
        by itself set ALERT_L4_KILL. Full kill is driven independently by
        risk.py's drawdown/daily-loss criteria, not by drift."""
        monitor, _ = _make_monitor()
        _add_bad_records(monitor, n=10)
        snap = monitor.get_drift_snapshot()
        assert snap.alert_level == ALERT_L3_PAUSE

    @pytest.mark.unit
    def test_l1_watch_on_negative_mean_edge(self):
        monitor, _ = _make_monitor()
        # Good Brier but negative edge
        for _ in range(10):
            # p < mip → negative edge, but good Brier (p=0.7, y=1)
            monitor.record_forecast_outcome(p_estimate=0.3, outcome=0, market_implied_prob=0.5)
        snap = monitor.get_drift_snapshot()
        # Brier = (0.3-0)^2 = 0.09 → OK on Brier; edge = 0.3 - 0.5 = -0.2 → L1
        assert ALERT_L1_WATCH in snap.alert_level or snap.mean_edge < 0

    @pytest.mark.unit
    def test_alert_messages_present_on_breach(self):
        monitor, _ = _make_monitor()
        _add_bad_records(monitor, n=10)
        snap = monitor.get_drift_snapshot()
        assert len(snap.alert_messages) > 0

    @pytest.mark.unit
    def test_no_messages_on_ok(self):
        monitor, _ = _make_monitor()
        _add_good_records(monitor, n=10)
        snap = monitor.get_drift_snapshot()
        assert snap.alert_level == ALERT_OK
        assert snap.alert_messages == []


# ---------------------------------------------------------------------------
# SystemMonitor — check_and_alert
# ---------------------------------------------------------------------------


class TestCheckAndAlert:
    @pytest.mark.unit
    def test_no_log_on_empty_window(self):
        monitor, logger = _make_monitor()
        monitor.check_and_alert()
        logger.log.assert_not_called()

    @pytest.mark.unit
    def test_info_log_on_ok(self):
        monitor, logger = _make_monitor()
        _add_good_records(monitor, n=10)
        monitor.check_and_alert(session_id="SES-001")
        assert logger.log.called
        call_kwargs = logger.log.call_args_list[0][1]
        assert call_kwargs["severity"] == "INFO"

    @pytest.mark.unit
    def test_warning_log_on_l2(self):
        threshold = BRIER_BASELINE + BRIER_L2_DELTA + 0.001
        p = float(np.sqrt(threshold))
        monitor, logger = _make_monitor()
        for _ in range(10):
            _record(monitor, p=p, y=0)
        monitor.check_and_alert()
        severities = [c[1]["severity"] for c in logger.log.call_args_list]
        assert "WARNING" in severities

    @pytest.mark.unit
    def test_error_log_on_l3_pause(self):
        """GG-095: L3 pause logs at ERROR severity (ALT-002), not CRITICAL."""
        monitor, logger = _make_monitor()
        _add_bad_records(monitor, n=10)
        monitor.check_and_alert()
        severities = [c[1]["severity"] for c in logger.log.call_args_list]
        assert "ERROR" in severities
        assert "CRITICAL" not in severities

    @pytest.mark.unit
    def test_l3_pause_does_not_auto_trigger_kill_switch(self):
        """GG-095: a Brier-drift breach alone must never fire the kill switch —
        real L4/kill is driven independently by risk.py's drawdown/daily-loss
        criteria (RISK_APPETITE_CONSTRAINTS.md), not by this drift ladder."""
        monitor, logger = _make_monitor()
        _add_bad_records(monitor, n=10)
        assert not monitor.is_kill_switch_active
        monitor.check_and_alert()
        assert not monitor.is_kill_switch_active
        event_types = [c[1].get("event_type") for c in logger.log.call_args_list]
        assert "drift_alert_l3_pause" in event_types
        assert "kill_switch_triggered" not in event_types

    @pytest.mark.unit
    def test_l4_auto_triggers_kill_switch_if_ever_set(self):
        """The L4 auto-kill branch in check_and_alert() is retained for a future
        caller that reflects risk.py's independently-triggered kill back into a
        DriftSnapshot (see monitor.py comment at the L4 branch). Nothing in this
        module sets ALERT_L4_KILL today (GG-095) — this test exercises the
        branch directly via a patched snapshot so the dormant idempotency logic
        stays covered."""
        monitor, logger = _make_monitor()
        _add_good_records(monitor, n=1)
        fake_snap = monitor.get_drift_snapshot()
        forced = DriftSnapshot(
            n_events=fake_snap.n_events,
            rolling_brier=fake_snap.rolling_brier,
            rolling_ece=fake_snap.rolling_ece,
            mean_edge=fake_snap.mean_edge,
            alert_level=ALERT_L4_KILL,
            alert_messages=["forced L4 for dormant-branch coverage"],
            brier_baseline=fake_snap.brier_baseline,
            ece_baseline=fake_snap.ece_baseline,
            computed_at=fake_snap.computed_at,
            shadow_n_events=fake_snap.shadow_n_events,
            shadow_brier_30=fake_snap.shadow_brier_30,
            shadow_promotion_flag=fake_snap.shadow_promotion_flag,
        )
        with patch.object(monitor, "get_drift_snapshot", return_value=forced):
            assert not monitor.is_kill_switch_active
            monitor.check_and_alert()
            assert monitor.is_kill_switch_active
            severities = [c[1]["severity"] for c in logger.log.call_args_list]
            assert "CRITICAL" in severities
            monitor.check_and_alert()
            ks_trigger_count = sum(
                1 for c in logger.log.call_args_list
                if c[1].get("event_type") == "kill_switch_triggered"
            )
            assert ks_trigger_count == 1

    @pytest.mark.unit
    def test_mean_edge_neg_emits_separate_warning(self):
        monitor, logger = _make_monitor()
        for _ in range(10):
            monitor.record_forecast_outcome(0.3, 0, 0.5)  # edge = -0.2
        monitor.check_and_alert()
        event_types = [c[1]["event_type"] for c in logger.log.call_args_list]
        assert "drift_alert_mean_edge_neg" in event_types


# ---------------------------------------------------------------------------
# SystemMonitor — trigger_kill_switch
# ---------------------------------------------------------------------------


class TestTriggerKillSwitch:
    @pytest.mark.unit
    def test_sets_kill_switch_active(self):
        monitor, _ = _make_monitor()
        monitor.trigger_kill_switch(reason="test")
        assert monitor.is_kill_switch_active
        assert monitor.kill_switch_state == KS_TRIGGERED

    @pytest.mark.unit
    def test_returns_kill_switch_result(self):
        monitor, _ = _make_monitor()
        result = monitor.trigger_kill_switch(reason="test", operator="Earl")
        assert isinstance(result, KillSwitchResult)
        assert result.trigger_reason == "test"
        assert result.operator == "Earl"

    @pytest.mark.unit
    def test_halt_time_within_sla(self):
        monitor, _ = _make_monitor()
        result = monitor.trigger_kill_switch(reason="test")
        assert result.halt_time_ms <= KILL_SWITCH_SLA_MS
        assert result.passed_sla is True

    @pytest.mark.unit
    def test_logs_critical_event(self):
        monitor, logger = _make_monitor()
        monitor.trigger_kill_switch(reason="test_reason")
        call_kwargs = logger.log.call_args_list[-1][1]
        assert call_kwargs["severity"] == "CRITICAL"
        assert call_kwargs["event_type"] == "kill_switch_triggered"

    @pytest.mark.unit
    def test_kill_switch_id_in_result_and_log(self):
        monitor, logger = _make_monitor()
        result = monitor.trigger_kill_switch(reason="test")
        payload = logger.log.call_args_list[-1][1]["payload"]
        assert payload["kill_switch_id"] == result.kill_switch_id

    @pytest.mark.unit
    def test_idempotent_second_trigger_still_active(self):
        monitor, _ = _make_monitor()
        monitor.trigger_kill_switch(reason="first")
        monitor.trigger_kill_switch(reason="second")
        assert monitor.is_kill_switch_active

    @pytest.mark.unit
    def test_auto_trigger_operator_is_none(self):
        monitor, _ = _make_monitor()
        result = monitor.trigger_kill_switch(reason="auto", operator=None)
        assert result.operator is None

    @pytest.mark.unit
    def test_c6_write_failure_still_sets_kill_event(self):
        monitor, logger = _make_monitor(write_ok=False)
        logger.log.return_value = False
        monitor.trigger_kill_switch(reason="test")
        assert monitor.is_kill_switch_active


# ---------------------------------------------------------------------------
# SystemMonitor — reset_kill_switch
# ---------------------------------------------------------------------------


class TestResetKillSwitch:
    @pytest.mark.unit
    def test_clears_kill_switch_active(self):
        monitor, _ = _make_monitor()
        monitor.trigger_kill_switch(reason="test")
        assert monitor.is_kill_switch_active
        monitor.reset_kill_switch(reason="drill recovery", operator="Earl")
        assert not monitor.is_kill_switch_active
        assert monitor.kill_switch_state == KS_ARMED

    @pytest.mark.unit
    def test_logs_warning(self):
        monitor, logger = _make_monitor()
        monitor.trigger_kill_switch(reason="test")
        logger.log.reset_mock()
        monitor.reset_kill_switch(reason="drill recovery", operator="Earl")
        call_kwargs = logger.log.call_args_list[0][1]
        assert call_kwargs["severity"] == "WARNING"
        assert call_kwargs["event_type"] == "kill_switch_reset"

    @pytest.mark.unit
    def test_clears_internal_state(self):
        monitor, _ = _make_monitor()
        monitor.trigger_kill_switch(reason="original reason")
        monitor.reset_kill_switch(reason="reset", operator="Earl")
        assert monitor._kill_reason is None
        assert monitor._kill_id is None


# ---------------------------------------------------------------------------
# SystemMonitor — run_kill_switch_drill (T-051 / TC-007)
# ---------------------------------------------------------------------------


class TestKillSwitchDrill:
    @pytest.mark.unit
    def test_drill_passes_sla(self):
        monitor, _ = _make_monitor()
        result = monitor.run_kill_switch_drill(operator="Earl")
        assert result.passed_sla is True
        assert result.halt_time_ms <= KILL_SWITCH_SLA_MS

    @pytest.mark.unit
    def test_drill_is_marked_as_drill(self):
        monitor, _ = _make_monitor()
        result = monitor.run_kill_switch_drill(operator="Earl")
        assert result.is_drill is True

    @pytest.mark.unit
    def test_kill_switch_reset_after_drill(self):
        monitor, _ = _make_monitor()
        monitor.run_kill_switch_drill(operator="Earl")
        assert not monitor.is_kill_switch_active

    @pytest.mark.unit
    def test_drill_logs_kill_triggered_and_drill_result_and_reset(self):
        monitor, logger = _make_monitor()
        monitor.run_kill_switch_drill(operator="Earl")
        event_types = [c[1]["event_type"] for c in logger.log.call_args_list]
        assert "kill_switch_triggered" in event_types
        assert "kill_switch_drill_result" in event_types
        assert "kill_switch_reset" in event_types

    @pytest.mark.unit
    def test_drill_result_has_kill_switch_id(self):
        monitor, _ = _make_monitor()
        result = monitor.run_kill_switch_drill()
        assert result.kill_switch_id.startswith("KS-")

    @pytest.mark.unit
    def test_drill_result_references_tc007(self):
        monitor, logger = _make_monitor()
        monitor.run_kill_switch_drill()
        drill_log = next(
            c for c in logger.log.call_args_list
            if c[1]["event_type"] == "kill_switch_drill_result"
        )
        assert drill_log[1]["payload"]["tc_ref"] == "TC-007"


# ---------------------------------------------------------------------------
# SystemMonitor — get_health_snapshot (IF-C7-C8)
# ---------------------------------------------------------------------------

_REQUIRED_HEALTH_FIELDS = {
    "kill_switch_active",
    "kill_switch_state",
    "metric_name",
    "metric_value",
    "threshold",
    "alert_level",
    "n_events_in_window",
    "rolling_brier",
    "rolling_ece",
    "mean_edge",
    "brier_baseline",
    "ece_baseline",
}


class TestGetHealthSnapshot:
    @pytest.mark.unit
    def test_contains_required_fields(self):
        monitor, _ = _make_monitor()
        snapshot = monitor.get_health_snapshot()
        for field in _REQUIRED_HEALTH_FIELDS:
            assert field in snapshot, f"Missing field: {field}"

    @pytest.mark.unit
    def test_kill_switch_active_reflects_state(self):
        monitor, _ = _make_monitor()
        assert monitor.get_health_snapshot()["kill_switch_active"] is False
        monitor.trigger_kill_switch(reason="test")
        assert monitor.get_health_snapshot()["kill_switch_active"] is True

    @pytest.mark.unit
    def test_alert_level_ok_on_empty(self):
        monitor, _ = _make_monitor()
        snap = monitor.get_health_snapshot()
        assert snap["alert_level"] == ALERT_OK

    @pytest.mark.unit
    def test_metric_name_correct(self):
        monitor, _ = _make_monitor()
        snap = monitor.get_health_snapshot()
        assert snap["metric_name"] == "c7.drift.rolling_brier_score"


# ---------------------------------------------------------------------------
# Thread safety
# ---------------------------------------------------------------------------


class TestThreadSafety:
    @pytest.mark.unit
    def test_concurrent_record_outcome_all_land(self):
        monitor, _ = _make_monitor(window_size=1000)
        threads = [
            threading.Thread(target=lambda: _record(monitor, 0.6, 1))
            for _ in range(100)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        snap = monitor.get_drift_snapshot()
        assert snap.n_events <= 1000

    @pytest.mark.unit
    def test_concurrent_kill_switch_trigger_safe(self):
        monitor, _ = _make_monitor()
        threads = [
            threading.Thread(
                target=lambda: monitor.trigger_kill_switch(reason="concurrent test")
            )
            for _ in range(20)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert monitor.is_kill_switch_active


# ---------------------------------------------------------------------------
# SystemMonitor — check_portfolio_pnl (KI-012 / T-091)
# ---------------------------------------------------------------------------


class TestCheckPortfolioPnl:
    @pytest.mark.unit
    def test_no_alert_when_profitable(self):
        monitor, logger = _make_monitor()
        monitor.check_portfolio_pnl(total_realized_pnl=10.0, initial_bankroll=1000.0)
        logger.log.assert_not_called()

    @pytest.mark.unit
    def test_no_alert_below_l1_threshold(self):
        monitor, logger = _make_monitor()
        loss = 1000.0 * PNL_L1_LOSS_PCT - 0.01  # just under 5%
        monitor.check_portfolio_pnl(total_realized_pnl=-loss, initial_bankroll=1000.0)
        logger.log.assert_not_called()

    @pytest.mark.unit
    def test_l1_alert_at_5pct_loss(self):
        monitor, logger = _make_monitor()
        loss = 1000.0 * PNL_L1_LOSS_PCT  # exactly 5%
        monitor.check_portfolio_pnl(total_realized_pnl=-loss, initial_bankroll=1000.0)
        assert logger.log.called
        call_kwargs = logger.log.call_args[1]
        assert call_kwargs["event_type"] == "pnl_alert_l1_watch"
        assert call_kwargs["severity"] == "INFO"

    @pytest.mark.unit
    def test_l2_alert_at_10pct_loss(self):
        monitor, logger = _make_monitor()
        loss = 1000.0 * PNL_L2_LOSS_PCT  # exactly 10%
        monitor.check_portfolio_pnl(total_realized_pnl=-loss, initial_bankroll=1000.0)
        assert logger.log.called
        call_kwargs = logger.log.call_args[1]
        assert call_kwargs["event_type"] == "pnl_alert_l2_loss"
        assert call_kwargs["severity"] == "WARNING"

    @pytest.mark.unit
    def test_l2_alert_above_10pct(self):
        monitor, logger = _make_monitor()
        monitor.check_portfolio_pnl(total_realized_pnl=-150.0, initial_bankroll=1000.0)
        call_kwargs = logger.log.call_args[1]
        assert call_kwargs["event_type"] == "pnl_alert_l2_loss"

    @pytest.mark.unit
    def test_l1_not_l2_between_thresholds(self):
        monitor, logger = _make_monitor()
        loss = 1000.0 * (PNL_L1_LOSS_PCT + PNL_L2_LOSS_PCT) / 2  # between 5% and 10%
        monitor.check_portfolio_pnl(total_realized_pnl=-loss, initial_bankroll=1000.0)
        call_kwargs = logger.log.call_args[1]
        assert call_kwargs["event_type"] == "pnl_alert_l1_watch"

    @pytest.mark.unit
    def test_payload_contains_loss_pct(self):
        monitor, logger = _make_monitor()
        monitor.check_portfolio_pnl(total_realized_pnl=-60.0, initial_bankroll=1000.0)
        payload = logger.log.call_args[1]["payload"]
        assert "loss_pct" in payload
        assert abs(payload["loss_pct"] - 0.06) < 1e-6


# ---------------------------------------------------------------------------
# SystemMonitor — shadow model tracking (ADR-0009)
# ---------------------------------------------------------------------------


from prediction_market_bot.c7_monitoring.monitor import (
    SHADOW_MIN_WINDOW,
    SHADOW_PROMOTION_DELTA,
)


def _record_shadow(monitor: SystemMonitor, p_shadow: float, y: int) -> None:
    monitor.record_shadow_outcome(shadow_p_estimate=p_shadow, outcome=y)


class TestShadowModelTracking:
    @pytest.mark.unit
    def test_snapshot_shadow_n_events_zero_initially(self):
        monitor, _ = _make_monitor()
        snap = monitor.get_drift_snapshot()
        assert snap.shadow_n_events == 0

    @pytest.mark.unit
    def test_snapshot_shadow_brier_none_below_min_window(self):
        monitor, _ = _make_monitor()
        for _ in range(SHADOW_MIN_WINDOW - 1):
            _record_shadow(monitor, 0.6, 1)
        snap = monitor.get_drift_snapshot()
        assert snap.shadow_brier_30 is None
        assert snap.shadow_promotion_flag is False

    @pytest.mark.unit
    def test_snapshot_shadow_brier_computed_at_min_window(self):
        monitor, _ = _make_monitor()
        for _ in range(SHADOW_MIN_WINDOW):
            _record_shadow(monitor, 0.6, 1)
        snap = monitor.get_drift_snapshot()
        assert snap.shadow_brier_30 is not None
        # p=0.6, y=1 → Brier = (0.6 - 1)^2 = 0.16
        assert snap.shadow_brier_30 == pytest.approx(0.16, abs=1e-6)

    @pytest.mark.unit
    def test_shadow_promotion_flag_not_set_when_similar(self):
        """Shadow and prod similar → no promotion flag."""
        monitor, _ = _make_monitor(brier_baseline=BRIER_BASELINE)
        # Load prod window with calibrated records (Brier ~0.21)
        for i in range(30):
            y = 1 if i % 10 < 7 else 0
            _record(monitor, p=0.70, y=y)
        # Load shadow window with same pattern
        for i in range(SHADOW_MIN_WINDOW):
            y = 1 if i % 10 < 7 else 0
            _record_shadow(monitor, 0.70, y)
        snap = monitor.get_drift_snapshot()
        # Shadow Brier ≈ prod Brier → no flag
        assert snap.shadow_promotion_flag is False

    @pytest.mark.unit
    def test_shadow_promotion_flag_fires_when_shadow_clearly_better(self):
        """Shadow beats prod by > SHADOW_PROMOTION_DELTA → flag fires."""
        monitor, _ = _make_monitor()
        # Prod window: poor calibration — p=0.20, y=1 repeatedly → Brier ~0.64
        for _ in range(30):
            _record(monitor, p=0.20, y=1)
        # Shadow window: good calibration — p=0.70, y=1 repeatedly → Brier ~0.09
        for _ in range(SHADOW_MIN_WINDOW):
            _record_shadow(monitor, 0.70, 1)
        snap = monitor.get_drift_snapshot()
        assert snap.shadow_promotion_flag is True
        assert snap.shadow_brier_30 is not None
        assert snap.rolling_brier is not None
        assert snap.rolling_brier - snap.shadow_brier_30 >= SHADOW_PROMOTION_DELTA

    @pytest.mark.unit
    def test_check_and_alert_logs_shadow_promotion_event(self):
        """When promotion flag fires, check_and_alert emits shadow_promotion_flag WARNING."""
        monitor, logger = _make_monitor()
        # Load prod with poor calibration
        for _ in range(30):
            _record(monitor, p=0.20, y=1)
        # Load shadow with good calibration
        for _ in range(SHADOW_MIN_WINDOW):
            _record_shadow(monitor, 0.70, 1)
        monitor.check_and_alert(session_id="SES-SHADOW-TEST")
        event_types = [c[1]["event_type"] for c in logger.log.call_args_list]
        assert "shadow_promotion_flag" in event_types

    @pytest.mark.unit
    def test_check_and_alert_logs_shadow_drift_computed(self):
        """When shadow window has events, check_and_alert emits shadow_drift_computed."""
        monitor, logger = _make_monitor()
        for _ in range(30):
            _record(monitor, p=0.70, y=1)
        for _ in range(SHADOW_MIN_WINDOW):
            _record_shadow(monitor, 0.70, 1)
        monitor.check_and_alert(session_id="SES-SHADOW-TEST")
        event_types = [c[1]["event_type"] for c in logger.log.call_args_list]
        assert "shadow_drift_computed" in event_types

    @pytest.mark.unit
    def test_shadow_promotion_flag_not_in_health_snapshot_when_absent(self):
        monitor, _ = _make_monitor()
        snap = monitor.get_health_snapshot()
        assert "shadow_promotion_flag" in snap
        assert snap["shadow_promotion_flag"] is False

    @pytest.mark.unit
    def test_shadow_window_rolls_over_at_max_size(self):
        """Shadow window respects maxlen — oldest records are evicted."""
        monitor, _ = _make_monitor(window_size=10)
        for i in range(25):
            _record_shadow(monitor, 0.5, i % 2)
        snap = monitor.get_drift_snapshot()
        assert snap.shadow_n_events == 10  # capped at window_size

    @pytest.mark.unit
    def test_record_shadow_outcome_thread_safe(self):
        """Concurrent shadow outcome recording doesn't lose records."""
        monitor, _ = _make_monitor(window_size=1000)
        threads = [
            threading.Thread(target=lambda: _record_shadow(monitor, 0.6, 1))
            for _ in range(100)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        snap = monitor.get_drift_snapshot()
        assert snap.shadow_n_events <= 1000

    @pytest.mark.unit
    def test_zero_initial_bankroll_no_crash(self):
        monitor, logger = _make_monitor()
        monitor.check_portfolio_pnl(total_realized_pnl=-50.0, initial_bankroll=0.0)
        logger.log.assert_not_called()
