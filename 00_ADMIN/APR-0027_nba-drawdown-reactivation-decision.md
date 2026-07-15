# APR-0027 — Decide NBA Main-Pool Kill-Switch Disposition Before 2026-27 Season Reactivation

**Status:** PENDING — requires Earl Ignacio (DS) sign-off. Not self-approved (Hard Rule 3: this decides
whether/how to reset a kill-switch baseline, and touches the standing G6 obligation to formally revise hard
limits — a decision only the DS can make).
**Addresses:** GG-056 (`03_DECISIONS/GOVERNANCE_GAP_LOG.md`)
**Drafted:** 2026-07-15, Terminal 3 (GG-burndown-even session), branch
`session/20260715T145447Z-gg-burndown-even`
**Approved by:** — (pending)

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

Either option requires an explicit ADR before the reactivation window opens; the point of this escalation is
to get that decision on record now, while there is no time pressure, rather than discovering the collision
live in October.

---

## Disposition Record

| Date | Action | By |
|---|---|---|
| 2026-07-15 | Drafted, submitted PENDING | GG-burndown-even session (even-numbered gap sweep) |
| — | Awaiting DS review | Earl Ignacio |
