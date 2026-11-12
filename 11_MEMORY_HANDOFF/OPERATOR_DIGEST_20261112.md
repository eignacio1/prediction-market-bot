# Operator Digest — 2026-11-12

- B-076 (auto): W111.1 B-076: a losing look closes only the FADE arm; NFL game total T1/T2 reopened as SHADOW (PR #482, c592dda).
- B-077 (auto): W111.2 B-077 doctrine-conformance audit: 41 code decision points, label fixes + banned-word test merged (#481), #480 merged

## W111.4 — NBA granularity index (DEPTH)
Built the NBA "situation" index: 24 entries, each with the split, how the team ranks against history, the matchup cross and the market map. 18 were scored per leaf, by arm, on games the fit never saw. None survived the multiple-comparison correction, so those leaves are routed to NO_BET for now, which is a routing result and not a verdict on any cell. NBA depth moved 10 to 11 of 17. Still zero real money at risk. NFL, NHL and MLB entries are not built yet.
**W111.3 (trees).** The bot's routing step now picks, for each kind of bet, which of its strategies to use, instead of leaving most bets unrouted. We also tested two more strategies (the long-shot side and following early price moves). Early price moves look promising for NHL moneylines, but that is a lead, not a result. A forward test is locked in. Still zero real money at risk and no orders placed. The full "wired end to end" count stays at 0 of 117 because filters, sizing and real fills are not built yet.

## W112.2 — a losing test no longer closes an arm; sizing rule built
- The two NFL game-total cells that lost their test are now recorded as "test closed, parked for research." Every betting route stays open for them, as you ruled.
- Built the rule that decides how much each route bets: the flat demo stake, cut by per-game, per-day and per-route limits, and correlated same-game bets count as one. It is not connected to orders yet.
- Still zero real money at risk. Kelly stays 0.
- Next: the window connects the sizing rule to the demo-order hook. Two things need a decision from the window, not you: the demo limits ($5 per game, $50 per day, $25 per route) are my placeholders, and the box needs a read-only task to run the 14-day replay on real rows.

## W112.1 (trees)
The bot's decision trees can now take the matchup-style filters as part of the decision, for NBA. Seven NBA filter rules passed our test, but none survives the stricter multiple-comparison check, so treat them as possibly luck; they only change paper (shadow) decisions, no orders. NFL and NHL are not wired yet (NFL lacks stored weather/matchup data; NHL waits on its own build). Still zero real money at risk. Nothing needed from you.
