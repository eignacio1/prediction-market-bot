# Wave 90 — paste blocks (ride the market: trees, router, momentum)

Copy each block as one fenced paste. The wave's table, results and status live in `04_EXECUTION/ACTIVE_QUEUE.md` § "NOW — Wave 90".
Rewritten 2026-10-27 16:40 PT: 89.7 ended partial (PR #349 open, CI failed), so its remainder is 90.1 Part A (operator 16:30 PT); the ride
tree's pre-registration and shadow arm move to Wave 91. All three blocks run now.

### 90.1 — Finish 89.7 (the ride data and the hold-out scan), then the ride tree as code
**PROOF + DEPTH** · terminal 1

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
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD. If a GG number
  collides, re-claim; never reuse. Commands added since your local folder last synced: read them with
  `git show origin/main:<path>` (window error W20).
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- CI runs on every PR. Never add a paid service. CI fails on any running component missing from
  02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml - register first (scripts/runtime_registry.py add), then install.
- Three blocks run in parallel. File ownership: 90.1 = PR #349's branch and files (12_EXPLORATORY/ride_market_scan/,
  12_EXPLORATORY/market_history/ additions, exp_output/KALSHI_HISTORY/), a new src/prediction_market_bot/decision_trees/ride.py + tests,
  the GG-1230..1232 and GG-1253 / GG-1260..1269 entries, and the archiver's family list only on GREEN; 90.2 = a new
  src/prediction_market_bot/decision_trees/router.py + tests, a new 12_EXPLORATORY/router_replay/, a new
  02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md, the decision_trees and filtering_mechanisms [[component]] entries in
  ARCHITECTURE_COMPONENTS.toml; 90.3 = a new 12_EXPLORATORY/momentum_j/. Data: 90.2 and 90.3 use the price archive
  (exp_output/PRICE_ARCHIVE/, MLB + NFL) and, for NBA / NHL, 89.7's Kalshi history tooling - from main once 90.1 merges PR #349, else
  read its branch's code read-only and fetch for yourself; never merge or push to PR #349. 90.2 defines the interface it expects from
  ride.py and tests against a stub of its own until ride.py is on main. Everyone may ADD to src/prediction_market_bot/quant/ (new
  functions with tests, no edits to existing ones); fetch + rebase before every push.
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

WAVE 90.1 - FINISH 89.7 (THE RIDE DATA AND THE HOLD-OUT SCAN), THEN THE RIDE TREE AS CODE. Repo: eignacio1/prediction-market-bot.
PURPOSE: PROOF + DEPTH. Measures: families testable for a calibration test MLB + NFL -> + NBA + NHL (+ props where Kalshi has candles);
89.2's candidate cells tested OUT OF SAMPLE 0 -> n; in-season ride candidates (NFL, NBA, NHL) 0 -> n; D5(a) decision_trees - a second
tree type (ride) built and tested as code. The operator, 2026-10-27 16:30 PT: "Just partition the remaining work from 89.7 into one of
the blocks". The operator, 2026-10-26 22:12 PT: "we need substantively more architecture around the \"ride the market\" trees than we
have before we come to any end all be all conclusions." The ride tree's PRE-REGISTRATION and SHADOW ARM move to Wave 91: they need this
block's out-of-sample results first.
STATE YOU INHERIT (W89.7, handoff 11_MEMORY_HANDOFF/SESSION_HANDOFF_20261027T0540Z_W89_7.md on branch
session/20261027T051711Z-w89-7-ride-data, PR #349, OPEN, CI FAILED): Kalshi's occurrence_datetime is exactly 3.0 h after the scheduled
start in all three sports; the ESPN join recovers true start times except 135 NFL events (Kalshi LA = Rams / ESPN LAR, LAC = Chargers
alias wrong); hourly candles exist for NBA and NHL game families and part of NFL's; spread, total, team-total and prop families are listed
but not fetched. CI failure: tests/test_exploratory_isolation.py flags w89_7_backfill.py:86 `.replace()` and :277 `.write_text()` as writes
not routed through safe_out() (CHARTER rule 3, the exploratory fence). Not done: GG-1260..1269 registration, DECISION_LOG, queue row,
runtime-registry entry, MLB HHMM-as-ET check (GG-1253), session close; the worktree and claim are still open. Note from 89.7: "run a
sport's phases one at a time - the original chained prep run overwrote a good NFL schedule with an empty one."
PERMISSIONS: per the common rules' ownership; you take over PR #349 and its branch (rebase on main, fix, merge on green CI); public
unauthenticated Kalshi market-data GETs (paced) and free schedule sources. NOT: any order, gate, model, runner, ledger, registry cell or
pre-registration; the price archiver's family list only if budget_read is GREEN (register first; otherwise a task).

PART A - Finish 89.7 (~50 min)
  1. PR #349: route the two writes through safe_out() (the fence is right; do not weaken it), rebase, CI green, merge, read back.
  2. Fix the LA alias and re-join the 135 NFL events; check MLB HHMM-as-ET against the schedule (GG-1253).
  3. Candles for spread, total, team-total and prop families per sport, newest first, one sport's phase at a time.
  4. 89.2's method unchanged, with a TIME SPLIT: cells chosen on the earlier half, tested on the later half; 89.2's three named MLB
     candidates re-tested on dates after its window and on 2025 history; then NBA, NHL and NFL with true start times. Every survivor:
     family, tier, bucket, side (ride the favourite / fade the longshot), n, games, net per contract with interval, held out of sample
     yes/no. Register GG-1260..1269 (or the numbers you claim), the DECISION_LOG entry, close 89.7's claim.
PART B - The ride tree as code (~30 min)
  src/prediction_market_bot/decision_trees/ride.py: a pure function from (sport, family, time tier, price, book state: spread / depth
  where measured) to RIDE-YES / RIDE-NO / NONE with the expected net per contract and its interval, driven by a table FILE of cells
  (the Part A out-of-sample survivors, labelled; no numbers hard-coded). Tests: a cell outside the table returns NONE; a book wider than
  the cell's measured spread returns NONE; the k007 fee is applied at the quote. Wired into nothing.
Results: results_W89_7.md (or results_W90_1.md), the module + tests, a handoff, and one operator line naming the survivors Wave 91 should
pre-register as ride trees (or "none held out of sample").

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
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD. If a GG number
  collides, re-claim; never reuse. Commands added since your local folder last synced: read them with
  `git show origin/main:<path>` (window error W20).
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- CI runs on every PR. Never add a paid service. CI fails on any running component missing from
  02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml - register first (scripts/runtime_registry.py add), then install.
- Three blocks run in parallel. File ownership: 90.1 = PR #349's branch and files (12_EXPLORATORY/ride_market_scan/,
  12_EXPLORATORY/market_history/ additions, exp_output/KALSHI_HISTORY/), a new src/prediction_market_bot/decision_trees/ride.py + tests,
  the GG-1230..1232 and GG-1253 / GG-1260..1269 entries, and the archiver's family list only on GREEN; 90.2 = a new
  src/prediction_market_bot/decision_trees/router.py + tests, a new 12_EXPLORATORY/router_replay/, a new
  02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md, the decision_trees and filtering_mechanisms [[component]] entries in
  ARCHITECTURE_COMPONENTS.toml; 90.3 = a new 12_EXPLORATORY/momentum_j/. Data: 90.2 and 90.3 use the price archive
  (exp_output/PRICE_ARCHIVE/, MLB + NFL) and, for NBA / NHL, 89.7's Kalshi history tooling - from main once 90.1 merges PR #349, else
  read its branch's code read-only and fetch for yourself; never merge or push to PR #349. 90.2 defines the interface it expects from
  ride.py and tests against a stub of its own until ride.py is on main. Everyone may ADD to src/prediction_market_bot/quant/ (new
  functions with tests, no edits to existing ones); fetch + rebase before every push.
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
  price history per sport (see the common rules' Data line): how many situations route to each tree, and - DESCRIPTIVE only - settlement minus price for each
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
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD. If a GG number
  collides, re-claim; never reuse. Commands added since your local folder last synced: read them with
  `git show origin/main:<path>` (window error W20).
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- CI runs on every PR. Never add a paid service. CI fails on any running component missing from
  02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml - register first (scripts/runtime_registry.py add), then install.
- Three blocks run in parallel. File ownership: 90.1 = PR #349's branch and files (12_EXPLORATORY/ride_market_scan/,
  12_EXPLORATORY/market_history/ additions, exp_output/KALSHI_HISTORY/), a new src/prediction_market_bot/decision_trees/ride.py + tests,
  the GG-1230..1232 and GG-1253 / GG-1260..1269 entries, and the archiver's family list only on GREEN; 90.2 = a new
  src/prediction_market_bot/decision_trees/router.py + tests, a new 12_EXPLORATORY/router_replay/, a new
  02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md, the decision_trees and filtering_mechanisms [[component]] entries in
  ARCHITECTURE_COMPONENTS.toml; 90.3 = a new 12_EXPLORATORY/momentum_j/. Data: 90.2 and 90.3 use the price archive
  (exp_output/PRICE_ARCHIVE/, MLB + NFL) and, for NBA / NHL, 89.7's Kalshi history tooling - from main once 90.1 merges PR #349, else
  read its branch's code read-only and fetch for yourself; never merge or push to PR #349. 90.2 defines the interface it expects from
  ride.py and tests against a stub of its own until ride.py is on main. Everyone may ADD to src/prediction_market_bot/quant/ (new
  functions with tests, no edits to existing ones); fetch + rebase before every push.
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
Data: the price archive (MLB, NFL, 20-min snapshots) and, for NBA / NHL, Kalshi hourly candles via 89.7's tooling (see the common
rules' Data line); true start = Kalshi occurrence_datetime minus 3.0 h (89.7's finding).
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
