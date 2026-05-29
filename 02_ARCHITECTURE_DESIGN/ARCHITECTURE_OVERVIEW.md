# Architecture Overview — Prediction Market Trading Bot

**Purpose:** Define the system's component architecture, their responsibilities, and how they interact. The authoritative map of what was built and why.  
**Owner (role):** Architecture Owner (AO)  
**Status:** **CANONICAL — G2 Architecture Gate 2026-05-22** — Changes require ADR or formal Change Class A/B record  
**Last reviewed:** 2026-05-28 (C8 Visual Dashboard registered; SCOPE_IN_OUT.md + INTERFACES_CONTRACTS.md updated; T-046/047 context)  
**Next review:** On staleness trigger only  
**Staleness triggers:** New component added; component removed; interface contract changed (ADR required); venue confirmed (affects execution layer); strategy class change  
**Upstream links:** 01_SPEC/REQUIREMENTS.md, 01_SPEC/NON_FUNCTIONAL_REQUIREMENTS.md, 01_SPEC/SCOPE_IN_OUT.md  
**Downstream links:** DATA_FLOWS_LINEAGE.md, INTERFACES_CONTRACTS.md, EXECUTION_ARCHITECTURE.md, RESILIENCE_FAILURE_MODES.md, 06_CODE_EXECUTION_REPRODUCIBILITY/RUN_INSTRUCTIONS.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 9/10 — Architecture canonical at G2; execution layer details pending venue confirmation (ADR-0003)  

---

## System Architecture Summary

The bot is a **pipeline-based forecasting and execution system** composed of six primary components and three cross-cutting services. In Phase 0–4 (research), only components C1–C3 and C6 are active. Components C4 and C5 are designed but gated behind paper trading (ADR-0004) and live capital (ADR-0005) promotions respectively. C7 and C8 activate at Phase 5.

```
┌─────────────────────────────────────────────────────────────────┐
│                    PREDICTION MARKET BOT                         │
│                                                                  │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐ │
│  │  C1      │   │  C2      │   │  C3      │   │  C4 [GATED] │ │
│  │ Signal   │──▶│ Feature  │──▶│Forecasting│──▶│  Risk       │ │
│  │ Ingestion│   │  Store   │   │  Engine  │   │  Engine     │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────┬──────┘ │
│                                                        │        │
│                                              ┌─────────▼──────┐ │
│                                              │  C5 [GATED]    │ │
│                                              │  Execution     │ │
│                                              │  Engine        │ │
│                                              └─────────┬──────┘ │
│                                                        │        │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  C6 — Audit Logger (cross-cutting; always active)        │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  C7 — Monitoring + Kill Switch (cross-cutting; Phase 5+) │   │
│  └─────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  C8 — Visual Dashboard (cross-cutting; Phase 5+)         │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Definitions

### C1 — Signal Ingestion
**Responsibility:** Ingest, validate, and version-stamp all input data. Assign Snapshot IDs and register in DATA_SNAPSHOTS_INDEX.md.

| Attribute | Detail |
|-----------|--------|
| Active from | Phase 3 (research; historical data) |
| Inputs | Player_Attribute_Matrix (DS-01); Market data feed (DS-02, Phase 6+); Outcome/resolution data (DS-03) |
| Outputs | Validated, schema-conformant data records with Snapshot ID |
| Key constraint | Must enforce schema contracts per DATA_REQUIREMENTS.md; must reject invalid records with structured error log |
| Phase gate | Historical ingestion: Phase 3 | Live ingestion: G5 Ops Gate (after ACC-0002 approved) |

### C2 — Feature Store
**Responsibility:** Transform raw signals into model-ready features. Record all transformations with traceability to source fields.

| Attribute | Detail |
|-----------|--------|
| Active from | Phase 3 |
| Inputs | C1 validated records (with Snapshot ID) |
| Outputs | Feature vectors keyed by (event_id, snapshot_id, feature_version) |
| Key constraint | All transformations documented in DATA_FLOWS_LINEAGE.md; no future data accessible in any feature |
| Interface | See INTERFACES_CONTRACTS.md: IF-C1-C2 |

### C3 — Forecasting Engine
**Responsibility:** Generate calibrated probability estimates for target market outcomes.

| Attribute | Detail |
|-----------|--------|
| Active from | Phase 3 (backtest); Phase 6 (live inference) |
| Inputs | C2 feature vectors; model artifacts (pinned version) |
| Outputs | Forecast record: {event_id, p_estimate, confidence_interval, snapshot_id, model_version, timestamp} |
| Key constraint | Model version must be immutable once deployed to paper/live; retraining requires ADR + new model version |
| Metrics | Brier score, log loss vs null model (market-implied probability) |
| Interface | See INTERFACES_CONTRACTS.md: IF-C2-C3 |

### C4 — Risk Engine *(GATED — Phase 6+ only)*
**Responsibility:** Enforce all hard limits from RISK_APPETITE_CONSTRAINTS.md. Calculate Kelly position size. Approve or reject orders before they reach C5.

| Attribute | Detail |
|-----------|--------|
| Active from | Phase 6 (simulated risk checks); Phase 8 (real enforcement) |
| Inputs | C3 forecast (p_estimate, confidence_interval); current portfolio state; RISK_APPETITE_CONSTRAINTS.md limits |
| Outputs | Order approval or rejection with reason; position size (fractional Kelly); kill-switch trigger on limit breach |
| Key constraint | **All limits are programmatic — no bypass path without ADR + RCO approval.** Kill switch auto-triggers on breach. FR-09. |
| Interface | See INTERFACES_CONTRACTS.md: IF-C3-C4, IF-C4-C5 |

### C5 — Execution Engine *(GATED — Phase 6+ only)*
**Responsibility:** Translate C4-approved orders into simulated (paper) or real venue orders. Manage order lifecycle.

| Attribute | Detail |
|-----------|--------|
| Active from | Phase 6 (simulated); Phase 8 (live) — requires ADR-0004/0005 |
| Inputs | C4 order approval + position size; venue API (Phase 8) |
| Outputs | Order record logged to C6; venue order (Phase 8 only) |
| Key constraint | **Cannot submit real orders without G6 sign-off (ACC-0002 + APR-0009).** Must receive C4 approval before every order. `venue_id` must be a parameter — no hardcoding (ADR-0003). FR-07, FR-08. |
| Interface | See INTERFACES_CONTRACTS.md: IF-C4-C5, IF-C5-VENUE |

### C6 — Audit Logger *(Cross-cutting; always active)*
**Responsibility:** Write all system events (forecasts, orders, risk decisions, kill-switch events, errors) to an append-only structured log.

| Attribute | Detail |
|-----------|--------|
| Active from | Phase 3 (all modes) |
| Inputs | Events from C1–C5 + C7 |
| Outputs | Append-only structured log files (format: JSON Lines) with required fields per NFR-02 |
| Key constraint | Log files are immutable after write. Read access for audit; no modification path. |

### C7 — Monitoring + Kill Switch *(Cross-cutting; Phase 5+)*
**Responsibility:** Monitor system health and risk metrics in real time; trigger kill switch on breach; emit structured metrics consumed by C8.

| Attribute | Detail |
|-----------|--------|
| Active from | Phase 5 (wired and tested at G5) |
| Inputs | Metrics from C1–C5; SLO thresholds from SLA_SLO_SLI.md; risk limits from RISK_APPETITE_CONSTRAINTS.md |
| Outputs | Alerts (P1/P2/P3); kill-switch signal; structured metric events (consumed by C8 via IF-C7-C8) |
| Key constraint | Kill switch must halt all active components within ≤60 seconds (NFR-03) |
| Runbook | 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_kill-switch.md |

### C8 — Visual Dashboard *(Cross-cutting; Phase 5+)*
**Responsibility:** Provide a human-readable, continuously updated view of bot progress and health. The mechanical mechanism for observing the bot's state without CLI log parsing. Grows with each new strategic component — as C1–C7 emit events and metrics, C8 surfaces them visually.

| Attribute | Detail |
|-----------|--------|
| Active from | Phase 5 (introduced alongside C7; required before paper trading) |
| Inputs | C6 audit log stream (IF-C6-C8); C7 metric events (IF-C7-C8); experiment results from 05_RESEARCH_EXPERIMENTS/ |
| Outputs | Live status panels: forecast performance, calibration trend, risk utilization, P&L (Phase 6+), system health, alert feed |
| Key constraint | Read-only consumer — C8 MUST NOT write to any component's state. No execution path through C8. |
| Evolution policy | Dashboard panels are extended at each phase: Phase 5 (health + forecasts), Phase 6 (paper P&L), Phase 8 (live capital metrics). Each extension triggers a CHANGELOG entry. |
| Interface | IF-C6-C8, IF-C7-C8 (see INTERFACES_CONTRACTS.md) |

---

## Deployment Modes

| Mode | Components Active | Capital | Gate Required |
|------|------------------|---------|--------------|
| Research (backtest) | C1, C2, C3, C6 | None | Phase 3 |
| Research (live inference, no orders) | C1, C2, C3, C6, C7, C8 | None | Phase 5 |
| Paper trading | C1, C2, C3, C4 (sim), C5 (sim), C6, C7, C8 | Simulated | ADR-0004 |
| Live capital | All (C1–C8) | Real | ADR-0005 + G6 |

---

---

## Phase 6 Idle Build — New Components (2026-05-29)

The following components were added during the Phase 6 idle period (waiting for paper bet accumulation). All are buildable on current cron infrastructure; T4/T5 are Phase 8+ stubs only.

| Component | File | Purpose | Phase |
|-----------|------|---------|-------|
| ExecutionBand framework | `execution_bands.py` | T1–T5 time-horizon bands; Kelly/SLA/compute per band | Phase 7 |
| VenueAdapter Protocol | `c5_execution/venue_adapter.py` | Abstract interface for all venue integrations | Phase 7 |
| KalshiVenueAdapter | `c5_execution/venue_adapter.py` | Wraps KalshiMarketClient; conforms to VenueAdapter | Phase 7 |
| PolymarketVenueAdapter | `c5_execution/venue_adapter.py` | Stub — T-077; slots in when API key provisioned | Phase 7 |
| DFSPickemVenueAdapter | `c5_execution/venue_adapter.py` | Stub — new ADR required (PrizePicks/Underdog/Sleeper) | Phase 7+ |
| VenueRouter | `c5_execution/venue_router.py` | Best-execution routing across venues; transparent to C3/C4 | Phase 7 |
| PIPE-05 (T2) | `run_t2_sameday.py` | Same-day injury overlay skeleton (DS-04 pending T-075) | Phase 7 |
| PIPE-06 (T3) | `run_t3_pretip.py` | Pre-tip momentum scan; reads T1 output + live prices | Phase 7 |

**Interface changes:** `PlayerMarket.venue` field added (default `"kalshi"` — backward-compatible). New contracts IF-VENUE-ADAPTER and IF-ROUTER in INTERFACES_CONTRACTS.md.

**Design docs:** EXECUTION_BANDS.md (T1–T5 canonical spec); VENUE_REGISTRY.md (V-001–V-005 CA-eligible venues).

---

## Technology Stack (Confirmed at G2)

*Core language and logging confirmed at G2. Storage, secrets vault, and monitoring selections deferred to G3/G5 respectively.*

| Layer | Requirement | Selection |
|-------|------------|-----------|
| Language | Reproducible, well-typed, 3.11+ | **Python 3.11** — pyproject.toml pinned; strict typing via mypy |
| Package management | Pinned; reproducible | pip + requirements-base.txt / requirements-dev.txt (DEPENDENCY_LOCKS/) |
| Code quality | Formatting + linting + security | black 24.4.2; flake8 7.0.0; bandit 1.7.8; pre-commit hooks |
| Data storage | Snapshot-capable; queryable | TBD at G3 (parquet + local FS likely for research; database for Phase 6+) |
| Logging | Structured (JSON Lines); append-only | **JSON Lines** — confirmed (NFR-02, NFR-06); `jsonlines` 4.0.0 |
| Secrets management | Vault-based; zero hardcoded | TBD at G5 (env-var + .env for dev; vault for Phase 6+; see SECRETS_HANDLING.md; NFR-05) |
| Monitoring | Metric emission; alerting | TBD at G5 (C7 wired at Phase 5; see OBSERVABILITY.md) |
