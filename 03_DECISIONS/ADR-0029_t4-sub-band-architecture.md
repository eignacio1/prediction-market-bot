# ADR-0029 — T4 Sub-Band Architecture: Multi-Tree Routing, Continuous Evaluation, Immediate Execution

**Status:** ACCEPTED — Tier A frozen (DS sign-off Earl Ignacio, 2026-06-22 SESSION 67). Tier B provisional per the two-tier acceptance model below.  
**Registered by:** T-179 (SESSION 66, 2026-06-22); scoped SESSION 67 (2026-06-22)  
**Drafted:** 2026-06-22 SESSION 66; scoped + accepted 2026-06-22 SESSION 67  
**Accepted:** 2026-06-22 SESSION 67 — DS sign-off (Earl Ignacio). Tier A organizing commitments are now immutable (hard rule #3); Tier B roster/numerics/hypotheses remain provisional and revisable via DECISION_LOG until each sub-band's Phase 8 Activation Gate.  
**Amends:** ADR-0010 (T4 Kelly fraction — superseded for T4; T1/T2/T3/T5 fractions unchanged), ADR-0014 (T4 decision tree section superseded), ADR-0018/ADR-0019 (NOISE_BUFFER_BAND_T4 superseded by per-sub-band derivation)  
**Completes:** ADR-0028 T4 Activation Gate placeholder (DESIGN INCOMPLETE notice removed upon DS sign-off on this ADR)  
**Carves out:** T4-MICRO (no-model market-microstructure / spread capture) — removed from this ADR's taxonomy and forwarded to **ADR-0030** as a distinct strategy class (execution-quality edge, not forecast edge). See "Scope Boundary" below.  
**Does NOT supersede:** ADR-0013 (T4 budget architecture — T4_BAND_WEIGHT=0.27 aggregate is unchanged), ADR-0022 (T4 realized-value exit credit semantics), ADR-0023 (proportional T4 band budget — aggregate unchanged), ADR-0026 (portfolio free-cash invariant — applies across all T4 sub-bands)  
**New governance gaps registered:** GG-038 (T4 kill switch SLA), GG-039 (T4 price cache / staleness check), GG-040 (T4 real-time data sources)  
**Effective:** Upon DS sign-off; governs T4 Phase 8 architecture design, all subsequent T4 code, and all T4 Activation Gate evidence criteria — **subject to the two-tier acceptance model below.**

---

## Scope Boundary and Two-Tier Acceptance

This ADR was scoped after a pre-sign-off alignment review (SESSION 67). Two structural decisions govern how it is to be read and signed.

### Why this architecture is built before alpha is demonstrated

The model has no demonstrated edge against Kalshi even at T1 (GG-004/GG-037 OPEN; edge currently anti-predictive). A fair challenge is therefore: why design an elaborate in-game architecture before the foundational edge question is answered?

**DS ruling (SESSION 67):** The T4 architecture is **strategy-agnostic scaffolding**, not a bet on any specific edge hypothesis. The organizing principle — "beat the situation, not the market" — is portfolio-management discipline, not a win-rate claim. A correct trade is evaluated against context (liquidity, volatility, target allocation, concentration, risk tolerance, cash-flow needs, macro alignment), not a binary profit/loss coin flip. The routing/evaluation/execution machinery (continuous evaluation → staleness arbitration → immediate execution) is reusable regardless of which specific edge strategy survives EXP validation. The edge/alpha math is treated as a separate, ongoing workstream (T-177) with the same rigor; locking the *architecture* now does not commit to any *edge claim*. This explicitly accepts the proportionality trade-off rather than ignoring it.

### Tier A vs Tier B — what sign-off freezes and what it does not

ADRs are immutable once accepted (hard rule #3). To avoid freezing unvalidated specifics, acceptance is **two-tier**:

- **Tier A — ACCEPTED ON SIGN-OFF (stable architecture):** The three-layer architecture (continuous evaluation → staleness-arbitrated queue → immediate C5 + C6 audit); the six design principles; the immediate-execution / staleness-arbitration model; the per-sub-band budget *mechanism* (shared pool + caps, not the cap values); the T4 Activation Gate *structure*; the kill-switch tier structure and ≤5s requirement. These are organizing commitments. Changing them requires a superseding ADR.

- **Tier B — PROVISIONAL (directional reference, not frozen):** The specific sub-band *roster* (which sub-bands exist, and how many); every numeric value (Kelly fractions, noise buffers, exposure caps, materiality gates, persistence thresholds, convergence premia); the alpha hypotheses each sub-band rests on. Tier B is a design hypothesis pending the first in-game EXP. A sub-band may be added, merged, split, or dropped, and any number revised, **without a superseding ADR** — only a DECISION_LOG entry — until its Phase 8 Activation Gate is cleared, at which point that sub-band's then-current values are frozen by its activation ADR (APR-XXXX). Tier B values are non-operational until their named EXP completes (Principle 5).

This means sign-off endorses the *machine and the method*, not the roster of 10 sub-bands or any number in this document. Nothing in Tier B can deploy capital before its EXP gate clears.

### T4-MICRO carve-out

T4-MICRO (pure order-book spread capture) has **no `model_p`** — its edge is execution quality, not forecast accuracy. That is a different strategy thesis from this project's core claim (`model_p > mip + vig`), closer in kind to the `arb/` folder (quarantined pending APR-0010) and DFS pick'em (requires its own ADR). It is therefore removed from this ADR's taxonomy and forwarded to **ADR-0030 (placeholder, registered SESSION 67)**, where it must carry its own thesis, activation gate, and EXP before any consideration. It is neither approved nor rejected here — only quarantined into the correct governance lane. This ADR's taxonomy is consequently **10 sub-bands**, all of which are `model_p`-based (or portfolio-structural overlays on `model_p`-based bets).

---

## The Problem with Monolithic T4

The current `execution_bands.py` defines T4 as a single `ExecutionBand.T4_IN_PLAY` with one model class (`bayesian_game_state`), one Kelly fraction (0.20), one compute budget (50ms), one SLA (5s). This treats the entire in-game execution window — spanning from pre-staged resting orders through multi-minute Bayesian posterior updates — as a single homogeneous signal type.

It isn't. DS directive 2026-06-22 (T-179 registration, DECISION_LOG SESSION 65):

> "In-game trading is the most diverse section — can be the most complex or simple dependent on the route. It can't just be clumped as one aggregate bucket."

The in-game window contains signal classes that differ in: what information they act on, what compute they require, what model class processes them, what execution mechanism they use, how long their edge window persists, and what governance review they require. Each of these dimensions drives architecture. Combining them into one band conflates architecturally distinct things.

**What was wrong about the previous design attempts:** An earlier design iteration organized sub-bands by clock time (5-second bucket, 1-minute bucket, 10-minute bucket). DS rejected this. The directive, paraphrased from the SESSION 66 design discussion (recorded in SESSION_HANDOFF_20260622_1300.md line 23; not captured verbatim in DECISION_LOG):

> Time buckets are "arbitrary band segments" — they *can* serve as a foundational reference point for the architecture, but they cannot be the taxonomy's defining principle.

*(Attribution note: this is a reconstructed paraphrase, not a verbatim transcript. The verbatim DS directives on record are the SESSION 65 "most diverse… can't just be clumped" entry [DECISION_LOG] and the SESSION 66 "immediate execution / nothing can be held" entry [handoff line 22]. DS to confirm or correct the paraphrase at sign-off.)*

The correct organizing principle: **what information is being acted on, and what does that require architecturally?** Time horizon emerges from that question as a consequence — it is not the definition. Clock buckets are reference points only; they do not create execution timing mandates.

---

## Design Principles (New — This ADR)

These principles extend ADR-0014's existing per-band decision tree framework:

**Principle 1 — Immediate Execution:** The moment a filtering mechanism approves a bet, it executes immediately. There are no execution time mandates. No sub-band "waits for its window to open." The system evaluates continuously; approved bets enter an execution queue and submit as fast as venue constraints allow. An edge window duration describes how long the edge is *expected to persist*, not when execution is *permitted*.

**Principle 2 — Staleness Arbitration Replaces Time Buckets:** The execution queue's staleness check — not a scheduled execution window — governs which bets actually execute. If an approved bet reaches the head of the queue and its edge has deteriorated below MIN_EDGE_TO_APPROVE at current market price, the bet is dropped. This is the correct architectural replacement for execution time mandates.

**Principle 3 — Parallel Evaluation:** All active decision trees run at their natural update frequency simultaneously. A slow T4-PROJ posterior computation (5–30s) does not block T4-EVENT from firing during that computation. Trees are independent pipelines sharing a common execution queue.

**Principle 4 — Multi-Tree, Bidirectional, Self-Insulating / Self-Growing:** Multiple trees from multiple sub-bands can fire on the same market simultaneously. Each fires in whatever direction its signal supports — YES or NO independently. Convergence across trees in the same direction is not blocked; it is convergent evidence. Divergence across trees signals uncertainty and invokes the divergence protocol (defined below). Each tree is bounded by its own Kelly fraction within the sub-band's exposure cap. The portfolio of trees self-insulates (no single tree pyramids) while self-growing (multiple trees find multiple edge opportunities in the same game state).

**Principle 5 — No Inherited Arbitrary Values:** Every numeric threshold, Kelly fraction, noise buffer, and exposure cap for every T4 sub-band must be either (a) formally derived analytically from the sub-band's signal properties using the ADR-0010 methodology, or (b) explicitly marked as provisional pending EXP derivation, with the EXP named and gated. "Confirmed at design time" is not a derivation. No sub-band activates with unresolved provisional values.

**Principle 6 — T4-CORR Is Downward-Only:** The correlation overlay (T4-CORR) adjusts sizes for correlated simultaneous approvals. It can only reduce sizes from C4-approved levels, never increase them. C4's free-cash invariant (ADR-0026) is evaluated at C4 approval time with original sizes; upward post-approval adjustment would violate the invariant.

---

## The Three-Layer Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER 1 — CONTINUOUS EVALUATION ENGINE                     │
│                                                             │
│  Each tree runs at its natural update frequency:            │
│  T4-STAGED  → each Kalshi price update (continuous)         │
│  T4-EVENT   → each qualifying game event (seconds)         │
│  T4-LINEUP  → each roster change detected (seconds)        │
│  T4-FLOW    → each possession completion (30–90s)           │
│  T4-SENTIMENT → N-second sustained price drift window      │
│  T4-PROJ    → every M minutes / each significant update     │
│  T4-ARITH   → each scoring event for near-threshold players │
│  T4-BOUNDARY → each quarter-end / halftime trigger         │
│  T4-EXIT    → continuous + every game event                 │
│                                                             │
│  Output per cycle: PASS | SIGNAL(bet) | EXIT(position)      │
│  SIGNAL → immediately enqueued to Layer 2                   │
│  EXIT → immediately enqueued to Layer 2 (priority=URGENT)  │
│  PASS → discarded                                           │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 2 — EXECUTION QUEUE WITH STALENESS ARBITRATION       │
│                                                             │
│  Queue discipline: priority-sorted by edge magnitude         │
│  EXIT signals bypass queue (priority=URGENT)                │
│                                                             │
│  Per-dequeue cycle (Kalshi: max 1 order/second sustained):  │
│  1. STALENESS CHECK                                         │
│     Recompute edge at current cached market price           │
│     edge < MIN_EDGE_TO_APPROVE OR direction reversed?       │
│     → DROP (log: sub_band, edge_at_entry, edge_at_drop,     │
│              queue_wait_ms, drop_reason)                    │
│     → PROCEED if edge still valid                           │
│                                                             │
│  2. T4-CORR ADJUSTMENT (downward-only)                      │
│     Are correlated bets from other sub-bands simultaneously │
│     queued for the same player or same game?                │
│     → Apply correlation discount to size if independent     │
│        signal not confirmed; enforce per-market exposure cap│
│     → Per-market exposure cap (max_single_event_exposure_usd│
│        = $500) enforced across ALL sub-bands combined       │
│                                                             │
│  3. C4 RISK CHECK (full engine)                             │
│     Kelly sizing at current bankroll + sub-band fraction    │
│     ADR-0026 free-cash invariant (solvency + 60% cap)       │
│     Drawdown kill switch check                              │
│                                                             │
│  4. SUBMIT to Layer 3 immediately                           │
│                                                             │
│  Rate-limit governance:                                     │
│  - Exits: reserved rate budget (cannot be starved by entry  │
│    volume); priority queue bypass                           │
│  - T4-PROJ: reserved rate budget (richest signal; high queue│
│    survival rate; must not be starved by T4-EVENT bursts)   │
│  - T4-EVENT: standard rate budget; high stale-drop rate     │
│    acceptable during burst periods                          │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  LAYER 3 — C5 EXECUTION + C6 AUDIT                          │
│                                                             │
│  C5: Submit order immediately upon receiving from Layer 2   │
│      No further delay; pays Kalshi 350ms API latency        │
│      Fill monitoring; cancel-on-no-fill within SLA window   │
│                                                             │
│  C6: Required audit fields (all sub-bands):                 │
│    - sub_band (T4-EVENT, T4-PROJ, etc.)                     │
│    - tree_id (which tree within the sub-band fired)         │
│    - signal_snapshot (game state at tree evaluation time)   │
│    - queue_entry_time, queue_exit_time, queue_wait_ms       │
│    - edge_at_entry, edge_at_execution (staleness delta)     │
│    - kelly_fraction_applied                                  │
│    - corr_adjustment_applied (bool + factor)                │
│    - fill_price, expected_price, slippage                   │
└─────────────────────────────────────────────────────────────┘
```

### The Staleness Check: Architectural Specification

The staleness check requires the current Kalshi market price for each bet dequeued. This creates a tension with the existing venue constraint (`max_api_calls_per_decision = 0` for T4). Resolution: a **separate read-only price polling loop** operates independently of the execution queue. It polls Kalshi market prices for all open markets at a cadence calibrated to the shortest expected edge window across active sub-bands, writes to an in-memory price cache, and does NOT consume execution rate limit budget.

Price cache staleness window per sub-band:
- T4-EVENT: ≤ 2 seconds (edge window is seconds; a 2s stale price is acceptable)
- T4-LINEUP: ≤ 5 seconds
- T4-FLOW, T4-SENTIMENT, T4-PROJ, T4-ARITH: ≤ 30 seconds

This architecture requires a dedicated price polling design (GG-039). The polling loop's API calls are read-only and time-separated from execution calls — they use the same Kalshi rate budget but are interleaved with execution calls rather than competing with them. Detailed design deferred to GG-039 resolution.

### Kill Switch Architecture Revision

**Current kill switch SLA (NFR-03): ≤60 seconds.** At Kalshi's 60 calls/min execution rate, 60 seconds represents up to 60 additional bets submitted between kill trigger and halt. For T4 with continuous evaluation potentially firing multiple signals per second, this is architecturally unacceptable.

**Required T4 kill switch SLA: ≤5 seconds.** This requires:
1. A T4-specific kill switch signal that halts the Layer 1 evaluation engine immediately (stops new SIGNALs from entering the queue)
2. A queue flush that drops all pending (not yet submitted) execution queue entries
3. An in-flight order cancellation mechanism for any orders submitted in the last 5 seconds but not yet confirmed filled

Implementing a ≤5s kill switch requires architectural changes to C7 that do not yet exist. This is registered as GG-038 and is a Phase 8 prerequisite. ADR-0029 establishes the requirement; the implementation ADR is required before T4 Phase 8 activation.

**Kill switch tier structure for T4:**

| Kill switch tier | Trigger | Scope | SLA |
|---|---|---|---|
| T4-sub-band budget exhausted | Sub-band exposure cap reached | Halts that sub-band; others continue | Immediate (pre-queue check) |
| T4 band budget exhausted | T4_BAND aggregate cap reached | Halts all T4 sub-bands; T1/T2/T3 continue | ≤5s (GG-038) |
| System kill switch | Drawdown ≥ 20%, daily loss ≥ 15% | Halts all bands | ≤5s for T4 (GG-038); current 60s for T1 |

The existing system-level kill switch (C7) remains operative for T1/T2/T3 at its current 60s SLA. T4 requires a separate fast-halt mechanism. The two must operate independently and without coupling.

---

## Sub-Band Taxonomy: Complete Specification

### Naming Convention

Each sub-band is a first-class `ExecutionBand` enum value, replacing the single `T4_IN_PLAY`. `T4_IN_PLAY` is superseded upon code implementation. Sub-band IDs follow the format `T4_{IDENTIFIER}` in enum form.

Strategy naming for BAND_REGISTRY: existing Strategy K ("In-Play Scalping") is split. Entry sub-bands receive new strategy IDs. Portfolio/structural sub-bands (T4-CORR, T4-EXIT, T4-BOUNDARY) are system-level components; they receive BandConfig entries but NOT StrategyBandSpec entries (they are not edge-source strategies). Exact strategy ID naming is a code implementation decision, deferred to the implementation task.

---

### T4-MICRO — CARVED OUT TO ADR-0030 (not in this taxonomy)

T4-MICRO (pure order-book spread capture / liquidity provision) is **removed from this ADR** and forwarded to **ADR-0030 (placeholder)**. Rationale: it has no `model_p` — its edge is execution quality, not forecast accuracy — which makes it a distinct strategy class from the forecast-edge thesis governing every other T4 sub-band. Folding a no-model HFT scalping leg into the forecast bot's T4 band would conflate two unrelated edge theses under one activation gate. Per the same governance discipline that quarantines `arb/` (APR-0010) and DFS pick'em (separate ADR), it gets its own lane.

It is neither approved nor rejected here. ADR-0030 must establish its own thesis, its own activation gate, its own EXP (does Kalshi order-book spread capture clear fees?), and its own C5 resting-order module before any consideration. Until ADR-0030 is drafted and signed, T4-MICRO does not exist as an executable strategy.

---

### T4-STAGED — Pre-Game Conditional Fill

**Information class:** T3-approved signal with pre-set price trigger. No new computation at fill time.

**Natural update frequency:** Continuous Kalshi price monitoring (passive).

**Decision tree:**
```
T3: C4 approves bet at current price → compute trigger_price range
    [trigger_YES = price at which edge_YES ≥ MIN_EDGE_TO_APPROVE]
    [trigger_NO  = price at which edge_NO  ≥ MIN_EDGE_TO_APPROVE]
    Place resting limit order(s) at trigger price(s)
    
T4: Market reaches trigger_price → resting order fills (passive)
    No new decision. Fill is the decision.
```

**Bracket variant:** Two resting orders per market (one YES at trigger_YES, one NO at trigger_NO). If YES fills, cancel NO (and vice versa). Bracket gives the market both directions — fills wherever edge materializes.

**Model class:** T1 model (same signal as T3 execution). No incremental computation.

**Kelly fraction:** T3 Kelly (0.07 per ADR-0010). The signal is a T3 decision; no independent T4 signal quality improvement justifies a higher fraction. If T3 Kelly changes via ADR, T4-STAGED Kelly changes identically.

**Noise buffer:** T3 noise buffer (NOISE_BUFFER_BAND_T3 = 0.22053). The position was sized and approved at T3; T3's buffer governs exits.

**Execution prong:** Resting limit order placed at T3 time. Zero live T4 API calls. T4-STAGED fills are counted against T4 budget (not T3 budget) because they execute in T4 time and consume T4 capital.

**Expected edge window duration:** Indefinite — the resting order persists until filled, cancelled at tip-off, or cancelled at game end. The edge window is not time-bounded.

**Budget charge:** T4 budget at fill time. T3 C4 approval authorizes the capital commitment; T4 budget is the accounting home.

**Currently activatable:** Phase 8 (same as all T4 sub-bands). Infrastructure feasibility is confirmed (resting orders are standard Kalshi API functionality); data source requirements are T3-level (already built).

---

### T4-EVENT — Discrete Stat Event Reaction

**Information class:** A single discrete game event that directly updates the expected terminal stat for a tracked player on a live market.

**Natural update frequency:** Per qualifying game event (real-time box score feed; event detection latency is a Phase 8 data source requirement — see GG-040).

**Trees within sub-band:**

| Tree ID | Trigger event | Affected market type | Signal direction |
|---|---|---|---|
| EVENT-PTS-MADE | Made field goal by tracked player | PTS market | YES (if below threshold), NO (if approaching threshold ceiling) |
| EVENT-PTS-OPPO | Made field goal by opponent → game pace spike | PTS markets (both teams) | Context-dependent |
| EVENT-MIN-FOUL | Personal foul #3+ in Q1/Q2, #4+ in Q3 | Minutes market | NO (early exit risk) |
| EVENT-MIN-SUB | Tracked player subbed out unexpectedly | Minutes market | NO (minutes accumulation slows) |
| EVENT-MIN-SUBIN | Tracked player checks back in early | Minutes market | YES (minutes accumulation resumes) |
| EVENT-BLOWOUT | Score differential crosses ±20 in Q2/Q3 | PTS markets — both trailing and leading | YES on trailing star (desperation pace ↑), NO on leading star (garbage time ↓) |

**Filtering mechanism — two mandatory gates:**
1. **Event whitelist:** Only events in the above tree table are routed. Non-scoring, non-substitution events (ball out of bounds, replay review, etc.) are discarded without evaluation.
2. **Materiality gate per tree:** The event must move `P(stat ≥ threshold | current_stat, time_remaining)` by > `materiality_threshold` from the pre-event estimate. Materiality threshold is EXP-derived per tree type. Preliminary reference: same `max(2σ_null(t), 0.04)` formula from ADR-0021, adapted for the event-conditional update context. Pre-activation EXP must validate this formula per tree.

**Decision tree (per qualifying event, per tree):**
```
Qualifying event detected →
  tree_id = identify_tree(event_type) →
  p_pre = P(stat ≥ threshold | state_before_event) [from price cache T4-PROJ layer]
  p_post = P(stat ≥ threshold | state_after_event)  [Bayesian point update]
  |p_post - p_pre| ≥ materiality_threshold? →
  No: PASS
  Yes:
    edge = p_post - market_implied_probability - vig
    edge ≥ MIN_EDGE_TO_APPROVE? →
    No: PASS
    Yes: SIGNAL(bet) → Layer 2
```

**Model class:** Lightweight Bayesian point update:
```
p_post = calibrated_Poisson_survival(
    threshold - current_stat | 
    lambda_remaining = lambda_T4_PROJ × (time_remaining / game_length)
)
```
Uses same calibration temperature as T4-PROJ (NBA T=2.05, ADR-0027). The lambda is sourced from T4-PROJ's current posterior estimate — T4-EVENT does not maintain its own lambda; it borrows from T4-PROJ. This creates a dependency: T4-EVENT should only fire after T4-PROJ has computed at least one posterior estimate for the player. At game start, T4-EVENT uses T1 prior lambda until first T4-PROJ posterior is computed.

**Kelly fraction:** EXP-required before activation. Preliminary analytical bound:

The key alpha hypothesis for T4-EVENT is that Kalshi systematically lags in repricing after discrete game events (edge window exists). If this is false, the sub-band has no edge. **EXP must confirm the repricing lag hypothesis before any Kelly fraction is meaningful.** Provisional structure (not a value): use ADR-0010 variance-scaling formula with σ_λ evaluated at event time. Early-game events have high σ_λ (→ low Kelly); Q4 events have low σ_λ (→ higher Kelly). Full game-phase dependency applies.

**Expected edge window duration:** 1–10 seconds. This is the primary alpha hypothesis — EXP must validate it.

**Queue survival rate:** LOW during burst periods (many events fire simultaneously); HIGH when queue is short. Burst stale-drops are architecturally correct — only the highest-edge events execute.

**Critical pre-activation EXP:** EXP must measure actual Kalshi market repricing latency after discrete game events across a sample of N ≥ 50 events per tree type. If mean repricing latency < 1 second for a given tree, that tree has no exploitable edge window and should not activate. This is the single most important validation gate for T4-EVENT.

---

### T4-LINEUP — Live Lineup / Rotation Detection

**Information class:** Unexpected roster changes — a player checks in or out at an unexpected time (not matching expected rotation). Affects multiple markets simultaneously (starter + backup).

**Natural update frequency:** Per roster change detected from live lineups/play-by-play API (see GG-040).

**Distinction from T4-EVENT:** T4-EVENT fires on a single market from a single stat event. T4-LINEUP fires on N markets (all markets for all affected players) from one roster event. The portfolio dimension defines this sub-band.

**Decision tree:**
```
Roster change detected (player X subbed out, player Y subbed in) →
  Is this change unexpected? 
  [unexpected = not in rotation model's predicted substitution window]
  No: PASS (normal rotation, no new information)
  Yes:
    affected_markets = all_open_markets_for(player_X) + all_open_markets_for(player_Y)
    For each market in affected_markets:
      p_adjusted = T4-PROJ_update(player, minutes_now_expected)
      edge = p_adjusted - market_implied_probability - vig
      edge ≥ MIN_EDGE_TO_APPROVE? → SIGNAL(bet) → Layer 2
    [All N SIGNALs enter Layer 2 simultaneously; T4-CORR evaluates correlation]
```

**Model class:** T4-PROJ posterior updated with revised minutes projection. Requires a rotation model that predicts expected substitution windows (EXP-required).

**Kelly fraction:** EXP-required. Conservatively bounded below T4-PROJ (more uncertain; portfolio-level cascading risk; harder to calibrate σ_λ for lineup changes). Provisional: 0.05 maximum until EXP-derived.

**Exposure constraint:** T4-LINEUP bets for players in the same game are highly correlated (same lineup change affects both). T4-CORR will apply discounts. Additionally, a per-event exposure cap applies: total capital deployed in a single lineup event ≤ X% of T4 budget (X: EXP-derived; provisional: 15%).

**Data source prerequisite:** Live play-by-play or lineups API with ≤ 5-second detection latency for substitutions. Not in current C1 architecture. Registered as component of GG-040.

---

### T4-FLOW — Accumulated Game State / Context Pattern

**Information class:** Sustained multi-possession patterns requiring 5–15+ possessions to confirm: foul trouble accumulation, pace deviation from expected, blowout context, rotation-driven role expansion.

**Natural update frequency:** Per possession completion (rolling window re-evaluated).

**Trees within sub-band:**

| Tree ID | Pattern | Persistence threshold | Lambda adjustment |
|---|---|---|---|
| FLOW-FOUL | Player X fouls ≥ 3 in Q1/Q2, ≥ 4 in Q3 | 3+ possessions post-foul with reduced minutes pace | EXP-derived foul_trouble_factor (expected ≈ 0.65–0.80× base lambda) |
| FLOW-PACE | Game pace ≥ 15% above/below expected | 5+ consecutive possessions showing deviation | pace_factor = (observed_pace / expected_pace); affects all PTS/AST/REB markets |
| FLOW-ROTATION | Starter's minutes pace implies shortened night | 3+ consecutive bench stints beyond expected | EXP-derived rotation_factor on minutes-dependent markets |
| FLOW-BLOWOUT | Score differential ≥ 20 for 5+ possessions | 5+ possessions sustained differential | Trailing star: lambda × blowout_desperation_factor; Leading star: lambda × garbage_time_factor |

**FLOW-BLOWOUT is the primary carrier of the "Knicks comeback consequences" architecture:** When a team is down 20+ for 5+ possessions, two distinct effects propagate to individual player markets: (1) trailing team stars take more shots (lambda ↑) trying to close the gap; (2) leading team may begin resting starters in Q4 (lambda ↓ for leading stars, lambda ↑ for leading backups). The system bets on CONSEQUENCES of the blowout state on individual player markets — not on the game outcome.

**Filtering mechanism — three mandatory gates:**
1. Pattern persistence threshold (per tree, as above)
2. Context classifier confidence ≥ threshold (EXP-derived per tree)
3. Market price has not already adjusted to reflect this context (staleness check pre-SIGNAL): `|p_T4_FLOW - market_implied_probability| ≥ MIN_EDGE_TO_APPROVE + vig`

**Model class:** Poisson with context-adjusted lambda:
```
lambda_adjusted = lambda_T4_PROJ × context_multiplier(tree_id, current_game_state)
p_T4_FLOW = calibrated_Poisson_survival(threshold - current_stat | lambda_adjusted × t_remaining)
```

Context multipliers (`foul_trouble_factor`, `pace_factor`, `blowout_desperation_factor`, `garbage_time_factor`) must be calibrated from historical data via EXP before activation. These are the most data-intensive derivation requirements in T4.

**Kelly fraction:** EXP-required. Framework: same ADR-0010 variance-scaling formula with σ_λ including both the base Poisson variance AND the variance of the context multiplier estimate (additional uncertainty from the multiplier calibration). Provisional: 0.08–0.12 depending on game phase and context type. Formal derivation required.

**Correlated stacking note:** FLOW trees can fire simultaneously on the same player (FLOW-FOUL and FLOW-PACE can both be active). T4-CORR handles this. Intentional stacking (convergent evidence) vs. accidental stacking (same underlying cause) is distinguished by whether the two signals are mechanistically independent. FLOW-FOUL and FLOW-PACE are independent signals (foul trouble ≠ pace); both firing is convergent evidence. FLOW-BLOWOUT and FLOW-FOUL may be correlated in a blowout (trailing team stars get foul trouble defending desperately) — T4-CORR must detect this.

---

### T4-SENTIMENT — Market Price Drift

**Information class:** Sustained directional Kalshi price movement not explained by recent game events. The market is signaling something the model hasn't captured, or the market is over-reacting and the model disagrees.

**Natural update frequency:** Price tick monitoring via the Layer 2 price cache; re-evaluated every N seconds of sustained drift (N: EXP-derived, likely 30–120 seconds).

**Decision tree:**
```
Observe price drift over window W:
  drift_rate = (price_now - price_W_ago) / W   [signed: positive = market moving YES]
  |drift_rate| ≥ drift_threshold AND
  no qualifying game event in window W (i.e., drift is not event-driven)?
    No: PASS (drift is explained by event — T4-EVENT handles it)
    Yes: Classify drift as INFORMED or NOISE:
      model_p = current T4-PROJ posterior estimate for this player/market
      market_p = current Kalshi price
      IF drift is toward model_p: drift is MOMENTUM (bet WITH drift)
      IF drift is away from model_p: drift is OVERREACTION (bet AGAINST drift)
      Compute edge under both interpretations → highest-confidence interpretation wins
      edge ≥ MIN_EDGE_TO_APPROVE? → SIGNAL(bet) → Layer 2
```

**Model class:** Divergence analysis between T4-PROJ posterior and Kalshi market price, interpreted through the lens of drift direction. No new model — T4-SENTIMENT is a second-order signal that uses T4-PROJ's output as its reference.

**Kelly fraction:** EXP-required. Lower than T4-PROJ (less certain signal — depends on correctly classifying drift as informed vs. noise). Provisional: 0.05.

**Critical EXP:** Can the system reliably distinguish informed drift (market learning from a data source we don't have) from noise drift (thin market overreacting to individual orders)? If not, T4-SENTIMENT is a noise-trading sub-band and should not activate.

---

### T4-PROJ — Bayesian Posterior Full-Game Projection

**Information class:** Accumulated in-game stats → posterior update on T1 prior. Full Poisson survival probability recomputed with game-state-updated lambda.

**Natural update frequency:** Every M minutes (continuous posterior drift trigger) AND on each significant game event (significant = |posterior_change| ≥ materiality_gate). The T4-PROJ posterior is the shared reference for T4-EVENT and T4-SENTIMENT. It is the richest signal in the T4 suite and the architectural spine of T4.

**Confidence regimes (derived from ADR-0010 game-phase analysis):**

| Regime | Game clock | σ_λ_T4 | T4 vs T1 | Behavior |
|---|---|---|---|---|
| EARLY | 0–24 min elapsed | 3.16–11.07 | Worse than T1 (1.5×–5.4×) | Sparse firing; materiality gate elevated; approach T1 conservatively |
| MID | 24–36 min elapsed | 1.29–3.16 | Comparable to T1 | Standard firing; normal edge gate |
| LATE | 36–44 min elapsed | 0.60–1.29 | Better than T1 (1.6×–3.4×) | Primary firing window; highest Kelly fraction |
| NEAR-CERTAIN | 44+ min elapsed | < 0.60 | Significantly better than T1 | Kelly approaches T4-ARITH territory; T5 threshold proximity check |

**Decision tree:**
```
Posterior update triggered (timer OR significant event):
  lambda_observed = (current_stat / elapsed_min) × 48   [full-game pace projection]
  confidence_weight(t) = (elapsed_min / 48)^α            [α: EXP-derived curve shape]
  lambda_posterior = confidence_weight × lambda_observed + (1 - confidence_weight) × lambda_T1_prior
  p_posterior = calibrated_Poisson_survival(threshold - current_stat | 
                    lambda_posterior × time_remaining / 48)
  
  materiality_gate: |p_posterior - p_T1_prior| ≥ T4_PROJ_MATERIALITY_GATE?
  [prevents re-firing on unchanged signal; gate: EXP-derived, preliminary ≥ 0.05]
  
  edge = p_posterior - market_implied_probability - vig
  edge ≥ MIN_EDGE_TO_APPROVE → full C4 check → SIGNAL → Layer 2
  
  Shared write: update T4-PROJ_CACHE[player][market] with current posterior
  [T4-EVENT and T4-SENTIMENT read from this cache]
```

**Model class:** Posterior-updated Poisson. Same calibration temperature as T1 (NBA T=2.05, ADR-0027). T4-PROJ is the sub-band where calibration temperature directly applies — T4-EVENT borrows this output.

**Kelly fraction — dynamic framework (ADR-0010 extended):**

From ADR-0010:
```
k_T4_PROJ(t) = k_T4_ref × (σ_λ_T4_ref / σ_λ_T4_PROJ(t))
```
where `k_T4_ref = 0.20`, `σ_λ_T4_ref = 0.50` (Q4 reference, ADR-0010 anchor).

σ_λ_T4_PROJ(t) from ADR-0010 derivation:
- 24 min elapsed (halftime): σ_λ = 3.16 → k = 0.20 × (0.50/3.16) = **0.032**
- 36 min elapsed (Q3 end): σ_λ = 1.29 → k = 0.20 × (0.50/1.29) = **0.078**
- 42 min elapsed (Q4 mid): σ_λ = 0.60 → k = 0.20 × (0.50/0.60) = **0.167**
- 46 min elapsed (Q4 late): σ_λ = 0.19 → k = 0.20 × (0.50/0.19) = **0.526** [exceeds project max; HARD-CAPPED at 0.25 — see caveat]

**⚠️ Formula-breakdown caveat (Tier B; EXP-required before any near-certain sizing).** The inverse-variance formula `k ∝ 1/σ_λ` diverges as σ_λ → 0: at 46 min it produces k = 0.526, which is **2.1× the project-wide maximum Kelly (DEFAULT_KELLY_FRACTION = 0.25)** and more than full-Kelly territory for a single position. The 0.25 cap is therefore a **hard governance ceiling, not a derived value** — the formula is *out of its valid regime* in the NEAR-CERTAIN band, and capping is a band-aid, not a derivation. Two distinct problems must be resolved by EXP before T4-PROJ activates in the NEAR-CERTAIN regime:
1. **Re-derivation, not capping:** the near-certain Kelly must be derived from a model valid at low σ_λ (e.g., arithmetic-survival sizing as in T4-ARITH / T5), not by truncating a diverging inverse-variance term.
2. **Calibration-vs-confidence conflict:** the model is documented to be *overconfident in the tails* (Poisson over-dispersion; the NBA T = 2.05 temperature shrink, ADR-0027; the Wembanyama NO concentration episode). Sizing at or near the project maximum *precisely* in the near-certain tail — where the model is least calibrated — is the highest-leverage place to be wrong. EXP-PROJ-01 must confirm post-calibration tail reliability *before* any NEAR-CERTAIN Kelly above the MID-regime level is permitted. Until then, NEAR-CERTAIN sizing is provisionally held at the LATE-regime ceiling (≤ 0.167), **not** 0.25.

**Dynamic Kelly schedule for T4-PROJ:**

| Game phase | k_T4_PROJ_derived | k_T4_PROJ_applied | Note |
|---|---|---|---|
| EARLY (< 24min) | < 0.032 | 0.010 (floor) | Worse than T1; use floor to prevent near-zero sizing noise |
| MID (24–36min) | 0.032–0.078 | EXP-derived | Full game-phase formula applies |
| LATE (36–44min) | 0.078–0.167 | EXP-derived | Primary T4-PROJ value zone |
| NEAR-CERTAIN (> 44min) | > 0.167 (formula diverges — invalid regime) | **provisional ≤ 0.167** until EXP-PROJ-01; hard ceiling 0.25 thereafter | Inverse-variance formula breaks down here (see caveat). Re-derive from arithmetic-survival model; do NOT size above MID/LATE level until tail calibration confirmed |

**This supersedes the monolithic T4 Kelly = 0.20 in ADR-0010 for T4-PROJ. The 0.20 was the anchor; the dynamic schedule is the operational derivation.**

The 2× operational premium over pure variance-derived Kelly (ADR-0010 §3) does NOT automatically apply to T4-PROJ's game-phase schedule. The variance formula alone is derivation-sufficient for T4-PROJ because the game-clock-dependent sigma is directly measurable, unlike T1 where non-stationarity uncertainty warranted the premium. EXP must confirm whether a premium is justified.

**Blowout-posterior regime (bidirectional edge capture):**

When score differential ≥ 20 AND game clock is in LATE or NEAR-CERTAIN regime:
```
lambda_posterior adjustments:
  trailing star: lambda × blowout_shooting_rate_factor (EXP-derived; expected > 1.0)
  leading star: lambda × garbage_time_usage_factor (EXP-derived; expected < 1.0)
  leading backup: lambda × backup_promotion_factor (EXP-derived; depends on roster depth)
```

Both expansion (trailing star's lambda ↑) and contraction (leading star's lambda ↓) produce edge because the market has not fully priced the game-state consequence. Both are signal. Both route through the same edge check. Direction is determined by sign of `p_posterior - market_implied_probability`. This is the architectural formalization of the "Knicks comeback consequences" design.

**Noise buffer:** This sub-band carries the most similarity to the original monolithic T4. The existing `NOISE_BUFFER_BAND_T4 = 0.19` (EXP-019B/C empirical, G4 n=1,199 positions) was derived from monolithic T4 behavior which was primarily Q3/Q4 T4-PROJ-equivalent positions. Provisionally, T4-PROJ inherits this buffer (0.19) pending EXP re-derivation with phase-specific data. Derivation should be repeated per game phase (EARLY buffer may differ from LATE buffer due to different σ_p profiles).

---

### T4-ARITH — Threshold-Approaching Arithmetic Near-Certainty

**Information class:** A player's current stat is within N points of their threshold with sufficient time remaining that the probability is high but not yet T5-level arithmetic certainty. The distribution has contracted to the point where arithmetic reasoning dominates stochastic modeling.

**Natural update frequency:** Per scoring event for tracked players with `threshold - current_stat ≤ ARITH_ENTRY_WINDOW`.

**Distinction from T4-PROJ:** T4-PROJ is a full posterior update valid across all probability ranges. T4-ARITH fires only when the distribution is tight (high certainty). T4-ARITH's decision tree simplifies: the probability is near-deterministic for the remaining gap, so the computation is dominated by the gap arithmetic rather than the full Poisson survival.

**Distinction from T5:** T5 fires in the final `EXIT_MIN_TIME_REMAINING_MIN = 3.0` minutes with certainty gate `p ≥ 0.85`. T4-ARITH fires earlier (up to ~15 minutes remaining) when the gap is small but the game clock has not yet entered T5 territory.

**Decision tree:**
```
Scoring event for player with (threshold - current_stat) ≤ ARITH_ENTRY_WINDOW:
  remaining_expected = lambda_T4_PROJ × time_remaining / 48
  gap = threshold - current_stat
  
  IF gap ≤ 0: player has exceeded threshold; bet is over (T5-EXIT protocol applies)
  
  p_arith = P(Poisson(remaining_expected) ≥ gap)   [simple Poisson survival for remaining gap]
  
  IF p_arith ≥ T4_ARITH_CONFIDENCE_GATE AND time_remaining > EXIT_MIN_TIME_REMAINING_MIN:
    edge = p_arith - market_implied_probability - vig
    edge ≥ MIN_EDGE_TO_APPROVE → SIGNAL → Layer 2
  
  IF time_remaining ≤ EXIT_MIN_TIME_REMAINING_MIN: hand off to T5 arithmetic
```

**Model class:** Poisson survival on remaining gap only. No full-game projection. Uses T4-PROJ's current `lambda_posterior` as the rate estimate.

**`T4_ARITH_CONFIDENCE_GATE`:** EXP-derived. Minimum `p_arith` to qualify for T4-ARITH routing (expected: 0.70–0.80). Below this, T4-PROJ handles the market. Above this, T4-ARITH routing applies with higher Kelly fraction.

**`ARITH_ENTRY_WINDOW`:** EXP-derived. Maximum gap (in stat units) to trigger T4-ARITH routing. Expected: 2–4 stat units (e.g., ≤3 points remaining to threshold with 10+ min left).

**Kelly fraction:** Higher than T4-PROJ (lower uncertainty in the near-certain regime); lower than T5 (not fully arithmetic). EXP-derived. Provisional: 0.22 (midpoint between T4-PROJ LATE regime and T5). **Subject to the same tail-calibration constraint as T4-PROJ NEAR-CERTAIN** — T4-ARITH operates in exactly the near-certain regime where the model is documented to be overconfident. The 0.22 provisional is held *non-operational* until EXP-ARITH-01 confirms post-calibration reliability of `p_arith` in the high-certainty band; it must not be read as an approved size.

---

### T4-BOUNDARY — Quarter / Halftime Structural Reset (Structural Sub-Band)

**Information class:** Predictable structural game events — end of Q1, Q2 (halftime), Q3, regulation end — where the model should reassess all open positions and re-scan for new entry opportunities with fresh quarter-level context.

**Natural update frequency:** Fires on game structure, not data signals. Quarter-end trigger from live game clock.

**This sub-band is primarily about EXITS and REASSESSMENTS, not new entries.** New entries at quarter boundaries are a secondary output — they happen when the post-reset T4-PROJ posterior reveals a significant edge on a market not yet in portfolio.

**Decision tree:**
```
Quarter-end detected (GAME_CLOCK == QUARTER_END):
  
  [PHASE 1 — EXIT EVALUATION]
  For each open T4 position:
    Recompute p_posterior with post-quarter game state
    Has direction reversed? → SIGNAL(EXIT) → Layer 2 (priority=URGENT)
    Is noise buffer cleared AND p_posterior diverged from entry by > buffer? → SIGNAL(EXIT)
    Else: HOLD
  
  [PHASE 2 — HALFTIME OVERLAY (Q2 end only)]
  Re-run T4-PROJ with halftime-adjusted inputs:
    Updated rest, rotation expectations, coach adjustments assumed
    For any player where posterior shifts > HALFTIME_MATERIALITY_GATE: re-evaluate
  
  [PHASE 3 — NEW ENTRY SCAN]
  Re-run T4-PROJ posterior for all tracked markets
  Any market with edge ≥ MIN_EDGE_TO_APPROVE not already in portfolio → SIGNAL(bet) → Layer 2
```

**Model class:** Full T4-PROJ run at each quarter boundary.

**Kelly fraction:** Inherits from T4-PROJ (new entries) and T4-EXIT (exits). No independent Kelly for T4-BOUNDARY.

**Note on halftime:** Halftime is structurally distinct from Q1/Q3 boundaries — coaches make lineup and strategy adjustments. The halftime overlay should incorporate any lineup change signals from T4-LINEUP detected at halftime. This is a T4-BOUNDARY ↔ T4-LINEUP integration point.

---

### T4-CORR — Cross-Market Correlation Overlay (Portfolio Sub-Band)

**What it does:** Detects when multiple trees from any sub-band have approved simultaneous bets on correlated markets and adjusts sizes downward to account for the correlation. Operates in Layer 2, between C4 approval and C5 submission. Does NOT approve new bets; only modifies sizes of already-approved bets.

**Correlation detection logic:**
```
For each group of simultaneously queued bets (same player, same game, same time window):
  Compute pairwise correlation score:
    SAME_PLAYER_SAME_MARKET: correlation = 1.0 → second bet is duplicate; DROP one
    SAME_PLAYER_DIFFERENT_MARKET: correlation = f(market_type_correlation)
      [PTS and AST for same player: moderate correlation → partial discount]
      [PTS and MIN for same player: high correlation → significant discount]
    SAME_TEAM_DIFFERENT_PLAYER: correlation = f(game_state_correlation)
      [Both players on trailing team during blowout: correlated signal → discount]
    DIFFERENT_TEAMS: correlation ≈ 0 → no adjustment
  
  Per-market exposure cap enforcement:
    sum(sizes for same market) ≤ max_single_event_exposure_usd ($500)
    If over cap: reduce proportionally (downward-only, per Principle 6)
```

**Convergence signal:** When N sub-bands from different families (e.g., T4-EVENT + T4-FLOW + T4-PROJ) fire on the same market in the same direction independently, this is convergent evidence — N trees with mechanistically independent signals all point the same direction. T4-CORR should NOT discount this as correlation. The test: are the signals mechanistically independent? EVENT-PTS-MADE + FLOW-BLOWOUT + T4-PROJ-BLOWOUT-POSTERIOR can all fire on the same trailing-star PTS market simultaneously and represent three independent signals.

**Kelly for convergent evidence:** When N mechanistically independent signals converge:
```
kelly_combined = base_kelly × convergence_factor(N)
convergence_factor(N) = 1 + (N-1) × convergence_premium
```
where `convergence_premium` is EXP-derived (expected: 0.10–0.25 per additional independent confirming signal). Subject to per-market exposure cap.

---

### T4-EXIT — Active Position Management (Portfolio Sub-Band)

**What it does:** Continuously monitors all open T4 positions and fires EXIT signals when a position's edge has deteriorated below the exit floor, the posterior has reversed direction, or the noise buffer condition is met.

**Natural update frequency:** Continuous + every qualifying game event.

**Exit decision tree (per open position, per evaluation cycle):**
```
For each open T4 position [player, market, sub_band_origin, entry_p, entry_price]:
  
  current_p = T4-PROJ_CACHE[player][market].posterior
  current_market_price = price_cache[player][market]
  
  [REVERSAL CHECK]
  IF sign(current_p - 0.5) ≠ sign(entry_p - 0.5):
    Full directional reversal → EXIT immediately
  
  [NOISE BUFFER CHECK]
  IF |current_p - entry_p| ≥ NOISE_BUFFER_for_sub_band:
    IF current_p has moved AGAINST the bet direction:
      EXIT (moved against us by more than noise buffer)
    IF current_p has moved FOR the bet direction:
      HOLD (favorable movement — do not exit winners)
  
  [TIME-BASED FLOOR]
  IF time_remaining ≤ EXIT_MIN_TIME_REMAINING_MIN:
    Hand off to T5 arithmetic certainty protocol
    If T5 would bet YES and we hold YES: hold
    If T5 would not bet: evaluate exit
  
  [Q4-BLOWOUT EXIT]
  IF score_differential ≥ 30 AND time_remaining ≤ 8 min:
    Leading team's starters may be rested → update expected minutes → recheck
```

**Noise buffers per sub-band (provisional pending EXP re-derivation):**
- T4-STAGED: NOISE_BUFFER_BAND_T3 = 0.22053 (same as T3, inherited from T3 decision)
- T4-EVENT: EXP-required (short edge window → expected tighter buffer, < 0.19)
- T4-LINEUP: EXP-required (portfolio-level; expected moderate)
- T4-FLOW: NOISE_BUFFER_BAND_T4 = 0.19 (monolithic T4 empirical basis; closest match)
- T4-SENTIMENT: EXP-required
- T4-PROJ: NOISE_BUFFER_BAND_T4 = 0.19 (direct inheritance; primary intended basis for this value)
- T4-ARITH: Below 0.19 (arithmetic near-certainty → tighter buffer); EXP-required

**Kill switch SLA requirement:** T4-EXIT signals must execute within ≤5s of trigger (same as T4 kill switch requirement). EXIT signals bypass the standard execution queue and receive priority processing.

---

## Budget Partitioning Within T4

**Aggregate T4 budget unchanged:** `T4_BAND_WEIGHT = 0.27` (ADR-0023). Total T4 budget = 0.27 × bankroll. This aggregate is not modified by ADR-0029.

**Internal architecture: Shared pool with per-sub-band maximum concurrent exposure caps.** Sub-bands draw from the shared T4 budget. No fixed allocations. Capital follows edge — sub-bands finding more edge get more capital, subject to caps.

**Per-sub-band maximum concurrent exposure** (as % of T4 aggregate budget; provisional pending EXP derivation):

| Sub-band | Max concurrent exposure (% T4 budget) | Rationale |
|---|---|---|
| T4-STAGED | 30% | Pre-staged orders have long hold times; prevent domination |
| T4-EVENT | 20% | High volume, short duration; stale-drops naturally limit actual deployment |
| T4-LINEUP | 15% | Portfolio cascade risk per lineup event; hard cap per event |
| T4-FLOW | 40% | Long edge window; sustained positions; primary T4-FLOW capital home |
| T4-SENTIMENT | 15% | Lower confidence signal; conservative cap until EXP validated |
| T4-PROJ | 60% | Richest signal; primary T4 capital home; approaches T1 evidence quality in Q3/Q4 |
| T4-ARITH | 30% | Near-certainty regime; limited market pool at any given time |
| T4-BOUNDARY | Inherits T4-PROJ cap | Not independent capital; boundary re-entry uses T4-PROJ cap |

**Sum-to-100% constraint is NOT required** — these are maximums per sub-band, not allocations. Total T4 exposure at any moment is governed by ADR-0026 (60% equity aggregate) + T4_BAND_WEIGHT (27% of bankroll). The per-sub-band caps prevent any single sub-band from consuming the entire T4 budget.

All per-sub-band caps are provisional and must be formally derived from EXP data showing expected concurrent positions per sub-band × Kelly size before Phase 8 ACTIVE designation.

---

## Amendments to Existing ADRs

### Amendment 1 — ADR-0010 (T4 Kelly Fraction)

**ADR-0010 established T4 Kelly = 0.20** for monolithic T4, anchored to σ_λ = 0.50 (Q4 reference) and justified for Q3/Q4 execution only.

**This ADR supersedes ADR-0010 for T4 only.** T1/T2/T3/T5 fractions from ADR-0010 are unchanged.

**What replaces T4 Kelly = 0.20:** The per-sub-band Kelly framework above. T4-PROJ in LATE regime (36–44 min elapsed) has the same derivation basis as the original T4 = 0.20 — this is where the monolithic value lived. The ADR-0010 anchor (0.20 at σ_λ = 0.50) remains the reference for T4-PROJ LATE regime; other sub-bands derive from it.

**Code change required:** `execution_bands.py` BAND_CONFIGS for `T4_IN_PLAY` → split into 10 sub-band entries (T4-MICRO excluded; ADR-0030). The `kelly_fraction` field for each sub-band either reflects its EXP-derived value (when available) or the placeholder from this ADR.

### Amendment 2 — ADR-0014 (T4 Decision Tree Section)

**ADR-0014 §T4** specified monolithic T4 decision tree mechanics. The ADR-0029 T4-PROJ sub-band specification supersedes ADR-0014 §T4 in full.

**What carries forward from ADR-0014 §T4:**
- Bayesian game-state update as the model class (now T4-PROJ specifically)
- ADR-0021 incremental delta materiality gate (applies to T4-PROJ materiality gate)
- T4 pool isolation semantics (ADR-0022 realized-value exit credit)
- Fee-adjusted edge gate (ADR-0016 applies to all T4 sub-bands)

ADR-0014's T1/T2/T3/T5 sections are unchanged.

### Amendment 3 — ADR-0018/ADR-0019 (T4 Noise Buffer)

**ADR-0019 established NOISE_BUFFER_BAND_T4 = 0.19** (EXP-019B/C empirical, G4 n=1,199 positions) for monolithic T4.

**This ADR supersedes the single T4 buffer with per-sub-band buffers.** The 0.19 value is provisionally inherited by T4-PROJ and T4-FLOW (the sub-bands closest to the original T4 behavior). All other sub-bands require EXP re-derivation.

**EXP requirement:** EXP-019D (or equivalent) must re-derive noise buffers per sub-band using the EXP-019A analytical framework: `NOISE_BUFFER = max(2×σ_p_at_firing_window, EXIT_NET_COST_at_sub_band)`. The `σ_p_at_firing_window` for T4-EVENT differs significantly from T4-PROJ because they fire at different game phases with different λ uncertainty.

---

## New Governance Gaps Registered (This ADR)

**GG-038 — T4 Kill Switch SLA (Phase 8 Prerequisite)**
Current NFR-03 kill switch SLA = ≤60 seconds. At Kalshi 60 calls/min, 60 seconds = 60 additional bets after kill trigger. T4 continuous evaluation requires ≤5s kill switch for T4 band and all T4 sub-bands independently. HIGH severity pre-Phase 8. Resolution: new ADR amending NFR-03 for T4 + C7 implementation of fast-halt mechanism.

**GG-039 — T4 Price Cache / Staleness Check Architecture (Phase 8 Prerequisite)**
Layer 2 staleness check requires current Kalshi market prices per queued bet. Venue constraint: `max_api_calls_per_decision = 0` for T4. Resolution: separate read-only price polling loop (not counted against execution rate budget) writing to in-memory cache. Cache staleness window per sub-band defined above. Design ADR required before Phase 8.

**GG-040 — T4 Real-Time Data Sources (Phase 8 Prerequisite)**
T4 sub-bands require data feeds not in the current C1 architecture:
- Live box score with ≤2s event detection latency (T4-EVENT, T4-ARITH)
- Live play-by-play / lineups API with ≤5s substitution detection (T4-LINEUP)
- Kalshi tick-level market price feed (T4-SENTIMENT; the tick/order-book feed for T4-MICRO is an ADR-0030 prerequisite, not tracked here)
Current C1 uses ESPN scoreboard API for box scores (multi-minute latency). Phase 8 C1 rebuild required. Severity: HIGH pre-Phase 8. Low now — Phase 8 is not imminent.

---

## EXP Requirements Before Activation (Per Sub-Band)

No sub-band activates with unresolved "EXP-required" markers. The following EXPs must complete before each sub-band receives Phase 8 ACTIVE status:

*(T4-MICRO and EXP-MICRO-01 are carved out to ADR-0030 — no longer part of this gate.)*

| Sub-band | Required EXP | Key question |
|---|---|---|
| T4-STAGED | No new EXP required | T3 signal quality (ADR-0010) applies; fill slippage measurement needed but not a blocker |
| T4-EVENT | EXP-EVENT-01 | Does Kalshi systematically reprice slowly after discrete game events? Measure per tree type. |
| T4-EVENT | EXP-EVENT-02 | Per-tree Kelly derivation: measure signal-specific σ at event time across game phases |
| T4-LINEUP | EXP-LINEUP-01 | Does Kalshi reprice slowly after substitution events? Rotation model validation. |
| T4-FLOW | EXP-FLOW-01 | Context multiplier calibration: foul_trouble_factor, pace_factor, blowout factors |
| T4-FLOW | EXP-FLOW-02 | Persistence threshold validation: is 5+ possessions correct for each tree type? |
| T4-SENTIMENT | EXP-SENT-01 | Can system classify drift as informed vs. noise at better-than-chance accuracy? |
| T4-PROJ | EXP-PROJ-01 | certainty_weight(t) curve shape: does game-phase formula match observed posterior variance? |
| T4-PROJ | EXP-PROJ-02 | convergence_premium derivation: does N-signal convergence actually increase EV? |
| T4-PROJ | EXP-PROJ-03 | Blowout lambda adjustment factors: empirical calibration of desperation/garbage-time factors |
| T4-ARITH | EXP-ARITH-01 | ARITH_ENTRY_WINDOW and T4_ARITH_CONFIDENCE_GATE calibration |
| All sub-bands | EXP-NOISE-01 | Sub-band-specific noise buffer re-derivation (extends EXP-019A/B/C) |
| All sub-bands | EXP-QUEUE-01 | Queue survival rate measurement per sub-band at realistic game event volumes |

---

## T4 Activation Gate (Completes ADR-0028 Placeholder)

The ADR-0028 T4 Activation Gate section carried: "DESIGN INCOMPLETE — T-179 REQUIRED FIRST." This ADR is the T-179 output. The placeholder is replaced with the following formal gate.

**The T4 Activation Gate must be satisfied before any T4 sub-band strategy is promoted from BLOCKED to ACTIVE.** It is independent of G6 — G6 may close before this gate opens.

For the T4 Activation Gate to clear for a given sub-band, ALL of the following must be satisfied for that sub-band:

1. **Infrastructure prerequisites** — GG-038 (T4 kill switch ≤5s) RESOLVED; GG-039 (price cache) RESOLVED; GG-040 (real-time data sources) RESOLVED
2. **Sub-band EXP prerequisites** — All EXPs in the table above for that sub-band must be COMPLETED with CONFIRMED_POSITIVE or ACCEPTABLE results
3. **Statistical floor** — ≥50 eligible bets AND ≥5 game nights of resolved T4 sub-band paper data (from Phase 8 paper mode)
4. **T4 Tier 2 (ADR-0028 Mod 6)** — T2-A (≤20pp calibration deviation), T2-B (post-haircut EV > 0), T2-C (Brier ≤ 0.265), T2-D (post-haircut P&L slope > 0) — all pass per sub-band independently
5. **T-AGG (ADR-0028 Mod 8)** — Aggregate portfolio EV > 0 and aggregate P&L slope > 0 across all simultaneously active bands
6. **Formal promotion** — BLOCKED→ACTIVE ADR for the specific sub-band strategy + DS sign-off (APR-XXXX)

Sub-bands activate independently. T4-PROJ may activate before T4-FLOW if T4-PROJ's evidence requirements are satisfied first. There is no "T4 must activate as a whole" constraint — the gate is per-sub-band.

---

## Code Changes Required (Post DS Sign-Off)

**No changes may be made until DS sign-off.**

| File | Change | Notes |
|---|---|---|
| `execution_bands.py` | Split `T4_IN_PLAY` into 10 sub-band `ExecutionBand` enum values; add `BandConfig` for each; add `StrategyBandSpec` for each entry sub-band (T4-CORR and T4-EXIT get system-level config objects, not StrategyBandSpec) | T4_IN_PLAY superseded; backwards-compatibility note in docstring. T4-MICRO excluded (ADR-0030). **Gated on Tier A sign-off; per-sub-band roster is Tier B (may change via DECISION_LOG before code lands)** |
| `execution_bands.py` | Add `NOISE_BUFFER` constants per sub-band; mark EXP-required values as provisional | Replaces single `NOISE_BUFFER_BAND_T4` for T4 |
| `execution_bands.py` | Update `VenueBandConstraint` entries for Kalshi: T4 splits into sub-band-specific latency/SLA constraints | T4-PROJ/T4-FLOW can tolerate live API calls; T4-EVENT requires pre-staging or zero calls |
| New: `t4_execution_engine.py` | Layer 1 continuous evaluation engine skeleton; Layer 2 execution queue; staleness check framework; T4-CORR overlay | Phase 8 infrastructure — BLOCKED until GG-038/039/040 resolved |
| New: `t4_price_cache.py` | Read-only Kalshi price polling loop; in-memory cache per market; staleness window enforcement | GG-039 resolution component |
| `c7_monitoring/kill_switch.py` | T4-specific fast-halt mechanism (≤5s SLA) | GG-038 resolution component; requires new ADR |
| `03_DECISIONS/GOVERNANCE_GAP_LOG.md` | Register GG-038, GG-039, GG-040 | Done in this session |

---

## Operator Sign-Off Checklist

**Review checklist:**

*Scoping decisions (SESSION 67) — confirm first:*

- [ ] **Two-tier acceptance model** — Tier A (three-layer architecture, six principles, budget mechanism, gate structure, kill-switch tiers) is frozen on sign-off; Tier B (sub-band roster, all numerics, alpha hypotheses) is provisional/directional and revisable via DECISION_LOG until each sub-band's Activation Gate — understood and acceptable
- [ ] **Strategy-agnostic scaffolding rationale** — building the T4 architecture before alpha is demonstrated is accepted because the machinery is reusable regardless of which edge survives; "beat the situation, not the market" is the organizing discipline; edge/alpha math remains a separate workstream (T-177) — acceptable
- [ ] **T4-MICRO carve-out** — removed from this taxonomy and forwarded to ADR-0030 (no `model_p`; distinct strategy class) — acceptable
- [ ] **DS quote attribution** — the "arbitrary band segments" blockquote is a reconstructed paraphrase (handoff line 23), not verbatim; confirm or correct — acknowledged

*Architecture (Tier A):*

- [ ] Three-layer architecture (continuous evaluation → staleness-arbitrated queue → immediate C5) — acceptable
- [ ] Immediate execution principle (no execution time mandates; staleness check is the gate) — acceptable
- [ ] Ten sub-bands, organized by information class — taxonomy directionally correct (Tier B; DS may redirect on specific sub-bands without a superseding ADR)
- [ ] T4-STAGED counted as T4 budget, T3 signal quality — acceptable
- [ ] T4-EVENT alpha hypothesis requires EXP confirmation before activation — acceptable
- [ ] T4-LINEUP cascading multi-market exposure per lineup event — acceptable
- [ ] T4-FLOW multi-tree structure (FLOW-FOUL, FLOW-PACE, FLOW-ROTATION, FLOW-BLOWOUT) — acceptable
- [ ] FLOW-BLOWOUT as primary carrier of blowout-context consequences on individual markets — acceptable
- [ ] T4-SENTIMENT lower confidence; EXP-required before activation — acceptable
- [ ] T4-PROJ dynamic Kelly framework (game-phase dependent; extends ADR-0010 methodology) — acceptable
- [ ] **T4-PROJ NEAR-CERTAIN Kelly** — inverse-variance formula breaks down at low σ_λ (yields 0.526); NEAR-CERTAIN sizing held provisionally ≤ 0.167 pending EXP-PROJ-01 tail-calibration confirmation; 0.25 is a hard ceiling, not a derived value — acceptable
- [ ] T4-PROJ BLOWOUT-POSTERIOR regime (bidirectional edge; trailing/leading star adjustments) — acceptable
- [ ] T4-ARITH as pre-T5 near-certainty sub-band; provisional 0.22 Kelly held non-operational pending EXP-ARITH-01 tail calibration — acceptable
- [ ] T4-BOUNDARY structural reset (exits + halftime overlay + new entry scan) — acceptable
- [ ] T4-CORR downward-only invariant (cannot increase C4-approved sizes) — acceptable
- [ ] T4-CORR convergence signal (N mechanistically independent signals → convergence premium) — acceptable
- [ ] T4-EXIT continuous position management (reversal + noise buffer + time-based floor) — acceptable
- [ ] Budget: T4_BAND_WEIGHT = 0.27 aggregate unchanged; shared pool with per-sub-band caps — acceptable
- [ ] ADR-0010 T4 amendment (dynamic game-phase Kelly replaces monolithic 0.20) — acceptable
- [ ] ADR-0014 T4 section superseded; T4-PROJ carries forward decision tree methodology — acceptable
- [ ] ADR-0018/ADR-0019 T4 noise buffer superseded by per-sub-band derivation; 0.19 provisionally inherited by T4-PROJ/T4-FLOW — acceptable
- [ ] GG-038 (T4 kill switch ≤5s) registered; Phase 8 prerequisite — acceptable
- [ ] GG-039 (T4 price cache) registered; Phase 8 prerequisite — acceptable
- [ ] GG-040 (T4 real-time data sources) registered; Phase 8 prerequisite — acceptable
- [ ] ADR-0028 T4 Activation Gate placeholder completed by this ADR — acceptable
- [ ] All numeric values marked provisional/EXP-required are understood to be non-operational until the named EXP completes — acceptable

**Sign-off:** _______________  
**Date:** _______________  
**Role:** DS — Earl Ignacio
