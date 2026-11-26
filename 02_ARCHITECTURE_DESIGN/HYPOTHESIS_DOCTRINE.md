# Hypothesis Doctrine — how this project asks questions, and every question it has asked

**Last reviewed:** 2026-11-26 (W129.5: §II.8 historical backfill, registry check; earlier W124.1: Part II Consequence cells carry judgeable dates from the power ledger). **Binding with:** DOCTRINE.md (wins any disagreement), ADR-0077 (multi-arm routing).
**Operator, 2026-11-20 10:10 PT:** "a scaffolding matrix or a dissertation eliciting the protocols and procedures / operations / testing /
parameters etc etc that you'd like to have FOUNDATIONALLY (we can't bottleneck it by being too specific yet - needs to have enough
dynamism to conceptually grow) ... let's get a Hypothesis Doctrine doc where we have all hypotheses (including ones parked for R&D)
listed in comprehensive detail."
**Operator, 2026-11-11 16:51 PT (DOCTRINE §1b):** "a cell being closed isn't just closing the 'fade arm' - it's closing THAT SPECIFIC
HYPOTHESIS, for future research and development that we'll circle back ... a cell closing shouldn't mean anything is being closed but a test."

Part I is the scaffold: what a hypothesis is here, how one is born, tested, judged, routed and revisited. It is written at the level of
principle so it can grow; the numbers in it are defaults, and every one can be changed by a dated entry in §I.6. Part II is the registry:
every hypothesis the project has stated, live or parked. Part III is how both stay current.

---

## Part I — The scaffold

### I.1 What a hypothesis is here
A hypothesis is a falsifiable claim about **where value sits between a price and an outcome**, stated so that data the project can get
for free can say yes, no, or not yet. It always names five things:
1. **Locus** — where it lives: sport, market family, band (horizon), and leaf if it is that fine.
2. **Mechanism** — why it would be true (attention, timing, information, execution, structure). A claim with no mechanism is a pattern,
   not a hypothesis; patterns may be logged, never promoted.
3. **Arm** — what the bot would do if it is true (ride, fade, momentum, pot of gold, no bet, or a new arm such as two-sided quoting).
4. **Measure** — the number that decides it, net of real cost.
5. **Consequence** — what gets built, routed or parked under each answer.

### I.2 The hierarchy (how the tree grows)
Hypotheses nest, and the registry keeps the nesting:
- **Program** — a question big enough to steer waves ("Where does the edge live?"). It names branches, not tests.
- **Branch hypothesis** — one mechanism under a program (H1 attention, H2 timing ...).
- **Test hypothesis** — one pre-registered, falsifiable claim under a branch, on a defined dataset (one EXP).
- **Leaf hypothesis** — a test applied at one router leaf (sport x family x band x split). Leaves are what the router routes; most are
  created and judged by the weekly evidence look, not by hand.

A branch grows by spawning test hypotheses, each pre-registered on its own. A program grows by adding branches (any session may propose
one, with a mechanism; the strategic window registers it). Nothing has to be fully specified on day one: a branch may sit at "stated" with
no test until data or priority reaches it.

### I.3 Lifecycle and statuses
| Status | Meaning | Who moves it |
|---|---|---|
| STATED | Written with locus, mechanism, arm; no test yet | anyone, registered by the window |
| PRE-REGISTERED | Test frozen (commit SHA) before any outcome is read | the block that writes it |
| COLLECTING | Data accruing; no judged look yet | automatic |
| LOOKING | Inside its look schedule (sequential / weekly) | weekly evidence look |
| SUPPORTED | Met its pre-registered rule; earns its consequence (an arm, a build budget) | the test, then the window |
| NOT SUPPORTED → PARKED (R&D) | Failed its rule. The hypothesis is closed and parked; the cell keeps logging and is routed elsewhere | the test, then the window |
| UNDERPOWERED | Cannot be judged at current n; states the n and date needed | the test |
| SUPERSEDED | Replaced by a sharper hypothesis (linked) | the window |
| REVISIT | A parked hypothesis whose reopen trigger fired | the window |

Rules: a status change is a dated line in the registry with its evidence. **Parked never means deleted, and never means the cell, family or
sport is ruled out** (DOCTRINE §1b, §8). Every parked hypothesis carries a reopen trigger (new data, a larger n, a new feature, a new venue,
a season change).

### I.4 Protocols (foundational, apply to every test)
1. **Pre-registration before reading.** The test, its data window, its measure, its decision rule and its consequence are committed
   before any outcome is read. Deviations are dated addenda written before the result they would change.
2. **Held-out judgment.** Fit on earlier data, judge on later data (time split), or judge forward only. Never judge on the fit set.
3. **The game is the unit.** Rows, orders and contracts from one game are not independent; intervals cluster by game (or by event).
4. **Costs are real.** Spread at submit where logged, backfilled otherwise; the Kalshi fee schedule; adverse selection where the arm
   rests orders. A gap smaller than one round cost is not an edge.
5. **Many tests, honest control.** When a test scans many cells or leaves, it states how many and controls for it (BH, or the pooled
   posterior + e-process of router v2). A lone survivor among hundreds is a lead to re-test, not a result.
6. **Sequential looks are scheduled.** Forward hypotheses are looked at on the weekly cut (Tuesday 10:00 UTC) with an always-valid
   e-process carried forward; a skipped look is reported, never filled in.
7. **Three answers, always.** SUPPORTED / NOT SUPPORTED / UNDERPOWERED. UNDERPOWERED states the n needed and the date the current rate
   reaches it.
8. **Step back after repeats.** Three nulls of the same shape are a finding about the method or the plumbing; the next wave fixes the
   method instead of running a fourth test of the same shape (strategic-handoff step 9).
9. **Free data only.** A test that needs paid data is registered as a data limit, not run (operator 2026-11-17).
10. **No capital follows a hypothesis.** SUPPORTED earns an arm in demo (or a build budget). Real capital is decided only under G6
    (ADR-0076) by the operator.

### I.5 Operations (how hypotheses are run day to day)
- **Data plane:** the price archive (~20-min snapshots, props since 11-10), shadow ledgers (every forecast row with v1 and candidate
  arms), the arm-order log (book at submit since 11-18), settlements (Kalshi), event stores per sport, Muse's archive at a pinned SHA,
  free consensus lines. Evidence is copied off the box weekly.
- **Cadence:** pre-game shadow rows every cycle; arm orders per v1; the weekly evidence look every Tuesday; the strategic window reviews
  the registry at every wave close.
- **Where a test lives:** its pre-registration in 05_RESEARCH_EXPERIMENTS/ (EXP-*) or 12_EXPLORATORY/<topic>/PREREG.md; its result
  beside it (RESULT.md); its registry line here.
- **Who decides what:** a block runs a test and writes the result; the window updates the registry and routes the consequence; the
  operator decides frozen-test changes, new trading modes, new data families and real capital.

### I.6 Parameters (defaults; each change is a dated line here)
| Parameter | Default | Where it bites |
|---|---|---|
| Interval level | 90%, game-clustered | every verdict |
| Held-out split | first 2/3 fit, last 1/3 judged, by date | retrospective tests |
| Pooled routing rule | P(net > 0) ≥ 0.90 and a node e-value ≥ 10 (α 0.10) | router v2 leaves |
| Multiple testing | BH at q 0.10 across the cells a test scans | scans |
| Minimum n for a placement cell | as frozen in config/placement_policy.json | placement |
| Round cost | spread + fee per contract, from logged book | every net figure |
| Look cadence | weekly, Tuesday 10:00 UTC | forward hypotheses |
| Power target | 80% at the stated effect, for the "n needed" line | UNDERPOWERED answers |

### I.7 Growth rules (keeping it dynamic)
- New programs and branches are welcome at STATED with only locus, mechanism and arm; they gain tests when data and priority allow.
- A SUPPORTED test spawns its own children (finer leaves, other sports, other bands) as new test hypotheses; it never silently widens.
- A parked hypothesis may be re-tested only through a new pre-registration that names what changed (data, n, feature, venue).
- The scaffold itself changes by a dated edit to Part I, logged in DECISION_LOG.

---

## Part II — The registry

Columns: **ID · Program / branch · Claim (mechanism) · Locus · Arm · Test (where) · Status (date) · Evidence · Consequence / reopen trigger.**
IDs: an existing EXP / HYP id is kept; new ones take `H-<PROGRAM>-<n>`. Compiled by SW-9 from this window's verified results (W104-W122).
**The historical backfill (B-110, W129.5) is §II.8: every pre-registration file under `05_RESEARCH_EXPERIMENTS/` and `12_EXPLORATORY/`
now has a row here, and `scripts/hypothesis_registry_check.py` (alarm-only, in Docs Guard) flags any PREREG that does not. Verdict cells
quote the results file; where this block did not re-read a result, the cell says so rather than guess.** Experiments before EXP-025 left
no PREREG file (their records are in `RESULTS_SUMMARIES/` and DECISION_LOG); they are listed in §II.8 only where a file exists.

### II.1 Program EDGE — where does the edge live? (12_EXPLORATORY/edge_location/, frozen 3cead0f; research program in RESEARCH_PROGRAM.md)
| ID | Claim (mechanism) | Locus | Arm | Test | Status | Evidence | Consequence / reopen |
|---|---|---|---|---|---|---|---|
| H-EDGE-0 | Popular game lines at the close are efficient (the null) | ML / spread / total, ~1 h before start | NO BET / RIDE | all below | WORKING NULL (11-20) | Kalshi vs books NHL ML gap +0.16c, n 1,312 (W117.2); 0 arms at the first weekly look (W121.1) | Rejected only by a SUPPORTED branch |
| H-EDGE-1 | Attention: less-watched markets are mispriced more | props, team totals, alt lines | FADE / RIDE / POT OF GOLD | W123.1 | NOT SUPPORTED (11-20) on 18 judged non-headline families (none net > 0; pooled non-headline -0.0361 [-0.0442, -0.0276]); 18 prop families UNDERPOWERED | 53,262 settled rows, 4 sports | No wiring priority moves; props re-run at 30 held-out games per family; judgeable ~2027-01-28 (NBA props, 234 games at 23.5/wk, proxy sd) and ~2028-02 (NFL props: next season) (power_ledger.json, W124.1) |
| H-EDGE-2 | Timing: far-from-start prices are looser and drift predictably | T1 (12-48 h), 6 h | RIDE / FADE / MOMENTUM at entry | W123.2 | NOT SUPPORTED (11-20) — hypothesis closed (H-EDGE-2, parked for R&D) | 6 h b +0.017 [−0.024, +0.056], 24 h b −0.063 [−0.239, +0.035]; CLV +0.86¢ vs 1.08¢ fee; n 89-107 games; `12_EXPLORATORY/edge_location/h2_timing/RESULT.md` | Depth budget into T1; earlier entries |
| H-EDGE-3 | News latency: Kalshi reprices news over minutes | lineups, scratches, inactives, injuries | MOMENTUM (news arm) | W123.3 | NOT SUPPORTED for NBA injury / starter news, PARKED (R&D) 11-20: +0.3-0.5c still to come at +5 min vs 1.9c cost, median repriced < 1 min, n 45-189; confirmations (n 6) and NFL inactives (n 14) UNDERPOWERED | NHL goalies already fast: 0.2c, n 14 (W118.3); h3_news/RESULT.md | A news-reaction arm per supported event type; judgeable ~2026-12-01 (NFL inactives, 30 games) and ~2027-01-02 (NBA confirmations, 30 events) (power_ledger.json) |
| H-EDGE-4 | Execution: quoting both sides near fair beats predicting | any family x horizon | NEW: two-sided quoting | W123.4 | NOT SUPPORTED (11-20): hypothesis closed, parked for R&D; frozen 15-min rule UNDERPOWERED (0 fills), 35-min run 0 of 18 cells net > 0 | resting orders adversely selected (RIDE 69% vs 83%) | Demo quoting test proposed to the operator; frozen rule has 0 fills, so no judgeable date until it fills (power_ledger.json) |
| H-MEAS-1 | Measurement: the closing price is a calibrated estimate of settlement, so closing-line value can stand in for settled P&L at far lower variance | every family with >= 30 games | all arms (outcome licence) | W124.2 | RESULT (11-23): 1 of 50 family cells LICENSED (MLB F3, thin: slope 0.90 [0.21, 1.67]); 19 NOT LICENSED (10 miscalibrated, 9 noise-limited); 30 UNDERPOWERED; orders slope PASS but uninformative [-1.27, 2.11] | 85,229 settled markets; variance ratio 6 h median ~410x, 24 h ~440x, only usable where LICENSED; `12_EXPLORATORY/edge_location/meas_close/RESULT.md` | LICENSED families score on CLV (settlement confirms); NOT LICENSED stay on settlement |
| H-EDGE-5 | Favourite-longshot bias at the close: favourites settle above their price and longshots below by more than one round cost, per family x price bucket | NHL / NBA moneyline, NBA / NFL team total (2025-26 history; NHL team total has no history) | RIDE favourite / NO longshot; keeps the pot of gold off longshot YES | W125.3 | NOT SUPPORTED (11-24): hypothesis closed (EXP-H-EDGE-5, parked for R&D); 0 of 7 testable cells net > 0, BH q 0.10 rejects none; 1 LEAD (NBA ML [.90,.98), +0.0496 [+0.0237, +0.0755], n 63, below the 100-contract bar, not routed) | NHL ML [.50,.75) -0.0432 [-0.0658, -0.0205], n 1,296 (population previously read by W117.2); NBA ML [.50,.75) -0.0279, [.75,.90) -0.0279; NBA TT four buckets, all net <= 0; NFL TT UNDERPOWERED; `12_EXPLORATORY/edge_location/h5_flb/RESULT.md` | Reopen if the gap shows in 2026-27 rows (finer close than hourly) or Kalshi history lists NHL TT / more TT seasons; NBA ML [.90,.98) judged forward on 2026-27 |

### II.2 Program ROUTER — does the tree route better than a fixed rule?
| ID | Claim | Locus | Arm | Test | Status | Evidence | Consequence / reopen |
|---|---|---|---|---|---|---|---|
| H-ROUTER-1 | v1 per-leaf arms beat no bet held out | all sports | per leaf | W116.1 | NOT SUPPORTED overall (11-17): −0.0064 / row [−0.0138, +0.0009] | 161 held-out games | v1 stays the frozen forward test |
| H-ROUTER-1a | v1 per-leaf arms, NFL | NFL | per leaf | W116.1 | PARKED (R&D) 11-17: −0.0201 [−0.0369, −0.0054] | — | NFL per-leaf demo orders → NO BET (operator 11-17); reopen with new NFL features or a new season |
| H-ROUTER-2 | Router v2 (pooled + e-process) earns arms where per-leaf cannot | all sports | per leaf | W116.1 prereg; weekly look W121.1 | LOOKING (first look 11-17: 0 arms) | e-process false claims 2 / 300; planted +0.10 found 79 / 100 | Arms when a leaf passes the rule; next look 11-24 |
| H-ROUTER-3 | Ride every favourite | all | RIDE | W116.1 | PARKED (R&D) 11-17: −0.0256 / row | — | Reopen per family if H-EDGE-1 finds favourite underpricing |
| H-ROUTER-4 | Coarse leaves earn arms sooner | all | per family | W117.2 | NOT SUPPORTED (11-18): 6-40 weeks later | power calendar | Keep leaf-level; reopen if effects prove homogeneous |
| H-ROUTER-5 | History as a prior shortens the clock | NFL (nflverse), NHL (consensus) | per leaf | W117.2 | SUPPORTED, small (11-18): 1-7 weeks earlier | power calendar | Priors stay on; seek more free history |

### II.3 Program EXEC — does how we trade decide the sign?
| ID | Claim | Locus | Arm | Test | Status | Evidence | Consequence / reopen |
|---|---|---|---|---|---|---|---|
| H-EXEC-1 | Resting orders are adversely selected | all arms | placement | W116.2 / W119.3 | SUPPORTED (11-17): RIDE 69 vs 83%, FADE 33 vs 38%; 11-24 read (W125.1, 3,214 orders): sign mixed by cell, none at 20 games | 486 joined orders | Placement becomes a decision per arm |
| H-EXEC-2 | FADE crossing the spread is net positive | NBA / NHL | FADE (cross) | W117.1 | UNDERPOWERED (11-18): +0.166 [−0.016, +0.348], 20 games; 11-24 W125.1 fill model has no supported cross cell | real spread | Keep collecting; part of H-EDGE-4; judgeable on settlement: not within 2 years (3,128 games); ~2026-12-01 on CLV only if H-MEAS-1 licenses it (power_ledger.json) |
| EXP-W117.1 | Frozen placement policy beats today's rule | all arms | placement | 05_.../EXP-W117.1 | COLLECTING (table 0 cells) | — | Policy on as cells clear minimum n |
| EXP-W119.3 | FADE one tick inside the spread fills more without worse selection | FADE | placement | 05_.../EXP-W119.3 | COLLECTING (touch 22 / 342, inside 2 / 17) | — | Read at its judged n; judgeable ~2027-02-14 (100 resolved orders at 7/wk) (power_ledger.json) |
| H-EXEC-3 | Demo caps sized like a real book starve the experiment | demo path | — | W115.2 / GG-1935 | SUPPORTED (11-17): ~9,000 orders zeroed | — | Caps separated and raised (approved 11-17); 11-24: caps removed 13,237 orders since 11-12, stake pinned at the $50 base cap on 11-14..16; RIDE board 500/150 still borrowed (GG-2008, orders OFF) |
| H-EXEC-4 | Filled orders beat the close net of the fee actually charged | arm x family x hours-to-start (2-6 h named lead) | all arms | W124.3 | COLLECTING (11-23; prereg frozen, first look 12-01); W125.1 11-24 descriptive read: best cell 11 settled-filled games, none supported; team totals fill 5 of 538 at the touch | W123.2 CLV all orders RIDE +1.43c, FADE +0.75c; W123.4 fills 2-6 h +10.1c (68 fills, descriptive) | Forward-judged; SUPPORTED cells get placement and size priority |

### II.4 Program DEPTH — do matchup / personnel / context factors change the arm?
| ID | Claim | Locus | Arm | Test | Status | Evidence | Consequence / reopen |
|---|---|---|---|---|---|---|---|
| H-DEPTH-NBA-S1..S5 | Pace / net rating (S1), shot-zone matchup (S2), lineups (S3), home / road gap (S4), refs (S5) split NBA leaves | NBA game families | per leaf | W118.2 (EXP nba_depth_splits) | COLLECTING: 12 kept leaves, 0 BH; S3 / S5 UNDERPOWERED (snapshots from 11-10) | best S2 SPREAD T3 MOMENTUM +0.155, lower +0.048, 16 games | Behind +nba_depth (logged beside v1); S3 / S5 reopen with Muse's 2024-26 lineup / ref history (Monday); best leaf S2 judgeable ~2027-05-22 (238 games; ~2026-12-04 on CLV if licensed) (power_ledger.json) |
| H-DEPTH-NHL-1 | Goalie and special-teams splits change NHL arms | NHL game families | per leaf | W119.1 | COLLECTING: 8 positive of 42 held out, 0 BH | — | nhl_v2 candidate logged |
| H-DEPTH-NHL-2 | Goalie confirmation moves the price with a usable lag | NHL | MOMENTUM | W118.3 | PARKED (R&D) 11-18: 0.2c [0.07, 0.43], n 14 | — | Reopen if H-EDGE-3 finds latency elsewhere |
| EXP-NBAPROPS-001 | Player splits (minutes / usage, opponent zones, pace, rest) route NBA props | NBA props T1-T3 | per leaf | W121.2 | COLLECTING (11-20): 1 earned (points), 14 kept of 143 leaves | — | Points now priced (W122.1); nba_props candidate logged |
| H-DEPTH-PAM-3 | Trait stability: per-minute rates shrunk by stat reliability (and shrunk minutes) calibrate NBA props better than EXP-047's raw prior-game mean | NBA props (points / rebounds / assists / threes), pre-game | per leaf (input licence) | 12_EXPLORATORY/pam_stability/PREREG.md (16fcd204) | SUPPORTED (11-23, W124.5) | pooled D +0.00201 log-loss, 90% [+0.00184, +0.00219], 4 of 4 stats positive (BH q 0.10), gain 0.0103 at 4-10 prior games vs 0.0001 at 31+; gross calibration, no costs (12_EXPLORATORY/pam_stability/RESULT.md) | next: licence used by EXP-047-S (W129.2, SUPPORTED 11-25); not applied until the router scores it per leaf on net after costs |
| EXP-047-S | Shrunk per-minute rates x shrunk minutes, carried through C2's usage shift, price NBA props better than C2 as logged | NBA props (points / rebounds / assists / threes), pre-game | per leaf (input licence) | 12_EXPLORATORY/nba_props_shrunk/PREREG.md (8d6b97e6) | SUPPORTED (11-25, W129.2), judged once on 2025-26 (not fresh to the program, disclosed): pooled D +0.00172 log-loss, 90% [+0.00140, +0.00204], 4 of 4 stats positive (BH q 0.10); gain 0.0088 at 4-10 prior games vs 0.00001 at 31+; holds with and without an Out player; gross calibration, no costs | 12_EXPLORATORY/nba_props_shrunk/RESULT.md | logs forward as PM_PROPS_SHRUNK (default on, shadow, own ledger); not applied until the router scores it per leaf on net after costs |
| EXP-047-C1 | Redistributing an Out player's usage to the active rotation (proportional absorption, shared with NBA-10) prices NBA props better than EXP-047's plain trailing average | NBA props (points / rebounds / assists / threes), pre-game | per leaf (input licence) | 12_EXPLORATORY/nba_props_role (W125.4) | RETRO 11-23: INDETERMINATE (mixed): points improves (-0.027 log-loss [-0.031,-0.024]); rebounds, assists, threes worse; 1,899 games. Uniform rule hypothesis closed (EXP-047-C1, parked for R&D) | 12_EXPLORATORY/nba_props_role/RESULT.md | Points-only variant (C2) needs its own pre-reg; PM_PROPS_C1 default off |
| EXP-047-C2 | Per-stat absorption of an Out player's usage (points full; rebounds / assists / 3PA fitted fraction lambda, fit 2022-23 only) prices NBA props better than EXP-047's plain trailing average | NBA props (points / rebounds / assists / threes), pre-game | per leaf (input licence) | 12_EXPLORATORY/nba_props_role (W126.2) | RETRO 11-24 on unread 2023-24: SUPPORTED; all four stats improve (points -0.026, rebounds -0.001 thin, assists -0.004, threes -0.003); lambda 0.26 / 0.31 / 0.27; 899 games. Forward net per arm pending | 12_EXPLORATORY/nba_props_role/RESULT_C2.md | PM_PROPS_C2 default off; activation is a dated proposal |
| H-DEPTH-NFL-1 | NFL tested splits (13 cells, W112-W113) change arms | NFL | per leaf | W120.1 | COLLECTING on box rows (stumps logged) | — | Recount after 11-22 / 23 |
| EXP-NFLSPLITS-001 | QB / rest / officials / forecast weather / matchup splits route NFL team totals and alternate spread / total ladders | NFL TT, AS, AT | per leaf | W126.5 (12_EXPLORATORY/nfl_splits) | HYPOTHESIS CLOSED (parked for R&D) 11-24 on proxy prices: 94 of 156 rows judged on 2025, 0 fit-routed, 0 earned, 0 intervals above zero | RESULT.md | Reopen on real Kalshi ladder quotes (2026 forward shadow rows; `PM_NFL_SPLITS` default off, tag only) |
| EXP-NFLPLAYLEVEL-001 | Play-level personnel / shell / motion / man crosses route NFL team totals and alternate spread / total ladders | NFL TT, AS, AT | per leaf | W128.3 (12_EXPLORATORY/nfl_playlevel) | HYPOTHESIS CLOSED (parked for R&D) 11-25 on proxy prices: 118 rows, 74 judged on 2025, 0 fit-routed, 0 earned, 0 intervals above zero | RESULT.md | Reopen on real Kalshi ladder quotes and 2026 participation data (2026 coverage carried; `PM_NFL_PLAYLEVEL` default off, tag only) |

### II.5 Program ARMS — pot of gold and momentum
| ID | Claim | Locus | Arm | Test | Status | Evidence | Consequence / reopen |
|---|---|---|---|---|---|---|---|
| POT-OF-GOLD (11-05 prereg) | Lottery tickets are overpriced (or underpriced) after cost in specific buckets | 17 cells: 15 MLB + 2 NFL | POT OF GOLD | 12_EXPLORATORY/pot_of_gold | IN_SAMPLE (11-20): 0 earned / 17 | forward 56 contracts | Next look 2026-12-10 |
| POT-OF-GOLD-W125 | Pot-of-gold branches earn per leaf (family x tier x FLB bucket x side) after partial pooling | NBA / NHL / NFL game families + props, 2026-27 shadow rows | POT OF GOLD | W125.3 | IN_SAMPLE (11-24): 0 of 18 judged leaves EARNED; 273 of 288 below judged n; 15 judged leaves routed away (hypothesis closed, EXP-POT-W125, parked for R&D, those leaves only) | 10,430 settled forward rows, 80 pools; `12_EXPLORATORY/pot_of_gold/RESULT_W125.md`; combo / parlay markets exist on Kalshi (KXMVE* collections) and are REGISTERED, NOT BUILT | Re-run `score_w125.py` after each settlement refresh; the 17 pre-registered cells still next look 2026-12-10 |
| H-ARMS-MOM-NHL | The NHL open-to-close move carries information past the close | NHL ML / PL / total | MOMENTUM | W117.2 | PARKED (R&D) 11-18: every interval contains 0 | 1,394 games | Reopen with intraday paths (not open / close only) |
| H-ARMS-BOOKS-NHL | Riding the books' side when Kalshi differs at the close pays | NHL ML | RIDE consensus | W117.2 | PARKED (R&D) 11-18: −0.055 after cost | n 1,312 | Reopen at earlier horizons (H-EDGE-2) and other families (H-EDGE-1) |
| MLB-POSTSEASON-FADE | Always-fade in the MLB postseason | MLB | FADE | W118.1 | PARKED (R&D) 11-18: −0.078 [−0.124, −0.027] | 22 games | 2027 forward test (PREREG_2027) |

### II.6 Program ENGINE — do the engines price well enough to route on?
| ID | Claim | Locus | Status | Notes |
|---|---|---|---|---|
| EXP-036 / 037 / 038 | Pre-game shadow arms per sport (NHL / MLB + NFL / NBA) | game families T1-T3 | COLLECTING; routing addenda 11-12 | the forward corpus every test reads |
| EXP-039 / 040 | NBA player points (frozen artifact; minutes + injury challenger) | NBA points | COLLECTING | points priced by the engine from 11-20 |
| EXP-041 | NFL market-anchored pricing | NFL | COLLECTING | conviction pricing (operator 10-21) |
| EXP-042 / 043 | Ride cells; ladder ride forward | ride arm | COLLECTING (EXP-042 cell 10 retired 11-04) | — |
| EXP-044 / 044b / 044c | NBA engine v1 / v2 / v3 | NBA | COLLECTING; blend test 12-29 .. 02-15 | — |
| EXP-045 | NFL engine forward (frozen, sha256) | NFL board | COLLECTING; reads 01-12 | — |
| EXP-047 | NBA engine props shadow | NBA props | COLLECTING | — |
| MLB-2027 | 2026 look-back routing holds in 2027 | MLB 42 cells | PRE-REGISTERED (PREREG_2027) | opening-day dry run passes (W122.4) |

### II.7 Parked elsewhere (W104-W122, short form; the backfill expands each)
- **The 39-row edge map as standalone bets** — PARKED (R&D): no single pattern beats cost alone; each is a routing input (W110-W111).
- **NFL game total T1 + T2, fade arm** — PARKED → routed to ride (EXP-037 NFL).
- **MLB pre-game model vs market (EXP-029)** — PARKED → routed to ride.
- **T4 latency thesis (T-569)** — NOT SUPPORTED with the current feature set; in-play arms wait for a measured speed advantage (ADR-0068).
- **Weather as a factor (W108-W109)** — PARKED (R&D): Kalshi already beats a free forecast; no build.
- **The old NBA book (GG-034 / GG-037)** — PARKED (historical): anti-predictive at the NBA Finals; frozen.

### II.8 Historical backfill (B-110, W129.5)
| ID | Claim | Population | Rule | Verdict / look date | File | Status |
|---|---|---|---|---|---|---|
| EXP-025 / HYP-010 NB | NB1 negative-binomial refit of the HYP-010 Phase-2 count model | MLB (HYP-010 population) | verdict states as EXP-022: INCONCLUSIVE-EXTEND ARCHIVE is not FALSIFIED | INCONCLUSIVE at n (predecessor EXP-022 / T-487); result not re-read here | 05_RESEARCH_EXPERIMENTS/EXP025_HYP010_NB_PREREGISTRATION_2026-08-28.md | PARKED (R&D) |
| EXP-028 | Pre-game MLB hit-prop model beats the base rate on the frozen 2024-26 matrix | MLB hit props | game-clustered paired dBrier, 5,000 bootstraps, seed 17 | RESULTS 2026-09-30 (`EXP028_..._RESULTS`); model vs market is the ROUTER question | 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/EXP028_pregame_mlb_hits_PREREGISTRATION_2026-09-30.md | PARKED (R&D) |
| EXP-030 | Deeper structure than the three-scalar binomial improves T4M-PROJ calibration on a sealed holdout | MLB T4M-PROJ, sealed holdout | paired Brier gain, harness verdict unmodified | NO DETECTABLE DIFFERENCE (harness INCONCLUSIVE), 2026-09-30 | 05_RESEARCH_EXPERIMENTS/EXP030_T4_STRUCTURE_PREREGISTRATION_2026-09-30.md | PARKED (R&D) |
| EXP-031 | Families rank on market efficiency; some are calibration-biased at first-seen | 14 families (10 MLB, 4 NFL) | frozen n / days rule, label per family | Zero CANDIDATES; 4 NFL families INCONCLUSIVE (2026-09-30) | 05_RESEARCH_EXPERIMENTS/EXP031_MARKET_EFFICIENCY_PREREGISTRATION_2026-09-30.md | PARKED (R&D) |
| EXP-032 | The execution toll is structural, not an artefact of when we looked | pre-game buckets per family | coverage rule per family bucket | RESULTS 2026-10-01 (not re-read here); feeds H-EXEC-* | 05_RESEARCH_EXPERIMENTS/EXP032_EXECUTION_COST_SURFACE_PREREGISTRATION_2026-10-01.md | SUPERSEDED by H-EXEC-1..4 |
| EXP-033 | Kalshi multi-leg books are incoherent enough to Dutch-book after cost | sports books, all legs | margin after asks + ADR-0016 fee | Nothing survived (2026-10-01); 44.1 cost surface had not landed | 05_RESEARCH_EXPERIMENTS/EXP033_MULTILEG_COHERENCE_PREREGISTRATION_2026-10-01.md | PARKED (R&D) |
| EXP-038 (+W111.1 addendum) | NBA pre-game shadow cells; a losing look closes the FADE arm, not the cell | NBA game families, 12 cells | shadow log; addendum routes per leaf | COLLECTING; addendum 2026-11-12 | 05_RESEARCH_EXPERIMENTS/EXP038_NBA_PREGAME_SHADOW_PREREGISTRATION_2026-10-06.md (+ _ADDENDUM_W111_1_ROUTING_2026-11-12.md) | COLLECTING |
| EXP-040 | Projected-minutes + injury challenger beats the points >= 15 model | NBA player points >= 15 | paired Brier vs frozen EXP-039 | COLLECTING (ACCEPTED) | 05_RESEARCH_EXPERIMENTS/EXP040_NBA_PLAYER_POINTS_MINUTES_PREREGISTRATION_2026-10-12.md | COLLECTING |
| EXP-043 | A ladder (>= 4 strikes, LOO normal fit) prices a strike better than the quote by more than cost | all sports, ladder families | take the side when gap > spread + exact fee | COLLECTING; judged n not reachable before the season's later weeks (file) | 05_RESEARCH_EXPERIMENTS/EXP043_LADDER_RIDE_FORWARD_PREREGISTRATION_2026-10-28.md | COLLECTING |
| EXP-044b | NBA engine v2 beats the market and v1 | NBA board | PASS at n >= 1,200 games; w >= 0.01 | Descriptive checkpoint 2027-01-31; verdict look 2027-04-20 | 05_RESEARCH_EXPERIMENTS/EXP044B_NBA_ENGINE_V2_CHALLENGER_PREREGISTRATION_2026-10-28.md | COLLECTING |
| EXP-044c | NBA engine v3 (availability + rotation lineups) beats v2 | NBA board | PASS at n >= 1,200 games per claimed family | Descriptive checkpoint 2027-01-31; verdict look 2027-04-20 | 05_RESEARCH_EXPERIMENTS/EXP044C_NBA_ENGINE_V3_CHALLENGER_PREREGISTRATION_2026-10-30.md | COLLECTING |
| HYP-011 | Moneyline-first LR track beats the base (Phase 2 reroute) | moneyline cells | clean_n < n* => INCONCLUSIVE, not FALSIFIED | PRE-REGISTERED, never run (no model fit) | 05_RESEARCH_EXPERIMENTS/HYP011_moneyline_lr_preregistration_2026-09-03.md | PARKED (R&D) |
| T-565 | T4M-PROJ model-vs-market calibration reproduces | MLB T4M-PROJ | ADR-0046 comparability checklist | RESULTS file `T565_RESULTS_...` (not re-read here) | 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T565_PREREGISTRATION_calibration_model_vs_market.md | PARKED (R&D) |
| T-567 | Market efficiency gradient ranks families | all families | pre-registered ranking | RESULTS 2026-09-23 (not re-read here) | 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T567_EFFICIENCY_GRADIENT_PREREGISTRATION_2026-09-23.md | SUPERSEDED by EXP-031 |
| T-572 | Closing-line value is a usable instrument | all families | CLV harness thresholds | RESULTS file `T572_clv_harness_RESULTS.md`; CLV now used by H-MEAS-1 | 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T572_clv_harness_PREREGISTRATION.md | SUPERSEDED by H-MEAS-1 |
| T-577 | T4M-PROJ epoch-12 cohort: salvage or declare | 905 clean rows (35 FILLED, 139 CANCELED, 731 NOT_RETRIEVABLE) | per-row verdict classes | RESULTS file `T577_RESULTS_cohort_salvage.md` | 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T577_PREREGISTRATION_cohort_salvage.md | PARKED (R&D) |
| W83.2 lineup window | NBA lineup news moves the price inside a window | NBA game prices | exhaustive verdict order; else INCONCLUSIVE at n | Superseded in effect by H-EDGE-3 (NOT SUPPORTED 11-20) | 12_EXPLORATORY/20261020_nba_lineup_cross/PREREG_lineup_window.md | SUPERSEDED by H-EDGE-3 |
| NFL-QB-SHRUNK | A shrunk-QB challenger beats the NFL pre-game model | NFL games | ~984 games needed (~3.6 seasons); looks before are keep accruing | COLLECTING (ACCEPTED 2026-10-10) | 12_EXPLORATORY/NFL_QB_SHRUNK_CHALLENGER_PREREGISTRATION_2026-10-09.md | UNDERPOWERED |
| THIN-MARKET | NFL passing-yards model beats the book mid after fill | KXNFLPASSYDS pre-game | 400 strikes over >= 60 games, paired Brier, one-sided 95% | FROZEN 2026-10-20; modal outcome no fill-adjusted edge (P 0.7) | 12_EXPLORATORY/THIN_MARKET_PREREGISTRATION_2026-10-20.md | COLLECTING |
| BLEND-TEST | Blend weights between engine and market (B-051) | engines EXP-041/044/045 | descriptive, no verdict edits | FROZEN 2026-11-06; NBA window 12-29 .. 02-15 | 12_EXPLORATORY/blend_test/BLEND_TEST_PREREGISTRATION_20261106.md | COLLECTING |
| H-ROUTER-2 prereg | Router v2 (pooled + sequential leaf map) | all sports | e-process rule | LOOKING (see H-ROUTER-2) | 12_EXPLORATORY/evidence_design/ROUTER_V2_PREREGISTRATION_2026-11-17.md | LOOKING |
| EXP-MLBSIM-001 | PA-level joint simulation, held-out 2026 report | MLB | a report, not a verdict (ADR-0077) | held-out 2026 report (W126.3) | 12_EXPLORATORY/mlb_engine/PREREG_W126_3.md | COLLECTING |
| MLB-2027 | 2026 look-back routing holds in 2027 | MLB 42 cells | frozen before the first 2027 row | PRE-REGISTERED (see II.6) | 12_EXPLORATORY/mlb_lookback/PREREG_2027.md | PRE-REGISTERED |
| W107.3 threshold | NBA v3 availability threshold, written before any outcome | NBA | descriptive; EXP-044c looks untouched | DESCRIPTIVE below judged n | 12_EXPLORATORY/nba_engine_v3/PREREG_W107_3.md | COLLECTING |
| NHL-TOTALS | NHL totals challenger beats the incumbent (B-029) | NHL totals | pre-registered (W101.1 Part C) | result not re-read here | 12_EXPLORATORY/nhl_engine/NHL_TOTALS_CHALLENGER_PREREGISTRATION_2026-11-05.md | COLLECTING |
| EXP-W119.1-NHL-GOALIE-ST | Goalie and special-teams splits (4 layer-3 splits) change NHL arms | NHL game families | routing test, not a gate | see H-DEPTH-NHL-1: 8 positive of 42 held out, 0 BH | 12_EXPLORATORY/nhl_factors_w112/PREREG_W119_1_GOALIE_ST.md | COLLECTING |
| LEAF-MAP-FWD | The 113 routed leaves' arms hold on forward shadow rows | 113 leaves + 3 family leads | routing result, not a verdict on a market | forward test (W111.3 / B-079) | 12_EXPLORATORY/retro_route/LEAF_MAP_FORWARD_PREREGISTRATION_2026-11-12.md | COLLECTING |
| RIDE-BOARD | Ride / fade board: held-out trade P&L per cell (B-053) | MLB totals etc. | Part 1 frozen; Part 2 cells appended | 0 cells HELD_OUT; KXMLBTOTAL FADE only lead; MLB opens ~2027-03-25 | 12_EXPLORATORY/ride_board/RIDE_BOARD_PREREGISTRATION_2026-11-06.md | UNDERPOWERED |
| EXP-035 (Part 1 + board survey) | The sports board survey finds candidate families on candle history | sports boards | frozen e28166a | Part 1 FAILED at 0972862 (GG-333); standing verdict unrescued | 05_RESEARCH_EXPERIMENTS/EXP035_BOARD_SURVEY_SPORTS_PREREGISTRATION_2026-10-02.md | PARKED (R&D) |
| EXP-035 Gate 2 | KXMLBTOTAL candle history agrees with the archive | MLB totals | 7 agreement checks | PASSED 7/7 (2026-10-02) | 05_RESEARCH_EXPERIMENTS/EXP035_GATE2_PREREGISTRATION_2026-10-02.md | SUPPORTED |
| HYP-012 | NFL moneyline LR track beats the base | NFL moneyline | as HYP-011 | PRE-REGISTERED 2026-09-09; result not re-read here | 05_RESEARCH_EXPERIMENTS/HYP012_nfl_moneyline_lr_preregistration_2026-09-09.md | PARKED (R&D) |

---

## Part III — Keeping it current
1. Every block that writes a pre-registration or a result adds or updates its registry line in the same PR (ID, status, date, evidence).
2. The strategic window reviews Part II at every wave close: statuses moved, reopen triggers fired, new branches stated.
3. The weekly evidence look's summary feeds the ROUTER and DEPTH lines automatically once wired (B-110 asks for a generated table).
4. Part I changes only by a dated edit, logged in DECISION_LOG; parameter changes are rows in §I.6.
5. This file is in the doctrine stack: older than 14 days is RED in the session scan (Hard Rule 16).
