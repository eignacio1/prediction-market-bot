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
ADR refs:     ADR-0001 (Compass OS), ADR-0002 (forecast-only), ADR-0009 (shadow model)
Policy refs:  MONITORING_DRIFT_PLAN.md, RUNBOOKS/RUNBOOK_kill-switch.md,
              SLA_SLO_SLI.md (ALT-001 through ALT-008), OBSERVABILITY.md

Kill switch SLA: ≤60 seconds (NFR-03). Drilled before G5 (TC-007).
Drift baselines: NBA Brier=0.2416, ECE=0.0247 (G4 TEST set; ADR-0004).
           MLB Brier=0.2190, ECE=0.0680 (n=261 resolved paper bets; ADR-0046/GG-044).
No bypass path. No partial halt. No override without ADR + RCO approval.

Shadow model tracking (ADR-0009):
  Separate _shadow_window tracks resolved shadow outcomes independently.
  shadow_promotion_flag fires when shadow_brier_30 <= prod_brier - 0.005
  over >= 30 resolved events. Flag is informational — no auto-promotion.
  Promotion requires operator review + ADR-0010 (DS sign-off).
  Wire via record_shadow_outcome() from resolve pipeline (T-121).

Audit events emitted:
  drift_metric_computed      (INFO)     — rolling window computation
  drift_alert_l1_watch       (INFO)     — Brier > baseline + 0.02
  drift_alert_l2_alert       (WARNING)  — Brier > baseline + 0.05 (ALT-001)
  drift_alert_l3_pause       (ERROR)    — Brier > baseline + 0.10 (ALT-002)
  drift_alert_mean_edge_neg  (WARNING)  — mean edge < 0 (ALT-003)
  pnl_alert_l1_watch         (INFO)     — realized loss ≥ 5% of initial bankroll (KI-012)
  pnl_alert_l2_loss          (WARNING)  — realized loss ≥ 10% of initial bankroll (KI-012)
  kill_switch_triggered      (CRITICAL) — kill switch activated
  kill_switch_reset          (WARNING)  — kill switch reset (drill recovery only)
  kill_switch_drill_result   (INFO)     — drill pass/fail record
  shadow_drift_computed      (INFO)     — shadow Brier rolling window (ADR-0009)
  shadow_promotion_flag      (WARNING)  — shadow beats prod by >= 0.005 over 30+ events (ADR-0009)
  band_monitor_anti_predictive_alarm (WARNING) — per-band Fisher-test ANTI_PREDICTIVE
                                        verdict from scripts/run_band_monitor.py (T-341/GG-099)
  band_monitor_calibration_alarm     (WARNING) — per-band calibration slope CI excludes
                                        1.0 from scripts/run_band_monitor.py (T-341)
  stale_open_position_alarm  (WARNING)  — open position older than staleness threshold,
                                        unresolved (GG-125/T-379, ops failure mode #4,
                                        STRATEGIC_ANALYSIS_2026-07-29.md §F)
  failed_order_rate_alarm    (WARNING)  — pool's failed-Kalshi-order fraction exceeds
                                        threshold (GG-125/T-379, ops failure mode #5,
                                        STRATEGIC_ANALYSIS_2026-07-29.md §F)
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
from prediction_market_bot.c7_monitoring.semantic_contracts import (
    SemanticContractMonitor,
    SemanticHealthState,
)

# ---------------------------------------------------------------------------
# Constants — G4 TEST set baselines (ADR-0004 / APR-0012)
# ---------------------------------------------------------------------------

COMPONENT = "C7"

BRIER_BASELINE: float = 0.2416
ECE_BASELINE: float = 0.0247

# MLB-native baselines (ADR-0046, GG-044) — derived from n=261 resolved MLB paper
# positions (t in {1,2}, GG-042 t=3 exclusion applied), NOT the NBA G4 TEST-set
# values above. Pass explicitly at SystemMonitor construction for MLB pipelines
# (run_mlb_paper_trade.py, run_resolve_mlb.py); NBA sites keep the defaults.
BRIER_BASELINE_MLB: float = 0.2190
ECE_BASELINE_MLB: float = 0.0680

DRIFT_WINDOW_SIZE: int = 30

# Drift thresholds (MONITORING_DRIFT_PLAN.md)
BRIER_L1_DELTA: float = 0.02   # watch
BRIER_L2_DELTA: float = 0.05   # alert   → ALT-001
BRIER_L3_DELTA: float = 0.10   # pause new positions (ERROR) → ALT-002
ECE_L2_DELTA: float = 0.05     # ECE alert

# L4 (full kill switch) is NOT a further Brier delta computed by this module.
# Per MONITORING_DRIFT_PLAN.md's ladder table, L4 is driven independently by
# RISK_APPETITE_CONSTRAINTS.md's real kill criteria (MAX_DAILY_LOSS_PCT,
# max_drawdown_pct — enforced in c4_risk_engine/risk.py). Drift alone, however
# severe, halts new positions (L3) — it does not by itself fire the kill
# switch. GG-095 (2026-07-07): a prior bug had this module jump straight from
# L2 to a full auto-triggered kill switch at the L3 delta, skipping the pause
# tier entirely and conflating drift monitoring with the real kill trigger.

BRIER_L1_THRESHOLD: float = BRIER_BASELINE + BRIER_L1_DELTA
BRIER_L2_THRESHOLD: float = BRIER_BASELINE + BRIER_L2_DELTA
BRIER_L3_THRESHOLD: float = BRIER_BASELINE + BRIER_L3_DELTA
ECE_L2_THRESHOLD: float = ECE_BASELINE + ECE_L2_DELTA

# P&L alert thresholds (KI-012; DS sign-off 2026-06-01 T-091)
PNL_L1_LOSS_PCT: float = 0.05   # 5% of initial bankroll → L1 watch (INFO)
PNL_L2_LOSS_PCT: float = 0.10   # 10% of initial bankroll → L2 alert (WARNING)

# Shadow model promotion thresholds (ADR-0009)
SHADOW_PROMOTION_DELTA: float = 0.005  # shadow Brier must beat prod by this margin
SHADOW_MIN_WINDOW: int = 30            # minimum resolved outcomes for promotion comparison

# Ops-alarm thresholds (GG-125/T-379, warn-only, GG-098 discipline). Chosen to
# sit well above normal resolution latency (positions typically settle within
# the existing 48h aged_open grace period — c5_execution/paper_trader.py) and
# well above T4's observed healthy failed-order baseline (~0.5%,
# STRATEGIC_ANALYSIS_2026-07-29.md §F), so routine noise does not fire these.
STALE_OPEN_DAYS_THRESHOLD: int = 7        # open position older than this, still unresolved
FAILED_ORDER_RATE_THRESHOLD: float = 0.05  # 5% — MAIN's observed 10.9% is well above this

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
    # Shadow model fields (ADR-0009)
    shadow_n_events: int = 0
    shadow_brier_30: float | None = None
    shadow_promotion_flag: bool = False


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

        # Shadow model window (ADR-0009) — (shadow_p_estimate, outcome) pairs
        self._shadow_window: deque[tuple[float, int]] = deque(maxlen=window_size)
        self._shadow_lock = threading.Lock()

        # Semantic contract monitor (ADR-0034 Layer 3)
        self._semantic = SemanticContractMonitor(
            logger=logger,
            session_id=session_id or "",
            snapshot_id=snapshot_id,
        )
        self._check_counter: int = 0  # tracks check_and_alert() calls for periodic emission

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
    def semantic_monitor(self) -> SemanticContractMonitor:
        return self._semantic

    def _write_global_flag(self, reason: str) -> None:
        """GG-745: cron/systemd order paths are separate processes and cannot see _kill_event;
        the global flag file is how a C7 trip reaches them (read inside submit_order)."""
        try:
            from prediction_market_bot.c5_execution import kill_switch_state as ksw
            p = ksw.global_flag_path()
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"{_utc_now_iso()} {reason}\n")
            self._wrote_global_flag = True
        except OSError as e:  # never mask the in-memory halt, but say so loudly
            self._logger.log(component=COMPONENT, event_type="kill_switch_flag_write_failed",
                             payload={"error": repr(e)}, severity="CRITICAL",
                             session_id=self._session_id, snapshot_id=self._snapshot_id)

    def _clear_global_flag(self) -> None:
        if getattr(self, "_wrote_global_flag", False):
            try:
                from prediction_market_bot.c5_execution import kill_switch_state as ksw
                ksw.global_flag_path().unlink(missing_ok=True)
                self._wrote_global_flag = False
            except OSError:
                pass

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
        """Add one resolved production forecast to the rolling drift window."""
        record = ForecastOutcomeRecord(
            p_estimate=float(p_estimate),
            outcome=int(outcome),
            market_implied_prob=float(market_implied_prob),
        )
        with self._window_lock:
            self._window.append(record)

    def record_shadow_outcome(
        self,
        shadow_p_estimate: float,
        outcome: int,
    ) -> None:
        """
        Add one resolved shadow forecast to the shadow rolling window (ADR-0009).

        Called from the resolve pipeline (T-121) when a bet resolves, alongside
        record_forecast_outcome(). outcome must be the same game outcome (0/1).
        Shadow window size mirrors the production window.
        """
        with self._shadow_lock:
            self._shadow_window.append((float(shadow_p_estimate), int(outcome)))

    # ------------------------------------------------------------------
    # Drift computation
    # ------------------------------------------------------------------

    def get_drift_snapshot(self) -> DriftSnapshot:
        """Compute rolling drift metrics over the current window."""
        with self._window_lock:
            records = list(self._window)
        with self._shadow_lock:
            shadow_records = list(self._shadow_window)

        # Shadow Brier is independent of production window — compute first
        shadow_brier: float | None = None
        shadow_promotion = False
        n_shadow = len(shadow_records)
        if n_shadow >= SHADOW_MIN_WINDOW:
            shadow_brier = float(np.mean(
                [(p - y) ** 2 for p, y in shadow_records]
            ))

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
                shadow_n_events=n_shadow,
                shadow_brier_30=shadow_brier,
                shadow_promotion_flag=False,
            )

        brier = _compute_brier(records)
        ece = _compute_ece(records)
        mean_edge = _compute_mean_edge(records)

        alert_level = ALERT_OK
        messages: list[str] = []

        # Brier drift ladder
        if not np.isnan(brier):
            if brier > self._brier_baseline + BRIER_L3_DELTA:
                alert_level = ALERT_L3_PAUSE
                messages.append(
                    f"Brier {brier:.4f} > L3 threshold {self._brier_baseline + BRIER_L3_DELTA:.4f} — L3 pause (ALT-002)"
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

        # Shadow promotion check — requires both prod and shadow Brier to be valid
        if shadow_brier is not None and not np.isnan(brier):
            if shadow_brier <= brier - SHADOW_PROMOTION_DELTA:
                shadow_promotion = True
                messages.append(
                    f"Shadow Brier {shadow_brier:.4f} beats prod {brier:.4f} "
                    f"by {brier - shadow_brier:.4f} >= {SHADOW_PROMOTION_DELTA} "
                    f"over {n_shadow} events — ADR-0010 review required"
                )

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
            shadow_n_events=n_shadow,
            shadow_brier_30=shadow_brier,
            shadow_promotion_flag=shadow_promotion,
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

        # Periodic semantic health emission (every 10 calls)
        self._check_counter += 1
        if self._check_counter % 10 == 0:
            self._semantic.emit_health_snapshot()

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

        # L4 — auto-trigger kill switch.
        # get_drift_snapshot() no longer sets ALERT_L4_KILL from Brier drift alone
        # (GG-095 fix, 2026-07-07) — that path now stops at ALERT_L3_PAUSE. This
        # branch is retained for a future caller that reflects risk.py's
        # independently-triggered drawdown/daily-loss kill (the real L4, per
        # RISK_APPETITE_CONSTRAINTS.md) back into a DriftSnapshot for a unified
        # C8 view; it does not fire from this module's own computation today.
        if snap.alert_level == ALERT_L4_KILL and not self.is_kill_switch_active:
            self.trigger_kill_switch(
                reason=f"L4 drift threshold breached: {'; '.join(snap.alert_messages)}",
                operator=None,
                session_id=sid,
            )

        # Shadow model promotion flag (ADR-0009) — informational, no auto-action
        if snap.shadow_n_events > 0:
            self._logger.log(
                component=COMPONENT,
                event_type="shadow_drift_computed",
                payload={
                    "shadow_n_events": snap.shadow_n_events,
                    "shadow_brier_30": snap.shadow_brier_30,
                    "prod_brier": snap.rolling_brier,
                    "shadow_promotion_flag": snap.shadow_promotion_flag,
                },
                severity="INFO",
                session_id=sid,
                snapshot_id=self._snapshot_id,
            )
        if snap.shadow_promotion_flag:
            self._logger.log(
                component=COMPONENT,
                event_type="shadow_promotion_flag",
                payload={
                    "shadow_brier_30": snap.shadow_brier_30,
                    "prod_brier": snap.rolling_brier,
                    "delta": (
                        round(snap.rolling_brier - snap.shadow_brier_30, 4)
                        if snap.rolling_brier is not None and snap.shadow_brier_30 is not None
                        else None
                    ),
                    "shadow_n_events": snap.shadow_n_events,
                    "promotion_threshold": SHADOW_PROMOTION_DELTA,
                    "action_required": "Operator review + ADR-0010 required before promotion",
                },
                severity="WARNING",
                session_id=sid,
                snapshot_id=self._snapshot_id,
            )

        return snap

    # ------------------------------------------------------------------
    # Portfolio P&L monitoring (KI-012 / T-091)
    # ------------------------------------------------------------------

    def check_portfolio_pnl(
        self,
        total_realized_pnl: float,
        initial_bankroll: float,
        session_id: str | None = None,
    ) -> None:
        """Emit C6 alert if realized P&L loss exceeds 5% (L1) or 10% (L2) of initial bankroll."""
        if initial_bankroll <= 0:
            return
        loss_pct = -total_realized_pnl / initial_bankroll
        if loss_pct < PNL_L1_LOSS_PCT:
            return
        sid = session_id or self._session_id
        payload: dict[str, Any] = {
            "total_realized_pnl": total_realized_pnl,
            "initial_bankroll": initial_bankroll,
            "loss_pct": round(loss_pct, 4),
            "l1_threshold_pct": PNL_L1_LOSS_PCT,
            "l2_threshold_pct": PNL_L2_LOSS_PCT,
        }
        if loss_pct >= PNL_L2_LOSS_PCT:
            self._logger.log(
                component=COMPONENT,
                event_type="pnl_alert_l2_loss",
                payload=payload,
                severity="WARNING",
                session_id=sid,
                snapshot_id=self._snapshot_id,
            )
        else:
            self._logger.log(
                component=COMPONENT,
                event_type="pnl_alert_l1_watch",
                payload=payload,
                severity="INFO",
                session_id=sid,
                snapshot_id=self._snapshot_id,
            )

    # ------------------------------------------------------------------
    # Band monitor verdict wiring (T-341, GG-099/GG-100/GG-098)
    # ------------------------------------------------------------------

    def report_band_monitor_verdicts(
        self,
        band_results: dict[str, dict[str, Any]],
        session_id: str | None = None,
    ) -> list[str]:
        """
        Wire scripts/run_band_monitor.py's per-band verdicts into C7.

        Mirrors the shadow_promotion_flag pattern (ADR-0009): WARNING severity,
        informational only, never calls trigger_kill_switch(). GG-098 established
        that acting automatically on a band-level signal is itself a failure
        mode — band-level halts remain a human (DS review) decision, always.

        Parameters
        ----------
        band_results:
            The `results` dict returned by run_band_monitor.run_all_bands():
            {band_name: {"verdict": "ANALYZED"|"UNDERPOWERED"|"NO_DATA", ...,
                         "anti_predictive_alarm": bool,
                         "calibration": {"b_excludes_1": bool, ...}}}.
            Bands not in ANALYZED verdict state (UNDERPOWERED/NO_DATA) are
            skipped — GG-098 discipline: no alarm without a real verdict.
        session_id:
            Overrides the monitor's session_id for this emission.

        Returns
        -------
        List of band names for which at least one alarm event was emitted.
        """
        sid = session_id or self._session_id
        alarmed: list[str] = []
        for band, r in band_results.items():
            if r.get("verdict") != "ANALYZED":
                continue
            band_alarmed = False

            if r.get("anti_predictive_alarm"):
                mono = r.get("edge_monotonicity") or {}
                self._logger.log(
                    component=COMPONENT,
                    event_type="band_monitor_anti_predictive_alarm",
                    payload={
                        "band": band,
                        "clean_n": r.get("clean_n"),
                        "fisher_pvalue": mono.get("fisher_pvalue"),
                        "edge_monotonicity_verdict": mono.get("verdict"),
                        "action_required": (
                            "DS review required before any capital/allocation "
                            "decision touches this band (GG-098) — warn-only, "
                            "no auto-halt."
                        ),
                    },
                    severity="WARNING",
                    session_id=sid,
                    snapshot_id=self._snapshot_id,
                )
                band_alarmed = True

            fit = r.get("calibration") or {}
            if fit.get("b_excludes_1"):
                self._logger.log(
                    component=COMPONENT,
                    event_type="band_monitor_calibration_alarm",
                    payload={
                        "band": band,
                        "clean_n": r.get("clean_n"),
                        "slope_b": fit.get("slope_b"),
                        "b_ci": fit.get("b_ci"),
                        "interpretation": fit.get("interpretation"),
                        "action_required": (
                            "Calibration slope CI excludes 1.0 — DS review "
                            "required (warn-only, no auto-halt)."
                        ),
                    },
                    severity="WARNING",
                    session_id=sid,
                    snapshot_id=self._snapshot_id,
                )
                band_alarmed = True

            if band_alarmed:
                alarmed.append(band)
        return alarmed

    # ------------------------------------------------------------------
    # Ops alarms — stale opens + failed-order rate (GG-125/T-379)
    # ------------------------------------------------------------------

    def check_stale_open_positions(
        self,
        open_positions: list[dict[str, Any]],
        pool_label: str,
        stale_days_threshold: int = STALE_OPEN_DAYS_THRESHOLD,
        session_id: str | None = None,
    ) -> int:
        """
        Warn-only alarm: count open positions whose game_date is more than
        stale_days_threshold days in the past and still unresolved.

        Surfaces resolution-pipeline stalls (STRATEGIC_ANALYSIS_2026-07-29.md §F:
        429 T4 / 39 MAIN positions unresolved for weeks) that previously had no
        live alarm — the existing 48h aged_open tagging (paper_trader.py) records
        the condition per-position but nothing rolls it up into a fleet-level
        signal. Log-only, no auto-halt (GG-098).
        """
        now = datetime.now(timezone.utc)
        stale: list[dict[str, Any]] = []
        for pos in open_positions:
            game_date = pos.get("game_date")
            if not game_date:
                continue
            try:
                gd = datetime.strptime(game_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            except ValueError:
                continue
            age_days = (now - gd).total_seconds() / 86400.0
            if age_days > stale_days_threshold:
                stale.append({
                    "position_id": pos.get("position_id"),
                    "player_name": pos.get("player_name"),
                    "game_date": game_date,
                    "age_days": round(age_days, 1),
                    "aged_open": bool(pos.get("aged_open", False)),
                })

        if not stale:
            return 0

        sid = session_id or self._session_id
        self._logger.log(
            component=COMPONENT,
            event_type="stale_open_position_alarm",
            payload={
                "pool": pool_label,
                "stale_count": len(stale),
                "total_open": len(open_positions),
                "stale_days_threshold": stale_days_threshold,
                "oldest_age_days": max(s["age_days"] for s in stale),
                "examples": stale[:5],
                "action_required": (
                    "Resolution-pipeline stall signal — warn-only, no auto-halt (GG-125)."
                ),
            },
            severity="WARNING",
            session_id=sid,
            snapshot_id=self._snapshot_id,
        )
        return len(stale)

    def check_failed_order_rate(
        self,
        all_positions: list[dict[str, Any]],
        pool_label: str,
        rate_threshold: float = FAILED_ORDER_RATE_THRESHOLD,
        session_id: str | None = None,
    ) -> float:
        """
        Warn-only alarm: fraction of positions with a failed Kalshi order status.

        `all_positions` should span open + closed + rejected positions for the
        pool, since a "failed: ..." kalshi_order_status can appear in any of the
        three lists depending on when the position was recorded relative to the
        GG-079/T-234 routing fix (which sends new failures to rejected_positions
        rather than open_positions). Surfaces STRATEGIC_ANALYSIS_2026-07-29.md
        §F's 10.9% MAIN failed-order rate, which had no live threshold before
        this wiring. Log-only, no auto-halt (GG-098).
        """
        total = len(all_positions)
        if total == 0:
            return 0.0

        failed = [
            p for p in all_positions
            if str(p.get("kalshi_order_status", "")).startswith("failed:")
        ]
        rate = len(failed) / total
        if rate < rate_threshold:
            return rate

        sid = session_id or self._session_id
        self._logger.log(
            component=COMPONENT,
            event_type="failed_order_rate_alarm",
            payload={
                "pool": pool_label,
                "failed_count": len(failed),
                "total_count": total,
                "failed_rate": round(rate, 4),
                "rate_threshold": rate_threshold,
                "action_required": (
                    "Elevated Kalshi order failure rate — warn-only, no auto-halt (GG-125)."
                ),
            },
            severity="WARNING",
            session_id=sid,
            snapshot_id=self._snapshot_id,
        )
        return rate

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
        if not _is_drill:
            self._write_global_flag(reason)
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
        self._clear_global_flag()

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
            # Shadow model (ADR-0009)
            "shadow_n_events": snap.shadow_n_events,
            "shadow_brier_30": snap.shadow_brier_30,
            "shadow_promotion_flag": snap.shadow_promotion_flag,
            # Semantic contracts (ADR-0034 Layer 3)
            "semantic_health": self._semantic.get_health_state().__dict__,
        }
