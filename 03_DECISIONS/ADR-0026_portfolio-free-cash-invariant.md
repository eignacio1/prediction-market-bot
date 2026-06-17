# ADR-0026 — Portfolio-Level Free-Cash Invariant (Aggregate Deployment Cap)

**Status:** ACCEPTED — 2026-06-16  
**Decision makers:** DS (Earl Ignacio) / operator directive (SESSION 64)  
**Amends:** ADR-0010 (band/Kelly hierarchy + reserve mandate) — promotes the 40% reserve from a per-bet *advisory warning* to an *enforced portfolio-level invariant*; ADR-0010 remains in force  
**Supersedes:** —  
**Closes:** GG-035 (structural half)  
**Related:** ADR-0006 (exposure-based risk framework), ADR-0012 (daily-loss limit), GG-034 (root scalar desync that hid the breach), GG-036 (the locked G5 positions)

---

## Context

### What GG-035 exposed

When the live VPS book was corrected under GG-034 (SESSION 63), the ledger-derived
`bankroll_usd` came out **negative: −$254.59**. Decomposed via the cash identity
(`bankroll = initial + Σ closed non-isolated pnl − Σ open non-isolated stake`):

```
$1,000 initial − $251.21 realized − $1,003.38 locked in 41 open G5 stakes = −$254.59
```

The bot had deployed **$1,003.38 into a single game window — 100.3% of the $1,000
initial bankroll and ~134% of the $748.79 equity** it actually held. Equity was
positive (+$748.79 realized); **free cash was negative.** This is a margin-breach /
forced-liquidation condition in the live-capital era: deploying more money than you
hold.

### Why nothing stopped it

Two independent failures combined:

1. **GG-034 (root):** the corrupted `total_realized_pnl`/`bankroll_usd` scalar
   reported a healthy +$130.62 bankroll. Kelly sizing and the orchestrator reserve
   gate read that phantom figure, so they sized against money that did not exist.
   GG-034 is now resolved (ledger-derived scalars + cross-process file lock).

2. **GG-035 (structural — this ADR):** even with a *correct* scalar, **C4 had no
   portfolio-level invariant.** Every risk control was per-bet:
   - Kelly fraction (per bet),
   - `max_single_event_exposure_usd = $500` (per event),
   - reserve mandate (per-bet **advisory warning only** — never blocked anything).

   None of these sum to a global cash constraint. The G5 book was built one
   sub-$500 bet at a time, each individually compliant, with **nothing watching the
   aggregate.** 41 compliant bets aggregated to a non-compliant book.

   The one batch-level guard that existed — the reserve gate in
   `run_paper_trade.py` — lived in the orchestrator (not C4), read the corrupted
   scalar, and was bypassed by every other caller (`run_t4_live`, EXP harnesses).

This is precisely the failure mode CLAUDE.md hard rule 9 warns about: a design that
only makes sense at low throughput. At ~1,000 evaluations per game, an aggregate
cash constraint is not optional — it is the only thing standing between per-bet
compliance and portfolio insolvency.

---

## Decision

**C4 (`RiskEngine.evaluate_forecast`) enforces a portfolio-level free-cash
invariant on aggregate open NON-isolated stake, in two tiers.**

Let:

```
equity            = initial_bankroll + Σ closed non-isolated pnl      (deployable base)
open_exposure     = Σ entry cost of still-open non-isolated positions (capital in flight)
projected         = open_exposure + approved_size                     (after this bet)
deployment_cap    = MAX_PORTFOLIO_DEPLOYMENT_PCT × equity             (= 0.60 × equity)
```

**CHECK 8a — Hard solvency invariant (KILL_SWITCH):**
```
projected > equity   ⇒   over-leverage   ⇒   KILL_SWITCH (portfolio_over_leverage)
```
Free cash may never go negative. A book already past equity (the literal GG-035
forensic state) trips this immediately. Solvency is checked **before** the policy
cap so a true breach halts rather than merely skipping a bet.

**CHECK 8b — Policy deployment cap (REJECT):**
```
projected > deployment_cap   ⇒   REJECT (aggregate_deployment_cap)
```
Aggregate open stake is held at or below 60% of equity. Each over-cap bet is
**rejected individually** — not a batch `break`. Because rejected bets deploy
nothing, exposure plateaus at the cap instead of growing toward 8a. This is the
per-bet expression CLAUDE.md hard rule 9 mandates: the control operates per bucket,
approaching per bet, and scales to 1,000 evaluations.

### Why the cap is 60% of equity

`MAX_PORTFOLIO_DEPLOYMENT_PCT = 1.0 − RESERVE_MANDATE_PCT = 0.60`. This is **not a
new free parameter.** ADR-0010 already mandates a 40% reserve uncommitted after the
T1 batch so T4/T5 have capital at game time. That reserve was only ever an advisory
warning per bet; this ADR makes it the binding aggregate constraint it was always
meant to be. The cap inherits ADR-0010's derivation; no new calibration is
introduced.

### Base = equity, not initial bankroll

Both tiers measure against **equity** (initial + realized pnl), not initial
bankroll. When the book is underwater — exactly the GG-035 stress scenario — equity
< initial, so 60% of equity is *stricter* than 60% of initial. A risk control must
tighten, not loosen, under losses. (The legacy orchestrator reserve gate, which
anchors to initial, is retained as redundant defense-in-depth but is no longer the
authoritative control.)

### Isolation (T4)

The invariant applies to **non-isolated stake only.** T4 (`pool_isolated`) runs its
own budget (ADR-0013 / ADR-0022 / ADR-0023) and is excluded from both `equity` and
`open_exposure`. `free_cash == _ledger_bankroll()` by construction.

### Backward compatibility

C4 stays a pure decision function — it receives a portfolio snapshot, it does not
own the ledger (same pattern as `current_daily_loss` / `current_drawdown_pct`). The
two new parameters default to `current_open_exposure_usd=0.0` and
`portfolio_equity_usd=None`. **When `portfolio_equity_usd` is None the invariant is
skipped**, so EXP harnesses and the T4 isolated path are unaffected.
`run_paper_trade.py` supplies the snapshot via the new
`PaperTrader.exposure_snapshot()`, so the T1 main book is always gated.

---

## Institutional verification (would it have stopped G5?)

`tests/test_c4_risk.py::TestPortfolioDeploymentInvariant::test_g5_overleverage_forensic_would_have_been_blocked`
replays the G5 deployment dynamic against the real pre-G5 equity:

| Quantity | Value |
|---|---|
| Equity going into G5 ($1000 − $251.21 realized G2–G4) | **$748.79** |
| Deployment cap (60% of equity) | **$449.27** |
| What the bot actually deployed | **$1,003.38** (134% of equity) |
| What ADR-0026 allows | ≤ $449.27 — every bet past the cap REJECTED |

The test places bets one at a time, feeding accumulated exposure back into C4, and
asserts deployment plateaus at the cap and **never reaches $1,003.38.** The
over-leveraged state is unreachable with the invariant active.

---

## Test coverage

`tests/test_c4_risk.py::TestPortfolioDeploymentInvariant` — 10 tests:

| Test | Asserts |
|---|---|
| `test_cap_constant_ties_to_reserve_mandate` | cap == 1 − reserve == 0.60 |
| `test_no_state_supplied_skips_invariant` | equity=None ⇒ check skipped, telemetry None (backward compat) |
| `test_clean_book_passes_and_records_check` | zero exposure ⇒ APPROVED, check recorded, telemetry set |
| `test_exposure_at_cap_rejects_next_bet` | at 60% ⇒ REJECT aggregate_deployment_cap |
| `test_exposure_at_equity_kill_switch` | at 100% ⇒ KILL_SWITCH portfolio_over_leverage |
| `test_solvency_breach_takes_priority_over_cap` | 8a fires before 8b on a pre-breached book |
| `test_below_cap_is_approved` | comfortably below cap ⇒ APPROVED |
| `test_c6_failure_during_cap_rejection_propagates_false` | C6 write failure ⇒ ok=False |
| `test_g5_overleverage_forensic_would_have_been_blocked` | the G5 replay above |

Full suite: 974 passed.

---

## Consequences

**Positive:**
- The portfolio can no longer deploy more than it holds. The GG-035 over-leverage
  condition is structurally impossible while the invariant is active.
- The ADR-0010 reserve mandate is finally enforced, not merely warned.
- The control is per-bet and scale-agnostic (hard rule 9 compliant).
- C4 remains a pure function; the position ledger stays the single source of truth
  in C5.

**Negative / risks:**
- Callers that do not supply `portfolio_equity_usd` are NOT protected. This is
  intentional (backward compat) but means the T4 path and any future runner must
  opt in explicitly. Tracked: extend coverage to T4/live runners before G7 venue
  expansion.
- The 60% cap inherits ADR-0010's paper-scale derivation. Like every hard limit it
  must be re-ratified via ADR at G6 when the live bankroll is set (see below).

---

## G6 obligation

`MAX_PORTFOLIO_DEPLOYMENT_PCT` (and the solvency invariant's implicit 100% line)
join the hard-limit set that must be formally re-derived at G6 against the live
bankroll, alongside `max_single_event_exposure_usd`, `max_drawdown_pct`,
`MAX_DAILY_LOSS_PCT`, and `RESERVE_MANDATE_PCT`. The structural invariant is
permanent; the 60% threshold is subject to that review.
