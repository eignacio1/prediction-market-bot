# Wave 119 common rules

Every Wave 119 block tells the terminal to read this file first. Text below is the rules verbatim.

```
COMMON RULES - WAVE 119 (WIRE WHAT 118 BUILT: NHL FROM ITS STORE, NBA DEPTH SPLITS INTO THE LIVE TREES, PLACEMENT THAT FILLS) - SW-9 (read first; they bind this block)
- THIS WAVE (three blocks, the regular three; operator 2026-11-17 21:17 PT framing below still binds; MODEL: Sonnet for all three - D-34: never Opus or Fable in a terminal). The
  operator: "with each coming wave close ... my strategy windows IMMEDIATELY turn to well fuck none of those experiments/research/dev
  moved the needle we must be fucked. It's just not the right conceptual building structure. We are fine - we've been fine." So:
  this is a router being BUILT. A null is a routing result (the leaf gets RIDE or NO BET, the hypothesis is closed and parked for
  R&D), never a verdict on a sport, a block or the project. Report what the router now does per cell and arm, and what was built.
  Layer 3 is where depth enters the router (ADR-0075, DOCTRINE): a factor is APPLIED only as a tested split, scored per leaf per arm.
- A GAP BURNER may run alongside (OPEN 264 -> 174 in W118; target 150). It owns the status
  lines of EXISTING gaps in GOVERNANCE_GAP_LOG.md. Blocks only APPEND new gaps (`git pull --rebase` right before pushing the log, and
  check the number with scripts/lib/gg_id_uniqueness_check.py) and never edit another gap's text or status.
- Do not edit ROLLING_BACKLOG.json (the window owns it).
- READING BUDGET (kept from the Fable wave): session-start protocol from the governance scan's printed output only; read the files your
  block names and what you touch; no archives or DECISION_LOG history. Handoff 60 lines at most.
- EVERY PREMISE IS DATED: the box numbers quoted are from 2026-11-18 06:20Z unless a block says otherwise. Re-read the box first
  (d6_read, arm_orders_read, deploy_truth_read are allowlisted read tasks) and work from what it says now.
- A LOSING LOOK CLOSES ONLY THAT TEST (operator 2026-11-11 16:51 PT, binding; DOCTRINE 1b): "a cell being closed isn't just closing the
  "fade arm" - it's closing THAT SPECIFIC HYPOTHESIS, for future research and development that we'll circle back ... a cell closing
  shouldn't mean anything is being closed but a test." No cell, market or arm closes. Text says "hypothesis closed (<EXP-id>, parked for
  R&D)". Never "ruled out", "no edge", "blocked", "fade arm closed" or "cell closed" for a model that lost.
- REPEATED DIRECTIVES: read 04_EXECUTION/OPERATOR_DIRECTIVES.md before building. Code that contradicts a directive there: fix it if you
  own the file, otherwise name it in your handoff under `directive_conflicts:` with file and line.
- THE ARCHITECTURE (operator 2026-11-10 21:35 PT, binding): depth does not exist to out-price the market. Factors feed LAYERED decision
  trees and filters that choose the ARM per market - ride the market, fade it, momentum, pot of gold, or no bet. Layer 1 market state (price,
  move, ladder gap, book, time to start); layer 2 filters built from the factors (matchup, lineup / usage, rest / travel, refs, weather, PAM);
  layer 3 a tree per cell that picks the arm. A factor is APPLIED when it is a tested split in that tree, scored per leaf: net after costs,
  held out ("where filter F holds, riding wins / fading wins / no bet"). The engine's own price is one input to the tree, never the bet.
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
- Decisions in force: DECISION_LOG through 2026-11-18 - incl. 11-17 22:18 PT (disk_retention_install approved; the window ran it),
  11-17 17:45 PT (NHL store; NFL v1 per-leaf -> NO BET; tested stumps at layer 3), 11-17 (caps raised; placement policy on), free only.
  Wave 118 results: 118.1 (#522) the 2026 MLB ledger holds the POSTSEASON only (22 games; GG-1957): router v2 armed 0 / 80 leaves; 12 MLB
  cells recorded NO BET (provisional); held out ride-every-favourite +0.037 / row [-0.024, +0.090], always-FADE -0.078 [-0.124, -0.027];
  frozen leaf_maps/mlb_2026_lookback.json + PREREG_2027. 118.2 (#523) five NBA depth splits built point in time from Muse's archive
  (decision_trees/filters/nba_depth.py, archive SHA bafaeef4): S1 pace / net rating 5 kept, S2 shot-zone matchup 5 kept (best: SPREAD T3
  home_edge MOMENTUM +0.155 / contract, lower bound +0.048, 16 held-out games), S4 home / road gap 2 kept, S3 lineups and S5 refs thin
  (snapshots start 11-10); 0 BH-significant; leaf_maps/nba_depth_v2.json, NOT wired. 118.3 (#520 #524) goalie confirmation lag 0.2c
  [0.07, 0.43] on 14 games, below one round cost: hypothesis closed, NO BET; the NHL store is NOT built on the box yet (one-shot refresh
  task requested 20261118T0613Z); D6 NHL 0. 118.4 (#521 #525) disk 87% (20.0 of 23.2 GB, +1.54 pt / day); retention as code (compress
  only, sha-checked, never delete); journald cap; logs/ride_board/decisions.jsonl alone 1.0 GB in a week. Gap burner 264 -> 174.
  Wave 117 results: 117.1 (#512 #514 #519) game-clustered with real spread, no arm-and-option clears zero: FADE crossed +0.166
  [-0.016, +0.348] (105 orders / 20 games), RIDE +0.016, MOMENTUM +0.052; FADE rests at its own best bid on the side the market is leaving,
  so 6 of 111 filled; spread backfilled 454 / 486; placement table 0 cells (policy on = no-op until re-fit). 117.2 (12_EXPLORATORY/
  nhl_consensus/) NHL consensus prior moves the first arm 1-7 weeks earlier, coarse leaves 6-40 weeks LATER; momentum closed; Kalshi vs
  books NHL moneyline (n 1,312, candle 1h before start): gap +0.0016, riding consensus at ask -0.055. 117.3 (#511 #516) D6 3 -> 4 (NBA:
  GAME_TOTAL T3, SPREAD T2 / T3, TEAM_TOTAL T3); NBA layer 1 12 -> 15; NBA layer 3: 9 kept splits, 12 stumps; unwired NBA causes: MONEYLINE
  T1-3 / SPREAD T1 / TEAM_TOTAL T1 layer 4 (thin leaves), GAME_TOTAL T1 layer 6, T2 cells layer 7, props layer 1-2; healthcheck false FAIL
  (SIGPIPE) fixed. 117.4 docs_guard on every push; live handoffs 644 -> 42. Window 05:04Z: nhl_event_store_install ran (daily 13:29Z);
  box HEALTHY, disk 87% before the ~325 MB store, FAIL at 90%.
  Wave 116 results: 116.1 (#506) router v2 = pooled tree posterior + always-valid e-process; Fable's plug-in variance made binary-null
  false claims 275/300, fixed to 2/300 (planted +0.10 found 79/100); held out (W110.5 split, 161 games): v2 arms 0 leaves, v1 per-leaf
  -0.0064 / row [-0.0138, +0.0009], NFL -0.0201 [-0.0369, -0.0054], ride every favourite -0.0256; power calendar at +0.02 first arm
  2027-07-21 (NHL), at +0.05 2027-01-20; NFL prior from nflverse; v2 map behind PM_LEAF_MAP_VERSION (default v1). 116.2 (#504, #505,
  #508) demo caps separated from risk.py (old 5 / 50 / 25 default, raised behind ARM_BOOK_CAPS); tolerant parse_ts (GG-1934); per-order
  join lookups failed 244 -> 0 of 486; box 00:58Z post-epoch per arm: RIDE 279 orders / 39 fills, fills win 69% vs non-fills 81%
  (adverse), E2 -0.008 after fees; MOMENTUM 96 / 20, 50% vs 50%, E2 +0.075; FADE 111 / 6, 33% vs 38%, E2 +0.106; best option per arm
  = cross: FADE +0.183 [+0.089, +0.277] n 100, RIDE +0.023 [-0.023, +0.069], MOMENTUM +0.020 [-0.091, +0.131] - spread_logged 0 on all,
  so cross cost is not measured yet. 116.3 (#503, #507) router ERROR fixed (KeyError market_ticker in LeafMap.row_for, GG-1939);
  size_for on every routed row; D6 on the box 3 of 117 (NBA_GAME_TOTAL T3, NBA_SPREAD T2, NBA_SPREAD T3); unwired causes: NFL layer 3
  (0 of 28 splits kept), NHL layer 3 (store absent; #507 shrinks it 2,049 -> 270 MB, install awaits approval), NBA_TEAM_TOTAL T1-3 layer
  3, NBA_SPREAD T1 layer 4, NBA_GAME_TOTAL T1 layer 6, T2 layer 7, moneylines / props / T4-T5 layer 1 (no model p); GG-1951 layer 3 is
  credited from the split file, not box rows. Muse 11-17: free NHL 2025-26 consensus lines (1,394 games, open + close, ML / puck line /
  total, vig-removed, 16-23 books) at sports-intel-archive L3-closing-lines/nhl/minmaxxxer-2025-26/ (B-099).
  Wave 114 results: 114.1 (#494 #500) Muse intake landed (archive_intake/, read-only, pinned SHA; GRADES.md); NBA index 24 -> 36 entries;
  54 leaves scored, 5 kept, 0 BH; NBA distance filters wired (14-day NBA RIDE 651 -> 382 as kept splits disagree). 114.2 (#498)
  scripts/arm_orders_read.py + scripts/d6_read.py allowlisted; D6 0 / 117 ON THE BOX; arm orders since 11-12 06:43Z: RIDE 162 orders /
  21 fills, FADE 37 / 1, MOMENTUM 7 / 1 (NBA and NFL; NHL 0 orders - 1,415 NHL rows UNROUTED on the box); E2 / E3 null (0 settled);
  skips: daily_breaker 690, size_zero 36, no_bet 3,542, unrouted 593 (NBA / NFL); layer 3 on the box NBA only (NHL_EVENTS absent,
  GG-1898; default_nfl_providers() returns None, GG-1933); GG-1934 (Python 3.9 "Z" timestamps in demo_fill_forward_report);
  GG-1935 (the daily breaker dominates skips). 114.3 (#497 #499) the orchestrator defers to the router; score_vs_market / run_w84_3 /
  edge-map rows per leaf per arm (E09 / E14 arm tables still open). 114.4 (#501) team usage-pool latents built (default off): teammate
  PTS x PTS +0.0230 -> +0.0224, PTS x AST +0.0108 -> +0.0078 - hypothesis closed (W114.4 team-pool latents, parked for R&D).
  Wave 113 results: 113.1 (#493) arm orders sized through size_for; NHL per-row filters (20 splits kept) - layer 3 NHL +9 cells LOCAL
  ONLY (needs exp_output/NHL_EVENTS, which has no box job: GG-1898); D6 rules for layers 6 / 7 written; D6 wired 0 of 117 (local
  recount: layers 6 / 7 need the box's logs/arm_orders/orders.jsonl, which no allowlisted task reads). 113.2 (#495) NFL wired for Sunday:
  pre-kickoff weather forecast store, MatchupBook, 25 NFL index entries (13 scored), layer 3 NFL 0 -> 13 cells, D5(b) NFL 12 -> 14 of
  23; box deployed. 113.3 (#496) nba_engine/joint.py shared-latent joint: same-player PTS x 3PM covariance gap +0.086 -> -0.004 (closed);
  teammate PTS x PTS +0.025 -> +0.023 (sign still wrong), PTS x AST teammates +0.004 -> +0.011 (worse), WIN x REB not closed; combo pricer
  merged. 113.4 (#494, branch session/20261112T230415Z-w113-4-archive-intake) archive_intake/ read-only at a pinned SHA, grades in
  12_EXPLORATORY/archive_intake/GRADES.md, 12 NBA index entries (opponent FG% and shot share by distance bin), nba_distance_filters.py -
  PR CONFLICTED (dirty), no CI run, not merged, no handoff.
  Wave 112 results: 112.1 (#488) decision_trees/filter_supply.py per-sport adapters (point-in-time asserts); NBA wired (layer 3 cells
  0 -> 9 of 25); NFL logs `nfl_weather_forecast_and_matchup_book_not_wired`, NHL logs `filters_unavailable:nhl_engine.filters_not_merged`
  (112.4 merged after it: call nhl_filters_for_row); 113 splits tested, 7 kept (all NBA, none BH-surviving); 14-day replay NBA 6,390
  decisions, 626 NO_BET -> RIDE. 112.2 (#487) closed HYPOTHESES replace closed arms (NFL game total T1 / T2: 2 recorded); c4_risk_engine/
  arm_sizing.size_for (Kelly 0, flat demo stake, per event / day / arm caps, same-game correlation cap, Kelly-shaped stake logged never
  placed); 14-day replay not run on real rows (box rows; needs a read task). 112.3 (#486 #492) decision_trees/arm_orders.py, hook in
  shadow_flat_stake.maybe_place, ADR-0072 superseding addendum 2026-11-12, per-arm forward report; ARM_ORDERS=on in deploy/demo_fill.env;
  sizes through its own flat default, not yet size_for. 112.4 (#489) NHL factor classes as filters: D5(b) NHL applied 3 -> 8 of 12;
  Part B open (goalie confirmation timing; Muse snapshots ungraded - archive not readable from the bot repo; GG-1010 starter post-game).
  Window: Live Terminal shows arms / D6 / arm orders (#491).
  Wave 111 results: 111.1 (#482) the verdict keeps its pre-registered label and adds `routing`; registry `closed_arms` (FADE) on NFL game
  total T1 / T2, both SHADOW again; proof_calendar / distance report closed arms. 111.2 (#481) 41 code decision points audited
  (04_EXECUTION/DOCTRINE_CONFORMANCE.md): left open - execution_bands_orchestrator.py:108,180 (the model's edge, not the tree, picks the
  arm), 12_EXPLORATORY/market_history/score_vs_market.py:69 and nhl_engine/run_w84_3.py:6 (scored only as Brier vs market), edge-map rows
  E01 / E09 / E10 / E14 (no per-leaf arm scoring); a banned-verdict-word test guards dashboard labels. 111.3 (#483 #484) the router reads
  decision_trees/leaf_map.json; every shadow row logs leaf_id / arm / arm_source / filters; pot of gold and momentum scored per leaf (arms
  4 -> 6); D6 scorecard in coverage.py; LEAF_MAP_FORWARD_PREREGISTRATION_2026-11-12.md frozen ("factor filters as splits (not supplied per
  row by any runner yet: D6 layer 3 stays open)"). 111.4 (#485) NBA granularity index: 24 entries, 18 scored per leaf (85 leaves, 0 BH
  survivors - routed NO_BET provisionally), `nba_filters(home_profile, away_profile)` exported for the router; D5(b) NBA 10 -> 11; GG-1895.
  Wave 110 results: 110.1 NFL weather (point-in-time) + matchup crosses as router filters (#473; nfl_engine/filters.py), D5(b) NFL
  applied 10 -> 12; per leaf 0 / 82 leaves earn an arm (about 2 by chance); MOMENTUM unscorable on one closing line; no NFL Kalshi spread /
  total history. 110.2 NBA (#475): D5(b) applied 5 -> 10 of 17 (B10, B12, B13, P1, P2); usage improves spread and team total Brier
  held out (n 2268); geometry and officials null; PAM hindsight-only. 110.3 router (#476): 27 of 117 cells routed (NHL 9/9, NFL 9/13,
  NBA 9/24, MLB 0/18); every shadow row logs the router's arm; 14-day replay 25,263 decisions all NO_BET - bounded by date-only tickers
  and IN_SAMPLE cells, not by the router. 110.4 same-game correlation (#478): the NBA engine joint is right for game x team / player
  points and wrong for same-player cross-stat (points x threes realised cov +0.091 vs engine +0.005) and teammate points (sign wrong).
  110.5 retro-route (#479; 12_EXPLORATORY/retro_route/ROUTING.md): 365 leaves, 189 thin, 113 routed on the fit window, 1 BH lead (NHL ML
  T2, 11 games), 0 drafts; family level held out: RIDE NFL moneyline +0.134 [+0.017, +0.236] (84 rows / 28 games), MODEL FADE NHL puck
  line +0.088 [+0.037, +0.136] (2,443 / 66), FOLLOW MOVE NHL moneyline +0.074 [+0.015, +0.133] (116 / 59); riding beats fading in nearly
  every family.
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
- Three blocks run in parallel; ownership is disjoint. 119.1 = NHL: nhl_engine/, nhl adapter and NHL event store files, leaf_maps/nhl_*.json,
  12_EXPLORATORY/nhl_*/, scripts/d6_read.py. 119.2 = NBA depth wiring: decision_trees/filter_supply.py (sole owner; 119.1 reaches it only
  through the existing nhl adapter - if it must change filter_supply, it rebases on 119.2's merge), decision_trees/filters/,
  decision_trees/coverage.py, c5_execution/market_type_registry.py, leaf_maps/nba_*.json. 119.3 = execution: decision_trees/arm_orders.py,
  ride_orders.py, c5_execution/placement/, config/placement_policy*.json, the ride board writer and logs/ride_board/ format,
  scripts/arm_orders_read.py, scripts/demo_fill_forward_report.py. Nobody edits router.py or the frozen v1 leaf map.
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
- No kelly_fraction change and no real capital. Demo orders follow the authorized arm path (11-11 16:51 PT); 113.1 changes only how they are sized, through size_for. No live-ledger row rewritten. No edit of an existing cron
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
