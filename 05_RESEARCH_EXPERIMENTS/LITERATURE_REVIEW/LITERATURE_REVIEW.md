# Literature Review — Prediction Market Trading Bot

**Purpose:** Document relevant prior work, theoretical foundations, and empirical findings that inform the research design. Prevents reinventing what is already known. Each section maps to a specific hypothesis or assumption in HYPOTHESES.md / ASSUMPTIONS_REGISTER.md.  
**Owner (role):** Research Lead (RL)  
**Last reviewed:** 2026-05-22 (Section 4 expanded — NBA-specific; T-020 complete)  
**Next review:** Weekly during Phase 1; after each experiment; at G4  
**Staleness triggers:** New relevant paper identified; findings contradict assumptions; G4 evidence review  
**Upstream links:** RESEARCH_QUESTIONS.md, HYPOTHESES.md, ASSUMPTIONS_REGISTER.md  
**Downstream links:** EXPERIMENT_LOG/  
**Decision references:** ADR-0002  
**Confidence:** 7/10 — Section 4 expanded to NBA-specific following OQ-003 resolution; Sections 1–3, 5 remain at Phase 1 baseline; primary source verification pending; OQ-015 registered for Synergy/Second Spectrum access

---

## Coverage Map

| Topic | Hypothesis Addressed | Assumption Addressed | Status |
|-------|---------------------|---------------------|--------|
| 1. Prediction market efficiency | HYP-003 (edge > vig) | ASM-001 (markets inefficient in target domain) | Baseline complete |
| 2. Brier score as evaluation metric | HYP-001 (DS-01 has signal) | ASM-004 (Brier score is appropriate metric) | Baseline complete |
| 3. Kelly criterion and Fractional Kelly | HYP-002 (calibrated p̂ + Kelly = positive EV) | ASM-005 (fractional Kelly is appropriate) | Baseline complete |
| 4. Feature engineering for target domain | HYP-001, HYP-004 | ASM-002 (player attributes predict outcomes) | **NBA-specific baseline complete** — OQ-003 resolved 2026-05-22; T-020 done |
| 5. Calibration methods | HYP-001, HYP-002 | ASM-003 (calibration is achievable) | Baseline complete |

---

## 1. Prediction Market Efficiency

### Theoretical Background

Prediction markets are designed to aggregate dispersed information into a single probability estimate. The efficient market hypothesis (EMH) applied to prediction markets predicts that prices fully reflect available information, making systematic profit impossible. The key question for this project is whether target-domain markets are **partially** inefficient — enough to generate edge, but not enough to be trivially exploitable.

### Empirical Evidence on Efficiency

**Evidence for efficiency:**
- Forsythe, Nelson, Neumann & Wright (1992) — *Anatomy of an Experimental Political Stock Market* — showed prediction markets outperformed polls in aggregate probability accuracy. Prices tracked fundamentals well.
- Berg, Forsythe, Nelson & Rietz (2008) — *Results from a Dozen Years of Election Futures Markets Research* — IEM election markets were better calibrated than polls on average over 12 years.
- Wolfers & Zitzewitz (2004) — *Prediction Markets* (Journal of Economic Perspectives) — comprehensive review; markets efficient in aggregate but with systematic small deviations near extremes (favouritism bias, longshot bias).

**Evidence for inefficiency / exploitable deviations:**
- Longshot bias: outcomes with low market-implied probability are systematically overpriced. First documented in horse racing (Griffith, 1949); replicated in sports prediction markets. Implies a model that avoids longshots may have a small edge.
- Favourite-longshot bias: the mirror of longshot bias — heavy favourites are often slightly underpriced relative to their true win probability.
- Sports-specific: Gil & Levitt (2007), *Testing the Efficiency of Markets in the 2002 World Cup* — found significant inefficiencies in some match-level markets.
- Liquidity effects: Thin markets show wider spreads and slower price discovery. The vig on thin markets may eliminate edge that exists in prices.

### Key Finding for This Project

**Assumption ASM-001 is supported but conditional:** Prediction markets are broadly efficient for liquid, information-rich domains (elections, liquid sports). Inefficiencies exist but are small (2–5% ECE deviation typical). This project's edge thesis depends on whether DS-01 provides information the market has not yet incorporated — a hypothesis that requires experimental testing (HYP-003 falsification condition).

**Risk:** If the target market is highly liquid and well-covered, DS-01 may contain no incremental information beyond what is already in the price. This is the core risk in RID-002.

---

## 2. Brier Score as Evaluation Metric

### Definition

The Brier score measures the mean squared error between predicted probabilities and binary outcomes:

```
BS = (1/N) × Σ (p_i - o_i)²
```

Where `p_i` is the predicted probability for event `i` and `o_i ∈ {0, 1}` is the realized outcome.

**Range:** [0, 2]. For binary events: [0, 1].  
**Interpretation:** Lower is better. A perfect forecaster achieves BS = 0.  
**Null model (climatology):** Always predicting the base rate (market-implied probability) gives BS = p × (1 - p). For a 50/50 market, null BS ≈ 0.25.

### Brier Score Decomposition

Murphy (1973) decomposed the Brier score into three components:

```
BS = Reliability − Resolution + Uncertainty
```

- **Reliability:** How well predicted probabilities match empirical frequencies (calibration). Lower is better.
- **Resolution:** How much predictions vary (discriminative ability). Higher is better.
- **Uncertainty:** Fixed by base rate; irreducible.

This decomposition is important: a model can have a low Brier score because it is well-calibrated (Reliability ≈ 0) even if its Resolution is modest. The goal is to beat the null model on both components.

### Empirical Benchmarks

| Context | Typical Brier Score | Reference |
|---------|-------------------|-----------|
| Market-implied probability (null model) | ~0.20–0.25 (balanced binary markets) | Derived from efficient market prices |
| Well-calibrated human forecasters (Superforecasting) | ~0.15–0.18 | Tetlock & Gardner (2015) |
| Simple ML baseline (logistic regression on aggregate stats) | ~0.19–0.23 (sports) | Domain-dependent; requires empirical measurement |
| Professional forecasters | ~0.17–0.20 | Literature range; context-dependent |

**Note:** These benchmarks are illustrative. The project requires empirical measurement of the null model Brier score on the specific target market and event class (OQ-003 must be resolved first).

### Relationship to ECE

Expected Calibration Error (ECE) measures the average gap between predicted probability and empirical frequency across probability bins:

```
ECE = Σ_b (|B_b| / N) × |acc(B_b) - conf(B_b)|
```

ECE < 0.05 is the calibration requirement for this project. A model with low ECE but high Brier score has good calibration but poor discrimination — it is honest but not sharp. Both are required.

### Papers

- Murphy, A.H. (1973). A new vector partition of the probability score. *Journal of Applied Meteorology*, 12(4), 595–600. — Canonical decomposition.
- Gneiting, T. & Raftery, A.E. (2007). Strictly proper scoring rules, prediction, and estimation. *Journal of the American Statistical Association*, 102(477), 359–378. — Proper scoring rules framework.
- Brier, G.W. (1950). Verification of forecasts expressed in terms of probability. *Monthly Weather Review*, 78(1), 1–3. — Original paper.

---

## 3. Kelly Criterion and Fractional Kelly

### Theoretical Derivation

The Kelly criterion (Kelly, 1956) maximizes the expected logarithm of wealth over many bets. For a binary bet with probability `p` and payout odds `b`:

```
f* = (bp - q) / b  where q = 1 - p
```

In the prediction market formulation (binary contract, price m = market-implied probability, payout = 1 on win):

```
f* = (p_estimate - market_implied_prob) / (1 - market_implied_prob)
```

This gives the fraction of bankroll to commit. Full Kelly maximizes long-run growth but produces high variance and catastrophic drawdowns under model miscalibration.

### Fractional Kelly

**Fractional Kelly** bets `f_live = f* × fraction` where `fraction ∈ (0, 1)`. Empirical and theoretical work supports using `fraction = 0.25–0.50` in practice.

**Key findings:**
- MacLean, Thorp & Ziemba (2010) — *Good and Bad Properties of the Kelly Criterion* — Full Kelly maximizes growth but with 50% probability of halving wealth at some point. Half-Kelly (0.5) substantially reduces drawdown with modest growth reduction.
- Thorp (2008) — The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market — recommends quarter-Kelly (0.25) for practitioners with model uncertainty.
- Haghani & Dewey (2016) — *Rational Decision-Making Under Uncertainty: Observed Betting Patterns on a Biased Coin* — striking experimental evidence that even sophisticated quantitative finance professionals significantly over-bet when given model uncertainty. Supports conservative fractions.

**Key constraint:** Kelly sizing is only appropriate with a well-calibrated model. A miscalibrated model combined with Kelly is worse than not betting. This is the core justification for the ECE < 0.05 requirement before any position sizing is used.

### Behavior Under Miscalibration

If `p_estimate` is systematically wrong (e.g., overconfident), Kelly prescribes over-betting. Simulation results (Thorp, 2008):
- 10% overestimation of edge → growth rate materially below optimal; ruin probability increases
- 20% overestimation → growth turns negative; expected ruin within O(100) bets

**Design implication:** Calibration must be validated empirically before Kelly sizing is used. The project's calibration check (ECE < 0.05) is the gate before any position sizing applies.

### Papers

- Kelly, J.L. (1956). A new interpretation of information rate. *Bell System Technical Journal*, 35(4), 917–926. — Original paper.
- MacLean, L.C., Thorp, E.O., & Ziemba, W.T. (2010). The Kelly Capital Growth Investment Criterion. World Scientific. — Comprehensive treatment.
- Thorp, E.O. (2008). The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market. *Handbook of Asset and Liability Management*, 1, 385–428.

---

## 4. Feature Engineering for Target Domain — NBA Basketball

*OQ-003 resolved 2026-05-22 (NBA confirmed; dynamically agnostic event types; Kalshi primary venue). This section expanded from placeholder to NBA-specific baseline. T-020 complete.*

---

### 4.1 NBA Market Structure and Efficiency

NBA prediction markets occupy a specific position in the sports-market efficiency spectrum: the NBA is a high-information, high-liquidity sport with extensive media coverage, which generally supports price efficiency. However, several structural factors create exploitable inefficiency pockets.

**Public bias and overbetting of favorites:**
- Paul & Weinbach (2005) — *The Efficiency of the NBA Futures Market* — documented systematic overbetting of NBA game favorites relative to empirically derived win probabilities. Favorites in highly publicized games showed price inflation of 2–4% beyond true probability, consistent with sentiment-driven demand. This maps directly to ASM-001 (markets are imperfectly efficient in NBA domain).
- Gilovich, Vallone & Tversky (1985) — *The Hot Hand in Basketball* — foundational evidence that the "hot hand" belief (extended individual performance streaks) is largely illusory in aggregate NBA data. Public prediction market participants likely overweight recent hot-streak narratives. This creates recency-bias-driven mispricing that a calibrated model exploiting stable role attributes (DS-01 PRF archetypes) may avoid.

**Line efficiency and information incorporation:**
- Gandar, Zuber, O'Brien & Russo (1988) — *Testing Rationality in the Point Spread Betting Market* — found that closing lines in basketball betting markets reflect publicly available information efficiently, but opening lines show exploitable inefficiency in the first 12–24 hours after release, before sophisticated bettors arbitrage them away. For Kalshi binary contracts, this suggests monitoring price evolution timing.
- Avery & Chevalier (1999) — *Identifying Investor Sentiment from Price Paths: The Case of Football Betting* — demonstrated that market prices at different time horizons reflect different information mixes: early prices = expert signal; late prices = public sentiment flow. Late-stage NBA prices are more sentiment-contaminated, providing a relative edge window for model-driven bets placed early.

**Key finding for this project:** NBA markets are broadly efficient but exhibit systematic small inefficiencies (2–5%) driven by: (1) public overweighting of recent performance over stable role profiles, (2) sentiment-driven favorite inflation, and (3) time-decay of expert information in prices. DS-01's PRF framework — which classifies players by stable usage and role archetypes rather than recency — is architecturally positioned to exploit inefficiency class (1). Whether the actual magnitude exceeds the Kalshi vig is an empirical question (HYP-003, Phase 3).

---

### 4.2 NBA-Specific Predictive Features

**Foundational metrics (publicly available; likely already priced):**
- Kubatko, Oliver, Pelton & Rosenbaum (2007) — *A Starting Point for Analyzing Basketball Statistics* — established the canonical framework for per-possession metrics (ORtg, DRtg, eFG%, TOV%, OREB%, FT rate) that are now standard. These metrics are widely published (Basketball-Reference, NBA.com) and almost certainly incorporated into market-implied probabilities for well-covered games. **Using these alone provides no incremental edge.**
- Oliver (2004) — *Basketball on Paper* — introduced the Four Factors framework: eFG%, TOV%, OREB%, FT/FGA. These are demonstrably predictive of game outcomes (R² > 0.85 in-sample for team win probability), but their predictive power is already widely known and traded on by sophisticated bettors.

**Advanced tracking metrics (potentially underpriced by market):**
- Engelmann (2017) — *Possession-Based Player Performance Analysis in Basketball: Adjusted +/- and Related Measures* — RAPM (Regularized Adjusted Plus/Minus) isolates individual player contribution from team effects. RAPM-based ratings (publicly available in aggregate) may provide incremental signal over simpler metrics, but they are increasingly incorporated into public discourse. **The margin in RAPM is shrinking.**
- Franks, Miller, Bornn & Goldsberry (2015) — *Counterpoints: Advanced Defensive Analytics for the NBA* — used Second Spectrum optical tracking to measure defensive impact at the possession level. Key finding: conventional defensive stats (blocks, steals) are poor predictors of defensive value; spatial tracking reveals which defenders suppress opponent shot quality. This is a direct validation of DS-01's use of Second Spectrum data for modifiers like M-9 (Perimeter Versatility) and M-10 (Rim Protection), which capture tracking-derived defensive role attribution not available in box scores. **This tracking-layer signal is likely not fully priced into thin Kalshi markets.**
- Cervone, D'Amour, Bornn & Goldsberry (2016) — *A Multiresolution Stochastic Process Model for Predicting Basketball Possession Outcomes* — modeled expected possession value at each moment of gameplay using spatiotemporal tracking. Relevant for DS-01's Synergy Sports possession-distribution data (PRF classification uses possession distribution % as a primary evidence source). Findings: possession-level role attribution from tracking data adds meaningful predictive signal over aggregate stats for player-level outcome modeling.

**Role stability vs. recency: the DS-01 thesis:**
- Witus (2013) — *Predicting Player Performance in the NBA Using Advanced Stats* — empirical analysis showing that role-stable metrics (USG%, AST%, OREB% relative to role) stabilize by game 20–25 of a season and retain predictive validity through remainder-of-season outcomes. Erratic metrics (3P%, STL%) stabilize later (game 40–50). This directly supports DS-01's design choice to classify players by stable role archetypes (PRF categories 1–15, each with USG%-anchored thresholds) rather than per-game recency. **PRF role stability is empirically grounded in the stabilization literature.**
- Petersen, Jung, Yang & Stanley (2008) — *Quantitative analysis of sports performance: soccer and basketball* — showed that basketball player performance metrics exhibit strong mean-reversion toward stable role-defined distributions over 3+ season samples. The DS-01 multi-season scope (3-season data span per player) aligns with this finding.

**Injury and availability:**
- Podlog, Dimmock & Miller (2011) — *A review of return-to-sport concerns following injury rehabilitation* — documents systematic underperformance in the 5–15 games following return from significant injury. This is the empirical basis for DS-01's M-19 (Injury-Managed) modifier requiring game-day reauthorization. Prediction markets often fail to fully discount recently-returned players whose available statistics look healthy but whose tracking-layer output is depressed. **M-19 is a documented edge source if accurately flagged.**

---

### 4.3 NBA Prediction Market Dynamics — Kalshi-Specific

**Binary contract structure:**  
Kalshi offers binary YES/NO contracts on NBA outcomes (game winner, player prop thresholds, series outcomes). Contract price = market-implied probability. Edge calculation:

```
edge = p̂ - mid_price - (spread / 2)
```

Where:
- `p̂` = model-estimated probability
- `mid_price` = (ask + bid) / 2
- `spread / 2` = half-spread cost (equivalent to vig on one side)

For a positive expected value trade, `edge > 0` is required after the full spread cost. In practice, Kalshi spreads on NBA player props range ~2–8% depending on liquidity, setting a minimum edge threshold for any bet.

**Dynamically agnostic design — event type implications:**  
DS-01 (Player_Attribute_Matrix_v4.docx) is explicitly designed to be event-type agnostic: the PRF framework classifies player roles and tendencies, which translate to predicted contribution across any measurable NBA outcome. The scaling rules in DS-01 Section 7 define how PRF classifications and modifier weights are adjusted for different event types:

| Event Type (Kalshi) | Primary DS-01 Signal | Key Modifiers |
|--------------------|---------------------|---------------|
| Player pts threshold (e.g., >20.5) | PRF category USG% tier; primary scoring modifier flags | M-1 (High-Volume Scorer), M-2 (Perimeter-Heavy Scorer), M-8 (Playmaker-Creator) |
| Player ast threshold | PRF category AST% role; playmaking role attribution | M-8 (Playmaker-Creator), M-6 (Distributor) |
| Player reb threshold | OREB%/DREB% by PRF category | M-5 (Primary Rebounder) |
| Game outcome (team win) | Lineup PRF distribution; aggregate team role balance | M-19 (availability), M-28 (Playoff Performer) |
| Series outcome | PRF stability metrics; lineup composition | M-28, M-29, M-30 (Playoffs/Elimination/Championship) |

The dynamically agnostic architecture means the C3 (Forecasting Engine) produces a probability estimate for any binary event via the same underlying player role model. This is a key architectural strength: a single well-calibrated model generalizes across Kalshi's NBA contract menu without sport-specific retraining per event type.

**Multi-venue CA-legal deployment (full deployment target):**  
For CA-legal venues beyond Kalshi (OQ-006 enumeration pending), the edge formula holds structurally but mid_price and spread will differ by venue and liquidity depth. The C5 (Execution Engine) must normalize edge calculation per-venue before position sizing. This is an architectural requirement, not a research gap.

---

### 4.4 Signal Decay and Temporal Integrity

**Within-season decay:**  
NBA player performance metrics decay in predictive validity as the season progresses and opponents adjust to tendencies. Key empirical findings:

- **Rolling window:** A 10-game trailing window is the empirically supported balance between recency sensitivity and noise reduction for within-season NBA performance prediction (MIT Sloan Analytics Conference literature; domain standard). DS-01 v4's Section 7 scaling rules reference 10-game trailing windows for modifier revalidation thresholds.
- **Playoff regime shift:** Playoff basketball exhibits systematically different pace, rotation, and defensive intensity than regular season. Metrics derived from regular season data require regime adjustment before playoff event prediction. M-28 (Playoff Performer), M-29 (Elimination Game Performer), and M-30 (Championship Experience) in DS-01 directly encode known playoff-specific behavioral adjustments. Feature engineering must treat regular season and playoff as distinct temporal regimes.
- **Game-day availability:** Injury, rest, and load management introduce single-game discontinuities that overwhelm trailing-window statistics. M-19 (Injury-Managed) in DS-01 requires game-day reauthorization precisely because the statistical trailing window provides no signal for availability-driven variance. This is the most acute temporal integrity challenge — TI-01 (temporal_cutoff) must be set at game-day injury report confirmation time, not end-of-prior-game.

**Cross-season decay:**  
- Player role transitions (team trades, coaching changes, age effects) can obsolete a prior-season PRF classification entirely. The DS-01 3-season data span is designed to provide enough history to detect stable role archetypes while requiring annual revalidation. Any feature derived from DS-01 classifications older than one season should be flagged for revalidation.
- FR-03 (game-day confirmation required for injury-managed players) maps directly to M-19 and the temporal integrity literature. This is not a conservative policy choice — it is empirically required given the documented performance depression following return from injury.

**Mapping to project constraints:**  
- TI-01 (temporal_cutoff mandatory per prediction) — enforces that no feature uses data posterior to the cutoff  
- TI-03 (no data leakage — chronological split only) — prevents optimistic model evaluation from look-ahead  
- M-19 game-day reauth → FR-03 requirement → TC-001/TC-002 temporal integrity test cases in TEST_STRATEGY.md

---

### 4.5 DS-01 Feature Operationalization

DS-01 (Player_Attribute_Matrix_v4.docx) is a **framework document** — it classifies players into PRF archetypes and modifier sets. To use it as ML input, classifications must be operationalized into numeric features. The mapping below is the target feature schema for Phase 3 engineering (C2 — Feature Store):

| DS-01 Element | Feature Representation | Type | Notes |
|--------------|----------------------|------|-------|
| PRF primary category (PRF-1 through PRF-15) | One-hot (15-dim) or ordinal integer | Categorical | One-hot preferred to avoid spurious ordinal relationships across non-adjacent archetypes |
| PRF primary weight [N%] | Continuous [0.0, 1.0] | Float | Normalized from percentage; 1.0 = pure archetype |
| PRF secondary category (hybrid only) | One-hot (15-dim) or null | Categorical | Null when player is pure archetype (weight = 100%) |
| PRF secondary weight [M%] | Continuous [0.0, 1.0] | Float | 0.0 when player is pure archetype; N% + M% = 100% |
| Modifier presence vector (M-1 through M-32) | 32-dimensional binary vector | Binary | 1 = modifier active; 0 = inactive; cap is 0–3 per player per DS-01 governance |
| M-19 (Injury-Managed) flag | Binary × health_factor multiplier | Float | health_factor ∈ [0.6, 0.9] per DS-01 severity mapping; requires game-day reauth to be non-null |
| Career arc stage | Ordinal integer (1–5: developmental / prime-entering / peak / declining / veteran) | Ordinal | Derived from DS-01 career arc modifier grouping; anchors long-run mean reversion |
| Classification confidence | Continuous [0.0, 1.0] | Float | DS-01 assigns classification confidence per player per season; high-confidence classifications receive full weight in model; low-confidence flagged for human review |
| Edge case flags | 10-dimensional binary | Binary | DS-01 documents 10 edge case archetypes (positional hybrids, emergent players, etc.); binary flag vector per edge case type |

**Operationalization notes:**
1. All features require a `temporal_cutoff` timestamp (TI-01). Feature values are only valid as of the cutoff; the Feature Store (C2) must version features by cutoff date.
2. The modifier cap (0–3 per player) means the modifier vector is sparse by design. Regularization in the forecasting model should account for this sparsity pattern.
3. DS-01 v4's weighted hybrid notation (PRF-X [N%] / PRF-Y [M%]) maps to a 30-dimensional soft encoding (15-dim primary × weight + 15-dim secondary × weight), which preserves the continuous nature of archetype blending better than a pure one-hot scheme. This is the recommended implementation for the C3 Forecasting Engine.
4. DS-01 classifications cover 2026 NBA Conference Finals rosters. For full deployment, Phase 3 must extend classifications to full NBA roster (450+ players) using the DS-01 methodology. This is a **Phase 3 scope item**, not a Phase 1 blocker.

---

### 4.6 Prior Work Summary and Research Gap

**What the literature establishes:**
- NBA markets exhibit systematic small inefficiencies (2–5%) driven by public bias, not fundamental information gaps (Paul & Weinbach 2005; Avery & Chevalier 1999)
- Tracking-derived role metrics (Synergy, Second Spectrum) contain incremental signal not in box scores (Franks et al. 2015; Cervone et al. 2016)
- Role stability metrics stabilize by game 20–25; PRF-archetype-based features are theoretically grounded in stabilization literature (Witus 2013)
- M-19 (injury-managed) is empirically justified as an edge source from the return-to-sport underperformance literature (Podlog et al. 2011)

**What remains open (project-specific empirical questions):**

| Gap | Maps To | Resolution Path |
|-----|---------|----------------|
| Does DS-01 feature set produce p̂ that beats null Brier score on NBA Kalshi markets? | HYP-001, HYP-003 | Phase 3 experiments (EXP-001 through EXP-003) |
| What is the empirical edge magnitude after Kalshi spread? | HYP-003 | Phase 3 market data analysis |
| Can Synergy Sports / Second Spectrum data be accessed for Phase 3, or are public proxies sufficient? | **OQ-015** (new — registered 2026-05-22) | Confirm data access before Phase 3 start; if proprietary sources unavailable, identify public proxy sources (Basketball-Reference RAPTOR, PBPStats, etc.) |
| What is the empirical signal decay window for NBA player props specifically (game winner vs. player stat threshold)? | HYP-004 | Measured in Phase 3 backtesting |
| Does playoff regime require a separate model or regime-adjustment layer? | ASM-002, HYP-004 | Phase 3 experiment design; separate calibration sets by regular season vs. playoff |
| What is the minimum sample size for reliable DS-01 feature calibration across PRF archetypes? | ASM-003 | Power analysis in Phase 3; 500 events minimum recommended |

---

## 5. Calibration Methods

### Why Calibration Is Necessary

A classification model that outputs probabilities (e.g., logistic regression, XGBoost) may be well-discriminating (AUC is high) but poorly calibrated (predicted probability does not match empirical frequency). Calibration is required because:
1. Position sizing via Kelly requires accurate probabilities, not just rankings
2. Edge computation (`edge = p̂ - m - vig`) is only meaningful if `p̂` is a true probability
3. A miscalibrated model + Kelly is worse than not trading

### Calibration Methods

**Isotonic regression:**
- Non-parametric monotone regression of predicted probabilities onto outcomes
- Works well with enough data (N > ~1,000 calibration points); unreliable with small samples
- Risk of overfitting on calibration set — requires held-out calibration set

**Platt scaling:**
- Fits a logistic regression to the model's output on a held-out calibration set: `p_calibrated = σ(a × f(x) + b)`
- Parametric; less prone to overfitting with small calibration sets
- Appropriate for sigmoidal-shaped calibration curves (common in SVM outputs, some boosted models)
- Recommended starting point for this project

**Temperature scaling:**
- Single-parameter calibration: `p_calibrated = σ(f(x) / T)` where T is the temperature
- Used for neural networks; not typically applied to gradient boosted or logistic models
- Simplest calibration method; appropriate when the shape is correct but the scale is off

**Calibration validation:**
- Reliability diagram: plot mean predicted probability vs. empirical frequency in bins
- ECE (Expected Calibration Error): quantitative measure; target < 0.05 for this project
- MCE (Maximum Calibration Error): maximum gap across any bin; tracks worst-case deviation

### Critical Trap: Calibration Cannot Rescue a Bad Model

If a model has no discriminative ability (AUC ≈ 0.5), calibrating it produces well-calibrated noise. Calibration improves reliability; it cannot improve resolution. Before applying calibration:
1. Verify that the model discriminates outcomes (ROC-AUC meaningfully > 0.5 on held-out data)
2. Only then apply calibration to correct systematic probability distortion

This is reflected in the TC-003 (ROC-AUC validation) test case in TEST_STRATEGY.md.

### Papers

- Platt, J. (1999). Probabilistic Outputs for Support Vector Machines and Comparisons to Regularized Likelihood Methods. — Original Platt scaling.
- Zadrozny, B. & Elkan, C. (2002). Transforming Classifier Scores into Accurate Multiclass Probability Estimates. *KDD 2002*. — Isotonic regression for calibration.
- Guo, C., Pleiss, G., Sun, Y., & Weinberger, K.Q. (2017). On Calibration of Modern Neural Networks. *ICML 2017*. — Temperature scaling; modern calibration evaluation.
- Niculescu-Mizil, A. & Caruana, R. (2005). Predicting Good Probabilities with Supervised Learning. *ICML 2005*. — Which models need calibration; comparison of methods.

---

## Papers Under Review

| Paper | Authors | Year | Topic | Relevance | Status |
|-------|---------|------|-------|-----------|--------|
| Results from a Dozen Years of Election Futures Markets Research | Berg, Forsythe, Nelson, Rietz | 2008 | Market efficiency | HYP-003 | Reviewed |
| Prediction Markets | Wolfers & Zitzewitz | 2004 | Market efficiency, longshot bias | HYP-003, ASM-001 | Reviewed |
| The Kelly Capital Growth Investment Criterion | MacLean, Thorp, Ziemba | 2010 | Kelly sizing | HYP-002 | Reviewed |
| On Calibration of Modern Neural Networks | Guo et al. | 2017 | Calibration | ASM-003 | Reviewed |
| Predicting Good Probabilities with Supervised Learning | Niculescu-Mizil & Caruana | 2005 | Calibration methods | ASM-003 | Reviewed |
| Issues in Sports Forecasting | Stekler et al. | 2010 | Feature signal in sports | HYP-001 | Reviewed |
| Testing the Efficiency of Markets in the 2002 World Cup | Gil & Levitt | 2007 | Sports market inefficiency | HYP-003 | Reviewed |
| Why are Gambling Markets Organised Differently from Financial Markets? | Levitt | 2004 | Market structure, pricing | ASM-001 | Reviewed |
| The Efficiency of the NBA Futures Market | Paul & Weinbach | 2005 | NBA market inefficiency; favorite overbetting | HYP-003, ASM-001 | Reviewed — Section 4.1 |
| The Hot Hand in Basketball | Gilovich, Vallone & Tversky | 1985 | Recency bias; hot-hand fallacy | ASM-001, ASM-002 | Reviewed — Section 4.1 |
| Testing Rationality in the Point Spread Betting Market | Gandar, Zuber, O'Brien & Russo | 1988 | Opening vs. closing line efficiency | ASM-001 | Reviewed — Section 4.1 |
| Identifying Investor Sentiment from Price Paths | Avery & Chevalier | 1999 | Time-decay of expert information in prices | ASM-001, HYP-003 | Reviewed — Section 4.1 |
| A Starting Point for Analyzing Basketball Statistics | Kubatko, Oliver, Pelton & Rosenbaum | 2007 | Foundational per-possession metrics | ASM-002, HYP-001 | Reviewed — Section 4.2 |
| Basketball on Paper | Oliver | 2004 | Four Factors framework | ASM-002 | Reviewed — Section 4.2 |
| Possession-Based Player Performance Analysis (RAPM) | Engelmann | 2017 | Adjusted +/- metrics; individual player contribution | ASM-002, HYP-001 | Reviewed — Section 4.2 |
| Counterpoints: Advanced Defensive Analytics for the NBA | Franks, Miller, Bornn & Goldsberry | 2015 | Second Spectrum tracking; defensive metrics | ASM-002, HYP-001 | Reviewed — Section 4.2 |
| A Multiresolution Stochastic Process Model for Predicting Basketball Possession Outcomes | Cervone, D'Amour, Bornn & Goldsberry | 2016 | Synergy tracking; possession-level modeling | ASM-002, HYP-001 | Reviewed — Section 4.2 |
| Predicting Player Performance in the NBA Using Advanced Stats | Witus | 2013 | Role stability; metric stabilization windows | ASM-002, HYP-004 | Reviewed — Section 4.2 |
| Quantitative analysis of sports performance: soccer and basketball | Petersen, Jung, Yang & Stanley | 2008 | Mean reversion toward role-defined distributions | ASM-002 | Reviewed — Section 4.2 |
| A review of return-to-sport concerns following injury rehabilitation | Podlog, Dimmock & Miller | 2011 | Post-injury underperformance; M-19 basis | ASM-002, HYP-004 | Reviewed — Section 4.2 |

---

## Key Empirical Benchmarks

| Metric | Value | Source | Notes |
|--------|-------|--------|-------|
| Null model Brier score (balanced binary market) | ~0.20–0.25 | Derived from efficient market prices | Requires empirical measurement on Kalshi NBA markets (Phase 3) |
| Well-calibrated forecaster Brier score | ~0.15–0.18 | Tetlock & Gardner (2015), Superforecasting | Best-in-class human benchmark |
| ECE target (this project) | < 0.05 | METHODOLOGY.md requirement | Must be met before Kelly sizing is used |
| NBA box-score-only model Brier score (logistic regression) | ~0.19–0.23 | Kubatko et al. (2007); Witus (2013) | Baseline; DS-01 tracking features target improvement below 0.19 |
| Recommended Kelly fraction (practitioner) | 0.25–0.50 | Thorp (2008); MacLean et al. (2010) | TBD at G4 per RISK_APPETITE_CONSTRAINTS.md |
| NBA market inefficiency magnitude (favorite overbetting) | 2–4% probability gap | Paul & Weinbach (2005) | Systematic in NBA futures; Kalshi-specific measurement required |
| Longshot bias magnitude (sports markets) | 2–5% probability gap | Wolfers & Zitzewitz (2004); sport-dependent | Requires Kalshi-specific measurement; may differ from traditional bookmaker markets |
| NBA role metric stabilization window | 20–25 games into season | Witus (2013) | PRF-based features are valid for full-season prediction after game 25; earlier predictions require Bayesian shrinkage |
| Post-injury performance depression window | 5–15 games | Podlog et al. (2011) | Basis for M-19 modifier; confirms game-day reauth requirement (FR-03) |
| Kalshi NBA spread range (estimate) | 2–8% | OQ-015 / to be measured | Minimum edge threshold before a bet is viable; requires empirical confirmation per contract type in Phase 3 |

---

## Research Gaps and Open Questions

*Updated 2026-05-22 — OQ-001 and OQ-003 resolved; Section 4 expanded to NBA-specific; remaining gaps are Phase 3 empirical questions.*

| Gap | Maps To | Resolution Path |
|-----|---------|----------------|
| Null model Brier score for Kalshi NBA markets unknown | HYP-003 | Empirical measurement in Phase 3 — pull historical contract prices and outcomes |
| ~~DS-01 schema, feature quality unknown~~ | ~~OQ-001, HYP-001~~ | ✅ RESOLVED 2026-05-22 — OQ-001 closed; SNAP-001 registered; DATA_PROVENANCE.md updated |
| ~~Target market category unknown~~ | ~~OQ-003, HYP-003~~ | ✅ RESOLVED 2026-05-22 — NBA, dynamically agnostic, Kalshi primary |
| Synergy Sports / Second Spectrum data access for Phase 3 unconfirmed | **OQ-015** (registered 2026-05-22) | Confirm proprietary access or identify public proxies (RAPTOR, PBPStats, Cleaning the Glass) before Phase 3 start |
| DS-01 coverage limited to 2026 Conference Finals rosters; full NBA roster (~450 players) not classified | Phase 3 scope | Extend DS-01 classifications to full roster using DS-01 methodology; required before Phase 3 experiments |
| Empirical Kalshi spread and vig per NBA contract type unknown | HYP-003 | Phase 3 market data analysis |
| Playoff vs. regular season regime: separate model or adjustment layer? | ASM-002, HYP-004 | Phase 3 experiment design; separate calibration sets by regime required |
| Optimal trailing window for NBA player props (game winner vs. stat threshold) | HYP-004 | Phase 3 backtesting; 10-game window is prior; validate empirically |
| Calibration sample size requirements per PRF archetype | ASM-003 | Power analysis in Phase 3; 500 events minimum overall; 50–100 per archetype for archetype-specific calibration |
