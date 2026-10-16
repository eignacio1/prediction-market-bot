# The granularity index — the intent behind every decision tree, filter and bet

**Status:** standing doctrine, recorded by the strategic window 2026-10-16 at the operator's request ("please log in the project
accordingly so the granularity index that we're gonna continue to arm our decision trees + filtering mechs + betting architecture
are being built with the right intent"). It implements ADR-0075 (accepted 2026-10-14) at the level of a single fact; it does not
amend it. Cross-referenced from CLAUDE.md § "What winning looks like" → "How this binds work" (edge bullet) and from the project doc
`claude/NORTH_STAR_AND_DISTANCE_TO_OPTIMUM.md`.

## In the operator's words (2026-10-16, verbatim)

> 08:03 PT: "The granularity I'm expecting: There are 701 qualified QB seasons through 6 games in the past 20 years. 2026 Bo Nix
> ranks 701st out of 701 in average pass length (4.9 air yards per attempt). His avg pass was thrown behind the line of scrimmage in
> the 2nd half on Thursday. Do we have mechanisms within the bot, spots within our decision tree, ranges within our architecture -
> to identify these opportunities AND FUCKING BLEED EM OUT? Just one of many examples."

> 08:04 PT: "Don't be so focus on now building something QB specific right now (we'll build all of that as we proceed) - I'm simply
> talking about the granularity index and how these are the type of subtle things that we can use to our advantage."

> 08:12 PT: "What if a team ranks #2 in the league in success rate when using a loaded box (8 defenders or more) against the run but
> drop to #26 in the league when using a light box against the run - but their opponent that weak is #14 in the league when faced
> with a light box BUT get tackled behind the line of scrimmage on 75% of their runs. How would bets get placed pre-game? How would
> bets get decided mid-game? I'm just giving examples - but this level of granularity is crucial - is it even a surprise why our bot
> isn't beating the market yet? ... we don't have a single substantive band built out yet - but we do have the architecture - which
> (considering the scale of this project) is IMPRESSIVE."

The examples are illustrations, not a build list (08:04 PT). Do not turn them into one-off features (window error W17, LITERAL).

## What the granularity index is

For each sport's engine, the index is the growing catalog of **conditional facts** the engine can state and use. Each entry has
five parts; an entry missing any of them is not finished:

1. **The split.** A metric cut by the situation that changes it: box count (loaded ≥ 8 / light), coverage shell, personnel, motion,
   down-and-distance, half, score state, field zone, opponent tier, venue, rest. Season averages hide exactly the thing that wins.
2. **The rank against history.** Where this player, unit or team sits against every comparable one at the same point in a season
   ("701st out of 701 through 6 games"), point-in-time, with how stable that metric is at that sample size (trait or noise).
3. **The matchup cross.** Both sides of the same split, joined: what the defense is in a light box *and how often it shows one*,
   against what the offense does against a light box *and how often it gets stopped behind the line*. One side alone is a stat;
   the cross is the edge.
4. **The market map.** Which lines the entry should move and in which direction (a rushing-yards prop, a team total, the spread, the
   total, a receiving prop, the first-half lines), and which execution band can act on it.
5. **The application.** The tested path from the entry to a price, against the market's own price: REAL-NOT-PRICED / REAL-AND-PRICED
   / INVISIBLE / NOT REAL (ADR-0075's aggregation → interpretation → application). Only the first is a bet.

The index is where subtle things live. The market prices the headline numbers (77.2: the closing line already holds the team/QB
base). It is less likely to price the cross of two splits, the tail of a distribution, or a shift that shows up in the second half.

## How it arms the betting architecture (ADR-0075's eight components)

| Component | What the index gives it |
|---|---|
| Decision trees | The branch points: each split is a node ("defense shows light box > X% vs this personnel" → node). Deep at the pre-game horizon, stripped in-play only where measured speed pays for it (horizon doctrine, ADR-0068). |
| Filtering mechanisms | The tails and crosses worth acting on: rank-vs-history extremes and matchup mismatches pass; the median does not. |
| Cluster designs | Teams and players grouped by how their splits behave (PAM archetypes and unit clusters), so thin samples borrow strength. |
| Cross-reference compatibility | The matchup cross itself: offense split × defense split × tendency frequency, joined on the same definition. |
| Momentum looping | In-game: the split's frequencies observed so far feed back into the remaining-game estimate (Strategy J). |
| Temporal evolution | The week-by-week rank as the sample grows; a tail that holds at week 6 vs one that regresses. |
| Structural tensions | Where an index entry cannot be built honestly (no free source, sample too small, definition mismatch): registered, not faked. |
| Seat interface | What a sports eye would read in each cell ("a run-stuff defense hiding a light-box weakness against an offense that gets stuffed"), mapped to the cell that prices it. |

## The operator's two questions, answered for the box example

**Pre-game.** The engine estimates how often the defense will show a light box against this offense (its tendency by personnel,
down and distance, and score state), multiplies through the cross (defense #26 vs light-box runs; offense #14 vs light boxes but
stopped behind the line 75% of the time), and feeds the resulting run-play distribution into the game simulation. The simulation
prices the rushing props, the team totals, the spread and the total from one draw. A bet is placed where that price beats the
market's by more than the threshold and the fillability floor holds.

**Mid-game.** The same cross is re-read with what has happened: box counts actually shown so far, stuffs so far, the score state
(a trailing team passes more and a defense lightens its box). The in-play layer reprices and acts only where the market lags the
update by more than our measured reaction time (the T4 thesis; a stripped in-play tree must be paid for in speed).

## Rules for building it

- Every factor class a block adds reports, for each index entry: the split, the rank method, the cross, the market map and the
  stage reached. Measured in D5(b).
- Free data first. Where a split needs charting a free source does not carry, it is a registered gap, never bought. Free sources
  that carry box counts and similar charting must be checked before relying on them (assumption until a block confirms it).
- An entry is never read below its judged n, and every cross is pre-registered before it touches a live cell.
- Built per sport as each engine reaches that stage (ADR-0073: NFL as the template, NBA next, then NHL and MLB), not as one-off
  features for the example of the day.
- What wins is accumulation: many small, subtle, correct entries, each with its market map, not one pot of gold.
