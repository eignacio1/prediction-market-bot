# Operator Digest — 2026-10-11 (W67.1)
- NBA player-points tracking is live in shadow mode (no money, no orders). Counts: market types 37→40, prop families 1→2.
- NFL injury snapshots are collecting before kickoff; first real capture worked today. Thursday's game will be picked up automatically.
- Found and fixed a blind spot: the "is this arm silent?" alarm wasn't watching the new NBA arm.
- Not proven yet: the preseason test wrote no rows because Kalshi has no NBA points markets open. Still zero real money at risk.

**W67.2 (forward test, day one setup):** The bot now checks that a market actually exists on the practice exchange before ordering, so the 404 errors should stop. Practice-money stakes on the football "shadow" bets were being rejected (261 rejects); a one-line ID fix means 36 were accepted in the first ten minutes after deploy. Still zero real money at risk. Tomorrow after the MLB game I read day one. Two small decisions waiting for you: NBA and NHL shadow bets are not staked (GG-570, GG-571).
