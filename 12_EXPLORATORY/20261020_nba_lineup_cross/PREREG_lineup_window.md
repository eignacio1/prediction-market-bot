# PRE-REGISTRATION -- NBA lineup-window price test (W83.2)

**Frozen:** 2026-10-22 (committed before the capture is installed, hence before its first row). **SHADOW only:** no
order, position, stake or kelly (kelly 0). Registers no cell. Capture: `scripts/nba_lineup_window_capture.py`.
**Pillar / measure:** DEPTH, D5(b) NBA -- lineup factor interpreted -> testable. **Looked at no data**: the only price
history that exists is the 2025-26 candles (GG-985), which could not observe the window and are not used here.

## Question
When the official injury report adds an Out to a rotation player, does the KXNBAPTS book for his teammates move by
what the lineup model predicts, and is any remaining gap tradable? Operator, 2026-10-16: "Do we have mechanisms
within the bot, spots within our decision tree, ranges within our architecture - to identify these opportunities AND
FUCKING BLEED EM OUT?"

## Factor
Absent player's role x the absorber. Role classes and team-level shifts are the W81.2 estimates
(INDEX_ENTRY_LINEUP.md, 2016-2025): creator out +1.75 pts to teammates, starter out +1.00, rotation out +0.34.
Player-level redistribution was not stable (split-half r 0.117), so the *model* prediction uses the class shift
allocated to each teammate by his share of the team's points, not a player-specific usage model.

## Unit and sample
- An **event** = one report change (a player added as Out, or Doubtful/Questionable -> Out, or Out -> Available) in a
  game with a KXNBAPTS market on the player. Games where the player has no market are `event_unresolved` (counted,
  not scored).
- Qualifying = absent player in the top 9 by season minutes; game not yet tipped; `book_before` age <= 20 min.
- **Judged n = games (clusters)**, not markets: all absorber markets in a game share one outcome path. First scored
  look at **30 qualifying games**; second at 60. No read below 30. Cluster bootstrap by game, 10,000 draws.

## Measures
1. **Model-predicted move** per absorber market: shift the absorber's points distribution (Normal; centre from the
   pre-change ladder-implied median, sd from the ladder spread) by his allocated class shift; predicted dP = change in
   P(over strike).
2. **Measured move**: mid(book after, the second follow-up run, ~30 min) minus mid(book before). Mid = (yes_bid +
   yes_ask)/2; a market with no two-sided quote at either time is dropped, not imputed.
3. **Pricing share** = sum(measured dP) / sum(predicted dP) over qualifying markets, ratio of cluster sums.
4. **Realization**: the absorbers' realized points shift vs their season mean in games with the absence, from final
   box scores (the same sign test the factor needs to be REAL).
5. **Residual**: realized outcome minus the post-change price (settled yes=1/no=0 minus mid_after), clustered by game.

## Verdicts (exhaustive, checked in this order)
- **INVISIBLE** -- fewer than 30 qualifying games by 2027-01-31, OR more than half of report changes are
  `event_unresolved` or have a stale `book_before`. The capture cannot see the window; fix the capture, do not read price.
- **NOT REAL** -- realization (4) has a 95% CI containing 0 or the wrong sign: the lineup shift is not in the outcomes.
- **REAL-AND-PRICED** -- realization CI > 0 and the pricing-share CI lies inside [0.7, 1.3], with the residual CI containing 0.
- **REAL-NOT-PRICED** -- realization CI > 0, pricing-share CI upper bound < 0.7, and the residual CI > 0 (the book
  under-reacts and the outcomes pay for it).
- Anything else is **INCONCLUSIVE at n** and extends to the next look; it is never rounded to a verdict.

## Expected outcome (stated before looking)
Modal **REAL-AND-PRICED** (~50%): the report is the last and most public lineup news, and desk traders already hold
the beat-reporter and team-announcement information that precedes it. **INVISIBLE** ~25% (a thin sample in a
roughly eight-week window: ~12/100 historical markets had a single rotation absence). **REAL-NOT-PRICED** ~15%.
**NOT REAL** ~10%. This cell sits at the most-attended end of the efficiency gradient; a null here is informative, not a failure.

## Guardrails
Capture-only; the test reads the store `exp_output/NBA/LINEUP_WINDOW/` (box). No look before judged n. A change to
any number above after the first row is a new pre-registration, not an edit.
