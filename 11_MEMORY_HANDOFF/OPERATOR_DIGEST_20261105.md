
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
## W101.3 flex lane
- Branch cleanup: the exact list is written (32 branches safe to delete once you approve; nothing deleted). One call is yours: the NHL data-layer branch.
- Picks sheet: fixed the double counting, so one opinion now shows once instead of per arm and per team side. Waiting on CI to merge.
- Not done yet: tonight's picks results and the memory-crash check need the clock to pass (about 07:30Z). The next window picks both up.
- Plumbing only; no pillar moved. Still zero real money at risk.

**W102.4 (quant lane).** We split the NFL practice-bet "ADOPT" gain into two parts: about 1 cent from paying a better price, about 18 cents from simply which bets got filled. So the gain is mostly a selection effect, not a better-price win. We also listed every pre-registered test together and adjusted for how many we run: the ADOPT result holds up, but the EXP-037 game-totals "ruled out" call would not hold up under that stricter view. The dashboard now shows how old the proof calendar is and turns red after a day. Nothing changed in any rule or verdict; no real money at risk. Pillar: PROOF.

## W102.3 (flex lane)
The picks sheet no longer lists the same pick twice: one night went from 259 rows to 127 distinct picks. Last night's write-up is done, and it is only a description of one night, not a verdict. We found 2,259 fake-money orders were refused since Oct 16, all before Oct 29, probably because the practice account ran out of cash. The fix that records the balance on every refusal is waiting on its tests and will merge by itself if they pass. We also found a bug that prices some "No" orders wrongly (GG-1771). I did not fix it. No real money was involved.
## W102.1 — NBA engine misses (STANDARD)
v2 missed 12 and v3 missed 18 games on 11-04. Cause: a kernel out-of-memory burst on the 961 MB box killed or starved their runs, and nothing retried or logged the kills. The OOM stopped after the 11-05 02:11Z lock stagger. I merged a small catch-up job plus an attempt trace (PR #425). **It isn't installed, so coverage is unchanged until you approve `nba_engine_catchup_install` by name.** NHL goalie/rest (B-012) and the NBA store lag check (B-017) were not started. I registered GG-1772 to 1774. The block title said "without OOM", but I found no non-OOM miss.

## W102.2 - the NFL ADOPT decision, ready for you
The test says posting-and-waiting beats the old way on NFL practice orders. Most of that gain is which orders happen to fill, not a smarter price, so it is not proof of edge. The change is built and tested but switched OFF; nothing about any bet changed. Three yes/no questions are waiting: accept the NFL addendum, pick which day counted as the look, and accept the draft second-look rule for EXP-038. Still no real money at risk. One check did not finish (a report re-run timed out), so the 11-04 wording is not re-confirmed.

**W103.3 (in-play math):** Built two models that price a live game from the score and time left, one for basketball, one for hockey. Both beat "pre-game only" at every checkpoint on last season's games (1,229 NBA, 1,312 NHL). They were not compared with Kalshi's live prices, because the archive can't tell us what the score was at each price snapshot. The code is in PR #433, which is not merged: its automated checks never started. No money or orders touched. Moves: PROOF/DEPTH.
