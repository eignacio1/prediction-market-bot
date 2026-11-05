# The last settled night, in plain English (W102.3, 2026-11-05)

Night: the 2026-11-03 Pacific slate, read from the 2026-11-04 picks sheet. All 134 markets on it have finalized. Fake money only. Descriptive, not a verdict.

## The night
- **11 NHL games** (30 market groups: moneyline, spread, game total). No NBA or MLB that night.
- **259 raw picks became 127 distinct picks** once the same bet seen from both sides, and from both arms (T2, T3), is counted once (GG-1690 de-dup).
- **127 of 127 got a fake-money order placed. 54 were filled** (43%). 73 never filled.
- Every pick has a result: **55 hit, 72 missed.** Taking every distinct pick at Kalshi's price when the pick was made, the average was **-8.6 cents per contract**.

## The filled picks (n = 54)
- They hit **8 times out of 54 (15%)**. Their average price at the pick was 31 cents, so about 31% was needed to break even. Average: **-17.4 cents per contract**.
- The 73 picks that did **not** fill hit **64%** and averaged **-2.1 cents**.
- So fills landed on the low-probability side. That is the adverse selection E3 is built to see. n=54 from one night is a description, not a rate.
- Caution on cause: GG-1771 (found this block) says NO-side orders go in at a mirror-image price. That alone could produce this pattern, so do not read the 15% as the market punishing the bot's model.
- The contract-weighted fill-price figure from the same data is not quoted, because of GG-1771.

## The games where the bot differed from Kalshi most
Every arm gave the same probability on each market and the sheet flagged no game as arms-disagree that night, so I ranked games by the biggest gap between the bot's chance and Kalshi's price on one pick.
1. **DAL at WSH, total.** Bot said NO on "6+ goals" at 60% vs Kalshi 46% (gap 14 pts). Filled. Missed. Its NO-7 (gap 11) filled and missed; NO-5 did not fill and missed.
2. **COL at CBJ, total.** Bot said NO on "6+" at 52% vs Kalshi 41% (gap 11). Filled. Missed. NO-7 filled and missed; NO-5 did not fill and missed.
3. **ANA at VAN, moneyline.** Bot said ANA YES at 71% vs Kalshi 60% (gap 11). Filled. Hit.
In two of three the "under" side lost together, which is one outcome (a high-scoring game) counted three times, not three independent misses.

## What this does not tell you
One night, one sport, one pipeline. Fill matching is per ticker and side from the order log, not an order id on the sheet, so a pick with more than one order is approximate.
Collector: `collect_night.py` (read-only). Analysis: `analyze_night.py`. Sheet de-dup: `pregame_shadow/picks_sheet.py`.
