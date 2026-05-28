# Context Pack: G0 Baseline Handoff — 2026-05-22

**Purpose:** Baseline context pack capturing the complete project state at G0 completion. This is the authoritative restore point for any future context window that needs to reconstruct where the project stood at the end of the foundation phase.  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-05-22  
**Next review:** G1 exit (new Context Pack issued); FROZEN after G1 clears  
**Staleness triggers:** This document is FROZEN once G1 exit is confirmed. Do not update — create a new CP.  
**Upstream links:** MEMORY_BANK.md (index), PLAN.md (phase milestones)  
**Downstream links:** All artifacts (this documents their state at this date)  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 9/10 — Accurate snapshot of project state on 2026-05-22

---

## What This System Is

A prediction market trading bot built with institutional-grade governance to prevent the failure modes of the prior iteration. The bot:

1. Ingests player attribute data (DS-01) and market data (DS-02)
2. Generates calibrated probability estimates for binary prediction market outcomes
3. Computes edge against market-implied probability
4. Sizes positions using Fractional Kelly within hard risk limits
5. Executes orders on a regulated prediction market venue (TBD)
6. Monitors for model drift and kills automatically on limit breach

**The system does NOT trade yet.** It is in Phase 0 (Foundation). No live capital, no paper trading, no experiments.

---

## Why This System Exists (and Why the Prior One Failed)

The prior iteration was abandoned due to **context rot** — accumulated ambiguity, data contamination, and undocumented decisions that made the system unauditable and unreliable.

**Five specific failure modes from the prior iteration:**
1. Shadow decisions — choices made without documentation, later contradicted
2. Data contamination — no temporal integrity enforcement; look-ahead bias risk
3. Scope creep — arb/ strategy incorporated without validation
4. Missing audit trail — no way to reconstruct why any decision was made
5. Context erosion — each new context window rebuilt incorrectly from stale state

**The mitigation is the entire Compass OS governance framework** (ADR-0001). Every artifact in this directory is designed to be self-auditable and context-rot-resistant.

---

## Preserved Artifacts from Prior Iteration

| Artifact | Status | Treatment |
|---------|--------|-----------|
| Player_Attribute_Matrix_v4.docx | Research input only | NOT canonical; requires validation; blocks experiments until OQ-001 resolved |
| arb/ folder | REFERENCE ONLY | DO NOT INCORPORATE; future planning only; APR-0010 is the gate |

---

## Seven Anti-Erosion Invariants (Restore These First)

1. arb/ = reference only; no ADR = no incorporation
2. Player_Attribute_Matrix = research input only; validation required
3. ADRs immutable once accepted
4. No live capital until G6 formally cleared
5. No automated retraining in production
6. Zero hardcoded secrets (NFR-05)
7. Kill switch ≤60s halt; no bypass path

---

## Accepted Architecture Decisions

### ADR-0001: Adopt Compass OS
- **Status:** ACCEPTED — IMMUTABLE
- **Date:** 2026-05-21
- **Decision:** All governance, documentation, and decision-making follows the Compass OS framework
- **Consequence:** Every change follows CHANGE_CONTROL.md classification; every artifact has universal header

### ADR-0002: Forecast-Only Strategy Class
- **Status:** ACCEPTED — IMMUTABLE; REVISIT AT G4
- **Decision:** System uses calibrated probability forecasting; no arbitrage incorporation
- **Consequence:** arb/ folder is reference-only until APR-0010; HYP-003 (edge exceeds vig) requires venue selection before testing

---

## System Architecture (Summary)

**7 Components:**
- C1: Signal Ingestion (DS-01 snapshots; DS-02 live feed Phase 5+)
- C2: Feature Store (temporal_cutoff mandatory; outcome data never enters)
- C3: Forecasting Engine (calibrated p_estimate; confidence_interval; null model baseline)
- C4: Risk Engine (gated Phase 5+; hard limits; Kelly sizing; kill switch trigger)
- C5: Execution Engine (gated Phase 8+; paper simulation Phase 6+)
- C6: Audit Logger (always active Phase 3+; append-only JSON)
- C7: Monitoring / Kill Switch (always active Phase 5+; ≤60s halt NFR-03)

**4 Execution Modes:** Research Backtest | Research Live Inference | Paper Trading | Live Capital

**3 Environments:** ENV-01 (Research, no credentials) | ENV-02 (Paper, read-only market data) | ENV-03 (Live Capital, full API)

---

## Key Formulas

**Edge:** `edge = p_estimate - market_implied_prob - vig`

**Null model:** `null_model_prediction = mid_price = (bid + ask) / 2`

**Full Kelly:** `f* = (p_estimate - market_implied_prob) / (1 - market_implied_prob)`

**Live position:** `f_live = f* × fraction` (fraction TBD at G4)

**Bet criterion:** Place bet only if `edge > threshold` (threshold TBD at G4)

---

## Active Open Questions (Priority Order)

| ID | Question | Due | Blocks |
|----|----------|-----|--------|
| OQ-001 | DS-01 provenance | 2026-06-03 | All experiments |
| OQ-003 | Target market category | 2026-06-01 | Experiment design |
| OQ-006 | Venue selection | G3 | API, execution, compliance |
| OQ-007 | Technology stack | G2 | Implementation start |
| OQ-009 | Secrets vault | G5 | Live credentials |
| OQ-010 | C7 monitoring approach | G5 | Paper trading |

Full list in OPEN_QUESTIONS.md.

---

## Active Risks (Priority Order)

| ID | Risk | Level | Mitigation |
|----|------|-------|-----------|
| RID-001 | Context rot recurrence | P1 | Compass OS + this entire directory |
| RID-002 | No signal in DS-01 | P1 | HYP-001 falsification at G4 |
| RID-003 | Venue API change | P2 | Pinned SDK; monitor venue changelog |
| RID-004 | Overfitting | P2 | Hold-out test; walk-forward; 3+ experiments |
| RID-005 | Solo operator timeline | P3 | Conservative milestones |
| RID-006 | Kill switch not tested | P3 | TC-009/010 drill before G5 |

---

## Phase Progression Map

| Phase | Name | Entry Condition | Key Deliverable | Gate |
|-------|------|----------------|----------------|------|
| 0 | Foundation | None | Directory build | G0 |
| 1 | Spec + Environment | G0 | Data spec; dev env; dependency lock | G1 |
| 2 | Architecture + Execution Design | G1 | C1-C3 design; interfaces; threat model | G2 |
| 3 | Research and Model Development | G2 | ≥3 experiments; HYP-001 tested | G3/G4 |
| 4 | Infrastructure Build | G4 evidence | C1-C3 implemented; C7 implemented | G5 prep |
| 5 | Paper Trading Authorization | G4 | Kill switch tested; C4-C6 implemented | G5 |
| 6 | Paper Trading | G5 | Paper PnL; model card complete | G6 prep |
| 7 | Live Capital Authorization | G6 | All compliance gaps resolved | G6 |
| 8+ | Live Capital | G6 | Active trading; drift monitoring | Ongoing |

**Current:** Phase 0 completing.

---

## What "Done" Looks Like for This Context Pack

This Context Pack is the G0 deliverable. G0 is done when:

- [ ] All 11 directory modules built (COMPLETE as of 2026-05-22)
- [ ] ADR-0001 and ADR-0002 accepted (COMPLETE)
- [ ] MEMORY_BANK.md populated (COMPLETE)
- [ ] APPROVALS_REGISTER.md signed off for G0 (PENDING — operator action)
- [ ] CHANGELOG.md updated with G0 completion (PENDING)

After G0 sign-off, next action is Phase 1: resolve OQ-001, OQ-003, set up development environment, lock dependencies.
