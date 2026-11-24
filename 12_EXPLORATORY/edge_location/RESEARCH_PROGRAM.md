# The edge-location research program — foundational scaffold

**Last reviewed:** 2026-11-20 (SW-9). Program EDGE in 02_ARCHITECTURE_DESIGN/HYPOTHESIS_DOCTRINE.md (Part II.1); its Part I binds here.
**Operator, 2026-11-20 10:10 PT:** "a scaffolding matrix or a dissertation eliciting the protocols and procedures / operations / testing /
parameters etc etc that you'd like to have FOUNDATIONALLY (we can't bottleneck it by being too specific yet - needs to have enough
dynamism to conceptually grow)."
The first tests of each branch are frozen in HYPOTHESIS.md (3cead0f) and run in Wave 123. This file is the program around them: what each
branch is about, how it grows, what it needs, and how its answers flow into the bot.

## 1. The question and why now
After two weeks of building the router, the evidence says the popular game lines an hour before start are efficient (Kalshi sits on the
books' consensus), per-leaf forecast edges sit near zero, and execution effects are large. The bot's method holds, but the method needs
somewhere to find value. This program maps that somewhere, by mechanism, and keeps the map honest as data arrives.

## 2. The scaffold matrix
Rows are branches (mechanisms). Columns are what every branch must have before it can steer a build. A cell marked "grows" is
deliberately open: it is filled as data and priority allow.

| | H1 Attention | H2 Timing | H3 News latency | H4 Execution / liquidity | H5 favourite-longshot / H6+ (open slots) |
|---|---|---|---|---|---|
| **Mechanism** | fewer eyes → slower correction of mispricing | information not yet in the price far from start; drift toward the close | the market digests news over minutes | spread capture minus adverse selection | e.g. cross-market coherence, structural (settlement-rule) quirks, venue gaps |
| **Where to look first** | props, team totals, alt lines, period lines | T1 band (12-48 h), 6 h | NBA lineups / scratches, NFL inactives, injury reports | families and horizons with deep books and stable mids | grows |
| **Arm it would feed** | FADE / RIDE / POT OF GOLD per family | entry timing for every arm | MOMENTUM (news arm) | a new arm: two-sided quoting | grows |
| **Data it needs** | settled prices by family (archive); a consensus where free | archive snapshots at 24 h / 6 h / close; shadow model p | timestamped news (Muse snapshots), Kalshi trade prints | book at submit, depth samples, real fills | grows |
| **Data it lacks today** | free consensus for props / team totals | consensus at early horizons (closes only) | trade-print history before 11-10 | queue position, fill-through modelling | grows |
| **First test** | W123.1 | W123.2 | W123.3 | W123.4 (simulation) | — |
| **What SUPPORTED changes** | wiring order by family | depth budget into T1, earlier entries | a news-reaction arm | a demo quoting test (operator decides) | grows |
| **Reopen trigger if parked** | a free consensus for a new family; a larger n | early-horizon consensus; new features | a new event type; trade-print depth | better fill modelling; lower fees | — |

## 3. Protocols (program level; HYPOTHESIS_DOCTRINE Part I applies in full)
- Every test under a branch is pre-registered on its own, with its own data window, before any read.
- Branches are judged independently. One branch's result never changes another branch's frozen test.
- Interactions are their own hypotheses (H1 x H2: are props looser far from start? H3 x H4: do quotes get picked off around news?),
  stated and tested only after both parents have a first answer.
- A branch with UNDERPOWERED results keeps collecting on its schedule; it does not get a second, wider test to force an answer.

## 4. Operations
- **Data that must keep flowing:** the ~20-min price archive (all families, props included), the book at submit on every order, Muse's
  timestamped snapshots, free consensus closes (NHL now; more as Muse finds them), settlements.
- **Cadence:** first tests in W123; the weekly evidence look carries the router-level lines; the window re-reads the matrix at every
  wave close and moves cells from "grows" to concrete as data arrives.
- **Instrumentation the program will ask for** (registered as backlog only when a branch needs it): consensus at early horizons; Kalshi
  trade-print capture going forward; queue-position estimates for resting orders; event timestamps on every snapshot record.

## 5. Parameters (program defaults; changes are dated lines in HYPOTHESIS_DOCTRINE §I.6)
- One round cost = spread at submit (or backfilled) + fee; an effect under one round cost is not an edge.
- Intervals: 90%, clustered by game (by event for H3).
- Retrospective split: first 2/3 fit, last 1/3 judged, by date.
- Minimum events to judge H3: 30 per event type; minimum games for a family verdict in H1 / H2: stated by each test's power line.

## 6. How the program grows
- A SUPPORTED branch spawns child hypotheses: finer loci (family → band → leaf), other sports, the interaction with another branch.
- A NOT SUPPORTED branch is parked with its reopen trigger, and its matrix column stays visible.
- New branches enter at STATED in the H5+ column with a mechanism and an arm; the window registers them.
- If every branch is parked, the program's own answer is written: the method holds, and the edge is not in these markets at this scale.
  The operator then decides scope (another venue, another market class).

## 7. Status board (updated at each wave close)
| Branch | Status | Next step | Date |
|---|---|---|---|
| H1 | NOT SUPPORTED on 18 judged non-headline families; 18 prop families UNDERPOWERED (no fit window) | Re-run props at 30 held-out games per family; dense prop capture (W124.4); judgeable date in the power ledger (W124.1) | 2026-11-20 |
| H2 | NOT SUPPORTED, parked (R&D): drift not predictable at 24 h / 6 h; arm CLV +0.86c gross vs 1.08c fee | Reopen with new features or early-horizon consensus; fill-level CLV → H-EXEC-4 (W124.3) | 2026-11-20 |
| H3 | NOT SUPPORTED on NBA injury / starter news (repriced < 1 min); NBA confirmations, NFL inactives UNDERPOWERED | Props and spreads around news (H1 x H3); trade prints forward (W124.4) | 2026-11-20 |
| H4 | NOT SUPPORTED, parked (R&D): 0 of 18 cells, gross negative before adverse selection | Reopen on 5-min snapshots (W124.4) or a lower fee | 2026-11-20 |
| H-MEAS-1 | Ran 11-23 (#558): CLV LICENSED in 1 of 50 families (MLB F3); 19 NOT LICENSED (10 miscalibrated), 30 UNDERPOWERED | Retest as games accrue; licensed families score on CLV | 2026-11-23 |
| H5 favourite-longshot (H-EDGE-5) | STATED from H-MEAS-1: close slope > 1 on NHL ML 1.71, NBA ML 1.26, NHL TT 1.10 | W125.3 on the 2025-26 Kalshi history | 2026-11-23 |
| H5+ | open | — | — |
