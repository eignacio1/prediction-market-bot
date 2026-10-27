# Wave 89 — paste blocks (six terminals)

The one place to copy Wave 89's pastes from: each block is one fenced paste under its `### 89.x` header. The wave's table, results and status live in `04_EXECUTION/ACTIVE_QUEUE.md` § "NOW — Wave 89". Moved here 2026-10-26 21:15 PT because the queue had grown too large to display (operator 21:08 PT).

### 89.1 — Before real money, finished: the red cleared, then the kill switch enforcing
**PLUMBING** · terminal 1

```
COMMON RULES - WAVE 89 (WHERE THE LINE IS WEAK) (read first; they bind this block)
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
- Decisions in force: DECISION_LOG through 2026-10-26 19:50 PT - incl. Wave 88 results (5 of 6 frozen models scored against the
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
- Three blocks run in parallel. File ownership: 89.1 = src/prediction_market_bot/c4_risk_engine/ (the enforce flip) + tests, the
  GG-441 / GG-1082 / GG-1230..1232 entries, and the silent-arm check if the red needs it; 89.2 = a new 12_EXPLORATORY/longshot_bias/;
  89.3 = a new 12_EXPLORATORY/unpriced_screen/ and SEATS/nfl.toml + SEATS/nba.toml (rows you move only). 89.2 and 89.3 may ADD to
  src/prediction_market_bot/quant/ (new functions with tests, no edits to existing ones).
  TO_MUSE.md is append-only: fetch + rebase right before pushing. The gap agent owns GG_BURNDOWN.md and GG_AGENT_STATE.md. Box access: ssh, or the box bridge
  (04_EXECUTION/BOX_TASKS/requests/*.toml naming an allowlisted task; results in 04_EXECUTION/BOX_TASKS/results/). The box pulls
  main on its own timer: before trusting a bridge result after a merge, read deploy_truth_read's box HEAD.
  SURFACE BUDGET: read the box's budget_read before installing anything. At the Wave 88 close it was RED on one silent arm (the
  MLB game-market shadow; W88.2 merged the fix, #336, awaiting an in-window row). Hard Rule 14: nothing new goes live until GREEN. Register every new component before it runs.
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W89_<n>.md (docs-only push).

WAVE 89.1 - BEFORE REAL MONEY, FINISHED: THE RED CLEARED, THEN THE KILL SWITCH ENFORCING. Repo: eignacio1/prediction-market-bot.
PURPOSE: PLUMBING. Measures: SURFACE BUDGET RED -> GREEN; GG-1082 and GG-441 OPEN -> RESOLVED (enforcing on every order path, read
back on the box); GG-1230 / GG-1232 closed on read-back.
W88.2 (#336, #339; handoff 11_MEMORY_HANDOFF/SESSION_HANDOFF_20261027T0150Z_W88_2.md): the MLB game-market shadow's silence was a
games-cache sync that stopped chaining from its previous output (GG-1230; GG-1231: no alarm on a failing sync); fixed, but no
in-window row had been written yet, so the budget still read RED. Shadow rows now carry quote_ts_utc / quote_age_s / quote_ts_source
from the response's Date header (GG-1232), not yet read back on the box. The enforce flip was not started. The exposure gate has run
LOG-ONLY on every order path since 2026-10-27 ~00:10Z (logs/exposure_gate_logonly.jsonl); t4-mlb was waiting for a no-game restart.
TIMING: Part B needs one full game day of LOG-ONLY with every book feeding (including T4 MLB after its restart). If that does not
exist when you start, do Part A, state the earliest time Part B can run, and stop.
PERMISSIONS: per the common rules' ownership; an idle-window t4-mlb restart (standing authorization 2026-10-08). NOT: any limit
VALUE, kelly_fraction, stakes, which orders a strategy places, existing cron lines.

PART A - Read back and clear the red (~30 min)
  Read on the box: a new MLB game-market shadow row written inside its window (if the World Series has no game in the window, show
  the schedule and make the silent-arm check say "no game" instead of alarming, with evidence); new shadow rows carrying the quote
  fields, with a sample of quote ages per sport. Budget must read GREEN; close GG-1230 and GG-1232 with the evidence; GG-1231 gets
  its alarm or a registered task. Confirm t4-mlb runs box HEAD and feeds the gate.
PART B - Enforce (~45 min)
  Read the LOG-ONLY file over the full game day: every would-halt by book and reason, and the "open_stake anomaly" W88.2 flagged. A
  would-halt a healthy book should not produce is a bug: fix it first. Then the enforce flip in its own PR, tests green; read back on
  the box that an order on a tripped book is refused and a missing state file halts. Close GG-1082 and GG-441 with the evidence.
Results: the PRs, the LOG-ONLY day's summary, the gap entries, budget_read before/after, a handoff.

END OF BLOCK 89.1. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 89.2 — Where the line itself is wrong: longshot bias and calibration of Kalshi's prices
**PROOF + DEPTH** · terminal 2

```
COMMON RULES - WAVE 89 (WHERE THE LINE IS WEAK) (read first; they bind this block)
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
- Decisions in force: DECISION_LOG through 2026-10-26 19:50 PT - incl. Wave 88 results (5 of 6 frozen models scored against the
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
- Three blocks run in parallel. File ownership: 89.1 = src/prediction_market_bot/c4_risk_engine/ (the enforce flip) + tests, the
  GG-441 / GG-1082 / GG-1230..1232 entries, and the silent-arm check if the red needs it; 89.2 = a new 12_EXPLORATORY/longshot_bias/;
  89.3 = a new 12_EXPLORATORY/unpriced_screen/ and SEATS/nfl.toml + SEATS/nba.toml (rows you move only). 89.2 and 89.3 may ADD to
  src/prediction_market_bot/quant/ (new functions with tests, no edits to existing ones).
  TO_MUSE.md is append-only: fetch + rebase right before pushing. The gap agent owns GG_BURNDOWN.md and GG_AGENT_STATE.md. Box access: ssh, or the box bridge
  (04_EXECUTION/BOX_TASKS/requests/*.toml naming an allowlisted task; results in 04_EXECUTION/BOX_TASKS/results/). The box pulls
  main on its own timer: before trusting a bridge result after a merge, read deploy_truth_read's box HEAD.
  SURFACE BUDGET: read the box's budget_read before installing anything. At the Wave 88 close it was RED on one silent arm (the
  MLB game-market shadow; W88.2 merged the fix, #336, awaiting an in-window row). Hard Rule 14: nothing new goes live until GREEN. Register every new component before it runs.
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W89_<n>.md (docs-only push).

WAVE 89.2 - WHERE THE LINE ITSELF IS WRONG: LONGSHOT BIAS AND CALIBRATION OF KALSHI'S SPORTS PRICES. Repo: eignacio1/prediction-market-bot.
PURPOSE: PROOF + DEPTH. Measures: Kalshi sports prices tested for calibration by price bucket, family, sport and time-to-start 0 -> n
families (with BH across all of them); market-level adjustments that survive, 0 -> n. Why now: W88.3 scored our frozen models against
the market on held-out seasons - NHL and NBA worse than it, MLB level - so no model-side edge exists yet. The other route to an edge
needs no model: the market's own price may be biased where retail money sits. The operator, 2026-10-16: "Beating Kalshi or
institutions is a tall task - beating buddy off his phone placing parlays, that's the first step." From his quant list (2026-10-22):
"Intraday Mean Reversion in Overreacted Markets" and "Micro-Liquidity Consolidations ... near boundary conditions (0.01 or 0.99)".
Premises to check: EXP031 (05_RESEARCH_EXPERIMENTS/EXP031_MARKET_EFFICIENCY_PREREGISTRATION_2026-09-30.md) pre-registered market-
efficiency tests and exp_output/EFFICIENCY_GRADIENT holds results: read both first; do not contradict or re-run a sealed test;
extend it. Kalshi's public API serves settled markets and candles; the shadow ledgers hold prices at T1/T2/T3 for every strike.
PERMISSIONS: per the common rules' ownership; public Kalshi market-data GETs; read-only box ledgers. NOT: any order, gate, model,
runner or pre-registration. A finding here is a CANDIDATE for a pre-registered market-anchored adjustment, not a trade.

PART A - Calibration of the price itself (~45 min)
  For settled Kalshi sports markets (NFL, NBA, NHL, MLB; game families, props, and any parlay or multi-leg family Kalshi lists),
  at fixed times before the start: bucket by price (1-5c, 5-10c, ... 95-99c), and compare the price with the share that settled YES,
  net of the k007 fee on the side you would take. Game-clustered intervals; BH across every family x bucket x time cell, stated
  family-wise. Separate thin from deep books (depth or spread where recorded). The quant bar applies (a simulated market with a
  known bias is recovered; a calibrated one is not flagged).
PART B - Overreaction after moves (~30 min)
  Where candles exist: after a large price move with no score change (pre-game: injury news windows; in-game where available),
  does the price revert over the next N minutes more than fees? Same clustering and correction. Label every result DESCRIPTIVE
  unless it survives BH.
Results: results_W89.md, the code, a handoff, and one operator line: which surviving cells, if any, deserve a pre-registration.

END OF BLOCK 89.2. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 89.3 — Which factors does the line not price? NFL and NBA
**DEPTH** · terminal 3

```
COMMON RULES - WAVE 89 (WHERE THE LINE IS WEAK) (read first; they bind this block)
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
- Decisions in force: DECISION_LOG through 2026-10-26 19:50 PT - incl. Wave 88 results (5 of 6 frozen models scored against the
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
- Three blocks run in parallel. File ownership: 89.1 = src/prediction_market_bot/c4_risk_engine/ (the enforce flip) + tests, the
  GG-441 / GG-1082 / GG-1230..1232 entries, and the silent-arm check if the red needs it; 89.2 = a new 12_EXPLORATORY/longshot_bias/;
  89.3 = a new 12_EXPLORATORY/unpriced_screen/ and SEATS/nfl.toml + SEATS/nba.toml (rows you move only). 89.2 and 89.3 may ADD to
  src/prediction_market_bot/quant/ (new functions with tests, no edits to existing ones).
  TO_MUSE.md is append-only: fetch + rebase right before pushing. The gap agent owns GG_BURNDOWN.md and GG_AGENT_STATE.md. Box access: ssh, or the box bridge
  (04_EXECUTION/BOX_TASKS/requests/*.toml naming an allowlisted task; results in 04_EXECUTION/BOX_TASKS/results/). The box pulls
  main on its own timer: before trusting a bridge result after a merge, read deploy_truth_read's box HEAD.
  SURFACE BUDGET: read the box's budget_read before installing anything. At the Wave 88 close it was RED on one silent arm (the
  MLB game-market shadow; W88.2 merged the fix, #336, awaiting an in-window row). Hard Rule 14: nothing new goes live until GREEN. Register every new component before it runs.
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W89_<n>.md (docs-only push).

WAVE 89.3 - DEPTH, MARKET-ANCHORED: WHICH FACTORS DOES THE LINE NOT PRICE? A SCREEN ACROSS NFL AND NBA. Repo: eignacio1/prediction-market-bot.
PURPOSE: DEPTH. Measures: D5(b) NFL and NBA factors with a measured "share priced by the line" 1 (F8) -> n; factors whose unpriced
part is big enough to clear the fee plus measured error, 0 -> n (named). The price now starts from the market's line (accepted
2026-10-21 20:28 PT); conviction = a reason the line does not already contain. W85.1: F8 (availability) is ~2/3 priced on spread and
adds nothing measurable from the line. W88.3: no frozen model beats the line. This block finds which built factors might.
Premises to check: SEATS/nfl.toml and SEATS/nba.toml list the factors and their stages (NFL 21, NBA 15); W77.2's method
(12_EXPLORATORY/nfl_engine/market_tests/closing_line.py: close = a + b0 x engine + b x term, b = share priced) is the template;
nflverse closes are free for NFL; for NBA use the Kalshi history W88.3 built (12_EXPLORATORY/market_history/).
PERMISSIONS: per the common rules' ownership. NOT: any live model, runner, ledger, gate or pre-registration; no factor weight or
threshold chosen from game outcomes.

PART A - The screen (~45 min)
  For every factor in SEATS/nfl.toml and SEATS/nba.toml that is built point-in-time: its share priced by the line (W77.2's
  regression, rolling origin, game-clustered intervals) and its unpriced part's size in probability terms per family. Rank them.
  BH across the screen. Each factor reports its stage and the granularity index's five parts as far as you get.
PART B - The top of the list, to a price (~35 min)
  For the top 1-3 factors by unpriced size: anchor + adjustment out of sample (the EXP-041 method, through
  src/prediction_market_bot/quant/), paired Brier vs the anchor, and how many strikes would clear fee + measured error. If none
  clears, say so plainly and say which factor classes the screen says are worth building next (that feeds the depth lane).
Results: results_W89.md, seat rows, a handoff, one operator line: pre-register one of these, or keep building.

END OF BLOCK 89.3. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### ➕ EXTRA TERMINALS 89.4-89.6 (operator 2026-10-26 21:02 PT: "Out of protocol request - give me another 3 terminals to run")
Six terminals run concurrently this wave. **Addendum for 89.1-89.3** (paste into each of the three original terminals):

```
ADDENDUM FROM THE OPERATOR (2026-10-26 21:02 PT) - read, then proceed as normal.
This wave runs SIX terminals concurrently, not three: 89.4 (an NFL game simulation in a new 12_EXPLORATORY/nfl_gamestate/ + the NFL
[[engine]] entry in ARCHITECTURE_COMPONENTS.toml), 89.5 (NBA PAM vs the points-prop line in 12_EXPLORATORY/nba_pam_mass_tier/ and new
files under qualitative_data/pam/nba/), and 89.6 (a small-fix gap sweep that closes class-C and observation gaps). Your block, its
ownership and its permissions are unchanged. Two things change: (1) never touch the files named above; 89.6 will not touch your
files or your gap entries; (2) more pushes are landing at once, so fetch + rebase right before EVERY push and PR merge, and if
src/prediction_market_bot/quant/ conflicts, keep both sides (89.2-89.5 may add to it; nobody edits existing functions).
```

### 89.4 — Depth + quant C1: one NFL game simulation that prices the whole board
**DEPTH** · terminal 4

```
COMMON RULES - WAVE 89, EXTRA TERMINALS 89.4-89.6 (operator, out of protocol: six terminals this wave) (read first; they bind this block)
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
- Decisions in force: DECISION_LOG through 2026-10-26 19:50 PT - incl. Wave 88 results (5 of 6 frozen models scored against the
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
- SIX blocks run in parallel this wave (operator 2026-10-26 21:02 PT: "Out of protocol request - give me another 3 terminals to
  run"). File ownership - never touch another block's files: 89.1 = c4_risk_engine/ (enforce flip) + the GG-441 / GG-1082 /
  GG-1230..1232 entries + the silent-arm check; 89.2 = 12_EXPLORATORY/longshot_bias/; 89.3 = 12_EXPLORATORY/unpriced_screen/ +
  SEATS/nfl.toml + SEATS/nba.toml; 89.4 = a new 12_EXPLORATORY/nfl_gamestate/ + the NFL [[engine]] entry in
  02_ARCHITECTURE_DESIGN/ARCHITECTURE_COMPONENTS.toml; 89.5 = 12_EXPLORATORY/nba_pam_mass_tier/ (W84.2's, continued) + new files
  under qualitative_data/pam/nba/; 89.6 = the gap log entries it closes and the small files those fixes need, never a file listed
  here. 89.2-89.5 may ADD to src/prediction_market_bot/quant/ (new functions with tests, no edits to existing ones): fetch and
  rebase before each push; on a conflict, keep both. Seat rows 89.4/89.5 would move go in their results file for 89.3 or the
  window to apply, never into SEATS/ directly.
  TO_MUSE.md is append-only: fetch + rebase right before pushing. The gap agent owns GG_BURNDOWN.md and GG_AGENT_STATE.md. Box access: ssh, or the box bridge
  (04_EXECUTION/BOX_TASKS/requests/*.toml naming an allowlisted task; results in 04_EXECUTION/BOX_TASKS/results/). The box pulls
  main on its own timer: before trusting a bridge result after a merge, read deploy_truth_read's box HEAD.
  SURFACE BUDGET: read the box's budget_read before installing anything. At the Wave 88 close it was RED on one silent arm (the
  MLB game-market shadow; W88.2 merged the fix, #336, awaiting an in-window row). Hard Rule 14: nothing new goes live until GREEN. Register every new component before it runs.
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W89_<n>.md (docs-only push).

WAVE 89.4 - DEPTH + QUANT C1: ONE NFL GAME SIMULATION THAT PRICES THE WHOLE BOARD CONSISTENTLY. Repo: eignacio1/prediction-market-bot.
PURPOSE: DEPTH. Measures: D4 NFL "data layer + engine scaffold" -> "whole board priced from one engine" (offline); families priced
from one joint distribution 0 -> n (moneyline, spread ladder, total ladder, team totals; props where the data allows). ADR-0073:
"One engine prices the whole board: a game simulation's joint distribution yields moneyline, spread, total, team totals, props and
parlays consistently - parlay correlations included." From the operator's quant list (2026-10-22): "Discrete-Time Markov Chains
(DTMC): Transition matrices, stationary distributions, and hitting times". W86.2 found the market's disagreement with us is mostly
about the CENTER, and NFL margins need key numbers (3, 7) that a normal curve cannot carry.
Premises to check: the NFL engine scaffold and data layer (02_ARCHITECTURE_DESIGN/ARCHITECTURE_COMPONENTS.toml [[engine]] NFL;
12_EXPLORATORY/nfl_engine/; nflverse play-by-play 2016+, free); the quant core's DTMC estimator (moved in by W87.1).
PERMISSIONS: per the common rules' ownership. NOT: any live model, runner, ledger, gate, registry cell or pre-registration;
nothing goes live (the box budget is RED, Hard Rule 14).

PART A - The chain (~45 min)
  States at drive or play level (down, distance bucket, field position bucket, score difference bucket, time bucket, possession);
  transitions estimated from nflverse play-by-play on earlier seasons only, with team strength entering point-in-time (the engine's
  rating layer) so two teams' chain differs. Simulate each game many times to a final score. The quant bar: the estimator recovers
  a known chain; the simulated league-wide score distribution reproduces key-number frequencies (3, 7, 10) on a held-out season.
PART B - The board from one simulation, against the market (~35 min)
  For a held-out season: moneyline, every spread and total strike, and team totals read off the SAME simulated joint distribution.
  Compare with nflverse closes (and the 2025-26 Kalshi candles where they exist) through src/prediction_market_bot/quant/: paired
  Brier per family vs the market, game-clustered intervals, and vs the frozen nfl_pregame_v1's normal curve. A simulation that
  matches the market's shape but not its center is the expected first result: say which.
Results: results_W89.md, the code, a handoff, proposed seat rows for the window. Stage per factor; D4 stage claimed only with evidence.

END OF BLOCK 89.4. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 89.5 — Depth, retail first: NBA player roles (PAM) against the points-prop line
**DEPTH** · terminal 5

```
COMMON RULES - WAVE 89, EXTRA TERMINALS 89.4-89.6 (operator, out of protocol: six terminals this wave) (read first; they bind this block)
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
- Decisions in force: DECISION_LOG through 2026-10-26 19:50 PT - incl. Wave 88 results (5 of 6 frozen models scored against the
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
- SIX blocks run in parallel this wave (operator 2026-10-26 21:02 PT: "Out of protocol request - give me another 3 terminals to
  run"). File ownership - never touch another block's files: 89.1 = c4_risk_engine/ (enforce flip) + the GG-441 / GG-1082 /
  GG-1230..1232 entries + the silent-arm check; 89.2 = 12_EXPLORATORY/longshot_bias/; 89.3 = 12_EXPLORATORY/unpriced_screen/ +
  SEATS/nfl.toml + SEATS/nba.toml; 89.4 = a new 12_EXPLORATORY/nfl_gamestate/ + the NFL [[engine]] entry in
  02_ARCHITECTURE_DESIGN/ARCHITECTURE_COMPONENTS.toml; 89.5 = 12_EXPLORATORY/nba_pam_mass_tier/ (W84.2's, continued) + new files
  under qualitative_data/pam/nba/; 89.6 = the gap log entries it closes and the small files those fixes need, never a file listed
  here. 89.2-89.5 may ADD to src/prediction_market_bot/quant/ (new functions with tests, no edits to existing ones): fetch and
  rebase before each push; on a conflict, keep both. Seat rows 89.4/89.5 would move go in their results file for 89.3 or the
  window to apply, never into SEATS/ directly.
  TO_MUSE.md is append-only: fetch + rebase right before pushing. The gap agent owns GG_BURNDOWN.md and GG_AGENT_STATE.md. Box access: ssh, or the box bridge
  (04_EXECUTION/BOX_TASKS/requests/*.toml naming an allowlisted task; results in 04_EXECUTION/BOX_TASKS/results/). The box pulls
  main on its own timer: before trusting a bridge result after a merge, read deploy_truth_read's box HEAD.
  SURFACE BUDGET: read the box's budget_read before installing anything. At the Wave 88 close it was RED on one silent arm (the
  MLB game-market shadow; W88.2 merged the fix, #336, awaiting an in-window row). Hard Rule 14: nothing new goes live until GREEN. Register every new component before it runs.
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W89_<n>.md (docs-only push).

WAVE 89.5 - DEPTH, RETAIL FIRST: NBA PLAYER ROLES (PAM) AGAINST THE POINTS-PROP LINE. Repo: eignacio1/prediction-market-bot.
PURPOSE: DEPTH. Measures: D5(b) NBA PAM factors applied 0 -> n (a tested path from the fact to a price, against the market); NBA
points props with settled actual points joined 0 -> n. The operator, 2026-10-16: "beating buddy off his phone placing parlays,
that's the first step" - player props are where retail money sits. W84.2 built the NBA PAM mass tier (~1,723 player-seasons,
stability interpreted; PRF-1 and PRF-4 the stable subset) but its cross was NOT RUN: n = 0, because the NBA points shadow rows carry
no actual points and the store had no 2026-27 games (GG-1064). The 2026-27 season has played a week since.
Premises to check: 12_EXPLORATORY/nba_pam_mass_tier/ and qualitative_data/pam/nba/ (W84.2's outputs); the NBA player-points shadow
ledgers on the box (KXNBAPTS strikes and prices at each evaluation); free box scores (NBA.com stats endpoints or the source the
bot's NBA store already uses). GG-1064 (charter rule 2 vs block text on reading PREGAME_SHADOW) - read it and follow its resolution.
PERMISSIONS: per the common rules' ownership; read-only box ledgers; free public box-score GETs. NOT: the NBA player-points models
(v1, EXP-040), their runners, rows, registry cells or pre-registrations; no live capture is installed (the box budget is RED);
no PAM threshold chosen from outcomes; SEATS/nba.toml is 89.3's: put your proposed rows in results.

PART A - The join (~35 min)
  2026-27 actual points per player-game from a free box-score source, point-in-time joined to every settled KXNBAPTS strike the
  shadow ledgers priced (the market's price at the row's time, the strike, the result). Report coverage and every unmatched name.
PART B - PAM to the price (~45 min)
  For PRF-1 and PRF-4 (the stable subset) and any FREE-row modifier with n to support it: does the player's PAM role explain where
  the points-prop PRICE is wrong - the market-anchored question (does the line misprice players of this role?), not whether the
  role predicts points. Anchor + role adjustment, out of sample by date, through src/prediction_market_bot/quant/, game-clustered
  intervals, BH across roles. Small n is expected one week in: say what n would be needed (power) and when the season reaches it.
Results: results_W89.md, the join, a handoff, proposed seat rows. Stage per factor.

END OF BLOCK 89.5. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 89.6 — The small-fix gap sweep
**PLUMBING** · terminal 6

```
COMMON RULES - WAVE 89, EXTRA TERMINALS 89.4-89.6 (operator, out of protocol: six terminals this wave) (read first; they bind this block)
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
- Decisions in force: DECISION_LOG through 2026-10-26 19:50 PT - incl. Wave 88 results (5 of 6 frozen models scored against the
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
- SIX blocks run in parallel this wave (operator 2026-10-26 21:02 PT: "Out of protocol request - give me another 3 terminals to
  run"). File ownership - never touch another block's files: 89.1 = c4_risk_engine/ (enforce flip) + the GG-441 / GG-1082 /
  GG-1230..1232 entries + the silent-arm check; 89.2 = 12_EXPLORATORY/longshot_bias/; 89.3 = 12_EXPLORATORY/unpriced_screen/ +
  SEATS/nfl.toml + SEATS/nba.toml; 89.4 = a new 12_EXPLORATORY/nfl_gamestate/ + the NFL [[engine]] entry in
  02_ARCHITECTURE_DESIGN/ARCHITECTURE_COMPONENTS.toml; 89.5 = 12_EXPLORATORY/nba_pam_mass_tier/ (W84.2's, continued) + new files
  under qualitative_data/pam/nba/; 89.6 = the gap log entries it closes and the small files those fixes need, never a file listed
  here. 89.2-89.5 may ADD to src/prediction_market_bot/quant/ (new functions with tests, no edits to existing ones): fetch and
  rebase before each push; on a conflict, keep both. Seat rows 89.4/89.5 would move go in their results file for 89.3 or the
  window to apply, never into SEATS/ directly.
  TO_MUSE.md is append-only: fetch + rebase right before pushing. The gap agent owns GG_BURNDOWN.md and GG_AGENT_STATE.md. Box access: ssh, or the box bridge
  (04_EXECUTION/BOX_TASKS/requests/*.toml naming an allowlisted task; results in 04_EXECUTION/BOX_TASKS/results/). The box pulls
  main on its own timer: before trusting a bridge result after a merge, read deploy_truth_read's box HEAD.
  SURFACE BUDGET: read the box's budget_read before installing anything. At the Wave 88 close it was RED on one silent arm (the
  MLB game-market shadow; W88.2 merged the fix, #336, awaiting an in-window row). Hard Rule 14: nothing new goes live until GREEN. Register every new component before it runs.
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W89_<n>.md (docs-only push).

WAVE 89.6 - THE SMALL-FIX SWEEP (GS-1 + GS-2, NEVER RUN): CLOSE CLASS-C GAPS WITH EVIDENCE. Repo: eignacio1/prediction-market-bot.
PURPOSE: PLUMBING. Measure: OPEN gaps 211 (2026-10-26 21:05 PT, `grep -cE "^\*\*Status:\*\* OPEN\b" 03_DECISIONS/GOVERNANCE_GAP_LOG.md`)
-> as low as the 90 minutes allow. The operator, 2026-10-21 19:28 PT: "The 30 small fixes and 25 small process one-offs- there has to
be an easy way to sweep those. I'm fine with a continual list knowing the scale of the project but please 200+ gaps is fucking
ludicrous". GS-3 ran (210 -> 199); GS-1 and GS-2 (class C, small fixes) were never run; the count has grown back to 211.
The rules of the gap sweep in ACTIVE_QUEUE.md § "GAP SWEEP" (GS common rules) apply, with these changes: one terminal takes class C at
ANY number (C = closes with a code or doc change plus a test in about 10-20 minutes); also take class O (observations: a measured fact
with nothing to fix) and re-file them WATCH ITEM per the operator's observation rule (accepted 2026-10-21); never touch class E
(engine data gaps); never touch GG-441, GG-1082, GG-1230..1232 (89.1's) or any file the common rules give 89.1-89.5.
PERMISSIONS: per the common rules' ownership; code fixes by PR with CI green, batched 3-5 per PR, each with a test; doc-only closures
docs-only. NOT: any order, stake, kelly_fraction, ledger row, live model, runner, registry cell, pre-registration, existing cron line
or .claude/settings*.json; a gap needing one of those is not a sweep item: skip it.

THE SWEEP (~90 min, batches)
  Classify the OPEN list first (C / P / O / E) into 03_DECISIONS/GG_BURNDOWN.md § "Sweep lists" (docs-only push). Then work C
  top-down and O as you meet them. Close a gap only on a real fix or evidence it is already fixed or moot (commit, file and line,
  or a box read). RESOLVED / CLOSED-AS-ARTIFACT entries move verbatim to GOVERNANCE_GAP_LOG_ARCHIVE.md. Fetch + rebase right before
  every push to the gap log; edit only the entries you work. After every batch: CLAUDE.md Step 3's checks (the OPEN grep, headers =
  status lines, the id-uniqueness script) and one row in GG_BURNDOWN.md § "Sweep tally".
Results: Status | PRs + CI | OPEN before -> after | ids closed | ids re-filed WATCH ITEM | ids skipped with the reason; a handoff
(11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W89_6.md).

END OF BLOCK 89.6. If you cannot see this line, the prompt reached you truncated: stop and report it.
```
