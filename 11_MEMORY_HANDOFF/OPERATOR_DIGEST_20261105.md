
## W100.1 engine lane (2026-11-05)
Pillar: DEPTH and PROOF. The hockey model's low goal totals were partly a bookkeeping mismatch; fixed in a new module, shrinking the bias from 0.080 to 0.059 goals a game, with no change in forecast accuracy. The rest is year-to-year drift and early-season uncertainty. For basketball, several games on last night's slate went unlogged because the small server runs out of memory and kills the jobs; nothing was installed, and the fix is to relieve server load. No money at risk, no orders touched.

## W100.2 proof lane (STANDARD)
- Cell 10 of the MLB totals test is retired, as you decided. Cells 9 and 11 keep running.
- The NFL totals model lost to the market on all 72 games. It did not lean high or low; where it disagreed with the market it was wrong more often than right.
- Weather could not be checked: 61 of 72 games had no weather data. That gap is worth fixing before the next NFL model.
- The proof calendar now has second-look logic, but I could not regenerate it because the box connection dropped (GG-1720).
- Nothing needs your decision.
## W100.3 — box memory + picks sheet (plumbing)
The box kills fewer runners than two days ago (142 → 39 a day) but not zero. The cause: the early-day shadow runners could pile up on top of each other. I wrote and merged a guard for them; it is not on the box yet, and it goes on only when you approve `t3_lock_stagger_install` by name. The picks sheet works (134 games, 2614 picks, reasons on 90%), but one bet can show as two picks (GG-1690), and yesterday's results can't show until games settle. Two leftover bugs are fixed. No real money, no model or stake changes.

## W101.1 (NBA coverage / NHL totals)
- The NBA v3 arm now records every game it misses and why; the tool to read that from the box is merged. Box numbers are not read yet (they wait until after 07:30Z).
- NHL totals: a fix for the model's habit of predicting too-extreme totals helped a little on paper but did not clear the bar we set in advance. Result: NO. Nothing changes in the live bot.
- Still zero real money at risk. Pillar: DEPTH (partly plumbing).
- W102.5 (auto): W102.5 (B-043) deleted 32 stray origin branches; stray branches 35 -> 3; w83-3 check found nothing lost, no GG.
