# Non-Functional Requirements — Prediction Market Trading Bot

**Purpose:** Define quality attributes the system must exhibit regardless of feature being exercised.  
**Owner (role):** Architecture Owner (AO) / Product Owner (PO)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: verified current, no drift found. All NFR statements (kill switch ≤60s, secrets handling, structured logging, etc.) still match live system behavior. NFR-06's "monitoring tool TBD at G5" remains accurate as literally stated — no third-party monitoring tool (Grafana/Prometheus/etc.) was ever formally selected; the custom C8 web dashboard fills that role informally, but no ADR retired the TBD.  
**Next review:** 2026-08-23  
**Staleness triggers:** New external integration; venue confirmed; scale threshold reached; compliance requirement confirmed  
**Upstream links:** REQUIREMENTS.md, RISK_APPETITE_CONSTRAINTS.md, PROJECT_CHARTER.md  
**Downstream links:** 02_ARCHITECTURE_DESIGN/ARCHITECTURE_OVERVIEW.md, 10_INFRA_OPERATIONS/SLA_SLO_SLI.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 8/10  

---

## NFR-01 — Reproducibility

| Attribute | Requirement |
|-----------|------------|
| Statement | Every research result and model output must be re-producible given: (a) pinned code commit, (b) pinned environment spec, (c) referenced Data Snapshot ID. No result is valid without all three. |
| Verification method | Run a prior experiment using only the pinned artifacts; confirm results match within numerical tolerance |
| Threshold | 100% of experiments in EXPERIMENT_LOG must reference all three anchors |
| Failure mode | Unpinned dependency; floating data version; undocumented random seed |
| Owner | Research Lead (RL) / Evidence Owner (EO) |

## NFR-02 — Auditability

| Attribute | Requirement |
|-----------|------------|
| Statement | All forecasts, simulated orders, real orders, risk limit checks, and kill-switch events must be written to an append-only log with: timestamp (UTC), event type, relevant IDs (snapshot, model version, market), and outcome. |
| Verification method | Confirm log cannot be modified post-write; confirm all required fields present in sample entries |
| Threshold | Zero unlogged forecast or order events |
| Failure mode | In-memory-only state; mutable log file; missing required fields |
| Owner | Architecture Owner (AO) |

## NFR-03 — Safety (Kill Switch)

| Attribute | Requirement |
|-----------|------------|
| Statement | The kill switch must halt all system processes (data ingestion, forecast, execution) within ≤60 seconds of trigger (manual or automatic). Auto-trigger must activate on: daily loss limit breach, drawdown limit breach, data integrity error, or operator command. |
| Verification method | Timed kill-switch drill; confirm all processes halted; log entry confirmed |
| Threshold | ≤60 seconds trigger-to-halt; 100% process coverage |
| Failure mode | Partial halt (some processes continue); trigger not wired to all components |
| Owner | Operations Owner (OO) |

## NFR-04 — Data Integrity and Anti-Contamination

| Attribute | Requirement |
|-----------|------------|
| Statement | No training or calibration data may leak into evaluation sets. Data Snapshot IDs must be immutable after creation. Train/test splits must be chronological (not random) to respect temporal order. |
| Verification method | Automated overlap check between train and test snapshot windows; look-ahead bias audit per experiment |
| Threshold | Zero confirmed instances of data leakage; zero random (non-chronological) splits |
| Failure mode | Date-based feature leak; overlapping train/test windows; shuffled time series |
| Owner | Research Lead (RL) |

## NFR-05 — Secrets Management

| Attribute | Requirement |
|-----------|------------|
| Statement | No API credentials, keys, or passwords may appear in code, configuration files, logs, or documentation. All secrets use the mechanism defined in SECRETS_HANDLING.md. |
| Verification method | Automated secrets scan on all committed code; manual review at each gate |
| Threshold | Zero hardcoded secrets detected |
| Failure mode | Credential in .env file committed to repo; key logged at DEBUG level |
| Owner | Risk/Control Owner (RCO) |

## NFR-06 — Observability

| Attribute | Requirement |
|-----------|------------|
| Statement | All production processes must emit structured (machine-readable) logs with: timestamp, process name, event type, severity level, and relevant IDs. Metrics must be emittable to a monitoring system (tool TBD at G5). |
| Verification method | Sample log review; confirm structured format; confirm metric emission |
| Threshold | 100% of production processes emit structured logs; 0 silent failures |
| Failure mode | Unstructured print statements; exceptions swallowed; no metric emission |
| Owner | Operations Owner (OO) |

## NFR-07 — Portability (Development Isolation)

| Attribute | Requirement |
|-----------|------------|
| Statement | The research pipeline must be fully executable in an isolated development environment with no external connectivity (no live API calls, no real credentials required) for Phases 0–5. |
| Verification method | Run full pipeline with all external endpoints mocked/stubbed; confirm results |
| Threshold | Zero hard dependencies on live external systems in research mode |
| Failure mode | Research code fails without live API key; no mock/stub layer |
| Owner | Architecture Owner (AO) |

## NFR-08 — Change Control

| Attribute | Requirement |
|-----------|------------|
| Statement | Any change to model architecture, signal set, evaluation methodology, or risk limits requires: (a) an ADR, (b) a CHANGELOG entry, (c) updated artifacts with new Last Reviewed dates. Minor changes require a CHANGELOG entry at minimum. |
| Verification method | DIR check: all major changes in last week have ADR references |
| Threshold | Zero major changes without ADR reference |
| Failure mode | Silent drift; undocumented model parameter change |
| Owner | Directory Steward (DS) |
