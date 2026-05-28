# Decision Log — Prediction Market Trading Bot

**Purpose:** Chronological index of all decisions (ADRs, approvals, and notable judgment calls) made during this project. Single source of truth for "why did we decide X."  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-05-28 (G4 Evidence Gate — ADR-0004 ACCEPTED via APR-0012; G4 gate CLOSED)  
**Next review:** G5 Operational Gate; any new ADR/approval  
**Staleness triggers:** New ADR accepted; approval decision made; major judgment call not captured elsewhere  
**Upstream links:** 03_DECISIONS/  
**Downstream links:** 00_ADMIN/APPROVALS_REGISTER.md, all ADRs  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 9/10 — Current decisions fully logged; completeness depends on ongoing discipline

---

## ADR Index

| ADR ID | Title | Status | Date | Gate |
|--------|-------|--------|------|------|
| ADR-0001 | Adopt Compass OS as Project Governance Framework | ACCEPTED | 2026-05-21 | G0 |
| ADR-0002 | Strategy Class: Forecast-Only Research (No Arbitrage) | ACCEPTED | 2026-05-21 | G0/G1 |
| ADR-0003 | Venue Selection (Kalshi Primary; CA-Legal Multi-Venue) | ACCEPTED | 2026-05-23 | G3 |
| ADR-0004 | Model Class: LogisticRegression + Platt Scaling (Phase 3 Baseline) | ACCEPTED | 2026-05-28 | G4 (APR-0012) |
| ADR-0005 | Live Capital Authorization | PENDING | TBD | G6 |

---

## Notable Judgment Calls

*Decisions that do not rise to ADR level but are recorded to prevent future confusion.*

| Date | Decision | Rationale | Owner |
|------|----------|-----------|-------|
| 2026-05-21 | arb/ folder designated reference-only | Prior iteration contamination risk; no validation history; requires formal ADR (APR-0010) before any use | DS |
| 2026-05-21 | Player_Attribute_Matrix staged as research input only, not canonical | Provenance requires independent validation; source details need documentation | RL |
| 2026-05-21 | All nine governance roles assigned to solo operator (Earl Ignacio) | Solo build; role definitions preserved for future team scaling | DS |
| 2026-05-21 | Technology stack deferred to G2 | Cannot finalize stack without venue API constraints and data volume estimates | AO |
| 2026-05-22 | Risk limit thresholds marked TBD at G4 | Thresholds must be grounded in Brier score evidence; premature specification creates false precision | RCO |

---

## Decision Principles

These principles guide all decisions in this project:

1. **No decision is reversible without a superseding ADR.** ADRs are immutable once accepted.
2. **"We'll fix it later" is a shadow commitment.** If it matters, log it as an open question or RID.
3. **Deferred decisions must have a named gate.** "TBD" without a deadline is a gap, not a decision.
4. **arb/ folder: gate is APR-0010, not momentum.** No incorporation without explicit approval.
5. **Live capital decisions require two artifacts:** a superseding ADR and a signed approval (APR-0009).
