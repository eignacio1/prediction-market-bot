# Access Requests — Prediction Market Trading Bot

**Purpose:** Track all access grants for data, compute, secrets, and external systems. Every access point is documented before use.  
**Owner (role):** Risk/Control Owner (RCO)  
**Last reviewed:** 2026-05-28 (ACC-0002 granted — Kalshi API read-only key provisioned)  
**Next review:** Monthly, or when any new access is requested  
**Staleness triggers:** New API integration; new data source; new compute environment; credential rotation; venue confirmed  
**Upstream links:** PROJECT_CHARTER.md, 09_SECURITY_PRIVACY_COMPLIANCE/ACCESS_CONTROL_MATRIX.md  
**Downstream links:** 06_CODE_EXECUTION_REPRODUCIBILITY/SECRETS_HANDLING.md  
**Decision references:** ADR-0001  
**Confidence:** 9/10 — Skeleton in place; rows populate as access is requested  

---

## Active Access Grants

| Access ID | Access Type | Resource / System | Requester Role | Justification | Approver Role | Approval Date | Evidence Link | Expiry |
|-----------|------------|-------------------|---------------|---------------|--------------|--------------|---------------|--------|
| ACC-0001 | Filesystem | Prediction Markets project directory | DS | Project development | DS | 2026-05-21 | This document | Ongoing |
| ACC-0002 | API credentials (read-only) | Kalshi trading API (`trading-api.kalshi.com`) | IO / DS | Live market price data for DS-02; EXP-004 (HYP-003 vig test); Phase 5 operational readiness | DS | 2026-05-28 | ADR-0003 APR-0011; VENUE_API_KEY in ENV-01 `.env` (gitignored; NFR-05) | Rotate on any suspected compromise; review at G5 |

---

## Pending / Future Access

| Access ID | Access Type | Resource / System | Justification | Required By Gate | Status |
|-----------|------------|-------------------|---------------|-----------------|--------|
| ACC-0002 | API credentials (read-only) | Kalshi trading API | Live data ingestion; EXP-004 (HYP-003) | G5 (Ops) minimum | ✅ GRANTED 2026-05-28 — moved to Active Grants above |
| ACC-0003 | External data feed | Player/market attribute data source | Signal enrichment beyond Player_Attribute_Matrix | G1 (Spec) | PENDING — DATA_REQUIREMENTS.md sign-off required |
| ACC-0004 | Secrets vault | API keys, credentials storage | Secure credential management | G4 (Evidence) | PENDING |
| ACC-0005 | Production compute | Cloud / server environment | Live execution | G5 (Ops) | PENDING |

---

## Access Control Rules

1. No API credentials may be stored in plaintext or in code files. See SECRETS_HANDLING.md.
2. No external venue access (read or write) without an approved ACC entry in this register.
3. Any new access grant must be reflected in ACCESS_CONTROL_MATRIX.md within 24h of approval.
4. Access that has not been reviewed within its stated expiry period is automatically suspended pending re-approval.
