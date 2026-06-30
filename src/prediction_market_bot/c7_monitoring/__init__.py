# C7: Monitoring / Kill Switch
# Phase active: ALWAYS ACTIVE from Phase 5+ (cross-cutting)
# Monitors drift metrics. Triggers kill switch on limit breach.
# Kill switch SLA: ≤60 seconds (NFR-03). Tested before G5 (TC-009, TC-010).
# Drift kill threshold: Brier > baseline + 0.10
# No bypass path. No partial halt. No override without ADR + RCO approval.
# See: MONITORING_DRIFT_PLAN.md, RUNBOOKS/RUNBOOK_kill-switch.md, SLA_SLO_SLI.md

from prediction_market_bot.c7_monitoring.monitor import (  # noqa: F401
    SystemMonitor,
    DriftSnapshot,
    ForecastOutcomeRecord,
    KillSwitchResult,
    BRIER_BASELINE,
    ECE_BASELINE,
    ALERT_OK,
    ALERT_L4_KILL,
    KS_ARMED,
)
from prediction_market_bot.c7_monitoring.semantic_contracts import (  # noqa: F401
    SemanticContractError,
    SemanticFloorViolation,
    SemanticFloorGuard,
    ContaminationGuard,
    BandInvariantChecker,
    SemanticContractMonitor,
    SemanticHealthState,
    ContractViolation,
    T4CorrDownwardViolation,
)

__all__ = [
    # monitor
    "SystemMonitor",
    "DriftSnapshot",
    "ForecastOutcomeRecord",
    "KillSwitchResult",
    "BRIER_BASELINE",
    "ECE_BASELINE",
    "ALERT_OK",
    "ALERT_L4_KILL",
    "KS_ARMED",
    # semantic contracts (ADR-0034 Layer 3)
    "SemanticContractError",
    "SemanticFloorViolation",
    "SemanticFloorGuard",
    "ContaminationGuard",
    "BandInvariantChecker",
    "SemanticContractMonitor",
    "SemanticHealthState",
    "ContractViolation",
    "T4CorrDownwardViolation",
]
