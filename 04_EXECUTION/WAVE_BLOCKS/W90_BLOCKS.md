# Wave 90 — paste blocks (ride the market: trees, router, momentum)

Copy each block as one fenced paste. The wave's table, results and status live in `04_EXECUTION/ACTIVE_QUEUE.md` § "NOW — Wave 90".
Run AFTER 89.7 (tonight's single block) has pushed its results: 90.1 and 90.3 read them.

### 90.1 — The ride-the-market tree: built, pre-registered, logging in shadow
**DEPTH + PROOF** · terminal 1

```
COMMON RULES - WAVE 90 (RIDE THE MARKET: TREES, ROUTER, MOMENTUM) (read first; they bind this block)
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
- Decisions in force: DECISION_LOG through 2026-10-26 22:15 PT - incl. THE RIDE-THE-MARKET DIRECTION (operator 22:12 PT: "we need
  substantively more architecture around the \"ride the market\" trees than we have before we come to any end all be all
  conclusions"; 22:08 PT: "Sometimes it's best just to roll with the market sentiment - we don't always have to be it - that's the
  meaning of having filtering mechs appropriately identifying the correct decision trees and routing mechanisms for execution"),
  Wave 89 results (kill switch ENFORCING; 89.2 longshot bias: 11 in-sample cells; 89.3/89.4/89.5 no edge) and 89.7 (the ride data
  and the hold-out scan; read its results first), Wave 88 results (5 of 6 frozen models scored against the
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
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD. If a GG number
  collides, re-claim; never reuse. Commands added since your local folder last synced: read them with
  `git show origin/main:<path>` (window error W20).
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- CI runs on every PR. Never add a paid service. CI fails on any running component missing from
  02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml - register first (scripts/runtime_registry.py add), then install.
- Three blocks run in parallel. File ownership: 90.1 = a new src/prediction_market_bot/decision_trees/ride.py + tests, one new
  pre-registration file in 05_RESEARCH_EXPERIMENTS/ (next free EXP number), a new shadow runner/cron line for it ONLY if the budget
  is GREEN (register first), its registry cells, and the GG-1230 / GG-1231 / GG-1232 entries; 90.2 = a new src/prediction_market_bot/decision_trees/router.py + tests, a new
  12_EXPLORATORY/router_replay/, a new 02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md, the decision_trees and filtering_mechanisms
  [[component]] entries in ARCHITECTURE_COMPONENTS.toml; 90.3 = a new 12_EXPLORATORY/momentum_j/. 90.2 may import 90.1's ride.py
  only after it is on main; until then it defines the interface it expects and tests against a stub of its own. May ADD to
  src/prediction_market_bot/quant/ (new functions with tests, no edits to existing ones); fetch + rebase before every push.
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W90_<n>.md (docs-only push).

WAVE 90.1 - THE RIDE-THE-MARKET TREE: BUILT, PRE-REGISTERED, LOGGING IN SHADOW. Repo: eignacio1/prediction-market-bot.
PURPOSE: DEPTH + PROOF. Measures: D5(a) decision_trees - a second tree type (ride) beside the contrarian one, built and tested;
D3 pre-registered challengers +1 (the ride tree); B1 cells logging +n if wired. The operator, 2026-10-26: "Sometimes it's best just to
roll with the market sentiment - we don't always have to be it". A ride tree buys the side the market already favours (or sells the
longshot) only where the market's own price has been measured wrong in that direction net of fees: 89.2 (in-sample) and 89.7 (with a
hold-out; read 12_EXPLORATORY/ride_market_scan/results_W89_7.md first). Riding is not "always bet the favourite": at a fair price the
favourite only breaks even before fees.
PERMISSIONS: per the common rules' ownership; the standing authorization for new pre-registered shadow arms (2026-10-08) covers a
shadow runner if the budget is GREEN. NOT: any existing runner, cell, model, ledger or pre-registration; stakes stay $1 demo /
kelly_fraction 0; no cell chosen from data after its pre-registration is committed.

PART 0 - The red (~10 min, only if budget_read is RED)
  At the Wave 89 close (2026-10-27 05:13Z) the box read RED on one fault: the MLB game-market shadow, silent since 2026-10-25 18:07Z;
  W89.1 expected its first in-window row at 06:07Z and left GG-1230 / GG-1232 open and GG-1231 without an alarm. Read whether that row
  landed (with the quote-time fields); if so, close GG-1230 / GG-1232 with the evidence and confirm GREEN; if not, find why before
  wiring anything. You own those three gap entries this wave.
PART A - The tree, as code (~40 min)
  decision_trees/ride.py: a pure function from (family, time tier, price, book state: spread / depth where measured, sport) to
  RIDE-YES / RIDE-NO / NONE, with the expected net per contract and its interval, driven by a table of cells loaded from the
  pre-registration file (no numbers hard-coded). Tests: a cell outside the table returns NONE; a wide book outside the measured
  spread returns NONE; the fee is applied at the quote.
PART B - Pre-register and log (~40 min)
  The pre-registration: ONLY the cells that held OUT OF SAMPLE in 89.7 (or the in-sample 89.2 cells labelled as such, if none held),
  per sport; primary metric = net settlement minus entry price per contract, game-clustered; judged n from a power calc on the
  measured effect; look dates; modal outcome written down first; the pooled-test rule (accepted 2026-10-21) across cells with BH.
  Commit it, then (budget GREEN only) a shadow arm that evaluates the ride tree on live markets and logs rows - no orders unless the
  demo switches already cover shadow arms, at $1. If the budget is RED, stop at the pre-registration and say so.
Results: the module + tests, the pre-registration, read-back of first rows if wired, a handoff.

END OF BLOCK 90.1. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 90.2 — The router: ride, fade or no-bet
**DEPTH** · terminal 2

```
COMMON RULES - WAVE 90 (RIDE THE MARKET: TREES, ROUTER, MOMENTUM) (read first; they bind this block)
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
- Decisions in force: DECISION_LOG through 2026-10-26 22:15 PT - incl. THE RIDE-THE-MARKET DIRECTION (operator 22:12 PT: "we need
  substantively more architecture around the \"ride the market\" trees than we have before we come to any end all be all
  conclusions"; 22:08 PT: "Sometimes it's best just to roll with the market sentiment - we don't always have to be it - that's the
  meaning of having filtering mechs appropriately identifying the correct decision trees and routing mechanisms for execution"),
  Wave 89 results (kill switch ENFORCING; 89.2 longshot bias: 11 in-sample cells; 89.3/89.4/89.5 no edge) and 89.7 (the ride data
  and the hold-out scan; read its results first), Wave 88 results (5 of 6 frozen models scored against the
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
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD. If a GG number
  collides, re-claim; never reuse. Commands added since your local folder last synced: read them with
  `git show origin/main:<path>` (window error W20).
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- CI runs on every PR. Never add a paid service. CI fails on any running component missing from
  02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml - register first (scripts/runtime_registry.py add), then install.
- Three blocks run in parallel. File ownership: 90.1 = a new src/prediction_market_bot/decision_trees/ride.py + tests, one new
  pre-registration file in 05_RESEARCH_EXPERIMENTS/ (next free EXP number), a new shadow runner/cron line for it ONLY if the budget
  is GREEN (register first), its registry cells, and the GG-1230 / GG-1231 / GG-1232 entries; 90.2 = a new src/prediction_market_bot/decision_trees/router.py + tests, a new
  12_EXPLORATORY/router_replay/, a new 02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md, the decision_trees and filtering_mechanisms
  [[component]] entries in ARCHITECTURE_COMPONENTS.toml; 90.3 = a new 12_EXPLORATORY/momentum_j/. 90.2 may import 90.1's ride.py
  only after it is on main; until then it defines the interface it expects and tests against a stub of its own. May ADD to
  src/prediction_market_bot/quant/ (new functions with tests, no edits to existing ones); fetch + rebase before every push.
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W90_<n>.md (docs-only push).

WAVE 90.2 - THE ROUTER: THE FILTERING LAYER THAT SENDS EACH SITUATION TO RIDE, FADE OR NO-BET. Repo: eignacio1/prediction-market-bot.
PURPOSE: DEPTH. Measures: D5(a) filtering_mechanisms and decision_trees components with a built, tested scaffold (name the sports);
situations replayed through the router 0 -> n, with the share routed to each tree. The operator, 2026-10-26 22:08 PT: "that's the meaning
of having filtering mechs appropriately identifying the correct decision trees and routing mechanisms for execution". Today every arm
runs one tree (bet where the model disagrees with the price) and it loses; ADR-0014's T3 CONFIRM / FADE / NEUTRAL overlay and
Strategy J (02_ARCHITECTURE_DESIGN/STRATEGY_OVERVIEW.md: J1 follow, J2 fade, "the transition point ... is the critical unknown") were
designed and never built. Read both, and ADR-0075's component definitions, before designing.
PERMISSIONS: per the common rules' ownership. NOT: any runner, cell, model, ledger, gate wiring or pre-registration; nothing goes live.

PART A - The routing doctrine (~30 min)
  02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md: the trees (FADE = our model or a factor says the line is wrong; RIDE = the market's own
  price is measured wrong toward its favourite; MOMENTUM-FOLLOW / MOMENTUM-FADE = Strategy J, pending 90.3; NO-BET), and the
  conditions that route a situation to each, every condition a MEASURED quantity with its source: the model's skill against the
  market for that sport and family (W88.3: ~0 everywhere, so FADE gets no traffic until a model earns it), the ride table (90.1),
  price level, book state, time to start, recent movement, news timing. Precedence when two trees claim the same market, and how
  T3's CONFIRM/FADE fits. One page of plain English first, then the table.
PART B - The router as code, replayed (~50 min)
  decision_trees/router.py implementing the doctrine as a pure function, with tests; replay it over the shadow ledgers and the
  Kalshi history (89.7) per sport: how many situations route to each tree, and - DESCRIPTIVE only - settlement minus price for each
  tree's traffic, game-clustered. A tree that gets traffic without measured skill is a defect: the replay should show none.
Results: the doctrine, the module + tests, results_W90.md, ARCHITECTURE_COMPONENTS.toml updates, a handoff, and one operator line:
accept the routing doctrine as written, or change it.

END OF BLOCK 90.2. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 90.3 — Momentum, measured (Strategy J)
**DEPTH + PROOF** · terminal 3

```
COMMON RULES - WAVE 90 (RIDE THE MARKET: TREES, ROUTER, MOMENTUM) (read first; they bind this block)
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
- Decisions in force: DECISION_LOG through 2026-10-26 22:15 PT - incl. THE RIDE-THE-MARKET DIRECTION (operator 22:12 PT: "we need
  substantively more architecture around the \"ride the market\" trees than we have before we come to any end all be all
  conclusions"; 22:08 PT: "Sometimes it's best just to roll with the market sentiment - we don't always have to be it - that's the
  meaning of having filtering mechs appropriately identifying the correct decision trees and routing mechanisms for execution"),
  Wave 89 results (kill switch ENFORCING; 89.2 longshot bias: 11 in-sample cells; 89.3/89.4/89.5 no edge) and 89.7 (the ride data
  and the hold-out scan; read its results first), Wave 88 results (5 of 6 frozen models scored against the
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
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD. If a GG number
  collides, re-claim; never reuse. Commands added since your local folder last synced: read them with
  `git show origin/main:<path>` (window error W20).
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- CI runs on every PR. Never add a paid service. CI fails on any running component missing from
  02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml - register first (scripts/runtime_registry.py add), then install.
- Three blocks run in parallel. File ownership: 90.1 = a new src/prediction_market_bot/decision_trees/ride.py + tests, one new
  pre-registration file in 05_RESEARCH_EXPERIMENTS/ (next free EXP number), a new shadow runner/cron line for it ONLY if the budget
  is GREEN (register first), its registry cells, and the GG-1230 / GG-1231 / GG-1232 entries; 90.2 = a new src/prediction_market_bot/decision_trees/router.py + tests, a new
  12_EXPLORATORY/router_replay/, a new 02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md, the decision_trees and filtering_mechanisms
  [[component]] entries in ARCHITECTURE_COMPONENTS.toml; 90.3 = a new 12_EXPLORATORY/momentum_j/. 90.2 may import 90.1's ride.py
  only after it is on main; until then it defines the interface it expects and tests against a stub of its own. May ADD to
  src/prediction_market_bot/quant/ (new functions with tests, no edits to existing ones); fetch + rebase before every push.
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W90_<n>.md (docs-only push).

WAVE 90.3 - MOMENTUM, MEASURED: WHEN A LINE MOVES, FOLLOW IT OR FADE IT? (STRATEGY J). Repo: eignacio1/prediction-market-bot.
PURPOSE: DEPTH + PROOF. Measures: D5(a) momentum_looping with a measured basis (0 -> per sport); the follow-vs-fade transition
estimated 0 -> n contexts. STRATEGY_OVERVIEW.md, Strategy J: "J1 - Trend following: Bet in the direction of momentum early (follow the
smart money as it moves the line)"; "J2 - Fade the crowd: Bet against momentum late"; "J1 and J2 are contradictory - the transition
point between \"follow\" and \"fade\" is the critical unknown." 89.2 Part B tested only FADING: after pre-game moves of 5c or more,
reverting lost in all 40 testable cells net of costs (every net negative) - which is evidence for FOLLOWING, not yet a test of it.
Data: the price archive (MLB, NFL, 20-min snapshots) and 89.7's Kalshi history with true start times (NBA, NHL, NFL; hourly or finer).
PERMISSIONS: per the common rules' ownership; read-only data. NOT: any order, runner, model, ledger or pre-registration.

PART A - Follow, net of costs (~45 min)
  For pre-game moves (size buckets 3c / 5c / 10c+, measured over 20-60 min), the return of entering IN the direction of the move at the
  next snapshot's quote and holding to +1h, +3h and to settlement, net of both half-spreads and the k007 fee; by sport, family, time
  to start and book state; game-clustered; BH. Then the same split by whether the move followed a public news time (NBA official
  injury report times from the relay; NFL report days; lineups) - news-driven moves vs unexplained ones.
PART B - The transition (~35 min)
  Where (time to start, move size, news or no news) does following stop paying and fading start? Fit it as a few interpretable
  cuts, not a black box; hold out the later half by date. The quant bar applies (a simulated trend and a simulated mean-reversion
  are each recovered). Name the contexts, if any, that 90.2's router should route to MOMENTUM-FOLLOW or MOMENTUM-FADE, with n and the
  out-of-sample net.
Results: results_W90.md, the code, a handoff, and one operator line: which contexts deserve a pre-registration.

END OF BLOCK 90.3. If you cannot see this line, the prompt reached you truncated: stop and report it.
```
