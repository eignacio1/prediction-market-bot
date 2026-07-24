# Project Charter — Prediction Market Trading Bot

**Purpose:** Define the project's intent, scope boundaries, success criteria, phase gates, and top risks. This is the authoritative statement of what we are building and why.  
**Owner (role):** Product/Problem Owner (PO) | Directory Steward (DS)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: fixed genuine drift (§4 Constraints "Venue: TBD" — ADR-0003 has been ACCEPTED since 2026-05-23, Kalshi primary/Polymarket US secondary); gate table, risks, and success-criteria sections verified current, no further drift found.  
**Next review:** 2026-08-23 (monthly) or at any phase gate passage  
**Staleness triggers:** Scope change; strategy class change; venue change; capital limit change; stakeholder change; gate passage  
**Upstream links:** None (root governance artifact)  
**Downstream links:** 01_SPEC/REQUIREMENTS.md, 01_SPEC/SCOPE_IN_OUT.md, 03_DECISIONS/DECISION_LOG/ADR-0001  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 8/10 — Venue-specific constraints and compliance requirements will sharpen this as they are confirmed  

---

## 1. Purpose and Outcomes

**Problem statement:** Prediction markets offer inefficiencies exploitable by systematic, calibrated forecasting — particularly in sports and event markets where participant attribute data is underutilized. Manual trading is too slow, inconsistent, and unscalable. A previous automated bot attempt failed due to context rot, data contamination, and lack of governance infrastructure, destroying trust in its outputs.

**Desired outcomes:**
1. A reproducible, auditable, context-rot-resistant prediction market bot that generates calibrated probability forecasts.
2. A systematic research pipeline that identifies, tests, and validates signal sources (beginning with player/market attribute data).
3. A governed promotion path from research-only to live capital, with hard risk controls and kill-switch capability at every stage.
4. A self-maintaining governance infrastructure that prevents the contamination and context erosion that destroyed the previous iteration.

---

## 2. Non-Goals (Explicit Exclusions)

- **NOT** a general-purpose financial trading system. Prediction markets only (scoped).
- **NOT** a high-frequency market maker. Latency is not a primary constraint in Phase 0–2.
- **NOT** incorporating the `arb/` reference folder into active development until a formal ADR approves it.
- **NOT** deploying real capital until G6 Release Gate is formally cleared with evidence artifacts and approvals.
- **NOT** building multi-venue execution in Phase 0–3. Single venue first; multi-venue is a future ADR.
- **NOT** using the Player_Attribute_Matrix_v4 as a canonical spec artifact immediately; it is staged as a research input and must earn canonical status through validation evidence.

---

## 3. Stakeholders

| Role | Responsibility |
|------|---------------|
| Product/Problem Owner (PO) | Intent, scope, requirements, acceptance criteria |
| Directory Steward (DS) | Directory health, link integrity, artifact lifecycle, health reports |
| Architecture Owner (AO) | System architecture, interfaces, NFRs, failure modes |
| Execution Lead (EL) | Plan, status, dependency tracking, delivery coordination |
| Evidence Owner (EO) | Test strategy, validation plan, evidence capture, sign-off readiness |
| Risk/Control Owner (RCO) | Control mapping, audit evidence spine, approvals register |
| Operations Owner (OO) | Runbooks, SLOs, observability, incident process |
| Research Lead (RL) | Research questions, experiment logs, research summaries |
| Model Owner / Validator (MO/V) | Model documentation, limitations, monitoring/drift plan, validation report |

*Note: In a solo build, all roles are held by the same individual. RACI assignments are maintained explicitly in STAKEHOLDERS_RACI.md to enable clean future delegation or handoff.*

---

## 4. Constraints

| Constraint | Detail |
|-----------|--------|
| Capital | $0 authorized in Phases 0–5. Phase 6 (paper trading): simulated capital only. Real capital requires G6 sign-off. |
| Venue | Decided (ADR-0003, ACCEPTED 2026-05-23): Kalshi primary (CFTC-DCM, active), Polymarket US secondary (KYC-gated, built not activated). |
| Data | Player/market attribute data (Player_Attribute_Matrix_v4.docx as initial research input). External data sources require Data Requirements sign-off. |
| Compute | Development environment only in Phases 0–3. Production compute requirements defined at G5. |
| Compliance | Any external venue connectivity, API credential use, or real capital triggers full instantiation of 09_SECURITY_PRIVACY_COMPLIANCE/. |
| Context integrity | All decisions, data sources, and code references must be traceable and pinned. Shadow docs are prohibited. |

---

## 5. Success Criteria (Measurable)

### Research Phase (Phases 0–4)
| Metric | Threshold |
|--------|-----------|
| Forecast calibration (Brier score) | Baseline established; improvement from null model demonstrated |
| Backtesting reproducibility | 100% of experiment results re-runnable from pinned snapshot IDs |
| Directory freshness | ≥90% of artifacts reviewed within SLA at each weekly DIR |
| Decision coverage | 0 major changes without a corresponding ADR |
| Context pack completeness | Every phase gate transition produces a Context Pack |

### Paper Trading Phase (Phase 6)
| Metric | Threshold |
|--------|-----------|
| Simulated PnL vs null baseline | Positive expected value demonstrated over ≥30 market events |
| Forecast accuracy | Brier score ≤ 0.20 (target; threshold to be refined at G4) |
| System uptime | ≥99% during scheduled market windows |
| Kill-switch response time | ≤60 seconds from trigger to full halt |

### Live Capital Phase (Phase 8+)
| Metric | Threshold |
|--------|-----------|
| Max single-event loss | Hard limit defined in RISK_APPETITE_CONSTRAINTS.md |
| Max daily drawdown | Hard limit defined in RISK_APPETITE_CONSTRAINTS.md |
| Monitoring alert response | ≤15 minutes for P1 alerts |
| Quarterly retrieval drill score | ≥8/10 questions answerable from directory alone |

---

## 6. Phase Gates

| Gate | Name | Key Exit Criteria |
|------|------|------------------|
| G0 | Intent | Charter frozen; RACI published; ADR-0001 accepted; Memory Bank initialized |
| G1 | Spec | Requirements testable; priorities explicit; assumptions logged; SCOPE_IN_OUT frozen |
| G2 | Architecture | Interfaces stable; failure modes identified; threat model drafted; architecture frozen |
| G3 | Execution | Plan credible; owners assigned; RID log baselined; delivery path frozen |
| G4 | Evidence | Validation plan populated; backtest evidence collected; model card instantiated; evidence sign-off path clear |
| G5 | Operational | Kill-switch runbook tested; SLOs defined; observability active; operable by someone other than builder |
| G6 | Release / Live Capital | Compliance spine complete; approvals register populated; final validation report signed; rollback tested |

---

## 7. Top 5 Risks

| # | Risk | Severity | Likelihood | Mitigation |
|---|------|----------|-----------|------------|
| R1 | Context rot recurrence — artifacts drift from code/data reality | HIGH | HIGH | Compass OS cadences, universal headers, staleness triggers, weekly DIR |
| R2 | Overfitting in backtest — inflated research-phase performance that collapses live | HIGH | HIGH | Pinned data snapshots, out-of-sample validation, multiple scoring metrics, sensitivity analysis |
| R3 | Shadow docs — decisions made outside the directory, losing traceability | HIGH | MED | Anti-shadow-doc rule: any doc used to make a decision must enter the directory within 72h |
| R4 | Premature promotion — real capital deployed before G6 evidence is sufficient | CRITICAL | MED | G6 gate is hard-blocked; real capital deployment requires approvals register sign-off |
| R5 | Data contamination — Player_Attribute_Matrix or other research inputs poisoning validation datasets | HIGH | MED | Strict snapshot ID discipline; train/test split enforced in experiment records |

---

## 8. Owner / Review Cadence / Staleness Triggers

- **Owner:** PO / DS (jointly)  
- **Review cadence:** Monthly minimum; immediately upon any phase gate passage or major scope change  
- **Staleness triggers:** Venue confirmed/changed; capital limits revised; new stakeholder role added; strategy class ADR issued; G0 or above gate passed  
