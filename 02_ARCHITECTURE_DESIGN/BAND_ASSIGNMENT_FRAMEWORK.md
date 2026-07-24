# Band Assignment Framework — Structural Time-Horizon Protocol

**Purpose:** Governance specification for how every quantitative strategy (A–K) is assigned to, validated in, and constrained by the T1–T5 execution band framework. This document makes band assignment a structural requirement — not a documentation convention — across strategy additions, modifications, and removals.
**Owner (role):** Architecture Owner (AO) + Director/Sponsor (DS)
**Status:** CANONICAL (2026-05-29)
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: verified current, no new drift found. Cross-checked against EXECUTION_BANDS.md's Live Registry (NBA T2/T3 still SKELETON, matches this document's registry table), TODO_NEXT.md (T-077/Polymarket KYC still pending, so Strategy E stays SKELETON; APR-0010 still unsigned, so Strategy C stays BLOCKED), and DECISION_LOG.md (EXP-014's +7.8% max EV citation and APR-0013's kill-switch pass both still accurate). This document's own 2026-07-02 scope note already correctly confines it to NBA-only (Strategies A–K); MLB's separate T4M sub-band registry is out of scope by design, not by omission.
**Next review:** 2026-08-23, or on any new strategy addition/removal, venue activation, or NBA reactivation ahead of the 2026-27 season
**Staleness triggers:** Strategy added/removed; new venue activated; band parameter revised (Kelly, SLA, compute); evidence experiment invalidates a band placement
**Upstream links:** EXECUTION_BANDS.md (band definitions); ARB_FRAMEWORK.md (arb decision trees); STRATEGY_OVERVIEW.md (strategy mechanics); VENUE_REGISTRY.md (venue params)
**Downstream links:** execution_bands.py (StrategyBandSpec, BandRegistry, VenueBandConstraint); execution_bands_orchestrator.py (ArbBandSignal, routing); CHANGE_CONTROL.md (band assignment as governed change)
**Decision references:** ADR-0002 (strategy class); ADR-0003 (venue selection); ADR-0004 (model class + Kelly); EXECUTION_BANDS.md
**Confidence:** 9/10 — Protocol is structurally complete; T2/T3 evidence gaps are known and registered
**Decisions logged:** true — Key structural decisions captured in DECISION_LOG.md (2026-05-29: band assignment as governed requirement; StrategyBandSpec as mandatory interface; VenueBandConstraint feasibility as gate; T2/T3 activation requires EXP evidence; ArbBandSignal schema separation)

---

## ⚠️ Scope Note (2026-07-02 documentation-remediation pass)

This document's "Current Band Registry — All 11 Strategies" table and all P1–P7 analysis below are **NBA-only** (Strategies A–K registered in the original `BAND_REGISTRY`/`execution_bands.py`) and predate MLB. MLB's band registry is a **separate registry** — `T4_MLB_SUBBAND_REGISTRY`/`T4_MLB_SUBBANDS` in `execution_bands.py` (added under ADR-0039, additive-only, does not touch the NBA registry this document describes). This document was not extended to cover it. If MLB ever needs a comparable Band Assignment Protocol treatment, that is new work, not an update to this file. Not independently re-verified against current NBA code in this pass beyond the T2/T3-SKELETON-in-production observation below, which remains accurate (NBA cron is dark/tabled, not removed).

---

## PDTP Problem Brief

**Decision statement:** A decision will be made by AO + DS on how to structurally enforce time-horizon band assignment for all quantitative strategies — such that every strategy addition, modification, or removal requires explicit band specification, evidence validation, venue-level feasibility checking, and fallback chain definition.

**The core problem:** The T1–T5 framework exists as documentation and partial code (Strategy A only). It is not a structural protocol. A new strategy can be added without specifying its band. Band assignments are not validated against evidence. Venue constraints (API latency, rate limits, simultaneous_legs support) are not checked before execution. Arb strategies (C, D, E) have no code representation in the orchestrator. Compute budgets are targets, not enforced limits.

**Scope:** All 11 strategies (A–K) + sizing components (G) + risk envelope (H). All current and future venues (V-001–V-005+). All phases (6–9+).

---

## PDTP Pass 1 — Deconstruction

| ID | Subproblem | Method | Done condition |
|----|-----------|--------|----------------|
| P1 | What does "structurally built" mean? | Implementation gap analysis vs. current code | Every gap identified; code change specified |
| P2 | Band assignment criteria — what qualifies a strategy for a band? | Formal criteria definition | Unambiguous criteria; any strategy can be evaluated |
| P3 | Evidence requirements — what validates a band placement? | Evidence taxonomy per band | EXP requirement per band specified |
| P4 | Venue-level technical constraints (the braces) | Feasibility math per venue per band | Constraint model defined; Kalshi T3 latency resolved |
| P5 | Fallback chains — what happens when a band fails? | Failure mode enumeration | Fallback defined per strategy |
| P6 | Arb signal routing — how do arb strategies integrate? | Schema analysis | Separate signal type; routing extension defined |
| P7 | Governance — how are band assignments controlled? | Change control integration | Mandatory protocol in CHANGE_CONTROL.md |

---

## PDTP Pass 2 — Sequential Execution

### P1: What "Structurally Built" Means

**Current state:**
- `BAND_CONFIGS`: defines T1–T5 parameters (compute, SLA, Kelly, pipeline) ✅
- `BandSignal` / `BandDecision`: data schema for model-edge signals ✅
- `MultiBandOrchestrator`: P6 interaction rules for Strategy A ✅
- Strategy B–K: no code representation in band system ❌
- Venue constraints: not checked before execution ❌
- Compute budgets: documentation only; not enforced at runtime ❌
- Band assignment: not validated against evidence ❌
- Arb signals: incompatible schema with existing orchestrator ❌

**What "structurally built" requires:**
1. `StrategyBandSpec` — per-strategy declaration of bands, evidence basis, signal type, fallback
2. `BandRegistry` — centralized map of all strategy specs; validates on import
3. `VenueBandConstraint` — per-venue feasibility at each band (latency, rate limits, simultaneous_legs)
4. `ArbBandSignal` / `ArbBandDecision` — separate schema for arb strategies (multi-leg, net_profit_usd)
5. Compute budget enforcement — runtime timeout mechanism around strategy logic
6. `BandFallbackChain` — defined degradation path per strategy when execution band fails
7. Band assignment as a governance gate — documented in CHANGE_CONTROL.md; no strategy adds/modifies without completing the protocol

---

### P2: Band Assignment Criteria

A strategy qualifies for assignment to band Tx if ALL four criteria are met:

| Criterion | Definition | Test |
|-----------|-----------|------|
| **C1 — Compute fit** | Full decision tree completes within `BandConfig.max_compute_ms` | Measured in dev environment; margin ≥ 20% |
| **C2 — SLA achievable** | `venue.api_latency_ms` + compute_ms + order_submission_ms ≤ `BandConfig.execution_sla_s × 1000` | Per venue; verified against VenueBandConstraint |
| **C3 — Signal exists** | There is a meaningful signal to compute at this time horizon | Defined signal source; not "we'll add data later" |
| **C4 — Evidence basis** | An EXP or backtest validates the signal quality at this horizon | EXP-NNN reference required; "theoretical" is not sufficient for ACTIVE status |

**Partial qualification — SKELETON status:**  A strategy may be registered in a band at SKELETON status if C1–C3 are met but C4 (evidence) is absent. SKELETON status means: code exists; pipeline runs; decisions are logged but not executed. Promotion from SKELETON → ACTIVE requires C4 evidence.

**Evidence threshold for ACTIVE promotion:**  Minimum: one EXP with ≥100 samples, positive EV or Brier improvement ≥ 0.001 at the band's time horizon specifically (not just at T1).

---

### P3: Evidence Requirements by Band

| Band | Evidence required for ACTIVE | Current state |
|------|------------------------------|---------------|
| T1 | EXP with ≥100 bets at 12-48h horizon; positive EV after vig | ✅ EXP-010: 871 bets, +$0.0958/bet (Strategy A only) |
| T2 | EXP confirming injury/lineup overlay adds Brier improvement ≥ 0.001 at 4-8h horizon | ❌ EXP-012 falsified injury signal at current scale; T2 SKELETON only |
| T3 | EXP or walk-forward test confirming CONFIRM/FADE momentum signal improves win rate vs T1-only | ❌ No EXP exists; T3 SKELETON only |
| T4 | Live paper bets (not backtest — no historical in-play data) showing positive EV | ❌ Phase 8+; no evidence possible until real-time infra |
| T5 | Mathematical derivation sufficient (arithmetic certainty is not probabilistic); but kill switch SLA must be validated < 5s | ❌ Phase 8+; kill switch SLA currently 60s (12× too slow) |

**Critical gap — T2 and T3 are SKELETON, not validated:**  The momentum signal (T3) and injury overlay (T2) are running as skeletons on the VPS cron. They produce signals but these signals are unvalidated. This is acceptable for paper trading (the paper bet is already determined by T1; T2/T3 are overlays). But it must be explicitly registered — T2 and T3 are SKELETON status, not ACTIVE, and must not be represented as validated strategies.

---

### P4: Venue-Level Technical Constraints (The Braces)

The "braces" are the per-venue, per-market, per-order constraints that determine whether the designed band is actually achievable in production.

**Per-Venue:**

| Venue | API latency (est.) | T3 achievable? | T4 achievable? | Notes |
|-------|-------------------|---------------|----------------|-------|
| V-001 Kalshi | 200–500ms | ⚠️ Borderline | ❌ Without pre-staging | T3 budget = 500ms; latency consumes 40–100% |
| V-002 Polymarket | TBD | TBD | TBD | Must measure after T-077 provisioning |
| V-003 PrizePicks | TBD | N/A (not real-time) | N/A | Bookmaker-fixed; no live price feed |
| V-004/V-005 | TBD | N/A | N/A | Same as V-003 |

**Kalshi T3 resolution:**  At 200ms latency, the T3 decision tree must be: fetch_current_ask() [200ms] → compare_to_cached_T1() [<1ms] → output_signal() [<1ms] = ~202ms total. This fits within 500ms. At 500ms latency, it consumes 100% of budget with no margin. **The T3 implementation must be a single API call only — no second call, no recomputation, no model inference.** This is already the design (reads cached T1 + one live price) but must be enforced as a hard constraint.

**Per-Market:**

| Constraint | Definition | Implication |
|-----------|-----------|-------------|
| Market depth | Volume available at ask_price | Large Kelly bets at T3/T4 move the market mid-execution; effective edge compresses |
| Market hours | Some markets close before tip-off | T3 window may be ≤15 min for late-opening markets |
| Market liquidity tier | Kalshi KXNBAPTS: low-medium (EXP-004 37 markets) | Position cap critical; $500/bet cap from ADR-0004 prevents full Kelly on thin markets |

**Per-Order:**

| Order size | Band compatibility | Issue |
|-----------|--------------------|-------|
| < $50 | All bands | No market impact; all SLAs achievable |
| $50–$200 | T1/T2/T3 | Moderate impact on thin Kalshi markets; T3 feasible |
| $200–$500 | T1/T2 | Market impact requires modeling; T3 compute budget insufficient for impact adjustment |
| > $500 | T1 only | Hard limit per ADR-0004 hard limits; $500 cap prevents this case |

**Conclusion:** The $500/bet cap from ADR-0004 is a de facto band constraint — it prevents orders where market impact modeling would be required, keeping all orders within T1/T2/T3 feasibility.

---

### P5: Fallback Chains

When a band's execution fails (API timeout, venue down, compute budget exceeded), the system must have a defined fallback. No fallback = silent failure or unhandled exception.

| Strategy | Primary band | Fallback | Logic |
|----------|-------------|---------|-------|
| A | T3 (if CONFIRM) | T2 sizing, then T1 sizing | T3 failure → use T2 if available; else T1 |
| A | T2 | T1 | T2 unavailable → proceed at T1 |
| A | T1 | PASS (skip market) | T1 failure = no signal; do not bet |
| C | T3 execute | Re-queue for next T3 scan (15 min) | Do NOT fall back to T1 execution; lock windows don't persist |
| C | T4 execute | T3 execute | Pre-staged orders fall back to T3 verification |
| D | T2 | T1 | z-score refresh fails → use cached T1 OU estimate |
| D | T1 | PASS | OU estimation fails → skip pair |
| E | T3 live route | Use T1 cached routing table | API timeout → route to cached best venue from T1 scan |
| E | T4 cached route | T3 live route | Routing table stale → re-fetch |

**Fallback invariant:** Fallback always degrades gracefully — it never escalates to a more aggressive action. T3 failure → T2; T2 failure → T1; T1 failure → PASS. No fallback should bet when the primary band has failed; it may only degrade to a more conservative decision.

---

### P6: Arb Signal Routing — Schema Separation

The existing `BandSignal` / `BandDecision` is incompatible with arb strategies:

| Field | Model-edge (Strategy A) | Arb (C, D, E) |
|-------|------------------------|---------------|
| `direction` | YES / NO / PASS | YES+NO (C); LONG/SHORT spread (D); route (E) |
| `edge` | p̂ − mid_price | net_profit_usd / fill_probability |
| `p_estimate` | calibrated probability | not applicable |
| `legs` | single leg | 1–2 legs (C/D); N venues (E) |

**Required: separate `ArbBandSignal` and `ArbBandDecision` schemas.** The `MultiBandOrchestrator` routes by signal type:
- `BandSignal` → model-edge routing (existing P6 rules)
- `ArbBandSignal` → arb routing (new — strategy-specific execution via ArbOpportunityLog)

The orchestrator is the single entry point; downstream routing differs by signal type.

---

### P7: Governance — Band Assignment as Controlled Change

Band assignment decisions have the same governance weight as Kelly fraction changes or gate criteria revisions. They affect what code runs, when, at what position size.

**Every strategy addition or modification must complete the Band Assignment Protocol:**

1. **Declare** — fill in `StrategyBandSpec` (bands, signal_type, evidence_basis, fallback_chain)
2. **Validate evidence** — reference a specific EXP-NNN or SKELETON if unvalidated
3. **Check venue constraints** — run `VenueBandConstraint.is_achievable()` for all registered venues
4. **Register** — add to `BandRegistry` in execution_bands.py
5. **Log decision** — DECISION_LOG.md entry for the assignment
6. **Set decisions_logged** — if a new document is created, set field per CHANGE_CONTROL.md

The CHANGE_CONTROL.md "What Requires an ADR" table must include: "New band assignment or change to existing band assignment (strategy moves bands or evidence invalidates a placement)."

---

## PDTP Pass 3 — Synthesis

### Cross-Domain Connections

1. **P2 + P3 → T2/T3 are mis-labeled:** Current EXECUTION_BANDS.md shows T2 and T3 as "SKELETON" but they are running on the VPS cron. The `phase_active` field in code says "Phase 7" for T2/T3 but PIPE-06 (T3) is actually deployed. The system is running unvalidated strategies in production. This is acceptable only if their outputs are LOGGED but not EXECUTED — which is currently true (paper bets are T1-driven; T3 is overlay). Must remain true until EXP validates them.

2. **P4 Kalshi latency + T3 → single-call rule is non-negotiable:** The 500ms T3 budget with 200–500ms Kalshi latency means T3 must be a single-API-call operation. Any code path that adds a second API call at T3 is a spec violation. This must be enforced structurally, not just as a convention.

3. **P5 fallback + P6 arb routing → complement lock has no T1 fallback:** Unlike Strategy A, which degrades from T3 → T1, a complement lock opportunity has no fallback. If the T3 verify-and-fire fails, the opportunity expires — you cannot "fall back" to T1 pricing and place a lock bet 12 hours earlier. The fallback for C is: re-queue for next T3 scan. This means C requires more robust T3 execution than A, not less.

4. **P3 evidence gaps + P7 governance → StrategyBandSpec must carry status:** SKELETON and ACTIVE are meaningfully different. SKELETON strategies produce signals but don't execute. This must be machine-readable (a field in `StrategyBandSpec`), not just a documentation convention. Otherwise a future code change could accidentally activate an unvalidated strategy.

### Contradiction Scan

| Claim A | Claim B | Resolution |
|---------|---------|------------|
| T3 is PIPE-06 "active skeleton" on VPS | T3 has no EXP validation | No contradiction: paper bets are T1-derived; T3 is overlay-only. But must remain overlay-only until validated. |
| T5 Kelly (0.15) > T4 Kelly (0.05) | Shorter horizon = less confidence = lower Kelly | Resolved in EXECUTION_BANDS.md: T5 is arithmetic certainty, not probabilistic. The general rule holds for probabilistic bands only. |
| Strategy C execution is T3/T4 | C is blocked until APR-0010 | No contradiction: the framework registers C's intended bands; APR-0010 is the activation gate. Registered ≠ activated. |
| VenueBandConstraint for T3 is "borderline" on Kalshi | T3 is designed and deployed | Resolution: T3 deployment is sound if (a) single API call only; (b) latency is measured empirically (add latency logging to PIPE-06); (c) timeout handling sends to T1 fallback. |

---

## PDTP Pass 4 — Blind Spots + Adversarial Critique

**1. The unvalidated-skeleton problem:**
T2 and T3 are running on VPS cron without backtest evidence. If a future sprint activates paper bets at T2/T3 sizing (rather than T1-only), unvalidated signals will determine real-money position sizes. The SKELETON status flag in `StrategyBandSpec` is the only guardrail. It must be code-level (raises an exception if SKELETON strategy tries to execute a bet), not documentation only.

**2. Compute budget is aspirational:**
`BandConfig.max_compute_ms = 500` for T3 is documented but not enforced. If a future developer adds a second feature computation to the T3 pipeline, the budget can silently overflow with no warning. A compute timeout (Python `signal.alarm` or thread timeout) would catch this in dev/test before it reaches the VPS.

**3. Correlation between arb and model-edge on the same API key:**
Strategy A (T1, PIPE-02) and Strategy C scanner (T1, future) share the Kalshi API key. If both run simultaneously, they compete for rate limits. API rate limit contention is not modeled anywhere. With 37 markets (EXP-004) and a rate limit of N calls/min, a simultaneous T1 scan (Strategy A) + complement lock scan (Strategy C) may exceed the limit and cause both to fail silently.

**4. The pre-staging gap at T4:**
For T4 execution, orders must be pre-staged at T3. But if T3 is on a 15-min cron and T4 is event-driven (real-time game feed), there's a window between cron firing and event trigger where pre-staged orders could be stale. A complement lock opportunity at T=+14min after last cron could use T3 prices from 14 minutes ago. Need a "pre-staged order freshness" TTL.

**5. Band remediation difficulty:**
If evidence invalidates a band assignment (e.g., T3 CONFIRM signal shows no improvement in win rate), changing the assignment requires: updating `StrategyBandSpec`, updating EXECUTION_BANDS.md, logging a DECISION_LOG entry, potentially rewriting pipeline logic. This is not "easy to remediate" without the governance protocol. With it, remediation is: update spec → log decision → disable pipeline → run new EXP.

**Top 3 risks that could break live capital operations:**
1. T2/T3 activated at non-SKELETON status without validation → unvalidated signals drive position sizing
2. Complement lock (C) fires at T3 when APR-0010 is pending → unauthorized trade execution
3. API rate limit contention between Strategy A and Strategy C scanner → both produce corrupted signals silently

---

## PDTP Pass 5 — Decision Extraction

| # | Decision | Canonical reference | Owner |
|---|----------|--------------------|----|
| 1 | `StrategyBandSpec` is a mandatory interface; no strategy is valid without one | `execution_bands.py` BandRegistry | AO |
| 2 | `band_status: SKELETON | ACTIVE` is machine-readable; SKELETON strategies may not execute bets | `StrategyBandSpec.band_status` field | AO |
| 3 | T2 and T3 are SKELETON status until validated by dedicated EXPs | BandRegistry registrations | DS |
| 4 | T3 decision tree is hard-constrained to one API call (Kalshi latency vs. 500ms budget) | `VenueBandConstraint` for V-001 at T3 | AO |
| 5 | `ArbBandSignal` is a separate schema from `BandSignal`; orchestrator routes by signal type | `execution_bands_orchestrator.py` | AO |
| 6 | Band assignment requires evidence (EXP-NNN ref) before ACTIVE status; SKELETON is the holding state | Band Assignment Protocol (Section P7) | DS + AO |
| 7 | Band assignment change (including evidence-invalidated placement) requires DECISION_LOG entry + CHANGE_CONTROL | CHANGE_CONTROL.md | DS |

---

## Current Band Registry — All 11 Strategies

| Strategy | Signal type | Detection band | Execution band | Status | Evidence |
|----------|-----------|---------------|---------------|--------|---------|
| A (ML+EV) | model_edge | T1 | T1/T2/T3 | T1=ACTIVE; T2/T3=SKELETON | T1: EXP-010 ✅; T2/T3: none |
| B (Data Agg.) | model_edge | T1 | T1 | SKELETON (HYP-005 falsified at scale) | None at current N |
| C (Complement Lock) | arb_lock | T1/T2 | T3/T4 | BLOCKED (APR-0010) | None |
| D (Stat Arb) | arb_spread | T1 | T1/T2 | BLOCKED (DS-02 required) | None |
| E (Line Shopping) | arb_route | T1/T2 | T1–T4 | SKELETON (T-077 required) | T1: EXP-014 (+7.8% max EV) ✅ |
| F (Parlays) | model_edge_joint | T1 | T1 | BLOCKED (joint dist. model required) | None |
| G (Kelly Sizing) | sizing | — | All bands | SKELETON → ACTIVE at G6 | ADR-0004 + EXP-010 ✅ |
| H (Risk Limits) | risk_envelope | — | All bands | ACTIVE (kill switch tested APR-0013) | KS-C8D7D90AF942 ✅ |
| I (Poisson/NB) | model_edge | T1 | T1 | SKELETON (EXP-013 incomplete) | None |
| J (Momentum) | momentum | T3 | T3 | BLOCKED (DS-02 required) | None |
| K (In-Play Scalp) | execution_scalp | T4 | T4/T5 | BLOCKED (Phase 8+) | None |

---

## Self-Assessment

**Quality score: 9/10**

| Dimension | Score | Justification |
|-----------|-------|--------------|
| Correctness | 9/10 | All claims grounded in current code (execution_bands.py, orchestrator), experiments (EXP-010, EXP-012), and ADRs |
| Completeness | 9/10 | All 11 strategies registered; all 7 structural gaps identified; all edge cases in Pass 4 enumerated |
| Traceability | 9/10 | Every decision references a code file and location; every status references an EXP or ADR |
| Robustness | 8/10 | T4 pre-staging TTL (blind spot 4) and API rate contention (blind spot 3) are identified but not yet fully mitigated |
| Decision usefulness | 9/10 | Pass 5 extracts 7 concrete decisions; implementation flows directly from this document |

**Weakest point:** T2/T3 validation evidence doesn't exist. These bands are running in production (VPS cron) at SKELETON status with no backtest. This is tolerable now (paper bets are T1-driven) but must not silently upgrade to ACTIVE.
