# DOCTRINE — the binding strategy, in one place

**Last reviewed:** 2026-11-11 (SW-9, Wave 110) · **Owner:** the strategic window · **Review rule:** every wave close; a file in the
Doctrine stack below whose "Last reviewed" is older than 14 days is RED in the session-start scan (`scripts/doctrine_freshness.py`).

*Operator 2026-11-10 21:45 PT: "This CANNOT keep fucking happening. I don't want to keep building blocks that I'll need to fix eventually
bc of some shit you/another window reads thats 20 waves stale." This file is the answer: one short, dated statement of what is binding,
with sources. Where any other document disagrees with this file, THIS FILE WINS and the other document is stale - fix it or register it.
State (numbers, what is running) never lives here: it is the RUNNING SITREP at the top of `04_EXECUTION/ACTIVE_QUEUE.md`.*

## 1. What the bot is (operator 2026-11-10 21:35 / 21:41 PT; 10-26; 11-05; ADR-0077)
Layered decision trees that optimize every route. For every market the tree picks the ARM: **ride the market, fade it, momentum, pot of
gold, or no bet.**
- Layer 1 market state: price, move, ladder gap, book, time to start.
- Layer 2 filters built from the depth factors: matchup, lineup / usage, rest / travel, refs, weather, PAM, qualitative.
- Layer 3 a tree per cell that chooses the arm, depth set by horizon (ADR-0068).
- Then risk / sizing (Kelly 0 until G6, ADR-0048 / ADR-0076) and execution (fills that are not picked off, ADR-0072).
- The engine's simulated probability is one input to the tree, never the bet by itself.
- **A test that says "this pattern does not beat the market" is a ROUTING result** ("routes it to the correct path so that loss still
  WINS"), never a stop. Frozen tests judge cells and leaves; they never gate building (operator 11-09 21:29 PT).
- **A factor is APPLIED when it is a tested split in the tree**, scored per leaf: net after costs, held out, per arm. "Model Brier vs
  market" may be reported; it is never the verdict.
- `model_p > market + vig` is the FADE arm's entry rule, nothing more.
- Worked example (operator 11-10): simulations say the favourite wins 39 of 40; at 90c ride (+7.5c, small fee); at 97c no bet (+0.5c,
  one upset costs ~32 wins). The tree checks the simulation AND the price.

## 1b. Where we are, and the words we use (operator 2026-11-10 21:56 PT)
> "I literally do not want a single fucking chance of you or any window coming up to me talking about "no edge" bc we can't beat the
> fucking market we are SO FAR AWAY from anything that will be ready to beat the market - for fucks sake we can't even tell which PG's
> shoot better in the mid range with 2 minutes left when their lineup is filled with defensive players against a team ranked #4 in
> defensive rating but #22 in perimeter shooting + #16 in clutch defensive rating. WE ARE SO FAR AWAY."
- The project is at the start of the depth it needs. A cell, pattern or factor that loses to the market today is reported as a ROUTING
  result ("routed to ride / no bet in these leaves"), never as "no edge", "blocked", "ruled out" or a reason to stop.
- In words, RULED_OUT is reserved for a market that cannot be traded at all (no book, no liquidity, no data); it never means "our model
  lost". In the registry code, `CellStatus.RULED_OUT` on a frozen-test cell is that test's state machine and reads "the fade arm is closed
  for this cell; ride / no bet stay open" (operator 2026-11-10 21:59 PT; NFL game total T1 / T2, EXP-037 first look). Human-facing text
  says "fade arm closed (routed)", never "ruled out".
- Reports lead with what was built and which arm each leaf goes to; a model-vs-market number, if given at all, comes last.

## 2. The scale (ADR-0073, operator 10-13)
One deep engine per sport at Syndicate32-level granularity or deeper, every factor class built once point-in-time, one joint simulation
pricing the whole board (moneyline, spread, totals, team totals, props, parlays). Free data first; a paid-only factor is a registered gap.

## 3. The betting architecture (ADR-0075, operator 10-14 "EDGE")
Aggregation > interpretation > application. The eight components per sport: decision trees, filtering mechanisms, cluster designs,
cross-reference compatibility, momentum looping, temporal evolution, structural tensions, seat interface. The granularity index
(`GRANULARITY_INDEX.md`): the split, its rank vs history at the same point of a season, the matchup cross, the market map, the application.

## 4. Pricing (operator 10-21)
Start from the market's own probability plus out-of-sample-tested factor adjustments; a real bet gate; one pooled test per sport.

## 5. Horizon (ADR-0068)
Tree depth is governed by decision horizon: the longer the horizon the deeper the tree; a shallow tree must be paid for in measured speed.
Pre-game first, then carry the granularity inward.

## 6. Market classes (operator 09-25, 10-16, 11-05)
Standard board first; the pot of gold (big hitters, longshots, parlays) is part of the vision and is routed in the same tree. Retail-priced
flow (props, parlays, thin markets) before institutionally priced headline lines. Accumulation, "every damn cent", not one pot.

## 7. How work is chosen
- Four pillars and the distance table (CLAUDE.md § "What winning looks like"); every block names the measure it moves.
- Ranking (operator 10-27): 1 market-anchored, 2 one engine per sport, 3 granularity, 4 quant, 5 architecture, 6 PAM, 7 Muse, 8 expansion.
- Wave composition is the window's call (11-05); standing three blocks unless the operator asks; the build continues on every lane (11-09).
- Doctrine check at every wave close (W48): the premise and its strongest counter-evidence; something said but not built.

## 8. Guardrails (unchanged)
No real capital; Kelly 0; pre-registration before a cell's first row; no score read below judged n; installs only on the operator's
named approval; demo / paper actions are plumbing.

**Every closed cell is provisional (operator 2026-11-10 22:03 PT):** "every single "closed" cell will get reopened once I feel the project
is at a suitable state. We're clearly not even close to that yet lol". A RULED_OUT / closed-arm cell keeps logging where it can, is never
deleted or treated as final, and is reopened when the operator says the project is ready - his call, not a window's. Until the W111.1
engine fix lands, no window or block applies a new RULED_OUT to the registry (operator 2026-11-10 22:10 PT).

## Doctrine stack — every file below carries a "Last reviewed" line and defers to this file
| File | What it holds | Last reviewed |
|---|---|---|
| `CLAUDE.md` | session rules, north star, distance table, § "The architecture" | 2026-11-11 |
| `02_ARCHITECTURE_DESIGN/DOCTRINE.md` | this file | 2026-11-11 |
| `03_DECISIONS/ADR-0077_multi-arm-routing-doctrine.md` | the multi-arm routing rule | 2026-11-11 |
| `02_ARCHITECTURE_DESIGN/STRATEGY_OVERVIEW.md` | strategy history and the strategies A-J | 2026-11-11 (banner; body pre-dates §1) |
| `02_ARCHITECTURE_DESIGN/ARCHITECTURE_OVERVIEW.md` | system components | 2026-11-11 (banner) |
| `02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md` | the router | 2026-11-11 (banner) |
| `02_ARCHITECTURE_DESIGN/COVERAGE_TARGET_MATRIX.md` | the coverage target | 2026-11-11 (banner) |
| `02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md` | bands, live registry | 2026-11-11 (banner) |
| `02_ARCHITECTURE_DESIGN/GRANULARITY_INDEX.md` | the granularity index | 2026-11-11 (banner) |
| `01_SPEC/PREGAME_FEATURE_ARCHITECTURE.md` | pre-game feature classes | 2026-11-11 (banner) |
| `00_ADMIN/README.md` | navigation hub | 2026-11-11 (banner) |
| `.claude/commands/strategic-handoff.md` | the window's protocol | 2026-11-11 |
| `.claude/commands/status.md` | the status command | 2026-11-11 |
