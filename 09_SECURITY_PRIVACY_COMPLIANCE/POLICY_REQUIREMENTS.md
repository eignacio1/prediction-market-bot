# Policy Requirements — Prediction Market Trading Bot

**Purpose:** Define the policy obligations the system must comply with, their source, and how compliance is demonstrated. Covers regulatory, platform terms-of-service, and internal policy requirements.  
**Owner (role):** Risk and Compliance Owner (RCO)  
**Last reviewed:** 2026-05-22  
**Next review:** G3 (venue selected — TOS confirmed); G5 (pre-live compliance audit); update when venue or jurisdiction changes  
**Staleness triggers:** Venue selected (OQ-006); jurisdiction confirmed (OQ-003); regulatory change; new policy obligation identified  
**Upstream links:** RISK_APPETITE_CONSTRAINTS.md, ADR-0003 (venue TBD), SCOPE_IN_OUT.md  
**Downstream links:** CONTROL_MAPPING.md, VENDOR_RISK.md, APPROVALS_REGISTER.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 4/10 — Framework correct; venue-specific and jurisdiction-specific obligations pending OQ-006 resolution

---

## Policy Obligation Register

### POL-001 — Venue Terms of Service

| Field | Detail |
|-------|--------|
| Policy ID | POL-001 |
| Source | Venue TOS (TBD — ADR-0003) |
| Status | PENDING — venue not selected |
| Scope | All interactions with the venue API (order submission, market data, account access) |
| Key obligations (known at this stage) | Rate limiting compliance; no wash trading; account identity verification; withdrawal of API access if TOS violated |
| Compliance mechanism | API rate limiter in C4/C5; no self-crossing logic; operator identity registration |
| Evidence | API usage logs (C6); venue account documentation |
| Verification gate | G3 (TOS review before venue selection finalized) |
| Open question | OQ-006 — venue selection determines specific obligations |

**Assumption:** Prediction market venues (Kalshi, Polymarket) operate as legal exchanges or regulated platforms in the operator's jurisdiction. If this assumption is false, trading may require licensing or registration. Flag immediately if venue review reveals regulatory obligations not covered here.

---

### POL-002 — Data Privacy (Personal Data)

| Field | Detail |
|-------|--------|
| Policy ID | POL-002 |
| Source | Applicable privacy law (jurisdiction TBD — OQ-003) |
| Status | LOW RISK CURRENTLY — DS-01 contains player attributes, not personal contact data for a consumer population |
| Scope | Any personal data ingested into the system |
| Key obligations | Purpose limitation; data minimization; retention limits; no unauthorized sharing |
| DS-01 assessment | Player_Attribute_Matrix contains athletic performance attributes. Likely not subject to consumer privacy law (GDPR, CCPA) unless players are private individuals with no public athlete status. Confirm at OQ-001 resolution. |
| Compliance mechanism | DATA_RETENTION_DELETION.md; no data sharing (single operator, local environment) |
| Evidence | Data provenance documentation (DATA_PROVENANCE.md); retention policy |
| Verification gate | G1 (confirm DS-01 data nature at provenance review) |

---

### POL-003 — Financial Regulation

| Field | Detail |
|-------|--------|
| Policy ID | POL-003 |
| Source | CFTC (US); applicable jurisdiction regulator |
| Status | MONITORING — scope depends on venue classification and jurisdiction |
| Scope | Live capital deployment (Phase 8+) |
| Key obligations | Potential registration as a Commodity Pool Operator (CPO) if operating on behalf of others; reporting obligations if trading volume exceeds thresholds |
| In-scope assessment | Single operator trading own capital on a CFTC-regulated venue (e.g., Kalshi) = likely retail trader status, no CPO registration required. Confirm with venue compliance documentation at G3. |
| Compliance mechanism | Single operator only; no external capital; trading on regulated venue only |
| Evidence | Venue compliance documentation; operator account classification |
| Verification gate | G3 (venue selection with regulatory review) |
| Open question | OQ-006 — venue regulatory status |

---

### POL-004 — Internal Information Security Policy (NFR-05)

| Field | Detail |
|-------|--------|
| Policy ID | POL-004 |
| Source | Internal — NFR-05 (Zero Hardcoded Secrets) |
| Status | ACTIVE |
| Scope | All code, configuration, VCS, logs, and documentation |
| Key obligations | No secrets in code; no secrets in git history; no secrets in logs; vault/env-var protocol only |
| Compliance mechanism | C-001 (CONTROL_MAPPING.md); bandit pre-commit hook; SECRETS_HANDLING.md protocol |
| Evidence | Pre-commit audit logs; bandit scan results |
| Verification gate | Ongoing — checked at every phase gate |

---

### POL-005 — Internal Governance Policy (ADR Immutability)

| Field | Detail |
|-------|--------|
| Policy ID | POL-005 |
| Source | Internal — ADR-0001; CHANGE_CONTROL.md |
| Status | ACTIVE |
| Scope | All Class A change types (strategy, risk limits, model promotion, capital authorization) |
| Key obligations | ADR required before implementation; ADRs are immutable once accepted; no shadow changes |
| Compliance mechanism | C-006 (CONTROL_MAPPING.md); CHANGE_CONTROL.md; DECISION_LOG.md |
| Evidence | ADR index in DECISION_LOG.md; APPROVALS_REGISTER.md sign-offs |
| Verification gate | G0 exit and every subsequent gate |

---

### POL-006 — No Automated Retraining Policy

| Field | Detail |
|-------|--------|
| Policy ID | POL-006 |
| Source | Internal — MODEL_CARD.md Governance; REJECTED_OPTIONS.md RO-007 |
| Status | ACTIVE |
| Scope | All production environments (ENV-02, ENV-03) |
| Key obligations | Model frozen at deployment; retraining requires new ADR + new model version + G4-equivalent evidence |
| Compliance mechanism | C-010 (CONTROL_MAPPING.md); ARTIFACT_REGISTRY.md promotion gates |
| Evidence | Model artifact version audit; production environment check |
| Verification gate | G5 (pre-paper), G6 (pre-live) |

---

## Compliance Gap Register

Gaps are items where compliance cannot yet be confirmed due to open decisions.

| Gap ID | Policy | Gap Description | Resolution Path | Due |
|--------|--------|----------------|-----------------|-----|
| GAP-001 | POL-001 | Venue TOS not reviewed | Resolve OQ-006; review TOS at ADR-0003 | G3 |
| GAP-002 | POL-002 | DS-01 privacy classification pending | Resolve OQ-001; confirm player data nature | G1 |
| GAP-003 | POL-003 | Regulatory status not confirmed | Venue selection + regulatory review | G3 |

---

## Compliance Attestation Requirements

Before G5 (paper trading authorization), RCO must attest:
- [ ] POL-001: Venue TOS reviewed and complied with
- [ ] POL-002: DS-01 data privacy classification confirmed
- [ ] POL-003: Regulatory status confirmed; operator classification documented
- [ ] POL-004: Secret isolation controls verified (bandit scan, no secrets in VCS)
- [ ] POL-005: ADR chain complete and immutable
- [ ] POL-006: No automated retraining path exists in production code

Before G6 (live capital authorization), RCO must additionally confirm:
- [ ] GAP-001, GAP-002, GAP-003 all resolved with documented evidence
- [ ] Operator compliance self-review: all identified regulatory obligations documented, assessed, and accepted or mitigated (operator is sole decision-maker; no external counsel routing)
