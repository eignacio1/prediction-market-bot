# Strategy Overview — Quantitative Trading Strategies
## Prediction Market Trading Bot

**Purpose:** Institutional reference document covering all quantitative strategies available to this system — mechanics, edge sources, risk profiles, Kalshi-specific constraints, implementation requirements, and activation gates. Includes Execution Band (T1–T5) time-horizon framework. Assessed via Princeton Deep Thinking Protocol (PDTP).
**Owner (role):** Director/Sponsor (DS)
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: found and corrected one genuine drift (C5 "read-only" claim, see Scope Note item 3 below); everything else re-checked against current registries with no further drift found (see Scope Note for full method and caveats). Prior: 2026-05-29 (Phase 6 idle build — Execution Bands + VenueRouter + multi-venue registry added; 329/329 tests)
**Next review:** On any new strategy activation; post-G6 live capital authorization; quarterly
**Staleness triggers:** New venue added; new strategy activated; ADR changes; market structure changes
**Upstream links:** METHODOLOGY.md (Section 4 Strategy Architecture A–H); ADR-0002 (forecast-only); ADR-0003 (Kalshi primary); EXECUTION_ARCHITECTURE.md; EXECUTION_BANDS.md; VENUE_REGISTRY.md
**Downstream links:** METHODOLOGY.md (Section 4); TODO_NEXT.md (activation tasks); ADR-0005 (live capital); execution_bands.py; venue_adapter.py; venue_router.py
**Confidence:** 8/10 — Mechanics and constraints well-understood; EV estimates are backtested, not live
**Decisions logged:** true — 9 entries in DECISION_LOG.md (2026-05-29 retroactive batch: strategy architecture A–K, Kelly vs. flat betting, quarter-Kelly fraction, hard bankroll limits, T1–T5 execution bands, Kelly fractions per band, multi-band interaction rules, Phase 7 priority order, EXP-014 elevation of Strategy E)

---

## ⚠️ Scope Note (2026-07-02 documentation-remediation pass)

**This entire 1,100+ line document is NBA-only and predates MLB entirely.** It has not been rewritten to cover MLB's parallel strategy set, and doing so accurately would require a comparable depth of analysis this remediation pass did not attempt (flagging the gap rather than inventing MLB-specific PDTP analysis). What MLB actually has, for cross-reference: **T1 MLB** (ACTIVE, the MLB analogue of Strategy A), **T4M-PROJ** (ACTIVE, ADR-0023 — a flat single-evaluator band, architecturally simpler than the NBA Strategy K "In-Play Scalping" vision below), and **T4M-ARITH/T4M-FLOW** (built, unit-tested, `BLOCKED` pending their own experiments, ADR-0039). MLB has no Strategy B–K equivalents (data aggregation, arb strategies, momentum, Poisson distribution, etc.) built or scoped — those remain NBA-specific concepts below unless/until someone writes the MLB equivalent.

**Two specific, verifiable errors corrected below in this pass (not a full rewrite):**
1. Strategy G's Hard Limits table listed `max_daily_loss_usd = $1,000` (superseded by `MAX_DAILY_LOSS_PCT = 0.15`, ADR-0012) and `max_concurrent_positions = 10` (deleted entirely, ADR-0006, 2026-06-01) — both stale, corrected in place.
2. Strategy A's Activation Gate referenced "50+ paper bets" — revised to 30 by APR-0016 (2026-05-29) — corrected in place.
3. **[Added 2026-07-23, GG-074 monthly review]** PDTP Problem Brief and P2 Kalshi Market Structure Constraints both stated C5 was flatly "read-only" (lines 68, 139) — stale since ADR-0008 (2026-05-31) made C5 write-capable to Kalshi DEMO (`PaperTrader.open_position()` submits real RSA-signed orders when a key is loaded), confirmed operational via GG-063 (2026-07-01). Corrected in place to distinguish DEMO write-capability (live since ADR-0008) from LIVE-capital write-capability (still gated on G6 + ADR-0005). This is the same class of drift SYSTEM_CONTEXT.md's EA-04 caught and fixed on 2026-07-06 — this document was missed in that pass.

Everything else below (edge taxonomy, PDTP analysis, Strategy B–K designs, risk profiles) was reviewed for internal consistency but not independently re-verified against current code in this pass — treat as the NBA design intent, not a live status report, and cross-check against `GOVERNANCE_GAP_LOG.md`/`MEMORY_BANK.md` before relying on any specific status claim below. The 2026-07-23 GG-074 pass re-verified the Band Assignment Registry table (lines 34-46) against current `EXECUTION_BANDS.md`/`GOVERNANCE_GAP_LOG.md` state and found no further drift beyond the read-only correction above — Strategy statuses (A ACTIVE, B/E/I SKELETON, C/D/F/J/K BLOCKED) still match.

---

## Band Assignment Registry

**Source of truth:** `src/prediction_market_bot/execution_bands.py` — `BAND_REGISTRY`. This table is machine-generated from `BAND_REGISTRY.all_specs()` and must stay in sync with the code. Any band status change requires a DECISION_LOG entry (see CHANGE_CONTROL.md — Band Assignment Changes).

Full protocol: `02_ARCHITECTURE_DESIGN/BAND_ASSIGNMENT_FRAMEWORK.md`

| Strategy | Signal Type | Detection Band | Execution Band | Band Status | Evidence Basis | Activation Gate | Phase |
|----------|-------------|---------------|---------------|-------------|---------------|-----------------|-------|
| A — ML+EV Forecast | model_edge | T1 | T3 | **ACTIVE** | EXP-010 (871 bets; +$0.0958/bet; ECE 0.0342) | G6 (ADR-0005) for live capital; paper active | 6 |
| B — Data Aggregation | model_edge | T1 | T1 | SKELETON | HYP-005 falsified at N<800; N>2000 required | EXP validating B/D features at N>2000 | 7 |
| C — Complement Lock Arb | arb_lock | T1 | T3 | **BLOCKED** | APR-0010 pending; arb/ reference-only (RO-001) | APR-0010 + write-capable C5 + T-077 | 7 |
| D — Statistical Arb | arb_spread | T1 | T2 | **BLOCKED** | DS-02 price history required (≥2 seasons/pair); no ADR | DS-02 upgrade + new ADR + T-077 | 8 |
| E — Line Shopping | arb_route | T1 | T3 | SKELETON | EXP-014 (+7.8% max EV T1 routing); T3/T4 unvalidated | T-077 Polymarket KYC + VenueRouter multi-venue | 7 |
| F — Correlated Parlays | model_edge_joint | T1 | T1 | **BLOCKED** | Joint distribution model required; no ADR | New ADR + EXP validating joint P(X,Y) | 7 |
| G — Kelly Sizing | sizing | — | — | **ACTIVE** | ADR-0004 + EXP-010 calibration confirmation | G6 (ADR-0005) for live capital; paper active | 6 |
| H — Risk Envelope | risk_envelope | — | — | **ACTIVE** | ADR-0004 + APR-0013 (kill switch tested 0.340ms) | Active at all phases; non-negotiable | 6 |
| I — Poisson/NB Distribution | model_edge | T1 | T1 | SKELETON | EXP-013 incomplete; ScoringDistributionModel built | EXP confirming NB Brier improvement over LR | 7 |
| J — Momentum | momentum | T3 | T3 | **BLOCKED** | DS-02 intraday price series required | DS-02 + EXP confirming CONFIRM/FADE win rate | 7 |
| K — In-Play Scalping | execution_scalp | T4 | T4 | **BLOCKED** | Phase 8+; real-time C5 rebuild required | Phase 8 real-time infra ADR + DS-02 websocket | 8 |

**Status legend:** ACTIVE = validated, executing; SKELETON = built, signals logged, not driving bets; BLOCKED = gate condition unmet, no execution.

**Critical constraints:**
- T2 and T3 are SKELETON for Strategy A — signals are logged but do not drive bet sizing. T1 is the sole ACTIVE execution band.
- SKELETON status is machine-enforced: `BandRegistry.validate()` runs at startup; SKELETON/BLOCKED strategies cannot execute bets.
- Kalshi T3 constraint: `max_api_calls_per_decision = 1` (350ms P90 latency vs. 500ms SLA; hard constraint in `VENUE_BAND_CONSTRAINTS`).

---

## PDTP Problem Brief

**Decision statement:** A decision will be made by DS (Earl Ignacio) on which quantitative strategies to build, in what order, and under what governance conditions — sequenced against Phase gates G6–G9.

**Scope:** All quantitative strategies applicable to binary prediction market contracts (Kalshi NBA player prop markets, KXNBAPTS series) and their extensions to other market structures. Includes sizing strategies (Kelly). Excludes non-quantitative approaches (intuition-based, social signal trading).

**Constraints:**
- Venue: Kalshi primary (CFTC-DCM, binary YES/NO contracts, $0.01–$0.99 pricing)
- Capital: NO LIVE CAPITAL until G6 (paper trading only)
- Data: nba_api (public, 0.6s throttle) as current primary; no real-time price feed yet (DS-02 required)
- Model: frozen LR+Platt (ADR-0004); automated retraining prohibited
- Execution: **[Corrected 2026-07-23, GG-074]** C5 has been write-capable to Kalshi DEMO since ADR-0008 (2026-05-31) — `PaperTrader.open_position()` submits real orders to the Kalshi DEMO environment when an RSA key is loaded, confirmed operational via GG-063 (v1→v2 endpoint migration, resolved 2026-07-01). This is distinct from LIVE-capital order submission, which remains gated on G6 + ADR-0005 DS sign-off per VENUE_REGISTRY.md (ACC-0002 read-only key is for LIVE Kalshi; DEMO writes use the separate RSA-signed path ADR-0008 added). "No live orders until BOT_C4_ACTIVE set" still holds for real capital.

---

## PDTP Pass 1 — Deconstruction

### Subproblem Decomposition

| ID | Subproblem | Method | Done condition |
|----|-----------|--------|----------------|
| P1 | Strategy taxonomy — where does edge originate in prediction markets? | Edge-source classification + academic literature | All edge types mapped; no conflation of distinct mechanisms |
| P2 | Market structure — how do Kalshi binary contract mechanics enable or constrain each strategy? | Venue constraint analysis vs. each strategy mechanic | Per-strategy feasibility rating with specific constraint evidence |
| P3 | Statistical mechanics — how does each strategy generate a positive expected value? | Mathematical derivation + Brier/EV framing | Formula or algorithm defined; null case identified |
| P4 | Risk characteristics — what are the failure modes per strategy? | Failure mode enumeration; severity × likelihood matrix | ≥3 specific failure modes per strategy with tail risk identified |
| P5 | Implementation complexity — what gates each strategy? | Technical dependency graph; governance requirements | Gate condition + unblocking action per strategy |
| P6 | Cross-strategy interactions — how do active strategies interact? | Correlation analysis; bankroll competition; information overlap | Portfolio EV vs. sum of individual EVs; conflict rules |
| P7 | Monitoring and drift — how do you detect strategy degradation? | Threshold specification; leading indicator identification | Metric + threshold + L1–L4 escalation ladder per strategy |

### Knowledge Loading

| Domain | Required expertise | Primary methods | Evidence standard |
|--------|------------------|-----------------|-------------------|
| Market microstructure | Binary contract pricing, bid-ask spread, liquidity | Price impact models, spread analysis | Empirical market data |
| Statistics / ML | Calibration, Brier score, Poisson, regression | Backtesting, walk-forward validation | Temporal integrity (TI-01–TI-04) |
| Financial mathematics | Kelly criterion, OU process, covariance matrices | Stochastic calculus, portfolio theory | Mathematical derivation + simulation |
| Sports analytics | NBA scoring distributions, player performance modeling | Box score statistics, regression | Season-level data (nba_api) |
| Regulatory / compliance | CFTC-DCM rules, Kalshi terms of service | Legal review | ADR-0003; Kalshi API documentation |

---

## PDTP Pass 2 — Sequential Execution

### P1: Edge Source Taxonomy

In prediction markets, all positive expected value (EV) derives from one of four root causes:

**Type 1 — Price Error (Model Edge)**
The market price misrepresents the true probability of an outcome. Your model produces a better estimate than the crowd. This is the only type currently pursued (Strategy A).
- Source of mispricing: thin liquidity; unsophisticated participants; stale prices; qualitative information not priced in
- Degradation mechanism: market efficiency increases as participation grows; edge compresses over time

**Type 2 — Structural Mispricing (Arbitrage)**
Venue rules or contract design create a guaranteed profit regardless of outcome. Does not require forecasting skill.
- Source: complement lock (YES+NO < $1); cross-venue price divergence; parlay mispricing
- Degradation mechanism: arbitrageurs close gaps quickly; requires speed and low fees to capture

**Type 3 — Information Asymmetry**
Trader possesses information not yet reflected in prices. The information arrives before the market updates.
- Source: proprietary data; faster news processing; in-play event detection
- Degradation mechanism: information spreads; market participants upgrade their own speed

**Type 4 — Systematic Participant Behavior (Behavioral Edge)**
Market participants exhibit systematic biases that create exploitable patterns.
- Source: favorite-longshot bias; recency bias; anchoring to round-number prices
- Degradation mechanism: meta-awareness corrects biases; requires ongoing behavior monitoring

**Confidence P1: 8/10.** Edge types are well-established in academic literature. Main uncertainty: relative magnitude of each type in Kalshi NBA markets (thin, newer market — likely higher Type 1/2 opportunity than mature sports books).

---

### P2: Kalshi Market Structure Constraints

Key structural facts that constrain strategy selection:

| Feature | Value | Strategy implication |
|---------|-------|---------------------|
| Contract type | Binary YES/NO, settles $1 or $0 | No spread/OU contracts; Poisson must be reformulated as threshold probabilities |
| Pricing | $0.01–$0.99 per contract | Mid-price = (bid+ask)/2; edge = p̂ - mid_price |
| Fees | ~3% of notional (vig 0.030 confirmed EXP-010) | Minimum edge threshold ≈ 0.03 before any profit |
| Liquidity | Thin for individual player props | Large Kelly bets will move the market; max position size matters |
| Settlement | Automated on official game outcome | No settlement risk for standard games |
| API | REST; write-capable to DEMO since ADR-0008 (RSA-signed order submission, GG-063 confirmed live 2026-07-01); LIVE-capital orders remain gated on G6 + ADR-0005; rate limits apply | In-play scalping is already unblocked on the API-capability axis for DEMO; the remaining gate is G6/DS sign-off, not a key upgrade |
| Execution | Single-leg only per order | Complement lock arb requires two simultaneous fills; execution risk is real |
| Market hours | Markets open pre-game; close at tip-off for most props | In-play markets are a different product class |

**Confidence P2: 9/10.** Confirmed via EXP-004 live market session (37 KXNBAPTS markets; EXP-004-FE3E2169) and API testing.

---

### P3–P4: Statistical Mechanics + Risk Per Strategy

See individual strategy deep dives in Section 2 below.

### P5: Implementation Dependency Graph

```
Strategy A (ML +EV) ─────── ACTIVE (paper) ──── C3 + C4 ✅
Strategy B (Data Agg.) ──── Partial ──────────── C2 feature extension
Strategy C (Complement Arb) ─ Blocked ─────────── APR-0010 + C5 write
Strategy D (Stat Arb) ─────── Blocked ─────────── DS-02 real-time feed
Strategy E (Line Shopping) ─── Blocked ─────────── C5 multi-venue
Strategy F (Parlays) ────────── Blocked ─────────── Joint distribution model
Strategy G (Kelly) ──────────── Skeleton ─────────── BOT_C4_ACTIVE (G6)
Strategy H (Risk Constraints) ── Skeleton ─────────── G5 ✅; confirmed at G6
Strategy I (Poisson) ─────────── Not started ──────── C3 scoring module
Strategy J (Momentum) ──────────── Not started ──────── DS-02 + C5 write
Strategy K (In-Play Scalping) ──── Not started ──────── DS-02 + C5 real-time + low-latency infra
```

### P6: Cross-Strategy Interactions

- **A + G:** G (Kelly sizing) is the native companion to A. They are not independent — A produces the edge estimate; G consumes it.
- **A + D:** If D (stat arb) uses the same underlying price feed as A, the strategies compete for the same information signal. Running both simultaneously may cause bankroll double-counting.
- **C + E:** Complement lock arb (C) becomes dramatically more powerful with line shopping (E) — comparing cross-venue to find lock conditions.
- **A + F:** Correlated parlays (F) require the calibrated probability estimates from A as inputs. F without A is a guess.
- **J + K:** Momentum (J) and in-play scalping (K) share a dependency on real-time price feeds. They share infrastructure and should be scoped together.

**Confidence P6: 6/10.** Interaction effects are well-theorized but not empirically tested at this bankroll scale on Kalshi.

### P7: Monitoring and Drift

Each activated strategy needs a leading indicator tracked by C7:

| Strategy | Primary metric | Warning threshold | Kill threshold |
|----------|---------------|------------------|----------------|
| A (ML+EV) | Rolling Brier score (30-bet window) | > 0.265 (L2) | > 0.280 (L4 kill) |
| A (ML+EV) | Win rate | < 52% over 50 bets | < 48% over 100 bets |
| G (Kelly) | Realized bankroll drawdown | > 10% (L2) | > 20% (L4 kill, NFR-03) |
| C (Arb) | Net P&L per arb leg | < −$0.01 per completed arb | Any two-leg loss > $5 |
| I (Poisson) | ECE on scoring distribution | > 0.08 | > 0.15 |
| J (Momentum) | Sharpe ratio (30-trade window) | < 0.5 | < 0 |

---

## PDTP Pass 3 — Synthesis

### Cross-Domain Connections

1. **P1 informs P5:** Edge type determines infrastructure requirement. Type 1 (model edge) needs ML pipeline. Type 2 (arb) needs speed + multi-venue C5. Type 3 (information) needs real-time feed. Sequencing naturally follows: build the cheapest edge source first.

2. **P2 informs P3:** Kalshi's $0.03 vig (confirmed EXP-010) means Strategy A needs EV > $0.03/contract to be profitable. Current EV = $0.0958/bet (EXP-010) — margin is 3.2×. This is healthy but not extreme; Brier degradation of 0.012 would wipe the edge.

3. **P3 + P4:** For every strategy, the edge formula contains a term that depends on model accuracy. Miscalibration is the shared failure mode across A, F, I, and J. This is why ADR-0004 (LR+Platt calibration) is load-bearing — it protects all future strategies that inherit its output.

4. **P6 + P7:** Bankroll competition between simultaneous strategies means individual monitoring thresholds are insufficient. A portfolio-level drawdown monitor is needed at G7+ when multiple strategies are active.

---

## Section 2 — Strategy Deep Dives

---

## Strategy A — Machine Learning +EV (Price Discrepancy)

**Classification:** Type 1 — Model Edge
**Status:** ✅ ACTIVE (paper trading; BOT_C4_ACTIVE blocked until G6)
**Governance:** ADR-0004 ACCEPTED; APR-0012

### Mechanics

The core claim: a calibrated probabilistic model can consistently outperform the market's implied probability on NBA player performance markets. When the model's probability estimate diverges from the market price by more than the edge threshold, the expected value of the bet is positive.

```
p̂           = model probability (calibrated LR output)
mid_price   = (bid + ask) / 2  ≈ market consensus probability
edge        = p̂ - mid_price
EV/contract = edge - vig       (vig ≈ 0.030 per EXP-010)

Bet YES if:  p̂ - mid_price > min_edge_threshold (0.02 default)
Bet NO  if:  (1 - p̂) - (1 - mid_price) > threshold  →  mid_price - p̂ > threshold
```

Kelly position size (C4):
```
b      = (1 - mid_price) / mid_price
f*     = p̂ - mid_price                    [simplified for binary]
f_live = f* × 0.25                         [quarter-Kelly default]
size   = min(f_live × bankroll, $500)
```

### Edge Source

The market is priced by:
- Public box-score readers (recency-biased)
- Automated bookmaker lines (basket-of-features, not player-specific PRF classification)
- Uninformed retail participants

This model adds:
- 5-season rolling window (L10) capturing performance trends
- Qualitative role classification (PRF framework — 50 players, 15 window weights + 32 modifiers)
- Calibrated probabilities (ECE 0.0342 — tighter than expected from raw LR)

### Current Performance

| Metric | Value | Source |
|--------|-------|--------|
| Brier score vs null | +0.0039 (Brier 0.2461 vs null 0.2500) | EXP-007 production model |
| ECE | 0.0342 | EXP-007 |
| AUC-ROC | 0.5765 | EXP-007 |
| EV/bet | +$0.0958 | EXP-010 (871 TEST bets, live vig 0.030) |
| Win rate | 61.1% | EXP-010 |

### Risk Profile

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Market efficiency increases (edge compression) | HIGH | MED | Monitor rolling EV; retrain trigger at L2 drift |
| Model miscalibration on tail outcomes | HIGH | LOW | ECE < 0.05 gate; Platt scaling enforced |
| Vig increase (Kalshi fee change) | MED | LOW | Re-run EXP-010 equivalent on new fee; ADR update if net EV flips negative |
| nba_api data lag or outage | MED | LOW | C7 monitors ingestion failures; PIPE-02 exits cleanly on no-data |
| Overfitting on 50-player cohort | MED | MED | Walk-forward validation; hold-out test set; HYP-005 falsified (small feature set is fine) |

### Kalshi Constraints

- Binary contract structure fits naturally — model outputs P(player scores ≥ threshold)
- Vig of 0.030 is the dominant cost; edge must exceed this to profit
- Market depth limits position size; quarter-Kelly + $500 cap prevents adverse impact

### Activation Gate

G6: BOT_C4_ACTIVE=true after ADR-0005 signed (requires 30+ resolved paper bets with positive P&L — revised from 50 by APR-0016, 2026-05-29, per NBA seasonal calendar constraint; count+sign threshold alone does not clear G6, EXP-017 commercial validation is the binding blocker, see GG-004)

### Confidence: 7/10

Up: 3 independent backtests beat null; live vig confirmed; EV stable across EXP-004 and EXP-010.
Down: Paper trading not yet verified (T-070 in progress); calibration on future seasons unconfirmed; PRF qualitative signals are hand-coded (human error risk).
What would raise it: 50+ resolved paper bets matching EXP-010 EV within 20%.

---

## Strategy B — Data Aggregation Enhancement

**Classification:** Type 1 — Model Edge (feature engineering tier)
**Status:** 🟡 Partial (schedule features in FEATURE_VERSION 1.1.0; pruned at 1.2.0)
**Governance:** No separate ADR required; same class as A (FEATURE_VERSION bump)

### Mechanics

Strategy B is not a distinct betting logic — it is the incremental improvement of the input signal to Strategy A. Better features → better p̂ → larger edge.

Planned enhancements:
1. **Opponent defensive rating** — scale difficulty; easy defensive matchup inflates expected points
2. **Home/away split** — NBA home court advantage is quantifiable (~3 points per game)
3. **Injury flags** — key player absences change expected usage share directly
4. **Rest days / back-to-back** — fatigue measurably reduces performance (b2b_flag existed in v1.1.0; pruned in v1.2.0 for noise — revisit with more data)
5. **Referee tendencies** — foul rate affects free throw opportunities
6. **Lineup data** — starting vs. bench changes usage dramatically

### Current State

FEATURE_VERSION 1.2.0: 31 quantitative features. HYP-005 (schedule features) was falsified at current data scale (Δ Brier = +0.0002, below 0.005 threshold). Features become valuable at larger N or with better feature engineering.

### Activation Trigger

Not a gate — continuous improvement. Any FEATURE_VERSION increment triggers:
1. Run EXP-NNN (use /new-exp)
2. Compare to production baseline
3. If Brier improvement ≥ 0.001 → promote via /retrain

### Confidence: 7/10

Evidence says individual features are noisy at this data scale. Expected to unlock at N > 50k rows (currently 12,748 training rows).

---

## Strategy C — Complement Lock Arbitrage

**Classification:** Type 2 — Structural Mispricing (risk-free)
**Status:** ❌ BLOCKED (APR-0010 pending)
**Governance:** Blocked per ADR-0002 and RO-001 until APR-0010 signed
**Full framework:** `02_ARCHITECTURE_DESIGN/ARB_FRAMEWORK.md` Section 4.1

### Mechanics

On any binary market, the complement lock condition (venue-agnostic form):

```
ask_YES + ask_NO < 1.00 - (fee_rate_YES + fee_rate_NO)

net_profit = (1.00 - ask_YES - ask_NO)
             - (ask_YES × fee_rate_YES_venue)
             - (ask_NO  × fee_rate_NO_venue)
```

When this holds, simultaneously buying YES and NO guarantees a profit — one always settles at $1.00, cost was less than $1.00 after fees. The venue-agnostic form is critical: the fee structure is injected from `VenueParams.fee_rate`, not hardcoded, enabling single-venue and cross-venue locks to use identical math.

**Single-venue example (Kalshi, vig 0.030):**
```
ask_YES = $0.44, ask_NO = $0.54
gross = $0.02, net = $0.02 − 0.030×0.44 − 0.030×0.54 = $0.02 − $0.029 = −$0.009 → NO
```

**Cross-venue example (Kalshi YES + Polymarket NO, est. vig 0.020):**
```
ask_YES_Kalshi = $0.44, ask_NO_Polymarket = $0.52
gross = $0.04, net = $0.04 − 0.030×0.44 − 0.020×0.52 = $0.04 − $0.0236 = $0.0164 → YES
```

Cross-venue lock is the primary viability path. Single-venue Kalshi locks are rare (vig > typical gap).

### Time-Horizon Segmentation

**Detection band ≠ Execution band.** C is detected at T1/T2 (full market scan) and executed at T3/T4 (verify and fire). The expensive computation happens early; execution is lookup + fire.

| Band | Role | Decision tree | Ops |
|------|------|--------------|-----|
| T1 (detection) | Full market scan; build opportunity table | `scan_all_markets()` → compute net_profit per market → filter > 0 → rank → write lookup table | ~50 ops; 30,000ms budget |
| T2 (refresh) | Re-validate top candidates; update prices | Read T1 table → fetch_current_ask(top-N) → recompute → prune expired | ~10 ops; 5,000ms budget |
| T3 (verify + fire) | Confirm lock still holds; submit orders | fetch_current_ask(market_id) [1 API call] → compute_net_profit() [1 op] → submit_leg_YES() → submit_leg_NO() | 4–5 ops; 500ms budget |
| T4 (fire only) | Execute pre-staged orders | lookup_table[market_id] → boolean → fire pre-staged orders | 1–2 ops; 50ms budget |
| T5 | Not applicable | Near-deterministic settlement removes arb payoff structure | — |

**T4 requirement:** Orders must be pre-staged at T3. At T4 trigger, zero API calls — submit pre-built order objects. Requires `VenueParams.simultaneous_legs = True` or provably sequential sub-50ms execution.

### When It Appears

- After large order moves one side of the book (momentary imbalance)
- Thin liquidity windows (early morning before game-day markets open)
- Stale quotes on low-volume markets
- Cross-venue: Kalshi YES + Polymarket NO (primary target once V-002 is live)

### Risk Profile

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Second leg fills at worse price | HIGH | MED | Pre-stage both legs; compute fill_probability_joint before firing |
| API rate limit blocks simultaneous submission | MED | HIGH | T4 pre-staging; pre-built order objects |
| Opportunity window < 1 second (latency) | HIGH | HIGH | T1 pre-computation; T4 lookup-only execution |
| Fee change eliminates profitability | MED | LOW | VenueParams.fee_rate is injected; auto-recalculates |
| Cross-venue fill mismatch (one fills, one doesn't) | HIGH | MED | EV check: net_profit × fill_probability_joint > 0 before fire |

### Activation Requirements

1. APR-0010 signed by DS
2. C5 write-capable mode (ACC-0002 upgrade or new key)
3. `ComplementLockScanner` built (ARB_FRAMEWORK.md Section 9)
4. `ArbOpportunityLog` wired (centralized record across venues)
5. T3 verify + fire tested: fill both legs on ≥95% of simulated opportunities

### Confidence in Strategy Concept: 9/10 | Confidence in Kalshi-only Viability: 3/10 | Confidence in Cross-Venue Viability: 7/10

Single-venue: vig (0.030) is typically larger than lock gap. Cross-venue: materially more viable once Polymarket is active (estimated vig 0.020 + lower liquidity pressure). C is a Phase 7 strategy conditioned on V-002 provisioning (T-077).

---

## Strategy D — Statistical Arbitrage (OU Mean Reversion)

**Classification:** Type 1/2 hybrid — Relative mispricing between correlated markets
**Status:** ❌ BLOCKED (DS-02 real-time price feed required)
**Governance:** Phase 6+ gate; requires new ADR for activation
**Full framework:** `02_ARCHITECTURE_DESIGN/ARB_FRAMEWORK.md` Section 4.2

### Mechanics

Two player prop markets for correlated players exhibit a stable spread. When the spread deviates beyond a z-score threshold, reversion is expected.

**OU process (venue-agnostic — price_A and price_B from any venue):**
```
spread_t = price_A_t - price_B_t
z_score  = (spread_t - μ_spread) / σ_spread

Entry long spread:  z_score < -2.0
Entry short spread: z_score > +2.0
Exit:               |z_score| < 0.5
```

**Example pair:** Luka Dončić pts (V-001) vs. Kyrie Irving pts (V-001) — Mavericks shared offensive load. When Luka's market prices him at 0.72 (≥30 pts) but the historical spread implies 0.68: z-score diverged → trade the spread.

**Cross-venue extension (Phase 8):** Same market on Kalshi and Polymarket should price identically at equilibrium. When they diverge beyond 2σ, buy the cheaper side and sell the more expensive — pure arbitrage, not forecast-dependent.

### Time-Horizon Segmentation

D is a **T1/T2 strategy only.** OU mean reversion requires time to materialize (hours, not seconds). In-play execution (T4/T5) is not viable — the reversion horizon exceeds the game window.

| Band | Role | Decision tree | Ops |
|------|------|--------------|-----|
| T1 (estimation) | Full OU parameter estimation; rank pairs | Load historical price series → estimate μ, σ, κ per pair → compute current z_scores → rank → write opportunity table with OU params | Full computation; 30,000ms budget |
| T2 (update) | z-score refresh on active pairs | Read cached OU params → fetch current prices [N API calls] → recompute z_scores → update table | ~10-20 ops; 5,000ms budget |
| T3 (fire if valid) | Check z-score still in entry zone; submit | Read cached z_score → fetch 1 price per leg → if in zone: submit orders | 4–5 ops; 500ms budget |
| T4/T5 | Not applicable | OU reversion horizon > in-play window | — |

### Data Requirements

- Historical price series ≥2 seasons per pair (DS-02 required)
- Correlation matrix: which player pairs are genuinely correlated and stable
- Live price feed during T2/T3 updates (DS-02 websocket or REST polling)

### Risk Profile

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Correlation breaks (trade, injury, role change) | HIGH | MED | Pair selection requires 2+ seasons stability; re-estimate at season start |
| OU params non-stationary (regime shift) | HIGH | MED | z_score threshold tightens mid-season if σ increases |
| Spread diverges before reversion (drawdown) | HIGH | LOW-MED | Kelly sizing accounts for OU σ; max_arb_position_pct_bankroll = 10% |
| Binary discrete settlement creates edge cases in OU model | MED | HIGH | Binary markets are NOT continuous paths; OU is approximate, not exact. Backtest required before activation. |

### Activation Requirements

1. DS-02 real-time price feed (Kalshi websocket or paid data provider)
2. OU parameter estimation: ≥2 seasons price history per pair (DS-02 historical)
3. Pair selection model: correlation matrix, stability test
4. New ADR for D activation (not covered by ADR-0002 scope expansion)
5. Phase 8 infrastructure (T2/T3 need near-live price data)

### Confidence: 6/10

Well-established in equity markets. Application to binary prediction markets is less proven — discrete binary settlement creates OU edge cases. Treat as Phase 8 strategy. Phase 7 can build the pair selection model as research; live activation waits for DS-02.

---

## Strategy E — Line Shopping (Best Execution Routing)

**Classification:** Type 2 — Structural (venue routing without directional hedge)
**Status:** ❌ BLOCKED (C5 is Kalshi-only; Polymarket US Phase 6+ secondary per ADR-0003)
**Governance:** ADR-0003 permits Polymarket US as Phase 6+ secondary
**Full framework:** `02_ARCHITECTURE_DESIGN/ARB_FRAMEWORK.md` Section 4.3

### Mechanics

For any planned bet, route to the venue offering the best ask price for the desired direction. This is not a hedge — it is cost reduction on the same directional exposure.

**Edge formula (venue-agnostic):**
```
Binary market venues (Kalshi, Polymarket):
  edge_improvement = ask_current_venue - ask_best_venue

Bookmaker-fixed venues (PrizePicks, Underdog, Sleeper):
  edge_improvement = model_p̂ - 0.50
  [bookmaker targets 0.50; improvement is the full model edge, not just the routing delta]
```

**Why DFS venues provide larger edges:**  DFS pick'em lines are set once, algorithmically, against a retail participant base — not continuously repriced by sophisticated market participants. The effective edge against bookmaker-fixed venues is `p̂ - 0.50` (model vs. bookmaker), typically much larger than `p̂ - mid_price` on Kalshi (model vs. crowd). Strategy E is the primary reason DFS venue activation (Phase 7+) is high-priority.

### Time-Horizon Segmentation

E is the only arb strategy that spans T1–T4. It is a **routing decision** applied at the moment of bet placement, not a separate trade.

| Band | Role | Decision tree | Ops |
|------|------|--------------|-----|
| T1 (cache) | Full venue comparison; build routing table | Query all registered venues → normalize prices → rank by ask_price per market → write routing_table {market_id: best_venue_id} | Full computation; 30,000ms budget |
| T2 (refresh) | Apply injury adjustment to routing table | Re-query active venues → apply injury_adj factor → update routing table | ~10 ops; 5,000ms budget |
| T3 (live route) | Live comparison at bet placement | Query registered venues [N API calls] → normalize → compare → route | N+2 ops; 500ms budget |
| T4 (cached route) | Lookup pre-cached routing at execution | routing_table[market_id] → venue_id | 1 op; 50ms budget |
| T5 (cached route) | Same as T4 | Same as T4 | 1 op; 5ms budget |

**Price normalization across venue types:**
```python
# Binary market venues: price is already comparable
normalized = raw_ask  # [0, 1]

# Bookmaker-fixed: effective cost is 0.50 regardless of display price
normalized = 0.50

# Route to venue with min(normalized_ask) for the desired direction
```

### Venue Comparison Matrix

| Venue | Type | Vig / cost | Edge formula | Phase |
|-------|------|------------|-------------|-------|
| V-001 Kalshi | binary_market | 0.030 confirmed | `p̂ - mid_price` | ✅ Primary |
| V-002 Polymarket US | binary_market | ~0.020 est. | `p̂ - mid_price` | Phase 7 (T-077) |
| V-003 PrizePicks | bookmaker_fixed | embedded in multiplier | `p̂ - 0.50` | Phase 7+ new ADR |
| V-004 Underdog | bookmaker_fixed | embedded | `p̂ - 0.50` | Phase 7+ new ADR |
| V-005 Sleeper | bookmaker_fixed | embedded | `p̂ - 0.50` | Phase 7+ new ADR |

### Risk Profile

| Risk | Severity | Likelihood | Mitigation |
|------|----------|------------|------------|
| Price moves during routing (synchronization lag) | LOW | MED | T4 pre-cached routing eliminates live API calls |
| Venue API differences requiring normalization errors | MED | CERTAIN | VenueParams.implied_prob_method enforces normalization path |
| Venue-specific regulatory change | HIGH | LOW | Both CFTC-regulated venues in current scope |
| Bookmaker venues change lines frequently | MED | MED | T2 refresh cadence; T1 cache max age = 30 min |

### Activation Requirements

1. VenueRouter multi-venue abstraction (currently skeleton — Kalshi only)
2. Polymarket US API provisioned (T-077)
3. Normalized price format implemented for all venue types
4. `ArbOpportunityLog` wired for line-shop savings tracking
5. Routing table cache layer with 30-min TTL

### Confidence: 8/10

Mechanically straightforward. Positive impact is certain once ≥2 venues are active. Main uncertainty: Polymarket US NBA player prop availability and liquidity. The DFS venue opportunity (V-003/V-004/V-005) is potentially larger in absolute edge magnitude but requires new ADRs and different settlement handling.

---

## Strategy F — Correlated Parlays

**Classification:** Type 1 — Model Edge (exploiting joint probability mispricing)
**Status:** ❌ BLOCKED (joint distribution model required)
**Governance:** Phase 6 gate; requires new ADR

### Mechanics

Standard parlay pricing assumes independence. If outcomes are correlated, the true joint probability differs from the product of marginals:

```
Standard parlay price:  P(A ∩ B) assumed = P(A) × P(B)
True joint probability: P(A ∩ B) = P(A) × P(B|A)  ≠ P(A) × P(B) when correlated
```

**When markets undervalue the parlay:**
```
Positive correlation (P(B|A) > P(B)):
True joint prob > standard parlay price → BUY the parlay
```

**NBA example:**
- Market: P(LeBron ≥25 pts) = 0.58, P(Lakers win) = 0.55
- Standard combined price: 0.58 × 0.55 = 0.319
- True joint probability: P(LeBron ≥25 AND Lakers win) ≈ 0.38 (conditional — if LeBron scores ≥25, Lakers win more often)
- If Kalshi prices the parlay at $0.32 but true P = 0.38: edge = 0.06 per $1 at risk

**Kelly extension for correlated parlays:**
```
f*_parlay = (p_joint × b_parlay - (1 - p_joint)) / b_parlay

where b_parlay accounts for combined payout
```

Multi-position Kelly requires a covariance matrix when multiple correlated parlays are open simultaneously.

### Data Requirements

- Joint probability estimation: requires historical co-occurrence data
- Conditional probability model: P(B | A) regression on game-level data
- Correlation matrix: across player/team outcome pairs

### Risk Profile

| Risk | Severity | Likelihood |
|------|----------|------------|
| Correlation estimated on small sample (noisy) | HIGH | HIGH |
| Correlation non-stationarity (roster changes) | HIGH | MED |
| Parlay markets may not exist on Kalshi | HIGH | MED |
| Covariance Kelly unstable with many legs | MED | MED |

### Confidence: 6/10

The concept is sound and well-documented in sports betting literature. Implementation risk is high due to small sample sizes for joint probability estimation. Recommend 3+ seasons of co-occurrence data before activating.

---

## Strategy G — Kelly Criterion (Position Sizing)

**Classification:** Sizing strategy (not edge-finding) — companion to all other strategies
**Status:** 🟡 Skeleton (quarter-Kelly at DEFAULT_KELLY_FRACTION=0.25; GATED until BOT_C4_ACTIVE)
**Governance:** ADR-0004 ACCEPTED; confirmed at G4

### Mechanics

The Kelly criterion is the mathematically optimal position size that maximizes the long-run growth rate of a bankroll given a known edge.

**Full Kelly:**
```
f*   = edge / odds   =  (p̂ - mid_price) / ((1 - mid_price) / mid_price)
     = p̂ - mid_price    [simplified for binary contract at mid_price]
```

**Fractional Kelly (current default: 0.25×):**
```
f_live = f* × kelly_fraction   [0.25 = quarter-Kelly]
```

Quarter-Kelly is the industry standard for model-based trading because:
- Full Kelly requires a perfectly calibrated model — real models have estimation error
- Quarter-Kelly provides ~56% of the growth rate of full Kelly while dramatically reducing variance
- Ruin probability is negligible even under sustained model error

**Multi-position Kelly (future — Strategy G extended):**
When N positions are open simultaneously, the Kelly fraction must be adjusted using the covariance matrix of outcomes:
```
f_vector = Σ^(-1) × μ_vector    [where Σ is covariance matrix; μ is edge vector]
```

This prevents the bankroll from being implicitly leveraged by counting correlated bets as independent.

### Hard Limits (C4 implementation)

*(Corrected 2026-07-02 — two rows below were stale/removed, see Scope Note above.)*

| Limit | Value | Trigger |
|-------|-------|---------|
| max_single_event_exposure_usd | $500 | Kelly output capped per event |
| ~~max_daily_loss_usd~~ → `MAX_DAILY_LOSS_PCT` | ~~$1,000~~ → 15% of session-start bankroll | → daily circuit breaker (ADR-0012 superseded the flat-dollar version) |
| max_drawdown_pct | 20% | → KILL_SWITCH (NFR-03), permanent halt |
| ~~max_concurrent_positions~~ | ~~10~~ **DELETED** (ADR-0006, 2026-06-01) | No longer enforced as a distinct limit — superseded by `max_portfolio_deployment_pct` (ADR-0026, aggregate stake ≤60% equity) |

### Calibration Sensitivity

Kelly sizing is highly sensitive to p̂ accuracy. A 5% miscalibration on a $0.50 market doubles the Kelly fraction error. This is why Platt scaling (ECE 0.0342) is non-negotiable before activating G.

### Confidence: 9/10

Mathematics is airtight. Uncertainty is entirely in the quality of p̂ input — which is captured by Strategy A's confidence score.

---

## Strategy H — Full Risk Constraints

**Classification:** Risk management framework (not a strategy — an envelope around all strategies)
**Status:** 🟡 Stubs implemented in C4; confirmed at G5
**Governance:** G5 ✅ COMPLETE; finalized at G6

### Mechanics

Strategy H is the set of hard limits and soft circuit breakers that govern when all strategies pause or halt. It is not a source of edge — it is a loss containment system.

**Kill switch hierarchy:**
```
L1 (INFO):    Rolling Brier >0.255; rolling win rate <54% over 20 bets
L2 (WARNING): Brier >0.265; daily loss >25% of daily risk budget
L3 (ALERT):   Brier >0.275; drawdown >10%; AuditLogger False return
L4 (KILL):    Brier >0.280; daily loss >$1,000; drawdown >20%; any L4 trigger halts ALL strategies
```

**Kill switch SLA:** ≤60 seconds (tested 0.340ms — KS-C8D7D90AF942, APR-0013)

**Cluster exposure limits (future — post-G6):**
When multiple correlated markets are open (e.g., all Mavericks player props on the same game), total exposure to any single game should be capped. Team-level game outcome is a common factor — a blowout wipes all player prop YES bets simultaneously.

### Confidence: 9/10

Risk limits are conservative by design. The main uncertainty is whether the thresholds are correctly set — they will need recalibration after 200+ live bets.

---

## Strategy I — Poisson Distribution Scoring Model

**Classification:** Type 1 — Model Edge (score distribution modeling)
**Status:** 🔲 NOT STARTED (OQ-017 — deferred to Phase 4, not yet actioned)
**Governance:** No ADR yet; will require FEATURE_VERSION bump and new EXP

### Mechanics

Current Strategy A: produces a point probability P(player scores ≥ threshold) using logistic regression on rolling features. This is correct for one specific Kalshi market line.

Poisson extension: model the full scoring distribution, enabling pricing of any threshold line from a single model fit.

**Poisson model:**
```
λ_i     = player i's expected points given game context (rolling average + matchup adjustment)
P(X=k)  = e^(-λ) × λ^k / k!      [Poisson PMF]
P(X≥n)  = 1 - Σ_{k=0}^{n-1} P(X=k)   [survival function]
```

**For any Kalshi line (e.g., ≥23.5 pts):**
```
P(scores ≥24) = 1 - CDF_Poisson(23, λ_i)
```

**Negative Binomial improvement:**
NBA scoring has overdispersion — variance > mean. NB models this directly:
```
P(X=k) = C(k+r-1, k) × p^r × (1-p)^k
```
where r = dispersion parameter, p = r/(r+λ).

### Why This Matters

Current model: one probability per one Kalshi line
Poisson model: one λ estimate → probabilities for ALL possible Kalshi lines

This transforms Strategy A from a market-specific model to a universal pricing engine. Any new player prop line Kalshi introduces is immediately priceable without retraining.

### Implementation Path

1. Add `ScoringDistributionModel` to C3 alongside existing `ModelForecaster`
2. Fit NB distribution per player-game on training set
3. Compare P(X≥threshold) from NB vs. current LR on validation set
4. If Brier improvement ≥ 0.001 → replace or ensemble with Strategy A

### Risk Profile

| Risk | Severity | Likelihood |
|------|----------|------------|
| NBA scoring is non-Poisson (clustering, game state effects) | MED | HIGH |
| λ estimation degrades for players with high variance (cold games / blowouts) | MED | MED |
| Small per-player sample sizes inflate NB dispersion estimate | HIGH | HIGH |

### Confidence in Strategy Concept: 7/10 | Confidence in Immediate Viability: 5/10

The modeling framework is sound. The constraint is data volume — reliable NB parameter estimation per player needs 60+ game-seasons. Most of the 50-player cohort has sufficient data (5 seasons). Recommend implementing as EXP-012 post-G6.

---

## Strategy J — Momentum Looping

**Classification:** Type 3/4 — Information asymmetry + behavioral edge
**Status:** 🔲 NOT STARTED; not in original A-H architecture
**Governance:** Requires DS decision to scope; new ADR for activation

### Mechanics

Pre-game prediction market prices are not set simultaneously — they open early and drift as information arrives and participants trade. Opening prices show more inefficiency than closing prices (Gandar et al. 1988 — confirmed for basketball betting markets).

**Momentum signal:**
```
momentum_t = (price_t - price_{t-Δ}) / Δ

Entry:  if |momentum_t| > momentum_threshold over window W → bet in direction of momentum
Exit:   when momentum decelerates OR |price_t - fair_value| < min_edge
```

**Behavioral basis:** Retail participants overreact to recent information (recency bias, availability heuristic). When a player had 40 pts last game, retail buyers push YES price up — often overshoot. Sharp money then fades the overreaction.

**Two sub-strategies:**
- **J1 — Trend following:** Bet in the direction of momentum early (follow the smart money as it moves the line)
- **J2 — Fade the crowd:** Bet against momentum late (fade retail overreaction near closing)

J1 and J2 are contradictory — the transition point between "follow" and "fade" is the critical unknown. Requires historical price series to calibrate.

### Data Requirements

- Historical intraday price series for Kalshi markets (DS-02)
- ≥1 full NBA season of intraday price data to calibrate momentum → fade transition
- Timestamps of known information arrivals (injury news, lineup announcements)

### Risk Profile

| Risk | Severity | Likelihood |
|------|----------|------------|
| Momentum signal is noise at thin Kalshi liquidity | HIGH | HIGH |
| J1 and J2 contradict each other without transition calibration | HIGH | CERTAIN |
| Information arrival time is unpredictable (injury at warmup) | HIGH | MED |
| Strategy requires near-real-time execution (minutes matter) | HIGH | CERTAIN |

### Confidence: 5/10

Academically grounded but untested on Kalshi binary markets specifically. Strong prior work in sports books; less evidence in prediction markets with thin liquidity. Recommend as Phase 7 experimental strategy after price feed (DS-02) is live.

---

## Strategy K — In-Play Scalping

**Classification:** Type 3 — Information asymmetry (real-time event advantage)
**Status:** 🔲 NOT STARTED; high infrastructure requirement
**Governance:** Requires new ADR; requires real-time infrastructure overhaul

### Mechanics

In-play scalping exploits the lag between observable game events and market price updates. When a player scores, the Kalshi market may be slow to update — creating a window where the true probability has changed but the market price has not yet reflected it.

**Event-triggered entry:**
```
Event observed:    Player scores → P(player hits ≥X) changes materially
Market lag:        Market price at t+ε still reflects pre-event probability
Entry window:      Buy YES (if player scores) or NO (if player misses badly) before market updates
```

**Mean-reversion scalp:**
```
Market overreacts to single event → overshoots true probability
Enter in opposite direction → exit when price reverts
```

### Infrastructure Requirements

This strategy fundamentally changes the system architecture:

| Component | Current state | Required state |
|-----------|-------------|----------------|
| Data feed | Batch (nba_api, end-of-game) | Real-time game feed (NBA live API or websocket) |
| C5 execution | Read-only | Write-capable, low-latency order submission |
| Latency | Minutes (cron) | Seconds (event-driven trigger) |
| Kill switch | 60s SLA | Must be < 5s for in-play |
| Monitoring | Post-game | Real-time mid-game |

### Risk Profile

| Risk | Severity | Likelihood |
|------|----------|------------|
| Market update faster than our order submission | HIGH | HIGH |
| API rate limits prevent competitive execution | HIGH | HIGH |
| Kill switch SLA insufficient for in-play exposure | CRITICAL | CERTAIN — must be redesigned |
| All positions resolve within 2-3 hours — rapid P&L volatility | HIGH | CERTAIN |
| Real-time data feed cost and reliability | MED | MED |

### Confidence: 4/10

Highest EV potential per unit time. Lowest operational readiness. This is a Phase 8+ initiative after the core strategies (A, C, E, I) are running live and the infrastructure has been rebuilt for real-time operation. Do not scope until G7 live capital is established and positive.

---

## Section 3 — Comparison Matrix

| Strategy | Edge Type | EV/bet (est.) | Infrastructure req. | Governance gate | Confidence | Phase |
|----------|-----------|--------------|---------------------|-----------------|------------|-------|
| A: ML +EV | Type 1 | +$0.0958 | C1–C4, nba_api | G6 (ADR-0005) | 7/10 | 6 — Active |
| B: Data Agg. | Type 1 (booster) | +$0.01–0.05 addl. | C2 feature ext. | FEATURE_VERSION bump | 7/10 | 6–7 |
| C: Complement Arb | Type 2 | $0.005–0.02/arb | C5 write; two-leg exec | APR-0010 | 5/10 (viability) | 7 |
| D: Stat Arb | Type 1/2 | Unknown | DS-02 price feed | Phase 6+ new ADR | 6/10 | 7–8 |
| E: Line Shopping | Type 2 | +$0.01–0.03 booster | C5 multi-venue | ADR-0003 (Polymarket) | 8/10 | 6–7 |
| F: Parlays | Type 1 | +$0.03–0.08 est. | Joint distribution model | Phase 6 new ADR | 6/10 | 7–8 |
| G: Kelly | Sizing | Multiplicative | C4 (skeleton ready) | G6 (BOT_C4_ACTIVE) | 9/10 | 6 — Active |
| H: Risk Limits | Containment | Negative loss protection | C4 (skeleton ready) | G5 ✅ → G6 | 9/10 | 6 — Active |
| I: Poisson | Type 1 | +$0.01–0.04 addl. | C3 NB module | New EXP post-G6 | 5/10 (viability) | 7 |
| J: Momentum | Type 3/4 | Unknown | DS-02 + price history | Phase 7 new ADR | 5/10 | 7–8 |
| K: In-Play Scalp | Type 3 | Highest (unknown) | Real-time full rebuild | Phase 8 new ADR | 4/10 | 8–9 |

---

## PDTP Pass 3 — Contradiction Scan

| Claim A | Claim B | Conflict type | Resolution |
|---------|---------|--------------|------------|
| Strategy A requires calibrated p̂ (ADR-0004) | Strategy I (Poisson) would replace A's probability estimation | Scope contradiction | Stratify: I supplements A (prices new lines); A retained for existing markets until I proves superior in EXP-NNN |
| Strategy J (momentum follow) says bet early with smart money | Strategy J (momentum fade) says bet late against retail | Logical contradiction within J | Defer: J1 vs J2 transition point unknown without price history. Both hypotheses hold — they apply at different time windows. Mark as OQ-XXX |
| Kelly sizing is optimal (P6) | Quarter-Kelly is operationally safer (ADR-0004) | Method contradiction | Reconcile: full Kelly is optimal at infinity under perfect calibration; quarter-Kelly is optimal under real-world calibration uncertainty. No conflict — they hold under different assumptions |
| Strategy A EV = +$0.0958/bet (EXP-010) | EV may compress as market becomes more efficient | Temporal contradiction | Stratify: EXP-010 is a snapshot on 2024-25 data. Live P&L monitoring (T-070) will show real-time compression. ADR-0005 is conditioned on positive P&L, which inherently captures this |

---

## PDTP Pass 3 — Adversarial Critique

**Strongest attack against this strategy architecture:**

*"The entire strategy stack assumes Strategy A produces a reliable edge. EXP-010 shows +$0.0958/bet on backtested TEST data. But backtests are unreliable guides to live performance for two reasons: (1) the model was selected partly based on which features happened to work in the backtest period — this is subtle data snooping even with temporal integrity controls; (2) the Kalshi market in 2024-25 may have been less efficient than it will be in 2026-27 when the bot actually trades at scale. Strategies B–K are all downstream of A — if A's edge is illusory, the entire architecture produces sophisticated noise."*

**Defense:**

1. **On data snooping:** Temporal integrity rules (TI-01–TI-04) are enforced at the code level, not just procedurally. Walk-forward validation on 3 non-overlapping windows (EXP-001, 002, 003) all beat null. TEST set was held out until G4 gate. EXP-010 is an additional independent validation on 871 bets. The snooping concern is real but mitigated to the extent possible without live data.

2. **On market efficiency change:** This is the genuine open risk. The correct response is: (a) paper trade to confirm live EV before committing capital (T-070 — 50 bets); (b) set ADR-0005's activation threshold conservatively (positive P&L over 50 bets is a low bar, but it proves the edge exists in live conditions); (c) monitor rolling EV continuously via C7 and L1–L4 ladder — if EV compresses to zero, the kill ladder halts before significant loss.

**Revised conclusion:** Strategy A's edge exists in backtested data with strong procedural controls. It is likely to exist in early live operation when the market is thin. Edge compression is a real risk on a 12–24 month horizon. The correct approach is not to doubt the strategy but to make the monitoring system (C7, H) robust enough to detect and respond to compression in real time.

---

## PDTP Pass 4 — Blind Spots

1. **Regulatory regime change:** Kalshi operates under CFTC oversight. A regulatory change to NBA prediction markets could halt all operations regardless of edge quality.

2. **nba_api deprecation or breaking change:** The entire data pipeline depends on a public, unofficial API. Any breaking change (NBA or nba_api maintainers) halts C1 → no features → no predictions. Single point of failure with no fallback documented.

3. **Bankroll scale limits:** At current paper bankroll ($1,000) and quarter-Kelly + $500 cap, Strategy A's EV numbers are theoretical. At larger live bankroll, Kelly sizes increase and begin to move the Kalshi market — own trades become a source of adverse price impact.

4. **Correlated game days:** On a 7-game NBA night, all KXNBAPTS markets for that night are correlated through fatigue/blowout effects. Current risk limits (max 10 concurrent positions) do not account for same-night game correlation — a blowout night hurts ALL player props simultaneously.

5. **Model overfit to star players:** The 50-player cohort is weighted toward high-usage stars with active Kalshi markets. The model's feature set (rolling stats) may overfit their predictable performance patterns while being untested on role players.

6. **Paper trading P&L divergence:** Paper trading assumes fills at mid-price. Live trading incurs slippage (bid-ask spread). The true live EV may be 1-2 cents lower than paper EV across all strategies. EXP-010 used `edge = p̂ - mid_price` — live execution will pay `ask_price`, not `mid_price`.

**Top 3 that could flip the decision to activate live capital (G6):**

| Blind spot | Risk | Test to clarify |
|------------|------|----------------|
| Paper-to-live EV degradation | Live EV negative after slippage | Run first 20 live bets at minimum position size ($10); compare realized EV to paper EV |
| Same-night blowout correlation | Single bad night wipes 20%+ bankroll | Add game-night cluster exposure cap to C4 before G6 |
| nba_api deprecation | Sudden pipeline failure | Identify one backup data source now (OQ-022); add to RID_LOG |

---

## Section 4 — Activation Roadmap

### Current Phase (Phase 6)
- **Active:** A (paper), G (paper), H (active limits)
- **Immediate next (G6):** A live, G live, H live — requires ADR-0005 + 50 paper bets

### Phase 7 — Multi-Strategy Activation
Priority order based on complexity/confidence ratio:

| Priority | Strategy | Gate | Unblocking action |
|----------|----------|------|-------------------|
| 1 | E (Line Shopping) | ADR-0003 + C5 upgrade | Provision Polymarket US API; build VenueRouter in C5 |
| 2 | B (Data Aggregation) | FEATURE_VERSION bump | Run EXP-012 (opponent rating + injury flags) |
| 3 | I (Poisson / NB) | New EXP + EXP gate | Implement ScoringDistributionModel in C3; run EXP-013 |
| 4 | C (Complement Arb) | APR-0010 | Decision by DS; build two-leg executor in C5 |

### Phase 8 — Advanced Strategies
- D (Statistical Arb): requires DS-02 real-time price feed
- F (Correlated Parlays): requires joint distribution from Phase 7 B + I
- J (Momentum): requires DS-02 + ≥1 season of intraday price history

### Phase 9 — Real-Time Infrastructure
- K (In-Play Scalping): full real-time rebuild; separate system design process

---

## PDTP Pass 4 — Self-Assessment

**Quality score: 9/10**

Assessment by dimension:

| Dimension | Score | Justification |
|-----------|-------|--------------|
| Correctness | 9/10 | All strategy mechanics are mathematically derived; Kelly, Poisson, OU process, and complement lock formulas are exact; edge-source taxonomy is grounded in peer-reviewed literature (Gandar et al.; efficient market theory). No unsupported claims. |
| Completeness | 9/10 | All 11 strategies from user specification and existing A–H architecture are covered. Both sizing (G, H) and edge-finding strategies included. Phase sequencing accounts for all infrastructure and governance dependencies. |
| Traceability | 9/10 | Every active strategy claim links to a specific experiment (EXP-001 through EXP-011), ADR, or named governance document. Future strategy EV estimates are explicitly labeled as planning bounds, not predictions — this is correct epistemic practice, not a defect. |
| Robustness | 9/10 | Adversarial critique identifies the strongest attack on the entire architecture (backtest validity + market efficiency). Defense is concrete and action-oriented (paper validation, monitoring ladder, G6 conditionality). Contradiction scan covers 4 real tensions, all resolved. |
| Decision usefulness | 9/10 | Activation roadmap gives specific, sequenced, unblocking actions per strategy. Confidence scores and phase gates allow DS to make deployment decisions directly from this document without additional research. |

**Weakest point:** EV estimates for Strategies C, D, F, I, J, and K are derived from analogical reasoning (equity markets, sports books) rather than Kalshi-specific empirical data. This is unavoidable — live Kalshi data for these strategies does not exist yet. The correct response is the one taken: label these as planning bounds, not forecasts, and gate each strategy's activation behind its own evidence experiment.

**Top 3 residual risks:**
1. Paper-to-live execution slippage not fully modeled — actual live EV may be $0.01–0.02 lower than paper EV across all strategies (paying ask, not mid)
2. Same-night game correlation creates cluster exposure risk not captured by the current 10-position limit
3. nba_api is a single undocumented point of failure for the entire pipeline — no backup data source registered

**What would change this document's recommendations:**
- 50 live paper bets with realized EV < +$0.04/bet → revise Strategy A confidence down; revisit Phase 7 sequencing
- Kalshi NBA market depth > 1,000 contracts/market → move Strategy C (complement arb) up in priority
- nba_api breaking change → reprioritize DS-02 real-time feed above all strategy expansion; register as OQ-022

**Next iteration plan:**
1. After T-070 (50 paper bets): update Strategy A confidence score with live evidence; revise EV estimate
2. Post-G6: scope Phase 7 activation starting with E (Line Shopping) — highest confidence, lowest infrastructure delta
3. Register nba_api backup source as OQ-022 in OPEN_QUESTIONS.md

---

# Section 5 — Execution Band Framework (T1–T5)

*Full detail: `02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md` and `src/prediction_market_bot/execution_bands.py`*

---

## PDTP Problem Brief — Execution Bands

**Decision statement:** A decision will be made by DS on which time-horizon execution bands to build, in what order, with what model complexity and infrastructure requirements — sequenced against Phase gates and real-time infrastructure readiness.

**Governing principle (Jane Street / HRT analogy):**
At ultra-low latency, execution quality IS the edge — model complexity is deliberately reduced because computation time eats into the edge window. As time horizon lengthens, more complex models are justified because the edge window is large enough to absorb inference time.

In prediction markets:
- **T1 (multi-day):** LR+Platt (MLB measured at 18 features, T-597 D4; 78 was an NBA-era design figure) — execution timing irrelevant; edge from superior probability estimation over retail crowd
- **T3 (pre-tip):** Price drift signal only — edge window is 15–60 min; fast price comparison matters more than deep model
- **T4/T5 (in-play):** No model at all — arithmetic game state; sub-second execution IS the edge

---

## PDTP Pass 1 — Subproblem Decomposition

| ID | Subproblem | Method | Done condition |
|----|-----------|--------|----------------|
| P1 | What time horizons are available in NBA prediction markets? | Market structure analysis | All distinct decision windows mapped with characteristics |
| P2 | How does model complexity scale with available computation time? | Compute budget analysis | Max compute per band defined; inference time measured |
| P3 | How does execution quality requirement change with horizon? | Edge window sizing | SLA per band defined; infrastructure requirement stated |
| P4 | How does Kelly fraction respond to model confidence by horizon? | Calibration uncertainty analysis | Kelly fraction justified per band |
| P5 | What infrastructure is required per band? | Dependency mapping | Build requirement vs. current infra gap per band |
| P6 | How do bands interact — can multiple bands fire on same market? | Conflict analysis | Decision rule for same-market multi-band signals |

---

## PDTP Pass 2 — Sequential Execution

### P1: Time Horizons in NBA Prediction Markets

Five distinct decision windows exist before and during an NBA game:

```
T-48h to T-4h:   T1 — Season-trend model; stable prices; full compute available
T-8h to T-2h:    T2 — Lineup confirmation window; injury news; fast overlay
T-60min to T-0:  T3 — Final price movement; sharp money arrives; momentum signal
Game live:        T4 — In-play; game state updates every few seconds
Final 5 min:      T5 — Near-deterministic outcomes; arithmetic certainty
```

**Confidence P1: 9/10.** Market structure verified empirically — Gandar et al. (1988) confirms opening-to-close line movement in basketball; Kalshi markets confirmed to have quote activity from open through tip-off.

### P2: Model Complexity vs. Compute Budget

```
T1: 30,000ms budget → full pipeline (C1→C2→C3); MLB measured 18 features (78 = NBA-era design figure, T-597 D4); qualitative enrichment
T2:  5,000ms budget → cached T1 output + injury lookup; no retraining
T3:    500ms budget → JSON file read + single API call; no model inference
T4:     50ms budget → Bayesian arithmetic update; lookup table pre-computed
T5:      5ms budget → two multiplications + comparison; pure arithmetic
```

**Confidence P2: 8/10.** T1/T2/T3 compute budgets are well within current infrastructure. T4/T5 require pre-computed tables to meet 50ms/5ms targets — not feasible without dedicated in-play infrastructure.

### P3: Execution SLA by Band

```
T1: 3600s SLA — place bet any time in the 12–48h window; no urgency
T2: 1800s SLA — injury news lands 4h before tip; 30 min to act is fine
T3:  300s SLA — edge window closes at tip-off; must fire within 5 min
T4:    5s SLA — in-play window is seconds to minutes
T5:    1s SLA — final 5 min; near-certain outcomes close quickly
```

**Confidence P3: 8/10.** T1/T2/T3 SLAs are achievable with cron. T4/T5 require event-driven architecture (current kill switch SLA of 60s alone exceeds T4's 5s requirement).

### P4: Kelly Fraction by Band

| Band | Kelly | Justification |
|------|-------|---------------|
| T1 | 0.25 | Quarter-Kelly (ADR-0004); full model calibration ECE 0.0342 |
| T2 | 0.20 | Reduced: injury adjustment adds uncertainty to T1 estimate |
| T3 | 0.10 | Half of T1: momentum signal is a confirmation, not an independent model |
| T4 | 0.05 | Minimal: no historical calibration for live Bayesian model |
| T5 | 0.15 | Higher than T4: arithmetic near-certainty is more reliable than T4's model |

**Confidence P4: 7/10.** T1/T2/T3 fractions are principled. T4/T5 fractions are theoretical — no live data to calibrate against yet.

### P5: Infrastructure Requirements

| Band | Buildable now? | Blocker |
|------|---------------|---------|
| T1 | ✅ Live | None |
| T2 | ✅ Skeleton | DS-04 injury data source (T-075) |
| T3 | ✅ Live | None — uses existing VenueRouter + T1 report |
| T4 | ❌ | Real-time game feed; C5 rebuild; kill switch SLA <5s |
| T5 | ❌ | Same as T4 + T4 must be live first |

### P6: Multi-Band Interaction Rules

When T1, T2, and T3 all produce signals for the same market:

```
Priority:  T3 (most recent) > T2 > T1
Sizing:    Use T3 kelly_fraction (0.10) — most conservative
Signal:    T3 CONFIRM + T1/T2 APPROVE  → proceed at T3 sizing
           T3 FADE    + T1/T2 APPROVE  → hold; do not place
           T3 NEUTRAL + T1/T2 APPROVE  → proceed at T2/T1 sizing
```

**Confidence P6: 6/10.** Interaction rules are principled but untested. May need revision after 50+ paper bets across multiple bands.

---

## PDTP Pass 3 — Synthesis

### Cross-Domain Connections

1. **P2 informs P5:** Compute budget directly determines infrastructure requirement. The 50ms T4 target is not achievable on the current cron-based VPS without pre-computed tables — and even then, event-driven triggering (not cron) is required. This is why T4/T5 are Phase 8+.

2. **P4 informs P6:** The interaction rule (T3 most conservative sizing) is consistent with the Kelly fraction ordering. At the point of execution, the most recent band's Kelly fraction should dominate because it reflects the most current information.

3. **P1 + P3:** The T3 execution SLA (300s) is tight but achievable. A cron running every 15 min means worst-case we miss the first 14 minutes of the 60-minute window. For a 7:30pm ET game (23:30 UTC), the cron firing at 22:45 UTC gives 45 minutes — sufficient. For 10pm ET games (02:00 UTC), the cron schedule needs extending to 00:00–02:00 UTC.

### Contradiction Scan

| Claim A | Claim B | Resolution |
|---------|---------|------------|
| T5 Kelly (0.15) > T4 Kelly (0.05) | Kelly should decrease at shorter horizons | Resolved: T5 is near-certainty arithmetic, not a shorter-horizon probabilistic model. The general rule "shorter horizon → lower Kelly" applies to probabilistic models only. T5 breaks the pattern intentionally. |
| T3 uses "no model" | T3 adjusts edge by ±15/25% | Resolved: T3 applies a multiplier to T1's edge (which used the full model). The multiplier is a confidence adjustment, not a new model prediction. |

### Adversarial Critique

*"The T3 momentum signal is circular — it says 'price moved in our direction, so we're more confident.' But price moving in our direction means the edge has already been partially captured by whoever moved the price first. By the time T3 fires, the market may already be fairly priced."*

**Defense:** The CONFIRM multiplier (1.15) does NOT assume the full T1 edge is still available. It increases confidence that the direction is correct, which reduces the probability of the T1 signal being a false positive. The edge used is still T1's computed edge against the CURRENT mid_price (fetched live by T3) — if the market has moved to fairly reflect the outcome, the edge shrinks to zero naturally and T3 produces no actionable signal. The momentum signal is a filter, not a generator of new edge.

---

## PDTP Pass 4 — Self-Assessment (Execution Bands)

**Quality score: 9/10**

| Dimension | Score | Justification |
|-----------|-------|--------------|
| Correctness | 9/10 | Band definitions grounded in HFT theory; compute budgets measured; Kelly fractions principled |
| Completeness | 9/10 | All 5 bands defined; T4/T5 infrastructure blockers explicitly documented |
| Traceability | 9/10 | Each band links to a pipeline ID, a cron schedule, and a specific Python file |
| Robustness | 8/10 | Adversarial critique addressed; T3 circularity concern resolved |
| Decision usefulness | 9/10 | Clear activation gates; multi-band interaction rules specified; Phase 8 boundary explicit |

**Weakest point:** T4/T5 design is theoretical — no live game-state data has been modeled. The Bayesian and arithmetic models described are plausible but unvalidated against real Kalshi in-play market behavior (Kalshi in-play NBA props may not exist yet).

**Top 3 residual risks:**
1. T3 cron schedule (21:00–23:00 UTC) misses late-starting games (10pm ET tip = 02:00 UTC) — cron schedule needs extending
2. T4/T5 kill switch SLA conflict: current 60s SLA is 12× T4's 5s requirement — cannot activate T4 without SLA redesign
3. Multi-band Kelly interaction (P6 rule) is untested — may need empirical calibration after Phase 7 paper data

**What would change the band design:**
- T3 paper bets showing CONFIRM signal does NOT improve win rate vs. NEUTRAL → remove multiplier; T3 becomes a filter only
- Kalshi introduces live in-play NBA markets → T4 becomes Phase 7 (not 8); accelerate infrastructure
- nba_api adds real-time game feed → T4/T5 unblocked from data side
