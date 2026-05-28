# Threat Model — Prediction Market Trading Bot

**Purpose:** Identify threats to system integrity, data validity, capital safety, and governance. Maps threats to mitigations and residual risk. Required for G2 gate.  
**Owner (role):** Architecture Owner (AO) + Risk and Compliance Owner (RCO)  
**Status:** **CANONICAL — G2 Architecture Gate 2026-05-22** — Changes require ADR or formal Change Class A/B record  
**Last reviewed:** 2026-05-22 (G2 review; C4/C5 corrected; promoted DRAFT → CANONICAL; RCO = AO as sole operator)  
**Next review:** On staleness trigger only; expanded at G5 (pre-live-inference) and G6 (pre-live-capital)  
**Staleness triggers:** New component added; new external integration; security incident; venue API confirmed; live capital authorized  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, SYSTEM_CONTEXT.md, RESILIENCE_FAILURE_MODES.md  
**Downstream links:** 09_SECURITY_PRIVACY_COMPLIANCE/, 10_INFRA_OPERATIONS/RUNBOOKS/  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 6/10 — Threats identified for current scope; live-capital threat surface expands significantly at G5–G6

---

## Threat Modeling Scope

This model covers Phases 0–5 (research and operational readiness). Live capital threats are flagged and will be expanded at G5. Threats are categorized using a simplified STRIDE framework applied to this system's specific risk profile.

**Primary adversarial concern:** Most threats in this system are **accidental** (configuration errors, data contamination, process failures) rather than external adversarial. External attack surface is minimal until live capital is deployed.

---

## TH-01 — Data Contamination / Look-Ahead Bias (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Future data leaks into training features; model appears performant but has zero live edge |
| Category | Integrity (Accidental) |
| Attack vector | Internal (data pipeline logic error) |
| Affected components | C1, C2 |
| Likelihood | HIGH — This class of error is common and often silent |
| Impact | CRITICAL — Silently invalidates all backtesting results |
| Controls | (1) TI-01 through TI-04 temporal integrity rules in DATA_FLOWS_LINEAGE.md. (2) temporal_cutoff field mandatory in IF-C2-C3. (3) Outcome data ingested on separate path (DS-03 ≠ feature store). (4) Automated temporal overlap check in backtesting framework. |
| Residual risk | MEDIUM — Automated check catches most cases; novel feature types require manual review |
| Related FM | FM-02 |
| Revisit trigger | New feature added to lineage register |

---

## TH-02 — Credential Exposure (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | API keys, venue credentials, or account details committed to version control or stored in plaintext |
| Category | Information Disclosure (Accidental) |
| Attack vector | Internal (developer error) |
| Affected components | C5 (venue connection), C1 (data source connection) |
| Likelihood | MEDIUM — Common in solo projects without secrets discipline |
| Impact | HIGH — Venue account compromise; unauthorized order submission |
| Controls | (1) NFR-05: zero hardcoded secrets policy. (2) Vault-based secrets management (implementation TBD at G2). (3) SECRETS_HANDLING.md governs all credential workflows. (4) Pre-commit hook or manual audit before any external repository push. |
| Residual risk | LOW (Phases 0–5, no live credentials exist yet) → HIGH (Phase 8, review at G5) |
| Related FM | N/A (new at G5) |
| Revisit trigger | Venue credentials created (ACC-0002); any external repository connection |

---

## TH-03 — Shadow Documentation / Governance Erosion (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Decisions made outside the directory; artifacts drift from reality; context rot recurs |
| Category | Integrity (Accidental) |
| Attack vector | Internal (process failure) |
| Affected components | All (governance layer) |
| Likelihood | HIGH — This is the identified cause of the previous iteration failure |
| Impact | HIGH — Loss of reproducibility; handoff failure; invalid decisions based on stale information |
| Controls | (1) Compass OS cadences mandatory. (2) Universal headers on all artifacts. (3) Anti-shadow-doc rule: 72-hour absorption deadline. (4) M1 freshness metric tracked weekly. (5) Escalation ladder: M1 < 85% → owner ping; < 75% → accountable review; < 65% → gate freeze. |
| Residual risk | MEDIUM — Process-based controls depend on operator discipline |
| Related FM | FM-08 |
| Revisit trigger | Quarterly retrieval drill; DIR health report below M1 threshold |

---

## TH-04 — Order Duplication / Double Submission (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Same order submitted twice due to retry logic or timeout; double position taken |
| Category | Integrity (Accidental) |
| Attack vector | Internal (network failure + retry without idempotency check) |
| Affected components | C5 (Phase 6+) |
| Likelihood | MEDIUM — Network failures are common; retry logic error is a known failure class |
| Impact | HIGH — Position exceeds approved limit; may breach risk limits |
| Controls | (1) idempotency_key required on all orders (IF-C5-VENUE). (2) Deduplication log in C6. (3) Venue confirmation checked before retry. |
| Residual risk | LOW (with idempotency key correctly implemented) |
| Related FM | FM-05 |
| Revisit trigger | Venue API change; any network failure event in paper/live trading |

---

## TH-05 — Kill Switch Failure (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Kill switch triggered but does not halt all components; losses continue |
| Category | Safety (Accidental) |
| Attack vector | Internal (implementation error in kill switch wiring) |
| Affected components | C7, all active components |
| Likelihood | LOW (if tested) → HIGH (if not tested before live use) |
| Impact | CRITICAL — Uncontrolled continued operation after halt signal |
| Controls | (1) Kill signal broadcast to all components simultaneously. (2) Each component independently checks kill flag. (3) Kill switch drill mandatory at G5 before any live use. (4) C7 monitors independently of C4. |
| Residual risk | LOW (if G5 drill passes) → CRITICAL (if G5 drill skipped) |
| Related FM | FM-06 |
| Revisit trigger | New component added; kill switch drill failure; architecture change |

---

## TH-06 — Model Overfitting / False Edge (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Model shows positive backtest performance due to overfitting; no real edge in live markets |
| Category | Integrity (Accidental) |
| Attack vector | Internal (insufficient validation discipline) |
| Affected components | C3 |
| Likelihood | HIGH — Overfitting is the dominant failure mode in predictive modeling |
| Impact | HIGH — Live capital deployed on a model with zero or negative EV |
| Controls | (1) Hold-out test set never used during development (accessed only at G4). (2) Null model comparison mandatory (market_implied_prob baseline). (3) Calibration curves required. (4) ≥3 independent experiments required for G4 evidence. (5) Risk limits prevent catastrophic drawdown even if model has negative edge. |
| Residual risk | MEDIUM — No guarantee of live edge; residual risk accepted and managed by risk limits |
| Related FM | FM-03 |
| Revisit trigger | G4 evidence review; live Brier score monitoring |

---

## TH-07 — Unauthorized Capital Deployment (Process Failure)

| Attribute | Detail |
|-----------|--------|
| Threat | Real capital deployed before G6 gate is cleared; premature live trading |
| Category | Safety (Process Failure) |
| Attack vector | Internal (gate bypass by operator) |
| Affected components | C5 (Phase 8) |
| Likelihood | LOW — Solo operator; temptation risk present without process controls |
| Impact | CRITICAL — Unvalidated model exposed to real capital loss |
| Controls | (1) C5 live mode hard-gated behind ADR-0005 acceptance. (2) Live venue credentials not created until G5+. (3) APR-0009 signature required. (4) G6 checklist explicit in ACCEPTANCE_CRITERIA.md. |
| Residual risk | LOW (process controls in place; single operator risk accepted) |
| Related FM | FM-04 |
| Revisit trigger | Any attempt to access live venue API before G6 |

---

## TH-08 — Stale Model in Production (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Market regime changes; model continues operating on stale assumptions; edge decays undetected |
| Category | Integrity (Accidental) |
| Attack vector | Environmental (market change) + Internal (monitoring gap) |
| Affected components | C3 (model), C7 (monitoring) |
| Likelihood | MEDIUM-HIGH — Market regimes do shift; signal decay is a known risk |
| Impact | HIGH — Continued operation generates negative EV |
| Controls | (1) Brier score monitoring on rolling 30-event window (FM-03). (2) Auto-alert at drift threshold. (3) No automated retraining in production — retraining requires ADR + new model version. (4) MONITORING_DRIFT_PLAN.md defines response. |
| Residual risk | MEDIUM — Monitoring provides early warning; action depends on operator response |
| Related FM | FM-03 |
| Revisit trigger | Live deployment; any drift alert |

---

## TH-09 — Audit Log Tampering or Loss (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Audit log modified, deleted, or corrupted; decision history unrecoverable |
| Category | Integrity (Accidental) |
| Attack vector | Internal (storage failure, process crash during write) |
| Affected components | C6 |
| Likelihood | LOW (if append-only enforced) |
| Impact | HIGH — Loss of auditability; governance invariant violated; cannot reconstruct decisions |
| Controls | (1) Append-only log format; no modification path. (2) Write confirmation before acknowledging event. (3) Log integrity check (hash verification). (4) Backup rotation per DATA_RETENTION_DELETION.md. |
| Residual risk | LOW |
| Related FM | FM-07 |
| Revisit trigger | Storage architecture change; any disk failure event |

---

## Threat Summary Matrix

| ID | Threat | Likelihood | Impact | Net Risk | Status |
|----|--------|------------|--------|----------|--------|
| TH-01 | Data contamination / look-ahead bias | HIGH | CRITICAL | CRITICAL | Mitigated (automated checks required) |
| TH-02 | Credential exposure | MED (now LOW, HIGH at G6) | HIGH | MED→HIGH | Mitigated (no live creds in Phases 0–5) |
| TH-03 | Shadow docs / context rot | HIGH | HIGH | HIGH | Mitigated (Compass OS cadences) |
| TH-04 | Order duplication | MED | HIGH | MED | Mitigated (idempotency key) |
| TH-05 | Kill switch failure | LOW (if tested) | CRITICAL | MED | Mitigated (G5 drill required) |
| TH-06 | Overfitting / false edge | HIGH | HIGH | HIGH | Partially mitigated (G4 evidence required) |
| TH-07 | Premature live capital | LOW | CRITICAL | MED | Mitigated (hard gate controls) |
| TH-08 | Stale model in production | MED | HIGH | MED | Mitigated (drift monitoring) |
| TH-09 | Audit log loss | LOW | HIGH | LOW | Mitigated (append-only + backup) |

---

## Threats Out of Scope (Phases 0–5)

The following threat categories are noted but out of scope until Phase 6+:

| Threat Category | Reason Deferred |
|-----------------|-----------------|
| External adversarial attacks on venue API | No live credentials exist; external attack surface is zero |
| Account takeover / venue fraud | No live account until G5+ |
| Price manipulation / market adversary | Cannot be fully mitigated; managed by position sizing limits |
| Regulatory/compliance action | Tracked in POLICY_REQUIREMENTS.md; no live trading until G6 |

**Expand this threat model at G5** before any live venue connection is established.
