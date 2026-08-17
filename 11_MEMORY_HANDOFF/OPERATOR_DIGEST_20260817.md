# Operator Digest — 2026-08-17

## T-458 (23:43Z)

We closed the loop on a data-quality bug flagged earlier (GG-170): the bot was accepting game results before the league's official record was final, causing it to lock in the wrong outcome roughly 26% of the time in one batch. We built a guard that refuses results until they're confirmed final, plus an automatic check that catches recurrence without manual review.

We also corrected an earlier-cited number: not 91% of that batch was affected, but 74%, once pending results are excluded — still serious, now accurate.

We did not fix the ~530 already-wrong results this session; that's tracked as separate follow-up work so it gets proper attention. Nothing about bet sizing or risk limits changed. Full test suite ran clean (2,883 passing).
