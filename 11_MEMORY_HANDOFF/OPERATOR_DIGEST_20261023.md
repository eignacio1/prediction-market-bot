
## W85.3 — safety plumbing (no money moved)
- Fixed a hole in the check that decides whether a new scheduled job may be installed: it could wave a job through while the system was in a red state. It now refuses unless the only red item is that job's own first-run notice. Three retired NBA preseason jobs were taken off the books.
- Built the new stop-loss counter: it now counts money at risk in open bets and in games that finished but have not been scored yet, not just realized losses. It saves its state, reloads it after a restart, and stops everything if the state is missing or damaged.
- Only the MLB pregame bot feeds it so far, and it does not yet block individual orders. That is logged as GG-1082, so the kill-switch item (GG-441) stays open.
- Still zero real money at risk. No limits, stakes or orders changed.

**W86.3 (fills and size).** Our demo fills lose far more often than the orders we skip (25% vs 48% win rate). The cause is that the market tends to hit us when we're wrong, not that we chose bad prices; the price we picked actually helped. We can't yet say how much is queue position, because the system never recorded where we sat in the line. Size available at the best price is now measured for each market type. Pillar: EXECUTION. No money at risk, nothing new running.

## W86.2 — what the market's price ladders imply
Measure only; no orders, no money at risk. We read the implied outcome spread out of the market's own ladders for 45 NFL, 28 NBA and 19 MLB games. The market uses almost one spread per sport, and our fixed NFL width is bigger than the market's because ours counts the 3 and 7 point jumps. Of about 2 million ladder snapshots, roughly 150 contradict themselves after fees, only NFL team totals show any persistence, and none has a size we can confirm, so nothing here is tradeable yet. Pillar: DEPTH (and EXECUTION evidence). Nothing applied to a price.
