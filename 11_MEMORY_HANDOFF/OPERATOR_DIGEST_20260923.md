# Operator Digest — 2026-09-23

- GG-236 (auto): Wave 31.3: reconciled origin/main, landed stranded commits, deleted 40 merged branches, pruned worktrees
- T-565 (auto): T4M-PROJ model-vs-market calibration reproduction from live VPS ledger, vs-ADR-0046 comparability verdict (NOT COMPARABLE), and extension to all bands/rejected cohort -- 5/5 deliverables complete.

## T-564/GG-291 — First real NFL T1 settlement (prose digest)

**NFL T1 crossed a milestone tonight: the bot settled real bets against real football scores for the first time.** Of the 42 open NFL moneyline paper positions, 20 belonged to games that had actually finished (10 games total), so those were settled — meaning we checked what the model predicted against what actually happened and booked the result. The other 22 positions are for games that haven't finished yet, so they were correctly left alone rather than guessed at.

The net result on those 20 settled bets: **up $13.48** (paper money, not real). We also caught and fixed a bug before it could cause a problem — some positions were missing a value the settlement code needed, which would have crashed the process; that got fixed and double-checked with a backup first. We also proved that re-running the settlement a second time doesn't double-count or corrupt anything — an important safety property for something that touches money math.

What this does **not** prove: there's still no live capital at risk anywhere, no real bet was placed with real money, and we haven't yet seen what happens when two teams tie (a case the code is designed to refuse to guess on, but hasn't been tested against a real tie yet). The remaining 22 positions will get settled in a future session once their games wrap up.

One housekeeping note: our internal state-of-the-project summary file is over a month out of date (last refreshed 2026-08-14) and our task-plan document never got a line item for NFL work at all. Neither is urgent, both are now flagged for a future cleanup pass.
- T-567 (auto): T-567 efficiency-gradient ranking complete — all 4 deliverables done, KXMLBHIT ties in tier 3, core four don't separate from props

## T-568/GG-296 — Shard-3 funding demand measured, held; first real fill confirmed (prose digest)

**We measured the real demand for a third funding shard on the MLB T4 live bot, and it came back higher than what our own tracking system was showing — so we did not fund it.** The internal counter that was supposed to tell us how much more collateral shard 3 needed caps out at 2,000 entries, so on a busy day it silently undercounts. Going straight to the raw event log for 2026-09-20 gave the true number: 3,221 approved bets needing $3,095.80 more than what shard 3 currently has, and $4,643.70 is the actual funding level required — a level the demo account can't reach. Rather than fund to the wrong (lower) number and have this happen again, we stopped and are flagging it for you to decide the next move.

Separately, we traced one bet all the way from risk approval through to a real, confirmed fill on Kalshi's side — the first time we've been able to prove the bot's order actually executed, not just that it was accepted. That's real progress on the shard-3 funding fault we've been chasing for weeks. But checking the wider book turned up a new problem: 139 of 140 positions marked "open" in our local records show as cancelled on Kalshi's side — only that one position is genuinely filled. That's now a separate, high-priority tracking item (GG-297), because it means our local "what's currently open" count can't be trusted right now without cross-checking against Kalshi directly.

We also cleared two smaller loose ends from last week's calibration-comparison work (a mislabeled data field, and a stale accuracy benchmark that drifted when re-measured on fresh data) — both logged, neither urgent.
## T-566 — Measuring the real cost of trading, not assuming it

Every bet this system considers has to clear a threshold: the model's edge over the market price has to be big enough to be worth taking, after accounting for the real cost of getting in and out. For two of the three time horizons (same-day and live in-game), the system already measures that real cost from live prices every time it checks. For the third — the pregame game-market bets (moneyline, spread, totals) — it had never been measured at all. The code just assumed that cost was zero.

This session measured what that cost actually is, using 54 days of real price history. For most markets the gap between zero and reality is small. But for a handful — partial-game markets and team-total markets — the real cost is close to, or several times larger than, the entire edge threshold the system requires. Re-checking past approved bets against the real number: 11% would have failed the bar using a typical cost, and as many as 72% would fail under worse-than-typical conditions.

Nothing was changed. This is a measurement and a decision document (APR-0036) laying out four options — the operator decides which, if any, to adopt.

## T-568 close-out — stray branch sweep

8 session branches sit unlanded on origin (2 are today's in-progress work, 6 range 1-13 days old). None were merged — report only. Oldest three (13d/11d/8d) worth a look: check whether their work already landed under a different commit before assuming it's lost. Full list in `SESSION_HANDOFF_20260923_0523.md` § Step 9.
