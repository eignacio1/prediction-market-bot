# Operator Digest — 2026-08-17

## T-458 (23:43Z)

We closed the loop on a data-quality bug flagged earlier (GG-170): the bot was accepting game results before the league's official record was final, causing it to lock in the wrong outcome roughly 26% of the time in one batch. We built a guard that refuses results until they're confirmed final, plus an automatic check that catches recurrence without manual review.

We also corrected an earlier-cited number: not 91% of that batch was affected, but 74%, once pending results are excluded — still serious, now accurate.

We did not fix the ~530 already-wrong results this session; that's tracked as separate follow-up work so it gets proper attention. Nothing about bet sizing or risk limits changed. Full test suite ran clean (2,883 passing).
**T-460 (STANDARD):**

**What changed today, in one paragraph:** Four small housekeeping bugs got fixed — not just written down for later. One was a false alarm in the tool that stops two sessions from grabbing the same task number (it was flagging safe, already-reserved numbers as if they were active conflicts). One was a flaky test that could randomly fail right at midnight UTC. One was a text-processing bug that could silently truncate data. The last was a leftover edge case in the tool that archives old session notes, where a file with exactly one entry never got its "last updated" pointer moved forward.

**What this means for your money:** No change — none of this touched bet sizing, risk limits, or how the bot decides to trade. Nothing in `src/` (the actual trading code) was modified this session.

**Does anything need your decision right now?** No.

**Anything that worried the session, even if not urgent:** One loose end: the session-start health check flagged that a status file (`Compass OS Health`) has grown an unusually long single line (~5,000 characters) — not fixed or formally logged this session, just noted so it doesn't get lost. Also, PR #82 (this session's four fixes) is open and will be merged as part of closing out.
- T-459 (auto): T-459: box 1.7 re-verified on main (2,875/29/0, exit 0) — Phase 1 8/8 closed; GG-179 unchanged/OPEN
- T-461 (auto): T-461: landed HYP-010 Phase 2 pre-registration (gate 2.3 metric swap, EXP-022 assigned) into governed docs, no src/
