# ADR-0036 — Phase 8 Partial Activation: Paper Trading Exemption for Data-Sufficient Sub-Bands

**Status:** ACCEPTED — DS sign-off (Earl Ignacio, 2026-06-30 SESSION 104)
**Registered by:** DS (Earl Ignacio)
**Drafted:** 2026-06-30
**Accepted:** 2026-06-30 SESSION 104
**Amends:** ADR-0029 (Phase 8 activation gate criteria — paper trading context only)
**Completes:** Partial resolution of GG-040 (data-sufficient sub-bands); paper-trading exemptions for GG-038, GG-039
**New governance gaps:** None

---

## Context

ADR-0029 established the T4 sub-band architecture (10 sub-bands by information class) and set Phase 8 as the activation gate for the full `t4_execution_engine.py` implementation. The file-level guard `_PHASE8_ACTIVE = False` blocks all sub-band routing. Three governance gaps were registered as uniform Phase 8 prerequisites — meaning ALL sub-bands were blocked until ALL three gaps were resolved:

- **GG-038** (T4 Kill Switch SLA): NFR-03 requires kill switch ≤60s. Continuous T4 polling makes 60s too coarse; the gap registered a need for T4FastHalt (≤5s mechanism).
- **GG-039** (T4 Price Cache): Continuous evaluation requires current market prices at each cycle. The gap registered a need for a dedicated price cache service distinct from the polling loop.
- **GG-040** (T4 Real-Time Data Sources): Various sub-bands require data infrastructure not yet built. The gap registered this as a uniform Phase 8 blocker without distinguishing which sub-bands were affected.

SESSION 104 strategic review (operator: Earl Ignacio) challenged the uniform Phase 8 block. Two questions were put to the architectural record:

1. Are these gaps valid paper trading blockers, or are they live capital concerns that do not apply to a paper trading context?
2. Does GG-040's blocking condition apply uniformly to all sub-bands, or does it apply selectively based on each sub-band's data requirements?

This ADR records the ruling on both questions and authorizes the partial Phase 8 activation that follows from it.

---

## Decision

### GG-038 — NOT a valid paper trading blocker

T4FastHalt (≤5s halt mechanism) was built in `t4_live_runner.py` as SESSION 71 work. The implementation-level problem GG-038 described was resolved before this ADR was written. GG-038 was registered against a system where the ≤5s mechanism didn't yet exist; it survived as a Phase 8 blocker because the governance document wasn't updated to reflect the build.

The paper trading context does not require a different kill switch SLA than live trading. NFR-03's ≤60s requirement applies to paper as well — and T4FastHalt (≤5s) already satisfies it. There is no paper-specific relaxation here; the requirement is met, and it was met before this ADR was written.

**Ruling:** GG-038 does not block Phase 8 activation for paper trading. The gap remains OPEN until T4FastHalt is formally validated in production (confirmed live, timed, logged). See GG-038 update.

### GG-039 — NOT a valid paper trading blocker

The T4 evaluation loop fetches Kalshi prices via `fetch_player_points_markets()` as part of each polling cycle (every 45–90 seconds). This provides a fresh price snapshot at the start of `_run_cycle()`. T4-PROJ and T4-ARITH need `market_implied_probability` at the moment of evaluation to compute `gross_edge = model_p - market_implied_probability`. The 45s polling cadence provides this.

A dedicated price cache (a separate process maintaining sub-second price freshness) would improve the latency of price data within each cycle, but it is not a prerequisite for the current data-sufficient sub-bands to function correctly. The edge signal computed against a 45s-old price is still the correct architectural computation — it reflects the most recent Kalshi ask the bot has observed. The gap's concern is about freshness degradation within a cycle; for paper trading purposes, this is an optimization target, not a correctness requirement.

**Ruling:** GG-039 does not block Phase 8 activation for paper trading. The gap remains OPEN as a live capital optimization — a price cache may be required before live capital deployment to ensure edge computations reflect current market depth. See GG-039 update.

### GG-040 — VALID, but only for data-deficient sub-bands

GG-040's blocking condition is: the sub-band cannot function without data infrastructure that does not currently exist. This is true for some sub-bands and false for others. The gap's uniform block was an architectural overstatement — it conflated sub-bands that can run on current data with sub-bands that cannot.

Evaluation by sub-band:

| Sub-Band | Data Required | Available Now? | Blocked by GG-040? |
|----------|--------------|---------------|---------------------|
| **T4-PROJ** | In-game batter stats (H, AB, inning, batting slot), game phase | ESPN scoreboard + Kalshi polling | **NO — UNBLOCKED** |
| **T4-ARITH** | Rolling hit rate over recent at-bats, game context | ESPN scoreboard + Kalshi polling | **NO — UNBLOCKED** |
| **T4-FLOW** | Live score differential, inning | ESPN scoreboard | **NO — UNBLOCKED** |
| **T4-BLOWOUT** | Live score gap | ESPN scoreboard | **NO — UNBLOCKED** |
| **T4-EVENT** | Pitch-level or at-bat-level event stream | Not available from ESPN scoreboard | **YES — REMAINS GATED** |
| **T4-LINEUP** | Confirmed in-game lineup state (batting order live updates) | Dedicated lineup feed not integrated | **YES — REMAINS GATED** |
| **T4-MICRO** | Order-book spread and depth data | Not built (ADR-0030 carve-out) | **YES — REMAINS GATED** |
| **T4-SENTIMENT** | Real-time sentiment signal feed | Not built | **YES — REMAINS GATED** |

**Ruling:** GG-040 blocks T4-EVENT, T4-LINEUP, T4-MICRO, and T4-SENTIMENT from Phase 8 activation. T4-PROJ, T4-ARITH, T4-FLOW, and T4-BLOWOUT are unblocked — their data requirements are satisfied by the current ESPN scoreboard + Kalshi polling infrastructure. Partial resolution of GG-040 is documented under that gap.

---

## Sub-Band Activation Matrix (Phase 8 Paper Trading)

| Sub-Band | Paper Trading Status | Basis |
|----------|---------------------|-------|
| T4-PROJ | **ACTIVATE** | GG-038 exempt, GG-039 exempt, GG-040 unblocked |
| T4-ARITH | **ACTIVATE** | GG-038 exempt, GG-039 exempt, GG-040 unblocked |
| T4-FLOW | **ACTIVATE** | GG-038 exempt, GG-040 unblocked |
| T4-BLOWOUT | **ACTIVATE** | GG-038 exempt, GG-040 unblocked |
| T4-EVENT | **REMAIN GATED** | GG-040 active — requires pitch event stream |
| T4-LINEUP | **REMAIN GATED** | GG-040 active — requires dedicated lineup feed |
| T4-MICRO | **REMAIN GATED** | GG-040 active — ADR-0030 carve-out, requires order-book data |
| T4-SENTIMENT | **REMAIN GATED** | GG-040 active — requires sentiment feed |

---

## Implementation Prerequisite

**T-209 must be resolved before `_PHASE8_ACTIVE` is set in `t4_execution_engine.py`.**

Two concurrent T4 MLB sessions were identified in SESSION 103 (CE494B3A from 06:30 UTC + B7193041 from 22:05 UTC) simultaneously hitting the Kalshi API. This doubles rate-limit pressure. Under Phase 8, each cycle will route through more sub-bands and generate more Kalshi API calls per cycle. Activating Phase 8 with dual concurrent sessions would amplify this pressure and contaminate early Phase 8 evaluation data.

The systemd service configuration must be corrected (T-210, which supersedes the T-209 investigation) to ensure only one T4 runner is active per game day before Phase 8 activation. The code change (T-211) is unblocked only after T-210 is confirmed complete.

---

## Governance Impact

1. **GG-038** — Paper-trading exemption note added. T4FastHalt (≤5s) already built in `t4_live_runner.py` SESSION 71. Not a blocker for paper trading activation. Remains OPEN until formally validated in production (timed + logged under real game load).

2. **GG-039** — Paper-trading exemption note added. 45s Kalshi polling provides sufficient price freshness for T4-PROJ/ARITH edge computation in paper mode. Remains OPEN as a live capital optimization — a dedicated price cache may be required before live capital deployment.

3. **GG-040** — Partial resolution documented. Data-sufficient sub-bands (T4-PROJ, T4-ARITH, T4-FLOW, T4-BLOWOUT) are now unblocked for paper trading. Data-deficient sub-bands (T4-EVENT, T4-LINEUP, T4-MICRO, T4-SENTIMENT) remain gated until their respective data infrastructure is built. GG-040 status changes from "Phase 8 prerequisite — all sub-bands blocked" to "partial — data-deficient sub-bands blocked; data-sufficient sub-bands unblocked."

---

## Tasks Registered

- **T-210** (supersedes T-209): Fix dual concurrent T4 MLB sessions — systemd service must kill stale sessions on restart; only one T4 runner active per game day.
- **T-211**: Phase 8 partial activation code — set `_PHASE8_ACTIVE = True` for T4-PROJ, T4-ARITH, T4-FLOW, T4-BLOWOUT in `t4_execution_engine.py`; keep T4-EVENT, T4-LINEUP, T4-MICRO, T4-SENTIMENT gated. Code change blocked on T-210 completion.

---

## DS Sign-Off

DS sign-off (Earl Ignacio, 2026-06-30 SESSION 104)
