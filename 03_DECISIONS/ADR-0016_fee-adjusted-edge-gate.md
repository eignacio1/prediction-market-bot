# ADR-0016 — Fee-Adjusted Edge Gate

**Status:** ACCEPTED  
**Date:** 2026-06-04 SESSION 30  
**Decisions logged:** true  
**Author:** Claude Code (T-131)  
**Approval required:** DS (Earl Ignacio) sign-off before ACCEPTED  
**Supersedes:** Nothing — adds obligation not previously captured in any ADR  
**Supplements:** ADR-0014 §T1 edge computation (adds fee subtraction step)  
**Related:** GG-009 (taker fee absent from MIN_EDGE gate), ADR-0014 §T1

---

## Context

GG-009 (logged SESSION 22): `MIN_EDGE_TO_APPROVE = 0.02` in `risk.py` does not account for the Kalshi taker fee. At P=0.50, the taker fee is `0.07 × 0.50 × 0.50 = $0.0175/contract` — 87.5% of the nominal MIN_EDGE. Bets approved by the current gate may have negative net-of-fee expected value.

SESSION 25 added fee annotation fields to each position record (`fee_per_contract`, `fee_net_edge`, `fee_contaminated`) for G6 audit purposes. But annotation is not prevention. The edge gate must reject fee-negative bets, not merely label them.

### Fee formula (Kalshi taker)

```
fee(P) = 0.07 × P × (1 − P)
```

Where P = contract cost (the YES price or NO price paid). For a YES bet, P = YES price ≈ `mid`. For a NO bet, P = NO price ≈ `1 − mid`. Due to symmetry: `fee(mid) = fee(1 − mid)`. In both cases, `fee ≈ 0.07 × mid × (1 − mid)`.

Maximum fee: at P=0.50, fee = $0.0175.  
Fee at P=0.10: $0.0063. At P=0.90: $0.0063.

The fee is not a constant — it is highest at mid-range prices and low at extremes. A flat MIN_EDGE uplift (Option A below) over-constrains low-probability markets and under-constrains mid-range markets simultaneously. The per-contract fee computation is correct.

---

## Decision: Fee-Adjusted Edge Computation

### Option selected: Per-market fee subtraction (Option B)

Three options were evaluated:

| Option | Mechanism | Tradeoff |
|--------|-----------|----------|
| A | Raise `MIN_EDGE = 0.02 → 0.0375` (add fee at P=0.50 to the constant) | Simple but wrong: over-filters P=0.10 markets (fee=$0.0063 << $0.0175 uplift), under-filters P=0.30–0.70 markets if fee there > $0.0175 (impossible; fee peaks at 0.50) |
| **B** | `net_edge = gross_edge - fee(mid)`; gate on `net_edge ≥ MIN_EDGE` | Accurate per-market fee deduction; correctly handles all price levels |
| C | Maker-first limit order policy (fee 4× lower) | Requires limit order infrastructure not yet built; deferred to future ADR |

**Selected: Option B.**

### Implementation

In `run_paper_trade.py` and `run_pregame.py`, the edge computation changes from:

```python
edge = p_threshold - mid - half
direction = "YES" if edge > EDGE_YES else "NO" if edge < EDGE_NO else "PASS"
```

To:

```python
gross_edge = p_threshold - mid - half
fee = 0.07 * mid * (1.0 - mid)
edge = gross_edge - fee          # net-of-fee edge (ADR-0016)
direction = "YES" if edge > EDGE_YES else "NO" if edge < EDGE_NO else "PASS"
```

`forecast_rec["edge"]` = `net_edge`. This propagates automatically to C4's `evaluate_forecast()` which gates on `edge ≥ MIN_EDGE_TO_APPROVE`. No change to `MIN_EDGE_TO_APPROVE` required.

### Audit traceability

The forecast record and C6 audit log include:
- `gross_edge` — raw edge before fee subtraction (for research/comparison)
- `kalshi_fee` — `fee(mid)` at the time of evaluation  
- `edge` — net-of-fee edge (the decision-making signal; what C4 receives)

`MIN_EDGE_TO_APPROVE = 0.02` in `risk.py` is unchanged. Post-ADR-0016, this constant means "minimum net-of-fee edge required for approval." The GG-009 contamination is resolved: the gate now correctly requires at least 2¢ net of transaction cost.

### Interaction with SESSION 25 position annotations

SESSION 25 added `fee_per_contract`, `fee_net_edge`, and `fee_contaminated` to position records. Post-ADR-0016:

- `fee_contaminated` will always be `False` for newly placed bets (because fee-net positions are the only ones that get approved)
- `fee_per_contract` and `fee_net_edge` remain for G6 audit completeness
- Historical pre-ADR-0016 positions in `closed_positions` may have `fee_contaminated = True`; these are accurately labeled as contaminated evidence

---

## Rationale

The bot places taker orders (market orders at ask price). Every approved bet incurs the taker fee. Approving a bet with `gross_edge = 0.03` at P=0.50 yields `net_edge = 0.03 - 0.0175 = 0.0125` — below MIN_EDGE of 0.02. This bet has positive gross edge but is a losing bet net of fees at scale.

At P=0.10: `fee = $0.0063`. A bet with `gross_edge = 0.025` has `net_edge = 0.0187` — also below 0.02. Even low-probability markets have material fee costs that must be in the gate.

---

## Governance implications

- GG-009: RESOLVED by this ADR. The edge gate now accounts for Kalshi taker fees.
- EXP-017 historical figures (Finals G1) were computed on pre-fee-adjusted positions. All future EXP-017 runs use fee-adjusted edge. The G1 figures are not directly comparable to post-ADR-0016 results.
- If maker order infrastructure is built (future ADR), the fee formula changes from `0.07 × P × (1-P)` to `0.0175 × P × (1-P)` — a 4× reduction. ADR required at that point.
- `LEAGUE_AVG_PTS_ALLOWED` refresh policy: handled in ADR-0015.
