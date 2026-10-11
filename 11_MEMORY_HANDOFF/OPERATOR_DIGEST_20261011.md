# Operator Digest — 2026-10-11 (W67.1)
- NBA player-points tracking is live in shadow mode (no money, no orders). Counts: market types 37→40, prop families 1→2.
- NFL injury snapshots are collecting before kickoff; first real capture worked today. Thursday's game will be picked up automatically.
- Found and fixed a blind spot: the "is this arm silent?" alarm wasn't watching the new NBA arm.
- Not proven yet: the preseason test wrote no rows because Kalshi has no NBA points markets open. Still zero real money at risk.

**W67.2 (forward test, day one setup):** The bot now checks that a market actually exists on the practice exchange before ordering, so the 404 errors should stop. Practice-money stakes on the football "shadow" bets were being rejected (261 rejects); a one-line ID fix means 36 were accepted in the first ten minutes after deploy. Still zero real money at risk. Tomorrow after the MLB game I read day one. Two small decisions waiting for you: NBA and NHL shadow bets are not staked (GG-570, GG-571).

## W68.3 — NFL totals: does venue and weather help? (no)
We tested whether stadium type (dome, turf) and game-day weather forecasts make our NFL over/under predictions better. They did not. Across 816 games from 2023-2025 every version was slightly worse than the model we already have, and the differences are within noise. Even using the actual observed weather, which is not available before a game, did not help. So no new model, no pre-registration, and no money or live settings were touched. We could not compare against Kalshi totals prices because no pre-2026 history exists. Next idea if you want it: train on a longer weather history (2015-2025) with just one wind/cold adjustment.
