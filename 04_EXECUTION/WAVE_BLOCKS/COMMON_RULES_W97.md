# Wave 97 common rules

Every Wave 97 block tells the terminal to read this file first. Text below is the rules verbatim.

```
COMMON RULES - WAVE 97 (THE PICKS SHEET; THE NBA ENGINE ON v3; THE FROZEN EVIDENCE, RESUMABLE) (read first; they bind this block)
- THIS WAVE: three blocks drawn from the top of the ROLLING BACKLOG (04_EXECUTION/ROLLING_BACKLOG.json, maintained by the strategic
  window only): 97.1 engine lane = B-001 + B-009, 97.2 proof lane = B-002 + B-011, 97.3 flex lane = B-026 + B-006 + B-007, 97.4 engine lane (second sport,
  operator 2026-10-30 11:42 PT: "send 4 of the most important blocks ready for this run") = B-012. Do not edit
  ROLLING_BACKLOG.json; report each ticket's state in your handoff.
- SIZE (operator 2026-10-30 08:38 PT, supersedes the 10-07 MEDIUM ceiling for these waves): THREE parts, about 130 minutes. Part C is a
  task you can switch to whenever an earlier part waits on the box (a game night, a long fetch, a deploy). Push after every part.
- After EACH part: push, and update this block's row in 04_EXECUTION/ACTIVE_QUEUE.md (NOW table: Status + one line) with a docs-only
  push. Stop at a pushed boundary (context ~60%, a blocker, or the time) and write the handoff. Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs, and ONLY on a CI result you
  have read as green (W80.1 merged #291 red and broke main). After each merge, read the box's deploy (deploy_truth_read, or
  logs/vps_deploy.log on the box: the box deploys itself on a timer; the GitHub "Deploy to VPS" job is manual-only since W67.3, GG-1462)
  and record the t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-30 10:05 PT - incl. Wave 96 results (96.1: NBA engine v3 (availability +
  lineups) beats v2 held-out on the spread (Brier -0.0079) and team totals, n 2,271 games; EXP-044c NOT frozen - it needs a live_v3
  runner; the engine's v1 / v2 arms still have no forward row (no NBA game had tipped since the install; GG-1450 open); the player-points
  layer merged, its apparent gain was a post-game-roster leak, removed - not applied, EXP-044d not frozen. 96.2: settlement cache
  complete, 0 of 13 frozen cells classified - a full-archive run does not fit the 900 s box-task limit (GG-1520) and the NFL regen's
  pinned schedules parquet is missing (GG-1521); Part C (B-011) not run. 96.3: the rolling backlog is LIVE on /visual (read back); demo
  balance and exposure now logged on every refused order, no refusal since (GG-1481); Part C (B-006) not run), THE PICKS SHEET
  (operator 2026-10-30 09:59 PT: "give me just the conviction picks - again keep it simple. Give me just one side whats the bot betting
  and why"; the window could not, because no read shows the bot's per-game picks - backlog B-026), STRETCHED BLOCKS (operator 08:38 PT),
  THE ROLLING BACKLOG (operator 2026-10-30 08:26 PT; 04_EXECUTION/ROLLING_BACKLOG.json; on the Visual
  Dashboard), Wave 94 results (EXP-044 / 044b / 045 frozen; NFL D5(a) 8/8; resting fills picked off, taking at the quote is not; no
  model earns a Bayesian skill weight; PROOF_CALENDAR.md), the box GREEN at the Wave 94
  close (2026-10-29 05:26Z: 83 live, healthcheck HEALTHY, no silent arm, box HEAD 8f1f9239), Wave 93 results (NBA engine scaffold,
  availability / travel / officials interpreted, NFL board v2 from the line; GG-1420, GG-1390), THE LANE RULE (operator 2026-10-27 22:24-22:38 PT), Wave 92 results (archive covers four sports;
  exact Kalshi fees in quant/money.py; EXP-043 frozen; NBA lineups interpreted on totals), Wave 91 results (91.1: EXP-042 FROZEN - 89.2's 11 ride
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
- Four blocks run in parallel. The operator's last wave before the weekend: finish inside the block and leave nothing half-installed.
  File ownership: 97.4 = a new src/prediction_market_bot/nhl_engine/ + tests, the NHL [[engine]] entry, the NHL seat rows it moves, EXP-046,
  12_EXPLORATORY/nhl_engine/ (97.1 owns the NBA [[engine]] entry: edit only your own, rebase before push); 97.1 = NEW modules in src/prediction_market_bot/nba_engine/ (v1 / v2 / v3 stay as
  merged), a live_v3 runner + its cron line / install task + RUNTIME_REGISTRY entry, EXP-044c, 12_EXPLORATORY/nba_engine_v3/ additions,
  GG-1450; 97.2 = 12_EXPLORATORY/frozen_evidence_check/ and its box tasks, the NFL regen inputs, GG-1520 / 1521, a new
  12_EXPLORATORY/forward_entry_cost/; 97.3 = a new picks builder (src/prediction_market_bot/pregame_shadow/ addition or scripts/) + its
  cron line / install task + RUNTIME_REGISTRY entry, scripts/build_visual_dashboard_html.py and 04_EXECUTION/visual_dashboard/ (the
  picks panel only), the silent-arm specs and MLB arms' off-season posture, memory measurements, 12_EXPLORATORY/picks_sheet_w97/. Data:
  the shadow arms' decision rows on the box, the NBA engine's rows, the forward-test report, the price archive. Muse's cards:
  github.com/eignacio1/sports-intel-archive (READ ONLY). Everyone may ADD to src/prediction_market_bot/quant/ (new functions with tests,
  no edits to existing ones); fetch + rebase before every push.
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
- Report back: Status (DONE / PARTIAL / BLOCKED) | your backlog ticket (B-NNN) and its state | branch @ SHA | PR + CI | one-line result | MEASURE MOVED: <measure>
  <before> -> <after> (source) or none | stage reached per factor | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W97_<n>.md (docs-only push).

```
