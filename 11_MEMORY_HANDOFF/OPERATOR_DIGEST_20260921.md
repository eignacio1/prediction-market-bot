# Operator Digest — 2026-09-21

**T-563/GG-291 — fixed the bug that would have crashed real settlement, stopped before touching real bets.**

Last session (09-18) found that all 42 real NFL bets were missing a data field settlement needs — it would have crashed. I found the actual root cause: two scripts were opening these bets without ever writing that field, so it defaulted to a value that crashes the settlement code. Fixed at the source — the scripts now compute the real value, or refuse to open the bet rather than write a bad one. Added 7 tests for this; ran the full related test suite (190 tests) clean.

Also found (registered as GG-295): those 42 bets already had the field patched in from an earlier repair, just never written down anywhere — so that mystery's solved too.

**What I did NOT do:** I did not run real settlement on the 42 bets tonight. You said work fast and close out the wave — real settlement means pulling final scores from two independent sources and proving I won't double-count if it's re-run, and I didn't think that was safe to rush. That's queued as the very next task (T-564), fully unblocked, no more code needed — just needs someone to sit down and do it carefully.

**Heads up:** even once settlement runs, we don't have enough resolved bets yet for a win or loss to mean much statistically — don't read a good or bad result from those 42 as proof the strategy works or doesn't.
