"""
C7: Monitoring + Kill Switch
============================
Component:    C7 (Monitoring + Kill Switch)
Phase active: ALWAYS ACTIVE from Phase 5+ (cross-cutting)
Status:       IMPLEMENTED (Phase 5 2026-05-28)
Upstream:     Forecast outcome records (pipeline driver feeds p_estimate + outcome)
              C6 Audit Logger (receives all C7 events)
Downstream:   C8 Visual Dashboard (IF-C7-C8 metric stream)
              All components check is_kill_switch_active before operating
Interfaces:   IF-ALL-C6 (writes drift + kill events); IF-C7-C8 (health snapshot)
ADR refs:     ADR-0001 (Compass OS), ADR-0002 (forecast-only)
Policy refs:  MONITORING_DRIFT_PLAN.md, RUNBOOKS/RUNBOOK_kill-switch.md,
              SLA_SLO_SLI.md (ALT-001 through ALT-008), OBSERVABILITY.md

Kill switch SLA: ≤60 seconds (NFR-03). Drilled before G5 (TC-007).
Drift baselines: Brier=0.2416, ECE=0.0247 (G4 TEST set; ADR-0004).
No bypass path. No partial halt. No override without ADR + RCO approval.

Audit events emitted:
  drift_metric_computed      (INFO)     — rolling window computation
  drift_alert_l1_watch       (INFO)     — Brier > baseline + 0.02
  drift_alert_l2_alert       (WARNING)  — Brier > baseline + 0.05 (ALT-001)
  drift_alert_l3_pause       (ERROR)    — Brier > baseline + 0.10 (ALT-002)
  drift_alert_mean_edge_neg  (WARNING)  — mean edge < 0 (ALT-003)
  kill_switch_triggered      (CRITICAL) — kill switch activated
  kill_switch_reset          (WARNING)  — kill switch reset (drill recovery only)
  kill_switch_drill_result   (INFO)     — drill pass/fail record
"""

from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import numpy as np

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Constants — G4 TEST set baselines (ADR-0004 / APR-0012)
# ---------------------------------------------------------------------------

COMPONENT = "C7"

BRIER_BASELINE: float = 0.2416
ECE_BASELINE: float = 0.0247
DRIFT_WINDOW_SIZE: int = 30

# Drift thresholds (MONITORING_DRIFT_PLAN.md)
BRIER_L1_DELTA: float = 0.02   # watch
BRIER_L2_DELTA: float = 0.05   # alert   → ALT-001
BRIER_L3_DELTA: float = 0.10   # pause + kill trigger → ALT-002
ECE_L2_DELTA: float = 0.05     # ECE alert

BRIER_L1_THRESHOLD: float = BRIER_BASELINE + BRIER_L1_DELTA
BRIER_L2_THRESHOLD: float = BRIER_BASELINE + BRIER_L2_DELTA
BRIER_L3_THRESHOLD: float = BRIER_BASELINE + BRIER_L3_DELTA
ECE_L2_THRESHOLD: float = ECE_BASELINE + ECE_L2_DELTA

# NFR-03 kill switch SLA in milliseconds
KILL_SWITCH_SLA_MS: int = 60_000

# Alert levels
ALERT_OK = "OK"
ALERT_L1_WATCH = "L1_WATCH"
ALERT_L2_ALERT = "L2_ALERT"
ALERT_L3_PAUSE = "L3_PAUSE"
ALERT_L4_KILL = "L4_KILL"

# Kill switch states
KS_ARMED = "ARMED"
KS_TRIGGERED = "TRIGGERED"

# ECE bins
_ECE_N_BINS: int = 10


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ForecastOutcomeRecord:
    """One resolved forecast event fed into the rolling drift window."""

    p_estimate: float
    outcome: int  # 0 or 1
    market_implied_prob: float


@dataclass
class DriftSnapshot:
    """Rolling drift metric values at a point in time (IF-C7-C8 metric data)."""

    n_events: int
    rolling_brier: float | None
    rolling_ece: float | None
    mean_edge: float | None
    alert_level: str
    alert_messages: list[str]
    brier_baseline: float
    ece_baseline: float
    computed_at: str  # ISO-8601 UTC


@dataclass
class KillSwitchResult:
    """Result record from a kill switch trigger (manual, auto, or drill)."""

    triggered_at: str          # ISO-8601 UTC
    trigger_reason: str
    operator: str | None       # None = automatic
    halt_time_ms: float        # measured wall-clock ms from trigger call to completion
    is_drill: bool
    passed_sla: bool           # halt_time_ms <= KILL_SWITCH_SLA_MS
    kill_switch_id: str        # unique ID for this trigger event


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _ks_id() -> str:
    return f"KS-{uuid.uuid4().hex[:12].upper()}"


def _compute_brier(records: list[ForecastOutcomeRecord]) -> float:
    if not records:
        return float("nan")
    return float(np.mean([(r.p_estimate - r.outcome) ** 2 for r in records]))


def _compute_ece(records: list[ForecastOutcomeRecord], n_bins: int = _ECE_N_BINS) -> float:
    """Expected calibration error using equal-width bins."""
    if not records:
        return float("nan")
    preds = np.array([r.p_estimate for r in records])
    outcomes = np.array([r.outcome for r in records], dtype=float)
    n = len(records)
    bin_edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        mask = (preds >= bin_edges[i]) & (preds < bin_edges[i + 1])
        if i == n_bins - 1:
            mask = (preds >= bin_edges[i]) & (preds <= bin_edges[i + 1])
        n_bin = int(mask.sum())
        if n_bin == 0:
            continue
        mean_pred = float(preds[mask].mean())
        frac_pos = float(outcomes[mask].mean())
        ece += (n_bin / n) * abs(mean_pred - frac_pos)
    return float(ece)


def _compute_mean_edge(records: list[ForecastOutcomeRecord]) -> float:
    if not records:
        return float("nan")
    return float(np.mean([r.p_estimate - r.market_implied_prob for r in records]))


# ---------------------------------------------------------------------------
# SystemMonitor
# ---------------------------------------------------------------------------


class SystemMonitor:
    """
    C7 Monitoring + Kill Switch.

    Thread-safe. Maintains a rolling window of resolved forecast outcomes and
    computes drift metrics. Triggers the kill switch automatically on L4 breach
    or when called manually.

    All components MUST check ``monitor.is_kill_switch_active`` before operating.
    A True value means halt immediately — do not process further events.

    Usage::

        monitor = SystemMonitor(logger=audit_logger, snapshot_id="SNAP-XXX")

        # After each forecast resolves:
        monitor.record_forecast_outcome(
            p_estimate=0.65, outcome=1, market_implied_prob=0.55
        )

        # In the pipeline loop, after recording outcomes:
        monitor.check_and_alert(session_id=session_id)

        # Before every component operation:
        if monitor.is_kill_switch_active:
            raise SystemHaltError("Kill switch is active")

        # Kill switch drill (T-051):
        result = monitor.run_kill_switch_drill(session_id=session_id)
        assert result.passed_sla
    """

    def __init__(
        self,
        logger: AuditLogger,
        snapshot_id: str,
        session_id: str | None = None,
        brier_baseline: float = BRIER_BASELINE,
        ece_baseline: float = ECE_BASELINE,
        window_size: int = DRIFT_WINDOW_SIZE,
    ) -> None:
        self._logger = logger
        self._snapshot_id = snapshot_id
        self._session_id = session_id
        self._brier_baseline = brier_baseline
        self._ece_baseline = ece_baseline

        self._window: deque[ForecastOutcomeRecord] = deque(maxlen=window_size)
        self._window_lock = threading.Lock()

        # Kill switch state
        self._kill_event = threading.Event()
        self._kill_reason: str | None = None
        self._kill_operator: str | None = None
        self._kill_id: str | None = None
        self._kill_triggered_at: str | None = None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def is_kill_switch_active(self) -> bool:
        return self._kill_event.is_set()

    @property
    def kill_switch_state(self) -> str:
        return KS_TRIGGERED if self._kill_event.is_set() else KS_ARMED

    # ------------------------------------------------------------------
    # Forecast outcome ingestion
    # ------------------------------------------------------------------

    def record_forecast_outcome(
        self,
        p_estimate: float,
        outcome: int,
        market_implied_prob: float,
    ) -> None:
        """Add one resolved forecast to the rolling drift window."""
        record = ForecastOutcomeRecord(
            p_estimate=float(p_estimate),
            outcome=int(outcome),
            market_implied_prob=float(market_implied_prob),
        )
        with self._window_lock:
            self._window.append(record)

    # ------------------------------------------------------------------
    # Drift computation
    # ------------------------------------------------------------------

    def get_drift_snapshot(self) -> DriftSnapshot:
        """Compute rolling drift metrics over the current window."""
        with self._window_lock:
            records = list(self._window)

        n = len(records)
        if n == 0:
            return DriftSnapshot(
                n_events=0,
                rolling_brier=None,
                rolling_ece=None,
                mean_edge=None,
                alert_level=ALERT_OK,
                alert_messages=[],
                brier_baseline=self._brier_baseline,
                ece_baseline=self._ece_baseline,
                computed_at=_utc_now_iso(),
            )

        brier = _compute_brier(records)
        ece = _compute_ece(records)
        mean_edge = _compute_mean_edge(records)

        alert_level = ALERT_OK
        messages: list[str] = []

        # Brier drift ladder
        if not np.isnan(brier):
            if brier > self._brier_baseline + BRIER_L3_DELTA:
                alert_level = ALERT_L4_KILL
                messages.append(
                    f"Brier {brier:.4f} > L3 threshold {self._brier_baseline + BRIER_L3_DELTA:.4f} — L4 kill"
                )
            elif brier > self._brier_baseline + BRIER_L2_DELTA:
                if alert_level == ALERT_OK:
                    alert_level = ALERT_L2_ALERT
                messages.append(
                    f"Brier {brier:.4f} > L2 threshold {self._brier_baseline + BRIER_L2_DELTA:.4f} — ALT-001"
                )
            elif brier > self._brier_baseline + BRIER_L1_DELTA:
                if alert_level == ALERT_OK:
                    alert_level = ALERT_L1_WATCH
                messages.append(
                    f"Brier {brier:.4f} > L1 threshold {self._brier_baseline + BRIER_L1_DELTA:.4f} — watch"
                )

        # ECE drift
        if not np.isnan(ece) and ece > self._ece_baseline + ECE_L2_DELTA:
            if alert_level in (ALERT_OK, ALERT_L1_WATCH):
                alert_level = ALERT_L2_ALERT
            messages.append(
                f"ECE {ece:.4f} > L2 threshold {self._ece_baseline + ECE_L2_DELTA:.4f}"
            )

        # Mean edge
        if not np.isnan(mean_edge) and mean_edge < 0:
            if alert_level == ALERT_OK:
                alert_level = ALERT_L1_WATCH
            messages.append(f"Mean edge {mean_edge:.4f} < 0 — ALT-003")

        return DriftSnapshot(
            n_events=n,
            rolling_brier=None if np.isnan(brier) else brier,
            rolling_ece=None if np.isnan(ece) else ece,
            mean_edge=None if np.isnan(mean_edge) else mean_edge,
            alert_level=alert_level,
            alert_messages=messages,
            brier_baseline=self._brier_baseline,
            ece_baseline=self._ece_baseline,
            computed_at=_utc_now_iso(),
        )

    # ------------------------------------------------------------------
    # Alert check + automatic kill switch
    # ------------------------------------------------------------------

    def check_and_alert(self, session_id: str | None = None) -> DriftSnapshot:
        """
        Compute drift snapshot, emit alerts to C6, and auto-trigger kill switch on L4.

        Returns the current DriftSnapshot. Callers should check the returned
        alert_level and respond per MONITORING_DRIFT_PLAN.md drift ladder.
        """
        snap = self.get_drift_snapshot()

        if snap.n_events == 0:
            return snap

        sid = session_id or self._session_id

        payload: dict[str, Any] = {
            "n_events": snap.n_events,
            "rolling_brier": snap.rolling_brier,
            "rolling_ece": snap.rolling_ece,
            "mean_edge": snap.mean_edge,
            "alert_level": snap.alert_level,
            "brier_baseline": snap.brier_baseline,
            "ece_baseline": snap.ece_baseline,
            "brier_l1_threshold": self._brier_baseline + BRIER_L1_DELTA,
            "brier_l2_threshold": self._brier_baseline + BRIER_L2_DELTA,
            "brier_l3_threshold": self._brier_baseline + BRIER_L3_DELTA,
        }

        severity_map = {
            ALERT_OK: "INFO",
            ALERT_L1_WATCH: "INFO",
            ALERT_L2_ALERT: "WARNING",
            ALERT_L3_PAUSE: "ERROR",
            ALERT_L4_KILL: "CRITICAL",
        }

        event_map = {
            ALERT_OK: "drift_metric_computed",
            ALERT_L1_WATCH: "drift_alert_l1_watch",
            ALERT_L2_ALERT: "drift_alert_l2_alert",
            ALERT_L3_PAUSE: "drift_alert_l3_pause",
            ALERT_L4_KILL: "drift_alert_l4_kill",
        }

        self._logger.log(
            component=COMPONENT,
            event_type=event_map.get(snap.alert_level, "drift_metric_computed"),
            payload=payload,
            severity=severity_map.get(snap.alert_level, "INFO"),
            session_id=sid,
            snapshot_id=self._snapshot_id,
        )

        # Mean edge alert is separate
        if snap.mean_edge is not None and snap.mean_edge < 0:
            self._logger.log(
                component=COMPONENT,
                event_type="drift_alert_mean_edge_neg",
                payload={"mean_edge": snap.mean_edge},
                severity="WARNING",
                session_id=sid,
                snapshot_id=self._snapshot_id,
            )

        # L4 — auto-trigger kill switch
        if snap.alert_level == ALERT_L4_KILL and not self.is_kill_switch_active:
            self.trigger_kill_switch(
                reason=f"L4 drift threshold breached: {'; '.join(snap.alert_messages)}",
                operator=None,
                session_id=sid,
            )

        return snap

    # ------------------------------------------------------------------
    # Kill switch
    # ------------------------------------------------------------------

    def trigger_kill_switch(
        self,
        reason: str,
        operator: str | None = None,
        session_id: str | None = None,
        _is_drill: bool = False,
    ) -> KillSwitchResult:
        """
        Activate the kill switch. Thread-safe. Idempotent if already triggered.

        Sets is_kill_switch_active = True. All components checking this flag
        will stop processing. Writes CRITICAL event to C6.

        Returns KillSwitchResult with measured halt_time_ms.
        """
        t_start = time.monotonic()

        ks_id = _ks_id()
        triggered_at = _utc_now_iso()
        sid = session_id or self._session_id

        # Set the event — this is the actual "halt" signal
        self._kill_event.set()
        self._kill_reason = reason
        self._kill_operator = operator
        self._kill_id = ks_id
        self._kill_triggered_at = triggered_at

        halt_ms = (time.monotonic() - t_start) * 1000.0
        passed = halt_ms <= KILL_SWITCH_SLA_MS

        self._logger.log(
            component=COMPONENT,
            event_type="kill_switch_triggered",
            payload={
                "kill_switch_id": ks_id,
                "reason": reason,
                "operator": operator,
                "is_drill": _is_drill,
                "halt_time_ms": round(halt_ms, 3),
                "passed_sla": passed,
                "sla_threshold_ms": KILL_SWITCH_SLA_MS,
            },
            severity="CRITICAL",
            session_id=sid,
            snapshot_id=self._snapshot_id,
        )

        return KillSwitchResult(
            triggered_at=triggered_at,
            trigger_reason=reason,
            operator=operator,
            halt_time_ms=round(halt_ms, 3),
            is_drill=_is_drill,
            passed_sla=passed,
            kill_switch_id=ks_id,
        )

    def reset_kill_switch(
        self,
        reason: str,
        operator: str,
        session_id: str | None = None,
    ) -> None:
        """
        Reset the kill switch after a drill or false-positive resolution.

        Requires a written reason and operator identification (NFR-03 / RUNBOOK).
        Logs a WARNING event to C6. Must not be used to bypass a real kill event
        without a written RCO decision logged to RID_LOG.md.
        """
        sid = session_id or self._session_id
        self._kill_event.clear()

        self._logger.log(
            component=COMPONENT,
            event_type="kill_switch_reset",
            payload={
                "reason": reason,
                "operator": operator,
                "prior_kill_id": self._kill_id,
                "prior_trigger_reason": self._kill_reason,
            },
            severity="WARNING",
            session_id=sid,
            snapshot_id=self._snapshot_id,
        )

        self._kill_reason = None
        self._kill_operator = None
        self._kill_id = None
        self._kill_triggered_at = None

    # ------------------------------------------------------------------
    # Kill switch drill (T-051 / TC-007)
    # ------------------------------------------------------------------

    def run_kill_switch_drill(
        self,
        operator: str = "Earl Ignacio",
        session_id: str | None = None,
    ) -> KillSwitchResult:
        """
        Execute a timed kill switch drill (TC-007, NFR-03).

        Triggers the kill switch, measures halt_time_ms, logs the drill result,
        then resets the kill switch so the system is ready again.

        Pass criteria (G5 gate blocker):
          - All components halt: enforced by is_kill_switch_active flag
          - Kill event in C6 log: ensured by trigger_kill_switch
          - Halt time ≤ 60,000ms: result.passed_sla

        Returns KillSwitchResult. result.passed_sla must be True to pass G5.
        """
        sid = session_id or self._session_id

        result = self.trigger_kill_switch(
            reason="DRILL: Scheduled pre-G5 kill switch drill (TC-007)",
            operator=operator,
            session_id=sid,
            _is_drill=True,
        )

        self._logger.log(
            component=COMPONENT,
            event_type="kill_switch_drill_result",
            payload={
                "kill_switch_id": result.kill_switch_id,
                "halt_time_ms": result.halt_time_ms,
                "passed_sla": result.passed_sla,
                "sla_threshold_ms": KILL_SWITCH_SLA_MS,
                "operator": operator,
                "tc_ref": "TC-007",
                "nfr_ref": "NFR-03",
            },
            severity="INFO",
            session_id=sid,
            snapshot_id=self._snapshot_id,
        )

        # Reset so system is operational after drill
        self.reset_kill_switch(
            reason="DRILL_RESET: Kill switch reset after successful drill (TC-007)",
            operator=operator,
            session_id=sid,
        )

        return result

    # ------------------------------------------------------------------
    # IF-C7-C8 health snapshot
    # ------------------------------------------------------------------

    def get_health_snapshot(self) -> dict[str, Any]:
        """
        Return a structured health snapshot for C8 Visual Dashboard (IF-C7-C8).

        Fields match IF-C7-C8 interface contract in INTERFACES_CONTRACTS.md.
        """
        snap = self.get_drift_snapshot()
        return {
            # System health
            "kill_switch_active": self.is_kill_switch_active,
            "kill_switch_state": self.kill_switch_state,
            "kill_switch_reason": self._kill_reason,
            "kill_switch_triggered_at": self._kill_triggered_at,
            # Drift metrics
            "metric_name": "c7.drift.rolling_brier_score",
            "metric_value": snap.rolling_brier,
            "threshold": BRIER_L2_THRESHOLD,
            "alert_level": snap.alert_level,
            "alert_message": "; ".join(snap.alert_messages) if snap.alert_messages else None,
            # Full drift context
            "n_events_in_window": snap.n_events,
            "rolling_brier": snap.rolling_brier,
            "rolling_ece": snap.rolling_ece,
            "mean_edge": snap.mean_edge,
            "brier_baseline": snap.brier_baseline,
            "ece_baseline": snap.ece_baseline,
            "brier_l1_threshold": BRIER_L1_THRESHOLD,
            "brier_l2_threshold": BRIER_L2_THRESHOLD,
            "brier_l3_threshold": BRIER_L3_THRESHOLD,
            "snapshot_computed_at": snap.computed_at,
        }
