# RID Log — Risks, Issues, Dependencies — Prediction Market Trading Bot

**Purpose:** Centralized tracker for all active risks, issues, and dependencies that require monitoring or resolution. The canonical escalation source for gate reviews.  
**Owner (role):** Execution Lead (EL)  
**Status:** **CANONICAL — G3 Execution Gate 2026-05-22** — Changes require version bump and CHANGELOG entry  
**Last reviewed:** 2026-05-28 (DS-02-B-001 RESOLVED — hotel wifi also confirmed working; block is home ISP + work ISP specific; mobile hotspot and hotel wifi both pass Kalshi CloudFront WAF)  
**Next review:** Weekly DIR; escalate P1 items immediately  
**Staleness triggers:** New risk identified; issue resolved; dependency unblocked; gate readiness review  
**Upstream links:** PLAN.md, RESILIENCE_FAILURE_MODES.md, OPEN_QUESTIONS.md  
**Downstream links:** STATUS_REPORTS/, COMMUNICATIONS_PLAN.md (escalation)  
**Decision references:** ADR-0001, ADR-0002, ADR-0003 (PENDING)  
**Confidence:** 8/10 — Known risks catalogued; G3 baseline clean; unknown risks surface during Phase 3

---

## RID Classification

| Type | Code | Meaning |
|------|------|---------|
| Risk | R | Known uncertainty that could negatively affect the project if it materializes |
| Issue | I | Active problem already affecting the project |
| Dependency | D | External item that must be resolved before work can proceed |

| Priority | Meaning |
|----------|---------|
| P1 | Blocks current phase gate or puts capital at risk |
| P2 | Blocks a specific milestone; must resolve before it can complete |
| P3 | Background risk; monitor and reassess at each gate |

---

## Active Risks

| RID | Type | Priority | Title | Description | Probability | Impact | Owner | Mitigation | Status | Gate |
|-----|------|----------|-------|-------------|-------------|--------|-------|-----------|--------|------|
| RID-001 | R | P1 | Context rot recurrence | Solo operator without peer accountability may allow cadences to slip, reproducing prior iteration failure | HIGH | CRITICAL | DS | Compass OS cadences; M1 metric tracked weekly; escalation ladder | ACTIVE | All |
| RID-002 | R | P1 | Player_Attribute_Matrix has no predictive signal | ASM-001 may be false; no edge found in Phase 3 experiments | MEDIUM | HIGH | RL | Null model comparison required; G4 evidence gate; ADR-0002 revisit criteria | ACTIVE | G4 |
| RID-003 | R | P2 | Venue API change invalidates interface design | Venue selection (ADR-0003) pending G3 formal acceptance (OQ-006); interface contracts may need revision after venue confirmed | MEDIUM | MEDIUM | AO | Versioned interface contracts (CANONICAL G2 2026-05-22); IF-C5-VENUE gated behind ADR-0003; G2 architecture artifacts now canonical — partial mitigation | ACTIVE — partially mitigated | G3 |
| RID-004 | R | P2 | Overfitting in backtest | Model appears to have edge due to overfitting, not real signal | HIGH | HIGH | RL | Hold-out test set; ≥3 independent experiments; calibration curves | ACTIVE | G4 |
| RID-005 | R | P3 | Timeline slip due to solo operator | Single operator across all roles means illness, distraction, or competing demands can delay every phase | MEDIUM | MEDIUM | DS | Realistic milestone dates; explicit buffers in Phase 3+ | ACTIVE | All |
| RID-006 | R | P3 | Kill switch not tested before G5 | Kill switch implementation error discovered after live capital deployed | LOW | CRITICAL | AO | Mandatory kill switch drill at G5 before any live use | ACTIVE | G5 |

---

## Active Issues

| RID | Type | Priority | Title | Description | Owner | Resolution Path | Status | Due |
|-----|------|----------|-------|-------------|-------|----------------|--------|-----|
| DS-02-B-001 | I | P1 | Kalshi API IP/ASN block (CloudFront WAF) | **RESOLVED 2026-05-28.** Root cause: IP/ASN-based block by Kalshi CloudFront WAF — home ISP and work ISP blocked; mobile hotspot and hotel wifi both work (different ASN). EXP-004 Part B executed on mobile hotspot (session EXP-004-FE3E2169). Confirmed hotel wifi also passes (2026-05-28). For Phase 6+ scheduled runs, a datacenter VPS (clean ASN) is required — not needed for manual runs. | IO/DS | RESOLVED — mobile hotspot and hotel wifi both confirmed working. Phase 6 VPS provisioning required for scheduled cron runs. | RESOLVED 2026-05-28 | — |

---

## Active Dependencies

| RID | Type | Priority | Title | What's Needed | Owner | Unblocks | Status | ETA |
|-----|------|----------|-------|--------------|-------|----------|--------|-----|
| RID-D001 | D | P1 | Venue selection (ADR-0003) | ADR-0003 ACCEPTED (APR-0011 2026-05-23); Kalshi primary confirmed; OQ-006 resolved. ACC-0002 granted 2026-05-28 (read-only key in ENV-01 .env). Blocked only by DS-02-B-001 (TLS connectivity). | AO | DS-02 (connectivity pending DS-02-B-001 resolution) | PARTIALLY RESOLVED — ADR accepted, creds obtained, connectivity blocked | DS-02-B-001 |
| RID-D004 | D | P3 | Secrets vault selection | Vault tooling chosen and configured | AO | ACC-0002; live credentials | OPEN | G5 |

---

## Resolved RIDs (Archive)

| RID | Type | Title | Resolution | Date |
|-----|------|-------|-----------|------|
| RID-006 | R | Kill switch not tested before G5 | APR-0013 signed 2026-05-28: TC-007 kill switch drill passed at 0.340ms (SLA 60,000ms); KS-C8D7D90AF942; VALIDATION_SIGNOFF.md TC-007 row complete | 2026-05-28 |
| RID-D002 | D | Player_Attribute_Matrix provenance (OQ-001) | OQ-001 RESOLVED: Creator = Earl Ignacio; Date = 2026-05-21; Sport = NBA; Document = "Weighted Hybrid PRF System — A Dynamically Agnostic Framework for Player Archetype Classification" (v4.0); SNAP-001 registered in DATA_SNAPSHOTS_INDEX.md | 2026-05-22 |
| RID-D003 | D | Target market category (OQ-003) | OQ-003 RESOLVED: NBA basketball; dynamically agnostic event types; Kalshi as primary venue for initial deployment; multi-venue (CA-legal) for full deployment per ADR-0003 | 2026-05-22 |
