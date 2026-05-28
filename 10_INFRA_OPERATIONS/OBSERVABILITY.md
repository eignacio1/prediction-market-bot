# Observability — Prediction Market Trading Bot

**Purpose:** Define what is observable about the system, how observability is achieved, and what signals are used to detect anomalies. Covers logging, metrics, alerting, and tracing strategy.  
**Owner (role):** Infrastructure Operator (IO) + Model Owner (MO)  
**Last reviewed:** 2026-05-22  
**Next review:** G2 (architecture confirmed); G5 (observability wired into Phase 5 pipeline); update when new component added  
**Staleness triggers:** New component added; metric renamed; alert threshold changed (requires evidence); C7 implementation completed  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, SLA_SLO_SLI.md, MONITORING_DRIFT_PLAN.md  
**Downstream links:** RUNBOOKS/, KNOWN_ISSUES.md  
**Decision references:** ADR-0001, OQ-010  
**Confidence:** 6/10 — Observability design complete; implementation TBD at Phase 5 (OQ-010)

---

## Observability Pillars

This system uses the three standard observability pillars:

1. **Logs** — Structured, append-only records of every decision, event, and anomaly (C6)
2. **Metrics** — Aggregated numerical signals computed over rolling windows (C7)
3. **Traces** — Request-level causality from data ingestion through forecast to execution (C6 event chain)

**Alerting** is derived from metrics crossing SLO thresholds (SLA_SLO_SLI.md).

---

## Logging Strategy

### Log Standard

All logs are structured JSON. Every log entry must include:

```json
{
  "timestamp": "ISO-8601 UTC",
  "component": "C1|C2|C3|C4|C5|C6|C7",
  "event_type": "<event_type>",
  "event_id": "<uuid>",
  "session_id": "<pipeline_run_id>",
  "snapshot_id": "<SNAP-YYYY-MM-DD-NNN if applicable>",
  "payload": { ... },
  "severity": "INFO|WARN|ERROR|CRITICAL"
}
```

**No secrets in logs.** Credentials, API keys, and tokens must never appear in any log entry (NFR-05 / C-001).

### Log Categories

| Log Type | Component | Content | Retention |
|----------|-----------|---------|-----------|
| Forecast log | C3 → C6 | event_id, snapshot_id, p_estimate, confidence_interval, market_implied_prob, edge | 2yr |
| Risk evaluation log | C4 → C6 | event_id, kelly_fraction, position_size, limit_check_result, rejection_reason | 2yr |
| Execution log | C5 → C6 | event_id, order_id, direction, size, venue_response, fill_price | 5yr (live) |
| Drift metric log | C7 → C6 | timestamp, rolling_brier, rolling_ece, mean_edge, alert_level | 2yr |
| Kill switch log | C7 → C6 | trigger_type (auto/manual), trigger_reason, halt_time_ms, components_halted | 5yr (live) |
| Audit integrity log | C6 | log_count, hash_chain_head, session_id | 5yr (live) |

### Log Storage

| Phase | Log location | Format | Notes |
|-------|-------------|--------|-------|
| Phase 3-4 (Research) | Local file system, `logs/` directory | JSON Lines (.jsonl) | No external dependencies |
| Phase 5-7 (Paper) | Local + optional remote sync | JSON Lines | Remote sync: backup only, not primary |
| Phase 8+ (Live) | Local primary + remote backup | JSON Lines | Durability tested at G5 |

---

## Metrics Strategy

### Metric Naming Convention

`{component}.{category}.{measure}_{unit}`

Examples:
- `c3.forecast.latency_ms`
- `c7.drift.rolling_brier_score`
- `c5.execution.order_rejection_rate`

### Core Metrics

| Metric | Component | SLO Reference | Aggregation |
|--------|-----------|--------------|-------------|
| `c3.forecast.latency_ms` | C3 | p99 < 200ms | Rolling p99 over 100 requests |
| `c3.forecast.success_rate` | C3 | ≥ 99.9% | Rolling 1hr window |
| `c3.forecast.output_valid_rate` | C3 | 100% | Rolling 1hr window |
| `c4.risk.limit_check_latency_ms` | C4 | p99 < 50ms | Rolling p99 over 100 checks |
| `c4.risk.rejection_count` | C4 | Alert if unexpected rejections | Count per session |
| `c5.execution.submission_latency_ms` | C5 | p99 < 1000ms | Rolling p99 |
| `c5.execution.venue_rejection_rate` | C5 | < 5% | Rolling 1hr |
| `c6.audit.write_latency_ms` | C6 | p99 < 100ms | Rolling p99 |
| `c6.audit.completeness_rate` | C6 | 100% | Per session |
| `c7.drift.rolling_brier_score` | C7 | < baseline + 0.05 | Rolling 30-event window |
| `c7.drift.rolling_ece` | C7 | < baseline + 0.05 | Rolling 30-event window |
| `c7.drift.mean_edge` | C7 | > 0 | Rolling 30-event window |
| `c7.kill_switch.halt_latency_ms` | C7 | ≤ 60,000ms | Per trigger event |
| `c7.monitoring.uptime_rate` | C7 | ≥ 99.9% | Rolling 24hr |

---

## Alerting Design

### Alert Levels (mapped from SLA_SLO_SLI.md)

| Level | Delivery | Target response time |
|-------|---------|---------------------|
| P1 | Immediate console + file log; future: SMS/push (OQ-010) | Immediate |
| P2 | Console + log; future: email or push notification | Within 60 seconds (awareness) |
| P3 | Log only | Next operator cadence |

### Alert Rules

| Alert ID | Metric | Condition | Level | Action |
|----------|--------|-----------|-------|--------|
| ALT-001 | `c7.drift.rolling_brier_score` | > baseline + 0.05 | P2 | L2 drift response |
| ALT-002 | `c7.drift.rolling_brier_score` | > baseline + 0.10 | P1 | L3 auto-halt |
| ALT-003 | `c7.drift.mean_edge` | < 0 on rolling window | P2 | Manual review |
| ALT-004 | `c4.risk.rejection_count` | Unexpected rejection detected | P1 | Halt; investigate |
| ALT-005 | `c5.execution.venue_rejection_rate` | > 5% | P2 | Circuit breaker; investigate |
| ALT-006 | `c7.kill_switch.halt_latency_ms` | > 60,000 on drill | P1 | Block G5; fix before live |
| ALT-007 | `c6.audit.completeness_rate` | < 100% | P1 | Halt; recover log |
| ALT-008 | `c7.monitoring.uptime_rate` | < 99% during trading | P2 | Investigate; resume or halt |

---

## Tracing / Causality Chain

Every prediction market decision must be traceable end-to-end:

```
Snapshot ID (C1)
  → Feature derivation run ID (C2)
    → Forecast event ID (C3) with p_estimate, confidence_interval
      → Risk evaluation ID (C4) with kelly_fraction, position_size
        → Order ID (C5) with venue response
          → Audit log entry (C6) linking all IDs
```

All IDs are logged in C6 with the `session_id` as the root correlation key. Any gap in the chain is a C-004 (audit completeness) violation.

---

## Observability Implementation Roadmap

| Phase | Observability Deliverable |
|-------|--------------------------|
| Phase 3 | C6 audit logger (structured JSON, local file); basic C3 logging |
| Phase 4 | Experiment log citing snapshot IDs; manual Brier score computation |
| Phase 5 | C7 metric collection; automated Brier score; alert rules ALT-001 through ALT-008 |
| Phase 6 | Kill switch drill with latency measurement (TC-009, TC-010) |
| Phase 8 | Remote log backup; extended retention; full alert delivery (OQ-010 resolved) |

**OQ-010 (C7 monitoring approach)** must be resolved before Phase 5 implementation begins.
