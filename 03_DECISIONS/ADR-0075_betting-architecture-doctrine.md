# ADR-0075 — The betting architecture: edge is aggregation > interpretation > application, at play-level granularity

**Status:** ACCEPTED 2026-10-14 21:55 PT (operator: "I accept ADR75. yes - add D5. definitions are good - grounded in reality bc
we've talk you to trust but verify."). Drafted by the strategic window from the operator's words, 21:30–21:47 PT ·
**Date:** 2026-10-14 · **Builds on:** ADR-0068 (horizon doctrine), ADR-0073 (one deep engine per sport), ADR-0074
(process integrity) · **Closes:** the generality-vs-edge open decision (decided EDGE, operator 2026-10-14 21:30 PT)

## Context — the operator's words (verbatim; quote, never compress — window error W16)

2026-10-14 21:30 PT:
> "How many times do we have to say it - a lot of my 'thesis's' were made before I even ran a terminal window. I expect most of
> them if not all of them to get shattered - if they do I couldn't care less - if they prove true - I still don't give a fuck. I
> care about one thing - I WANT TO WIN. We're going with edge - and we're gonna start piping in the PAM into the NFL, NBA, MLB and
> NHL (starting with NFL and NBA) - this is going to be a portion of our Syndicate32 bridging - it needs to stay dynamic enough
> that we can port it easily and do mass application but we'll keep it substantive for when it matters most. Let's segment
> accordingly."

2026-10-14 21:38 PT:
> "let's not make it so general though - what i mean by 'edge' when presented with a two sided coin is simply building on
> comprehensive betting architecture, this side requires our attention a bit more now. If I ask you what teams runs the most
> cover 6 against 3 wide out sets that's motioned to the boundary, matched with volume and success rate - then I ask you to tell
> me what it means - you better be able to tell me. but that's not even the hardest part. data aggregation > data interpretation
> > data application. Whats the hardest? I'll make it easy - data application is the basic question: cool info, so what? it's a
> never ending race - one that we'll continue to chase again, and again, and again, and again, and again, and again, and again.
> But THAT is the level of granularity I expect. THAT is what we'll build out for our decision trees, our filtering mechs, our
> cluster designs, our cross-reference compatibility, our momentum looping, our temporal evolution, our structural tensions, our
> seat interface - our ENTIRE betting architecture. I don't just want to dilute it to something as simple as 'no more generality
> go edge' - it's not that simple and should never be treated as such."

2026-10-14 21:47 PT:
> "structural tensions: where the architecture strains, seat interface: deep mapping of sports-eyes to cells. a lot of your
> window is actually bringing my strategic vision to life, documented and placed into the file cabinet efficiently. i'm
> actually doing my job. i assumed that was already piped into the project - if it hasn't then we need to open up the
> scaffolding to get those built lol - anyways, the deep PAM tier will be a multi layer effort between me and you (Claude).
> right now - we just need to get the ball rolling on at least building it out foundationally."

## Decision

### 1. What edge means here
Edge is the betting architecture, built to play-level granularity and run through one chain for every factor:

| Stage | Question | Example (the operator's) |
|---|---|---|
| **Aggregation** | Do we have the fact, point-in-time? | Every defensive snap: coverage shell, offensive personnel, formation, motion and its direction, result; rate of Cover 6 vs 3-WR sets motioned to the boundary, with volume and success rate, as of before each game |
| **Interpretation** | What does it say? | This defense's tendency against that look, against the league baseline; stable trait or short-run noise |
| **Application** (the hardest; never finished) | Cool info — so what? | This week's opponent lives in that look → expected efficiency on those snaps → drives → the simulated score distribution → team total, spread, the boundary receiver's prop → against the price → bet or pass, and how much. Re-derived every week |

A factor that stops at interpretation is not done. Every factor class in every engine (ADR-0073) must reach application: a
stated path from the fact to a price, tested against the market.

### 2. The eight components of the architecture
The same granularity governs all eight. Definitions are the operator's where he gave one (**bold**); the rest are the window's
working descriptions, **confirmed by the operator 2026-10-14 21:55 PT** ("definitions are good"), marked *(window, confirmed)*.
Confirmed means a working definition to build against, not a frozen one — trust but verify: a scaffold that shows a definition
is wrong records it as a structural tension and brings it back to the operator.

| Component | Definition | Exists today | Gap | First scaffold |
|---|---|---|---|---|
| **Decision trees** | *(window, confirmed)* The per-band trees that turn factors into a probability; depth governed by horizon (ADR-0068) | Per-cell thin models (LR+Platt, probit); NFL engine scaffold (possession Monte Carlo, W73.3) | Trees are shallow everywhere (largest pre-game set 18 features) | Engine stage 2: factor classes enter the NFL simulation through one feature interface |
| **Filtering mechanisms** | *(window, confirmed)* What turns an evaluation into a bet: edge vs price net of fees, listing/liquidity, correlation, risk gates | Edge threshold, C4 risk gates, demo-fill policy (ADR-0072), listing pre-check (GG-564) | Filters are per-cell and price-only; no factor-aware filter (e.g. skip when the matchup read is low-confidence) | A filter layer fed by the engine's confidence, not just its point estimate |
| **Cluster designs** | *(window, confirmed)* Grouping players, units, schemes and situations so sparse samples borrow strength | PAM v4: 15 NBA archetypes + modifiers, 50 hand-classified players (DS-01) | No team/scheme/situation clusters; PAM NBA-only | PAM core schema shared by all sports; NFL position-group taxonomy |
| **Cross-reference compatibility** | *(window, confirmed)* Every factor and output fits together across markets, bands and sports | `pregame_shadow/contract.py`, NFL `INTERFACE.md`, registry keyed (market, band) | No shared factor schema across sports; each arm has its own features | One factor schema + point-in-time view used by every engine |
| **Momentum looping** | STRATEGY_OVERVIEW.md Strategy J (follow / fade price momentum) *(window, confirmed; scope beyond J open)* | Price archive cron (`archive_market_prices.py`), Kalshi candles | Strategy J never started | Price-path features from the archive, tested as a filter, not a model |
| **Temporal evolution** | *(window, confirmed)* How tendencies change over time — recency, decay, regime change | Point-in-time contracts (NFL event store, injury builder), frozen models | Tendencies treated as static within a model; no drift or regime detection | Rolling, as-of tendency features with stability tests ("trait or blip") |
| **Structural tensions** | **"Where the architecture strains"** (operator) | Pieces of it: gap log, hygiene audits, runtime registry, surface budget (ADR-0074) | No single map of where the betting architecture itself strains (e.g. a factor that cannot reach application, a cell no engine serves, signals that contradict) | A tension register per engine, reviewed at every wave close |
| **Seat interface** | **"Deep mapping of sports-eyes to cells"** (operator) | Nothing — registry cells carry status, not the expert lens | Every cell lacks the mapping from what a sport-knowledgeable eye would read to that cell | A seat file per sport: for each cell, the factors a sports eye reads, the free source for each, and its stage (aggregated / interpreted / applied) |

### 3. PAM (Player Attribute Matrix, DS-01) into every engine
Order: NFL and NBA first, then MLB and NHL. Segmented so it ports for mass application and stays substantive where it matters:
- **Core (sport-agnostic):** one schema — player → archetype mix (weighted hybrid) + modifiers + effective_from / effective_until
  (point-in-time, QTI-01) + classifier + confidence + version; one store; one read path for every engine.
- **Sport taxonomy:** per-sport archetypes. NBA's 15 exist; NFL position-group archetypes from the Syndicate32 bridge first.
- **Mass tier:** automatic, data-derived archetypes for every player, refreshed on a schedule.
- **Deep tier:** a **multi-layer effort between the operator and Claude** (operator, 21:47 PT) for the players who matter most.
- **Now:** build it out foundationally — core schema, store and NFL/NBA taxonomies first; the deep tier's working method is
  set with the operator when the foundation exists.

### 4. Standing calls made the same evening
- **MLB** goes idle for live betting after the World Series and becomes the look-back corpus (retrospective of the
  architecture, execution post-mortem, MLB engine built off-season on a full season, first PAM port tested on known outcomes).
- **NBA** is the engine's speed lane (≈1,230 games a season vs ≈270 NFL); NBA engine work starts by Wave 77 beside NFL.

## Consequences
- **Measure D5 — ACCEPTED 2026-10-14 21:55 PT ("yes - add D5"),** added to CLAUDE.md's distance table the same evening: per live
  sport, (a) how many of the eight components have a built, tested scaffold, and (b) how many factor classes have reached each
  stage — aggregated / interpreted / **applied** (a tested path from the fact to a price, compared with the market). Only (b)'s
  applied count is the race; aggregated alone is not progress toward edge.
- Every block that adds a factor reports which stage it reached (aggregated / interpreted / applied).
- The scaffolding columns above are the backlog the Waves 75–80 plan draws from (`04_EXECUTION/ACTIVE_QUEUE.md`).
