# Operator Digest — 2026-09-15

**NFL Saturday capture gap, diagnosed and fixed in git.** We were missing all football price data on Saturdays — the schedule grabbing NFL prices ran every day except Saturday, so 09-12 has zero football rows while every other day that week has plenty. That day's data is gone for good. The fix is a one-line schedule addition mirroring Sunday's, dry-run tested. I also built an automatic check to catch this going forward.

The fix sits in a pull request (#133) awaiting your review rather than auto-deployed — the last five changes here were all merged by you, so I kept that pattern rather than pushing it live myself. It still needs deploying plus confirming next Saturday. Until then the gap stays open in tracking.

One loose thread, not chased: two other days had suspiciously identical football counts. Flagged, out of scope.
