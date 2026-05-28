# Access Control Matrix — Prediction Market Trading Bot

**Purpose:** Define who has access to what resources, under what conditions, and with what permissions. Single source of truth for access rights across all environments.  
**Owner (role):** Risk and Compliance Owner (RCO) + Director/Sponsor (DS)  
**Last reviewed:** 2026-05-22  
**Next review:** G5 (pre-live audit); update when new role, resource, or environment added  
**Staleness triggers:** New environment activated; new API credential provisioned; role change; live capital deployment  
**Upstream links:** ENVIRONMENTS.md, SECRETS_HANDLING.md, STAKEHOLDERS_RACI.md  
**Downstream links:** CONTROL_MAPPING.md (C-001, C-005), AUDIT_EVIDENCE/  
**Decision references:** ADR-0001  
**Confidence:** 7/10 — Matrix is complete for current roles; environment-specific access governed at G5

---

## Roles

This is a single-operator system. All roles are held by the same individual (Earl Ignacio). The role separation is conceptual — it ensures accountability and prevents the "operator=owner=no-check" failure mode common in solo projects.

| Role ID | Role Name | Abbreviation | Responsibilities |
|---------|-----------|-------------|-----------------|
| R-01 | Director/Sponsor | DS | Final authority on strategy, capital allocation, gate approvals |
| R-02 | Research Lead | RL | Experiment design, feature engineering, model development |
| R-03 | Model Owner | MO | Model promotion, monitoring, drift response |
| R-04 | Risk and Compliance Owner | RCO | Risk limit enforcement, control audit, gate sign-off |
| R-05 | Methodology Validator | MV | Structured methodology self-review: calibration check, test design challenge, documented self-challenge log (solo build — operator performs this role with explicit written justification per CHANGE_CONTROL.md Class A) |
| R-06 | Infrastructure Operator | IO | Environment provisioning, secrets management, deployment |

**Note:** In a solo project, wearing multiple hats is unavoidable. The governance mitigation is: for any Class A change (CHANGE_CONTROL.md), the operator must explicitly document the decision in the role of each relevant owner — not just act as "the operator."

---

## Resource Inventory

| Resource ID | Resource | Classification | Phase Active |
|-------------|----------|---------------|-------------|
| RES-01 | DS-01 Player_Attribute_Matrix file | RESEARCH | Phase 3+ |
| RES-02 | DS-02 Market Data Feed (read-only) | SENSITIVE | Phase 5+ |
| RES-03 | DS-03 Outcome / Resolution Data | SENSITIVE | Phase 5+ |
| RES-04 | Venue API (read-only market data) | SENSITIVE | Phase 5+ |
| RES-05 | Venue API (order submission) | CRITICAL | Phase 8+ |
| RES-06 | Model artifacts (ARTIFACT_REGISTRY.md) | INTERNAL | Phase 3+ |
| RES-07 | Audit logs (C6 output) | SENSITIVE | Phase 3+ |
| RES-08 | Live capital funds | CRITICAL | Phase 8+ |
| RES-09 | Git repository / VCS | INTERNAL | All phases |
| RES-10 | Secrets vault / env variables | CRITICAL | All phases |
| RES-11 | Kill switch interface | CRITICAL | Phase 5+ |
| RES-12 | Paper trading position state | INTERNAL | Phase 6+ |

---

## Access Matrix

Permission codes: R = Read, W = Write, E = Execute, A = Admin, — = No access

| Resource | R-01 DS | R-02 RL | R-03 MO | R-04 RCO | R-05 MV | R-06 IO |
|----------|---------|---------|---------|---------|---------|---------|
| RES-01 DS-01 file | R | R/W | R | R | R | — |
| RES-02 Market Data Feed | R | R | R | R | R | R |
| RES-03 Outcome Data | R | R | R | R | R | — |
| RES-04 Venue API (read) | R | — | R | R | — | R |
| RES-05 Venue API (orders) | **A** | — | E¹ | R (audit) | — | — |
| RES-06 Model artifacts | R | R/W | R/W | R | R | — |
| RES-07 Audit logs | R | — | R | R/W | R | — |
| RES-08 Live capital funds | **A** | — | — | R (audit) | — | — |
| RES-09 Git repo | R | R/W | R | R | R | R/W |
| RES-10 Secrets vault | — | — | — | A | — | A |
| RES-11 Kill switch | **A** | — | E | A | — | E |
| RES-12 Paper trading state | R | R | R/W | R | R | R |

¹ RES-05 (Venue API order submission): Model Owner executes orders only within approved risk limits; any order outside limits is rejected by C4 Risk Engine before transmission.

---

## Access Conditions

### RES-05 (Venue API order submission) — Live Capital Only

Access to live order submission is gated by **all** of the following:
1. G6 Release Gate cleared (APPROVALS_REGISTER.md, DS sign-off)
2. ADR-0005 (Live Capital Authorization) accepted
3. Kill switch tested and confirmed ≤60s halt (TC-009, TC-010)
4. Risk limits confirmed in RISK_APPETITE_CONSTRAINTS.md (ADR required for any change)
5. No position open outside automated risk engine enforcement

### RES-10 (Secrets vault / env variables)

- Access limited to RCO and IO roles at time of provisioning
- Secrets never logged, never in code, never in VCS (NFR-05)
- Rotation schedule documented in SECRETS_HANDLING.md
- Vault solution TBD at G5 (OQ-009)

### RES-11 (Kill switch)

- Manual trigger: any operator action during observed anomaly
- Automatic trigger: C7 monitoring on limit breach
- No bypass path — kill switch is the only emergency response
- Post-trigger: state logged to C6; manual restart requires written decision in RID_LOG.md

---

## Environment-Specific Access Rules

| Environment | Market Data | Order API | Live Funds | Kill Switch |
|-------------|-------------|-----------|------------|-------------|
| ENV-01 Research | Snapshots only (read) | NOT CONNECTED | NOT CONNECTED | N/A |
| ENV-02 Paper Trading | Live feed (read) | Simulated only | NOT CONNECTED | Active |
| ENV-03 Live Capital | Live feed (read) | ACTIVE | ACTIVE | Active |

**ENV-01 isolation rule:** No live credentials may exist in ENV-01. If a credential is needed for market data access in Phase 5+, it must be scoped read-only and managed via vault.

---

## Access Review Schedule

| Event | Review Required |
|-------|----------------|
| Phase gate cleared | Verify new resources activated match matrix |
| New API credential provisioned | Update RES table; RCO sign-off |
| Live capital deployment (Phase 8) | Full access audit; DS + RCO sign-off |
| Suspected unauthorized access | Immediate audit; log to RID_LOG.md |
| Annual (if project reaches that milestone) | Full matrix re-review |
