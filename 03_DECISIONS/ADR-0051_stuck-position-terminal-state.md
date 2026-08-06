# ADR-0051: Terminal State for Permanently Unresolvable `aged_open` Positions

**Status:** DRAFT — NOT ACCEPTED. Proposal only, per T-422's hard scope fence (no `src/` changes this session). Requires operator review and explicit sign-off before any implementation.
**Date:** 2026-08-05/06
**Author:** Session `session/20260805T054958Z-resolution-layer-repair` (T-422)
**Depends on:** GG-161 (diagnosis + T-422 amendment), GG-084 (VPS datacenter-IP escalating block), `05_RESEARCH_EXPERIMENTS/T416_STUCK_POSITIONS_DIAGNOSIS.md`

---

## 1. Problem

As of this session, 17 of the T1/MAIN book's original 22 `aged_open` positions (2026-07-01 through 2026-07-29 game dates) have been confirmed — not merely presumed — permanently unresolvable. T-422's out-of-band repair re-fetched all 22 from a network unaffected by GG-084's IP block, specifically to rule out infrastructure as a confound; all 17 returned `reason=no_split_for_date` across all three resolution sources (MLB Stats API regular-season `gameLog`, postseason `gameLog`, ESPN boxscore fallback). No split exists for these player/date pairs in any source this system queries. This is not a retry problem — no amount of re-running resolution will produce data that does not exist upstream.

`aged_open` today is not a terminal state. `mark_aged_open()` (`paper_trader.py:935-969`) sets a flag and leaves the position in `open_positions` indefinitely. Capital allocated to these 17 positions (`size_usd` sum — recompute at implementation time; do not carry forward the stale $194.24 figure, which included the 5 now-settled positions) sits permanently locked with no path back to `bankroll_usd`, and `run_resolve_mlb.py`'s daily cron will retry all 17 forever, every day, at zero marginal benefit — each retry is a wasted request against an API that has never once returned this data and has no mechanism by which it would start.

## 2. Decision (PROPOSED)

Introduce a genuinely terminal status, distinct from `open` and from the existing `aged_open` flag, for positions that have exhausted all three resolution sources past an age ceiling. Two design questions are left open for operator decision (§4) rather than pre-decided by this draft.

### 2.1 Proposed mechanism

- A new position status value, e.g. `status="unresolvable"` (name TBD — must not collide with existing values; confirm the full enum in `paper_trader.py` before implementation).
- Trigger condition: `aged_open is True` AND age past `game_date` exceeds a ceiling (candidate: 21 days — inside T416's suggested 14-30 day range, chosen to comfortably exceed the longest observed resolution lag among genuinely-recoverable positions in this session's data, while not leaving capital locked for a full month) AND all three resolution sources have been attempted and failed on the most recent retry.
- On transition to `unresolvable`: the position leaves `open_positions` and moves to a new `unresolvable_positions` list (NOT `closed_positions` — it never resolved, and conflating it with a real win/loss would corrupt win-rate and P&L-per-bet statistics used by `run_power_calc.py`'s `n*` derivation, GG-004/APR-0024). `run_resolve_mlb.py`'s daily `pending` list must exclude `unresolvable_positions` going forward, stopping the wasted daily retry.

### 2.2 What happens to the locked capital — the open question

Two candidate dispositions, not adjudicated by this draft:

- **(a) Credit back at $0 net P&L** (return `size_usd` to `bankroll_usd`, log `pnl=0.0`, `outcome="unresolvable"`). Capital is freed; the position is excluded from win/loss statistics entirely (it counts toward neither a win nor a loss — it is removed from the denominator, not scored as a loss).
- **(b) Leave `size_usd` as a permanently forfeited loss** (`pnl = -size_usd`, `outcome="loss_unresolvable"`), on the theory that the capital was deployed and is gone regardless of why, and crediting it back understates the book's true risk history.

(a) is more consistent with the fact that a "no data" outcome is not the model being wrong — it is an infrastructure/data-source gap unrelated to the forecast's quality, and folding it into loss statistics would bias any future edge measurement against the model for a reason that has nothing to do with the model. (b) is more conservative about capital accounting and avoids ever making `bankroll_usd` look better than a naive investor's cash-in-cash-out experience would have been. **This ADR does not pick between them — that choice belongs to the operator** (Q6-style judgment call, not a technical one).

## 3. Interaction with GG-004 / commercial validation

Regardless of which disposition (a)/(b) is chosen, `unresolvable_positions` must **not** enter `clean_n` for any band's `run_power_calc.py` sample-adequacy calculation — these are not resolved bets in the sense GG-004/APR-0024 means (a real edge realized or not), they are bets whose outcome is permanently unknowable. Silently counting them as losses (disposition (b)) without an explicit `outcome="loss_unresolvable"` tag distinct from a genuine market loss would corrupt every downstream win-rate and variance calculation without any visible signal that it happened.

## 4. Decisions requiring operator sign-off before implementation

1. Age ceiling — 21 days (proposed) vs. the 14-30 day range T416 originally suggested vs. some other value.
2. Capital disposition — (a) $0 credit-back / excluded from win-loss statistics, vs. (b) forfeited loss / counted as `loss_unresolvable`.
3. Whether `unresolvable_positions` should still be retried at some much lower cadence (e.g. monthly) in case a data source backfills historical splits later, or whether the resolution attempt should stop permanently once terminal.
4. Naming of the new status value and list (`unresolvable` / `unresolvable_positions` used here as placeholders).

## 5. Explicitly out of scope for this ADR

- No `src/` code implementing this is written in this session (hard scope fence, T-422).
- Does not touch GG-084 (the VPS IP-block) or the `_is_game_final()` query-shape bug (GG-161 amendment) — those are separate, real fixes deferred to Phase 1, and fixing them does not make the 17 positions in this ADR's scope resolvable (they have no underlying data, independent of any infrastructure issue).
- Does not touch T4 MLB's cycle-log join-key issues (GG-164, Window G/T-421) — this ADR is scoped to T1/MAIN's `paper_trader.py` position lifecycle only.

## 6. Verification (not yet run — draft stage)

No tests exist for this proposal; none should be written until the operator has resolved §4's open questions, since the age ceiling and capital disposition are both testable invariants that would need to be locked in first.
