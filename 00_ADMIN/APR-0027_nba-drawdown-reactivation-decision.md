# APR-0027 — Decide NBA Main-Pool Kill-Switch Disposition Before 2026-27 Season Reactivation

**Status:** **DECIDED 2026-07-17 — Option B selected** (Earl Ignacio, DS sign-off). This document records the
choice of disposition; it is not itself the implementing ADR. The actual formal reset of NBA's drawdown
baseline/`initial_bankroll` still requires a dedicated ADR to be drafted and accepted before the reactivation
window opens (~1 month before the 2026-27 season) — see T-383, registered this session (renumbered from an
initial T-381 self-assignment — that ID was already claimed, concurrently, by an unrelated real session
(GG-059 C8 dashboard follow-on) at commit `e7206c6`, discovered via a fresh ID check before this document
was saved; T-383 is the verified next-free ID as of 2026-07-17 HEAD `f961fba`).
**Addresses:** GG-056 (`03_DECISIONS/GOVERNANCE_GAP_LOG.md`)
**Drafted:** 2026-07-15, Terminal 3 (GG-burndown-even session), branch
`session/20260715T145447Z-gg-burndown-even`
**Approved by:** Earl Ignacio (DS), 2026-07-17 — Option B

---

## Why This Escalation Is Required

NBA's main pool is dormant (dark/frozen per standing operator directive, [[project_nba_deferred]]) at a
realized drawdown of 24.9% (bankroll $751.10/$1,000 initial, realized P&L −$248.90), already past
`risk.py`'s `max_drawdown_pct = 0.20` permanent kill-switch threshold. This is historical/adjudicated
(GG-034/GG-036/GG-037) and not a live risk while NBA sits at zero live evaluations. But no decision exists
for what happens on the **first** `evaluate_forecast()` call once NBA resumes (~1 month before the 2026-27
season, per the standing reactivation window shared with [[GG-038]]/[[GG-040]]): the kill switch will fire
immediately and reject every subsequent bet indefinitely, with no reset mechanism currently defined.

Left undecided, this reproduces the exact silent-failure shape already logged in GG-049/GG-060: a cron run
that produces zero bets looks identical whether the cause is "off-season, no games" or "kill switch
permanently engaged." Nothing in the current session-start protocol distinguishes the two without an
operator explicitly reading the kill-switch reason code — and there will be no reason to think to check that
reason code if no one has flagged, ahead of time, that this collision is coming.

---

## Decision Requested of the DS

Choose one (or specify an alternative):

**Option A — Stay dark until a G6-scoped bankroll/limit revision.** NBA resumes evaluation only after the
standing G6 obligation to formally revise all `_HARD_LIMITS` (CLAUDE.md Q1; DECISION_LOG 2026-05-29
retroactive entries) is completed for NBA specifically, at which point the kill switch's relationship to the
historical 24.9% drawdown gets resolved as part of that broader limit-revision work rather than as a special
case now.

**Option B — Formally reset the NBA drawdown baseline / initial_bankroll for the new season via ADR**,
consistent with treating each season as a new evaluation window, while leaving the frozen -24.9%/-$248.90
figure on record as historical fact (per [[audit_finding_pnl_desync]] and [[feedback_portfolio_ledger_delineation]]
— the two ledgers must never be conflated, and a reset must not be read as erasing the adjudicated history).

**→ SELECTED 2026-07-17 (Earl Ignacio, DS).**

Either option requires an explicit ADR before the reactivation window opens; the point of this escalation is
to get that decision on record now, while there is no time pressure, rather than discovering the collision
live in October.

---

## Disposition Record

| Date | Action | By |
|---|---|---|
| 2026-07-15 | Drafted, submitted PENDING | GG-burndown-even session (even-numbered gap sweep) |
| 2026-07-17 | **Option B selected — formal reset via ADR.** Implementing ADR not yet drafted; registered as T-383 (renumbered from an initial T-381 self-assignment that collided with a concurrent real session's claim — see note above), due before the NBA reactivation window (~1 month before 2026-27 season). GG-056 stays OPEN until that ADR is drafted and accepted — this record closes the *disposition choice*, not the gap itself. | Earl Ignacio (DS) |
| 2026-07-22 | **T-383 closed — no new ADR drafted; the implementing ADR already existed.** `03_DECISIONS/ADR-0035_nba-paper-portfolio-reset-2026-27.md` was drafted and ACCEPTED 2026-06-30 SESSION 102 — *before* this document was even opened (2026-07-15) — and already implements Option B in full: resets `paper_portfolio.json` to a clean $1,000.00 baseline at 2026-27 season start, preserves the 158-bet 2025-26 record as a distinct historical EXP-017 cohort, and includes a pre-activation checklist gated on the October 2026 reactivation window. The 2026-07-17 row above registered T-383 believing no implementing ADR existed; it did, this document and GG-056 simply never cross-referenced it. Fixed this session: ADR-0035's own Status header (stale, still read "DRAFT" despite its filled Sign-off table) corrected to ACCEPTED; GG-056 and this Disposition Record both now point to ADR-0035 directly. T-383 is DONE via this cross-reference/status-fix, not via a new ADR-0048. The underlying Option B decision and its October-2026 execution timeline are unchanged. | Claude (Window B session), T-383 close-out |
