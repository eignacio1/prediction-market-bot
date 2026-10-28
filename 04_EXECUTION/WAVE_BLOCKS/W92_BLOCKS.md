# Wave 92 — paste blocks (the winter archive, exact fees, the NBA engine)

Copy each block as one fenced paste. The wave's table, results and status live in `04_EXECUTION/ACTIVE_QUEUE.md` § "NOW — Wave 92".
Written 2026-10-27 ~22:00 PT at the Wave 91 close. All three blocks run in parallel. No Muse paste (operator): Muse runs ten scheduled
cycles a day from TO_MUSE.md.

### 92.1 — The winter archive: NBA and NHL prices captured for real, and a surface budget that tells the truth
**BREADTH + PLUMBING** · terminal 1

```
COMMON RULES - WAVE 92 (THE WINTER ARCHIVE, EXACT FEES, THE NBA ENGINE) (read first; they bind this block)
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
- Decisions in force: DECISION_LOG through 2026-10-27 21:50 PT - incl. Wave 91 results (91.1: EXP-042 FROZEN - 89.2's 11 ride
  cells, forward test only; the backward test VOID, and Muse's R-069 showed it was never possible: no Kalshi sports series was listed
  before August 2026; forward looks: NFL cell ~2026-12-21, MLB cells April-June 2027. 91.2: ride.py + ride_cells.toml built, router stub
  replaced (replay RIDE 3,838 -> 0, every cell IN_SAMPLE); the ladder ride measured: a strike off its own ladder does move toward it
  (+1.3c in 1 h, gross) but net of cost +0.7c [-0.2c, +1.7c], not distinguishable from 0; 2 cells HELD_OUT on one time split
  (KXMLBTOTAL T0-2h tight, 2-5c and 5c+). 91.3 PARTIAL: #347 and #354 merged; 6 NBA/NHL archive cron lines registered but NOT
  installed on the box; the surface budget counted them live and still read GREEN), ADR-0076 ACCEPTED (operator 2026-10-27 17:30 PT:
  G6 per (book, sport), a cell WINS at its judged n; section 4 blanks stay blank until a positive Kelly is proposed), RIDE ONLY ON
  OUT-OF-SAMPLE CELLS (operator 17:26 PT: HELD_OUT or FORWARD_PASSED), NO POLYMARKET BUILD WORK (operator 17:31 PT: "we're not building
  shit for polymarket yet"), Muse's R-068: Kalshi's fee schedule verbatim (taker 0.07 x C x P x (1-P), multiplier 1, rounded UP to a
  centicent, since 2026-07-07; maker 0.0175 curve on listed series; MLB spread / total / team-total / props and MLB game at multiplier
  0.5 PRE-LIVE, 1 live), Muse on ten daily scheduled runs (operator 2026-10-27), Wave 90 results (90.1: PR #349 and #352 merged; the hold-out
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
- Three blocks run in parallel. File ownership: 92.1 = a new scripts/archive_cron_install.py + tests, ADDED entries in scripts/box_tasks.py's
  allowlist (no edits to existing entries), new archiver cron lines + their RUNTIME_REGISTRY.toml entries, scripts/runtime_registry.py's
  budget logic + tests, a new 12_EXPLORATORY/ride_scan_nba_nhl/, exp_output/KALSHI_HISTORY/nba/ and /nhl/, GG-1250 / GG-1330; 92.2 = NEW
  functions in src/prediction_market_bot/quant/money.py (existing ones stay as they are) + a new fee table data file + tests,
  src/prediction_market_bot/decision_trees/ride_cells.toml, a new EXP-043 pre-registration, a new 12_EXPLORATORY/fees_exact/; 92.3 = the
  NBA engine's new factor module(s), the B7 row of 02_ARCHITECTURE_DESIGN/SEATS/nba.toml, 02_ARCHITECTURE_DESIGN/NBA_ENGINE/ additions, a
  new 12_EXPLORATORY/nba_lineups/. Data: the price archive (exp_output/PRICE_ARCHIVE/, MLB + NFL today), Kalshi's public history via
  12_EXPLORATORY/market_history/, the NBA event store (02_ARCHITECTURE_DESIGN/NBA_ENGINE/event_store_manifest.json). Muse's cards are in
  github.com/eignacio1/sports-intel-archive (READ ONLY; never write to it). Everyone may ADD to src/prediction_market_bot/quant/ (new
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W92_<n>.md (docs-only push).

WAVE 92.1 - THE WINTER ARCHIVE: NBA AND NHL PRICES CAPTURED FOR REAL, AND A SURFACE BUDGET THAT TELLS THE TRUTH. Repo: eignacio1/prediction-market-bot.
PURPOSE: BREADTH + PLUMBING. Measures: sports in the price archive 2 -> 4 (read back as rows on the box, not as merged lines); NBA / NHL
families archived 0 -> n (game, spread, total, team total); surface budget: registered-but-not-installed entries counted as live 6 -> 0.
Why: every ride cell found so far is MLB, and MLB is done until April. Forward evidence this winter has to come from NBA and NHL, and
neither has a single archived price. 91.3 merged six NBA / NHL archive lines (#354), but they are not installed: deploy does not touch
the crontab, the terminal's ssh append was refused, and it handed the install to the operator as a decision. It is plumbing, not his
call. The box's 04:33Z read shows the real gap twice over: "6 mirrored-but-not-installed", counted in "83 live components", with the
budget still GREEN.
Premises to check: past cron installs on the box went through allowlisted bridge tasks with their own installer scripts
(scripts/thin_capture_install.py, scripts/source_capture_install.py: backup, additive install, readback, uninstall) - read them and copy
the pattern, do not invent a new one. The six lines are in deploy/cron.conf and RUNTIME_REGISTRY.toml (KXNBAGAME, KXNHLGAME only).
PERMISSIONS: per the common rules' ownership; NEW cron lines only (never edit or remove an existing line); public unauthenticated
Kalshi market-data GETs, paced. NOT: any order, gate, model, runner, ledger, registry cell or pre-registration; 92.2's or 92.3's files.

PART A - Install route, then the lines (~45 min)
  1. scripts/archive_cron_install.py with install / readback / uninstall, on the thin_capture / source_capture pattern: back up the
     crontab first, append only the archiver lines RUNTIME_REGISTRY.toml names as live and the crontab lacks, idempotent, never touch any
     other line. Add archive_cron_install, archive_cron_readback and archive_cron_uninstall to the bridge allowlist. Tests: idempotent
     second run; a foreign line is never modified; a missing backup aborts.
  2. Add the NBA and NHL spread, total and team-total series (list them from Kalshi's public API, never assume) as new lines on the same
     schedule pattern; measure one run's rows, bytes and duration per series and project a month's disk use against the box's free
     space; stay within the rate limit 91.1 hit (GG-1341: about 4 requests a second combined with 429s) - state the pacing.
  3. Merge on green CI, then request the install through the bridge and read back: every new line on the crontab, first rows per
     series in exp_output/PRICE_ARCHIVE/, no 429 storm, the staleness alarm wired. Resolve GG-1250 / GG-1330 for what is captured.
PART B - The budget tells the truth (~25 min)
  scripts/runtime_registry.py: a registry entry marked live with nothing installed on the box must not count as live and must turn the
  SURFACE BUDGET RED (Hard Rule 14 reads that budget). Tests on a fixture registry. Pattern sweep (Hard Rule 13): every other place that
  counts registry entries as live without checking the box (distance, dashboard, healthcheck) - fix or register each. Read back on the box
  after the merge: the budget line and the live count.
Results: the installer + tests + allowlist entries, the new lines read back with rows, the budget fix read back, a handoff (vision_pillar
BREADTH + PLUMBING; surface_delta = lines actually installed). If time remains after both parts (and only then): 89.2's calibration scan
on NBA / NHL candles as discovery (91.3's old Part B), labelled IN_SAMPLE.

END OF BLOCK 92.1. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 92.2 — Exact fees, and the ladder ride put on a forward clock
**PROOF** · terminal 2

```
COMMON RULES - WAVE 92 (THE WINTER ARCHIVE, EXACT FEES, THE NBA ENGINE) (read first; they bind this block)
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
- Decisions in force: DECISION_LOG through 2026-10-27 21:50 PT - incl. Wave 91 results (91.1: EXP-042 FROZEN - 89.2's 11 ride
  cells, forward test only; the backward test VOID, and Muse's R-069 showed it was never possible: no Kalshi sports series was listed
  before August 2026; forward looks: NFL cell ~2026-12-21, MLB cells April-June 2027. 91.2: ride.py + ride_cells.toml built, router stub
  replaced (replay RIDE 3,838 -> 0, every cell IN_SAMPLE); the ladder ride measured: a strike off its own ladder does move toward it
  (+1.3c in 1 h, gross) but net of cost +0.7c [-0.2c, +1.7c], not distinguishable from 0; 2 cells HELD_OUT on one time split
  (KXMLBTOTAL T0-2h tight, 2-5c and 5c+). 91.3 PARTIAL: #347 and #354 merged; 6 NBA/NHL archive cron lines registered but NOT
  installed on the box; the surface budget counted them live and still read GREEN), ADR-0076 ACCEPTED (operator 2026-10-27 17:30 PT:
  G6 per (book, sport), a cell WINS at its judged n; section 4 blanks stay blank until a positive Kelly is proposed), RIDE ONLY ON
  OUT-OF-SAMPLE CELLS (operator 17:26 PT: HELD_OUT or FORWARD_PASSED), NO POLYMARKET BUILD WORK (operator 17:31 PT: "we're not building
  shit for polymarket yet"), Muse's R-068: Kalshi's fee schedule verbatim (taker 0.07 x C x P x (1-P), multiplier 1, rounded UP to a
  centicent, since 2026-07-07; maker 0.0175 curve on listed series; MLB spread / total / team-total / props and MLB game at multiplier
  0.5 PRE-LIVE, 1 live), Muse on ten daily scheduled runs (operator 2026-10-27), Wave 90 results (90.1: PR #349 and #352 merged; the hold-out
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
- Three blocks run in parallel. File ownership: 92.1 = a new scripts/archive_cron_install.py + tests, ADDED entries in scripts/box_tasks.py's
  allowlist (no edits to existing entries), new archiver cron lines + their RUNTIME_REGISTRY.toml entries, scripts/runtime_registry.py's
  budget logic + tests, a new 12_EXPLORATORY/ride_scan_nba_nhl/, exp_output/KALSHI_HISTORY/nba/ and /nhl/, GG-1250 / GG-1330; 92.2 = NEW
  functions in src/prediction_market_bot/quant/money.py (existing ones stay as they are) + a new fee table data file + tests,
  src/prediction_market_bot/decision_trees/ride_cells.toml, a new EXP-043 pre-registration, a new 12_EXPLORATORY/fees_exact/; 92.3 = the
  NBA engine's new factor module(s), the B7 row of 02_ARCHITECTURE_DESIGN/SEATS/nba.toml, 02_ARCHITECTURE_DESIGN/NBA_ENGINE/ additions, a
  new 12_EXPLORATORY/nba_lineups/. Data: the price archive (exp_output/PRICE_ARCHIVE/, MLB + NFL today), Kalshi's public history via
  12_EXPLORATORY/market_history/, the NBA event store (02_ARCHITECTURE_DESIGN/NBA_ENGINE/event_store_manifest.json). Muse's cards are in
  github.com/eignacio1/sports-intel-archive (READ ONLY; never write to it). Everyone may ADD to src/prediction_market_bot/quant/ (new
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W92_<n>.md (docs-only push).

WAVE 92.2 - EXACT FEES, AND THE LADDER RIDE PUT ON A FORWARD CLOCK. Repo: eignacio1/prediction-market-bot.
PURPOSE: PROOF (+ quant). Measures: fee definitions matching Kalshi's published schedule 0 -> 1 (with every reported net figure
re-checked); ride cells HELD_OUT in ride_cells.toml 0 -> 2; ride hypotheses pre-registered for a forward look 11 (EXP-042) -> 11 + the
ladder ride (EXP-043), with at least one look that can fall this winter.
Why: every net-of-cost number the bot has reported uses fee k007 = 0.07 x p x (1 - p). Muse's R-068 (archive
sources/kalshi-fees/, read it) quotes Kalshi's schedule: the same taker formula, rounded UP to a centicent; a maker fee of 0.0175 x
p x (1 - p) on listed series; and for MLB spread, total, team-total and props (and MLB game), a multiplier of 0.5 BEFORE the game goes
live. The MLB pre-game nets in 89.2, 90.3 and 91.2 therefore charge twice the real taker fee. The ladder ride (91.2) is the one ride idea
with a mechanism we can see (the strike moves toward the ladder, +1.3c in 1 h), but net of cost it is +0.7c [-0.2c, +1.7c] over the whole
sample, and its two HELD_OUT cells are MLB, which cannot be judged before April.
Premises to check: money.py's fee_k007 and its callers (grep every caller first, Hard Rule 13); Muse's three fee cards (they quote a
PDF effective 2026-07-07 and the live web table); EXP-041 and EXP-042 both froze "k007" - they are frozen artifacts and stay as written.
PERMISSIONS: per the common rules' ownership; a NEW pre-registration (standing authorization 2026-10-08). NOT: editing fee_k007 or any
existing function, EXP-041, EXP-042, any order, gate, model, runner, ledger or registry cell; wiring anything.

PART A - Fees as Kalshi publishes them (~40 min)
  NEW functions in money.py: fee(series, price, contracts, side = taker | maker, phase = prelive | live) driven by a fee-table DATA file
  built from Muse's cards (series -> taker / maker multiplier, prelive / live), rounding up to a centicent per order. Known-answer tests
  copied from the schedule's own formula and examples. Then a table: every published net figure that used k007 (89.2's 11 cells, 90.3's
  momentum grid headline, 91.2's ladder whole-sample and its 2 HELD_OUT cells, distance E2 if it charges a fee) recomputed with the exact
  fee - old, new, difference. Do not re-select any cell. If a frozen pre-registration's fee differs from the real one, say by how much
  and which direction, and give one operator line with your recommendation (k007 overstates MLB pre-game fees, so it is conservative).
PART B - The ladder ride on a forward clock (~40 min)
  1. ride_cells.toml: add 91.2's two KXMLBTOTAL T0-2h tight LADDER cells with status HELD_OUT and their measured net and interval (from
     12_EXPLORATORY/ride_ladder/), through a PR; ride.py's tests still pass.
  2. EXP-043, frozen before any new row is read: (a) the two HELD_OUT cells, forward, scored from the price archive (look dates in the
     MLB season); (b) the ladder trigger as a POOLED hypothesis across sports and families (91.2's definition exactly: leave-one-out
     normal fit on a ladder of >= 4 strikes, trigger when the ladder price beats the quote net of cost), scored forward on NFL rows now
     and on NBA / NHL rows from the date 92.1's archive lines are installed, with the exact fee from Part A; judged n from 91.2's variance
     at the effect it measured (state power and alpha); the pass rule, the modal outcome, and the earliest look date. If no look can fall
     before 2027, say so plainly.
Results: the fee functions + data file + tests, results_W92_2.md (the old / new fee table), the ride table PR, EXP-043 frozen (hash), a
handoff, and the operator line on the frozen fees.

END OF BLOCK 92.2. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 92.3 — The NBA engine, depth lane: lineups and on/off, point-in-time
**DEPTH** · terminal 3

```
COMMON RULES - WAVE 92 (THE WINTER ARCHIVE, EXACT FEES, THE NBA ENGINE) (read first; they bind this block)
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
- Decisions in force: DECISION_LOG through 2026-10-27 21:50 PT - incl. Wave 91 results (91.1: EXP-042 FROZEN - 89.2's 11 ride
  cells, forward test only; the backward test VOID, and Muse's R-069 showed it was never possible: no Kalshi sports series was listed
  before August 2026; forward looks: NFL cell ~2026-12-21, MLB cells April-June 2027. 91.2: ride.py + ride_cells.toml built, router stub
  replaced (replay RIDE 3,838 -> 0, every cell IN_SAMPLE); the ladder ride measured: a strike off its own ladder does move toward it
  (+1.3c in 1 h, gross) but net of cost +0.7c [-0.2c, +1.7c], not distinguishable from 0; 2 cells HELD_OUT on one time split
  (KXMLBTOTAL T0-2h tight, 2-5c and 5c+). 91.3 PARTIAL: #347 and #354 merged; 6 NBA/NHL archive cron lines registered but NOT
  installed on the box; the surface budget counted them live and still read GREEN), ADR-0076 ACCEPTED (operator 2026-10-27 17:30 PT:
  G6 per (book, sport), a cell WINS at its judged n; section 4 blanks stay blank until a positive Kelly is proposed), RIDE ONLY ON
  OUT-OF-SAMPLE CELLS (operator 17:26 PT: HELD_OUT or FORWARD_PASSED), NO POLYMARKET BUILD WORK (operator 17:31 PT: "we're not building
  shit for polymarket yet"), Muse's R-068: Kalshi's fee schedule verbatim (taker 0.07 x C x P x (1-P), multiplier 1, rounded UP to a
  centicent, since 2026-07-07; maker 0.0175 curve on listed series; MLB spread / total / team-total / props and MLB game at multiplier
  0.5 PRE-LIVE, 1 live), Muse on ten daily scheduled runs (operator 2026-10-27), Wave 90 results (90.1: PR #349 and #352 merged; the hold-out
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
- Three blocks run in parallel. File ownership: 92.1 = a new scripts/archive_cron_install.py + tests, ADDED entries in scripts/box_tasks.py's
  allowlist (no edits to existing entries), new archiver cron lines + their RUNTIME_REGISTRY.toml entries, scripts/runtime_registry.py's
  budget logic + tests, a new 12_EXPLORATORY/ride_scan_nba_nhl/, exp_output/KALSHI_HISTORY/nba/ and /nhl/, GG-1250 / GG-1330; 92.2 = NEW
  functions in src/prediction_market_bot/quant/money.py (existing ones stay as they are) + a new fee table data file + tests,
  src/prediction_market_bot/decision_trees/ride_cells.toml, a new EXP-043 pre-registration, a new 12_EXPLORATORY/fees_exact/; 92.3 = the
  NBA engine's new factor module(s), the B7 row of 02_ARCHITECTURE_DESIGN/SEATS/nba.toml, 02_ARCHITECTURE_DESIGN/NBA_ENGINE/ additions, a
  new 12_EXPLORATORY/nba_lineups/. Data: the price archive (exp_output/PRICE_ARCHIVE/, MLB + NFL today), Kalshi's public history via
  12_EXPLORATORY/market_history/, the NBA event store (02_ARCHITECTURE_DESIGN/NBA_ENGINE/event_store_manifest.json). Muse's cards are in
  github.com/eignacio1/sports-intel-archive (READ ONLY; never write to it). Everyone may ADD to src/prediction_market_bot/quant/ (new
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W92_<n>.md (docs-only push).

WAVE 92.3 - THE NBA ENGINE, DEPTH LANE: LINEUPS AND ON/OFF, BUILT POINT-IN-TIME FROM THE PLAY-BY-PLAY. Repo: eignacio1/prediction-market-bot.
PURPOSE: DEPTH. Measures: D5(b) NBA factor B7 (lineup / on-off / matchup) none -> interpreted (applied only with a market test);
D4 NBA "data layer" -> first factor class built point-in-time from event-level data; D5(b) NBA aggregated / interpreted / applied
2 / 6 / 5 of 15 -> n.
ADR-0073 (operator 2026-10-13): one deep engine per sport, built from the finest event-level data (NBA: possessions), every factor class
built once, point-in-time; "NFL first, as the template; NBA next". Depth has a continuous lane in every wave until each live sport has its
engine; Waves 89-91 spent it on riding the market. NBA's seat (02_ARCHITECTURE_DESIGN/SEATS/nba.toml) has B7 "Lineup / on-off, play-type,
matchup" at stage none, while B10 (lineup cross) and B11 (absorber play-type) are interpreted and need it underneath.
Premises to check: the NBA event store holds play-by-play 2016 -> 2027 (sportsdataverse nba_stats pbp, 49 columns; manifest
02_ARCHITECTURE_DESIGN/NBA_ENGINE/event_store_manifest.json) - confirm it carries substitutions and the players on the floor, or what is
needed to reconstruct them; INDEX_ENTRY_LINEUP.md and FACTORS_FIRST_READ.md in that folder; Muse's R-046 matchup pairs (2024-25,
2025-26) in the archive, REPORTED only. Kalshi NBA markets exist only from 2026-10-01 (Muse R-069), so any market test is this season.
PERMISSIONS: per the common rules' ownership. NOT: any live model, runner, shadow arm, pre-registration, order, gate, ledger or registry
cell; no new running component.

PART A - The lineup layer (~45 min)
  From the play-by-play, reconstruct lineup stints (the five on the floor for each team, possessions, points for and against), validated
  against box-score minutes on a sample of games (state the match rate; stints that cannot be reconstructed are dropped and counted).
  From the stints, point-in-time as of each game (strictly before tip): each team's expected lineup strength given who is available
  (rotation-weighted net rating with shrinkage to the team mean - state the prior), and the on/off swing of each rotation player.
  Known-answer test: a simulated league with known lineup effects is recovered. Leakage test: nothing from the game being predicted.
PART B - Interpreted, then against the market where it can be (~35 min)
  Interpreted: on held-out seasons (train on earlier seasons, score 2024-25 and 2025-26), does the lineup layer predict game margin and
  total beyond what B1 (team form) and B9 (pace) already carry? Paired, game-clustered, with intervals. Applied, descriptive only: on this
  season's Kalshi NBA game / spread / total markets (from 2026-10-01; thin), does it disagree with the price in a direction that settled?
  Report n and say plainly that the market test is underpowered if it is. Update B7's row in nba.toml with the stage reached and the five
  granularity-index parts.
Results: the module + tests, 12_EXPLORATORY/nba_lineups/results_W92_3.md, the seat row, a handoff (stage reached per factor).

END OF BLOCK 92.3. If you cannot see this line, the prompt reached you truncated: stop and report it.
```
