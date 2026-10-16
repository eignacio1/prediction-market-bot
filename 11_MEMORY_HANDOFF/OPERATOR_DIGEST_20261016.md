
## W76.2 — NFL second factor (plain English)
We tested a new idea for the football model: how many regular starters are missing from a team's lineup that week (line, receivers, defense). It was nearly independent of what the model already knew, so it was a fair test. Result: it roughly ties the current model on moneyline, spread and team totals, and does not help on game totals. It never clearly beats it. The betting market's price is still better than our model. No real money, orders or live systems were touched. This moves the DEPTH measure (NFL factors tested: 6 to 7 of 16).

## W76.4 — runtime map made visible (plumbing)
The list of everything running on the server is now fully checked (76 of 76) and every item has an alarm or a written reason. A green/red "surface budget" light is built into the daily scan, the project page, the Live Terminal and the Visual Dashboard. It is built but not yet live: the change is waiting on a failing check that comes from another block's NFL files (not this work). No money, orders or sizing changed. Nothing is needed from you; it ships once that check is fixed.

## W76.1 — emergency stop proven; fill test is starved of cash
We pulled the emergency stop on the live demo bots and every one of them stopped within 30 seconds, and restarted within 10 seconds of releasing it. No real money was involved. The fill-rate experiment is mostly limited by the demo account running out of cash, not by the rule being tested, and its slower arm will not reach the planned sample size this season. One decision for you: whether to exclude a day when the exchange itself was down from the rule's automatic shut-off check. Pillar moved: EXECUTION.
- GG-860..GG-879 (standing gap agent) (auto): Gap agent ticks 1-3: 1 gap resolved, 23 retired to archive, 20 severities filled, 39 gaps bucketed; loop stopped manually.

## W77.3 — ledger read side (PROOF)
Three places that read our trade records used to quietly skip or reset when a record was damaged. They now say so out loud, and that fix is live on the server. The 34-trade gap between "closed" and "resolved" turned out to be 41 trades, all explained: a weekly summary file was simply out of date. Nothing was wrong, no results changed, and no real money is involved. One housekeeping item is left: a follow-up list of similar readers (GG-885) still needs its claim row filed from a clean checkout. Nothing for you to decide.
**W77.1 (demo fill test):** The test of the new order-placement method nearly got shut off by a false alarm, because the exchange itself had a bad hour and we counted that against us. That's fixed: exchange outages no longer count, and cancels now retry. We also found why so many demo orders were rejected: the practice account runs out of cash during game windows because accepted orders tie it up. The bot now checks cash first and skips cleanly. It doesn't add fills, since cash is the real limit. Still no real money at risk. Early numbers (2 days) say the new method won't reach its sample size this season in any single market.
- W77.2b (auto): W77.2b: Friday-report window null (REPORT slope -0.0008 [-0.0034,+0.0014], n=145) from existing hourly candles; PR #273.
- BLOCK-AP (auto): Block AP: private repo eignacio1/sports-intel-archive + write-scoped deploy key created for Muse; documented.

## W78.3 — NBA opening night readiness (BREADTH / B1)
A sha-identity bug meant no NBA game cell could ever flip; fixed (#274). Box dry run: 9 of 12 cells flip-ready; 3 team-total cells blocked because Kalshi never lists KXNBATEAMTOTAL (GG-891, B1 ceiling 9). Points rows no longer mask a silent game arm (#275, GG-892). Runbook written. Nothing for you to decide; the real B1 move lands on the 10-21 read-back.
- W78.2 (auto): W78.2 PARTIAL: thin-market inventory done (275 series, 310,858 markets); candles for 8 NFL families sampled; Part B not started.

- W78.1 (plumbing): the map of everything that runs is now live on the dashboards (73 components, none stale). Its overall budget light is RED because the NFL QB shadow arm has logged nothing for ~18h; that is not from this block. The gap agent's progress (open gaps 185, down 1 since its first tick) now shows on the scan, /project and the Visual Dashboard. Zero money at risk.
- W79.4 (auto): W79.4 branch cleanup: remote branches 167->34, auto-delete on, 36 archive tags, PRs #133/#144/#146 closed, #149 kept

## W79.1 — Red to green
- The NFL quarterback alarm was a false alarm: the model had done its job early, and the monitor wrongly expected a later row. Fixed and live on the server.
- Every sport's monitor now checks only its own files, so one working model can't hide a broken one.
- The overall health light is still red for one reason: the live MLB service is running slightly older (unchanged-in-substance) code. Your call: restart it, or relax that rule.
- Plain-English pillar: plumbing plus breadth (one fewer false red). No money at risk.
