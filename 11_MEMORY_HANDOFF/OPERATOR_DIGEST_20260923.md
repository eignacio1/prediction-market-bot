# Operator Digest — 2026-09-23

- GG-236 (auto): Wave 31.3: reconciled origin/main, landed stranded commits, deleted 40 merged branches, pruned worktrees
- T-565 (auto): T4M-PROJ model-vs-market calibration reproduction from live VPS ledger, vs-ADR-0046 comparability verdict (NOT COMPARABLE), and extension to all bands/rejected cohort -- 5/5 deliverables complete.

## T-564/GG-291 — First real NFL T1 settlement (prose digest)

**NFL T1 crossed a milestone tonight: the bot settled real bets against real football scores for the first time.** Of the 42 open NFL moneyline paper positions, 20 belonged to games that had actually finished (10 games total), so those were settled — meaning we checked what the model predicted against what actually happened and booked the result. The other 22 positions are for games that haven't finished yet, so they were correctly left alone rather than guessed at.

The net result on those 20 settled bets: **up $13.48** (paper money, not real). We also caught and fixed a bug before it could cause a problem — some positions were missing a value the settlement code needed, which would have crashed the process; that got fixed and double-checked with a backup first. We also proved that re-running the settlement a second time doesn't double-count or corrupt anything — an important safety property for something that touches money math.

What this does **not** prove: there's still no live capital at risk anywhere, no real bet was placed with real money, and we haven't yet seen what happens when two teams tie (a case the code is designed to refuse to guess on, but hasn't been tested against a real tie yet). The remaining 22 positions will get settled in a future session once their games wrap up.

One housekeeping note: our internal state-of-the-project summary file is over a month out of date (last refreshed 2026-08-14) and our task-plan document never got a line item for NFL work at all. Neither is urgent, both are now flagged for a future cleanup pass.
