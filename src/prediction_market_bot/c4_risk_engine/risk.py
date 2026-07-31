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

T-213 (GG-060) — C4 Edge Accounting:
  evaluate_forecast() optionally emits one 'edge_decision' record per call
  to a secondary sink (edge_logger), independent of approval outcome. This
  is a per-market-EVALUATION log, not a per-bet log — at ~1,000 evals/game
  (CLAUDE.md hard rule #9), it is the only place that distinguishes three
  zero-bet states that are otherwise indistinguishable from bet count alone:
  pipeline broken (0 evaluations reached C4), no edge (evaluations happened,
  none cleared MIN_EDGE_TO_APPROVE), and risk-rejected (edge found, every
  instance rejected downstream). See summarize_edge_run() at module scope.
  edge_logger is opt-in (None = feature inactive, zero behavior change) —
  callers construct their own AuditLogger pointed at the sink path, same
  pattern as the primary `logger` parameter.
"""

from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import jsonlines
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

# Kelly boundary guard margin (T-280/B1). market_implied_prob exactly at 0.0/1.0 was
# already excluded, but that leaves values arbitrarily close to the boundary (e.g.
# 0.999999) able to produce a near-zero Kelly odds denominator `b` — mathematically
# finite, but precision-fragile. Real Kalshi prices are cent-quantized (never within
# this margin of 0/1), so this has no effect on production behavior; it only guards
# against a future caller passing a higher-precision or interpolated probability.
_MIP_EPSILON: float = 1e-6

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

# ADR-0026 (GG-035): portfolio-level aggregate deployment cap. The per-bet reserve
# mandate (RESERVE_MANDATE_PCT, advisory above) was never enforced in aggregate —
# nothing summed open stakes to a global cash constraint, so the G5 book deployed
# 100.3% of initial / 134% of equity while the corrupted scalar (GG-034) reported
# headroom. This cap is the PORTFOLIO-level expression of the same 40% reserve:
# aggregate open non-isolated stake is held at or below (1 - reserve) of equity.
MAX_PORTFOLIO_DEPLOYMENT_PCT: float = 1.0 - RESERVE_MANDATE_PCT  # 0.60

# Hard limits — confirmed at G4/ADR-0004; count gate deleted per ADR-0006 (2026-06-01)
# Revise all values via new APR at G6 when live bankroll is set.
_HARD_LIMITS: dict[str, float] = {
    "max_single_event_exposure_usd": 500.0,    # $500 per event; caps Kelly output
    "max_drawdown_pct": 0.20,                   # 20% realized drawdown; KILL_SWITCH
    "max_portfolio_deployment_pct": MAX_PORTFOLIO_DEPLOYMENT_PCT,  # ADR-0026: aggregate open stake ≤ 60% equity → REJECT
    # Hard solvency invariant (open stake ≤ 100% equity → KILL_SWITCH) is implicit at 1.0 — see CHECK 8a.
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
    if market_implied_prob <= _MIP_EPSILON or market_implied_prob >= 1.0 - _MIP_EPSILON:
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
        edge_logger: AuditLogger | None = None,
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
        edge_logger:
            T-213 (GG-060): optional secondary AuditLogger pointed at the
            per-evaluation edge-accounting sink (e.g. logs/audit_mlb_edge_decisions.jsonl).
            When provided, evaluate_forecast() emits one 'edge_decision' record
            per call — for every market evaluated, not just approvals. When
            None (default), edge accounting is inactive and behavior is
            unchanged from pre-T-213. A write failure on this sink is logged
            as a WARNING to `logger` — it does NOT trigger the kill switch;
            this is a secondary analytics sink, not the canonical C6 trail.
        """
        self._logger = logger
        self._snapshot_id = snapshot_id
        self._bankroll = bankroll
        self._kelly_fraction = kelly_fraction
        self._initial_bankroll = initial_bankroll if initial_bankroll is not None else bankroll
        self._daily_loss_threshold = self._initial_bankroll * MAX_DAILY_LOSS_PCT
        self._min_bet_usd = min_bet_usd if min_bet_usd is not None else MIN_BET_USD
        self._edge_logger = edge_logger

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
        current_open_exposure_usd: float = 0.0,
        portfolio_equity_usd: float | None = None,
        pool_isolated: bool = False,
    ) -> tuple[bool, dict[str, Any]]:
        """
        Evaluate a forecast record and return a risk approval decision.

        Thin wrapper around _evaluate_forecast_impl() that additionally emits
        a T-213 (GG-060) edge-decision record (when edge_logger is set) for
        EVERY call — approved, rejected, or kill-switched alike. See the
        module docstring's "T-213 (GG-060)" section for why this must cover
        the full evaluation population, not just approvals.
        """
        ok, approval = self._evaluate_forecast_impl(
            forecast_record,
            current_daily_loss=current_daily_loss,
            current_drawdown_pct=current_drawdown_pct,
            session_id=session_id,
            current_open_exposure_usd=current_open_exposure_usd,
            portfolio_equity_usd=portfolio_equity_usd,
            pool_isolated=pool_isolated,
        )
        self._emit_edge_decision(forecast_record, approval, session_id)
        return ok, approval

    def _emit_edge_decision(
        self,
        forecast_record: dict[str, Any] | pd.Series,
        approval: dict[str, Any],
        session_id: str | None,
    ) -> None:
        """T-213 (GG-060): write one per-evaluation record to the edge sink."""
        if self._edge_logger is None:
            return

        fc: dict[str, Any]
        if isinstance(forecast_record, pd.Series):
            fc = {str(k): v for k, v in forecast_record.to_dict().items()}
        else:
            fc = dict(forecast_record)

        edge = float(fc.get("edge", 0.0) or 0.0)
        status = approval.get("approval_status")
        reason = approval.get("rejection_reason")
        decision = status if status == STATUS_APPROVED else f"{status}:{reason}"

        wrote = self._edge_logger.log(
            component=COMPONENT,
            event_type="edge_decision",
            payload={
                "model_p": fc.get("p_estimate"),
                "market_implied_p": fc.get("market_implied_prob"),
                "vig": fc.get("vig"),
                "edge": edge,
                "edge_signal": edge >= MIN_EDGE_TO_APPROVE,  # GG-142: signed, not abs()
                "recommended_direction": fc.get("recommended_direction"),
                "approval_status": status,
                "rejection_reason": reason,
                "decision": decision,
                "approved_size": approval.get("approved_size"),
            },
            session_id=session_id,
            snapshot_id=self._snapshot_id,
            risk_eval_id=approval.get("risk_eval_id"),
            forecast_id=approval.get("forecast_id"),
            severity="INFO",
        )
        if not wrote:
            self._log(
                "edge_decision_write_failed",
                {"risk_eval_id": approval.get("risk_eval_id")},
                severity="WARNING",
                session_id=session_id,
                risk_eval_id=approval.get("risk_eval_id"),
                forecast_id=approval.get("forecast_id"),
            )

    def _evaluate_forecast_impl(
        self,
        forecast_record: dict[str, Any] | pd.Series,
        current_daily_loss: float = 0.0,
        current_drawdown_pct: float = 0.0,
        session_id: str | None = None,
        current_open_exposure_usd: float = 0.0,
        portfolio_equity_usd: float | None = None,
        pool_isolated: bool = False,
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
        current_open_exposure_usd:
            ADR-0026: aggregate open NON-isolated stake already deployed (Σ open
            stake on the book this bet would join). Used by the portfolio-level
            free-cash invariant (CHECK 8). Caller (C5/orchestrator) owns the
            position ledger and passes a snapshot — same pattern as drawdown/loss.
        portfolio_equity_usd:
            ADR-0026: current equity (initial_bankroll + Σ closed pnl for the
            relevant pool). When None (default), the portfolio invariant is
            SKIPPED — backward compatible for callers that do not supply
            portfolio state. run_paper_trade.py supplies T1 equity; T4 live
            supplies t4_band_budget when not in VIRTUAL mode.
        pool_isolated:
            T-175 (ADR-0026 extension): when True, this call represents a
            capital-isolated pool (e.g. T4 band budget). CHECK 8a (solvency
            KILL — projected stake > equity) applies. CHECK 8b (60% policy
            cap REJECT) is SKIPPED because the reserve-for-T4 constraint
            does not apply to the T4 pool itself. EXP harnesses pass
            pool_isolated=False (default) — they are always phase-gate
            rejected before CHECK 8 is reached, so the value is moot.

        Returns
        -------
        (ok, approval_dict):
            ok — False if C6 write failed; caller triggers kill switch.
            approval_dict — IF-C4-C5 record with approval_status, approved_size, etc.
        """
        eval_id = _risk_eval_id()
        fc: dict[str, Any]
        if isinstance(forecast_record, pd.Series):
            fc = {str(k): v for k, v in forecast_record.to_dict().items()}
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
                "current_open_exposure_usd": current_open_exposure_usd,
                "portfolio_equity_usd": portfolio_equity_usd,
                "pool_isolated": pool_isolated,
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
            # GG-142: `edge` on the forecast record is already direction-resolved
            # by the caller (run_t4_mlb_live.py, run_mlb_paper_trade.py,
            # run_t2_mlb_sameday.py all recompute it post-direction-assignment
            # via a directional-edge helper, per GG-077/GG-113) — a positive
            # value means "this recommended direction has a real, fee-net edge
            # of this magnitude." abs() here treated a confidently-*wrong* bet
            # (edge very negative — vig/fee cost exceeds the signal in the
            # recommended direction) as if it were a confidently-right one,
            # rescuing 46.1% of T4 epoch-8 evaluations (239/239 with
            # vig > |model_p - mid|). The gate must be signed: only a
            # sufficiently positive directional edge clears it.
            edge = float(fc.get("edge", 0.0) or 0.0)
            if edge < MIN_EDGE_TO_APPROVE:
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

            # CHECK 4b — Direction/edge-sign consistency (GG-142).
            # `recommended_direction` is carried on every forecast record
            # (written at the three edge_decision/log sites in this module)
            # but, before this fix, was never cross-checked against anything
            # — a producer bug that assigns "NO" while still sending the raw
            # YES-frame gross_edge (instead of the direction-flipped value)
            # would sail through CHECK 3 undetected, since a positive
            # gross_edge also satisfies a positive-edge threshold. Only
            # enforced when the raw `gross_edge` is present on the record —
            # it is optional on the shared forecast contract (not every
            # producer sets it), so its absence is not itself a violation.
            gross_edge_raw = fc.get("gross_edge")
            if gross_edge_raw is not None:
                gross_edge_val = float(gross_edge_raw)
                sign_ok = (
                    (direction == "YES" and gross_edge_val > 0.0)
                    or (direction == "NO" and gross_edge_val < 0.0)
                )
                if not sign_ok:
                    ok = self._log(
                        "risk_eval_rejected",
                        {
                            "risk_eval_id": eval_id,
                            "reason": "direction_edge_sign_inconsistent",
                            "recommended_direction": direction,
                            "gross_edge": gross_edge_val,
                            "edge": edge,
                        },
                        severity="WARNING",
                        session_id=session_id,
                        risk_eval_id=eval_id,
                        forecast_id=forecast_id,
                    )
                    if not ok:
                        all_ok = False
                    return all_ok, self._build_rejection(
                        eval_id, "direction_edge_sign_inconsistent", checks_passed, forecast_id
                    )
            checks_passed.append("direction_edge_consistency")

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

            kelly_frac = float(fc.get("kelly_fraction", self._kelly_fraction))
            approved_size = _compute_kelly_size(
                p_estimate=p_effective,
                market_implied_prob=mip_effective,
                kelly_fraction=kelly_frac,
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

            # ------------------------------------------------------------------
            # CHECK 8 — Portfolio-level aggregate deployment invariant
            # (ADR-0026 / GG-035). Enforced only when the caller supplies
            # portfolio_equity_usd (backward compatible — None ⇒ skip).
            #
            # Per-event caps and per-bet Kelly do NOT sum to a global cash
            # constraint. GG-035: the G5 book deployed $1003.38 (100.3% of
            # initial / 134% of equity) one bet at a time, each individually
            # under the $500 event cap, with nothing watching the aggregate.
            # 8a is the hard solvency invariant (free cash ≥ 0 — KILL_SWITCH);
            # 8b is the policy cap that prevents reaching 8a incrementally —
            # each over-cap bet REJECTS (per-bet expression, not a batch break),
            # so exposure plateaus at the cap instead of growing past equity.
            # ------------------------------------------------------------------
            if portfolio_equity_usd is not None:
                equity = float(portfolio_equity_usd)
                projected_exposure = float(current_open_exposure_usd) + float(approved_size)

                # 8a — Hard solvency invariant: open stake must never exceed
                # equity (free cash ≥ 0). Breach = over-leverage = KILL_SWITCH.
                if projected_exposure > equity:
                    ok = self._log(
                        "risk_eval_kill_switch",
                        {
                            "risk_eval_id": eval_id,
                            "trigger": "portfolio_over_leverage",
                            "current_open_exposure_usd": float(current_open_exposure_usd),
                            "approved_size": float(approved_size),
                            "projected_exposure_usd": projected_exposure,
                            "portfolio_equity_usd": equity,
                            "free_cash_usd": equity - projected_exposure,
                        },
                        severity="CRITICAL",
                        session_id=session_id,
                        risk_eval_id=eval_id,
                        forecast_id=forecast_id,
                    )
                    if not ok:
                        all_ok = False
                    return all_ok, self._build_kill_switch(
                        eval_id, "portfolio_over_leverage", checks_passed, forecast_id
                    )

                # 8b — Policy deployment cap: hold aggregate stake ≤ cap × equity
                # (ADR-0010 reserve enforced in aggregate). Breach = REJECT.
                # Skipped for isolated pools (pool_isolated=True) — the 60%
                # reserve-for-T4 constraint does not apply to T4's own budget.
                if not pool_isolated:
                    deployment_cap = _HARD_LIMITS["max_portfolio_deployment_pct"] * equity
                    if projected_exposure > deployment_cap:
                        ok = self._log(
                            "risk_eval_rejected",
                            {
                                "risk_eval_id": eval_id,
                                "reason": "aggregate_deployment_cap",
                                "current_open_exposure_usd": float(current_open_exposure_usd),
                                "approved_size": float(approved_size),
                                "projected_exposure_usd": projected_exposure,
                                "deployment_cap_usd": deployment_cap,
                                "max_portfolio_deployment_pct": _HARD_LIMITS["max_portfolio_deployment_pct"],
                                "portfolio_equity_usd": equity,
                            },
                            severity="INFO",
                            session_id=session_id,
                            risk_eval_id=eval_id,
                            forecast_id=forecast_id,
                        )
                        if not ok:
                            all_ok = False
                        return all_ok, self._build_rejection(
                            eval_id, "aggregate_deployment_cap", checks_passed, forecast_id
                        )
                    checks_passed.append("aggregate_deployment_cap")

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
                # ADR-0026 / T-175 portfolio telemetry (None when caller did not supply state)
                "portfolio_equity_usd": (
                    float(portfolio_equity_usd) if portfolio_equity_usd is not None else None
                ),
                "open_exposure_before_usd": (
                    float(current_open_exposure_usd) if portfolio_equity_usd is not None else None
                ),
                "pool_isolated": pool_isolated,
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


# ---------------------------------------------------------------------------
# T-213 (GG-060) — Run-level edge accounting summary
# ---------------------------------------------------------------------------


def summarize_edge_run(
    edge_log_path: str | Path,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Read an edge-decision JSONL sink (written by RiskEngine.evaluate_forecast()
    when edge_logger is set) and produce a run-level report.

    GG-060's core problem: at ~1,000 evals/game, "0 bets placed" is ambiguous.
    It can mean the pipeline never reached C4 (upstream break — C1/C2/C3
    failure), the market was quiet (no edge found in any evaluation — a
    legitimate outcome), or C4's own checks rejected every edge signal found
    (kill switch, sizing floor, exposure cap — a risk-control problem). These
    three states are indistinguishable from bet count alone; this function
    reads the full evaluation population and disambiguates them.

    Parameters
    ----------
    edge_log_path:
        Path to the edge-decision JSONL sink.
    session_id:
        If provided, restrict the summary to entries matching this session_id.
        If None, summarizes every entry in the file.

    Returns
    -------
    dict with:
      total_evaluations       — count of edge_decision records read
      edge_signals_found      — count where edge_signal was True
      bets_approved           — count where approval_status == APPROVED
      rejection_reason_counts — {rejection_reason_or_status: count} for
                                 every non-approved record
      run_state                — one of PIPELINE_BROKEN / NO_EDGE /
                                 RISK_REJECTED / ACTIVE
      silent_success_flag      — True when total_evaluations >= 50 and
                                 edge_signals_found == 0 (GG-060 resolution
                                 item 3: flag runs where edge_signals == 0
                                 for >=50 evaluations)
    """
    path = Path(edge_log_path)
    total_evaluations = 0
    edge_signals_found = 0
    bets_approved = 0
    rejection_reason_counts: dict[str, int] = {}

    if path.exists():
        with jsonlines.open(str(path), mode="r") as reader:
            for entry in reader:
                if session_id is not None and entry.get("session_id") != session_id:
                    continue
                payload = entry.get("payload", {}) or {}
                total_evaluations += 1
                if payload.get("edge_signal"):
                    edge_signals_found += 1
                if payload.get("approval_status") == STATUS_APPROVED:
                    bets_approved += 1
                else:
                    reason = (
                        payload.get("rejection_reason")
                        or payload.get("approval_status")
                        or "unknown"
                    )
                    rejection_reason_counts[reason] = rejection_reason_counts.get(reason, 0) + 1

    if total_evaluations == 0:
        run_state = "PIPELINE_BROKEN"
    elif edge_signals_found == 0:
        run_state = "NO_EDGE"
    elif bets_approved == 0:
        run_state = "RISK_REJECTED"
    else:
        run_state = "ACTIVE"

    return {
        "session_id": session_id,
        "total_evaluations": total_evaluations,
        "edge_signals_found": edge_signals_found,
        "bets_approved": bets_approved,
        "rejection_reason_counts": rejection_reason_counts,
        "run_state": run_state,
        "silent_success_flag": total_evaluations >= 50 and edge_signals_found == 0,
    }
