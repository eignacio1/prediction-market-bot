
## W106.2 — the cost wall (2026-11-10)
We measured what a trade costs before any edge. Buying and selling on game lines costs about 1.5–2.3¢ per contract each way; player props and team totals cost 4–8¢. Resting orders instead of crossing the spread still lose money in every price bucket. Put against that wall, the fades we found earlier all lose; the only things that clear it are the 11 longshot cells held to settlement, which are in-sample so far. One check is not done: confirming Kalshi's fees against our own demo fills, because the safety classifier blocked the read. No real money at risk, nothing live changed.

**W106.1 — pot-of-gold graft.** The bot's single decision tree now has a fifth branch for long-shot bets, so it can route fade, ride, momentum, long-shot or no-bet. All of it is paper only: the 17 long-shot cells have only been tested on past data, so none can place an order yet. Still zero real money at risk. Next step is testing them on settled markets they haven't seen.
- W107.3 (auto): W107.3 B-061 NBA availability lead: no evidence v3 leads Kalshi (42 games, descriptive); coverage 3 of 3 confirmed.
- W107.1 (auto): W107.1 B-059 edge map delivered: 39-hypothesis EDGE_MAP.md/json plus /visual panel (#452), no verdicts changed.
