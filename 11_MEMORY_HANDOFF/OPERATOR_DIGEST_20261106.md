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
