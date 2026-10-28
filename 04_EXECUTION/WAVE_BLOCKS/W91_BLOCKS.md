# Wave 91 — paste blocks (ride the market: prove it or drop it, and two new sources)

Copy each block as one fenced paste. The wave's table, results and status live in `04_EXECUTION/ACTIVE_QUEUE.md` § "NOW — Wave 91".
Written 2026-10-27 17:40 PT at the Wave 90 close. All three blocks run in parallel. No Muse paste this wave: Muse's live session (ten
tickets, R-065 → R-026) is running, and its scheduled runs then take the order in TO_MUSE.md (R-068 → R-071 next).

### 91.1 — The ride cells: pre-register first, then test them where they were not found
**PROOF** · terminal 1

```
COMMON RULES - WAVE 91 (RIDE THE MARKET: PROVE IT OR DROP IT, AND TWO NEW SOURCES) (read first; they bind this block)
- SIZE: MEDIUM. Target 60 minutes, hard ceiling 90 (operator 2026-10-07). Two parts. If your first estimate for the
  whole block is over 90 minutes, say so in one line, do Part A only, and name Part B as the next undone part. Do not
  re-verify things this prompt states as verified unless your work depends on them.
  After EACH part: push, and update this block's row in 04_EXECUTION/ACTIVE_QUEUE.md (NOW table: Status + one line)
  with a docs-only push. Stop at a pushed boundary (context ~60%, a blocker, or 90 minutes) and write the handoff.
  Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs, and ONLY on a CI result you
  have read as green (W80.1 merged #291 red and broke main). Read the Deploy job summary after each merge and record the
  t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-27 17:30 PT - incl. Wave 90 results (90.1: PR #349 and #352 merged; the hold-out
  scan found 0 candidates because only 1 of 1,850 cells was testable - UNDERPOWERED, not a null, GG-1292; ride.py not built. 90.2: the
  router built and wired to nothing; replay of 164,354 MLB + NFL situations = 97.66% NO-BET, 2.34% RIDE (in-sample cells only), 0 FADE,
  0 MOMENTUM. 90.3: pre-game moves of 3c+ are a random walk at 1-3 h in every sport; both following and fading lose to cost; 0 contexts
  routable), THE ROUTING DOCTRINE ACCEPTED (operator 2026-10-27: "Accept - proceed in full"; 02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md:
  FADE only on measured skill, RIDE only on a net-positive table cell, same side to RIDE, opposite sides to NO-BET, T3 a FADE-only overlay,
  news timing excluded; no wiring authorized by it), the box GREEN again (2026-10-28 00:18Z: 77 live, healthcheck HEALTHY, the MLB arm
  writing rows), THE RIDE-THE-MARKET DIRECTION (operator 22:12 PT: "we need
  substantively more architecture around the \"ride the market\" trees than we have before we come to any end all be all
  conclusions"; 22:08 PT: "Sometimes it's best just to roll with the market sentiment - we don't always have to be it - that's the
  meaning of having filtering mechs appropriately identifying the correct decision trees and routing mechanisms for execution"),
  Wave 89 results (kill switch ENFORCING; 89.2 longshot bias: 11 in-sample cells; 89.3/89.4/89.5 no edge), 89.7 left PARTIAL (PR #349
  open, CI failed; its remainder is 90.1 Part A, operator 2026-10-27 16:30 PT), Wave 88 results (5 of 6 frozen models scored against the
  market: NHL and NBA worse than it, MLB level with it; every skill weight effectively 0, so the gate keeps nothing; DRAFT ADR-0076
  awaiting the operator; kill switch still LOG-ONLY), Wave 87 results (core reconciled on 9 paths, 3 re-pointed;
  exposure gate on every order path in LOG-ONLY; 2 of 6 models scored vs market, both no better than it; skill weights all 0),
  Muse back on its three daily runs with a reordered backlog (2026-10-26), Wave 86 results (quant core merged; 1 of 6 models scored
  against the market; the market uses about one width per sport too; adverse selection dominates E3), THE QUANT ROLLOUT (operator 2026-10-22 16:58 PT: "I want one
  of the next waves to be purely quant refinement - I want to get our figures right (structurally ...)" ... "we need to have the same
  level of optionality - WITH QUALITY"; accepted 17:06 PT: Wave 86 = quant Wave A; a technique enters the library only with a test,
  a stated condition for when it applies, and one measured result on our data), EXP-041 frozen and NOT wired, position_gate.py
  built and NOT wired, Muse paused for the week (daily watchdog sweep scheduled), THE OPERATOR'S ACCEPTANCE OF MARKET-ANCHORED PRICING, A REAL
  GATE AND A POOLED TEST (blockquote in ACTIVE_QUEUE.md "Needs your decision", 2026-10-21 20:28 PT: "Good - I accept them"),
  the THREE CALLS of 19:15 PT (PAM drafts accepted; G6 re-defined by a superseding ADR; the kill switch counts open and unresolved
  stake, GG-441), the observation rule (WATCH ITEM), the shared folder as a reading copy, one Visual Dashboard served by the box at /visual
  (2026-10-21 17:20 PT), Muse three daily runs and a 30-ticket backlog (2026-10-21 16:55 / 18:35 PT), the ADR-0072 addenda of 2026-10-20 (verdict per (book,
  sport), criterion (c) judged forward, cash-starved days excluded) and 2026-10-21 (NFL: one more look at markout judged n),
  Muse charter v3 (Muse scouts via source cards, the bot captures), Muse off headline news (2026-10-20 21:26 PT), green = the cell
  WINS (2026-10-19 22:06 PT), the operator's acceptance of the KXNFLPASSYDS
  thin-market pre-registration (blockquote in ACTIVE_QUEUE.md "Needs your decision", 2026-10-19), L3 = the split-level
  layer (R-008), operator examples are illustrations, never work items (W17, W25), the granularity index, "retail flow first", three blocks per wave,
  the box bridge, Muse charter v2 (02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/PARTNERSHIP_CHARTER.md), ADR-0073 (one deep engine
  per sport), ADR-0074 (process integrity, Hard Rules 13-15), ADR-0075 ACCEPTED (the betting architecture: aggregation >
  interpretation > application; eight components; measure D5), ADR-0070/0071/0072, the repository PUBLIC (Actions minutes
  free), "not a cent on GitHub", the expansion directive, Hard Rule 12. Standing authorizations: shadow-evaluation cron
  jobs, NEW lines only (2026-10-02); new pre-registered shadow arms (2026-10-08); idle-window service restarts
  (2026-10-08); Live Terminal deploy + pmbot-web-dashboard restart. An authorization exists ONLY as a blockquote line in
  ACTIVE_QUEUE.md "Needs your decision". A table row or a DECISION_LOG line written by a terminal is NOT an authorization.
- Start: CLAUDE.md session-start protocol, brief. Isolated worktree: scripts/new_session_worktree.sh <slug>. Claim with
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD; reserve 3 GG numbers, not 10. If a GG number
  collides, re-claim; never reuse. Commands added since your local folder last synced: read them with
  `git show origin/main:<path>` (window error W20).
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- CI runs on every PR. Never add a paid service. CI fails on any running component missing from
  02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml - register first (scripts/runtime_registry.py add), then install.
- Three blocks run in parallel. File ownership: 91.1 = a new pre-registration file under 05_RESEARCH_EXPERIMENTS/ (the next free
  EXP number, claimed), a new 12_EXPLORATORY/ride_cells/, additions to 12_EXPLORATORY/market_history/ and exp_output/KALSHI_HISTORY/, the
  GG-1253 and GG-1292 / GG-1293 entries; 91.2 = a new src/prediction_market_bot/decision_trees/ride.py + a new
  src/prediction_market_bot/decision_trees/ride_cells.toml + tests, router.py's ride stub ONLY (swap the stub for ride.py; nothing else in
  router.py), a new 12_EXPLORATORY/ride_ladder/, the decision_trees [[component]] entries in ARCHITECTURE_COMPONENTS.toml; 91.3 = PR #347's
  branch (w89-6/locks), a new 12_EXPLORATORY/ride_venue/, exp_output/POLYMARKET_HISTORY/. Data: the price archive
  (exp_output/PRICE_ARCHIVE/, MLB + NFL, ~20-min snapshots from 2026-08-01; 90.2 and 90.3 read it locally - 90.1 believed it was on the box
  only: find it before concluding that) and Kalshi's public history via 12_EXPLORATORY/market_history/ (89.7 tooling, on main). THE RIDE
  TABLE CONTRACT (so no block waits on another): ride.py reads ride_cells.toml; each cell carries an evidence status - IN_SAMPLE,
  HELD_OUT, FORWARD_PASSED, FAILED, UNTESTED - and ride.py returns RIDE only for HELD_OUT or FORWARD_PASSED. 91.2 seeds the table with
  89.2's 11 cells as IN_SAMPLE (so they route NONE today). 91.1 and 91.2 Part B write their results to their own folders; the window
  moves statuses into the table at the wave close. Everyone may ADD to src/prediction_market_bot/quant/ (new functions with tests, no
  edits to existing ones); fetch + rebase before every push.
  TO_MUSE.md is append-only: fetch + rebase right before pushing. The gap agent owns GG_BURNDOWN.md and GG_AGENT_STATE.md. Box access: ssh, or the box bridge
  (04_EXECUTION/BOX_TASKS/requests/*.toml naming an allowlisted task; results in 04_EXECUTION/BOX_TASKS/results/). The box pulls
  main on its own timer: before trusting a bridge result after a merge, read deploy_truth_read's box HEAD.
  SURFACE BUDGET: read the box's budget_read before installing anything; Hard Rule 14: nothing new goes live unless it reads GREEN. Register every new component before it runs.
- ALL CODE lands through a PR with CI green - src/, scripts/, tests/ AND 12_EXPLORATORY/*.py. Only results (.md/.json/.csv) may be
  pushed docs-only.
- PERMISSIONS (revised 2026-10-13): do NOT edit .claude/settings*.json. If a command is refused: record the exact command and
  refusal, skip only that step, finish the rest, hand back. Never work around it. DONE means merged AND, for anything that
  runs, read back where it runs - never "merged" alone.
- DEMO / PAPER / SHADOW ACTIONS ARE PLUMBING (operator rule). Never write "operator decision needed" for a demo-only action;
  only real capital is his.
- PR mergeable_state dirty = almost always SESSION_CLAIMS.md / .last_session_checkpoint: merge origin/main into the
  branch locally, re-run the suite, push, merge.
- Shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md): fetch + rebase right before each push; edit
  only your own entries/rows. DECISION_LOG is append-only.
- No order, position, fill, stake size or kelly_fraction change. No live-ledger row rewritten. No edit of an existing cron
  line. No change to a live model, runner, registry cell or pre-registration except where your block's PERMISSIONS name
  it. Read-only GETs against the Kalshi DEMO API, and public unauthenticated Kalshi market-data GETs, are allowed.
- Python on the box is 3.9 and rejects Kalshi's 5-digit fractional ISO timestamps: parse with the tolerant parse_ts (W80.2).
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- A choice between two fixes for a demo/paper/shadow problem is NOT an operator decision: take the root-cause fix. Only a
  change to a pre-registration, a frozen artifact, a frozen book, real capital or an open strategic question goes to the
  operator - as one line, with your recommendation, after the rest of the block is done.
- PURPOSE (Hard Rule 12): your claim string names the distance-to-optimum measure this block is FOR (the PURPOSE line
  under the title). Your handoff fills vision_pillar, gap_measure and gap_delta (measured before -> after, with source).
  If what you find means the block cannot move its measure, say so and stop rather than doing adjacent work.
- THE QUANT BAR (from Wave 86 on): every technique you add carries (1) a test on known answers (a simulated case where the truth is
  known), (2) a one-line statement of when it applies and when it does not, (3) one measured result on OUR data with n and an
  interval. Without all three it is not added. Read-only on every live ledger, model, runner and pre-registration.
- ADR-0075: every factor you touch reports the stage it reached - aggregated / interpreted / applied (a tested path from
  the fact to a price, compared with the market). Quote the operator's words, never compress them (window error W16).
- GRANULARITY INDEX (operator 2026-10-16, 02_ARCHITECTURE_DESIGN/GRANULARITY_INDEX.md): every factor you build reports its
  five parts - the split, the rank against history, the matchup cross, the market map, the application. The operator's
  examples are illustrations, not build lists (window error W17).
- ADR-0074: handoffs carry pattern_sweep: ("n/a (no defect fixed)" when nothing was fixed) and surface_delta:.
- Every premise below is a claim to verify - CHECK IT AGAINST LOGS/DATA BEFORE BUILDING ON IT.
- Free data only. A factor only a paid source has is a registered GAP (GG), never bought.
- Report back: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result | MEASURE MOVED: <measure>
  <before> -> <after> (source) or none | stage reached per factor | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W91_<n>.md (docs-only push).

WAVE 91.1 - THE RIDE CELLS: PRE-REGISTER FIRST, THEN TEST THEM WHERE THEY WERE NOT FOUND. Repo: eignacio1/prediction-market-bot.
PURPOSE: PROOF. Measures: ride cells pre-registered 0 -> 11 (a forward look date joins P3); 89.2's cells tested out of sample 0 -> n of 11.
The operator, 2026-10-26 22:12 PT: "we need substantively more architecture around the \"ride the market\" trees than we have before we
come to any end all be all conclusions." 90.2's router sent 2.34% of 164,354 situations to RIDE, but only on cells chosen from that same
archive. Until a cell holds where it was not found, it routes nothing. 90.1's hold-out was a time split INSIDE the archive and too thin
(1 of 1,850 cells testable, GG-1292). This block tests the 11 cells as they were defined, on data that played no part in finding them.
Premises to check: 89.2's 11 cells and their definitions are in 12_EXPLORATORY/longshot_bias/results*.md (family, tier, price band, book
view, side, net with interval). Kalshi's public API serves settled markets and hourly candles (89.7: 12_EXPLORATORY/market_history/).
Kalshi's listed time is the true start + 3.0 h (89.7). It is unknown how far back each family was listed: find it, never assume it.
PERMISSIONS: per the common rules' ownership; public unauthenticated Kalshi market-data GETs (paced, resumable) and free schedule sources
(MLB StatsAPI, ESPN). A NEW pre-registration (standing authorization: new pre-registered shadow arms, 2026-10-08); scoring it from the
price archive needs no runner, so nothing goes live. NOT: any order, gate, model, runner, ledger, registry cell or existing
pre-registration; the router or ride.py (91.2's).

PART A - Pre-register before reading any new row (~30 min)
  One file, the next free EXP number, frozen (hash recorded) and pushed BEFORE Part B fetches anything. It fixes:
  1. The 11 cells exactly as 89.2 defined them: entry is a taker at the quote (YES at the ask, NO at 1 - bid), k007 fee, depth at the
     quote recorded; no re-selection, no new buckets, side fixed.
  2. BACKWARD test: the same cells on every date before 2026-08-01 that Kalshi lists (MLB 2026 before August, 2025 where listed; NFL
     2025 season), from hourly candles (first two-sided candle per ticker per tier, as 90.1 did). State the method difference between
     hourly candles and the archive's ~20-min snapshots, and a check: on the overlap (Aug-Oct 2026, where both exist) the candle method
     must reproduce 89.2's per-cell numbers within their intervals before any earlier date is read. If it does not, the backward test is
     void and says so.
  3. FORWARD test: the price archive's rows after the freeze time, scored at a look date; each cell's judged n from 89.2's variance at
     the effect 89.2 measured (state power and alpha). MLB cells accrue nothing between the World Series and April: say when each look
     falls.
  4. The pass rule (net lower bound > 0, game-clustered 95%), Benjamini-Hochberg at q = 0.10 across the 11, and the pre-registered modal
     outcome per test.
PART B - Run the backward test exactly as written (~50 min)
  Fetch every strike of every event in those families for the backward window (no sampling budget; one sport's phases at a time - 89.7:
  "the original chained prep run overwrote a good NFL schedule with an empty one"), true start times from MLB StatsAPI / ESPN (close GG-1253:
  MLB ticker HHMM as ET, checked against the schedule). Overlap check first. Then per cell: n, games, net per contract with interval,
  PASS / FAIL / UNTESTED (family not listed then: NONE, and the cell rests on the forward test alone), BH. Results to
  12_EXPLORATORY/ride_cells/results_W91_1.md + backward_W91.json (cell id, status HELD_OUT / FAILED / UNTESTED, net, interval, n, games)
  - the window moves those statuses into ride_cells.toml. Register gaps for what you could not test.
Results: the frozen pre-registration, results_W91_1.md + backward_W91.json, a handoff, and one operator line: which cells held out of
sample (or none), and the forward look dates.

END OF BLOCK 91.1. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 91.2 — The ride tree as code, and a second kind of ride: the market's own ladder
**DEPTH (+ PROOF)** · terminal 2

```
COMMON RULES - WAVE 91 (RIDE THE MARKET: PROVE IT OR DROP IT, AND TWO NEW SOURCES) (read first; they bind this block)
- SIZE: MEDIUM. Target 60 minutes, hard ceiling 90 (operator 2026-10-07). Two parts. If your first estimate for the
  whole block is over 90 minutes, say so in one line, do Part A only, and name Part B as the next undone part. Do not
  re-verify things this prompt states as verified unless your work depends on them.
  After EACH part: push, and update this block's row in 04_EXECUTION/ACTIVE_QUEUE.md (NOW table: Status + one line)
  with a docs-only push. Stop at a pushed boundary (context ~60%, a blocker, or 90 minutes) and write the handoff.
  Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs, and ONLY on a CI result you
  have read as green (W80.1 merged #291 red and broke main). Read the Deploy job summary after each merge and record the
  t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-27 17:30 PT - incl. Wave 90 results (90.1: PR #349 and #352 merged; the hold-out
  scan found 0 candidates because only 1 of 1,850 cells was testable - UNDERPOWERED, not a null, GG-1292; ride.py not built. 90.2: the
  router built and wired to nothing; replay of 164,354 MLB + NFL situations = 97.66% NO-BET, 2.34% RIDE (in-sample cells only), 0 FADE,
  0 MOMENTUM. 90.3: pre-game moves of 3c+ are a random walk at 1-3 h in every sport; both following and fading lose to cost; 0 contexts
  routable), THE ROUTING DOCTRINE ACCEPTED (operator 2026-10-27: "Accept - proceed in full"; 02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md:
  FADE only on measured skill, RIDE only on a net-positive table cell, same side to RIDE, opposite sides to NO-BET, T3 a FADE-only overlay,
  news timing excluded; no wiring authorized by it), the box GREEN again (2026-10-28 00:18Z: 77 live, healthcheck HEALTHY, the MLB arm
  writing rows), THE RIDE-THE-MARKET DIRECTION (operator 22:12 PT: "we need
  substantively more architecture around the \"ride the market\" trees than we have before we come to any end all be all
  conclusions"; 22:08 PT: "Sometimes it's best just to roll with the market sentiment - we don't always have to be it - that's the
  meaning of having filtering mechs appropriately identifying the correct decision trees and routing mechanisms for execution"),
  Wave 89 results (kill switch ENFORCING; 89.2 longshot bias: 11 in-sample cells; 89.3/89.4/89.5 no edge), 89.7 left PARTIAL (PR #349
  open, CI failed; its remainder is 90.1 Part A, operator 2026-10-27 16:30 PT), Wave 88 results (5 of 6 frozen models scored against the
  market: NHL and NBA worse than it, MLB level with it; every skill weight effectively 0, so the gate keeps nothing; DRAFT ADR-0076
  awaiting the operator; kill switch still LOG-ONLY), Wave 87 results (core reconciled on 9 paths, 3 re-pointed;
  exposure gate on every order path in LOG-ONLY; 2 of 6 models scored vs market, both no better than it; skill weights all 0),
  Muse back on its three daily runs with a reordered backlog (2026-10-26), Wave 86 results (quant core merged; 1 of 6 models scored
  against the market; the market uses about one width per sport too; adverse selection dominates E3), THE QUANT ROLLOUT (operator 2026-10-22 16:58 PT: "I want one
  of the next waves to be purely quant refinement - I want to get our figures right (structurally ...)" ... "we need to have the same
  level of optionality - WITH QUALITY"; accepted 17:06 PT: Wave 86 = quant Wave A; a technique enters the library only with a test,
  a stated condition for when it applies, and one measured result on our data), EXP-041 frozen and NOT wired, position_gate.py
  built and NOT wired, Muse paused for the week (daily watchdog sweep scheduled), THE OPERATOR'S ACCEPTANCE OF MARKET-ANCHORED PRICING, A REAL
  GATE AND A POOLED TEST (blockquote in ACTIVE_QUEUE.md "Needs your decision", 2026-10-21 20:28 PT: "Good - I accept them"),
  the THREE CALLS of 19:15 PT (PAM drafts accepted; G6 re-defined by a superseding ADR; the kill switch counts open and unresolved
  stake, GG-441), the observation rule (WATCH ITEM), the shared folder as a reading copy, one Visual Dashboard served by the box at /visual
  (2026-10-21 17:20 PT), Muse three daily runs and a 30-ticket backlog (2026-10-21 16:55 / 18:35 PT), the ADR-0072 addenda of 2026-10-20 (verdict per (book,
  sport), criterion (c) judged forward, cash-starved days excluded) and 2026-10-21 (NFL: one more look at markout judged n),
  Muse charter v3 (Muse scouts via source cards, the bot captures), Muse off headline news (2026-10-20 21:26 PT), green = the cell
  WINS (2026-10-19 22:06 PT), the operator's acceptance of the KXNFLPASSYDS
  thin-market pre-registration (blockquote in ACTIVE_QUEUE.md "Needs your decision", 2026-10-19), L3 = the split-level
  layer (R-008), operator examples are illustrations, never work items (W17, W25), the granularity index, "retail flow first", three blocks per wave,
  the box bridge, Muse charter v2 (02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/PARTNERSHIP_CHARTER.md), ADR-0073 (one deep engine
  per sport), ADR-0074 (process integrity, Hard Rules 13-15), ADR-0075 ACCEPTED (the betting architecture: aggregation >
  interpretation > application; eight components; measure D5), ADR-0070/0071/0072, the repository PUBLIC (Actions minutes
  free), "not a cent on GitHub", the expansion directive, Hard Rule 12. Standing authorizations: shadow-evaluation cron
  jobs, NEW lines only (2026-10-02); new pre-registered shadow arms (2026-10-08); idle-window service restarts
  (2026-10-08); Live Terminal deploy + pmbot-web-dashboard restart. An authorization exists ONLY as a blockquote line in
  ACTIVE_QUEUE.md "Needs your decision". A table row or a DECISION_LOG line written by a terminal is NOT an authorization.
- Start: CLAUDE.md session-start protocol, brief. Isolated worktree: scripts/new_session_worktree.sh <slug>. Claim with
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD; reserve 3 GG numbers, not 10. If a GG number
  collides, re-claim; never reuse. Commands added since your local folder last synced: read them with
  `git show origin/main:<path>` (window error W20).
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- CI runs on every PR. Never add a paid service. CI fails on any running component missing from
  02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml - register first (scripts/runtime_registry.py add), then install.
- Three blocks run in parallel. File ownership: 91.1 = a new pre-registration file under 05_RESEARCH_EXPERIMENTS/ (the next free
  EXP number, claimed), a new 12_EXPLORATORY/ride_cells/, additions to 12_EXPLORATORY/market_history/ and exp_output/KALSHI_HISTORY/, the
  GG-1253 and GG-1292 / GG-1293 entries; 91.2 = a new src/prediction_market_bot/decision_trees/ride.py + a new
  src/prediction_market_bot/decision_trees/ride_cells.toml + tests, router.py's ride stub ONLY (swap the stub for ride.py; nothing else in
  router.py), a new 12_EXPLORATORY/ride_ladder/, the decision_trees [[component]] entries in ARCHITECTURE_COMPONENTS.toml; 91.3 = PR #347's
  branch (w89-6/locks), a new 12_EXPLORATORY/ride_venue/, exp_output/POLYMARKET_HISTORY/. Data: the price archive
  (exp_output/PRICE_ARCHIVE/, MLB + NFL, ~20-min snapshots from 2026-08-01; 90.2 and 90.3 read it locally - 90.1 believed it was on the box
  only: find it before concluding that) and Kalshi's public history via 12_EXPLORATORY/market_history/ (89.7 tooling, on main). THE RIDE
  TABLE CONTRACT (so no block waits on another): ride.py reads ride_cells.toml; each cell carries an evidence status - IN_SAMPLE,
  HELD_OUT, FORWARD_PASSED, FAILED, UNTESTED - and ride.py returns RIDE only for HELD_OUT or FORWARD_PASSED. 91.2 seeds the table with
  89.2's 11 cells as IN_SAMPLE (so they route NONE today). 91.1 and 91.2 Part B write their results to their own folders; the window
  moves statuses into the table at the wave close. Everyone may ADD to src/prediction_market_bot/quant/ (new functions with tests, no
  edits to existing ones); fetch + rebase before every push.
  TO_MUSE.md is append-only: fetch + rebase right before pushing. The gap agent owns GG_BURNDOWN.md and GG_AGENT_STATE.md. Box access: ssh, or the box bridge
  (04_EXECUTION/BOX_TASKS/requests/*.toml naming an allowlisted task; results in 04_EXECUTION/BOX_TASKS/results/). The box pulls
  main on its own timer: before trusting a bridge result after a merge, read deploy_truth_read's box HEAD.
  SURFACE BUDGET: read the box's budget_read before installing anything; Hard Rule 14: nothing new goes live unless it reads GREEN. Register every new component before it runs.
- ALL CODE lands through a PR with CI green - src/, scripts/, tests/ AND 12_EXPLORATORY/*.py. Only results (.md/.json/.csv) may be
  pushed docs-only.
- PERMISSIONS (revised 2026-10-13): do NOT edit .claude/settings*.json. If a command is refused: record the exact command and
  refusal, skip only that step, finish the rest, hand back. Never work around it. DONE means merged AND, for anything that
  runs, read back where it runs - never "merged" alone.
- DEMO / PAPER / SHADOW ACTIONS ARE PLUMBING (operator rule). Never write "operator decision needed" for a demo-only action;
  only real capital is his.
- PR mergeable_state dirty = almost always SESSION_CLAIMS.md / .last_session_checkpoint: merge origin/main into the
  branch locally, re-run the suite, push, merge.
- Shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md): fetch + rebase right before each push; edit
  only your own entries/rows. DECISION_LOG is append-only.
- No order, position, fill, stake size or kelly_fraction change. No live-ledger row rewritten. No edit of an existing cron
  line. No change to a live model, runner, registry cell or pre-registration except where your block's PERMISSIONS name
  it. Read-only GETs against the Kalshi DEMO API, and public unauthenticated Kalshi market-data GETs, are allowed.
- Python on the box is 3.9 and rejects Kalshi's 5-digit fractional ISO timestamps: parse with the tolerant parse_ts (W80.2).
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- A choice between two fixes for a demo/paper/shadow problem is NOT an operator decision: take the root-cause fix. Only a
  change to a pre-registration, a frozen artifact, a frozen book, real capital or an open strategic question goes to the
  operator - as one line, with your recommendation, after the rest of the block is done.
- PURPOSE (Hard Rule 12): your claim string names the distance-to-optimum measure this block is FOR (the PURPOSE line
  under the title). Your handoff fills vision_pillar, gap_measure and gap_delta (measured before -> after, with source).
  If what you find means the block cannot move its measure, say so and stop rather than doing adjacent work.
- THE QUANT BAR (from Wave 86 on): every technique you add carries (1) a test on known answers (a simulated case where the truth is
  known), (2) a one-line statement of when it applies and when it does not, (3) one measured result on OUR data with n and an
  interval. Without all three it is not added. Read-only on every live ledger, model, runner and pre-registration.
- ADR-0075: every factor you touch reports the stage it reached - aggregated / interpreted / applied (a tested path from
  the fact to a price, compared with the market). Quote the operator's words, never compress them (window error W16).
- GRANULARITY INDEX (operator 2026-10-16, 02_ARCHITECTURE_DESIGN/GRANULARITY_INDEX.md): every factor you build reports its
  five parts - the split, the rank against history, the matchup cross, the market map, the application. The operator's
  examples are illustrations, not build lists (window error W17).
- ADR-0074: handoffs carry pattern_sweep: ("n/a (no defect fixed)" when nothing was fixed) and surface_delta:.
- Every premise below is a claim to verify - CHECK IT AGAINST LOGS/DATA BEFORE BUILDING ON IT.
- Free data only. A factor only a paid source has is a registered GAP (GG), never bought.
- Report back: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result | MEASURE MOVED: <measure>
  <before> -> <after> (source) or none | stage reached per factor | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W91_<n>.md (docs-only push).

WAVE 91.2 - THE RIDE TREE AS CODE, AND A SECOND KIND OF RIDE: THE MARKET'S OWN LADDER. Repo: eignacio1/prediction-market-bot.
PURPOSE: DEPTH (+ PROOF). Measures: D5(a) decision_trees - ride tree built and tested as code (router stub replaced); ride KINDS with a
measured basis 1 (calibration cells, in-sample) -> 2 (+ ladder); ladder ride cells tested out of sample 0 -> n.
The operator, 2026-10-26 22:08 PT: "Sometimes it's best just to roll with the market sentiment - we don't always have to be it - that's the
meaning of having filtering mechs appropriately identifying the correct decision trees and routing mechanisms for execution." Riding the
market is not one tree. The calibration cells (89.2) ride the market's price where the whole market is biased. The LADDER ride trusts the
market's own centre: each game lists many strikes (totals, spreads, team totals), and 86.2 fitted the distribution they imply. A single
strike quoted off its own ladder is the market disagreeing with itself; riding the ladder means taking the ladder's side against that one
strike.
Premises to check: router.py (90.2, on main) defines the interface it expects from ride.py and uses a stub; the quant core has ladder.py
and coherence.py (86.2's helpers, moved in Wave 87); 86.2 measured coherence violations per 1,000 snapshots (12_EXPLORATORY/ladder_implied/).
PERMISSIONS: per the common rules' ownership. NOT: any order, gate, model, runner, ledger, registry cell or pre-registration; wiring the
router or ride.py into anything that runs (no wiring is authorized: DECISION_ROUTING.md).

PART A - ride.py (~35 min)
  A pure function from (sport, family, time tier, price, book state: spread and depth where measured, kind) to RIDE-YES / RIDE-NO / NONE
  with the expected net per contract and its interval. Driven by ride_cells.toml per the common rules' table contract (no numbers in
  code); seed it with 89.2's 11 cells as IN_SAMPLE. Two kinds: CALIBRATION (the table) and LADDER (Part B's cells, same table, kind =
  LADDER). Replace router.py's stub with ride.py and nothing else in router.py; the router tests still pass. Tests: a cell outside the
  table returns NONE; an IN_SAMPLE or FAILED cell returns NONE; a HELD_OUT cell returns its side; a book wider than the cell's measured
  spread returns NONE; k007 at the quote; a router replay on a frozen snapshot gives the same traffic as before the swap except RIDE,
  which goes to 0 (every cell is IN_SAMPLE today) - report that number.
PART B - The ladder ride, measured (~45 min)
  For each game's ladder in the price archive (MLB and NFL totals, spreads, team totals; NBA / NHL where 89.7's candles have ladders):
  fit the ladder WITHOUT the strike being tested (leave one out, with the core's ladder.py), and compare that strike's quote with the
  ladder's price. When the gap is larger than the cost to take the strike (half-spread + k007), does that strike settle toward the
  ladder, and does its quote move toward the ladder within 1 h and 3 h? Net of cost, game-clustered intervals, cells by family x tier x
  gap size x book state, BH at q = 0.10; selected on the first half in time, scored on the second half (the cell is HELD_OUT only if its
  second-half lower bound is > 0). Also: how often does the ladder correct the strike versus the strike correcting the ladder (both
  moving)? Results to 12_EXPLORATORY/ride_ladder/results_W91_2.md + cells json (kind LADDER, status HELD_OUT / FAILED).
Results: ride.py + ride_cells.toml + tests, the router swap, results_W91_2.md, the component entry (stage per ADR-0075: interpreted, or
applied only if a ladder cell holds out of sample), a handoff.

END OF BLOCK 91.2. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 91.3 — A third kind of ride: the other venue (Polymarket vs Kalshi)
**DEPTH + BREADTH** · terminal 3

```
COMMON RULES - WAVE 91 (RIDE THE MARKET: PROVE IT OR DROP IT, AND TWO NEW SOURCES) (read first; they bind this block)
- SIZE: MEDIUM. Target 60 minutes, hard ceiling 90 (operator 2026-10-07). Two parts. If your first estimate for the
  whole block is over 90 minutes, say so in one line, do Part A only, and name Part B as the next undone part. Do not
  re-verify things this prompt states as verified unless your work depends on them.
  After EACH part: push, and update this block's row in 04_EXECUTION/ACTIVE_QUEUE.md (NOW table: Status + one line)
  with a docs-only push. Stop at a pushed boundary (context ~60%, a blocker, or 90 minutes) and write the handoff.
  Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs, and ONLY on a CI result you
  have read as green (W80.1 merged #291 red and broke main). Read the Deploy job summary after each merge and record the
  t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-27 17:30 PT - incl. Wave 90 results (90.1: PR #349 and #352 merged; the hold-out
  scan found 0 candidates because only 1 of 1,850 cells was testable - UNDERPOWERED, not a null, GG-1292; ride.py not built. 90.2: the
  router built and wired to nothing; replay of 164,354 MLB + NFL situations = 97.66% NO-BET, 2.34% RIDE (in-sample cells only), 0 FADE,
  0 MOMENTUM. 90.3: pre-game moves of 3c+ are a random walk at 1-3 h in every sport; both following and fading lose to cost; 0 contexts
  routable), THE ROUTING DOCTRINE ACCEPTED (operator 2026-10-27: "Accept - proceed in full"; 02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md:
  FADE only on measured skill, RIDE only on a net-positive table cell, same side to RIDE, opposite sides to NO-BET, T3 a FADE-only overlay,
  news timing excluded; no wiring authorized by it), the box GREEN again (2026-10-28 00:18Z: 77 live, healthcheck HEALTHY, the MLB arm
  writing rows), THE RIDE-THE-MARKET DIRECTION (operator 22:12 PT: "we need
  substantively more architecture around the \"ride the market\" trees than we have before we come to any end all be all
  conclusions"; 22:08 PT: "Sometimes it's best just to roll with the market sentiment - we don't always have to be it - that's the
  meaning of having filtering mechs appropriately identifying the correct decision trees and routing mechanisms for execution"),
  Wave 89 results (kill switch ENFORCING; 89.2 longshot bias: 11 in-sample cells; 89.3/89.4/89.5 no edge), 89.7 left PARTIAL (PR #349
  open, CI failed; its remainder is 90.1 Part A, operator 2026-10-27 16:30 PT), Wave 88 results (5 of 6 frozen models scored against the
  market: NHL and NBA worse than it, MLB level with it; every skill weight effectively 0, so the gate keeps nothing; DRAFT ADR-0076
  awaiting the operator; kill switch still LOG-ONLY), Wave 87 results (core reconciled on 9 paths, 3 re-pointed;
  exposure gate on every order path in LOG-ONLY; 2 of 6 models scored vs market, both no better than it; skill weights all 0),
  Muse back on its three daily runs with a reordered backlog (2026-10-26), Wave 86 results (quant core merged; 1 of 6 models scored
  against the market; the market uses about one width per sport too; adverse selection dominates E3), THE QUANT ROLLOUT (operator 2026-10-22 16:58 PT: "I want one
  of the next waves to be purely quant refinement - I want to get our figures right (structurally ...)" ... "we need to have the same
  level of optionality - WITH QUALITY"; accepted 17:06 PT: Wave 86 = quant Wave A; a technique enters the library only with a test,
  a stated condition for when it applies, and one measured result on our data), EXP-041 frozen and NOT wired, position_gate.py
  built and NOT wired, Muse paused for the week (daily watchdog sweep scheduled), THE OPERATOR'S ACCEPTANCE OF MARKET-ANCHORED PRICING, A REAL
  GATE AND A POOLED TEST (blockquote in ACTIVE_QUEUE.md "Needs your decision", 2026-10-21 20:28 PT: "Good - I accept them"),
  the THREE CALLS of 19:15 PT (PAM drafts accepted; G6 re-defined by a superseding ADR; the kill switch counts open and unresolved
  stake, GG-441), the observation rule (WATCH ITEM), the shared folder as a reading copy, one Visual Dashboard served by the box at /visual
  (2026-10-21 17:20 PT), Muse three daily runs and a 30-ticket backlog (2026-10-21 16:55 / 18:35 PT), the ADR-0072 addenda of 2026-10-20 (verdict per (book,
  sport), criterion (c) judged forward, cash-starved days excluded) and 2026-10-21 (NFL: one more look at markout judged n),
  Muse charter v3 (Muse scouts via source cards, the bot captures), Muse off headline news (2026-10-20 21:26 PT), green = the cell
  WINS (2026-10-19 22:06 PT), the operator's acceptance of the KXNFLPASSYDS
  thin-market pre-registration (blockquote in ACTIVE_QUEUE.md "Needs your decision", 2026-10-19), L3 = the split-level
  layer (R-008), operator examples are illustrations, never work items (W17, W25), the granularity index, "retail flow first", three blocks per wave,
  the box bridge, Muse charter v2 (02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/PARTNERSHIP_CHARTER.md), ADR-0073 (one deep engine
  per sport), ADR-0074 (process integrity, Hard Rules 13-15), ADR-0075 ACCEPTED (the betting architecture: aggregation >
  interpretation > application; eight components; measure D5), ADR-0070/0071/0072, the repository PUBLIC (Actions minutes
  free), "not a cent on GitHub", the expansion directive, Hard Rule 12. Standing authorizations: shadow-evaluation cron
  jobs, NEW lines only (2026-10-02); new pre-registered shadow arms (2026-10-08); idle-window service restarts
  (2026-10-08); Live Terminal deploy + pmbot-web-dashboard restart. An authorization exists ONLY as a blockquote line in
  ACTIVE_QUEUE.md "Needs your decision". A table row or a DECISION_LOG line written by a terminal is NOT an authorization.
- Start: CLAUDE.md session-start protocol, brief. Isolated worktree: scripts/new_session_worktree.sh <slug>. Claim with
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD; reserve 3 GG numbers, not 10. If a GG number
  collides, re-claim; never reuse. Commands added since your local folder last synced: read them with
  `git show origin/main:<path>` (window error W20).
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- CI runs on every PR. Never add a paid service. CI fails on any running component missing from
  02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml - register first (scripts/runtime_registry.py add), then install.
- Three blocks run in parallel. File ownership: 91.1 = a new pre-registration file under 05_RESEARCH_EXPERIMENTS/ (the next free
  EXP number, claimed), a new 12_EXPLORATORY/ride_cells/, additions to 12_EXPLORATORY/market_history/ and exp_output/KALSHI_HISTORY/, the
  GG-1253 and GG-1292 / GG-1293 entries; 91.2 = a new src/prediction_market_bot/decision_trees/ride.py + a new
  src/prediction_market_bot/decision_trees/ride_cells.toml + tests, router.py's ride stub ONLY (swap the stub for ride.py; nothing else in
  router.py), a new 12_EXPLORATORY/ride_ladder/, the decision_trees [[component]] entries in ARCHITECTURE_COMPONENTS.toml; 91.3 = PR #347's
  branch (w89-6/locks), a new 12_EXPLORATORY/ride_venue/, exp_output/POLYMARKET_HISTORY/. Data: the price archive
  (exp_output/PRICE_ARCHIVE/, MLB + NFL, ~20-min snapshots from 2026-08-01; 90.2 and 90.3 read it locally - 90.1 believed it was on the box
  only: find it before concluding that) and Kalshi's public history via 12_EXPLORATORY/market_history/ (89.7 tooling, on main). THE RIDE
  TABLE CONTRACT (so no block waits on another): ride.py reads ride_cells.toml; each cell carries an evidence status - IN_SAMPLE,
  HELD_OUT, FORWARD_PASSED, FAILED, UNTESTED - and ride.py returns RIDE only for HELD_OUT or FORWARD_PASSED. 91.2 seeds the table with
  89.2's 11 cells as IN_SAMPLE (so they route NONE today). 91.1 and 91.2 Part B write their results to their own folders; the window
  moves statuses into the table at the wave close. Everyone may ADD to src/prediction_market_bot/quant/ (new functions with tests, no
  edits to existing ones); fetch + rebase before every push.
  TO_MUSE.md is append-only: fetch + rebase right before pushing. The gap agent owns GG_BURNDOWN.md and GG_AGENT_STATE.md. Box access: ssh, or the box bridge
  (04_EXECUTION/BOX_TASKS/requests/*.toml naming an allowlisted task; results in 04_EXECUTION/BOX_TASKS/results/). The box pulls
  main on its own timer: before trusting a bridge result after a merge, read deploy_truth_read's box HEAD.
  SURFACE BUDGET: read the box's budget_read before installing anything; Hard Rule 14: nothing new goes live unless it reads GREEN. Register every new component before it runs.
- ALL CODE lands through a PR with CI green - src/, scripts/, tests/ AND 12_EXPLORATORY/*.py. Only results (.md/.json/.csv) may be
  pushed docs-only.
- PERMISSIONS (revised 2026-10-13): do NOT edit .claude/settings*.json. If a command is refused: record the exact command and
  refusal, skip only that step, finish the rest, hand back. Never work around it. DONE means merged AND, for anything that
  runs, read back where it runs - never "merged" alone.
- DEMO / PAPER / SHADOW ACTIONS ARE PLUMBING (operator rule). Never write "operator decision needed" for a demo-only action;
  only real capital is his.
- PR mergeable_state dirty = almost always SESSION_CLAIMS.md / .last_session_checkpoint: merge origin/main into the
  branch locally, re-run the suite, push, merge.
- Shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md): fetch + rebase right before each push; edit
  only your own entries/rows. DECISION_LOG is append-only.
- No order, position, fill, stake size or kelly_fraction change. No live-ledger row rewritten. No edit of an existing cron
  line. No change to a live model, runner, registry cell or pre-registration except where your block's PERMISSIONS name
  it. Read-only GETs against the Kalshi DEMO API, and public unauthenticated Kalshi market-data GETs, are allowed.
- Python on the box is 3.9 and rejects Kalshi's 5-digit fractional ISO timestamps: parse with the tolerant parse_ts (W80.2).
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- A choice between two fixes for a demo/paper/shadow problem is NOT an operator decision: take the root-cause fix. Only a
  change to a pre-registration, a frozen artifact, a frozen book, real capital or an open strategic question goes to the
  operator - as one line, with your recommendation, after the rest of the block is done.
- PURPOSE (Hard Rule 12): your claim string names the distance-to-optimum measure this block is FOR (the PURPOSE line
  under the title). Your handoff fills vision_pillar, gap_measure and gap_delta (measured before -> after, with source).
  If what you find means the block cannot move its measure, say so and stop rather than doing adjacent work.
- THE QUANT BAR (from Wave 86 on): every technique you add carries (1) a test on known answers (a simulated case where the truth is
  known), (2) a one-line statement of when it applies and when it does not, (3) one measured result on OUR data with n and an
  interval. Without all three it is not added. Read-only on every live ledger, model, runner and pre-registration.
- ADR-0075: every factor you touch reports the stage it reached - aggregated / interpreted / applied (a tested path from
  the fact to a price, compared with the market). Quote the operator's words, never compress them (window error W16).
- GRANULARITY INDEX (operator 2026-10-16, 02_ARCHITECTURE_DESIGN/GRANULARITY_INDEX.md): every factor you build reports its
  five parts - the split, the rank against history, the matchup cross, the market map, the application. The operator's
  examples are illustrations, not build lists (window error W17).
- ADR-0074: handoffs carry pattern_sweep: ("n/a (no defect fixed)" when nothing was fixed) and surface_delta:.
- Every premise below is a claim to verify - CHECK IT AGAINST LOGS/DATA BEFORE BUILDING ON IT.
- Free data only. A factor only a paid source has is a registered GAP (GG), never bought.
- Report back: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result | MEASURE MOVED: <measure>
  <before> -> <after> (source) or none | stage reached per factor | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W91_<n>.md (docs-only push).

WAVE 91.3 - A THIRD KIND OF RIDE: THE OTHER VENUE. DOES KALSHI FOLLOW POLYMARKET, OR THE REVERSE? Repo: eignacio1/prediction-market-bot.
PURPOSE: DEPTH + BREADTH. Measures: venues with a joined price history 1 (Kalshi) -> 2; sports with a Kalshi-vs-Polymarket series 0 -> n
of 4; cross-venue ride cells tested out of sample 0 -> n. PART 0 is PLUMBING (PR #347).
The operator, 2026-10-26 22:08 PT: "Sometimes it's best just to roll with the market sentiment - we don't always have to be it". Muse found
no free history of sportsbook lines (R-057, R-058), so Kalshi has no outside anchor. A second market pricing the same game is one: when
the two disagree by more than Kalshi's cost to trade, one of them is about to move. If Kalshi reliably moves to Polymarket, riding
Polymarket's price on Kalshi is a ride tree. Reading Polymarket's public prices is allowed; trading there is not (the operator's identity
check is pending).
Premises to check: Polymarket serves public market data without an account (an events/markets listing and a price-history endpoint for
the international exchange; Polymarket US may differ) - verify which, how far back, at what granularity, and its terms. Muse's R-063
(running now, in a live session) covers the same sources: read its STATUS entry if it has landed, do not wait for it. Kalshi side: the
price archive (MLB + NFL) and 89.7's candles (NBA, NHL).
PERMISSIONS: per the common rules' ownership; PR #347's branch; public unauthenticated GETs to Polymarket and Kalshi (paced). NOT: any
Polymarket account, wallet or order; any Kalshi order, gate, model, runner, ledger, registry cell or pre-registration.

PART 0 - PR #347 (~10 min)
  89.6's lock alignment (pandas 2.2.3, scikit-learn 1.8.0, scipy 1.12.0, read from the box venv 2026-10-26) is green and unmerged: rebase
  on main, read CI green on the new head, merge, read the Deploy job summary and record the t4-mlb decision.
PART A - The joined series (~35 min)
  Polymarket's sports events for NFL, NBA, NHL and MLB game winners first (then spreads and totals if listed): join each to its Kalshi
  event by teams and true start time (Kalshi's listed time is start + 3.0 h); fetch both venues' prices on a common clock (the coarser
  of the two). Report per sport: events joined, unmatched (with reasons), history depth, and the price gap distribution (after removing
  Polymarket's fee and Kalshi's spread).
PART B - Who leads (~35 min)
  When the gap exceeds Kalshi's cost to trade (half-spread + k007), does Kalshi's price move toward Polymarket's within 1 h and 3 h, or
  Polymarket's toward Kalshi's? Which venue's pre-start price is better calibrated against the result (Brier, paired, game-clustered)?
  Net per Kalshi contract of riding Polymarket's side on Kalshi at the quote, by sport x family x tier x gap size, BH at q = 0.10,
  selected on the first half in time and scored on the second (HELD_OUT only if the second-half lower bound is > 0). If a sport has too
  few joined games for a test, say so with the n needed.
Results: 12_EXPLORATORY/ride_venue/results_W91_3.md + cells json (kind CROSS_VENUE, status HELD_OUT / FAILED / UNTESTED), the
stage reached per ADR-0075, gaps registered for what is not free, a handoff.

END OF BLOCK 91.3. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 91.3 REROUTED (operator 2026-10-27 17:32 PT) — NBA and NHL into the price archive, then the first NBA / NHL calibration scan
**BREADTH + PROOF** · terminal 3 · replaces the 91.3 block above (Polymarket stopped, 17:31 PT)

```
WAVE 91.3 (REROUTED, operator 2026-10-27 17:32 PT) - THE WINTER DATA THE RIDE TREES NEED: NBA AND NHL INTO THE PRICE ARCHIVE, THEN THE
FIRST NBA / NHL CALIBRATION SCAN. Repo: eignacio1/prediction-market-bot.
REPLACES your earlier 91.3 entirely. Polymarket is stopped (operator 17:31 PT: "we're not building shit for polymarket yet"): make no
Polymarket request; commit, push or merge nothing Polymarket; if you opened a Polymarket PR, close it unmerged; leave local Polymarket
files uncommitted and list them in your handoff. The Wave 91 common rules you already have still bind, except 91.3's file ownership,
which is replaced below. Keep your claim range (T-1350..T-1354 / GG-1350..GG-1352); append a claim row naming the reroute.
PURPOSE: BREADTH + PROOF. Measures: sports in the price archive 2 (MLB, NFL) -> 4 (+ NBA, NHL); NBA / NHL families with a calibration
scan 0 -> n; in-season ride candidates (IN_SAMPLE, for a later pre-registration) 0 -> n.
Why: 10 of the 11 ride cells are MLB, whose season ends this week. The ride trees need evidence this winter, and that means NBA and NHL.
Neither is in the price archive (GG-1250, GG-1330): only 89.7's hourly candles exist for them, and only for game families. Without
~20-minute snapshots with the bid and ask, nothing found in NBA / NHL can ever be tested forward.
Premises to check: scripts/archive_market_prices.py takes --series and --depth-sample-per-family and writes exp_output/PRICE_ARCHIVE/; its
MLB and NFL cron lines are in 02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml (MLB windows are UTC evening only, a fit for MLB, not
necessarily for NBA / NHL tip times and the T6-24h tier). Kalshi's listed time is the true start + 3.0 h (89.7). Which NBA / NHL series
exist (game, spread, total, team total, player props) - list them from Kalshi's public API, never assume.
FILE OWNERSHIP (replaces the common rules' 91.3 line): NEW cron lines for the archiver + their RUNTIME_REGISTRY.toml entries, a new
12_EXPLORATORY/ride_scan_nba_nhl/, NBA / NHL candles under exp_output/KALSHI_HISTORY/nba/ and /nhl/ only (91.1 owns MLB and NFL there),
the GG-1250 / GG-1330 entries, PR #347's branch.
PERMISSIONS: NEW cron lines only (never edit an existing line, including the MLB ones that go idle after the World Series), installed
only if budget_read reads GREEN and only after registering each line; public unauthenticated Kalshi market-data GETs, paced. NOT: any
order, gate, model, runner, ledger, registry cell or pre-registration; ride.py or the router (91.2's); 91.1's files.

PART 0 - PR #347 (~10 min, if not already merged)
  Rebase on main, read CI green on the new head, merge, read the Deploy job summary, record the t4-mlb decision.
PART A - NBA and NHL into the archive (~40 min)
  1. List the NBA and NHL series Kalshi serves; choose game, spread, total and team-total families first, player props where listed
     (say which and why any are left out).
  2. Cron windows that cover each sport's pre-game tiers (T>24h, T6-24h, T2-6h, T0-2h before the TRUE start), ~20-min cadence near
     the start, coarser further out. Measure one run's rows, bytes and duration per sport, project disk use per month against the box's
     free space, and stay within Kalshi's rate limits (state the pacing).
  3. Register, install on GREEN, then read back on the box (bridge or ssh): rows written per sport in the first window, no 429s, the
     staleness alarm wired. GG-1250 / GG-1330: resolve what is done, keep open what is not (parlays, if not covered).
PART B - The first NBA / NHL calibration scan, as discovery (~35 min)
  89.2's method unchanged (12_EXPLORATORY/longshot_bias/calib.py: first two-sided snapshot per ticker per tier, settled outcome, net at
  the quote minus k007, game-clustered, BH at q = 0.10) on 89.7's NBA / NHL candles plus any spread / total / team-total candles you
  fetch (every strike, not a sample; 90.1's 4-strikes-per-event sample is why its scan was underpowered, GG-1292). Report every
  survivor: family, tier, price band, book view, side, n, games, net with interval. Label them all IN_SAMPLE: they are candidates for a
  pre-registered forward test on the new archive rows next wave, not evidence. If no cell is testable, give the n needed per family and
  the date the new archive reaches it.
Results: the cron lines + registry entries (read back on the box), 12_EXPLORATORY/ride_scan_nba_nhl/results_W91_3.md + candidates json
(status IN_SAMPLE), a handoff (vision_pillar BREADTH + PROOF; surface_delta = the lines added), and one operator line: which NBA / NHL
candidates a forward test should cover, or none.

END OF BLOCK 91.3 (REROUTED). If you cannot see this line, the prompt reached you truncated: stop and report it.
```
