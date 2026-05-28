# ADR-0002 — Strategy Class: Forecast-Only Research (No Arbitrage)

**Status:** ACCEPTED (research phase); REVISIT AT G4 before paper trading promotion  
**Date:** 2026-05-21  
**Deciders:** DS, PO, RL  
**Supersedes:** None  
**Superseded by:** TBD — separate ADR required if strategy class changes at G4  

---

## Context

Two candidate strategy classes were identified from the previous iteration's artifacts:

1. **Forecast-only:** Build a calibrated probability model; trade when the model's estimate deviates from the market-implied probability by a sufficient edge margin. The model is the alpha source.

2. **Arbitrage (arb/):** Exploit structural pricing inefficiencies across venues or contract types without requiring a forecast model. A reference implementation exists in the `arb/` folder from the previous iteration.

The project must select a primary strategy class before the research environment is built (Phase 3). The choice determines what data is needed, what the backtesting framework must measure, and what the success criteria are.

---

## Decision Drivers

| Driver | Weight |
|--------|--------|
| Avoid contaminating current research with unvalidated prior work | CRITICAL |
| Build a system that can be validated with Brier score and calibration metrics | HIGH |
| Minimize complexity in Phase 0–4 (research only) | HIGH |
| Preserve option value for future strategy expansion | MEDIUM |
| Avoid prior iteration's data/process contamination | CRITICAL |

---

## Options Considered

### Option A — Forecast-Only (Calibrated Probability Model)
Build a model that takes features (starting with Player_Attribute_Matrix) and outputs a calibrated probability estimate. Place bets only when `edge = p_estimate - market_implied_prob - vig > threshold`. Success is measured by Brier score, log loss, and calibration curve relative to a null model (market_implied_prob baseline).

**Pros:** Clear, measurable success criteria. Independent of prior iteration's contaminated code. Fully compatible with Compass OS validation gates.

**Cons:** Requires a genuinely informative signal; no guarantee of positive edge.

### Option B — Arbitrage (from arb/ folder)
Use the arb/ folder from the previous iteration as the foundation. Exploit cross-venue pricing inefficiencies.

**Pros:** May not require a forecast model; edge may be more structural.

**Cons:** arb/ folder is from the contaminated prior iteration. Incorporating it without an ADR and formal validation would reproduce the prior failure. Arbitrage opportunities in prediction markets may be time-limited or already closed. Adds regulatory/compliance surface that must be assessed.

### Option C — Hybrid (Forecast + Arb)
Pursue both simultaneously.

**Cons:** Doubles complexity at the research phase. Conflicts with Compass OS principle of validating one approach before expanding.

---

## Decision

**Option A — Forecast-only calibrated probability model** is adopted as the strategy class for Phases 0–6.

**arb/ folder disposition:** Reference-only until a formal ADR (APR-0010) explicitly approves incorporation. Nothing from arb/ enters the canonical directory or influences any experiment without that ADR.

**Rationale:**
- Option A provides clear, auditable success criteria (Brier score vs null model)
- Option B would require validating the arb/ folder's methodology from scratch — no different from building a new strategy, but with additional contamination risk
- Option C violates the "one validated approach before expanding" principle
- This decision can be revisited at G4 once forecast-only validation evidence exists

---

## Consequences

**Positive:**
- Research environment design is unambiguous: C1→C2→C3 pipeline with calibration metrics
- Player_Attribute_Matrix is the natural starting feature set
- Null model (market_implied_prob) provides an immediate, defensible baseline
- arb/ folder isolation prevents contamination recurrence

**Negative / Trade-offs:**
- Deliberately forecloses arbitrage in the near term; may miss opportunities during Phase 3–6
- Success depends on Player_Attribute_Matrix containing predictive signal — not guaranteed

**Constraints introduced:**
- arb/ folder: reference-only; APR-0010 required before any incorporation
- Model class within forecast-only (logistic regression, XGBoost, etc.) deferred to ADR-0003 (backtesting methodology ADR)
- Retraining in production prohibited; model version frozen at paper→live promotion

---

## Revisit Criteria

This ADR should be revisited at G4 if:
- G4 evidence shows zero predictive signal in Player_Attribute_Matrix → strategy class may need to change
- Brier score cannot beat null model across ≥3 independent experiments → evidence base insufficient for promotion

If revised, a **superseding ADR is required** — this ADR does not auto-expire.

---

## Follow-Ups

| Action | Owner | Due |
|--------|-------|-----|
| Stage Player_Attribute_Matrix as DS-01 with snapshot discipline | RL | 2026-06-03 |
| Define RESEARCH_QUESTIONS.md scope (forecast-only framing) | RL | 2026-06-01 |
| Define HYPOTHESES.md (signal in Player_Attribute_Matrix) | RL | 2026-06-03 |
| ADR-0003: select backtesting methodology and model class | RL/DS | 2026-06-28 |

---

## Links

- Upstream: PROJECT_CHARTER.md, SCOPE_IN_OUT.md, VISION_OUTCOMES.md
- Downstream: RESEARCH_QUESTIONS.md, HYPOTHESES.md, DATA_REQUIREMENTS.md (DS-01)
- Approval: APR-0002 (PENDING — G1 gate)
- Related: APR-0010 (arb/ incorporation — PENDING indefinitely)
