# Resilience and Failure Modes — Prediction Market Trading Bot

**Purpose:** Enumerate failure modes for every component, their detection signals, impact, mitigations, and runbook links. Required for G2 gate.  
**Owner (role):** Architecture Owner (AO)  
**Status:** **CANONICAL — G2 Architecture Gate 2026-05-22** — Changes require ADR or formal Change Class A/B record  
**Last reviewed:** 2026-05-22 (G2 review; C4/C5 corrected; promoted DRAFT → CANONICAL)  
**Next review:** On staleness trigger only; after each incident postmortem  
**Staleness triggers:** New component added; incident reveals unmodeled failure mode; architecture change; runbook updated  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, INTERFACES_CONTRACTS.md  
**Downstream links:** 10_INFRA_OPERATIONS/RUNBOOKS/, 08_MODEL_RISK_GOVERNANCE/MONITORING_DRIFT_PLAN.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 7/10 — Known failure modes catalogued; live-mode failure modes expand at G5
**Decisions logged:** true — FM-01–FM-08 failure mode prioritization captured at G2 gate (APR-0004) and G5 kill switch drill (APR-0013)  

**⚠️ Corrected 2026-07-06 (GG-074 remediation) — real gap found, not just staleness.** G5 is closed and the system has been running paper trading in production for weeks, but of the four runbooks marked "(to be created at G5)" below (FM-01 ingestion-failure, FM-02 data-contamination, FM-05 order-duplication, FM-07 audit-log), **none exist** — confirmed via directory listing of `10_INFRA_OPERATIONS/RUNBOOKS/`, which contains only `RUNBOOK_kill-switch.md`, `RUNBOOK_model-drift.md`, and `RUNBOOK_polymarket-activation.md` (matching FM-04/FM-06 and FM-03 respectively, both correctly un-flagged below). This is a genuine operational-readiness gap, not merely a stale citation: FM-02 (data contamination — rated CRITICAL, "silently destroys validity of all downstream validation") and FM-04's sibling FM-05 (order duplication — rated HIGH) have no runbook despite the system now placing real Kalshi demo orders (ADR-0008) and running live MLB paper trading. Recommend registering this as its own governance gap (candidate: missing G5-promised incident runbooks) rather than treating it as closed by this note.

---

## FM-01 — Data Ingestion Failure (C1)

| Attribute | Detail |
|-----------|--------|
| Failure mode | C1 fails to ingest data: source unavailable, schema mismatch, or corrupt file |
| Cause | Network error; source API down; schema version mismatch; malformed data |
| Detection signal | C1 emits ERROR log; missing Snapshot ID in DATA_SNAPSHOTS_INDEX.md for expected batch |
| Impact | Research: pipeline halts; no forecast for affected events. Live: data gap; forecasts not generated |
| Severity | Research: LOW (recoverable) | Live: HIGH (no forecasts = no orders = missed market window) |
| Mitigation | Schema validation at ingestion rejects bad records before poisoning feature store. Retry logic with exponential backoff. Alert on ingestion gap >threshold. |
| Runbook | 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_ingestion-failure.md (to be created at G5) |
| Revisit trigger | Venue API change; schema version bump |

## FM-02 — Look-Ahead Bias / Data Contamination (C1/C2)

| Attribute | Detail |
|-----------|--------|
| Failure mode | Future data (post-event) leaks into training features, inflating backtest performance |
| Cause | Incorrect temporal cutoff in feature derivation; outcome data mixed into feature store; non-chronological train/test split |
| Detection signal | temporal_cutoff field post-dates feature derivation window; automated overlap check fails |
| Impact | All backtesting results are invalid; model may have zero live edge; cannot detect without explicit check |
| Severity | CRITICAL — silently destroys validity of all downstream validation |
| Mitigation | (1) Temporal safety column mandatory in lineage register. (2) Automated temporal overlap check in backtesting framework. (3) Outcome data ingested separately, never in feature store. (4) All train/test splits are chronological. |
| Runbook | 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_data-contamination.md (to be created at G3) |
| Revisit trigger | Any new feature added to lineage register; backtesting framework change |

## FM-03 — Model Performance Degradation (C3)

| Attribute | Detail |
|-----------|--------|
| Failure mode | Forecast accuracy degrades materially vs. validated baseline (model drift) |
| Cause | Market regime change; signal decay; distribution shift in input data; model-market coevolution |
| Detection signal | Live Brier score exceeds baseline + 0.05 over rolling 30-event window; calibration curve deviates |
| Impact | Continued operation generates negative EV; drawdown likely to increase |
| Severity | HIGH in live capital phase |
| Mitigation | MONITORING_DRIFT_PLAN.md defines drift thresholds and response. Auto-alert at threshold. Manual review before re-enabling after drift alert. |
| Runbook | 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_model-drift.md (to be created at G5) |
| Revisit trigger | G4 validation confirms drift thresholds; live deployment |

## FM-04 — Risk Limit Breach / Runaway Loss (C4/C5)

| Attribute | Detail |
|-----------|--------|
| Failure mode | Capital loss exceeds daily or drawdown hard limit; kill switch not triggered; losses continue |
| Cause | Risk engine bug; kill switch not wired to all components; limit calculation error |
| Detection signal | Programmatic limit check fires; daily_loss monitor exceeds threshold |
| Impact | CRITICAL — uncontrolled capital loss |
| Severity | CRITICAL |
| Mitigation | (1) Kill switch must be tested at G5 before any live capital. (2) Risk limits enforced in C4 (Risk Engine) before every order approval (not just at day end). (3) C7 monitoring checks limits independently of C4. (4) No override path without ADR + RCO approval. |
| Runbook | 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_kill-switch.md |
| Revisit trigger | Any change to RISK_APPETITE_CONSTRAINTS.md; live capital deployment |

## FM-05 — Order Duplication / Double Submission (C5)

| Attribute | Detail |
|-----------|--------|
| Failure mode | The same order submitted twice due to retry logic or network failure; double position taken |
| Cause | Timeout retry without idempotency check; network partition |
| Detection signal | Venue confirms two fills for same idempotency_key |
| Impact | Position size exceeds approved limit; risk limit may be breached |
| Severity | HIGH |
| Mitigation | idempotency_key required on all orders per IF-C5-VENUE. Venue confirmation checked before retry. Deduplication log in C6. |
| Runbook | 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_order-duplication.md (to be created at G5) |
| Revisit trigger | Venue API change; execution engine change |

## FM-06 — Kill Switch Failure (C7)

| Attribute | Detail |
|-----------|--------|
| Failure mode | Kill switch triggered but does not halt all components within 60 seconds |
| Cause | Component not wired to kill switch signal; process hung; messaging system failure |
| Detection signal | Component still emitting activity logs >60s after kill switch trigger |
| Impact | Uncontrolled continued operation; risk limits not enforced |
| Severity | CRITICAL |
| Mitigation | Kill switch signal broadcast to all components; each component independently checks kill flag. Drill tested at G5 before any live use. |
| Runbook | 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_kill-switch.md |
| Revisit trigger | New component added; kill switch drill fails; architecture change |

## FM-07 — Audit Log Corruption / Loss (C6)

| Attribute | Detail |
|-----------|--------|
| Failure mode | Audit log entries are missing, modified, or unreadable |
| Cause | Disk failure; process crash during write; log rotation misconfiguration |
| Detection signal | Log file hash mismatch; gap in sequential event IDs; expected entries absent |
| Impact | Loss of auditability; cannot reconstruct decision history; governance invariant violated |
| Severity | HIGH |
| Mitigation | Append-only log format. Write confirmation before acknowledging event. Periodic log integrity check. Backup rotation per DATA_RETENTION_DELETION.md. |
| Runbook | 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_audit-log.md (to be created at G5) |
| Revisit trigger | Storage architecture change; log format change |

## FM-08 — Context Rot / Directory Drift (Governance)

| Attribute | Detail |
|-----------|--------|
| Failure mode | Artifacts become stale; MEMORY_BANK links break; shadow docs accumulate; real system diverges from documented system |
| Cause | Cadences not followed; staleness triggers ignored; ADRs not written for major changes |
| Detection signal | DIR freshness metric M1 drops below 85%; broken links detected; major change without ADR reference |
| Impact | Loss of reproducibility; handoff failure; recurrence of previous iteration's context rot |
| Severity | HIGH (this was the cause of the previous iteration failure) |
| Mitigation | Compass OS cadences mandatory. Universal headers on all artifacts. Weekly DIR. Escalation ladder: M1 < 85% → owner ping; < 75% → accountable review; < 65% → gate freeze. |
| Runbook | COMMUNICATIONS_PLAN.md escalation path |
| Revisit trigger | Quarterly retrieval drill; DIR health report |
