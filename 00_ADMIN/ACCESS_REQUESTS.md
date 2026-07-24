# Access Requests — Prediction Market Trading Bot

**Purpose:** Track all access grants for data, compute, secrets, and external systems. Every access point is documented before use.  
**Owner (role):** Risk/Control Owner (RCO)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: fixed genuine drift (ACC-0005 production compute showed PENDING; the VPS has been live in production for paper trading since ~2026-06). ACC-0004 clarified as accepted-for-now open item per T-352/GG-093, not silently stale. ACC-0003 (Polymarket) still accurately PENDING — KYC-gated, unchanged.  
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
| ACC-0003 | API credentials (read-only) | Polymarket US CLOB API (`clob.polymarket.com`) | Line shopping (Strategy E); complement lock detection (Strategy C); VenueRouter best_price mode activation | Phase 7 (T-077) | **PENDING PROVISIONING** — operator must create account at polymarket.com and generate API key; see RUNBOOK_polymarket-activation.md |
| ACC-0004 | Secrets vault | API keys, credentials storage | Secure credential management | G4 (Evidence) | OPEN, accepted-for-now — system runs on `.env` + systemd `EnvironmentFile=` in production (not a formal vault); OQ-009 tracks formal vault adoption; not blocking per T-352/GG-093 (2026-07-21) |
| ACC-0005 | Production compute | Cloud / server environment (VPS 157.230.91.33, DigitalOcean) | Live paper-trading execution | G5 (Ops) | ✅ GRANTED — live since Phase 6 cutover (~2026-06); T1/T2/T4 MLB cron + systemd services running in production on this host |

---

## Access Control Rules

1. No API credentials may be stored in plaintext or in code files. See SECRETS_HANDLING.md.
2. No external venue access (read or write) without an approved ACC entry in this register.
3. Any new access grant must be reflected in ACCESS_CONTROL_MATRIX.md within 24h of approval.
4. Access that has not been reviewed within its stated expiry period is automatically suspended pending re-approval.
