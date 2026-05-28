# SLA / SLO / SLI — Prediction Market Trading Bot

**Purpose:** Define service level agreements, objectives, and indicators for each pipeline component. Provides the performance baseline against which monitoring alerts and operational responses are calibrated.  
**Owner (role):** Infrastructure Operator (IO) + Model Owner (MO)  
**Last reviewed:** 2026-05-22  
**Next review:** G5 (validate SLOs against paper trading baseline); G6 (confirm live capital SLOs)  
**Staleness triggers:** Component added; SLO threshold adjusted; persistent SLO miss; phase gate cleared  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, RESILIENCE_FAILURE_MODES.md, NON_FUNCTIONAL_REQUIREMENTS.md  
**Downstream links:** OBSERVABILITY.md, MONITORING_DRIFT_PLAN.md, RUNBOOKS/  
**Decision references:** ADR-0001  
**Confidence:** 6/10 — SLO definitions complete; threshold values are targets pending Phase 5 calibration

---

## Definitions

- **SLI (Service Level Indicator):** A quantitative measure of a service behavior (e.g., latency in ms, availability %)
- **SLO (Service Level Objective):** The target value or range for an SLI (e.g., p99 latency < 500ms)
- **SLA (Service Level Agreement):** The consequence of missing an SLO. For a solo operator internal system, SLA "breach" maps to an operational response (alert, pause, kill switch) rather than a financial penalty.
- **Error budget:** The allowed amount of SLO violation before escalation. Not computed in Phase 3/4; introduced at Phase 5.

---

## Component SLO Table

### C1 — Signal Ingestion

| SLI | SLO | Measurement | Breach Response |
|-----|-----|-------------|----------------|
| Data freshness (DS-01 snapshot age) | Snapshot used in experiment ≤ stale threshold defined at registration | DATA_SNAPSHOTS_INDEX.md audit | Halt experiment; update snapshot |
| Ingestion success rate (Phase 5+) | ≥ 99% of scheduled ingestion runs succeed | C6 audit log | Alert P2; investigate; log to RID_LOG.md |
| Ingestion latency (Phase 5+) | p99 < 30 seconds per batch | C7 metric | L1 Watch if >30s on rolling avg |

---

### C2 — Feature Store

| SLI | SLO | Measurement | Breach Response |
|-----|-----|-------------|----------------|
| Temporal integrity | 100% — zero look-ahead violations | TC-001 automated check; pre-experiment audit | HALT experiment immediately; log contamination incident |
| Feature completeness | ≥ 95% of required features present per event | Schema validation at ingestion | Reject event; log gap; investigate |
| Schema version consistency | 100% — all features cite consistent schema version | Snapshot ID audit | Alert; halt affected experiment |

**Note:** Temporal integrity is a binary SLO — any violation is a CRITICAL failure, not a degraded state.

---

### C3 — Forecasting Engine

| SLI | SLO | Measurement | Breach Response |
|-----|-----|-------------|----------------|
| Inference latency (single event) | p99 < 200ms | C6 log | L1 Watch |
| Inference success rate | ≥ 99.9% (paper/live) | C6 log | L2 Alert if <99.9% on rolling hour |
| Output validity | 100% — p_estimate ∈ (0,1); confidence interval valid | Output schema validation | Reject prediction; log anomaly |
| Calibration (rolling Brier) | Rolling 30-event Brier < baseline + 0.05 | C7 drift calculator | Drift response ladder (MONITORING_DRIFT_PLAN.md) |

---

### C4 — Risk Engine (Phase 5+)

| SLI | SLO | Measurement | Breach Response |
|-----|-----|-------------|----------------|
| Limit check latency | p99 < 50ms (synchronous, blocking order path) | C6 log | L2 Alert; C5 blocked until resolved |
| Limit enforcement accuracy | 100% — zero orders passed that violate hard limits | Audit log reconciliation | CRITICAL — kill switch; full audit |
| Availability | 100% during any open position | C7 health check | Kill switch auto-trigger if C4 unavailable with open position |

---

### C5 — Execution Engine (Phase 8+)

| SLI | SLO | Measurement | Breach Response |
|-----|-----|-------------|----------------|
| Order submission latency | p99 < 1 second from C4 approval to venue | C6 log | L1 Watch if >1s rolling avg |
| Order rejection rate (venue-side) | < 5% of submitted orders | C6 log | L2 Alert; investigate cause |
| Position reconciliation accuracy | 100% — local state matches venue state | Reconciliation check on startup and after each fill | HALT; reconcile before any new order |
| Circuit breaker activation | Auto-halt on ≥ 3 consecutive venue errors | C6 log | L3 Pause; manual investigation required |

---

### C6 — Audit Logger

| SLI | SLO | Measurement | Breach Response |
|-----|-----|-------------|----------------|
| Log completeness | 100% — every forecast, risk evaluation, and execution event has a log entry | Audit completeness check (TC-007) | CRITICAL — halt pipeline; recover log |
| Log write latency | p99 < 100ms (synchronous write) | Internal timing | L1 Watch if >100ms |
| Log durability | Zero data loss on crash | Recovery test at G5 | CRITICAL if failed |

---

### C7 — Monitoring and Kill Switch

| SLI | SLO | Measurement | Breach Response |
|-----|-----|-------------|----------------|
| Kill switch latency | ≤ 60 seconds from trigger to full halt | TC-009, TC-010 (NFR-03) | **NFR-03 violation — do NOT go live until fixed** |
| Alert delivery latency | P2 alert delivered within 60 seconds of threshold breach | C7 internal log | L2 Alert on missed alerts |
| Metric collection uptime | ≥ 99.9% during paper/live trading hours | C7 heartbeat | L3 Pause — monitoring must be active during trading |
| False positive rate | < 10% of L2 alerts confirmed false positive (rolling 30 events) | Post-alert review log | Review thresholds; update MONITORING_DRIFT_PLAN.md |

---

## Availability Targets by Phase

| Phase | Environment | Required Availability | Trading Hours |
|-------|-------------|----------------------|--------------|
| Phase 3-4 | ENV-01 Research | Best effort (batch only) | N/A |
| Phase 5-7 | ENV-02 Paper Trading | ≥ 95% during market hours | Venue market hours |
| Phase 8+ | ENV-03 Live Capital | ≥ 99% during market hours | Venue market hours |

**Note:** "Availability" for a single-operator local system means the pipeline can ingest data and generate forecasts during market hours. No uptime commitment is possible for truly unattended operation until Phase 8.

---

## SLO Breach Escalation

| Severity | Condition | Response | Owner |
|----------|-----------|----------|-------|
| P1 | Temporal integrity violation; limit enforcement failure; kill switch latency > 60s | Immediate halt; full incident log | DS + RCO |
| P2 | SLO miss on C3, C4, C5, C6; drift L2 alert | Alert delivered within 60s; manual review within 24h | MO |
| P3 | SLO miss on C1, C2 (non-temporal); L1 Watch | Log; review at next cadence | IO |

All P1 incidents are logged to RID_LOG.md with root cause and corrective action.
