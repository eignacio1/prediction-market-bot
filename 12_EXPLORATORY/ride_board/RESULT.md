# Ride / fade board — RESULT (W105.4, B-053)

Rules: `RIDE_BOARD_PREREGISTRATION_2026-11-06.md` (Part 1 frozen before any P&L). Numbers: `results.json`. Code: `quant/ride_net.py`, `analyze.py`. Per contract, after the quoted spread and Kalshi's exact fee. Intervals are game-clustered. Earlier 70% of games fit, later 30% held out.

## Headline
**After spread and fees, no family has a ride/fade rule that passes out of sample.** Zero cells are HELD_OUT. The router has 0 new live cells. The 103.2 "market overshoots after a 3-sigma move" finding is real in mid-prices and is eaten by crossing the spread twice and paying two fees.

## By sport
- **NFL.** 103.2 flagged FADE on team totals and totals. Net of costs the fade loses: team totals -0.09 per contract fit, -0.08 held out (interval entirely below 0); totals -0.12 fit, -0.25 held out. Following loses too. Spreads and moneylines are flat to slightly negative. Held-out samples for moneyline are thin (12 events). **Cells for the router: 0.**
- **NHL.** Totals FADE looked strong in mid-prices; net it is -0.37 fit and -0.52 held out, because books are wide. The tight-book fit result (+0.14) did not hold (-0.04 held out, n=11 events). Team totals: same story. Moneyline and spread held-out samples are too small (9-13 events) to judge. **Cells: 0.**
- **NBA.** Season is young (23 held-out games). Every primary cell is negative fit and held out; team totals -0.20 / -0.18. **Cells: 0.** Nothing here supports a ride/fade rule yet.
- **MLB (context, router already covers 12 calibration cells).** Totals FADE is the only primary cell with positive fit (+0.022) and positive held-out (+0.036) but its interval includes 0 [-0.008, ...]. Tight-book and settle-exit views produce 4 more cells that clear the status rule uncorrected.

## What we are not claiming
Of 160 held-out tests, 4 pass the status rule on secondary views; at this alpha, chance gives about 4. They are written as IN_SAMPLE forward candidates (judged n 118-740 event-bearing games), not promoted. Holm over the 28 primary tests: smallest adjusted p is 1.0. KXMLBHIT's positive FOLLOW-to-settle cell rests on 19 held-out games.

## Live for the router
Cells in `ride_cells.toml`: 13 -> 18 (5 new MOVE rows, all IN_SAMPLE). RIDEABLE new cells: **0**. NBA/NHL/NFL ride/fade cells: 1 -> 1 (no new cell earned a row, because no primary-view cell has positive fit net). The rows are inert until 105.5 wires a MOVE lookup, and the router still requires HELD_OUT or FORWARD_PASSED.

## Next
Forward rows accrue from MLB opening day (~2027-03-25); interim n reports 2027-06-01 and 2027-07-15; scored looks at judged n. NBA/NHL need more games before a held-out split carries power (re-run at ~150 games per family).
