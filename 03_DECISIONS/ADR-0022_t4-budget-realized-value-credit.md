# ADR-0022: T4 Band Budget — Realized-Value Exit Credit

**Status:** ACCEPTED  
**Date:** 2026-06-10  
**Author:** Earl Ignacio (DS) + Claude Code (implementation)  
**Amends:** ADR-0013 (T4 throughput capital budget) — budget-ledger semantics only. The band-budget architecture, Kelly-within-band sizing, and band-level kill behavior of ADR-0013 remain in force.  
**Resolves:** GG-023 / T-161  
**Decisions logged:** true

---

## Context

ADR-0013 designed `t4_deployed_usd` as a one-way commitment counter: every entry
fire adds `approved_size`; nothing ever subtracts. That was coherent when positions
were held to resolution. ADR-0018/0019 then added exit mechanics — positions now
close mid-game and free their capital — but the budget accounting was never
re-examined (GG-023: "no test or review question asked what an exit does to the
budget counter").

**G4 observation:** T4 fired 1,199 bets and pinned the $500 pool at 100% before
halftime. 29 exits then fired correctly and freed economic capital, but the counter
never moved — `fired=0` every cycle for the entire second half, exactly the window
where live Bayesian signal is densest and where ADR-0021's gate now gains
sensitivity (Q4 materiality 13.5% vs 1.4% old). The defect silently halved T-152
exit-event evidence collection.

DS directive (SESSION 46): resolve T-161 with "a reset so the strip runs clean"
on G5.

## Decision space (T-161)

| Option | Mechanics | Failure mode |
|--------|-----------|--------------|
| (a) Revolving credit | Exit credits full entry cost regardless of P&L | A losing exit frees more capacity than the cash that returned; in a high-churn losing game, gross deployment is unbounded — losses are bounded only by the daily-loss switch, leaving the band budget meaningless as a capital constraint |
| (b) Gross commitment cap (status quo) | No credit; budget = per-game gross commitment | The G4 failure: entry-dead from Q2 with capital free and 24+ minutes of the best signal window remaining |
| (c) **Realized-value credit (chosen)** | Exit credits what actually came back, capped at entry cost | None identified; see invariants |

## Decision — realized-value credit, capped at entry cost

```
deployed = open T4 exposure + realized T4 losses this game

on exit:  credit = size_usd + min(0, exit_pnl)     # _exit_budget_credit()
          deployed = max(0, deployed − credit)
```

- **Winning exit** (pnl ≥ 0): credit exactly the entry cost. Capacity returns to
  its pre-entry level and never exceeds the authorized band budget — wins do not
  expand risk authorization (the budget is a DS-authorized ceiling, not a
  performance-scaled one).
- **Losing exit** (pnl < 0): credit entry cost + pnl — only the cash that actually
  returned. Realized losses permanently consume budget.

### Structural invariants (all test-enforced, test_t161_budget_credit.py)

1. **Aggregate loss bound:** the band's cumulative realized loss in one game can
   never exceed `t4_band_budget` — the budget is a true capital constraint again,
   not merely a throughput throttle. (Option (a) loses this property.)
2. **No starvation:** capacity recycles on every exit; the G4 regime (100 winning
   round-trips on a budget that holds 20 concurrent positions) fires all 100.
   (Option (b) loses this property.)
3. **No expansion:** deployed ≥ 0 always; capacity ≤ budget always.
4. **Restart-losslessness:** `_reconstruct_t4_ledger(portfolio, game_date)`
   rebuilds the identical ledger value from portfolio state — open
   `pool_isolated` exposure plus per-exit realized losses for the game date.
   The G4 T4 process died mid-game; a restarted process now resumes with the
   true ledger instead of an empty counter (which would have authorized a
   second full budget). Per-exit losses are summed individually — a win restores
   only its own entry cost and never offsets another position's loss, keeping
   reconstruction arithmetic identical to the incremental path.

### Coherence with existing controls

- **Daily-loss kill switch (ADR-0012, net semantics 424698a):** unchanged and
  independent. The band ledger uses per-exit loss accounting (wins don't offset)
  because it governs *capital authorization*; the daily-loss switch uses net
  accounting because it governs *loss tolerance*. Both fire independently —
  consistent with the two-tier kill design (CLAUDE.md rule 9, GG-010 ruling).
- **Band-level kill (ADR-0013/GG-010):** `BAND_BUDGET_EXHAUSTED` still halts
  entries when deployed + size > budget; it now triggers on true consumed
  capital. A band that loses its entire pool still goes entry-dead — by design.
- **End-of-game resolutions** (status RESOLVED, not EXITED) settle outside the
  in-game ledger; positions held to resolution consume budget until the game
  ends, which is correct — their capital never recycled.
- **G5 clean strip:** the ledger is keyed to `game_date`; G5 starts at
  deployed = $0.00 automatically. No manual state reset required, and G4's
  unresolved open positions (prior game_date) cannot contaminate G5 capacity.

## Throughput note (CLAUDE.md rule 9)

At ~1,000 evaluations/game the ledger is O(1) per entry/exit and reconstruction
is O(positions); no per-bet assumptions. The design is capital-ceiling agnostic:
the same arithmetic governs a $500 pool or $1M band budget.

## Review trigger

Post-G5: compare second-half `fired` counts and budget trajectory against G4.
If `BAND_BUDGET_EXHAUSTED` still occurs early with ADR-0021's gate active
(expected fire volume ~10% of G4's), escalate sizing review (PAPER_T4_POOL_USD
vs flat per-contract cost) to DS before the next game night.
