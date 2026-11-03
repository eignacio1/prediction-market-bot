# Forward-test entry cost (W98.2 Part B) — read-only, nothing changed

**Source:** box task `forward_entry_cost_read`, `04_EXECUTION/BOX_TASKS/results/20261103T053316Z_forward_entry_cost_read.md` (ran 2026-11-03T05:35Z; window 17.59 days from the 2026-10-16 top-up; shadow book; 130,093 orders, 121,297 with a settled outcome; 4,924 still pending and 3,872 without cache rows dropped). Per contract = outcome − price − exact fee (taker headline; maker as sensitivity). Intervals are 95%, game-clustered.

## Operator line
**Keep the frozen rule.** Taking at the quote at decision time loses about 0.10 per contract in NBA and NFL (intervals exclude zero), so a switch would cost money in the two sports with the most orders; NHL is the one sport where taking is not clearly negative (+0.01 to +0.08, intervals span zero, only about 200 priced orders per arm). A superseding addendum would need its own pre-registration; I would only revisit it for NHL, once more NHL quotes exist. I changed nothing.

## Table (P&L per contract)
| sport | arm | orders | fills | fills / game | as entered (taker fee) | taken at the quote (n priced) |
|---|---|---:|---:|---:|---|---|
| NBA | control (rest at model mid) | 41,992 | 18,623 | 202.4 | −0.024 [−0.064, +0.019] | −0.091 [−0.151, −0.027] (1,749) |
| NBA | treatment (post at book, cancel 60 s) | 39,907 | 3,623 | 39.4 | +0.181 [+0.110, +0.250] | −0.115 [−0.171, −0.053] (1,502) |
| NFL | control | 13,483 | 6,778 | 169.5 | +0.039 [−0.026, +0.103] | −0.133 [−0.197, −0.058] (1,601) |
| NFL | treatment | 11,669 | 2,527 | 63.2 | +0.231 [+0.124, +0.338] | −0.099 [−0.159, −0.034] (1,565) |
| NHL | control | 7,140 | 3,168 | 28.0 | +0.168 [+0.117, +0.216] | +0.084 [−0.065, +0.197] (230) |
| NHL | treatment | 7,106 | 698 | 6.2 | +0.497 [+0.406, +0.572] | +0.013 [−0.089, +0.118] (199) |
| all | control | 62,615 | 28,569 | 116.6 | +0.012 [−0.020, +0.047] | −0.099 [−0.142, −0.052] (3,580) |
| all | treatment | 58,682 | 6,848 | 28.0 | +0.231 [+0.174, +0.286] | −0.099 [−0.138, −0.055] (3,266) |

Maker-fee sensitivity adds about +0.012 to the as-entered column everywhere; the full table is in the box result.

## What each does
- **Fills per game:** as entered, treatment fills about a quarter as often as control (28 vs 117 per game overall). Taking at the quote would fill every order that has depth, so fills per game would rise, but depth at the quote held on only a handful of the priced orders (2 NBA control, 5 NBA treatment; unknown elsewhere), so the real fill gain is unmeasured.
- **Verdict timeline:** days to 550 per arm read 0.0 as entered (the order count is already past 550 in every cell, so this number says nothing about independent evidence) and 24.5 (control) / 31.0 (treatment) days for NHL if taking. That NHL figure is an upper bound that counts unknown depth as holding.

## Read these before using the numbers
- The as-entered column counts filled contracts only. Treatment's large positive P&L (+0.23) comes from which orders fill after waiting 60 s, not from a measured edge; it should not be read as one.
- Only about 6% of orders (3,580 of 62,615 control) have an archive quote at most 300 s old, so the taken-at-quote column rests on a small, possibly unrepresentative subset.
- Orders within a game are heavily repeated; intervals are game-clustered but the order counts are not independent evidence.
