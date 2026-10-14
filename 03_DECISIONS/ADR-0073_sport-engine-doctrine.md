# ADR-0073 — The scale doctrine: one deep engine per sport prices the whole board

**Status:** ACCEPTED (operator directive, 2026-10-13 17:43 PT: "Wire it into our core docs - the project needs to reverberate this convo and read it back to me when I call for it.") · **Date:** 2026-10-13 · **Supersedes:** nothing (it makes explicit what the operator held from the start) · **Canonical summary:** `CLAUDE.md` § "The scale — one deep engine per sport" · **Read-back:** `/vision` (`.claude/commands/vision.md`)

## Context — the conversation, in the operator's words (2026-10-13, strategic window)

- On Syndicate32 (syndicate32.com, an NFL advanced-stats platform by an Eagles analytics creator he follows; already cited 2026-09-25 as the granularity bar for every arm, *a bar, not an endorsement*): "the level of granularity is simply absurd - there's a clear bar that we aren't even remotely close to getting to (NBA PAM is sort of a similar albeit structurally general template)."
- "I want to turn it completely inside out but before that I want to get our foundation set cus I'm not bouta pay $20 for something that we can get without it."
- "Do you see what I'm trying to get to? at the SCALE that I'm trying to build for?"
- "I had thought that was explicit early on in the project - but apparently not."

What the platform does, from its public page (read 2026-10-13): opponent-adjusted team and unit profiles; QB efficiency per dropback against man / zone / specific coverages; matchup comparisons across passing, rushing, protection, pressure, coverage, special teams, injuries, play callers, penalties, rest and home field; fair values vs market across spread, moneyline and total; live game state; historical backtests with game-condition filters.

Where the project stood that day: NFL pre-game models condition on team + QB; the largest pre-game feature set anywhere is 18 features with 0 qualitative (MLB player hits); no live model uses matchup, weather or qualitative factors; 107 registered cells, most served by thin cell-specific models.

## Decision — the doctrine

1. **The bar.** Syndicate32-level granularity — or deeper — is the target for **every** sport the bot trades (NFL, NBA, NHL, MLB), not one. Automated, continuously updated, and feeding a machine that prices every line rather than a page a human reads.
2. **The unit of depth is the sport, not the cell.** Each sport gets **one deep engine**: ingest the finest event-level data that sport has (NFL plays, NBA possessions, NHL shots, MLB pitches); build every factor class once, point-in-time (player, unit, scheme/coverage, matchup, personnel/availability, rest, venue, weather, officials, coaching, qualitative); every market family and every band reads from it. Cell-specific thin models are interim scaffolding, kept only until the engine serves that cell and beats them under a pre-registration.
3. **One engine prices the whole board.** The engine outputs the joint distribution of a game (a game / drive / possession simulation or equivalent), so moneyline, spread, total, team totals, player props and parlays come out of one model and stay mutually consistent. The correlations parlays need come from the same simulation — this is the only honest route into the parlay and long-shot classes on the roadmap ("after the standard board is built").
4. **The data layer is the work.** The edge of a platform like Syndicate32 is its data layer. Build it from free sources first (nflverse play-by-play / EPA, FTN charting — coverage man/zone and pressure from 2022 — participation, snap counts, injuries; the equivalents per sport). No paid service ($0 rule). A factor that only a paid source supplies is registered as a gap, not bought.
5. **Depth gets a continuous lane.** Building one sport's engine is months of staged work, not a three-block wave. Every wave carries a DEPTH lane until each live sport has its engine; each factor class lands as a tested, point-in-time, pre-registered addition (beat the frozen model first; the market comparison is reported, judged only where pre-registered).
6. **Template, then repeat.** NFL is built first, explicitly as the template for all four sports; NBA follows on the same template once in-season data exists; then NHL and MLB.
7. **Unchanged guardrails.** No real capital, `kelly_fraction` 0, pre-registration before a cell's first row, no score read below judged n. The generality-vs-edge question (`CLAUDE.md` § "Market efficiency gradient") stays an **open operator decision**: the deeper the engine, the more it is aimed at efficient markets; every pre-registration says "thinner edge expected" where that applies.

## Consequences

- New DEPTH measure **D4** (CLAUDE.md distance table): per live sport, the engine's stage — event-level data layer · factor classes built point-in-time · board priced from one engine.
- Strategic windows plan every wave against this doctrine: a wave with no DEPTH lane says why.
- Wave 73 starts the NFL engine: Syndicate32's factor taxonomy rebuilt and mapped to free sources, then the event-level data layer, then the first factor class tested against the frozen model.
- The foundation comes first (Wave 72): a deep engine fed from untrustworthy ledgers and deploys produces confident garbage faster.
