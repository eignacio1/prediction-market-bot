# Operator Digest — 2026-08-31

**What changed today:**
Four housekeeping items: a stray local queue file checked in; a status page properly regenerated (not hand-edited); a 6-week-old bug that misread "NOT accepted" as "accepted" fixed and pinned with tests; and a decision paper (not a fix) on last week's trading-service repair-clobber incident, with four options for you.

**Money impact:** None. Zero real money at risk; nothing touched trading code, limits, or ledger.

**Decision needed?** One, not urgent: the paper's four fixes (reload-before-save, lock file, stop-repair-start checklist, proper repair channel) aren't ranked — it leans toward the cheaper two, but it's your call on discipline vs. engineering effort for a one-time problem.

**Worry flag:** The safety check meant to catch this already existed and still didn't stop last week's incident — why is unresolved, flagged as follow-up.
**T-504 (STANDARD):** Added scaffolding to the bot's market registry for the five "game-level" MLB bet types (moneyline, run line, totals, team totals, partial-game) so they now have live-trading placeholder slots, same as the player-prop bets already trading. Nothing new is live — these are inactive placeholders, no money at risk, no strategy behavior changed.

Two things flagged for you, not fixed yet: (1) extending this same idea to football/hockey needs a bigger structural change than this task was scoped for, so it's logged as a follow-up (GG-226) rather than done partway; (2) a minor, pre-existing test-cleanup issue was spotted and logged (GG-228), not touched.

**Needs your action:** PR #125 (this work) is open on GitHub but the auto-merge got blocked by a permission check — someone needs to click merge (`gh pr merge 125 --merge` or via the GitHub UI). Tracked as T-506.
