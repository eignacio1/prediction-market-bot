# Vision and Outcomes — Prediction Market Trading Bot

**Purpose:** Define the north star vision and the concrete outcomes that constitute success. Upstream of all requirements.  
**Owner (role):** Product/Problem Owner (PO)  
**Last reviewed:** 2026-05-21  
**Next review:** 2026-06-21 or at G1 Spec Gate  
**Staleness triggers:** Strategy class changes; venue confirmed; capital targets revised; major signal source added or removed  
**Upstream links:** PROJECT_CHARTER.md  
**Downstream links:** REQUIREMENTS.md, SCOPE_IN_OUT.md, ROADMAP_MILESTONES.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 8/10 — Vision is stable; outcome thresholds will sharpen through validation  

---

## North Star Vision

A systematically governed prediction market bot that exploits calibrated information advantages — primarily player and event attribute data — to generate consistent positive expected value in prediction market venues. The bot operates transparently, is fully auditable, and promotes itself from research to live capital only when evidence-backed gates are cleared.

---

## Outcome Hierarchy

### Tier 1 — Research Integrity (Phases 0–4)
*If these fail, nothing downstream is trustworthy.*

| Outcome | Measure |
|---------|---------|
| Reproducible backtests | 100% of experiment results re-runnable from pinned snapshot IDs |
| No look-ahead bias | Confirmed in every experiment record via data snapshot discipline |
| Calibrated forecasts beating null model | Brier score improvement over market-implied probability as baseline |
| Zero shadow docs | All decision artifacts in directory within 72h of use |

### Tier 2 — Operational Safety (Phases 5–6)
*If these fail, real capital cannot be deployed.*

| Outcome | Measure |
|---------|---------|
| Kill switch operational | ≤60 seconds trigger-to-halt |
| Risk limits enforced | Hard position and daily loss limits are programmatic, not discretionary |
| Monitoring active before live deployment | All SLOs defined, alerts wired, observability confirmed |
| Rollback tested | At least one full rollback drill documented before G6 |

### Tier 3 — Live Capital Performance (Phase 8+)
*Monitored continuously after promotion.*

| Outcome | Measure |
|---------|---------|
| Positive expected value | Cumulative PnL positive over rolling 30-market window |
| Calibrated live forecasts | Brier score ≤ threshold defined at G4 |
| Drawdown within limits | Max drawdown never exceeds RISK_APPETITE_CONSTRAINTS.md hard limit |
| Governance sustained | Directory freshness ≥90%; quarterly retrieval drills pass at ≥8/10 |

---

## What Success Explicitly Does NOT Require

- Perfect forecasts (impossible in stochastic markets)
- Zero losses (a calibrated positive-EV bot will have losing bets)
- Speed superiority (this bot competes on calibration and signal quality, not latency)
- Multi-venue optimization in Phase 0–4 (single venue first)
