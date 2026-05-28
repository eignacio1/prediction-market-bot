# Scope In / Out — Prediction Market Trading Bot

**Purpose:** Explicit boundary definition. Ambiguities in scope cause contamination; this artifact eliminates them.  
**Owner (role):** Product/Problem Owner (PO)  
**Last reviewed:** 2026-05-21  
**Next review:** At G1 Spec Gate, or when any item moves between IN/OUT  
**Staleness triggers:** New venue added; new strategy class approved (ADR); arb/ folder incorporated (future ADR); Phase 6+ entry  
**Upstream links:** PROJECT_CHARTER.md, VISION_OUTCOMES.md  
**Downstream links:** REQUIREMENTS.md, 02_ARCHITECTURE_DESIGN/ARCHITECTURE_OVERVIEW.md, 03_DECISIONS/ADR-0002  
**Decision references:** ADR-0002  
**Confidence:** 9/10  

---

## IN SCOPE (Current: Phases 0–4)

| Item | Detail |
|------|--------|
| Prediction market forecasting | Generating calibrated probability estimates for binary/categorical prediction market events |
| Player/event attribute signal research | Using Player_Attribute_Matrix_v4 and similar structured attribute data as signal inputs (research phase) |
| Backtesting framework | Historical simulation of forecast performance using pinned data snapshots |
| Governance infrastructure | Full Compass OS directory, cadences, ADRs, context packs, MEMORY_BANK |
| Research-only execution | Forecast generation without any live order placement |
| Signal validation pipeline | Hypothesis → experiment → results → evidence chain for each signal source |
| Kill switch architecture | Design and implementation (even in research phase, for safety readiness) |

## IN SCOPE (Operational Readiness — Phase 5, pending G5)

| Item | Detail |
|------|--------|
| Live data ingestion (no orders) | Real-time market data consumption from confirmed venue; no order placement |
| Visual Dashboard (C8) | Operator-facing display of bot state: forecast performance, calibration, risk utilization, system health, alert feed. Required before paper trading. Evolves with each new strategic component. Read-only consumer of C6/C7. |
| Monitoring + Kill Switch (C7) | Full wiring and testing of C7; G5 gate requirement |

## IN SCOPE (Paper Trading — Phase 6, pending ADR-0004)

| Item | Detail |
|------|--------|
| Simulated order placement | Recording hypothetical bets with live prices; no real capital |
| Performance tracking vs backtest | Live vs. historical performance comparison |
| Visual Dashboard — paper trading panels | P&L panel, fill rates, position history added to C8 |

## IN SCOPE (Live Capital — Phase 8, pending G6 + ADR-0005)

| Item | Detail |
|------|--------|
| Real order execution | Placing and canceling real orders on confirmed prediction market venue |
| Capital management | Position sizing, risk limit enforcement, drawdown tracking |
| Live monitoring and alerting | Full observability stack, SLO enforcement, P1/P2 alert response |

---

## OUT OF SCOPE (Hard Exclusions)

| Item | Reason | Gate to Revisit |
|------|--------|----------------|
| arb/ folder incorporation | Holdover from previous iteration; reference-only until formal ADR | Future ADR (post-Phase 6) |
| Multi-venue execution | Complexity before single-venue is validated | Post-G6, new ADR required |
| High-frequency / latency-sensitive strategies | Not the competitive advantage; adds infrastructure complexity without Phase 0–4 payoff | Not planned |
| Equity, crypto, or traditional financial instruments | Outside prediction market scope | Out of scope entirely |
| Automated social media signal ingestion | Unstructured; requires separate data pipeline with additional compliance | Post-Phase 4, new ADR |
| Fully automated capital deployment without human review | Kill switch and human-in-the-loop required at G6 minimum | Never fully removed in Phase 8 |
| Model training on live capital data without evidence gate | Circular validation risk | Requires new validation cycle per model change |

---

## Boundary Clarifications

| Ambiguity | Resolution |
|-----------|-----------|
| Is the Player_Attribute_Matrix canonical spec or research input? | Research input only. It must earn canonical status via validation evidence. |
| Does "research-only" mean no code that can execute orders? | Yes — execution module is designed but gated behind a configuration flag; no live credentials in Phase 0–5 |
| Can signals from arb/ inform hypotheses (without incorporating the folder)? | No. arb/ is reference-only; any hypothesis derived from it must be independently formulated in HYPOTHESES.md with no direct lineage reference until an ADR approves incorporation. |
