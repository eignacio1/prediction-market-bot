# Glossary — Prediction Market Trading Bot

**Purpose:** Define project-specific terminology, prediction market mechanics terms, and governance vocabulary. Prevents semantic drift across artifacts.  
**Owner (role):** Directory Steward (DS) / Research Lead (RL)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: fixed genuine drift (venue-selection row said "not yet selected," but ADR-0003 was ACCEPTED 2026-05-23, Kalshi primary/Polymarket US secondary); all other terms verified current, no further drift found.  
**Next review:** 2026-08-23  
**Staleness triggers:** New strategy class adopted; venue confirmed (venue may introduce its own terminology); new signal source added; term used inconsistently across two or more artifacts  
**Upstream links:** PROJECT_CHARTER.md  
**Downstream links:** All artifacts that use these terms  
**Decision references:** ADR-0001, ADR-0002, ADR-0003  
**Confidence:** 8/10 — Venue confirmed (ADR-0003); remaining gap is venue-specific mechanics terms not yet added  

---


## Operating Vocabulary (added 2026-10-09 — strategic window forest pass)

| Term | Project-Specific Meaning | Notes | Owner | Last Reviewed |
|------|--------------------------|-------|-------|---------------|
| Wave | One round of work: three blocks written by the strategic window into `04_EXECUTION/ACTIVE_QUEUE.md`, run in parallel by terminals, then verified against GitHub and closed | Numbered (Wave 61, 62 ...); outcomes kept in the queue's Sequencing track | Strategic window | 2026-10-09 |
| Block | One paste-in prompt for one terminal session; MEDIUM size = two parts, ~60 min target, 90 min hard ceiling, each part pushed before the next | Ends with an END OF BLOCK line so a truncated paste is caught | Strategic window | 2026-10-09 |
| Strategic window | The directing Claude session: derives state from GitHub, writes waves, verifies results, routes decisions to the operator; never executes blocks itself | Its operating doc is `04_EXECUTION/STRATEGIC_WINDOW_CARRY_FORWARD.md`; hands off via `/strategic-handoff` | Operator | 2026-10-09 |
| RUNNING SITREP | The forest view at the top of ACTIVE_QUEUE.md: bottom line, pillar scoreboard, calendar, operator's open calls | Updated at every wave close; the first place to look for where the project is | Strategic window | 2026-10-09 |
| Pillars (BREADTH / DEPTH / EXECUTION / PROOF) | The operator's north star, canonical in CLAUDE.md § "What winning looks like". Every block and session names the pillar it moved; PLUMBING is necessary but not a pillar | Two consecutive waves with no pillar moved = drift, flagged to the operator | Operator | 2026-10-09 |
| Distance to optimum | The gap between the project and the bot at optimum, kept as numbers per pillar (measures B1–B4, D1–D3, E1–E3, P1–P3, defined in CLAUDE.md) | Values recomputed at every wave close at the top of the RUNNING SITREP; every task names the measure it is for (Hard Rule 12) | Operator | 2026-10-09 |
| Cell | One (MarketType, ExecutionBand) pair in `MARKET_TYPE_REGISTRY`, with its own CellStatus | Status values: ACTIVE, SHADOW, BLOCKED, DARK, NOT_IMPLEMENTED, RULED_OUT | Execution Lead | 2026-10-09 |
| SHADOW | Cell status: evaluate and log forecasts under a pre-registration; no order, position, stake or sizing | Evidence for calibration, never for execution | Execution Lead | 2026-10-09 |
| Shadow arm | The jobs that produce one sport's shadow forecasts (e.g. the NFL arm = 12 cells under EXP-037) | A silent arm (games scheduled, zero rows) is flagged by the SILENT ARMS block of the governance scan | Execution Lead | 2026-10-09 |
| Pre-registration | A committed document fixing a cell's comparisons, judged n, seed and verdict rule before its first row | Changes only by a dated addendum before any judged data, with the operator's line; never after results | Research Lead | 2026-10-09 |
| Judged n / first look | The pre-registered sample size at which a cell is first scored (e.g. 60 games per NFL cell); the first look is that scoring | Below judged n a cell is sealed: no score may be read | Research Lead | 2026-10-09 |
| Calibration engine | The daily job (13:49 UTC) that scores every cell under its own pre-registration, sealed below judged n, and writes frozen release manifests | Its output is the Calibration section of the Visual Dashboard | Research Lead | 2026-10-09 |
| Fill / CONFIRMED_FILLED | A demo-venue order that actually executed, per the venue's own fill history; "submitted" is not "filled" | Since 2026-10-08 (GG-527) T4M-PROJ's G6 and execution evidence count CONFIRMED_FILLED rows only | Execution Lead | 2026-10-09 |
| Exploratory track | `12_EXPLORATORY/`: research on archives and past seasons that builds challengers for pre-registered cells; never reads sealed results; never a verdict | Graduates only through a new operator-accepted pre-registration | Research Lead | 2026-10-09 |
| Visual Dashboard / Live Terminal | Visual Dashboard (`/project`) = operational review of the whole bot; Live Terminal (`/`) = what the bot is placing and evaluating, live | Opened via `Open Dashboard.command` (SSH tunnel to localhost:8050) | Operator | 2026-10-09 |
| Authorization (blockquote) | An operator decision recorded as a `> **AUTHORIZATION - ...**` line in ACTIVE_QUEUE.md "Needs your decision", with what it covers and does not | A table row describing a decision is not an authorization | Operator | 2026-10-09 |

## Prediction Market Mechanics

| Term | Project-Specific Meaning | Notes | Owner | Last Reviewed |
|------|--------------------------|-------|-------|---------------|
| Prediction market | A market where participants trade on the outcome of future events; prices represent implied probabilities | Venue selection is decided (ADR-0003, ACCEPTED 2026-05-23): Kalshi primary (CFTC-DCM), Polymarket US secondary (KYC-gated). PredictIt not selected. | RL | 2026-07-23 |
| AMM (Automated Market Maker) | A liquidity mechanism using a mathematical pricing rule (e.g., LMSR) rather than an order book | Polymarket uses AMM; Kalshi uses CLOB | RL | 2026-05-21 |
| CLOB (Central Limit Order Book) | A traditional order book where bids and asks are matched by price-time priority | Kalshi primarily uses CLOB | RL | 2026-05-21 |
| LMSR (Logarithmic Market Scoring Rule) | A cost-function-based AMM that guarantees liquidity; prices shares in a binary outcome market | Common in academic prediction markets | RL | 2026-05-21 |
| Implied probability | The probability of an outcome as implied by the current market price (e.g., a contract trading at $0.65 implies 65% probability) | Must account for bid-ask spread and fees when computing true implied prob | RL | 2026-05-21 |
| Vig / take rate | The platform's fee or spread embedded in prices; reduces expected value for all participants | Critical input to edge calculation | RL | 2026-05-21 |
| Settlement | The process by which a market resolves and winning contracts pay out | Settlement rules vary by venue and event type | RL | 2026-05-21 |
| Position | A holding in a prediction market contract (YES or NO shares, or equivalent) | Risk limits are defined at the position level in RISK_APPETITE_CONSTRAINTS.md | RCO | 2026-05-21 |
| Edge | The bot's expected profit per dollar wagered, net of vig: Edge = P(win) - implied_probability - vig | Positive edge is a necessary but not sufficient condition for a good bet | RL | 2026-05-21 |
| Kelly criterion | A formula for optimal position sizing given edge and odds: f* = (bp - q) / b | Used in position sizing module; full Kelly is aggressive — fractional Kelly preferred | RL | 2026-05-21 |
| Paper trading | Simulated trading using live market data but no real capital; records hypothetical orders and outcomes | Phase 6 of the iteration plan | EL | 2026-05-21 |

---

## Forecasting and Model Terms

| Term | Project-Specific Meaning | Notes | Owner | Last Reviewed |
|------|--------------------------|-------|-------|---------------|
| Brier score | Mean squared error of probability forecasts: BS = (1/N) Σ(f_i - o_i)² where f is forecast probability, o is outcome (0 or 1); lower is better | Primary calibration metric in Phase 3–4 | MO/V | 2026-05-21 |
| Log loss | Negative log likelihood of forecasts; penalizes overconfident wrong predictions more severely than Brier score | Used as secondary metric; complement to Brier | MO/V | 2026-05-21 |
| Calibration | The alignment between forecast probabilities and empirical outcome frequencies; a well-calibrated model predicting 70% probability should be right ~70% of the time | Assessed via calibration curves (reliability diagrams) | MO/V | 2026-05-21 |
| Null model | A baseline forecast that uses no signals — e.g., implied market probability, or uniform 50/50 | All forecasting experiments must beat the null model to show positive signal | RL | 2026-05-21 |
| Signal | A measurable input that has predictive power for market outcomes; e.g., player performance metrics, market liquidity changes | Signals are documented in HYPOTHESES.md and validated in EXPERIMENT_LOG/ | RL | 2026-05-21 |
| Feature | A processed or derived representation of a signal used as model input | Signal → Feature transformation must be documented in DATA_FLOWS_LINEAGE.md | RL | 2026-05-21 |
| Overfitting | When a model learns noise in the training data and performs worse on new data; a primary research-phase risk | Mitigated by pinned train/test splits and out-of-sample validation | MO/V | 2026-05-21 |
| Look-ahead bias | Using information that would not have been available at forecast time in backtesting; a silent contaminator | Strictly prohibited; enforced via data snapshot discipline | RL | 2026-05-21 |
| Data snapshot | A frozen, versioned extract of data used in an experiment; identified by a Snapshot ID | Defined in 06_CODE_EXECUTION_REPRODUCIBILITY/DATA_SNAPSHOTS_INDEX.md | EO | 2026-05-21 |

---

## Governance and Directory Terms

| Term | Project-Specific Meaning | Notes | Owner | Last Reviewed |
|------|--------------------------|-------|-------|---------------|
| ADR (Architecture Decision Record) | A formal, immutable record of a major decision; once accepted, changes require a new superseding ADR | Template at 00_ADMIN/TEMPLATES/TEMPLATE_ADR.md | DS | 2026-05-21 |
| Context rot | Gradual degradation of a project's shared understanding as artifacts drift from current reality; primary failure mode of the previous bot iteration | Prevented by Compass OS cadences, staleness triggers, and universal headers | DS | 2026-05-21 |
| Canonical | The single authoritative version of an artifact; all references must point to it | Status tracked in each artifact's header | DS | 2026-05-21 |
| Frozen | A snapshot of an artifact taken at a phase gate; immutable for audit purposes; a new version can supersede it | Artifacts must be frozen before passing a gate | DS | 2026-05-21 |
| Context Pack (CP) | A short structured handoff artifact produced at every major transition (phase gate, ownership change, incident) | Template at 00_ADMIN/TEMPLATES/TEMPLATE_CONTEXT_PACK.md | DS | 2026-05-21 |
| DIR (Directory Integrity Review) | Weekly session to check freshness SLA breaches, orphan artifacts, broken links, and ADR coverage | Run by Directory Steward | DS | 2026-05-21 |
| C4 Council (Cross-Cutting Concerns Council) | Weekly review of changes that impact security, privacy, reliability, performance, model risk, or compliance | Run by AO or RCO | AO/RCO | 2026-05-21 |
| RID Log | Risk / Issue / Dependency log; tracks active threats to delivery | Updated daily; at 04_EXECUTION/RID_LOG.md | EL | 2026-05-21 |
| Staleness trigger | An explicit condition that invalidates an artifact and requires it to be reviewed/updated | Listed in every artifact's universal header | DS | 2026-05-21 |
| Shadow doc | Any document used to make a project decision that is not in the directory or linked from it; prohibited | Must be absorbed within 72h of use | DS | 2026-05-21 |
| Player_Attribute_Matrix | The Player_Attribute_Matrix_v4.docx from the previous bot iteration; staged as a research input artifact in 05_RESEARCH_EXPERIMENTS/ | NOT canonical spec; earns canonical status through validation evidence only | RL | 2026-05-21 |
| arb/ folder | Reference-only artifact from previous iteration; not incorporated into active development until an ADR approves it | Stored in project root; off-limits for Phase 0–6 development | DS | 2026-05-21 |
| Kill switch | The procedure and code path that halts all bot execution (forecasting, order placement, data ingestion) within ≤60 seconds | Runbook at 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_kill-switch.md | OO | 2026-05-21 |

---

## Risk and Operations Terms

| Term | Project-Specific Meaning | Notes | Owner | Last Reviewed |
|------|--------------------------|-------|-------|---------------|
| Max drawdown | The maximum observed loss from a peak to a trough in cumulative PnL over a defined period | Hard limit defined in RISK_APPETITE_CONSTRAINTS.md | RCO | 2026-05-21 |
| Daily loss limit | Maximum allowable loss in a single calendar day before the kill switch is triggered automatically | Hard limit defined in RISK_APPETITE_CONSTRAINTS.md | RCO | 2026-05-21 |
| SLO (Service Level Objective) | A measurable target for system reliability (e.g., 99% uptime during market windows) | Defined at 10_INFRA_OPERATIONS/SLA_SLO_SLI.md | OO | 2026-05-21 |
| P1 / P2 / P3 alerts | Severity classification for operational alerts: P1 = immediate response required (kill switch candidate); P2 = respond within 1h; P3 = respond within 24h | Defined in OBSERVABILITY.md | OO | 2026-05-21 |
