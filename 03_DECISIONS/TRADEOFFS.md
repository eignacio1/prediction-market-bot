# Trade-offs Log — Prediction Market Trading Bot

**Purpose:** Document explicit trade-offs made during design. Recording what was sacrificed (and why) prevents future revisionism and clarifies the design space.  
**Owner (role):** Architecture Owner (AO)  
**Last reviewed:** 2026-05-22  
**Next review:** G2 Architecture Gate; add entries whenever a non-obvious design choice is made  
**Staleness triggers:** New component designed; major architecture change; post-incident retrospective  
**Upstream links:** ADR-0001, ADR-0002, ARCHITECTURE_OVERVIEW.md  
**Downstream links:** REJECTED_OPTIONS.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 7/10 — Current trade-offs documented; implementation trade-offs emerge in Phase 3

---

## TR-001 — Gate Overhead vs Speed to Research

| Attribute | Detail |
|-----------|--------|
| Decision | Compass OS gates (G0–G6) are mandatory; no shortcuts |
| What we sacrifice | Time: G0 alone takes ~1 week of directory work before any research begins |
| What we gain | Prevention of the prior iteration's failure mode (context rot + unvalidated promotion) |
| Why this balance | The previous iteration had zero gates and reached live capital prematurely. The cost of building gates is less than the cost of another failed iteration. |
| Conditions for revisit | If G0–G2 overhead exceeds 4 weeks without producing a meaningful governance artifact |

## TR-002 — Forecast-Only vs Arbitrage (Strategy Class)

| Attribute | Detail |
|-----------|--------|
| Decision | Forecast-only strategy in Phase 0–6; arb/ folder excluded |
| What we sacrifice | Potential arbitrage edge that may exist in the arb/ folder |
| What we gain | Clean slate: no contamination from prior iteration; clear success criteria; interpretable model |
| Why this balance | Arbitrage requires validating the prior codebase from scratch, which carries equal effort to building new but adds contamination risk. A proven forecast model is more transferable. |
| Conditions for revisit | G4 evidence shows zero signal in Player_Attribute_Matrix → strategy class must change; APR-0010 clears the arb/ folder formally |

## TR-003 — Immutable ADRs vs Flexibility

| Attribute | Detail |
|-----------|--------|
| Decision | ADRs are immutable once accepted; changes require a superseding ADR |
| What we sacrifice | Flexibility to quietly change direction without documentation |
| What we gain | Audit trail for every major decision; accountability for direction changes |
| Why this balance | The prior iteration's failure included undocumented direction changes that destroyed coherence across sessions. Immutability enforces documented accountability. |
| Conditions for revisit | Never — this is a hard governance invariant |

## TR-004 — Local Execution vs Cloud (Phases 0–5)

| Attribute | Detail |
|-----------|--------|
| Decision | All research runs locally; no cloud dependency until G5 |
| What we sacrifice | Compute scalability; potential parallelization of backtests |
| What we gain | Zero external dependencies; simpler secrets handling; faster iteration in early phases |
| Why this balance | Research-phase data volume does not require cloud compute. Adding cloud dependency before the research approach is validated adds operational complexity with no benefit. |
| Conditions for revisit | Data volume exceeds local compute capacity; cloud is required for Phase 5+ model training at scale |

## TR-005 — Frozen Model in Production vs Continuous Retraining

| Attribute | Detail |
|-----------|--------|
| Decision | Model version is frozen at paper→live promotion; no automated retraining in production |
| What we sacrifice | Potential adaptation to market regime changes |
| What we gain | Auditability: we always know exactly what model is running; drift is detectable against a fixed baseline |
| Why this balance | Automated retraining in production is a common source of silent model changes that invalidate risk assumptions. Drift monitoring (C7) provides early warning; retraining requires a new ADR and model version. |
| Conditions for revisit | Post-G6 governance ADR may introduce a controlled retraining framework |

## TR-006 — Conservative Risk Limits vs Capital Efficiency

| Attribute | Detail |
|-----------|--------|
| Decision | Risk limits are hard limits with no override path; fractional Kelly at a conservative fraction TBD at G4 |
| What we sacrifice | Maximum capital deployment; some positive EV trades may be passed due to limit constraints |
| What we gain | Protection against model failure; drawdown bounded even if model has mild negative edge |
| Why this balance | At initial live capital deployment, model validation is limited. Conservative limits reduce the cost of being wrong. Limits can be relaxed in future phases with evidence. |
| Conditions for revisit | G6 evidence review; after ≥N live events with observed drawdown well within limits |
