# Pot of gold: definition (W105.6, B-055, 2026-11-05)

## Plain English
Some people buy cheap tickets that almost never win (a 6c "yes" that pays $1). Some markets also list the near-certain side at 94c.
The old finding (favourite-longshot bias) is that the cheap tickets cost more than they are worth and the near-certain side costs
less than it is worth. If that holds on Kalshi after Kalshi's fee and the gap between buy and sell price, we can take the other side.
This block defines that bet, measures it on all four sports, and builds a paper-only decision module. It does not place orders.

## Classes (price = the listed YES contract's mid)
1. **Single-line longshots**: YES mid 1-15c (buckets 1-5, 5-10, 10-15c). Includes big-hitter player props (e.g. KXMLBHIT 3+ hits) which are only listed as longshots.
2. **Mirror favourites**: YES mid 85-99c (buckets 85-90, 90-95, 95-99c).
3. **Multi-leg combos**: the live API lists `KXMVECROSSCATEGORY*` collections (2-91 legs, `mve_selected_legs`). In the 1,000-market sample they had zero quotes and our archive does not hold them. They are **defined but not measurable today**.

## Routes (what we buy)
| Route | Applies at | Buys | Bet is |
|---|---|---|---|
| FADE_LONGSHOT | YES mid 1-15c | NO at 1 - yes_bid | the longshot is overpriced |
| TAKE_FAVOURITE | YES mid 85-99c | YES at yes_ask | the favourite is underpriced |
| BUY_LONGSHOT | 1-15c: YES at ask; 85-99c: NO at 1 - bid | the lottery ticket is cheap (the opposite finding) |
FADE and TAKE are the two views of one bias, kept separate because the listed contract differs (a prop is only ever listed as the longshot).

## The bar each route must clear (all required)
Net per contract after Kalshi's exact fee (`quant/money.fee_rate`: multiplier x 0.07 x P(1-P), MLB multiplier 0.5, others 1.0) with entry at the quote (spread paid);
fit on the earlier 70% of games, tested on the later 30%; game-clustered interval with lower bound > 0; at least 30 fit contracts, 20 held-out games,
5 held-out outcomes of the rarer kind (a sample with no losses has no variance and proves nothing); Holm across held-out candidates;
orders only after status HELD_OUT or FORWARD_PASSED. **Epoch rule (GG-1771):** fill-based evidence counts only NO-side fills from 2026-11-06T01:03:42Z; this block uses quotes, not fills, so the rule does not bind the measurement but binds any forward fill evidence.

## Later (operator 09-25 sequencing)
Parlay pricing needs each engine's joint distribution (correlations). Deferred until the engines exist. Multi-leg combos stay unpriced.
