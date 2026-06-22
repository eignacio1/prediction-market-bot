# ADR-0030 — T4-MICRO: Execution-Quality (No-Model) Strategy Class

**Status:** PLACEHOLDER — registered, NOT drafted, NOT accepted  
**Registered by:** SESSION 67 (2026-06-22), as the carve-out target of ADR-0029  
**Owner (role):** DS — Earl Ignacio  
**Blocks:** Any T4-MICRO / spread-capture / liquidity-provision implementation. Until this ADR is drafted and signed, T4-MICRO does not exist as an executable strategy.

---

## Why this ADR exists

ADR-0029 (T4 Sub-Band Architecture) originally included **T4-MICRO** as one of eleven in-game sub-bands. A pre-sign-off alignment review (SESSION 67) found that T4-MICRO is **structurally a different strategy class** from everything else in T4:

- Every other T4 sub-band is **forecast-edge**: it computes a calibrated `model_p` and bets when `model_p > mip + vig`. That is the project's core commercial thesis.
- T4-MICRO has **no `model_p`**. It is pure order-book spread capture / liquidity provision — *execution quality is the edge*, not forecast accuracy. It is an HFT-class strategy.

Folding a no-model strategy into the forecast bot's T4 band would:
1. Conflate two unrelated edge theses under one activation gate (you could not tell which thesis the evidence was validating).
2. Import HFT-class infrastructure and risk assumptions (sub-millisecond resting-order management, order-book microstructure, adverse-selection/queue-position risk) into a band designed around multi-second model updates.
3. Violate the separation-of-concerns discipline the project already applies to other non-forecast strategy classes: `arb/` is quarantined until APR-0010, and DFS pick'em requires its own ADR before activation. T4-MICRO belongs in the same lane.

**Decision (SESSION 67):** Remove T4-MICRO from ADR-0029 and quarantine it here as its own strategy class. It is **neither approved nor rejected** — it is parked in the correct governance lane so it can be evaluated on its own merits, with its own thesis and its own evidence, if and when it is taken up.

---

## What this ADR must establish before T4-MICRO can be considered

This is a placeholder. A future drafting session must, at minimum, resolve all of the following before T4-MICRO moves from PLACEHOLDER to a draft for sign-off:

1. **Thesis statement** — what is the precise edge claim? (e.g., "Kalshi NBA player-prop order books exhibit capturable bid/ask spread net of fees and adverse selection.") State it as a falsifiable hypothesis.
2. **Strategy-class boundary** — confirm whether a no-model execution-quality strategy is in scope for this project at all, or whether it should be deferred indefinitely like `arb/`. This is a DS-level scope decision, not a technical one.
3. **Activation gate** — its own gate, independent of the ADR-0029 T4 Activation Gate. Forecast-edge gate criteria (calibration, Brier, post-haircut EV vs market) do not apply to a no-model strategy; new criteria are required (spread-capture realized vs expected, fill-rate, adverse-selection cost, inventory risk).
4. **Required EXP** — does Kalshi order-book spread capture clear fees after adverse selection? Measure on real order-book data, not synthetic. (This was provisionally "EXP-MICRO-01" in ADR-0029; renumber/re-scope here.)
5. **Infrastructure prerequisites** — WebSocket / low-latency order-book feed; a dedicated C5 resting-order management module distinct from the new-order submission path; tick-level market data (a component formerly tracked under GG-040, to be re-homed here).
6. **Risk framework fit** — Kelly does not apply without a probabilistic model. Sizing must be derived from spread width, depth, and inventory limits. How does this interact with C4's free-cash invariant (ADR-0026) and the drawdown kill switch? A no-model strategy still consumes capital and must be governed.
7. **Budget home** — if activated, does T4-MICRO draw from the T4 aggregate budget (T4_BAND_WEIGHT = 0.27) or from a separate allocation? It is not obvious that a no-model strategy should share the forecast bands' capital pool.

---

## Status & next step

PLACEHOLDER only. No drafting authorized yet. T4-MICRO is dormant until DS elects to take up this ADR. ADR-0029 proceeds to sign-off with a **10-sub-band** taxonomy and no dependency on this document.

**Cross-references:** ADR-0029 (carve-out source), ADR-0002 / APR-0010 (`arb/` quarantine precedent), ADR-0026 (free-cash invariant), GG-040 (real-time data sources — tick-feed component re-homed here).
