# Active queue — the only prompt file to read

> **RULE: prompt text here is ONLY for blocks firing now.** Closed prompts move verbatim to
> `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`; closed waves keep their ROWS in the Sequencing track below.

**Verified against:** `origin/main = 49c6d5a` (2026-10-08 ~18:20 PT, Wave 61 close). PRs, CI and results docs read from GitHub; VPS facts are the Wave 61 terminals' reports (this window has no SSH).

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | Claimed through **GG-535** (registered: GG-532; GG-533 reserved, unregistered) · **T-755** · **ADR-0071** · **EXP-038** · gap log **129 OPEN** (parity 153 = 153, no duplicate ids) |
| Registry (104 cells) | ACTIVE 1 (T4M-PROJ) · SHADOW 24 (3 MLB player-hits, 12 NFL, 9 NHL) · BLOCKED 2 · DARK 1 · NOT_IMPLEMENTED 76 (incl. 12 NBA, flip ~10-21). MLB postseason game cells log + settle but are not registered SHADOW. Counted from `MARKET_TYPE_REGISTRY` at `edb3138`. |
| Capital | **$0 real.** `kelly_fraction = 0.0` on every operating band; **T4M-PROJ places flat paper measurement stakes of min($1, max_contracts x price)** (ADR-0050). Demo venue only. SHADOW = evaluate and log. |
| Shadow arms | **NFL** 12 cells logging, first look projected **2026-11-02**. **MLB postseason** armed and logging (judged n starts 2027). **NHL** 9 cells logging; judged n unreachable this season (GG-514); no NHL T3 score may be read (GG-401). **NBA** preseason rows to a separate labelled ledger; regular season 10-20, cells flip ~10-21. |
| Open PRs | Only stale ones from Waves 30-34 (#133, #144, #146, #149). Nothing from Waves 52-59 is waiting. |
| VPS | Last deploy `056428f` (#188), 2026-10-08 02:43 UTC, success; t4-mlb not restarted by Wave 60 (no T4 import changed). |
| Deploy | **GG-432 resolved (#158, 2026-10-05):** a push restarts `t4-mlb` only if it changes a file t4-mlb imports AND no MLB game is live; otherwise the restart is skipped and logged. Dashboard restarts every deploy. Code can land at any hour. |

---

## 🌲 RUNNING SITREP — the forest (kept by every strategic window; last window: Waves 52–60, 2026-10-03 → 10-08)

*Updated by the strategic window at every wave close and at every handoff. Last update: Wave 62 closed, Wave 63 issued, 2026-10-09 ~01:30 PT.*

### 📏 DISTANCE TO OPTIMUM — read this first

*The gap between the project and the bot at optimum, as numbers. Measures are defined in CLAUDE.md § "What winning looks like" →
"Distance to optimum"; values are recomputed at every wave close. Values below: 2026-10-09 ~07:45 UTC, hand-derived from the cited
sources — a generator that computes them mechanically is the first Wave 63 block. "Moved" = change during the last closed wave (Wave 62).*

| Pillar | Measure | Now | At optimum | Moved in W62 | Source |
|---|---|---|---|---|---|
| **BREADTH** | B1 registered cells logging (ACTIVE + SHADOW) / registered | **25 / 104** (+12 MLB postseason cells logging, unregistered) | every cell of the whole board registered and logging | 0 | `MARKET_TYPE_REGISTRY` |
| | B2 market families with a logging cell / registered families | **8 / 18** | 18 / 18, with props and parlays registered | 0 | registry |
| | B3 bands with a logging cell | **4 of 5** (no T5; T4 = T4M-PROJ only) | 5 of 5, T4 sub-bands included | 0 | registry |
| | B4 props · parlay families logging | **1 · 0** | the board's props and parlays | 0 | registry |
| **DEPTH** | D1 granularity-bar inputs in live pre-game models | **0 qualitative inputs anywhere; personnel/availability: NHL projected goalie only; weather: none** | matchup, personnel, team, venue, weather and qualitative factors at every pre-game arm | 0 | EXP-036/037/038 pre-registrations; T-597 |
| | D2 largest pre-game feature set | **18** (MLB player hits T1, 0 qualitative) | coverage of the factor classes, not a count | 0 | `models/mlb_v1_model_meta.json` |
| | D3 pre-registered challengers ready | **0** (2 NFL candidates tested exploratorily; neither beat the frozen model) | at least one per arm before its first look | 0 | `12_EXPLORATORY/` |
| **EXECUTION** | E1 demo orders filled / closed positions | **251 / 4,705 = 5.3%** (T4 166/4,220; T1 MLB 85/485) | fills ≈ intended orders | T1 measured for the first time | W61.1, W62.3 |
| | E2 P&L per filled bet | **T4M-PROJ −$0.26** (n=165) · **T1 MLB −$1.50** (n=83) | positive, net of fees | measured | W61.1, W62.3 |
| | E3 win rate on fills vs non-fills | **T1 MLB 28.9% vs 52.1%** — orders fill mostly when they are about to lose | fills at least as good as non-fills | measured | W62.3 |
| **PROOF** | P1 cells at a scored look / logging cells | **0 / 25** | every cell judged at its pre-registered n | 0 | calibration engine |
| | P2 verdicts issued | **0** | a verdict per cell (a rigorous NO counts) | 0 | — |
| | P3 next look | NFL ~11-02 (15/60 per cell): MDE ~0.038 Brier vs a plausible ~0.008 → ~91% "keep accruing" (W62.2) | — | — | EXP-037; W62.2 |

**Rule (operator, 2026-10-09: "perfection isn't a dream, it's a protocol"):** every block, session and review states before it starts
which measure it is meant to move, and reports at close what moved and by how much — or says PLUMBING in plain words. Two waves in a
row that move nothing is drift, and the strategic window says so unprompted.

**Forest read (2026-10-09):** Waves 52–61 were almost entirely BREADTH plumbing and PROOF machinery. The instrument is ready; the
thing it measures — model depth — and the thing that converts it into money — execution — were never staffed. Both books now show
the same execution signature (fills lose, non-fills "win"), so every paper P&L figure in the project's history is calibration
evidence at best.

**Wave 62 (10-09), in one line:** the T1 MLB book has the same execution problem as T4M-PROJ (fills lose, non-fills "win"), and the
NFL first look is ~91% likely to say "keep accruing" with the current model — so Wave 63 goes to MLB coverage while games
remain, NFL model depth (the math), and why our fills lose.

**Bottom line.** The plumbing is now sound. Code lands at any hour without killing live services, MLB data no longer
depends on a blocked source, every resolved bet books from Kalshi's own settlement (1,229 of 1,229 match), and four
sports log shadow forecasts. **We still have no verdict that the model beats the market anywhere.** Wave 60 settled
what the only ACTIVE cell's sample is: **94.5% of T4M-PROJ's 1,952 rows were never filled.** The 107 real fills lose
$0.40 a bet. So T4M-PROJ is a calibration record, not trading evidence. **You decided that 2026-10-08 (GG-527 (b)+(c)); Wave 61 builds it.** The first scored
look is **NFL, ~2026-11-02** (15 of 60 games per cell; date confirmed by 61.2) — and its own pre-registration expects it to be
inconclusive (plausible edge below what 60 games can detect). See the distance-to-optimum table above.

**Wave 61 (10-08):** fills-only counting is live on both dashboards (T4M-PROJ real fills n=165, about -$0.26/bet). The
stand-down gate is merged but not yet in the running process (62.3). The first-look release path had a real bug (no
REPORT written) — fixed before it mattered. **The MLB postseason shadow arm has been silent since 10-08 (GG-532)** —
found by hand, which is why 62.1 also builds an alarm. Early exploratory read (not a verdict): on 2025 NFL games the
market priced at least as well as our frozen model; expect the 11-02 look to be hard-pressed to show edge.

### Scoreboard

| Measure | Start of window (10-03) | Now (10-08) |
|---|---|---|
| Real capital | $0 | $0 — demo only, Kelly 0 everywhere |
| Cells (registry) | 92 · ACTIVE 1 · SHADOW 16 on an unmerged branch | 104 · ACTIVE 1 · SHADOW 24 on main · 12 NBA ready to flip ~10-21 · MLB postseason logging |
| Sports logging forecasts | NFL, NHL (partly) | NFL, NHL, MLB postseason, NBA (preseason labelled + excluded) |
| Cells at a scored look | 0 | 0 — engine sealed below each cell's pre-registered n |
| Books truthful? | 26 MLB positions stuck; NFL book orphaned | All booked from Kalshi (ADR-0071); NFL book archived; **T4 fills classified: 166 of 4,220; dashboards count fills only for T4M-PROJ** (T1 book: 62.3 asks) |
| Open gaps | 176, many stale | **129** (10-09); resolved entries retired to the archive |
| VPS stability | Nightly out-of-memory crashes | Staggered crons + swap; clean since 10-05 |

### What this window built, by theme

| Theme | Waves | Outcome |
|---|---|---|
| **Landing + deploy safety** | 52–55 | Four stuck PRs landed (#158–#161). Deploys restart t4-mlb only when its code changed and no game is live. |
| **MLB data off statsapi** | 52–58 | Schedule, cache and features build on GitHub Actions; the degrading 22:30 cron is off; player-hits restored. |
| **Books + settlement** | 53–60 | Kalshi settlement is the paper resolution source; 26 stuck positions booked; settlements cross-checked; T4M-PROJ fill truth established; weekly rebuild can no longer wipe a repair. |
| **Shadow arms** | 53–60 | NFL 12, NHL 9, MLB postseason 12, NBA 12 (EXP-038, frozen model, crons, preseason ledger). |
| **Calibration engine** | 58–60 | One engine, every cell under its own pre-registration, sealed below n, frozen tamper-evident releases, schedule-based projections, NBA included, pre-registration holes closed by dated addenda. |
| **Dashboards** | 52, 56–60 | Live Terminal (`/`) = what the bot places/evaluates now; Visual Dashboard (`/project`) = health, books, evidence clocks, Calibration. Phone-width clean. |
| **Fill truth + verdict readiness** | 61 | Fills-only T4M-PROJ counting on both dashboards; stand-down gate; first-look release path fixed + runbook; exploratory track fenced (no NFL challenger beats frozen). |
| **Governance** | 58–60 | Gap log 176 → 130, all re-verified; deploy/ mirrors the live crontab; ADR-0070 accepted; window handoff is now a command (`/strategic-handoff`). |

### PROOF, per arm — does the model know something the market doesn't?

| Arm | Status | When a verdict is possible |
|---|---|---|
| **T4M-PROJ** (MLB player hits, ACTIVE) | All rows -0.053/bet (CI spans 0); **real fills -0.40/bet (CI excludes 0), n=107**; latency thesis not supported (T-569) | Execution evidence says no. **Built (61.1):** fills-only counting live (fills n=165, ≈-$0.26/bet); calibration record kept; stand-down gate merged, restart pending (62.3) |
| **NFL** (12 SHADOW) | Logging; 15/60 per cell (61.2). Exploratory 2025: market mid Brier 0.2115 vs model 0.2182 (CI spans 0) | First look **11-02** confirmed (~11-09 if a game slips); 62.2 writes the expectations down first |
| **NHL** (9 SHADOW) | Logging; T3 rows now carry the projected-goalie flag (new rows) | PRELIMINARY all 2026-27 (accepted); base-rate check at 500 games |
| **NBA** (12 cells) | Sealed 0/150; opening night 10-20 | Cells flip ~10-21; first look at 150 games/cell |
| **MLB** game markets | **Postseason arm silent since 10-08 (GG-532)** — 62.1 fixes + alarms | 2027 regular season |

### Calendar ahead

| Date | What happens |
|---|---|
| Mon 10-12 14:20 UTC | Weekly T4 resolved-ledger rebuild — first live test of the overwrite guard; also refreshes the T4 fill sidecar (61.1) |
| 10-20 / 10-21 | NBA opening night; NBA cells flip to SHADOW once valid rows exist |
| ~11-02 | NFL first scored look — the project's first pre-registered edge verdict |
| World Series end | T4M-PROJ stakes stop (61.1 gate); registry flip to DARK (later block); T1 MLB winter posture is your call |
| before 2027-01-31 | Define EXP-038's date-triggered second look (GG-529) |

### Your open calls
~~T4M-PROJ cohort (GG-527)~~ decided 10-08 · ~~t4-mlb restart~~ authorized 10-08 · ~~expansion~~ directed 10-08 (demo-stake ADR acceptance due at Wave 63 close) · **T1 MLB counting (GG-536) — new** · MLB winter posture (T1 MLB; T4M-PROJ already stands down) · T4M-PROJ band placement (GG-320) · a P&L
gate that can be reached (GG-285) · approval path for self-modifying scripts (GG-289) · kill switch to count
unresolved stake (GG-441) · the unexplained SSH poller (GG-347) · T1 MLB postseason flag · EXP-038 second look
(GG-529, January) · EXP-034 (park recommended).

---

## ⬛ NOW — Wave 63 · issued 2026-10-09 ~00:45 PT · three MEDIUM blocks · paste all three in parallel

Wave 62 verified on GitHub (see Sequencing track). Every block carries a PURPOSE line (Hard Rule 12). Surfaces: 63.1 = MLB arms,
registry, feature build (GitHub Actions); 63.2 = 12_EXPLORATORY only; 63.3 = a new generator script, governance scan, Visual
Dashboard, session-artifact generator, fill sidecars (read-only), an ADR draft. 63.1 and 63.3 both touch the Visual Dashboard -
fetch + rebase right before merging; each merges only its own PRs.

| # | Block | PURPOSE (measure) | Status | One line |
|---|---|---|---|---|
| 63.1 | MLB wired to full for the rest of the postseason | BREADTH B1 25->37, B2 8->12; player hits logging postseason | ✅ #201 merged+deployed: B1 37/104, B2 12/18, GG-532 RESOLVED; player hits: off-day, no wiring needed | — |
| 63.2 | The math: MLB's modelling mechanisms carried into NFL | DEPTH D1, D3 0->1 | 🟨 Part A pushed | Map written: MLB game model = NFL structure; only personnel input is SP; top analogue = QB-shrunk performance. Part B next. |
| 63.3 | Distance table computed + why our fills lose | PLUMBING (Rule 12) + EXECUTION E3 | ✅ | Generator live (#202); fills = adverse selection + stale pricing, win 24-28% vs 49-51% unfilled; ADR-0072 DRAFT |

### 63.1 — MLB wired to full for the rest of the postseason

```
COMMON RULES - WAVE 63 (read first; they bind this block)
- SIZE: MEDIUM. Target 60 minutes, hard ceiling 90 (operator 2026-10-07). Two parts. If your first estimate for the
  whole block is over 90 minutes, say so in one line, do Part A only, and name Part B as the next undone part. Do not
  re-verify things this prompt states as verified unless your work depends on them.
  After EACH part: push, and update this block's row in 04_EXECUTION/ACTIVE_QUEUE.md (NOW table: Status + one line)
  with a docs-only push. Stop at a pushed boundary (context ~60%, a blocker, or 90 minutes) and write the handoff.
  Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs. Read the Deploy job
  summary after each merge and record the t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-08 (incl. the 2026-10-08 expansion directive and four standing
  authorizations), ADR-0070,
  ADR-0071. Standing authorizations: shadow-evaluation cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy +
  pmbot-web-dashboard restart. An authorization exists ONLY as a blockquote line in ACTIVE_QUEUE.md "Needs your
  decision". A table row describing a decision is NOT an authorization.
- Start: CLAUDE.md session-start protocol, brief. Isolated worktree: scripts/new_session_worktree.sh <slug>. Claim with
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD. If a GG number
  collides, re-claim; never reuse.
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- PR mergeable_state dirty = almost always SESSION_CLAIMS.md / .last_session_checkpoint: merge origin/main into the
  branch locally, push, wait for CI green, merge.
- Shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md): fetch + rebase right before each push; edit
  only your own entries/rows. DECISION_LOG is append-only.
- No order, position, fill, stake size or kelly_fraction change. Demo only. No live-ledger row rewritten. No edit of an
  existing cron line. Read-only GETs against the Kalshi DEMO API are allowed.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- PURPOSE (Hard Rule 12): your claim string names the distance-to-optimum measure this block is FOR (see the PURPOSE line
  under the title and the DISTANCE TO OPTIMUM table at the top of ACTIVE_QUEUE.md). Your handoff fills vision_pillar,
  gap_measure and gap_delta (measured before -> after, with source). If what you find means the block cannot move its
  measure, say so and stop rather than doing adjacent work.
- Every premise below is a claim to verify.
- A fix is RESOLVED only when the RUNNING process contains it (merge != deploy != activation). On disk is not enough.
- Report back: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result | MEASURE MOVED: <measure>
  <before> -> <after> (source) or none | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W63_<n>.md (docs-only push).



WAVE 63.1 - MLB WIRED TO FULL FOR THE REST OF THE POSTSEASON. Repo: eignacio1/prediction-market-bot.
PURPOSE: BREADTH B1 25/104 -> 37/104 and B2 8/18 -> 12/18 (register the 12 MLB postseason game cells SHADOW), and MLB
player-hits T1/T2/T3 logging postseason games again (0 players matched since ~2026-09-27). Pillar: BREADTH.

WHY
Operator, 2026-10-09: "I want to have MLB wired to full cus of the limited games left." Only the 2026 postseason remains (World
Series ends late October). Two MLB arms are not fully on: (1) the MLB postseason game-market arm (moneyline, run line, game total,
team total x T1/T2/T3 = 12 cells, EXP-037 MLB) logs rows but the cells are NOT_IMPLEMENTED in MARKET_TYPE_REGISTRY, so the
calibration engine and the dashboards do not count them; it was silent 10-08 (GG-532) and the fix (#195) awaited its first
scheduled write at the 12:07 UTC T1 run; (2) MLB player-hits T1/T2/T3 (SHADOW) has matched 0 players since ~09-27 because the
feature build only reads regular-season (gameType R) batter logs; postseason logs are opt-in in
scripts/generate_mlb_features.py (POSTSEASON_GAME_TYPES, D6(b)), and the feature build now runs on GitHub Actions
(mlb_features_sync.yml), not on a VPS cron.

PART A - The game-market arm counted (~40 min)
  1. GG-532: show the scheduled-run rows written after the #195 deploy (cbbd2658) - count by family x band, newest timestamp. Rows
     written by the scheduled job -> RESOLVED with that evidence; none yet -> say when the next run is and leave it OPEN.
  2. Confirm the EXP-037 MLB pre-registration was committed before these cells' first row (git log dates vs the first row's
     timestamp). Then, under AUTHORIZATION - STANDING: NEW PRE-REGISTERED SHADOW ARMS, flip the 12 MLB game cells
     NOT_IMPLEMENTED -> SHADOW with promote_cell_status (or the registry's sanctioned path), citing EXP-037 MLB. If the
     pre-registration post-dates the first row, STOP and report - do not flip.
  3. Make sure the calibration engine lists the 12 cells (sealed; judged n per EXP-037 MLB - postseason rows count or stay
     descriptive exactly as that pre-registration says) and both dashboards show them. Tests; PR; CI green; merge; record the
     deploy decision. Prove on the VPS: registry counts, engine listing, Live Terminal row.
PART B - Player hits back on for the playoffs (~45 min)
  4. Trace why T1/T2/T3 player-hits match 0 players: feature build (regular season only?), runner filters, market discovery.
     Show the evidence, not a guess.
  5. Read the MLB player-hits cells' pre-registration/epoch rules: are postseason games in scope? If yes, wire them in. If not,
     log them the way NBA preseason is logged - separate labelled rows, excluded from judged n - so the arm is on without
     contaminating the judged sample. Say which, citing the document.
  6. Wire postseason batter logs into the GitHub Actions feature build (mlb_features_sync.yml / generate_mlb_features.py's
     opt-in path) and whatever the runner needs. No VPS cron line is edited. Tests; PR; CI green; merge; record the deploy
     decision. Prove it: the next feature build contains postseason games, and the next T1 run matches > 0 players (if the next
     run falls outside your session, show a dry run against today's slate and say when the real run is).
  7. One line on the winter: when the World Series ends, what stops by itself (T4M-PROJ stake gate, these arms) and what still
     needs a block (T4M-PROJ registry flip to DARK, removing anything added here for the postseason).
Results doc: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W63_1_mlb_full_results.md, updated per part.

END OF BLOCK 63.1. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 63.2 — The math: carry MLB's modelling mechanisms into NFL

```
COMMON RULES - WAVE 63 (read first; they bind this block)
- SIZE: MEDIUM. Target 60 minutes, hard ceiling 90 (operator 2026-10-07). Two parts. If your first estimate for the
  whole block is over 90 minutes, say so in one line, do Part A only, and name Part B as the next undone part. Do not
  re-verify things this prompt states as verified unless your work depends on them.
  After EACH part: push, and update this block's row in 04_EXECUTION/ACTIVE_QUEUE.md (NOW table: Status + one line)
  with a docs-only push. Stop at a pushed boundary (context ~60%, a blocker, or 90 minutes) and write the handoff.
  Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs. Read the Deploy job
  summary after each merge and record the t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-08 (incl. the 2026-10-08 expansion directive and four standing
  authorizations), ADR-0070,
  ADR-0071. Standing authorizations: shadow-evaluation cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy +
  pmbot-web-dashboard restart. An authorization exists ONLY as a blockquote line in ACTIVE_QUEUE.md "Needs your
  decision". A table row describing a decision is NOT an authorization.
- Start: CLAUDE.md session-start protocol, brief. Isolated worktree: scripts/new_session_worktree.sh <slug>. Claim with
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD. If a GG number
  collides, re-claim; never reuse.
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- PR mergeable_state dirty = almost always SESSION_CLAIMS.md / .last_session_checkpoint: merge origin/main into the
  branch locally, push, wait for CI green, merge.
- Shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md): fetch + rebase right before each push; edit
  only your own entries/rows. DECISION_LOG is append-only.
- No order, position, fill, stake size or kelly_fraction change. Demo only. No live-ledger row rewritten. No edit of an
  existing cron line. Read-only GETs against the Kalshi DEMO API are allowed.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- PURPOSE (Hard Rule 12): your claim string names the distance-to-optimum measure this block is FOR (see the PURPOSE line
  under the title and the DISTANCE TO OPTIMUM table at the top of ACTIVE_QUEUE.md). Your handoff fills vision_pillar,
  gap_measure and gap_delta (measured before -> after, with source). If what you find means the block cannot move its
  measure, say so and stop rather than doing adjacent work.
- Every premise below is a claim to verify.
- A fix is RESOLVED only when the RUNNING process contains it (merge != deploy != activation). On disk is not enough.
- Report back: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result | MEASURE MOVED: <measure>
  <before> -> <after> (source) or none | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W63_<n>.md (docs-only push).



WAVE 63.2 - THE MATH: CARRY MLB'S MODELLING MECHANISMS INTO NFL. Repo: eignacio1/prediction-market-bot.
PURPOSE: DEPTH D1 (NFL pre-game model: from "no injury/QB/weather/travel" toward the granularity bar) and D3 0 -> 1 (a
pre-registered NFL challenger ready to log beside the frozen model). Pillar: DEPTH.

WHY
Operator, 2026-10-09: "the translatability should be mechanisms that we spent fucking months on with the MLB and should absolutely
have already been integrated in the NFL - when are we finally getting towards math work?" The NFL arm (EXP-037, 12 cells) runs a
thin frozen model: per its pre-registration, the feature row has no point-in-time injury, QB, weather or travel input. W61.3 found
no NFL challenger beating it (2025 recalibration; 2019-2023 rolling origin). W62.2 (PR #197): at 60 games per cell the first look
(~11-02) can only detect a Brier edge of ~0.038 vs market; the 2025 gap is ~0.008 the other way - so ~91% "keep accruing". A
better MODEL is the only thing that can change that. The MLB stack carries months of mechanisms the NFL model never got.

PART A - The translation map (~35 min; read code and ADRs, run nothing live)
  1. List every modelling mechanism the MLB stack actually uses, each with its file and ADR: e.g. empirical-Bayes shrinkage of
     rolling rates (ADR-0047, K=40), opponent-adjusted rates (ADR-0015), probability temperature/calibration (ADR-0027), Platt,
     recency weighting, venue/park factor, lineup/personnel inputs, the PRF qualitative design (and the fact that the MLB T1
     model as built uses 0 qualitative features, T-597). Verify each is really in the code path, not only in a document.
  2. For each: the NFL analogue, whether a POINT-IN-TIME source exists for 2019-2025 (e.g. weekly injury reports, QB starts,
     stadium roof/weather, rest and travel), and what it would take. Rank by expected information per unit of work. Name what
     is NOT translatable and why. Write 12_EXPLORATORY/NFL_TRANSLATION_MAP.md. Docs push.
PART B - Build and test the deep challenger (~50 min; 12_EXPLORATORY only, charter rules bind)
  3. Pick the top mechanisms from the map that have point-in-time data. FREEZE the feature list, model class and evaluation plan
     in the study's README BEFORE fitting anything (a forking-paths guard): seasons for development vs the held-out evaluation,
     which seasons W61.3 already consumed (2025 recalibration; 2019-2023 rolling origin) and therefore cannot be the sole test.
  4. Fit; evaluate once on the frozen plan vs the frozen EXP-037 model (Brier, game-cluster bootstrap CI) and, where 2025 Kalshi
     mids exist (exp_output/KALSHI_HISTORY, 2025-season tickers only), vs the market. No 2026 rows, no sealed result, ever.
  5. If it beats the frozen model with a CI excluding zero: draft a PROPOSED challenger pre-registration (cells, judged n sized
     with W62.2's measured per-game SD ~0.106, verdict rule, seed, "thinner edge expected" vs market) so it can log beside the
     frozen model from the next NFL week, judged only on data after the operator accepts it. If it does not: say so plainly,
     scoped to what was tested, and name the next mechanism to try.
Results doc: 12_EXPLORATORY/W63_2_nfl_translation_results.md, updated per part.

END OF BLOCK 63.2. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

### 63.3 — The distance table computed, not typed + why our fills lose

```
COMMON RULES - WAVE 63 (read first; they bind this block)
- SIZE: MEDIUM. Target 60 minutes, hard ceiling 90 (operator 2026-10-07). Two parts. If your first estimate for the
  whole block is over 90 minutes, say so in one line, do Part A only, and name Part B as the next undone part. Do not
  re-verify things this prompt states as verified unless your work depends on them.
  After EACH part: push, and update this block's row in 04_EXECUTION/ACTIVE_QUEUE.md (NOW table: Status + one line)
  with a docs-only push. Stop at a pushed boundary (context ~60%, a blocker, or 90 minutes) and write the handoff.
  Never leave work unpushed.
- Runs at any hour. Since #158 (GG-432), a push to main restarts t4-mlb only if it changes a file t4-mlb imports AND
  no MLB game is live; otherwise the restart is skipped and logged. Merge ONLY your own PRs. Read the Deploy job
  summary after each merge and record the t4-mlb decision.
- Decisions in force: DECISION_LOG through 2026-10-08 (incl. the 2026-10-08 expansion directive and four standing
  authorizations), ADR-0070,
  ADR-0071. Standing authorizations: shadow-evaluation cron jobs, NEW lines only (2026-10-02 15:22 PT); Live Terminal deploy +
  pmbot-web-dashboard restart. An authorization exists ONLY as a blockquote line in ACTIVE_QUEUE.md "Needs your
  decision". A table row describing a decision is NOT an authorization.
- Start: CLAUDE.md session-start protocol, brief. Isolated worktree: scripts/new_session_worktree.sh <slug>. Claim with
  scripts/claim_session.sh IMMEDIATELY, before any commit of your own. Real ID range, never TBD. If a GG number
  collides, re-claim; never reuse.
- Before ANY push to main: git diff --name-only origin/main..HEAD lists only the paths you intend.
- PR mergeable_state dirty = almost always SESSION_CLAIMS.md / .last_session_checkpoint: merge origin/main into the
  branch locally, push, wait for CI green, merge.
- Shared docs (GOVERNANCE_GAP_LOG.md, DECISION_LOG.md, ACTIVE_QUEUE.md): fetch + rebase right before each push; edit
  only your own entries/rows. DECISION_LOG is append-only.
- No order, position, fill, stake size or kelly_fraction change. Demo only. No live-ledger row rewritten. No edit of an
  existing cron line. Read-only GETs against the Kalshi DEMO API are allowed.
- The operator never runs plumbing. Nothing you build may depend on him running a command by hand.
- Never bypass a permission control: record the exact command and refusal, hand back.
- PURPOSE (Hard Rule 12): your claim string names the distance-to-optimum measure this block is FOR (see the PURPOSE line
  under the title and the DISTANCE TO OPTIMUM table at the top of ACTIVE_QUEUE.md). Your handoff fills vision_pillar,
  gap_measure and gap_delta (measured before -> after, with source). If what you find means the block cannot move its
  measure, say so and stop rather than doing adjacent work.
- Every premise below is a claim to verify.
- A fix is RESOLVED only when the RUNNING process contains it (merge != deploy != activation). On disk is not enough.
- Report back: Status (DONE / PARTIAL / BLOCKED) | branch @ SHA | PR + CI | one-line result | MEASURE MOVED: <measure>
  <before> -> <after> (source) or none | operator decisions.
  Same into 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W63_<n>.md (docs-only push).



WAVE 63.3 - THE DISTANCE TABLE COMPUTED, NOT TYPED + WHY OUR FILLS LOSE. Repo: eignacio1/prediction-market-bot.
PURPOSE: PLUMBING for Hard Rule 12 (the distance-to-optimum table generated from data, so it cannot drift) and EXECUTION E3
(measure the adverse selection behind "fills lose, non-fills win" in both books, as the design input for demo fills). Pillars:
PLUMBING + EXECUTION.

WHY
Operator, 2026-10-09: "perfection isn't a dream its a protocol." The DISTANCE TO OPTIMUM table at the top of ACTIVE_QUEUE.md is
hand-derived today; hand-derived numbers drift the way the nav docs did. Separately, both books show the same execution signature:
T4M-PROJ fills -$0.26/bet (n=165); T1 MLB fills -$1.50/bet at 28.9% win rate vs 52.1% for orders that never filled (W62.3). Before
the demo-fills ADR is written (authorized: build behind an OFF switch, live only on operator acceptance), we need to know WHY.

PART A - The generator (~45 min)
  1. scripts/distance_to_optimum.py: compute every measure defined in CLAUDE.md, section "What winning looks like" -> "Distance
     to optimum": B1-B4 from MARKET_TYPE_REGISTRY; D1 from a small declared manifest per live pre-game model (factor classes it
     conditions on), checked against each model's metadata/feature list - any mismatch is an error, not a warning; D2 from model
     metadata; D3 from PROPOSED/ACCEPTED challenger pre-registrations in 12_EXPLORATORY; E1-E3 from the fill sidecars
     (logs/t4_mlb_fill_status.jsonl, logs/t1_mlb_fill_status.jsonl) and their ledgers; P1-P3 from the calibration engine's
     output. Every value carries its source path and timestamp. Missing inputs print UNAVAILABLE with the reason - never a guess.
  2. Print it in .claude/hooks/governance_scan.sh (alarm-only) and show it on the Visual Dashboard (/project), current look,
     390px clean. Tests (fixture registry and sidecars). PR; CI green; merge; record the deploy decision. Run it on the VPS and
     paste the table; any value that differs from the hand-derived table in ACTIVE_QUEUE.md is a finding - report it.
  3. scripts/generate_session_artifacts.py: make gap_measure and gap_delta required for handoffs timestamped after Wave 62's
     close (older handoffs still parse). Test both.
PART B - Why the fills lose (~40 min; read-only, demo venue GETs only)
  4. For every CONFIRMED_FILLED position in both books: order type and limit price vs the market (bid/ask/mid) at submit, time
     from submit to fill, and the market's move after the fill (markout at 1, 5, 30 minutes and to settlement) from the price
     archive / candles where they exist. Compare with the never-filled orders at the same horizons. Game-clustered CIs.
  5. Plain-English verdict: is this adverse selection (resting orders filled by better-informed flow), stale pricing, or
     something else - and what order-placement rule the evidence supports (e.g. take vs make, price relative to mid, cancel
     after N seconds). Write it as the design input section of the demo-fills ADR draft (03_DECISIONS, PROPOSED, switch OFF by
     default). Do not build or enable anything; acceptance is the operator's.
Results doc: 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W63_3_distance_generator_fill_markouts_results.md, updated per part.

END OF BLOCK 63.3. If you cannot see this line, the prompt reached you truncated: stop and report it.
```

---

## Sequencing track

Legend: ✅ landed on main · ⚠️ done but NOT on main (branch / PR) · ✂️ cut short by operator · ❌ never ran · ⏳ in flight · ⬜ not started

### ⏳ WAVE 63 — ISSUED 2026-10-09 ~00:45 PT · three MEDIUM blocks · first wave with PURPOSE lines (Hard Rule 12)

| # | Block | PURPOSE | Status | Outcome |
|---|---|---|---|---|
| 63.1 | MLB wired to full for the rest of the postseason | B1, B2; player hits on | ⬜ | — |
| 63.2 | The math: MLB mechanisms into NFL | D1, D3 | ⬜ | — |
| 63.3 | Distance table computed + why fills lose | PLUMBING + E3 | ✅ | #202/#203; ADR-0072 draft, switch OFF |

### ✅ WAVE 62 — CLOSED 2026-10-09 ~08:30 UTC (verified on GitHub) · three MEDIUM blocks · moved: E1–E3 measured for T1 MLB; B, D, P unchanged

| # | Block | Status | Outcome |
|---|---|---|---|
| 62.1 | MLB postseason shadow back up + silent-arm alarm | ✅ code / ⏳ proof | #195/#198/#199: matcher keys on teams + date, cache kickoff; SILENT ARMS in governance scan + dashboards; GG-532 open until the first scheduled write (→ 63.1) |
| 62.2 | Exploratory part 2 | ✅ | #197 (landed by the window after the branch went stale): pre-2026 Kalshi history on the VPS, sha-verified (GG-538); **NFL first look: MDE ~0.038 Brier at n=60 vs ~0.008 plausible → ~91% "keep accruing"**; pre-registered SD 0.07 vs measured 0.106 |
| 62.3 | Gate + T1 fill audit + NBA dry run | ✅ | #196/#200: t4-mlb restarted once, gate in the running process (GG-527 RESOLVED); **T1 MLB 85/485 filled, fills −$1.50/bet, 28.9% vs 52.1% win rate (GG-536)**; NBA flip check + cron-removal script ready (run ≥ 10-21) |

### ✅ WAVE 61 — CLOSED 2026-10-08 ~18:10 PT (verified at `49c6d5a`) · three MEDIUM blocks, all under 60 min

| # | Block | Status | Outcome |
|---|---|---|---|
| 61.1 | GG-527: fills-only evidence + stand-down gate | ✅ code / ⚠️ activation | #191/#193; 166 of 4,220 closed T4 positions filled; T4M-PROJ fills n=165, -$42.17 (≈-$0.26/bet) vs all rows n=3,855, -$121.60; gate merged but t4-mlb not restarted (game live) → GG-527 set back to PARTIALLY RESOLVED; 62.3 restarts |
| 61.2 | Verdict readiness | ✅ | #190: release path did NOT write the REPORT — fixed; NFL 15/60 per cell, first look 11-02 confirmed (~11-09 if a game slips); GG-401 resolved on 510/510 T3 rows; 5 gaps retired; **GG-532: MLB postseason shadow silent since 10-08** |
| 61.3 | Exploratory track | 🟨 A–C merged | #189/#192/#194: fence + isolation test; no NFL challenger beats frozen EXP-037; 2025 market mid at least as good as the model (EXPLORATORY); history store on the Mac only, GG-533 unregistered → 62.2 |

### ✅ WAVE 60 — CLOSED 2026-10-08 · three MEDIUM blocks (60/90-min rule held) · last wave of the Waves 52–60 window

| # | Block | Status | Outcome |
|---|---|---|---|
| 60.1 | Cohort fill truth + Monday guard | ✅ | #185; 107 of 1,952 filled; real fills -0.40/bet; GG-527 to you; GG-228 guarded |
| 60.2 | NBA engine + addenda | ✅ | #186/#188; 12 NBA cells sealed 0/150; addenda applied; GG-529/530 |
| 60.3 | Dashboard truth + gap-log hygiene | ✅ | #184/#187; NBA row, 390px fixed, hook count live; OPEN 130 |

### ✅ WAVE 59 — CLOSED 2026-10-08 ~02:05 UTC · three LARGE blocks (ran long: operator set the 60/90-min rule for Wave 60)

| # | Block | Status | Outcome |
|---|---|---|---|
| 59.1 | The backlog | ✅ | OPEN 176 → 131 re-verified (136 at close); GG-498 resolved (#183) |
| 59.2 | Calibration correctness | ✅ | #178/#181/#182; NFL look 11-02; NHL n unreachable; 1,229/1,229 settlements agree |
| 59.3 | NBA, NHL goalie, ADR-0070 | ✅ | #179/#180; goalie verdict (b); ADR-0070 ACCEPTED; GG-400 resolved |

### ✅ WAVE 58 — CLOSED 2026-10-07 ~02:45 UTC · three LARGE blocks

| # | Block | Status | Outcome |
|---|---|---|---|
| 58.1 | Arms, books, gaps | ⚠️ A–C done, D not run | GG-489, GG-490 resolved; NHL probe job live; NFL book archived; gap triage outstanding |
| 58.2 | NBA arm end to end | ⚠️ built + armed | EXP-038, frozen model, crons; rows from ~10-19 |
| 58.3 | Calibration engine | ✅ | #175; 33 cells, sealed; Calibration section live |

### ✅ WAVE 57 — CLOSED 2026-10-07 ~01:00 UTC · three terminal blocks

| # | Block | Status | Outcome |
|---|---|---|---|
| 57.1 | MLB player-hits dark | ⚠️ partial | #171 features via GH Actions (success); T1 PIPE-05 proof pending; GG-489 unregistered |
| 57.2 | MLB settle + stagger night | ✅ | #170; 128 settled; GG-472, GG-477 resolved |
| 57.3 | Truthful books | ✅ | #172; T4 placements shown; NFL book unmaintained (GG-490) |

### ✅ WAVE 56 — CLOSED 2026-10-06 ~00:30 UTC · three terminal blocks

| # | Block | Status | Outcome |
|---|---|---|---|
| 56.1 | MLB cache via GH Actions + cron stagger | ✅ | #165/#166; GG-482 resolved; stagger applied |
| 56.2 | Live Terminal decision stream + design | ✅ | #167/#169; NOW view live |
| 56.3 | Visual Dashboard ops health + design | ✅ | #168; health strip, ops, books, evidence clocks |

### ✅ WAVE 55 — CLOSED 2026-10-05 ~23:40 UTC · three terminal blocks (+55.3b)

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 55.1 | Land #159 + book 26 positions | ✅ | #159 merged; 26 booked; T1 12.44%, T4 13.45%; GG-440/450 resolved |
| 55.2 | Land #160 + Live Terminal + t4-mlb restart | ✅ | #160 merged; 24 SHADOW live; GG-451 resolved; OOM root cause GG-477 |
| 55.3 | MLB shadow source off statsapi | ⚠️→✅ | ESPN ruled out; 55.3b #164 off-box refresh, 69 MLB T1 rows; GG-482 |

### ✅ WAVE 54 — CLOSED 2026-10-05 ~07:50 UTC · three terminal blocks

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 54.1 | Final landing PR #160 | ✅ | #160 @ `5dbddb2` green + clean; SHADOW 24 on landing |
| 54.2 | Merge #158, VPS proof, arm MLB shadow | ⚠️ partial | #158/#162/#163 merged, t4-mlb never restarted; MLB cells armed, 0 rows (statsapi 406) |
| 54.3 | Kalshi-settlement resolver | ✅ | ADR-0071; #159 @ `2421c0a` green; drawdown after booking T1 12.44%, T4 13.45% |

### ✅ WAVE 53 — CLOSED 2026-10-05 ~04:30 UTC · three terminal blocks · run 10-04 evening PT

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 53.1 | Resolver VPS confirmation (GG-440) | ✅ | 406 on cache-MISS confirmed; 16 cancelled + 10 postponed-game = 0 of 26 settle; #159 @ `c9462a1` CI green |
| 53.2 | Shadow ledger + crontab audit | ✅ | 9 NHL + 12 NFL logging; 12 MLB postseason never armed (GG-453); 8 NFL T2/T3 not SHADOW on landing |
| 53.3 | GG-451 guard into #160 | ⚠️ partial | Guard on `w52/landing` @ `2365cc7`; prompt truncated at D3 — GG-452 + CI check not run; #160 `dirty` on union files |

### ✅ WAVE 52 — CLOSED 2026-10-03 22:00 UTC · one Claude Code session · all 5 done · nothing merged (verified on GitHub)

| # | Block | Status | Outcome |
|---|---|---|---|
| 52.A | Landing prep | ✅ | **PR #160** `w52/landing` @ `6f962400`, CI green, clean: #157 + 51.1 + 51.2 + NHL 9-cell SHADOW flip; suite 3649 passed. Registry on that branch: SHADOW 16. |
| 52.B | GG-432 decision PR | ✅ | **PR #158** (draft): `t4-mlb` restarts only if its import closure changed AND no MLB game live; dashboard always restarts. Yours to decide. |
| 52.C | MLB resolver (GG-440) | ✅ (root cause LIKELY) | **PR #159** (draft): statsapi 406 = Fastly IP block of the VPS (GG-084); ESPN fallback silent. Fix books only Kalshi yes/no, cancelled = skip, `--dry-run`. VPS confirmation = 53.1. |
| 52.D | NHL confirmed goalie (GG-401) | ✅ verdict (c) | Cloud egress refused every NHL source. Probe script on `w52/nhl-goalie-probe`; tonight's measurement = 53.2. |
| 52.E | Live Terminal truth | ✅ | **PR #161** on top of #160: every registry SHADOW cell shown, ledger-only cells labelled "(ledger only)", NHL settled copies no longer double-counted, GG-431 FROZEN label with true age. |
| — | New gaps | — | **GG-451 HIGH** `close_session_claim.sh` pushes HEAD to main (fix = 53.3) · **GG-452 LOW** stale dependency locks. |

### ⚠️ WAVE 51 — all 3 done · folded into 52.A

| # | Block | Status | Touches | Gate |
|---|---|---|---|---|
| 51.1 | Kill-switch truth | ⚠️ done, branch not merged | Verdict (d): realized drawdown **10.60%**, not tripped; dashboard's 26.63% = 10.60% realized + 16.02% stake in 17 positions already settled on Kalshi but never resolved — Kalshi cancelled 16 of them, so realized after booking is ~11–12% (GG-441, GG-450). Dashboard fix on `6cbe62f`. GG-440..442 | Merge in the landing block |
| 51.2 | NHL silent drops | ⚠️ done, branch not merged | SJ/TB/LA/NJ codes were silently dropped; fixed + abstention counters on `f822b6b` | Merge in the landing block |
| 51.3 | PR #157 merge-ready | ✅ done | PR #157 MERGEABLE, CI green (run 37151320465), head `42a0d0d`; 9 NHL cells have rows. **Dirty again by 21:05 UTC** (union-file conflict after main moved) | Re-merge main, then merge in the landing block |
| — | ~~51.3 original: land #157 + NHL SHADOW flip~~ | ❌ withdrawn | — | Needed an idle window; becomes the landing block below |

**Superseded by 52.A:** all three land as one integration PR in an idle window.

### ✅ WAVES 49–50 — CLOSED 2026-10-03 · run inside harness sessions, not from this queue

| # | Block | Status | Outcome |
|---|---|---|---|
| 49.1–49.3 | NFL + MLB shadow code, dashboard fixes, NHL pre-registration | ✅ | On main and auto-deployed by CI (VPS `077558b1`); GG-400..429 registered; crons not armed (cloud can't reach VPS) |
| 50.1 | Process fixes + GG-400..429 triage (T-636) | ⚠️ | PR #157, draft, green but conflicted — 51.3 makes it mergeable |
| 50.2 | Cleanup (T-637) | ✅ | Shadow crons ARMED; tree synced; PR #156 closed; #157 held for live games; GG-430..432 (CI restarts t4-mlb) |

### ✂️ WAVE 48 — CLOSED 2026-10-03

| # | Block | Status | Outcome |
|---|---|---|---|
| 48.1 | Land NFL + MLB shadow (T-631) | ✂️ | Stopped early at operator request; rebased only — landed later by 49.1 |
| 48.2 | Record + VPS jobs (T-632) | ✂️ | Queue + `vps_job.py` landed; detached jobs still unauthorized |
| 48.3 | Dashboards in a real browser (T-621..630) | ⚠️→✅ | Fixes on a branch; landed by 49.2 |

### ✂️ WAVE 47 — CLOSED 2026-10-02 · all three cut at ~2h → the 30-min block rule

| # | Block | Status | Outcome |
|---|---|---|---|
| 47.1 | Candles Gate 2 + Live Terminal v2 (T-615) | ✂️ | **Gate 2 PASSED 7/7** on KXMLBTOTAL; Live Terminal v2 + `/project` deployed; GG-340..356 |
| 47.2 | NFL + MLB postseason shadow (T-608 / EXP-037) | ✂️ | 24 cells built + pre-registered, ADR-0070 PROPOSED; landed later by 49.1 |
| 47.3 | NHL arm (T-607 / EXP-036) | ✅ | **First new arm flying** — model frozen, cron installed, first T3 rows |

### ✅ WAVE 46 — CLOSED 2026-10-02

| # | Block | Status | Outcome |
|---|---|---|---|
| 46.1 | Why candles failed (T-605) | ✅ | Matching rule + sparse candles; Gate 2 pre-registered |
| 46.2 | EXP-034 control arm | ⚠️ | Gate FAIL as run (runner lookback); numbers VOID; branch not merged |
| 46.3 | Shared-tree repair (T-606) | ✅ | Stale lock removed, tree synced, ADR-0067 docs landed |

### ⚠️ WAVE 45 — CLOSED 2026-10-02

| # | Block | Status | Outcome |
|---|---|---|---|
| 45.1 | Candle reconstruction Part 1 (T-604 / EXP-035) | ✅ | Gate FAILED → candle numbers VOID; GG-329..333 |
| 45.2 | EXP-034 setup | ⚠️ | Tolerance frozen; comparison not run |
| 45.3 | Record + dashboard page | ⚠️ | Queue landed; dashboard page running; tree sync blocked |

Waves 10–44: see `ACTIVE_QUEUE_ARCHIVE.md`.

---

## ⬛ OPERATOR DIRECTIVE, 2026-10-08 23:16–23:20 PT — EXPANSION ("we're trying to win"); supersedes calibration-only mode

> *"I'm talking about decision making and execution cadence --- we're leaving money on the table. I feel it's time to
> expand our arms to intake all of this volatility knowing we're still not touching live capital."* And, on the four
> levers the window proposed: *"all 4 of these should fire ... CUS WE'RE TRYING TO FUCKING WIN. Tha's it."*

From Wave 63 the waves build arms, not just plumbing: (1) start more evidence clocks — new pre-registered shadow arms,
least-efficient families first, then game markets; (2) real demo fills on shadow cells (flat stake, ADR); (3) standing
authorizations so waves don't stall on one-off lines; (4) a bigger VPS so the arms don't bring back the OOM crashes.
**Supersedes the 2026-10-06 "calibration mode: do not add cells" rule.** Terminal block size is unchanged (MEDIUM,
60/90) — the operator keeps terminals on strict parameters for context/quality reasons; the expansion is in what the
waves take on and how fast decisions clear, not in block length.
**Guardrails that do NOT loosen** (they are what makes a win real): a pre-registration committed before a cell's first
row; no score read below judged n; no relabel after results; no real capital; kelly_fraction 0; demo venue only.

## ⬛ OPERATOR DIRECTIVE, 2026-10-07 18:58 PT — MEDIUM BLOCKS (amends the LARGE-block directive below)

"You're making some of these tasks far too long. The terminals are coming back stating ETAs upwards of 3 hours which is
ludicrous from any one terminal to take on." Rule from Wave 60: each block is two parts, ~60-minute target, 90-minute
hard ceiling; a block whose own estimate exceeds 90 minutes does Part A only and hands Part B on. Still three blocks
per wave, still substantive - sized to finish, not to impress.

## ⬛ OPERATOR DIRECTIVE, 2026-10-06 18:10 PT — LARGE BLOCKS (supersedes the 30-minute rule below)

> *"Remember - the terminals can handle plenty of weight. You can expand the workload for each block so that we're not
> spending each wave back and forth making such incremental build progress... give each block enough that they can handle."*

Blocks are multi-part. Each part is pushed and recorded in the queue before the next, so a cut never strands work.
Still: three blocks per wave, disjoint surfaces, never a block that can't run now.

## OPERATOR DIRECTIVE, 2026-10-02 17:03 PT — TIME-BOUNDED BLOCKS (SUPERSEDED 2026-10-06)

> *"We added so many extra tasks to the windows that it was about to take over 2+ hours for each window to
> complete so I cut it short each way. I'm not letting windows run for hours on end — if there's a task that'll
> take that long, don't place it."*

> And minutes later, when a wave was first sized at ~75 minutes a block: *"Even 75 minutes is way too long —
> none of these tasks better take 75 minutes."*

**Every block is sized at about 30 minutes, hard stop at 45** — at the nearest pushed boundary, with a handoff
that names where the next session resumes. Scope is cut to fit the clock, never the reverse: one job per block,
done completely. Budget includes the one full test-suite run (~11 minutes) a block landing `src/` code needs.

**What does not belong in a window:** anything whose wall time is set by waiting rather than working. Those run
unattended on the VPS under their own authorization, and a later block reads what they produced.

---

## ⬛ WHAT 50.2 FOUND (and what this window found checking it)

- **NFL + MLB postseason shadow crons are armed.** The 33 pre-game cells now log unattended. Nothing restarted. **[Corrected 2026-10-05 by 53.2: only the 12 NFL cells were armed; MLB postseason never was — GG-453.]**
- **Who restarted t4-mlb: CI.** `deploy.yml` restarts `t4-mlb` and the dashboard on every code push to main (GG-432).
  That contradicts the standing "never restart t4-mlb" rule; the policy is yours (Needs your decision, first row).
- **The dashboard's stale panel and its 26.63% drawdown are one file** (strategic window, arithmetic):
  `paper_portfolio_mlb.json`, last written 2026-08-06 00:05Z (+58d20h = the panel's "read 58d20h ago", GG-431);
  $733.75 of $1,000 = 26.63%, past the 20% permanent kill switch.
- **The two drawdowns are not the same quantity** (strategic window, code read — 51.1 verifies): the T1 runner feeds
  the kill switch *realized* loss only (`run_mlb_paper_trade.py:670-671`); the dashboard shows
  `(initial − bankroll) / initial` (`web_dashboard.py:761`, `:1498`), which also counts stake locked in ~17 positions
  open since August. So the tile may be alarming on money that is tied up, not lost — or the kill switch may have
  missed a real breach. No capital either way (kelly 0.0).
- **PR #157 is not mergeable as it stands** (GitHub: `mergeable_state = dirty`) — 50.2's report did not say so. 51.3 makes it mergeable; it lands in a later idle window.

---

## Read this first (standing)

- **Protocol (operator, 2026-10-04):** every time this file changes, the strategic window loads it into the chat as a file card. He never has to dig through folders for it.

- **North star (2026-10-09):** CLAUDE.md § "What winning looks like" — four pillars, BREADTH / DEPTH / EXECUTION / PROOF.
  Every block's report and handoff names the pillar it moved (`vision_pillar:`; PLUMBING is a valid answer). The window
  updates the pillar scoreboard at every wave close and flags two pillar-less waves in a row.
- **PURPOSE before work (2026-10-09).** Every block prompt carries, right under its title, a `PURPOSE:` line naming the
  distance-to-optimum measure it moves (B1..P3, or PLUMBING) and the change it expects; its report and handoff state the
  measured change (`gap_measure:` / `gap_delta:` in the session-meta block). A terminal that cannot say what its task is
  for stops and asks before working.
- **Three blocks per wave. Not four.** Operator directive 2026-09-15.
- **Blocks are LARGE and multi-part (operator 2026-10-06)** — each part pushed and recorded before the next. Waiting is still not work.
- **Deliverable 0 in every block: confirm your base** (`git fetch`; work from current `origin/main`).
- **Claim IDs at run time and re-verify after ANY release or retry** (GG-322). Never "TBD".
- **A premise written in a block is a claim to verify, not a fact.** Including every number in this file.
- **Never bypass, disable, or work around a permission control.** Record the exact command and refusal text, then hand back.
- **Pre-register before scoring.** Frozen pre-registrations stay frozen. No scoring before a cell's judged n.
- **SHADOW means evaluate and log.** No order, position, paper fill, stake or `kelly_fraction` change.
- **A merge is a deployment here, and a code deployment restarts `t4-mlb`** (deploy.yml, GG-432). Until the operator
  decides GG-432: code reaches main only when no MLB game is live (Stats API shows none In Progress, T4 cycle log idle
  > 15 min, no first pitch within 60 min). Docs-only pushes are always fine.
- **Paper and shadow work is plumbing** (operator's standing framing). Real capital is his.
- **The Live Terminal and the project view move with the bot.** A block that adds a cell, ledger, source or verdict makes it visible.
- Register-and-stop on any gap outside scope (Hard Rule 11).

---

## THE ARC — renumbered (49-50 went to landing and cleanup)

| Wave | The question it answers |
|---|---|
| **51** | *Is what the operator sees true, and is everything built actually landed?* Kill switch vs dashboard; NHL silent drops; #157 made mergeable. |
| **52** | **NHL scoring readiness** — confirmed-goalie source at T3 (GG-401), pre-registered spread cutoff (GG-404), clustered scorer (GG-407), matinee coverage (GG-405). **NBA (opens 10-20)** in ~30-minute blocks. Merge whatever 51 left on branches. |
| **53** | First looks as cells reach judged n (NFL first: 60 games ≈ late October). A **flat-stake paper ADR** for SHADOW cells — yours to accept. |
| **later** | In-play arms only where C5 / ADR-0068 shows speed is measured. Sizing only for a cell that cleared its gate and its capacity question. |

What should reorder this, and what should stop it:

- **A shadow path that reaches an order, position or sizing function** stops everything shadow until fixed.
- **A dashboard that shows a number it did not read live, or a number that is not what its label says** is a defect of the same severity.
- **A kill switch that should have fired and did not** (51.1 verdict c) stops everything until understood.
- **Per cell, the pre-registered rules decide.** RULED_OUT at judged n is a completed cell.
- **Board-survey stop condition — pre-registered in Wave 45, carried unchanged.**

---

## Queued next — not yet fired (refreshed 2026-10-08 by the incoming window; dated items wait for their date)

- **Built in 63.3 — the distance-to-optimum generator:** compute every measure in the table above from the registry,
  pre-registrations, model metadata, fill sidecars and calibration-engine output; print it in the governance scan, show it on the
  Visual Dashboard, and make `gap_measure`/`gap_delta` required in the session-meta block once Wave 62 has closed.
- **On/after 10-21 — NBA flip:** `scripts/w59_3_nba_flip_check.py` prints the `promote_cell_status` lines; flip once valid
  regular-season rows exist. Same block or next: remove the NBA preseason cron line after 10-20 (added under the new-line
  authorization; removal of a line we added).
- **After Mon 10-12 14:20 UTC — first real run of the GG-228 guard:** read `band_monitor_cron.log` for a GG-228 WARNING /
  `rebuild_<UTC>.jsonl`.
- **After the World Series — T4M-PROJ registry flip to DARK** (GG-527 (c), authorized) + the t4-mlb restart if 62.3 could
  not do it (authorized) + **T1 MLB winter posture** (your call).
- **The day an NFL cell crosses n (~11-02):** first scored look, per 61.2's runbook.
- **Before 2027-01-31 — GG-529:** define EXP-038's date-triggered second look (your call; window will propose).
- **Exploratory track, Wave 63+:** NFL slate (b) and (a) need a held-out season, not 2025 again; NBA challenger before its
  first look. 61.1 handed back: local governance scan can't see the VPS fill sidecar (SSH mirror denied) - VPS-side is fine.
- Carried, unscheduled: board survey (needs the detached-VPS-jobs line) · Step 4 season-awareness (GG-343..345) · PIPE-08
  406s · T3 disposition (MISFILED) · branch estate · stale PRs #133/#144/#146/#149 · test-suite runtime.

---

## Needs your decision

> **OPERATOR DIRECTIVE (2026-10-09 00:14 PT):** "I want to have MLB wired to full cus of the limited games left - the
> translatebility should be mechanisms that we spent fucking months on with the MLB and should absolutely have already been
> integrated in the NFL - when are we finally getting towards math work?" Used by 63.1 (MLB coverage) and 63.2 (NFL depth).

> **AUTHORIZATION - STANDING: NEW PRE-REGISTERED SHADOW ARMS (operator, 2026-10-08 23:20 PT: "all 4 of these should
> fire").** Covers: building new SHADOW cells for any sport, market family and band, and flipping them NOT_IMPLEMENTED ->
> SHADOW, PROVIDED the cell's pre-registration (comparisons, judged n, verdict rule, seed, and the expected edge
> direction - "thinner edge expected" for efficient game markets) is committed to main before the cell's first row;
> plus the NEW cron lines those arms need, off :00/:30 and the staggered minutes, in their own marked block. Not
> covered: editing or removing an existing cron line; promotion to ACTIVE; any order or stake (see the demo-stake line).

> **AUTHORIZATION - STANDING: IDLE-WINDOW SERVICE RESTARTS (operator, 2026-10-08 23:20 PT: "all 4 of these should
> fire").** Covers: restarting t4-mlb, pmbot-web-dashboard or a shadow service to load code already merged to main,
> only while no MLB game is live (none In Progress, T4 cycle log idle > 15 min, no first pitch within 60 min), as often
> as needed, each restart recorded with proof the running process has the code. Not covered: restarts during a live
> game; any config, unit-file or code change made on the box.

> **AUTHORIZATION - DEMO FLAT STAKES ON SHADOW CELLS: BUILD (operator, 2026-10-08 23:20 PT: "all 4 of these should
> fire").** Covers: drafting the ADR (flat stake per order, demo venue only, fills classified by the 61.1 sidecar,
> per-cell fill evidence kept separate from calibration evidence, kelly 0 unchanged) and building it behind a switch
> that is OFF by default, with tests. Not covered: turning the switch on. It goes on when the operator ACCEPTS the ADR -
> one line from him at wave close; that acceptance is the only remaining gate.

> **AUTHORIZATION - VPS RESIZE (operator, 2026-10-08 23:20 PT: "all 4 of these should fire").** Covers: resizing the
> droplet to at most 4 GB RAM (same region, same plan family), in a window with no live game and no shadow run due
> within 30 min, with a snapshot or backup first and a full Step 4 health check before and after. If no DigitalOcean
> credential is available to the terminal, the block prepares everything and the window hands the operator the single
> console step. Not covered: region or plan-family change, deleting snapshots, any other paid service.

> **AUTHORIZATION - T4-MLB RESTART TO LOAD THE GG-527 GATE (operator, 2026-10-08 ~18:25 PT: "Yes, once (Recommended)").**
> Covers: ONE `systemctl restart t4-mlb`, only while no MLB game is live (none In Progress, T4 cycle log idle > 15
> min, no first pitch within 60 min), to load the stake_stood_down gate merged in #193. If a game is live when the
> block runs, it does not wait: the post-World-Series block does the restart instead. Not covered: any other
> service, any second restart, any code or config change. Used by 62.3 (fallback: post-World-Series block).

> **AUTHORIZATION - GG-527 T4M-PROJ COHORT (operator, 2026-10-08 ~17:14 PT, choosing the window's recommendation: "(b)+(c) (Recommended)").**
> Covers: (b) every T4M-PROJ row (epoch-12 and later) counts as model-calibration evidence only; G6 sample adequacy and
> any execution or P&L claim for T4M-PROJ count CONFIRMED_FILLED rows only - computed and labelled that way in the power
> calc, governance scan, band monitor and both dashboards, from a sidecar fill-status file (no live-ledger row
> rewritten). (c) T4M-PROJ places no paper stake for any MLB game after the 2026 World Series: a code gate in the T4
> placement path, default off, re-enabled only by a new operator decision; evaluations keep logging; and, once the
> World Series has ended, T4M-PROJ's registry status goes to DARK with this decision as the reason (a later block).
> Not covered: any kelly_fraction or stake-size change, any other band or cell, T1 MLB winter posture, deleting or
> rewriting any row. Used by 61.1.

> **AUTHORIZATION - PRE-REGISTRATION ADDENDA (operator, 2026-10-07 19:03 PT: "Yes proceed with both recommendations").**
> Covers: appending four dated addenda (original text untouched), before any judged data exists: (1) EXP-037 "earliest
> 60" ordered by (start_time_utc, game_key); (2) EXP-036 bootstrap seed 20261002; (3) EXP-036 goalie: projected starter
> (last start) at every band, T3 included, rows flagged confirmed=False - W59.3 Part B text verbatim; (4) MLB: the
> climatology comparison is unavailable (no p_clim on MLB settled rows), stated with the reason. Not covered: any other
> parameter, judged n, verdict rule or look. Used by 60.2 Part B.

> **DECISION - NHL JUDGED N (operator, 2026-10-07 19:03 PT): keep EXP-036 as written** (judged n 2,473; NHL stays
> PRELIMINARY in 2026-27; the 500-game climatology check still applies). Recorded on GG-514 by 60.2 Part B.

> **AUTHORIZATION - FEATURES CRON REMOVAL (operator, 2026-10-06 18:16 PT: "Yes permission granted").** Covers:
> commenting out the ONE VPS cron line that runs `scripts/generate_mlb_features.py` at 22:30 UTC (it overwrites the
> GitHub-built feature CSV nightly with degraded output), crontab backed up first, mirrored into `deploy/`. Not
> covered: any other line. Used by 58.1 Part A5.

> **AUTHORIZATION - GG-477 CRON STAGGER (operator, 2026-10-05 16:41 PT: "Yes").** Covers: changing ONLY the minute
> field of the existing cron lines listed in `scripts/ops/gg477_cron_stagger.py` RULES, crontab backed up first, and
> mirroring those minutes into `deploy/` cron files. Not covered: any command, hour or other line. Used by 56.2.

> **OPERATOR DIRECTIVE (2026-10-05 16:41 PT):** "MLB can't go dark while games are going on." The MLB postseason
> shadow arms keep logging every game day; nothing in their data path may depend on a manual step.

> **NAMES (operator, 2026-10-05):** **Visual Dashboard** = the operational review of the whole bot (`/project`). "ERP"
> describes its purpose, not a rebuild — he likes its current look; enhance it, keep the style. **Live Terminal** = what
> the bot is actually placing / evaluating, live, full black (`/`).


GG-432, GG-440, GG-450 and postponed games were decided 2026-10-04 (DECISION_LOG 2026-10-05). Arming the MLB postseason shadow cells needs no line — the 2026-10-02 shadow-cron authorization covers new lines.

> **AUTHORIZATION — SHADOW-EVALUATION CRON JOBS (operator, 2026-10-02 15:22 PT: "Yes permission granted").** Unchanged;
> used by 50.2. Not covered: any order, position, fill, stake or `kelly_fraction` change; any EXISTING cron line.

> **AUTHORIZATION — LIVE TERMINAL DEPLOY AND RESTART (operator, 2026-10-02 15:44 PT).** Standing. Covers
> `pmbot-web-dashboard` only. Note: under today's `deploy.yml`, any code merge also restarts `t4-mlb` — see GG-432 below.

| Item | Plain English | What it costs while it waits |
|---|---|---|
| **Expansion (win mode)** | ✅ **DIRECTED 2026-10-08 23:20 PT: all four levers** — directive section + four lines above; Wave 63 is built on it. Demo stakes go live only on your ADR acceptance (one line). | — |
| **NEW — T1 MLB book counting (GG-536)** | 62.3 found the T1 MLB book shows the same pattern as T4M-PROJ: only 85 of 485 positions filled; fills lost −$1.50/bet at a 28.9% win rate, while non-fills "won" 52.1%. GG-527's decision covered T4M-PROJ only. **Window recommends the same rule for T1:** rows are a calibration record; any execution or G6 claim counts real fills only. | Until decided, T1's paper P&L can be read as execution evidence. |
| **T4M-PROJ cohort (GG-527)** | ✅ **DECIDED 2026-10-08 ~17:14 PT: (b)+(c)** — built by 61.1; gate activation by 62.3. | — |
| **t4-mlb restart for the gate** | ✅ **AUTHORIZED 2026-10-08 ~18:25 PT: once, no live game** — line above; 62.3. | — |
| **NEW — EXP-038 second look (GG-529)** | The NBA pre-registration says "n=400 or 2027-01-31, whichever first" but never says what is scored on the date. Needs a definition before 2027-01-31; the engine scores only n=150/400 until then. | Nothing before January. |
| **Pre-registration addenda** | ✅ **DECIDED 2026-10-07 19:03 PT: yes** — authorization line above; 60.2 Part B applies them. | — |
| **NHL judged n (GG-514)** | ✅ **DECIDED 2026-10-07 19:03 PT: keep as written** — NHL PRELIMINARY all 2026-27. | — |
| **GG-432** | ✅ **DECIDED 2026-10-04: option (a), PR #158** — merged in 54.2. | — |
| **GG-450** | ✅ **DECIDED 2026-10-04:** booked at Kalshi settlement value, flagged cancelled, excluded from G6 + calibration — built in 54.3. | — |
| **GG-440** | ✅ **DECIDED 2026-10-04:** Kalshi settlement is the resolution source; statsapi/ESPN cross-check only — ADR + code in 54.3. | — |
| **NHL goalie timing (GG-401)** | Pulled from Wave 53 (timing-bound). The measurement — run `scripts/nhl_goalie_source_probe.py` at ~60/30/15 min before one slate's puck drop — fits a detached read-only VPS job (row below) instead of a terminal. | No NHL T3 score may be read. |
| **Postponed games** | ✅ **DECIDED 2026-10-04:** resolve on Kalshi's result — in 54.3. | — |
| **GG-477 cron stagger** | ✅ **AUTHORIZED 2026-10-05** — line above; 56.2 applies it. | — |
| **VPS 22:30 UTC features cron** | ✅ **AUTHORIZED 2026-10-06** — line above; 58.1 A5 removes it. | — |
| **NEW — NFL game-market paper book (GG-490)** | Old NFL paper book: no writer, no resolver, ~820 open positions on past games. The live NFL work is the EXP-037 shadow arm, which is healthy. **Recommend: retire it** — book its positions once under ADR-0071 (Kalshi settlement, backup + dry-run first), then freeze it and label it archived on both dashboards. | The Visual Dashboard keeps showing a stale book with ~820 open positions. |
| **ADR-0070 scope (GG-400)** | ✅ **DECIDED 2026-10-07:** widen to NHL + NBA, then accept — 59.3. | — |
| **NBA preseason rows** | ✅ **DECIDED 2026-10-07:** default kept — logged, labelled, excluded from judged n. | — |
| **Detached read-only VPS jobs** | Long read-only work runs unattended on the VPS through `scripts/vps_job.py`. A line naming *detached read-only VPS jobs* unlocks it. | The board survey and NFL/NHL market backtests stay blocked. |
| **T1 MLB postseason flag** | Adds `--include-postseason` to the existing T1 MLB cron line. Edits an existing line, so the shadow authorization does not cover it. | T1 player-hits stays blind for the rest of the playoffs. |
| **EXP-034** | Run its ≥2.5-hour sampler as a VPS job, or **park** it (window's recommendation). | Nothing urgent. |
| **GG-347, remaining half** | The SSH poller from 73.231.159.158 — yours? | An unexplained actor on the VPS. |
| **MLB winter** | After the World Series: stand T1/T4 MLB down, or idle all winter? | Daily false alarms in Step 4 until spring. |
| **Settlement + depth capture schedules · Polymarket KYC · odds feed · provenance allowlist · APR-0035 · ADR-0068 · ADR-0067 · 39.3 triage · ADR-0063/0064/0065/0066 · APR-0034/0036** | Unchanged. | — |

---

## DO NOT — standing

- **Never bypass, disable, or work around a permission control.** Record the exact command and the exact refusal text, then hand back. An approval authorizes a CHANGE, never a bypass.
- **Submit no order against the production Kalshi account or with real funds. Demo only, always.**
- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Push code to main while an MLB game is live (until GG-432 is decided).
- Promote `assert_ledger_invariants.py` to `--strict`.
- Repair or backfill a DERIVED field without establishing provenance first (GG-228).
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport, band or market family on one finding.
- Modify or re-time an existing price-capture window. Additive sibling writers only.
- Rotate, truncate or clear a VPS log or journal.
- Restart a production service without a scoped, written authorization. Do not hand-pull on the VPS.
- Add or edit a cron entry without explicit operator authorization.
- Pre-assign T-/GG-/ADR- numbers. Claim at run time; verify uniqueness across `git log --all`.
- Report a live fix RESOLVED without proving the RUNNING process contains it.
- Manufacture a position, a row, a cohort member, a price, a fill, or a final score.
- Delete, truncate or rewrite a live pool file. Work on copies.
- Weaken a predicate, or widen an allowlist without citation, to raise a count.
- Modify `p_hits_gte_threshold` — 1,694 rows' provenance citation rests on its source hash.
