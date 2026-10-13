# Operator Digest — 2026-10-13

* NBA player points: a new model that accounts for who is playing and for how many minutes did slightly better than the current one on past games, but only for the "15 or more points" bet. It was worse at 25 points.
* You accepted it as a formal test (EXP-040) and it is now frozen, so it can't be tweaked after the fact.
* It is not running live yet. Wiring it in needs a server deploy from you and should wait until the opening-night work is clear of the same code. Until it runs live, no results count.
* Data caveat: injury reports for Jan–Apr 2026 couldn't be found, so the test used partial data.
* No real money at risk; nothing changed in trading.
- PLUMBING-hook-timeout (auto): Governance scan hook split into 0.03s cached wrapper + full scan to beat the 30s hook timeout (PR #235, awaiting merge).

## W70.1 - forward test (execution pillar)
- Fixed the bug that made the demo-fill safety switch trip falsely; it is live on the server.
- The switch is still off on purpose: 8 real cancels on MLB hit orders genuinely failed (the demo exchange returned errors), so turning it back on would just trip again. Demo money only; nothing real at risk.
- The NFL "+0.39 per fill" is not proof of anything: no fills happened after kickoff, but it comes from about 4 correlated games.
- Your call: re-arm anyway, or diagnose the MLB cancel problem first (recommended).
