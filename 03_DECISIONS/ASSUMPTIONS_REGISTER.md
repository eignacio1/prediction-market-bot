# Assumptions Register — Prediction Market Trading Bot

**Purpose:** Log all assumptions made during research and architecture design. Assumptions that turn out to be wrong can invalidate downstream work — tracking them enables targeted remediation.  
**Owner (role):** Research Lead (RL) + Architecture Owner (AO)  
**Last reviewed:** 2026-05-22  
**Next review:** G1 Spec Gate; then updated as each assumption is validated or falsified  
**Staleness triggers:** New experiment results; venue confirmed; G4 evidence review; any assumption proved false  
**Upstream links:** REQUIREMENTS.md, RESEARCH_QUESTIONS.md, ADR-0002  
**Downstream links:** HYPOTHESES.md, EXPERIMENT_LOG/, 07_TEST_VALIDATION_EVIDENCE/VALIDATION_PLAN.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 6/10 — Assumptions are initial; validation evidence collected from Phase 3 onward

---

## Assumption Classification

| Class | Meaning |
|-------|---------|
| A — Research | Assumption about data, signal, or model that determines research validity |
| B — Architecture | Assumption about system design that determines implementation correctness |
| C — Operational | Assumption about operational environment that determines live viability |
| D — Business | Assumption about market structure or venue that determines commercial viability |

---

## Assumption Register

### ASM-001 — Player_Attribute_Matrix Contains Predictive Signal

| Field | Detail |
|-------|--------|
| Class | A — Research |
| Assumption | The Player_Attribute_Matrix contains features that are predictive of prediction market outcomes at a level that beats the null model (market_implied_prob baseline) |
| Basis | Prior iteration identified this dataset as valuable; no validation yet in current iteration |
| Risk if false | Entire Phase 3 research produces no viable signal; strategy class may need revisiting (ADR-0002 revisit) |
| Validation method | Brier score vs null model across ≥3 independent experiments (G4 evidence requirement) |
| Status | UNVALIDATED |
| Owner | RL |
| Revisit at | G4 Evidence Gate |

### ASM-002 — Prediction Market Prices Are Reasonably Calibrated (Null Model Validity)

| Field | Detail |
|-------|--------|
| Class | A — Research |
| Assumption | Market-implied probability (mid-price) is a reasonable approximation of the event's true probability, sufficient to serve as a null model baseline |
| Basis | Efficient market hypothesis in liquid prediction markets; literature support (Brier scores of market prices vs outcomes) |
| Risk if false | Null model is not a meaningful baseline; edge calculation may be meaningless |
| Validation method | Compute Brier score of market_implied_prob vs outcomes on historical data before any model comparison |
| Status | UNVALIDATED (validates at Phase 3 with historical data) |
| Owner | RL |
| Revisit at | Phase 3 first results |

### ASM-003 — Sufficient Historical Event Volume for Backtesting

| Field | Detail |
|-------|--------|
| Class | A — Research |
| Assumption | Sufficient historical events exist in the target market category to produce statistically meaningful calibration metrics from backtesting |
| Basis | Prediction market venues have been operating for 3+ years; assumed sufficient event history |
| Risk if false | Backtest results are statistically underpowered; cannot make valid G4 decisions |
| Validation method | Count available historical events before Phase 3 experiments begin |
| Status | UNVALIDATED |
| Owner | RL |
| Revisit at | Phase 3 data ingestion |

### ASM-004 — Fractional Kelly Provides Adequate Drawdown Protection

| Field | Detail |
|-------|--------|
| Class | A — Research / B — Architecture |
| Assumption | Fractional Kelly position sizing (at some fraction TBD at G4) limits drawdown to acceptable levels even if model has mild negative edge |
| Basis | Kelly criterion literature; conservative fractions (0.25×–0.5×) widely used in practice |
| Risk if false | Even fractional Kelly fails to limit losses; additional hard limits required |
| Validation method | Paper trading simulation with historical data; drawdown analysis at multiple Kelly fractions |
| Status | UNVALIDATED (validates at Phase 6 paper trading) |
| Owner | RCO + RL |
| Revisit at | G4 (threshold selection), G6 (paper trading evidence) |

### ASM-005 — Venue API Provides Adequate Data for Feature Engineering

| Field | Detail |
|-------|--------|
| Class | D — Business |
| Assumption | The selected venue's API provides sufficient market data (prices, order book, volume, resolution outcomes) to support the feature engineering pipeline |
| Basis | Kalshi and Polymarket both provide documented public APIs; assumed to include required fields |
| Risk if false | Venue selection must change (ADR-0003 revisit) or feature set must be reduced |
| Validation method | API documentation review at ADR-0003; test API access at G5 (ACC-0002) |
| Status | UNVALIDATED (validates at ADR-0003) |
| Owner | AO |
| Revisit at | ADR-0003 |

### ASM-006 — Solo Operator Can Maintain Compass OS Cadences Without Peer Accountability

| Field | Detail |
|-------|--------|
| Class | C — Operational |
| Assumption | A single operator (Earl Ignacio) can maintain DIR, Context Pack, and cadence discipline without team accountability structures |
| Basis | Compass OS was designed for teams; adapted for solo use; M1 metric provides objective self-accountability |
| Risk if false | Context rot recurs; G0-G6 gates are not meaningful guardrails |
| Validation method | M1 freshness metric tracked weekly; retrieval drill at G4 |
| Status | MONITORING |
| Owner | DS |
| Revisit at | G2, G4 retrieval drill |

### ASM-007 — No Regulatory Barrier to Research-Phase Operation

| Field | Detail |
|-------|--------|
| Class | D — Business |
| Assumption | Research-phase backtesting with historical data and paper trading simulation requires no regulatory registration or compliance action |
| Basis | Research with historical data and simulation is standard practice; no money at risk until G6 |
| Risk if false | Compliance requirements affect timeline or scope |
| Validation method | POLICY_REQUIREMENTS.md review; operator compliance self-review before G5 (operator is sole compliance decision-maker) |
| Status | UNVALIDATED |
| Owner | RCO |
| Revisit at | G5 Operational Gate |

### ASM-008 — ERI (Emotional Relay Index) Contains Independent Predictive Signal

| Field | Detail |
|-------|--------|
| Class | A — Research |
| Assumption | Emotional Relay Index signals (previous-game performance streaks, carry-over psychological context) provide incremental Brier score improvement beyond rolling box-score features alone |
| Basis | Sports psychology literature; anecdotal evidence of performance regression/follow-through after extreme games; not yet validated quantitatively |
| Risk if false | ERI features add noise; FEATURE_VERSION 1.2.0 should drop them; reduces feature set to schedule context only |
| Validation method | Compare Brier score of model with ERI features vs without ERI features on same validation window; incremental improvement > 0.005 required |
| Status | UNVALIDATED — ERI v0 features implemented in FEATURE_VERSION 1.1.0; validates at Phase 4 experiment |
| Owner | RL |
| Revisit at | Phase 4 first ERI-enabled experiment |

### ASM-009 — Back-to-Back and Load Fatigue Negatively Impact Scoring Performance

| Field | Detail |
|-------|--------|
| Class | A — Research |
| Assumption | Players in back-to-back games (days_since_last_game == 1) and high schedule load (load_games_l7d ≥ 4) show measurably lower points output, detectable by the model as a directional signal |
| Basis | NBA analytics literature; rest-day studies (Charest et al. 2018; FiveThirtyEight NBA rest analysis); nba_api game log data sufficient to derive the feature |
| Risk if false | Schedule features are noise; remove from model and reduce feature set by 2 |
| Validation method | Feature importance analysis on EXP-002/003; compare model Brier score with/without schedule features |
| Status | UNVALIDATED — schedule features in FEATURE_VERSION 1.1.0; validates at Phase 4 |
| Owner | RL |
| Revisit at | Phase 4 feature importance analysis |

---

## Falsified Assumptions

*Populated as experiments invalidate assumptions.*

| ASM ID | Assumption | Date Falsified | Impact | Response |
|--------|-----------|----------------|--------|----------|
| — | — | — | — | — |

---

## Validated Assumptions

*Populated as experiments confirm assumptions.*

| ASM ID | Assumption | Date Validated | Evidence | Confidence Gain |
|--------|-----------|----------------|----------|-----------------|
| — | — | — | — | — |
