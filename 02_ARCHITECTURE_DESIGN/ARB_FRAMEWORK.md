# Arbitrage Framework — Venue-Agnostic Execution with Time-Horizon Segmentation

**Purpose:** Centralized design reference for all arbitrage strategies (C: Complement Lock, D: Statistical Arb, E: Line Shopping). Defines the venue-agnostic data model, band-specific decision trees, and opportunity lifecycle. All arb strategy implementations derive from this framework.
**Owner (role):** Architecture Owner (AO)
**Status:** CANONICAL (2026-05-29)
**Last reviewed:** 2026-05-29 (initial build — Phase 6 idle period)
**Next review:** On any new venue activation; on Phase 7 arb activation; on T4/T5 infrastructure scope
**Staleness triggers:** New venue added to VENUE_REGISTRY.md; arb strategy activated; execution SLA changed; Kelly fraction revised
**Upstream links:** EXECUTION_BANDS.md (band definitions); STRATEGY_OVERVIEW.md (C/D/E mechanics); VENUE_REGISTRY.md (VenueParams source)
**Downstream links:** venue_router.py; arb_scanner.py (to be built); arb_opportunity_log.py (to be built); PIPELINES_JOBS.md
**Decision references:** ADR-0002 (forecast-only — arb is Type 2, not Type 1); ADR-0003 (Kalshi primary; Polymarket secondary); EXECUTION_BANDS.md (band definitions)
**Confidence:** 8/10 — Framework design is sound; T3/T4 arb execution requires write-capable C5 (Phase 7+)
**Decisions logged:** true — Key design decisions captured in DECISION_LOG.md (2026-05-29 initial build; see entries for framework adoption, venue-agnostic model, and band-specific decision tree depth rules)

---

## 1. Core Design Principle (HRT/Jane Street Analogy)

From EXECUTION_BANDS.md:

> **At the lowest latency, execution quality IS the edge. Model complexity is inversely proportional to time horizon because computation time eats into the edge window.**

For arbitrage specifically, this principle is more acute than for model-edge strategies. A complement lock window can close in under 1 second. A line shopping divergence can compress in seconds. Statistical arb spreads can widen before you fill both legs. The cost of latency is not missing a better entry price — it is **missing the opportunity entirely.**

**The arb decision tree rule:**

| Compute budget | Max tree depth | Primary operation | Analogy |
|---------------|---------------|------------------|---------|
| T1: 30,000ms | Unlimited | Full scan, rank, pre-populate | Research analyst |
| T2: 5,000ms | 10–20 ops | Re-validate, refresh live prices | Trading desk manager |
| T3: 500ms | 3–5 ops | Verify pre-computed + one API call | Floor trader |
| T4: 50ms | 1–2 ops | Lookup table only; pre-computed flag | Market maker (no analysis) |
| T5: 5ms | 1 op | Arithmetic comparison only | Automated trigger |

**The arb inversion:** For model-edge strategies (A), all bands run the same direction — T1 is the primary strategy, T3/T4 are supplements. For arb strategies, **T1 is preparation and T3/T4 are execution.** The expensive computation happens early (T1 scan builds the opportunity table); the execution at T3/T4 is pure lookup + fire.

---

## 2. Critical Distinction — Detection Band vs. Execution Band

The band at which an opportunity is **detected** is not the band at which it is **executed**.

| Strategy | Detection band | Execution band | Why |
|----------|---------------|---------------|-----|
| C (Complement Lock) | T1/T2 (scan builds table) | T3/T4 (verify and fire when live) | Lock windows are seconds; must pre-compute |
| D (Statistical Arb) | T1 (OU estimation) | T1/T2 (spread mean-reverts over hours) | OU reversion is slow; execution is deliberate |
| E (Line Shopping) | T1/T2 (venue comparison cached) | T1–T3 (route at time of bet placement) | Divergence can persist minutes to hours |

This distinction is architecturally load-bearing. The pre-computation at detection time (T1/T2) is what makes T3/T4 execution possible within the compute budget. **Without a pre-populated opportunity table, no arb strategy can meet T3/T4 SLAs.**

---

## 3. Venue-Agnostic Data Model

### 3.1 VenueParams

Every venue participating in arb calculations must register a `VenueParams` entry. The arb math uses these values as inputs — no venue-specific constants are hardcoded in the strategy logic.

```python
@dataclass
class VenueParams:
    venue_id: str              # V-001 (Kalshi), V-002 (Polymarket), V-003 (PrizePicks), etc.
    contract_type: str         # 'binary_market' | 'bookmaker_fixed'
    fee_rate: float            # fraction of notional (0.030 for Kalshi per EXP-010)
    min_tick: float            # minimum price increment (0.01 for binary markets)
    min_order_size_usd: float  # minimum bet size
    max_order_size_usd: float  # per-order limit (venue-imposed)
    execution_latency_ms: int  # estimated round-trip API response time
    fill_model: str            # 'instantaneous' | 'probabilistic' (does fill guarantee?)
    implied_prob_method: str   # 'market' (dynamic) | 'bookmaker' (static 0.50)
    liquidity_tier: str        # 'low' | 'medium' | 'high' — affects fill probability model
    simultaneous_legs: bool    # True if venue supports atomic multi-leg orders
    api_rate_limit_per_min: int
```

**Registered venues (from VENUE_REGISTRY.md):**

**⚠️ Corrected 2026-07-06 (GG-074 remediation) — the Kalshi `fee_rate: 0.030` flat constant below (sourced "per EXP-010," 2026-05-29 or earlier) was superseded by ADR-0016 (2026-06-04, GG-009 resolution), which is the fee model actually implemented in production (`run_paper_trade.py`, `run_mlb_paper_trade.py`, `run_t4_mlb_live.py`, `paper_trader.py`, etc.): `kalshi_fee = 0.07 × mid × (1 − mid)`, not a flat 3% of notional. This is not a rounding difference — at mid=0.44/0.52 (the section 5.2 worked example below), the real ADR-0016 fee is ~$0.0172–0.0175 per contract vs. the ~$0.0132–0.0104 this table's flat rate implies, meaning this framework's arb profit math currently understates true Kalshi fees across most of the price range. This section and the worked example in §5.2 have not been updated to the ADR-0016 formula since arb strategies (Phase 7+) are not yet built — flagging for whoever picks up the Phase 7 `ArbOpportunityLog`/`ComplementLockScanner` build to use the correct fee formula, not this table's flat constant.**

| venue_id | contract_type | fee_rate | implied_prob_method | simultaneous_legs | Phase |
|----------|--------------|----------|--------------------|--------------------|-------|
| V-001 (Kalshi) | binary_market | 0.030 (stale — see correction above; real formula is `0.07 × p × (1-p)` per ADR-0016) | market | False | ✅ Active |
| V-002 (Polymarket US) | binary_market | ~0.020 est. | market | TBD | Phase 7 |
| V-003 (PrizePicks) | bookmaker_fixed | embedded | bookmaker | N/A (single pick) | Phase 7+ ADR |
| V-004 (Underdog) | bookmaker_fixed | embedded | bookmaker | N/A | Phase 7+ ADR |
| V-005 (Sleeper) | bookmaker_fixed | embedded | bookmaker | N/A | Phase 7+ ADR |

### 3.2 ArbLeg

A single side of an arbitrage trade. One opportunity contains 1–N legs.

```python
@dataclass
class ArbLeg:
    leg_id: str
    venue_id: str          # which venue
    market_id: str         # venue's market identifier
    direction: str         # 'YES' | 'NO' | 'OVER' | 'UNDER'
    ask_price: float       # price at detection time
    size_usd: float        # intended position size
    fee_usd: float         # fee_rate × size_usd
    net_cost: float        # ask_price × size_usd + fee_usd
    fill_probability: float  # estimated probability this leg fills at ask_price
    venue_params: VenueParams
```

### 3.3 ArbOpportunity

The centralized record for a detected arb opportunity. Venue-agnostic — the same schema handles Kalshi-only, cross-venue, or future DFS opportunities.

```python
@dataclass
class ArbOpportunity:
    opportunity_id: str        # UUID — generated at detection
    strategy: str              # 'C_complement_lock' | 'D_stat_arb' | 'E_line_shop'
    detection_band: str        # 'T1' | 'T2' | 'T3'
    execution_band: str        # 'T1' | 'T2' | 'T3' | 'T4'
    legs: List[ArbLeg]
    gross_profit_usd: float    # sum(leg settlements) - sum(leg costs), pre-fee
    net_profit_usd: float      # gross_profit - sum(leg.fee_usd)
    net_profit_pct: float      # net_profit / total_capital_required
    fill_probability: float    # joint probability all legs fill (product if independent)
    ev_usd: float              # net_profit_usd × fill_probability
    decision_tree_depth: int   # number of ops used to produce this record
    detected_at: datetime
    expires_at: datetime       # when opportunity window closes (strategy-specific)
    status: str                # 'detected'|'validated'|'queued'|'executed'|'expired'|'failed'
    execution_notes: str       # fill prices, rejection reason, etc.
```

### 3.4 ArbOpportunityLog

The centralized persistent store for all detected opportunities. Written at detection time; updated at execution time.

```
src/prediction_market_bot/c5_execution/arb_opportunity_log.py   (to build)
logs/arb_opportunities/YYYYMMDD_arb_log.jsonl                  (runtime output)
```

All strategies write to the same log via a shared `ArbOpportunityLog.record()` method. This provides:
- Unified P&L tracking across strategy types and venues
- Opportunity frequency analysis (how often does each type appear?)
- Fill rate monitoring (how often do we successfully execute?)
- Decay analysis (how fast do opportunity windows close?)

---

## 4. Band-Specific Decision Trees by Strategy

### 4.1 Strategy C — Complement Lock Arbitrage

**Core condition:** `ask_YES + ask_NO < 1.00 - (2 × fee_rate)`  
(Venue-agnostic form: uses `VenueParams.fee_rate`; works for any binary market venue)

**Net profit formula:**
```
gross_profit = 1.00 - ask_YES - ask_NO
net_profit   = gross_profit - (ask_YES × fee_rate_YES_venue) - (ask_NO × fee_rate_NO_venue)

Cross-venue form (YES on Kalshi, NO on Polymarket):
net_profit = 1.00 - ask_YES_V001 - ask_NO_V002
             - (ask_YES × 0.030) - (ask_NO × est_V002_fee)
```

**Decision tree by band:**

| Band | Compute budget | Operations | Description |
|------|---------------|------------|-------------|
| **T1** | 30,000ms | Full scan | `scan_all_markets()` → for each market: compute net_profit → filter(net_profit > 0) → rank → write to opportunity table. Also: cross-venue scan if multiple venues active. Pre-populate T3/T4 lookup table with {market_id: lock_condition}. |
| **T2** | 5,000ms | Refresh known opportunities | Read T1 opportunity table → fetch current ask prices for top-N candidates → recompute net_profit → update table. Prune expired or closed windows. |
| **T3** | 500ms | Verify + fire | Read lookup table → fetch_current_ask(market_id) [1 API call] → compute_net_profit() [1 arithmetic op] → if valid: submit_order(leg_YES) → submit_order(leg_NO). Total: 4–5 ops. |
| **T4** | 50ms | Lookup only | lookup_table[market_id] → boolean. If True: fire pre-computed orders. No API calls during execution window. Orders pre-staged at T3. Total: 1–2 ops. |
| **T5** | N/A | Not applicable | Near-deterministic settlement means complement lock payoff is known — no arb opportunity exists. |

**T4 pre-staging requirement:** For T4 execution, complement lock orders must be staged at T3 (orders built, not submitted). At T4 trigger, the staged orders are submitted with zero additional computation. This requires atomic or near-atomic order submission — only viable when `VenueParams.simultaneous_legs = True` or when execution latency is provably low enough to submit sequential legs within the window.

**Fill risk (execution risk):** The primary failure mode is second-leg fill at a worse price. Mitigation:
```
fill_probability_joint = fill_probability_leg1 × fill_probability_leg2
EV = net_profit × fill_probability_joint - |second_leg_slippage| × (1 - fill_probability_leg2)
```
Only execute if `EV > 0` after slippage adjustment.

---

### 4.2 Strategy D — Statistical Arbitrage (OU Mean Reversion)

**Core condition:** Spread between correlated market prices deviates > 2σ from historical mean.

**OU spread formula (venue-agnostic):**
```
spread_t = price_A_t - price_B_t          [from any two venues/markets]
z_score  = (spread_t - μ_spread) / σ_spread

Entry (long spread): z_score < -2.0
Entry (short spread): z_score > +2.0
Exit: |z_score| < 0.5
```

**Decision tree by band:**

| Band | Compute budget | Operations | Description |
|------|---------------|------------|-------------|
| **T1** | 30,000ms | Full OU estimation | Load historical price series → compute μ_spread, σ_spread, κ (reversion speed) per pair → compute current z_scores → rank pairs by deviation → write to opportunity table with OU parameters. Full covariance matrix update across all active pairs. |
| **T2** | 5,000ms | z-score update | Read cached OU params from T1 → fetch current prices for active pairs [N API calls] → recompute z_scores → update opportunity table. No OU re-estimation. |
| **T3** | 500ms | Check + fire | Read cached z_score → verify still in entry zone (1 price fetch per leg) → if valid: submit orders. OU params not recomputed at T3. |
| **T4/T5** | Not applicable | — | OU mean reversion requires time to materialize (hours, not seconds). In-play execution of stat arb is not viable — the reversion horizon is longer than the game window. |

**Pair selection:** Correlated pairs must be pre-registered in the opportunity table at T1. Valid pairs:
- Same team, same game (positive correlation — shared offensive load)
- Opposing players with negatively correlated usage in close games
- Cross-venue: same market on Kalshi vs. Polymarket (price should converge)

**OU parameter stability:** κ (reversion speed) and σ (spread volatility) must be estimated on ≥2 seasons of price history per pair. For cross-venue pairs, price history requires DS-02 (historical Polymarket prices) — currently unavailable. Single-venue stat arb is therefore the Phase 7 scope; cross-venue OU requires Phase 8+.

---

### 4.3 Strategy E — Line Shopping (Best Execution Routing)

**Core condition:** For a planned bet, identify the venue offering the lowest ask price for the desired direction.

**Edge formula (venue-agnostic):**
```
For binary_market venues:     edge_improvement = ask_best - ask_current_venue
For bookmaker_fixed venues:   edge_improvement = 0.50 - ask_bookmaker_line
                              [bookmaker targets 50/50 → edge is model probability minus 0.50]

Best execution:               route to venue with min(ask_price) for direction
```

**Decision tree by band:**

| Band | Compute budget | Operations | Description |
|------|---------------|------------|-------------|
| **T1** | 30,000ms | Full venue comparison | Query all registered venues → normalize prices (binary vs. bookmaker_fixed) → rank by ask_price per market → cache routing table {market_id: best_venue_id}. Compute edge_improvement per venue pair. Update line_shop_log with historical divergence data. |
| **T2** | 5,000ms | Cache refresh with injury adjustment | Re-query active venues → apply injury/lineup adjustment factor to cached routing table → update routing table. Injury news changes implied probabilities and therefore line shopping decisions. |
| **T3** | 500ms | Fast re-route | Query registered venues [N API calls, N = venue count] → normalize → compare → route. No caching — live price at time of execution. Must complete within 300s SLA (T3 window). |
| **T4** | 50ms | Pre-cached routing | Lookup routing_table[market_id] → route to pre-cached best venue. No API calls. Pre-fetch required at T3. |
| **T5** | 5ms | Same as T4 | Routing table lookup only. |

**Normalization — the venue comparison problem:**

```python
def normalize_ask(venue_params: VenueParams, raw_ask: float, direction: str) -> float:
    """Normalize venue-specific ask price to a comparable probability-equivalent."""
    if venue_params.contract_type == 'binary_market':
        # Both YES and NO sides are probabilities; direct comparison valid
        return raw_ask  # already in [0,1]
    elif venue_params.contract_type == 'bookmaker_fixed':
        # Bookmaker targets 0.50 for both sides; ask IS the effective cost
        return raw_ask  # 0.50 is the implied probability baseline
    # Future: handle spread/OU contracts when added
```

**Line shopping specifically benefits from venue competition:** DFS pick'em venues (V-003/V-004/V-005) use bookmaker-set lines targeting 0.50. When our model p̂ > 0.55, the effective edge against bookmaker venues is `p̂ - 0.50` — typically much larger than the `p̂ - mid_price` edge on Kalshi where market participants continuously reprice. This is why Strategy E creates the most value when bookmaker venues are active (Phase 7+), not just binary market venues.

---

## 5. Multi-Strategy Interaction in Arb Context

### 5.1 Bankroll competition

When C, D, and E are all active simultaneously, they compete for bankroll. Each strategy produces an `ArbOpportunity.ev_usd`. The multi-strategy Kelly allocation must account for covariance:

```
If C and E fire on the same market simultaneously:
  → C is buying YES+NO (zero net directional exposure)
  → E is routing the same bet to a better venue (directional)
  → No bankroll conflict — they are independent operations

If D fires on pair (A, B) and E also fires on market A:
  → D requires exposure to A; E affects the venue and price of A
  → E should always precede D: line shop first, then execute stat arb at the best venue
```

**Execution precedence rule:** E (line shopping) is a **routing decision** that applies before any directional bet is placed. C (complement lock) is **venue-agnostic** (both legs must fill). D (stat arb) uses E's output as its execution venue.

Order of operations: `E.route() → C.check_lock() → D.execute(via best_venue)`

### 5.2 C + E combination (cross-venue lock)

The highest-value complement lock scenario combines C and E:
```
Kalshi ask_YES = 0.44  (buy YES on V-001)
Polymarket ask_NO = 0.52  (buy NO on V-002)
Total = 0.96 → gross profit = 0.04

net_profit = 0.04 - (0.44 × 0.030) - (0.52 × 0.020)
           = 0.04 - 0.0132 - 0.0104
           = 0.0164 per $1 invested

This is why Strategy C's Phase 7 viability improves dramatically when V-002 (Polymarket) is active.
```

Cross-venue lock requires both venues to be live and write-capable. This is the primary motivation for accelerating Polymarket provisioning (T-077).

---

## 6. Opportunity Lifecycle

```
T1 SCAN ──→ [Detected] ──→ T2 REFRESH ──→ [Validated] ──→ T3 VERIFY ──→ [Queued]
                                                                          ↓
                                                                    T3/T4 FIRE
                                                                          ↓
                                                                [Executed] or [Failed]
                                                                          ↓
                                                             ArbOpportunityLog.record()
```

State transitions:
- **detected → validated:** Net profit confirmed positive after fee adjustment
- **validated → queued:** Orders pre-staged at T3 (for T4 execution)
- **queued → executed:** Both legs fill at or near expected price
- **queued → failed:** Second leg fills at worse price (fill_probability_joint realized as 0); or API error; or opportunity closed before execution
- **any → expired:** `opportunity.expires_at` passes without execution

---

## 7. Configuration — Centralized Arb Parameters

These are the tunable thresholds for the arb framework. All are governance-controlled — changes require DECISION_LOG.md entry and owner sign-off.

| Parameter | Default | Strategy | Rationale |
|-----------|---------|----------|-----------|
| `min_net_profit_usd` | $0.005 | C | Minimum lock profit after fees; below this, execution risk eats the edge |
| `min_net_profit_pct` | 0.5% | C | As a fraction of capital deployed |
| `min_fill_probability` | 0.85 | C | Joint probability both legs fill at stated price |
| `min_z_score_entry` | 2.0 | D | OU entry threshold |
| `min_z_score_exit` | 0.5 | D | OU exit threshold (mean reversion achieved) |
| `min_ou_history_seasons` | 2 | D | Minimum seasons for OU parameter estimation |
| `min_line_shop_saving_cents` | 1.0 | E | Minimum saving per contract to justify multi-venue routing overhead |
| `max_arb_position_pct_bankroll` | 0.10 | C/D/E | Hard cap per arb opportunity (10% of bankroll) |
| `opportunity_table_max_age_min` | 30 | C/E | Stale opportunity table entries are pruned after 30 min |

**Owner:** DS + RCO. Any change to these thresholds requires a DECISION_LOG.md entry with rationale.

---

## 8. Activation Gates by Band and Strategy

| Strategy | Band | Phase | Gate | Blocking dependencies |
|----------|------|-------|------|----------------------|
| E | T1 | 7 | ADR-0003 + Polymarket key (T-077) | VenueRouter multi-venue; V-002 API |
| E | T2 | 7 | Same as T1 + DS-04 injury data | Injury adjustment factor |
| E | T3 | 7 | Same as T1 | None additional |
| E | T4 | 8 | T4 infrastructure | Real-time C5 rebuild |
| C | T1/T2 scan | 7 | APR-0010 (DS sign-off) | Governance approval |
| C | T3 execute | 7 | APR-0010 + write-capable C5 | C5 write key (ACC-0002 upgrade) |
| C | T4 execute | 8 | T4 infrastructure | Same as E T4 |
| D | T1/T2 | 8 | New ADR + DS-02 price history | ≥2 seasons price data per pair |
| D | T3 | 8 | Same as T1/T2 | DS-02 must be live |

---

## 9. Implementation Roadmap

**Phase 7 (immediate post-G6):**
1. Build `ArbOpportunityLog` — centralized record with VenueParams injection
2. Build `ComplementLockScanner` — T1 scan + T3 verify/fire loop
3. Build `LineShoppingRouter` — extend VenueRouter with routing table + cache
4. Activate E at T1 once T-077 (Polymarket API) is complete
5. APR-0010 decision by DS on complement lock activation (C)

**Phase 8:**
1. Build `StatArbScanner` — OU parameter estimation on ≥2 seasons price data
2. Extend C and E to T4/T5 with pre-staged order tables
3. Cross-venue complement lock (C + E combined) once V-002 is write-capable

**Phase 9+:**
- Full covariance Kelly across simultaneous C/D/E positions
- Real-time opportunity decay monitoring
- Automated threshold recalibration from ArbOpportunityLog evidence
