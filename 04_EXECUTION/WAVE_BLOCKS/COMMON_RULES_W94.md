# Wave 94 common rules

Every Wave 94 block tells the terminal to read this file first. Text below is the rules verbatim.

```
COMMON RULES - WAVE 94 (THE ENGINES GO LIVE: NBA PRICES TONIGHT, NFL ON A FORWARD CLOCK; RED FIRST; QUANT IN TANDEM) (read first; they bind this block)
- THIS WAVE (the lane rule, operator 2026-10-27 22:24-22:38 PT: one engine block every wave, a proof lane, a flex lane, quant in
  tandem; "let's just be a bit more intentional about things moving forward"): 94.1 engine lane (rank 2, one engine per sport),
  94.2 proof lane (ranks 1-2: market-anchored test of the NFL engine), 94.3 flex lane (red first), 94.Q quant in tandem (rank 4).
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
- Decisions in force: DECISION_LOG through 2026-10-28 17:10 PT - incl. Wave 93 results (93.1: NBA availability known before tip
  built point-in-time from the injury report (P(played | Questionable) 0.514, Out 0.0008, Available 0.856); it adds nothing measurable
  beyond the rotation (n 2,008); expected missing minutes is the lead; applied blocked - the NBA event store ends at 2025-26 and has NO
  2026-27 games (nba_event_store.py: NBA_STATS_LAST = 2026), GG-1420. 93.2: NBA travel / time zones / altitude and officials built
  point-in-time; margin no, altitude -> total small yes, officials weak and unstable; crew assignment has no pre-game timestamp
  (GG-1390). 93.3: NBA board engine (src/prediction_market_bot/nba_engine/): one simulated joint score distribution prices moneyline,
  spread, total, team totals; beats its Gaussian twin on held-out 2021-26 (n 7,230, dBrier -0.0004 [-0.00054, -0.00025]); moneyline
  under-confident (slope 1.83); score correlation over-stated by ~0.06-0.09; vs Kalshi unestimable (0 settled rows at the time).
  93.4: NFL board v2 (src/prediction_market_bot/nfl_engine/board_v2.py) priced from the market's own line: key number 3 now within noise
  on held-out seasons (z -0.7, was +23.8 for a Gaussian); it matches Kalshi's ladders - no edge; N15 travel / short weeks interpreted.
  93.Q did not run (carried as 94.Q)), the box RED at the Wave 93 close (2026-10-29 00:04Z: T4 MLB live SILENT - a World Series game
  started, no rows for 19.6 h), THE LANE RULE (operator 2026-10-27 22:24-22:38 PT), Wave 92 results (archive covers four sports;
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
- Four blocks run in parallel. File ownership: 94.1 = NBA current-season ingestion (c1_signal_ingestion/ additions, NEW cron lines or
  bridge tasks + RUNTIME_REGISTRY entries), a new runner for the NBA engine shadow arm (pregame_shadow/ addition) + tests, a new EXP-044
  pre-registration, a new 12_EXPLORATORY/nba_engine_live/; it CALLS src/prediction_market_bot/nba_engine/ and does not edit it except to add
  a thin entry point; 94.2 = NEW modules in src/prediction_market_bot/nfl_engine/ (board_v2.py may gain functions; existing ones stay),
  a new EXP-045 pre-registration, the NFL temporal_evolution [[component]] entry in ARCHITECTURE_COMPONENTS.toml, a new
  12_EXPLORATORY/nfl_engine_forward/; 94.3 = the t4-mlb runner and its ingestion path ONLY as the root cause requires, its tests, the
  GG entries it registers, 12_EXPLORATORY/t4_mlb_silent/; 94.Q = NEW functions in src/prediction_market_bot/quant/ + tests,
  src/prediction_market_bot/decision_trees/ride.py (the LADDER side fix only), a new 12_EXPLORATORY/quant_w94/, 04_EXECUTION/PROOF_CALENDAR.md
  (generated), a new allowlisted read-only box task if needed. Data: the NBA event store, the price archive (four sports), Kalshi's
  public history, the NFL play-level store. Muse's cards: github.com/eignacio1/sports-intel-archive (READ ONLY). Everyone may ADD to
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
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W94_<n>.md (docs-only push).

```
