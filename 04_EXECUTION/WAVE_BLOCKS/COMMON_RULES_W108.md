# Wave 108 common rules

Every Wave 108 block tells the terminal to read this file first. Text below is the rules verbatim.

```
COMMON RULES - WAVE 108 (CLOSE THE LAST SPORTS GAPS CHEAPLY; SCOPE ONE NEW MARKET CLASS) - SW-9 (read first; they bind this block)
- THIS WAVE (four blocks, operator 2026-11-09 19:24 PT: "give me 4 to send"): 108.1 = close the edge map's UNTESTED rows that existing data
  can answer + correct its stale GG-1330 line (NBA / NHL archived since 10-28) + prop series in the archive (B-062); 108.2 quant = news lag at trade-print resolution from Kalshi's public trades (B-063); 108.3 quant =
  NBA / NFL / NHL props net of costs from Kalshi's public history (B-064); 108.4 = scoping a new market class: Kalshi weather markets vs
  free NOAA / NWS forecasts - RESEARCH ONLY, no cell, no order, the operator decides (B-065). Do not edit ROLLING_BACKLOG.json.
- CI IS THE GATE FOR CODE ONLY (operator 2026-11-05 17:15 PT, DECISION_LOG): check locally first (run the tests that touch what you
  changed; `python3 scripts/precheck_changed.py` once #436 is on main). Open a PR only for code. Never wait on, re-run or dispatch CI for
  docs, results or queue edits. Merge code only on a green CI run of its current head.
- DATA EPOCH (GG-1771 / GG-1784): NO-side demo fills before 2026-11-06T01:03:42Z were mirror-priced. Any block reading fills or P&L
  reports pre-epoch YES-only and post-epoch all sides, and says which; never mix them.
- DOCS-ONLY MEANS NO CODE (SW-9, 2026-11-05, after aae5e6c turned main red): a push labelled docs-only contains no .py file;
  any .py - including under 12_EXPLORATORY/ - goes through a PR and merges on green CI. Before opening a PR, run
  `python3 scripts/precheck_changed.py` (#436) once it is on main.
- NO FUTURE DATA (operator 2026-11-04 21:45 PT: "please ensure you're not give me an active block that requires some sort of future time
  to hit - that makes no sense"): every part of this block runs on data that exists at paste time. Never wait for a game, a night, a
  settle or a clock time. If something you need does not exist yet, write that in the handoff for the window and move on.
- INSTALLS ON THE BOX: the auto-mode classifier refuses the allowlisted *_install bridge tasks (terminals 97.1 / 97.3; the strategic
  window too). Never work around it. Prepare and test the install, push, and name the exact task in your handoff; the window runs it
  only after the operator approves that task by name in chat (as he did for t3_lock_stagger_install and install_batch_w99_install on
  2026-11-03). The install gate's deadlock is fixed (#405, #412: the batch exempts only its own reds; each step reads its own conf).
- SIZE (operator 2026-10-30 08:38 PT): THREE parts, about 130 minutes. Part C is a task you can switch to whenever an earlier part
  waits on the box (a long fetch, a deploy, CI). Push after every part.
- After EACH part: push, and update this block's row in 04_EXECUTION/ACTIVE_QUEUE.md (NOW table: Status + one line) with a docs-only
  push. Stop at a pushed boundary (context ~60%, a blocker, or the time) and write the handoff. Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs, and ONLY on a CI result you
  have read as green (W80.1 merged #291 red and broke main). After each merge, read the box's deploy (deploy_truth_read, or
  logs/vps_deploy.log on the box: the box deploys itself on a timer; the GitHub "Deploy to VPS" job is manual-only since W67.3, GG-1462)
  and record the t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-11-09 19:30 PT - incl. Wave 107 results: 107.1 edge map (#452; 39 hypotheses: 14 ACCRUING,
  13 NO EFFECT NET, 7 RULED_OUT, 5 UNTESTED; nothing has survived costs forward); 107.2 news lag (#453): 276 NBA injury-report events,
  moneyline moves < 1c vs the 1.5-2.3c cost wall = NO at 20-minute resolution, news_burst_capture_install prepared and NOT run;
  107.3 v3 does not lead Kalshi on 42 availability-change games (lead -0.06c [-0.27, +0.14]); NBA coverage 3 of 3 since 11-05.
  The window's strategy recommendation is in ACTIVE_QUEUE "Needs your decision". Wave 106 and earlier as below.
  Standing (carried from Wave 100, verbatim): incl. Wave 99 results (99.1: Muse's archive in an engine for the first
  time - NFL crews and NBA referees into totals: NULL (NBA an upper bound: no pre-tip crew time); Muse's NBA referee records VERIFIED
  236/239, NFL crew yards exact / counts not reproduced; NHL OT / SO settlement already exact - the totals bias sits in REGULATION scoring.
  99.2: EXP-037 verdicts in the registry (#406: GAME_TOTAL T1 + T2 RULED_OUT, 10 KEEP ACCRUING); frozen ride evidence 13 / 13 classified
  (every sign held, every net smaller; held-out KXMLBTOTAL 5c+ cell +0.26 exact [+0.13, +0.38] on 24 games); B-035 PARTIAL - 18 of 72
  games (box output cap); registered: the box output cap, proof_calendar.py has no second-look state, B1 undercounts RULED_OUT-but-logging
  arms. 99.3: batch install + one gate rule (#405), reasons on NHL / NBA points / NBA engine rows (#407), second NBA events refresh
  15:46Z (#409). INSTALLED 2026-11-04 (operator-approved by name): T3 lock + stagger 01:55Z; NBA events refresh 15:46Z, NBA engine v3,
  picks builder 03:30Z (#412 fixed the batch); box 88 live, the picks builder STALE until its first run 05:37Z), OPERATOR: RETIRE
  EXP-042 CELL 10 (2026-11-03 19:16 PT, "Yes" - KXMLBTOTAL T0-2h 85-90c wide yes; a superseding addendum, the frozen file untouched;
  cells 9 and 11 NOT retired), MUSE ON 100 DAILY RUNS (2026-11-03: 90 split runs on QUEUE.md in its own archive - 359 single-table
  chunks - and 10 ticket runs; switched on 2026-11-04 00:01 PT; 50-run stress test: 46 / 50 done, 1 gate failure, no collisions with
  assigned tickets, hard multi-source jobs slow), Wave 98 results (98.1: NBA v1 missed games because of the box's
  OOM kills and lock skips, not runner logic; v1 / v2 now write coverage.jsonl with every unlogged past-tip game and its reason. NHL
  engine v2 (empty-net / late-game state): spread better held-out (-0.0025 Brier), totals bias UNCHANGED (-0.16 / -0.12 / -0.05) - late
  scoring is not the cause; next candidate OT / shootout credit and tie handling; EXP-046 not frozen. v3's availability and lineups fully
  indexed (rank vs history, matchup cross): no Brier lift. 98.2: THE NFL FIRST LOOK READ - 12 cells at 60 games: GAME_TOTAL T1 and T2
  RULED_OUT (about 0.016 Brier worse than the market, one finding: shared games), 10 KEEP ACCRUING (all a little behind the market, all a
  little ahead of climatology, none proven), 0 CANDIDATE; entry cost: KEEP the frozen rule (taking at the quote loses about 0.10 per
  contract in NBA and NFL; NHL unclear); frozen ride evidence 11 of 13 DIFFERS - every sign held, every net smaller than reported (two
  held-out KXMLBTOTAL cells unclassified, GG-1600; the window queued the remaining shards). 98.3: T3 lock + stagger (GG-1581), the picks
  install task, v3 on the shared engine lock, top-3 reasons on the NBA / NFL / MLB game-market rows - all merged, NOTHING INSTALLED (the
  classifier refused the window too); GG-1630: NHL, NBA-points and nba_engine writers log no reasons), MUSE'S STANDING ROLE (operator
  2026-11-02 21:33 PT: "we're still gonna run it as a data aggregator bc it's far from getting to the type of stats/pulls I'm
  envisioning"; charter v3 amendment: every card names the engine and factor it feeds and whether the bot can capture the source itself;
  the bot reads none of the archive's 177,346 records today), THE CONCEPTUAL LAYER (operator 21:40 PT: "the raw table stats are a starting
  place that we'll be able to build on once we start hitting conceptual data aggregation ... The interpretative data should be able to
  feed each other as each branch gets built - exponentially making each branch easier to build"; drawn as "Compound splits" spokes on
  the aggregation web), Wave 97 results (97.1: NBA engine v3 frozen as EXP-044c and
  merged, NOT installed (the install was refused by the classifier); the v1 and v2 arms are logging (box 11-03 03:10Z: v1 1,645 rows / 69
  events, v2 2,008 rows / 81 events - v1 misses games v2 logs; two "Killed" lines in the runner's log); player points with availability
  LOSES to the existing arm held-out (+0.0131 Brier), no EXP-044d. 97.2: resumable reproduction tooling merged; 2 of 20 units cached;
  the ladder units time out at 900 s on a 1-core 961 MB box at load ~25; 0 of 13 cells classified; B-011 not started (third time).
  97.3: the picks sheet built, merged and deployed (dry run: 4,538 picks over 161 games), its cron NOT installed; MLB arms IDLE with
  written reasons (#393); MEMORY: 20 OOM kills in ~90 minutes, the T3 shadow runners stack 2-3 deep with no lock, an NBA pre-game T3 run
  lasts 62 minutes (GG-1581, HIGH); pick reasons need a runner logging change (GG-1580). 97.4: the NHL engine (one Poisson simulation
  prices moneyline, puck line, totals, team totals); beats climatology on moneyline and team totals held-out, totals at climatology and
  running low (late / empty-net scoring not modelled); trails Kalshi at n = 33 games, not significant; EXP-046 not earned), THE NFL FIRST
  LOOK RAN on 2026-11-02 (the calibration engine: P1 12 / 49 cells at a scored look, P2 12 verdicts; the verdict text is not yet read -
  98.2), the box RED at the close (11-03 03:10Z: two registered-not-installed cron lines - the NBA events refresh and the picks builder -
  and the NBA engine v3 arm SILENT because it is not installed), THE PICKS SHEET
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
- Four blocks run in parallel. File ownership: 108.1 = 12_EXPLORATORY/edge_map/ (rows it closes), the archiver's prop-series list (scripts/archive_market_prices.py config - add
  series, do not change existing capture) with ONE allowlisted install task PREPARED if a crontab change is needed, NEW quant/ functions;
  108.2 = NEW functions in quant/ (trade prints) + tests, 12_EXPLORATORY/news_lag/ additions; 108.3 = NEW functions in quant/ (props)
  + tests, 12_EXPLORATORY/quant_w108_props/; 108.4 = 12_EXPLORATORY/weather_scope/ ONLY (+ NEW functions in quant/ with tests).
  READ-ONLY for everyone: ledgers, logs, stores, reports, pre-registrations, verdicts, cell tables, router, runner, order path. Kalshi's
  public market-data endpoints only (no orders, no account changes). Muse's archive: READ ONLY. Shared navigation files: append-only,
  separate docs-only commit, never inside a code PR.
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W100_<n>.md (docs-only push).

```
