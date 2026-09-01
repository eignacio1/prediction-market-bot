# Operator Digest — 2026-08-31

**What changed today:**
Four housekeeping items: a stray local queue file checked in; a status page properly regenerated (not hand-edited); a 6-week-old bug that misread "NOT accepted" as "accepted" fixed and pinned with tests; and a decision paper (not a fix) on last week's trading-service repair-clobber incident, with four options for you.

**Money impact:** None. Zero real money at risk; nothing touched trading code, limits, or ledger.

**Decision needed?** One, not urgent: the paper's four fixes (reload-before-save, lock file, stop-repair-start checklist, proper repair channel) aren't ranked — it leans toward the cheaper two, but it's your call on discipline vs. engineering effort for a one-time problem.

**Worry flag:** The safety check meant to catch this already existed and still didn't stop last week's incident — why is unresolved, flagged as follow-up.
