
## W95.3 — the box tells the truth (T-1480, PARTIAL)
- **Shipped (#378, live on box):** deploy-lag alarm (box HEAD vs origin/main, 45 min bound; measured median 2.1 min over 325 deploys) and a 30-min start grace for the t4_mlb silent-arm, so a :00 game start no longer reads false RED. Real outages still alarm.
- **Not solved:** demo orders refused for `insufficient_balance` (demo cash is $3,287, stakes $0.50). The cash guard is active yet logged zero skips; likely resting shadow orders reserving cash. Cause unproven — GG-1481.
- **Registered:** GG-1480 (docs-only pushes under 12_EXPLORATORY run the full deploy gate, up to 23 min).
- **Operator action:** none. Demo-only plumbing.

**W95.2 (proof lane) — partial.** I built the tooling to re-check the frozen evidence on the full data archive and fixed a bug that wrote some NFL results to the wrong folder. The actual re-check of the 13 frozen cells did not run yet: the box drops long connections, so the settlement data is only about 60% fetched. Good news from the inventory: the box does hold the data two cells were missing locally, so those misses look like a local-copy problem, not a flaw in the cells. No frozen file was touched, no money at risk, nothing needed from you. Moves: PROOF (no measured change yet).

## Wave 96.3 (backlog panel and demo balance)
- Your rolling backlog now shows on the Visual Dashboard. I checked it on the live box and it is there.
- The demo account refused some orders earlier this month for lack of funds. They stopped by themselves on Oct 29. I don't know why they stopped.
- Every refused order now records the account balance, so the next one will show the cause. I added no funds and changed no bets.
- Nothing is needed from you. If refusals return, a demo-account top-up is the fix. No real money was involved.
- The "MLB winter posture" item was not part of this block, so it has not been run.
