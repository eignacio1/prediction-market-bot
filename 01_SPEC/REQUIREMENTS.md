# Requirements — Prediction Market Trading Bot

**Purpose:** Define all functional and non-functional requirements in testable form. Every requirement links to an acceptance test and evidence location.  
**Owner (role):** Product/Problem Owner (PO)  
**Status:** **FROZEN — G1 Spec Gate 2026-05-22** — Changes require a new ADR or formal Change Class A/B record in CHANGE_CONTROL.md  
**Last reviewed:** 2026-05-22 (FROZEN at G1)  
**Next review:** On staleness trigger only; any change unfreezes and requires re-gate  
**Staleness triggers:** Strategy class change (ADR); venue API confirmed (ADR-0003); new signal source incorporated; model architecture change (ADR-0004); risk appetite revision (RCO review)  
**Upstream links:** VISION_OUTCOMES.md, SCOPE_IN_OUT.md, PROJECT_CHARTER.md  
**Downstream links:** ACCEPTANCE_CRITERIA.md, 07_TEST_VALIDATION_EVIDENCE/TEST_STRATEGY.md, 07_TEST_VALIDATION_EVIDENCE/VALIDATION_PLAN.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 9/10 — FROZEN at G1; venue-specific API requirements (order format, rate limits) will be captured in a separate interface specification at G3 without requiring requirements re-open  

---

## Functional Requirements

### FR-01 — Signal Ingestion
| Field | Value |
|-------|-------|
| Requirement ID | FR-01 |
| Statement | The system SHALL ingest structured player and event attribute data from defined input sources, validate against a schema, and make the data available to the forecasting pipeline with a traceable Snapshot ID. |
| Rationale | Signal quality is the primary driver of forecast edge; provenance tracking prevents data contamination recurrence. |
| Priority | P0 (blocking for all downstream requirements) |
| Owner | Research Lead (RL) / Architecture Owner (AO) |
| Acceptance test reference | 07_TEST_VALIDATION_EVIDENCE/TEST_CASES/TC-FR-01.md |
| Evidence pointer | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-01/ |
| Dependencies | DATA_REQUIREMENTS.md; DATA_SNAPSHOTS_INDEX.md |
| Staleness triggers | New data source added; schema version change |

### FR-02 — Forecast Generation
| Field | Value |
|-------|-------|
| Requirement ID | FR-02 |
| Statement | The system SHALL generate a probability estimate for each target market event, accompanied by a confidence interval, the Snapshot ID of data used, and the model version. |
| Rationale | Forecast must be traceable and auditable; confidence intervals are required for position sizing (Kelly criterion). |
| Priority | P0 |
| Owner | Model Owner / Validator (MO/V) |
| Acceptance test reference | 07_TEST_VALIDATION_EVIDENCE/TEST_CASES/TC-FR-02.md |
| Evidence pointer | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-02/ |
| Dependencies | FR-01 (signal ingestion); MODEL_CARD.md |
| Staleness triggers | Model architecture change; new signal incorporated |

### FR-03 — Calibration Evaluation
| Field | Value |
|-------|-------|
| Requirement ID | FR-03 |
| Statement | The system SHALL evaluate forecast calibration using Brier score and log loss against a null model baseline, with results written to a timestamped output file referencing the Snapshot ID. |
| Rationale | Calibration is the measurable definition of "good forecast"; null model comparison is the minimum viable evidence of signal value. |
| Priority | P0 |
| Owner | Research Lead (RL) / Evidence Owner (EO) |
| Acceptance test reference | 07_TEST_VALIDATION_EVIDENCE/TEST_CASES/TC-FR-03.md |
| Evidence pointer | 07_TEST_VALIDATION_EVIDENCE/BENCHMARKS/ |
| Dependencies | FR-02; DATA_SNAPSHOTS_INDEX.md |
| Staleness triggers | Evaluation metric set changed; null model definition changed |

### FR-04 — Decision Recording
| Field | Value |
|-------|-------|
| Requirement ID | FR-04 |
| Statement | The system SHALL record every forecast decision (event ID, timestamp, probability estimate, data snapshot ID, model version, edge calculation, rationale) in a structured, append-only log. |
| Rationale | Full auditability; prevents post-hoc rationalization; required for backtesting validation. |
| Priority | P0 |
| Owner | Architecture Owner (AO) |
| Acceptance test reference | 07_TEST_VALIDATION_EVIDENCE/TEST_CASES/TC-FR-04.md |
| Evidence pointer | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-04/ |
| Dependencies | FR-02 |
| Staleness triggers | Log schema change; new decision field required |

### FR-05 — Kill Switch (Research Phase)
| Field | Value |
|-------|-------|
| Requirement ID | FR-05 |
| Statement | The system SHALL implement a kill switch that halts all processing (data ingestion, forecast generation, any simulated or real order placement) within ≤60 seconds of manual trigger or automatic limit breach. |
| Rationale | Safety invariant; required before any data flows to or from external systems. |
| Priority | P0 |
| Owner | Operations Owner (OO) |
| Acceptance test reference | 07_TEST_VALIDATION_EVIDENCE/TEST_CASES/TC-FR-05.md |
| Evidence pointer | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-05/ |
| Dependencies | RUNBOOKS/RUNBOOK_kill-switch.md; RISK_APPETITE_CONSTRAINTS.md |
| Staleness triggers | System architecture change; new execution component added |

### FR-06 — Backtesting Framework
| Field | Value |
|-------|-------|
| Requirement ID | FR-06 |
| Statement | The system SHALL support historical simulation of the forecast pipeline using pinned data snapshots, with explicit train/test split enforcement, look-ahead bias detection, and results output including all metrics in FR-03. |
| Rationale | Reproducibility and overfitting mitigation are foundational; backtesting must be locked against data snooping. |
| Priority | P0 |
| Owner | Research Lead (RL) |
| Acceptance test reference | 07_TEST_VALIDATION_EVIDENCE/TEST_CASES/TC-FR-06.md |
| Evidence pointer | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-06/ |
| Dependencies | FR-01, FR-03, DATA_SNAPSHOTS_INDEX.md |
| Staleness triggers | Backtesting methodology change (requires ADR-0003) |

### FR-07 — Simulated Order Placement (Phase 6, gated)
| Field | Value |
|-------|-------|
| Requirement ID | FR-07 |
| Statement | The system SHALL support paper trading mode: recording hypothetical orders (event, direction, size, price, timestamp) against live market data without submitting to a venue, and tracking simulated PnL outcomes. |
| Rationale | Paper trading is the bridge between research validation and live capital; must be indistinguishable from live mode except for order submission. |
| Priority | P1 (Phase 6) |
| Owner | Architecture Owner (AO) |
| Acceptance test reference | 07_TEST_VALIDATION_EVIDENCE/TEST_CASES/TC-FR-07.md |
| Evidence pointer | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-07/ |
| Dependencies | ADR-0004 (paper trading promotion); FR-04; FR-05 |
| Staleness triggers | Venue confirmed; order format changed |

### FR-08 — Live Order Execution (Phase 8, gated)
| Field | Value |
|-------|-------|
| Requirement ID | FR-08 |
| Statement | The system SHALL support real order placement and cancellation on the confirmed prediction market venue, subject to all risk limit checks in FR-09, and with every order recorded per FR-04. |
| Rationale | Live execution is the end goal; must inherit all safety controls from earlier phases. |
| Priority | P1 (Phase 8) |
| Owner | Architecture Owner (AO) |
| Acceptance test reference | 07_TEST_VALIDATION_EVIDENCE/TEST_CASES/TC-FR-08.md |
| Evidence pointer | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-08/ |
| Dependencies | ADR-0005 (live capital promotion); G6 gate passage; FR-05, FR-09 |
| Staleness triggers | Venue API change; order type change; risk appetite revision |

### FR-09 — Risk Limit Enforcement
| Field | Value |
|-------|-------|
| Requirement ID | FR-09 |
| Statement | The system SHALL enforce all hard limits defined in RISK_APPETITE_CONSTRAINTS.md (max position size, max daily loss, max order rate) programmatically, triggering the kill switch automatically on breach. |
| Rationale | Risk limits must be enforced by the system, not by discretion; discretionary limits fail under pressure. |
| Priority | P0 (design Phase 2–3; enforce Phase 6+) |
| Owner | Risk/Control Owner (RCO) / Architecture Owner (AO) |
| Acceptance test reference | 07_TEST_VALIDATION_EVIDENCE/TEST_CASES/TC-FR-09.md |
| Evidence pointer | 07_TEST_VALIDATION_EVIDENCE/EVIDENCE/FR-09/ |
| Dependencies | RISK_APPETITE_CONSTRAINTS.md; FR-05 |
| Staleness triggers | Risk appetite revision (requires RCO review + CHANGELOG entry) |

---

## Non-Functional Requirements

*See NON_FUNCTIONAL_REQUIREMENTS.md for full detail. Summary here for cross-reference.*

| NFR ID | Category | Summary |
|--------|----------|---------|
| NFR-01 | Reproducibility | Every result re-runnable from pinned code + environment + Snapshot ID |
| NFR-02 | Auditability | All forecasts, orders, and decisions logged with full provenance |
| NFR-03 | Safety | Kill switch ≤60s; risk limits programmatic; rollback documented |
| NFR-04 | Data integrity | No look-ahead bias; train/test splits enforced; snapshot IDs immutable |
| NFR-05 | Secrets management | No credentials in plaintext or code; rotation policy defined |
| NFR-06 | Observability | All production processes emit structured logs; metrics available to monitoring |
| NFR-07 | Portability | Research pipeline runnable in dev environment before any external connectivity |
| NFR-08 | Governance cadence | No major changes in 4-week period without ADR or CHANGE_CONTROL.md entry; verified at each DIR |
