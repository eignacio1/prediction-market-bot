"""
C4: Risk Engine — Kelly Sizing + Hard Limit Enforcement
=======================================================
Component:    C4 (Risk Engine)
Phase active: GATED — Phase 5+ (requires ADR-0004 acceptance + G5 gate passage)
Status:       SKELETON — NOT ACTIVE (Phase 3 2026-05-26)
Upstream:     C3 Forecasting Engine (IF-C3-C4 forecast record)
Downstream:   C5 Execution Engine (IF-C4-C5 approval record)
              C6 Audit Logger (IF-ALL-C6)
Interfaces:   IF-C3-C4 (input); IF-C4-C5 (output)
ADR refs:     ADR-0001 (Compass OS), ADR-0002 (forecast-only),
              ADR-0004 (paper trading gate — PENDING)
Policy refs:  01_SPEC/RISK_APPETITE_CONSTRAINTS.md,
              EXECUTION_ARCHITECTURE.md,
              RUNBOOKS/RUNBOOK_kill-switch.md

PHASE GATE — CRITICAL:
  C4 is DISABLED until ADR-0004 is formally accepted and G5 is signed.
  Calling evaluate_forecast() before the gate is opened will return
  (True, REJECTED) with rejection_reason="phase_gate_not_reached".
  The gate is opened by setting C4_PHASE_GATE_OPEN = True in environment
  (BOT_C4_ACTIVE=true). This is enforced at runtime, not at import time.
  DO NOT set BOT_C4_ACTIVE=true in ENV-01 or ENV-02.

Kelly sizing formula (fractional):
  f* = (p̂ - q̂) / b   for a binary market where b = odds - 1
  For binary YES/NO at price p_market:
    b_yes = (1 - p_market) / p_market     (payout on YES)
    f_yes = (p̂ - (1 - p̂)) / b_yes       (simplified: f_yes = p̂ - p_market)
    f_live = f_yes × kelly_fraction        (fractional Kelly)
  Fractional Kelly (kelly_fraction): TBD at G4. Skeleton uses 0.25.

Hard limits (ADR-0006 — pipeline + Kelly + kill switch are the risk framework):
  MAX_SINGLE_EVENT_EXPOSURE   — max $ per event (caps Kelly output)
  MAX_DAILY_LOSS              — daily stop-loss (KILL_SWITCH trigger)
  MAX_DRAWDOWN_PCT            — portfolio drawdown (KILL_SWITCH trigger)
  MIN_BET_USD (10.0)          — minimum bet floor; sub-floor bets rejected

  NOTE: max_concurrent_positions was deleted (ADR-0006, 2026-06-01).
  Count is the wrong primitive. The pipeline IS the filter. Kelly handles sizing.
  The drawdown kill switch is the backstop. See GOVERNANCE_GAP_LOG.md GG-001.

Kill switch integration (NFR-03):
  If any hard limit is breached:
    → Return approval_status=KILL_SWITCH
    → Caller (C5 or orchestrator) must halt all activity within ≤60s.
  If C6 write fails:
    → Return (False, ...)
    → Caller must treat False as kill switch trigger.

Audit events emitted:
  - risk_eval_start              (INFO)
  - risk_eval_rejected_gate      (INFO) — phase gate not yet open
  - risk_eval_approved           (INFO) — all checks passed
  - risk_eval_rejected           (WARNING) — check failed, no order
  - risk_eval_kill_switch        (CRITICAL) — hard limit breach → halt
  - risk_eval_error              (ERROR) — unhandled exception
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd

from prediction_market_bot.c6_audit_logger.audit_logger import AuditLogger

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPONENT = "C4"

# Environment variable that enables C4 (set by ops after ADR-0004 + G5)
_GATE_ENV_VAR = "BOT_C4_ACTIVE"

# Fractional Kelly multiplier — placeholder until confirmed at G4
# Research evidence suggests 0.25 (quarter-Kelly) as default (Thorp et al.)
DEFAULT_KELLY_FRACTION: float = 0.25

# Minimum edge required to enter a position (even after Kelly sizing)
MIN_EDGE_TO_APPROVE: float = 0.04  # ADR-0020: raised 0.02→0.04; filters sub-threshold NO bets

# Maximum daily loss as a fraction of initial bankroll (ADR-0012).
# 15% fires before the 20% drawdown kill switch — restoring two independent kill switches.
# Recalibrate at G6 when live bankroll is set.
MAX_DAILY_LOSS_PCT: float = 0.15

# Minimum position size in USD. Bets sized below this floor carry negligible
# P&L signal and inflate position counts without contributing evidence.
# Applies in all modes (paper and live). Change requires ADR evidence.
MIN_BET_USD: float = 10.0

# Reserve mandate: ≥40% bankroll uncommitted after T1 batch so T4/T5 have capital
# at game time (ADR-0010). Warning-only at paper scale; blocking at live capital.
RESERVE_MANDATE_PCT: float = 0.40

# Hard limits — confirmed at G4/ADR-0004; count gate deleted per ADR-0006 (2026-06-01)
# Revise all values via new APR at G6 when live bankroll is set.
_HARD_LIMITS: dict[str, float] = {
    "max_single_event_exposure_usd": 500.0,    # $500 per event; caps Kelly output
    "max_drawdown_pct": 0.20,                   # 20% realized drawdown; KILL_SWITCH
    # max_daily_loss_usd removed — replaced by MAX_DAILY_LOSS_PCT (ADR-0012)
}

# Approval status values (IF-C4-C5)
STATUS_APPROVED = "APPROVED"
STATUS_REJECTED = "REJECTED"
STATUS_KILL_SWITCH = "KILL_SWITCH"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _risk_eval_id() -> str:
    return f"RISK-{uuid.uuid4().hex[:12].upper()}"


def _is_gate_open() -> bool:
    """Check if the C4 phase gate is open via environment variable."""
    return os.environ.get(_GATE_ENV_VAR, "").lower() in ("true", "1", "yes")


def _compute_kelly_size(
    p_estimate: float,
    market_implied_prob: float,
    kelly_fraction: float,
    bankroll: float,
) -> float:
    """
    Compute fractional Kelly position size in dollars.

    For a binary market at price p_market (probability units):
      b = (1 - p_market) / p_market   (net odds on YES side)
      f* = (p * b - q) / b            (full Kelly fraction)
        = p - q / b                   (simplified)
        = p - (1-p) * p_market / (1-p_market)
      f_live = f* * kelly_fraction
      size = f_live * bankroll

    Returns 0.0 if Kelly fraction is negative (no edge on this side).
    """
    if market_implied_prob <= 0.0 or market_implied_prob >= 1.0:
        return 0.0

    b = (1.0 - market_implied_prob) / market_implied_prob
    q = 1.0 - p_estimate
    f_star = (p_estimate * b - q) / b  # Full Kelly

    if f_star <= 0.0:
        return 0.0

    f_live = f_star * kelly_fraction
    return float(min(f_live * bankroll, _HARD_LIMITS["max_single_event_exposure_usd"]))


# ---------------------------------------------------------------------------
# RiskEngine
# ---------------------------------------------------------------------------


class RiskEngine:
    """
    C4 Risk Engine — fractional Kelly sizing and hard limit enforcement.

    GATED: Returns REJECTED (phase_gate_not_reached) until BOT_C4_ACTIVE=true.

    Usage (Phase 5+)::

        engine = RiskEngine(
            logger=audit_logger,
            snapshot_id="SNAP-2024-10-01-001",
            bankroll=10000.0,
        )

        ok, approval = engine.evaluate_forecast(
            forecast_record=forecast_row,
            current_daily_loss=0.0,
            session_id=session_id,
        )
        if not ok:
            trigger_kill_switch()

        if approval["approval_status"] == "KILL_SWITCH":
            trigger_kill_switch()
        elif approval["approval_status"] == "APPROVED":
            # pass to C5
            ...

    All evaluate_forecast() calls return (bool, dict) where:
      bool = False only on C6 write failure (triggers kill switch)
      dict follows IF-C4-C5 contract
    """

    def __init__(
        self,
        logger: AuditLogger,
        snapshot_id: str,
        bankroll: float = 10000.0,
        kelly_fraction: float = DEFAULT_KELLY_FRACTION,
        initial_bankroll: float | None = None,
        min_bet_usd: float | None = None,
    ) -> None:
        """
        Parameters
        ----------
        logger:
            Shared AuditLogger (C6) instance.
        snapshot_id:
            DS-01 snapshot anchor.
        bankroll:
            Current simulated or live bankroll in USD.
            Used for Kelly position sizing.
        kelly_fraction:
            Fraction of full Kelly to bet (default 0.25 — quarter Kelly).
            Confirmed at G4; do not change without ADR evidence.
        initial_bankroll:
            Session-start bankroll used to anchor MAX_DAILY_LOSS_PCT threshold
            (ADR-0012). If None, defaults to bankroll. Callers that refresh the
            engine mid-session should pass the original session-start value here
            so the threshold remains stable across the run.
        min_bet_usd:
            Override the global MIN_BET_USD floor. Pass 1.0 for paper-mode T4
            to allow sub-$10 Kelly bets without changing the live floor. If None,
            uses the global MIN_BET_USD constant.
        """
        self._logger = logger
        self._snapshot_id = snapshot_id
        self._bankroll = bankroll
        self._kelly_fraction = kelly_fraction
        self._initial_bankroll = initial_bankroll if initial_bankroll is not None else bankroll
        self._daily_loss_threshold = self._initial_bankroll * MAX_DAILY_LOSS_PCT
        self._min_bet_usd = min_bet_usd if min_bet_usd is not None else MIN_BET_USD

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _log(
        self,
        event_type: str,
        payload: dict[str, Any],
        severity: str = "INFO",
        session_id: str | None = None,
        risk_eval_id: str | None = None,
        forecast_id: str | None = None,
    ) -> bool:
        return self._logger.log(
            component=COMPONENT,
            event_type=event_type,
            payload=payload,
            severity=severity,
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            risk_eval_id=risk_eval_id,
            forecast_id=forecast_id,
        )

    def _build_rejection(
        self,
        risk_eval_id: str,
        reason: str,
        checks_passed: list[str],
        forecast_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "risk_eval_id": risk_eval_id,
            "approval_status": STATUS_REJECTED,
            "rejection_reason": reason,
            "approved_size": 0.0,
            "approved_direction": None,
            "risk_check_timestamp": _utc_now_iso(),
            "checks_passed": checks_passed,
            "forecast_id": forecast_id,
        }

    def _build_kill_switch(
        self,
        risk_eval_id: str,
        reason: str,
        checks_passed: list[str],
        forecast_id: str | None = None,
    ) -> dict[str, Any]:
        return {
            "risk_eval_id": risk_eval_id,
            "approval_status": STATUS_KILL_SWITCH,
            "rejection_reason": reason,
            "approved_size": 0.0,
            "approved_direction": None,
            "risk_check_timestamp": _utc_now_iso(),
            "checks_passed": checks_passed,
            "forecast_id": forecast_id,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate_forecast(
        self,
        forecast_record: dict[str, Any] | pd.Series,
        current_daily_loss: float = 0.0,
        current_drawdown_pct: float = 0.0,
        session_id: str | None = None,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Evaluate a forecast record and return a risk approval decision.

        PHASE GATE: Returns REJECTED (phase_gate_not_reached) until
        BOT_C4_ACTIVE=true in environment. This is enforced at runtime.

        Parameters
        ----------
        forecast_record:
            IF-C3-C4 record (dict or Series). Required keys:
              p_estimate, market_implied_prob, edge, recommended_direction,
              forecast_id (optional but strongly encouraged for traceability).
        current_daily_loss:
            Cumulative realized daily loss in USD. 0.0 = no loss today.
        current_drawdown_pct:
            Current portfolio drawdown as a fraction (0.0 = no drawdown, 0.2 = 20%).
        session_id:
            Current run session ID.

        Returns
        -------
        (ok, approval_dict):
            ok — False if C6 write failed; caller triggers kill switch.
            approval_dict — IF-C4-C5 record with approval_status, approved_size, etc.
        """
        eval_id = _risk_eval_id()
        if isinstance(forecast_record, pd.Series):
            fc = forecast_record.to_dict()
        else:
            fc = dict(forecast_record)

        forecast_id = fc.get("forecast_id", None)

        ok = self._log(
            "risk_eval_start",
            {
                "risk_eval_id": eval_id,
                "phase_gate_open": _is_gate_open(),
                "p_estimate": fc.get("p_estimate"),
                "edge": fc.get("edge"),
                "recommended_direction": fc.get("recommended_direction"),
                "current_daily_loss": current_daily_loss,
                "current_drawdown_pct": current_drawdown_pct,
            },
            session_id=session_id,
            risk_eval_id=eval_id,
            forecast_id=forecast_id,
        )
        all_ok = ok if ok else False

        # ------------------------------------------------------------------
        # PHASE GATE CHECK — must be first
        # ------------------------------------------------------------------
        if not _is_gate_open():
            ok = self._log(
                "risk_eval_rejected_gate",
                {
                    "risk_eval_id": eval_id,
                    "reason": "BOT_C4_ACTIVE not set — ADR-0004 acceptance and G5 gate required",
                },
                severity="INFO",
                session_id=session_id,
                risk_eval_id=eval_id,
                forecast_id=forecast_id,
            )
            if not ok:
                all_ok = False
            return all_ok, self._build_rejection(
                eval_id, "phase_gate_not_reached", [], forecast_id
            )

        try:
            checks_passed: list[str] = []

            # ------------------------------------------------------------------
            # Hard limit checks (evaluated in order; first failure → reject/kill)
            # ------------------------------------------------------------------

            # CHECK 1 — Daily loss limit (ADR-0012: percentage-based, anchored to initial_bankroll)
            if current_daily_loss >= self._daily_loss_threshold:
                ok = self._log(
                    "risk_eval_kill_switch",
                    {
                        "risk_eval_id": eval_id,
                        "trigger": "daily_loss_limit_breached",
                        "current_daily_loss": current_daily_loss,
                        "limit_usd": self._daily_loss_threshold,
                        "limit_pct": MAX_DAILY_LOSS_PCT,
                        "initial_bankroll": self._initial_bankroll,
                    },
                    severity="CRITICAL",
                    session_id=session_id,
                    risk_eval_id=eval_id,
                    forecast_id=forecast_id,
                )
                if not ok:
                    all_ok = False
                return all_ok, self._build_kill_switch(
                    eval_id, "daily_loss_limit_breached", checks_passed, forecast_id
                )
            checks_passed.append("daily_loss_limit")

            # CHECK 2 — Drawdown limit
            if current_drawdown_pct >= _HARD_LIMITS["max_drawdown_pct"]:
                ok = self._log(
                    "risk_eval_kill_switch",
                    {
                        "risk_eval_id": eval_id,
                        "trigger": "drawdown_limit_breached",
                        "current_drawdown_pct": current_drawdown_pct,
                        "limit": _HARD_LIMITS["max_drawdown_pct"],
                    },
                    severity="CRITICAL",
                    session_id=session_id,
                    risk_eval_id=eval_id,
                    forecast_id=forecast_id,
                )
                if not ok:
                    all_ok = False
                return all_ok, self._build_kill_switch(
                    eval_id, "drawdown_limit_breached", checks_passed, forecast_id
                )
            checks_passed.append("drawdown_limit")

            # CHECK 3 — Edge threshold (minimum edge to trade)
            edge = float(fc.get("edge", 0.0) or 0.0)
            if abs(edge) < MIN_EDGE_TO_APPROVE:
                ok = self._log(
                    "risk_eval_rejected",
                    {
                        "risk_eval_id": eval_id,
                        "reason": "insufficient_edge",
                        "edge": edge,
                        "min_edge": MIN_EDGE_TO_APPROVE,
                    },
                    severity="INFO",
                    session_id=session_id,
                    risk_eval_id=eval_id,
                    forecast_id=forecast_id,
                )
                if not ok:
                    all_ok = False
                return all_ok, self._build_rejection(
                    eval_id, "insufficient_edge", checks_passed, forecast_id
                )
            checks_passed.append("edge_threshold")

            # CHECK 4 — Direction is actionable
            direction = fc.get("recommended_direction", "PASS")
            if direction == "PASS":
                ok = self._log(
                    "risk_eval_rejected",
                    {
                        "risk_eval_id": eval_id,
                        "reason": "direction_pass",
                        "recommended_direction": direction,
                    },
                    severity="INFO",
                    session_id=session_id,
                    risk_eval_id=eval_id,
                    forecast_id=forecast_id,
                )
                if not ok:
                    all_ok = False
                return all_ok, self._build_rejection(
                    eval_id, "direction_pass", checks_passed, forecast_id
                )
            checks_passed.append("direction_actionable")

            # ------------------------------------------------------------------
            # Kelly sizing
            # ------------------------------------------------------------------
            p_estimate = float(fc.get("p_estimate", 0.5) or 0.5)
            market_implied_prob = float(fc.get("market_implied_prob", 0.5) or 0.5)

            # For NO direction, flip the probability frame
            if direction == "NO":
                p_effective = 1.0 - p_estimate
                mip_effective = 1.0 - market_implied_prob
            else:
                p_effective = p_estimate
                mip_effective = market_implied_prob

            approved_size = _compute_kelly_size(
                p_estimate=p_effective,
                market_implied_prob=mip_effective,
                kelly_fraction=self._kelly_fraction,
                bankroll=self._bankroll,
            )

            # CHECK 6 — Single-event exposure limit
            if approved_size > _HARD_LIMITS["max_single_event_exposure_usd"]:
                approved_size = _HARD_LIMITS["max_single_event_exposure_usd"]
            checks_passed.append("single_event_exposure_cap")

            if approved_size <= 0.0:
                ok = self._log(
                    "risk_eval_rejected",
                    {
                        "risk_eval_id": eval_id,
                        "reason": "kelly_size_zero",
                        "p_estimate": p_effective,
                        "market_implied_prob": mip_effective,
                    },
                    severity="INFO",
                    session_id=session_id,
                    risk_eval_id=eval_id,
                    forecast_id=forecast_id,
                )
                if not ok:
                    all_ok = False
                return all_ok, self._build_rejection(
                    eval_id, "kelly_size_zero", checks_passed, forecast_id
                )
            checks_passed.append("kelly_size_positive")

            # CHECK 7 — Minimum bet floor (uses instance override for paper T4)
            if approved_size < self._min_bet_usd:
                ok = self._log(
                    "risk_eval_rejected",
                    {
                        "risk_eval_id": eval_id,
                        "reason": "min_bet_floor",
                        "approved_size": approved_size,
                        "min_bet_usd": self._min_bet_usd,
                    },
                    severity="INFO",
                    session_id=session_id,
                    risk_eval_id=eval_id,
                    forecast_id=forecast_id,
                )
                if not ok:
                    all_ok = False
                return all_ok, self._build_rejection(
                    eval_id, "min_bet_floor", checks_passed, forecast_id
                )
            checks_passed.append("min_bet_floor")

            # Reserve mandate advisory warning (ADR-0010) — warning-only at paper scale;
            # blocking enforcement belongs in PIPE-03 batch-level check (dark period).
            # Fires when a single bet would exceed the uncommitted capital allowance.
            if approved_size > self._bankroll * (1.0 - RESERVE_MANDATE_PCT):
                ok = self._log(
                    "risk_reserve_mandate_warning",
                    {
                        "risk_eval_id": eval_id,
                        "approved_size": approved_size,
                        "bankroll": self._bankroll,
                        "reserve_mandate_pct": RESERVE_MANDATE_PCT,
                        "uncommitted_floor_usd": self._bankroll * RESERVE_MANDATE_PCT,
                    },
                    severity="WARNING",
                    session_id=session_id,
                    risk_eval_id=eval_id,
                    forecast_id=forecast_id,
                )
                if not ok:
                    all_ok = False

            # ------------------------------------------------------------------
            # APPROVED
            # ------------------------------------------------------------------
            approval: dict[str, Any] = {
                "risk_eval_id": eval_id,
                "approval_status": STATUS_APPROVED,
                "rejection_reason": None,
                "approved_size": float(approved_size),
                "approved_direction": direction,
                "risk_check_timestamp": _utc_now_iso(),
                "checks_passed": checks_passed,
                "forecast_id": forecast_id,
                "kelly_fraction": self._kelly_fraction,
                "bankroll": self._bankroll,
            }

            ok = self._log(
                "risk_eval_approved",
                {
                    "risk_eval_id": eval_id,
                    "approved_size": approved_size,
                    "approved_direction": direction,
                    "checks_passed": checks_passed,
                    "kelly_fraction": self._kelly_fraction,
                },
                session_id=session_id,
                risk_eval_id=eval_id,
                forecast_id=forecast_id,
            )
            if not ok:
                all_ok = False

            return all_ok, approval

        except Exception as exc:
            ok = self._log(
                "risk_eval_error",
                {"error": repr(exc), "risk_eval_id": eval_id},
                severity="ERROR",
                session_id=session_id,
                risk_eval_id=eval_id,
                forecast_id=forecast_id,
            )
            if not ok:
                all_ok = False
            return False, self._build_rejection(
                eval_id, f"unhandled_exception: {repr(exc)}", [], forecast_id
            )
