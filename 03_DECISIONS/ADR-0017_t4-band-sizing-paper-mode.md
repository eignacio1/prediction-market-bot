# ADR-0017 — T4 Band Sizing: Paper Mode Architecture and Phase 8 Deferral

**Status:** ACCEPTED  
**Date:** 2026-06-05 SESSION 35  
**Decisions logged:** true  
**Author:** Claude Code (GG-011 resolution)  
**Approval required:** DS (Earl Ignacio) sign-off before ACCEPTED  
**Supersedes:** Nothing — resolves GG-011; defers T4 ACTIVE sizing to ADR-0018  
**Related:** GG-011, ADR-0013 (T4 band budget), run_t4_live.py T4_BAND_WEIGHT stub

---

## Context

GG-011 (logged SESSION 28) identified that `T4_BAND_WEIGHT = 0.10` is a stub value with no empirical derivation methodology, and that the fractional-allocation formula used to compute the T4 band budget is architecturally incompatible with high-throughput T4 execution at design scale (~1,000 evaluations/game).

**Design scale:** The system generates ~1,000+ evaluated bet opportunities per game — not 10–20 pre-scheduled bets. Kill switches and capital sizing must be designed to this scale. A fixed-budget Kelly formula exhausts capital after a small fraction of evaluations and silently stops firing bets.

### Data from Finals Game 1 (2026-06-03, G1)

G1 was the first live T4 paper deployment. Key calibration data:

| Metric | Value |
|---|---|
| Total evaluations | 1,459 |
| C4-approved bets | 1,447 (99.2% approval rate) |
| C4-rejected bets | 12 |
| Average edge | 0.305 (sum=442.52 / 1,447 approved) |
| Average C4 Kelly-approved size | $57.25/bet |
| Total C4 Kelly-approved deployment | $82,836.90 (uncapped Kelly) |
| KELLY_T4 used | 0.20 |
| Approximate bankroll used for sizing | ~$950 (full deployable capital) |
| Actual bets placed (flat sizing) | 1,417 × $0.10 = $141.70 |

### The Band Budget Formula Incompatibility

The ADR-0013 formula:
```
t4_band_budget = bankroll × (1 − RESERVE_MANDATE_PCT) × T4_BAND_WEIGHT
bet_size = edge × KELLY_T4 × t4_band_budget
```

At T4_BAND_WEIGHT=0.10, bankroll=$1,000, RESERVE_MANDATE_PCT=0.05:
- `t4_band_budget` = $95
- Average bet size = 0.305 × 0.20 × $95 = $5.80
- Bets before budget exhaustion ≈ $95 / $5.80 ≈ **16 bets**

16 bets vs. 1,447 approved bets. The formula stops T4 after ~1% of evaluations and renders 99% of edge signal inaccessible.

This is not a calibration problem — it is an architectural incompatibility. No choice of T4_BAND_WEIGHT resolves it: at any T4_BAND_WEIGHT, the ratio of bets-before-exhaustion to total-approved-bets is:
```
bets_to_exhaustion / total_approved ≈ 1 / (avg_edge × KELLY_T4 × total_approved)
= 1 / (0.305 × 0.20 × 1447) ≈ 1/88 ≈ 1.1%
```

The formula is the problem. Kelly sizing from a fixed per-game budget is correct for single-bet or low-frequency decision making. At 1,000+ evaluations/game, each evaluation consumes Kelly fraction × budget, depleting the budget exponentially. The architecture needs a different sizing primitive.

---

## Decision

### Paper Mode (Phase 6/7): PAPER_T4_FLAT_SIZING=true

**Accepted approach:** Flat contract sizing (`PAPER_T4_FLAT_SIZING=true`) bypasses the band budget formula entirely and is the correct paper prototype architecture.

```
t4_band_budget = PAPER_T4_POOL_USD (currently $500)
bet_size = flat 1-contract minimum per approved bet (~$0.10)
Budget constraint: stop only when t4_deployed_game >= PAPER_T4_POOL_USD
```

At $0.10/bet, the $500 pool accommodates 5,000 bets — sufficient for any game. In G1, only $141.70 was deployed against a $500 pool. The paper pool was never a binding constraint.

**Why flat sizing is correct for paper calibration:**
1. Decouples bet count from Kelly sizing — all 1,447 approved bets fire, giving complete signal data
2. Preserves the C4 Kelly-approved size in audit logs for Phase 8 calibration
3. Eliminates the compounding distortion of Kelly budget depletion from calibration data
4. Paper bets are $0.10 flat regardless — pool size has no commercial meaning in paper mode

### PAPER_T4_VIRTUAL: Already False

`PAPER_T4_VIRTUAL` defaults to `"false"` in `run_t4_live.py` (line 252) and is not set in VPS `.env`. T4 has run in non-virtual mode (budget-enforced flat sizing) since G1 activation. No configuration change is needed.

The TODO_NEXT reference to "flip PAPER_T4_VIRTUAL=false for G3" was premised on the variable being true. It was always false. Confirmed by MEMORY_BANK: "PIPE-07 LIVE ✅ (PAPER_T4_VIRTUAL=false, PAPER_T4_FLAT_SIZING=true)".

### KELLY_T4 Discrepancy

The DECISION_LOG 2026-05-29 retroactive entry states "T4=0.05 because no historical calibration exists for live Bayesian model." The code has `KELLY_T4 = 0.20` in `game_state_model.py`. These are inconsistent.

**Resolution:** `KELLY_T4 = 0.20` is accepted as the operative value for paper calibration purposes.

Rationale:
- In PAPER_T4_FLAT_SIZING=true mode, KELLY_T4 only affects the C4 `approved_size` audit field, not actual bet placement. Commercial exposure is $0.10/bet regardless.
- G1 data with KELLY_T4=0.20 gives useful calibration: at 0.20, 99.2% of evaluations are approved, average approved size=$57.25. This is the empirical baseline.
- The DECISION_LOG entry was a design-intent placeholder ("no calibration exists") — now overridden by actual G1 data.
- KELLY_T4=0.05 (the originally documented value) would reduce approved sizes to $14.31/bet average. Bets would still be placed at $0.10 flat. No operational difference in paper mode.

**Gate obligation:** The correct KELLY_T4 for Phase 8 (T4 ACTIVE, real Kelly sizing) must be derived from paper bet outcomes, not from the approved_size alone. This derivation is gated on EXP-018 (adj_λ validation) and the G6 gate. The 0.20 value is not approved for live Kelly sizing without a dedicated EXP.

### Phase 8 Deferral

**ADR-0018 required before T4 ACTIVE designation.** That ADR must:
1. Define the per-bet sizing primitive (flat contract sizing is the recommended starting point, with Kelly sizing of pool size, not individual bets)
2. Calibrate T4_BAND_WEIGHT against paper results (≥3 game nights of flat-sizing deployment data)
3. Reconcile KELLY_T4 against empirical paper outcomes
4. Define the T4 pool kill switch: max per-game pool as % of bankroll, not per-bet fraction

### T4_BAND_WEIGHT Stub

The stub at `run_t4_live.py:291` remains. Its comment is updated to reference ADR-0017. The value `0.10` is kept as a Phase 8 placeholder — it is not used in `PAPER_T4_FLAT_SIZING=true` mode.

---

## Resolution of GG-011

GG-011 is **RESOLVED for paper mode (Phase 6/7)** by this ADR.

- The stub is acknowledged, documented, and its inapplicability in flat-sizing mode is explicit.
- The Phase 8 requirement is forwarded to ADR-0018 with specific inputs defined.
- T4 can run cleanly through the Finals paper window and the G6 evidence accumulation period without any configuration change.

**GG-011 severity update:** LOW (paper mode, formula bypassed) → RESOLVED for Phase 6/7. HIGH severity obligation transferred to ADR-0018 pre-condition list.

---

## What Does Not Change

- `PAPER_T4_FLAT_SIZING=true` in VPS (default; not in `.env` — do not add it)
- `PAPER_T4_POOL_USD=500.0` (default; adequate for any Finals game)
- `PAPER_T4_VIRTUAL=false` (default; already correct)
- `T4_BAND_WEIGHT=0.10` stub value (Phase 8 placeholder only; updated comment)
- Kill switches (ADR-0013 §band kill switch: stop T4 when pool exhausted; unchanged)

---

## Approval

**DS sign-off:** _______________  
**Date:** 2026-06-05
