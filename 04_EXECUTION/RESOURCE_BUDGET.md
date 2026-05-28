# Resource and Budget — Prediction Market Trading Bot

**Purpose:** Track time, compute, and capital resources. Ensures capital constraints are documented and gate-controlled.  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-05-22  
**Next review:** Monthly; update at each gate; update on any capital authorization  
**Staleness triggers:** Capital authorization approved; phase gate passed; compute spend changes  
**Upstream links:** PROJECT_CHARTER.md, RISK_APPETITE_CONSTRAINTS.md  
**Downstream links:** PLAN.md, 00_ADMIN/APPROVALS_REGISTER.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 7/10 — Phase 0–5 resources well-understood (minimal); live capital amount TBD at G6

---

## Capital Budget by Phase

| Phase | Capital Type | Amount | Authorization | Status |
|-------|-------------|--------|---------------|--------|
| 0 — Scaffolding | Real | $0 | None required | ✅ Confirmed |
| 1 — Spec | Real | $0 | None required | ✅ Confirmed |
| 2 — Architecture | Real | $0 | None required | ✅ Confirmed |
| 3 — Research Build | Real | $0 (data costs only) | None required | ✅ Confirmed |
| 4 — Validation | Real | $0 | None required | ✅ Confirmed |
| 5 — Operational Readiness | Real | $0 | None required | ✅ Confirmed |
| 6 — Paper Trading | Simulated | Simulated | ADR-0004 | 🔴 Pending |
| 7 — Promotion Gate | Real | $0 | None required | 🔴 Pending |
| 8 — Live Capital | Real | TBD at G6 | ADR-0005 + APR-0008 + APR-0009 + G6 | 🔴 Pending |

**Hard rule:** No real capital is deployed at any phase until G6 Release Gate is cleared and APR-0009 is signed. Breaching this rule is a CRITICAL governance failure (TH-07).

---

## Time Budget

| Phase | Estimated Effort | Notes |
|-------|-----------------|-------|
| 0 — Scaffolding | ~40 hours | Directory build, all 12 modules, Context Pack |
| 1 — Spec | ~8 hours | Refining + freezing spec artifacts; resolving OQ-001/OQ-003 |
| 2 — Architecture | ~16 hours | Review and canonicalize Phase 0 DRAFT architecture artifacts |
| 3 — Research Build | ~80 hours | C1–C3 pipeline; first experiments; backtesting framework |
| 4 — Validation | ~40 hours | Evidence collection; model card; G4 sign-offs |
| 5 — Operational Readiness | ~40 hours | C7 wiring; kill switch drill; secrets vault; G5 checklist |
| 6 — Paper Trading | Ongoing | Minimum N events (TBD at ADR-0004) |
| 7 — Promotion Gate | ~8 hours | Evidence review; G6 checklist |
| 8 — Live Capital | Ongoing | Monitoring; incident response; quarterly reviews |

*All time estimates are solo-operator effort. Adjustments required if scope changes.*

---

## Compute Resources

| Phase | Resource | Estimated Usage | Cost Basis |
|-------|----------|----------------|------------|
| 0–4 | Local machine | All research and backtesting | $0 (local) |
| 5+ | Local + potential cloud | Model training at scale if needed | TBD at G5 |
| 8 | Venue API access | Per-request; venue fee structure | TBD at ADR-0003 |

---

## Data Cost Estimates

| Source | Cost | Notes |
|--------|------|-------|
| DS-01 (Player_Attribute_Matrix) | $0 | Already available; static file |
| DS-02 (Market Data Feed) | TBD | Depends on venue API pricing (ADR-0003) |
| DS-03 (Outcome Data) | TBD | Likely bundled with DS-02 via venue API |

---

## Live Capital Sizing Parameters (TBD at G6)

*Specific amounts are not set until G6 gate evidence supports sizing decisions.*

| Parameter | Value | Basis | Status |
|-----------|-------|-------|--------|
| Initial capital allocation | TBD | Evidence-based at G6; fraction of available capital | Pending G6 |
| Maximum single-event exposure | ≤5% of capital (placeholder) | RISK_APPETITE_CONSTRAINTS.md | Confirm at G4 |
| Maximum daily loss | ≤10% of capital (placeholder) | RISK_APPETITE_CONSTRAINTS.md | Confirm at G4 |
| Replenishment policy | TBD | No replenishment during Phase 8 without separate authorization | Pending G6 |

*Placeholders in RISK_APPETITE_CONSTRAINTS.md; confirmed with Brier evidence at G4.*
