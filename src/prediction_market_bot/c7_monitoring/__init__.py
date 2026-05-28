# C7: Monitoring / Kill Switch
# Phase active: ALWAYS ACTIVE from Phase 5+ (cross-cutting)
# Monitors drift metrics. Triggers kill switch on limit breach.
# Kill switch SLA: ≤60 seconds (NFR-03). Tested before G5 (TC-009, TC-010).
# Drift kill threshold: Brier > baseline + 0.10
# No bypass path. No partial halt. No override without ADR + RCO approval.
# See: MONITORING_DRIFT_PLAN.md, RUNBOOKS/RUNBOOK_kill-switch.md, SLA_SLO_SLI.md
