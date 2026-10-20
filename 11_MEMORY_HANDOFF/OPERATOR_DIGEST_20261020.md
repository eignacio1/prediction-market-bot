
**W80.2 — NBA opens (partial).** Pillar: DEPTH (NBA). The first NBA factor, pace, was tested against Kalshi's game-total prices: the market already prices it, so there is no edge there. That is a clear result, not a failure. The tester had a bug that made last week's run silently empty; it is fixed. The opening-night check of the new NBA cells could not run because the games had not been played yet; it is the one thing pending. Still zero real money at risk.

## W80.3 — NFL granularity index (DEPTH)
We built the reusable machine that finds a team's splits (like run success against loaded vs light boxes), ranks them against history, and crosses them with the opponent. Your example was the test. Honest result: the "loaded box" rank is mostly noise at today's sample sizes, the "stuffed on runs against light boxes" trait is real and stable, and the cross does not yet beat plain season-long ratings. Too few Kalshi markets exist to say whether prices miss it. Still zero money at risk; nothing placed, nothing running changed.

## W80.4 — Foundation docs (PLUMBING)
- Your point was right: several core docs in the infra, security and code-reproducibility folders were stale or wrong for months.
- Every foundation doc is now listed in one registry (83 entries) and marked live, a record, or superseded.
- Three live docs that contradicted the system were rewritten: kill-switch runbook, access matrix, vendor risk. Two obsolete ones were archived.
- A silent check now runs in the session scan and speaks only when a doc goes stale.
- Not done: most live docs are registered but not yet verified. That is GG-970 for the gap agent. GG-971 records root-run services and a shared SSH key.
- Nothing about trading, orders or capital changed.
## W80.1 — Where the retail flow is
The recorder that watches the order books had been finding nothing since yesterday afternoon; it was looking at the wrong clock. It is fixed and working. We now have a table showing which markets are thin: the money-line markets are deep and tight, while player props such as passing yards are thin and wide, so a small bet may not fill. You approved the first thin-market test: NFL passing yards, simulated only, no money at risk. We still lack real pre-game depth for football; it starts arriving this weekend. I merged one change before its checks passed; it was repaired within minutes. Moves: breadth and depth.

**W81.2 (NBA depth):** We studied what happens to a basketball team's scoring when a key player sits out. The extra points do go up (about 1.75 more for the rest of the team when a main scorer is out), but which teammate picks them up is mostly random. We could not check whether Kalshi's prices already account for it, because we have no record of when each absence was announced. That is logged as a gap. This moves the DEPTH part of the plan. No money at risk; nothing changed in trading.
