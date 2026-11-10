# Operator Digest — 2026-11-06 — W104.1 (B-048, EXECUTION / E3)

## W103.2 — Overreaction and regimes in Kalshi prices (B-045) — STANDARD
- We measured what Kalshi prices do after a big jump: do they snap back (a fade would pay) or keep going (a follow would pay)?
- All 22 market series got an answer. Three snap back reliably: MLB player hits (mostly a bid-ask bounce, not real), NFL team totals (~29% given back), NHL totals (~51%). Two more look like it under a looser test. None keep going.
- Calm vs jumpy hours are labeled, with no look-ahead. This is a measurement only: no cell, no orders, no verdict.
- Pillar: PROOF/DEPTH (measure P2 and D3 context). Stage: aggregated and interpreted, not applied.
- Also logged your approved CI trim (PR #436): exploratory result files skip the full test run, plus a local pre-PR check script.
- Waiting: main is red from a W103.4 file (PR #435); #434 and #436 merge once it is green.
**W103.4 (red alert, fixed).** The bot was pricing "No" bets backwards on the practice exchange, and the report scored those bets backwards too. Both are fixed and running on the server. No real money was ever involved.
The NFL "adopt" result does not hold up once the bad bets are removed; it reads inconclusive. You said Restart, so the NFL test now counts only bets placed after the fix (from 6 Nov, 01:03 UTC). The old result is kept on record as superseded.
Pillar moved: execution (fills are now measured correctly). Still open: one small timing-audit script has the same blind spot (GG-1783).

## W104.3 — landing Wave 103's stranded work
Pillar: EXECUTION / PLUMBING. Three finished research pieces that were stuck unmerged (price give-back, NBA/NHL in-play math, a CI speed-up) are now in the project, each only after its automatic tests passed. The puzzle of why paper fills seemed to win less often than their price implied turned out to be a bookkeeping bug (buy-NO orders were scored backwards), not a real trading problem; once rescored, fills still win a bit below price, so no edge is shown. The after-the-fix check cannot be done yet — there are no newer fills to look at. A small reader-script bug was fixed too. No real money at risk; nothing needed from you.

## W104.2 - how far to follow the model off Kalshi's price
We measured how much weight NBA's models deserve against the market's own price. The answer is about zero on every bet type: the models did not beat Kalshi's line once tested on games they had not seen. Samples are small (about 30 games per type), so this is "no evidence yet", not "proven useless". NFL, NHL and MLB were not measured because their test cells are sealed. No real money touched; north-star pillar: PROOF.
- **Question:** why do our filled demo orders win less than the ones that never filled?
- **Answer: the data we log cannot explain it.** Using price, sport, days to game and hour of day, the covariates account for none of the gap on held-out days (E3 raw -1.5pp, adjusted -2.6pp, 90% interval -7.8 to +2.4; not distinguishable from zero).
- **Fills do lose a little after they happen:** about -1.2c one minute later, near -0.5c on cheap contracts and -4.1c at 0.80 and above.
- **Fill model:** weak but honest (AUC 0.62, calibration error 2.1%); fill rate drifted 17.5% to 15.5% train to test.
- **Limits:** NFL/NBA/NHL demo only, YES-side pre-epoch only (post-epoch n=0), MLB headline E3 not reproduced. Non-fill side is unreliable (GG-1793); intended side, mid, depth and fill time are not logged (GG-1794).
- **No placement change; no decisions needed.** Candidate rules are named in RESULT.md but not pre-registered.
- Merged: PR #439 (CI green). Read `12_EXPLORATORY/quant_w104_fills/RESULT.md`.

## W105.1 — blend-weight test (plain English)
We asked: does our engine's view actually nudge Kalshi's price in a useful direction? Earlier data (about 30 games) could not say. We worked out how many games it takes to tell: roughly 100 to 2,000 per market type, and a few types (NBA totals, v3) will probably never get enough this season. The test plan, with four scheduled peeks at 100/200/300/400 games, is now written down and frozen before looking at any new data. Expect "can't tell yet" most likely. A read-only check was added that shows only game counts until a peek date arrives. No money, no live changes.
## W105.5 — ride/fade board wired to live markets
The program that watches live NBA/NHL/NFL prices and decides ride, fade or skip is built and merged. It logs every decision and can place a small practice-account order. It is not running yet and places nothing: it needs your OK to install, and a separate switch for orders. No real money is involved. Moves EXECUTION (the order path now exists; zero fills so far). Needs from you: approve installing `ride_board_install`.

## W105.3 — MLB engine data layer (DEPTH)
We now hold every 2024 and 2025 MLB pitch (1.42 million) on the laptop, free, with checks that nothing is duplicated or looks ahead in time. A first simple game model trained on 2024 and tested on 2025 is a hair better than guessing the league average, but not by an amount we can tell from luck. That was expected; it is a plumbing test, not edge. Nothing runs on the server and no money is at risk. Next: compare it to real market prices, then add bullpen, park and platoon factors.

## W105.4 ride/fade board
We tested whether riding or fading big sudden price moves makes money after spreads and fees. It does not, yet: no cell passed on held-out games, so nothing is promoted and no orders can fire from it. Five long-shot candidates are logged as untested forward watches and cannot trade. NBA, NHL and NFL showed no edge at all. Still demo only, zero real money at risk. Next data arrives at MLB opening day, around 2027-03-25.
Moved: BREADTH (ride/fade cells), no new cells earned.

## W105.2 — order data and placement study (EXECUTION)
The bot now records the context of each demo order (the side, book sizes, timing), so we can finally explain why fills lose. We tested placement rules on 65,217 past orders: no rule makes fills win. Fills lose more as the price rises, from half a cent under 20c to four cents above 80c. Skipping resting orders at 50c or higher trims the loss slightly but does not change final profit. Resting at the bid gains about half a cent per order but fills 29 points less often. I recommend, but have not applied, a pre-registered shadow arm for "no resting at 50c or higher". Still zero real money at risk. Not yet confirmed: a real order row carrying the new fields (none placed since the merge).
