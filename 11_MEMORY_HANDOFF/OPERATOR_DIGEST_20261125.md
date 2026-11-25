# Operator digest 2026-11-25
- NBA props: tested whether an absent player's rebounds, assists and threes really pass to teammates in full. They don't: about a quarter to a third does.
- Pricing with that fix beat the plain average on a full season nobody had scored before, on all four stats. Rebounds only barely.
- Shadow only, switched off, no money. No profit figures yet; those need forward games.
- Your call: switch on the logging for it (small, no new service). Proposal is in the queue.

## W126.5 — NFL factor splits (plain English)
We tested whether five things (who's at QB, rest days, the officiating crew, forecast weather, team matchups) help us pick a side on NFL team totals and alternate spreads and totals. On last season's games, none of them found a profitable route after costs, so those bets route to ride the market or no bet. That closes only this one test, parked for later. One caveat: the prices were reconstructed from the betting consensus, because Kalshi has no history for these markets before 2026. The new code is merged but switched off. Turning it on for the box would start collecting real 2026 rows for a proper second look; I need your OK for that, and it adds nothing new to run. No real money involved.
# Operator Digest — 2026-11-25

- W126.1 (auto): W126.1 partial: #562 and #565 merged (router per-day skip totals, archive_dense gate read); box reads pending.

## W126.4 — Kalshi combo (parlay) markets
Kalshi parlays turn out to have almost no standing price: 97% of open combos have no quote at all, and only 2 of 7,203 NBA same-game combos were two-sided. So this is a quote-hunting job first, not a P&L one. I built the pricer (it prices combos off the same game simulation, so correlation is carried) and a logger that is switched off. The test plan is written down before any data exists. Nothing is live and no money is at risk. Your call: whether to turn the logger on (it needs the install task approved by name).

## W126.3 — MLB engine (STANDARD)
- Built the MLB game simulator: it prices moneyline, run line, totals, team totals and batter hits from the same draws. 12 tests pass.
- Scored on all 2,429 games of 2026. It does not beat Kalshi's prices on any of the four families (moneyline closest, -0.004 Brier). That is a report, not a verdict: it becomes one input to the tree.
- It under-prices home/team runs and over-prices hits. Home-field and park are the missing pieces.
- Not done: opening-day dry run, registry row (so D4/D5 MLB did not move), PR/merge. Nothing live changed; no orders.
