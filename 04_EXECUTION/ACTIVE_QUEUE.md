# Active queue — the only prompt file to read

> **RULE: prompt text here is ONLY for blocks firing now.** Closed prompts move verbatim to
> `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`; closed waves keep their ROWS in the Sequencing track below.

**Verified against:** `origin/main = edb3138` (2026-10-08, strategic window handoff). PRs, CI and results docs read from GitHub; VPS facts are the Wave 60 terminals' reports.

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-530** · **T-746** · **ADR-0071** · **EXP-038** · ADR-0070 ACCEPTED · gap log **130 OPEN** (parity 157 = 157, no duplicate ids) |
| Registry (104 cells) | ACTIVE 1 (T4M-PROJ) · SHADOW 24 (3 MLB player-hits, 12 NFL, 9 NHL) · BLOCKED 2 · DARK 1 · NOT_IMPLEMENTED 76 (incl. 12 NBA, flip ~10-21). MLB postseason game cells log + settle but are not registered SHADOW. Counted from `MARKET_TYPE_REGISTRY` at `edb3138`. |
| Capital | **$0 real.** `kelly_fraction = 0.0` on every operating band; **T4M-PROJ places flat paper measurement stakes of min($1, max_contracts x price)** (ADR-0050). Demo venue only. SHADOW = evaluate and log. |
| Shadow arms | **NFL** 12 cells logging, first look projected **2026-11-02**. **MLB postseason** armed and logging (judged n starts 2027). **NHL** 9 cells logging; judged n unreachable this season (GG-514); no NHL T3 score may be read (GG-401). **NBA** preseason rows to a separate labelled ledger; regular season 10-20, cells flip ~10-21. |
| Open PRs | Only stale ones from Waves 30-34 (#133, #144, #146, #149). Nothing from Waves 52-59 is waiting. |
| VPS | Last deploy `056428f` (#188), 2026-10-08 02:43 UTC, success; t4-mlb not restarted by Wave 60 (no T4 import changed). |
| Deploy | **GG-432 resolved (#158, 2026-10-05):** a push restarts `t4-mlb` only if it changes a file t4-mlb imports AND no MLB game is live; otherwise the restart is skipped and logged. Dashboard restarts every deploy. Code can land at any hour. |

---

## 🌲 RUNNING SITREP — the forest (kept by every strategic window; last window: Waves 52–60, 2026-10-03 → 10-08)

*Updated by the strategic window at every wave close and at every handoff. Last update: Wave 60 closed + handoff, 2026-10-08.*

**Bottom line.** The plumbing is now sound. Code lands at any hour without killing live services, MLB data no longer
depends on a blocked source, every resolved bet books from Kalshi's own settlement (1,229 of 1,229 match), and four
sports log shadow forecasts. **We still have no verdict that the model beats the market anywhere.** Wave 60 settled
what the only ACTIVE cell's sample is: **94.5% of T4M-PROJ's 1,952 rows were never filled.** The 107 real fills lose
$0.40 a bet. So T4M-PROJ is a calibration record, not trading evidence (your call, GG-527). The first honest
pre-registered edge verdict is **NFL, ~2026-11-02**.

### Scoreboard

| Measure | Start of window (10-03) | Now (10-08) |
|---|---|---|
| Real capital | $0 | $0 — demo only, Kelly 0 everywhere |
| Cells (registry) | 92 · ACTIVE 1 · SHADOW 16 on an unmerged branch | 104 · ACTIVE 1 · SHADOW 24 on main · 12 NBA ready to flip ~10-21 · MLB postseason logging |
| Sports logging forecasts | NFL, NHL (partly) | NFL, NHL, MLB postseason, NBA (preseason labelled + excluded) |
| Cells at a scored look | 0 | 0 — engine sealed below each cell's pre-registered n |
| Books truthful? | 26 MLB positions stuck; NFL book orphaned | All booked from Kalshi (ADR-0071); NFL book archived; **T4M-PROJ fills now known: 107 of 1,952** |
| Open gaps | 176, many stale | **130**, every one re-verified with dated evidence; hook shows the live count |
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
| **Governance** | 58–60 | Gap log 176 → 130, all re-verified; deploy/ mirrors the live crontab; ADR-0070 accepted; window handoff is now a command (`/strategic-handoff`). |

### Against the north star — does the model know something the market doesn't?

| Arm | Status | When a verdict is possible |
|---|---|---|
| **T4M-PROJ** (MLB player hits, ACTIVE) | All rows -0.053/bet (CI spans 0); **real fills -0.40/bet (CI excludes 0), n=107**; latency thesis not supported (T-569) | Execution evidence says no. What the cohort counts as is GG-527 (your call). |
| **NFL** (12 SHADOW) | Logging; 15 settled games per cell at last count | First look **~11-02** (60 games/cell) — may slip; rests on one week of coverage |
| **NHL** (9 SHADOW) | Logging; T3 rows now carry the projected-goalie flag (new rows) | PRELIMINARY all 2026-27 (accepted); base-rate check at 500 games |
| **NBA** (12 cells) | Sealed 0/150; opening night 10-20 | Cells flip ~10-21; first look at 150 games/cell |
| **MLB** game markets | Postseason logging, never scored | 2027 regular season |

### Calendar ahead

| Date | What happens |
|---|---|
| Mon 10-12 14:20 UTC | Weekly T4 resolved-ledger rebuild — first live test of the overwrite guard |
| 10-20 / 10-21 | NBA opening night; NBA cells flip to SHADOW once valid rows exist |
| ~11-02 | NFL first scored look — the project's first pre-registered edge verdict |
| World Series end | MLB winter posture (T1/T4 down or idle) — ties into GG-527 |
| before 2027-01-31 | Define EXP-038's date-triggered second look (GG-529) |

### Your open calls
**T4M-PROJ cohort (GG-527) — the important one** · MLB winter posture · T4M-PROJ band placement (GG-320) · a P&L
gate that can be reached (GG-285) · approval path for self-modifying scripts (GG-289) · kill switch to count
unresolved stake (GG-441) · the unexplained SSH poller (GG-347) · T1 MLB postseason flag · EXP-038 second look
(GG-529, January) · EXP-034 (park recommended).

---

## ⬛ NOW — Wave 61 · to be written by the incoming strategic window

The window that ran Waves 52–60 handed off on 2026-10-08 (operational doc: `04_EXECUTION/STRATEGIC_WINDOW_CARRY_FORWARD.md`;
paste-in: `04_EXECUTION/NEW_WINDOW_PASTE_IN.md`; handoff procedure: `.claude/commands/strategic-handoff.md`).
No prompt blocks are live. The incoming window verifies state, then writes Wave 61 here with its blocks inside.

### Wave 60 results (closed 2026-10-08, verified on GitHub at `edb3138`)

| Block | Status | Result |
|---|---|---|
| **60.1** Is the only ACTIVE cohort real? + Monday guard | ✅ **DONE** | #185. Demo venue's full fill history (back to 05-19, past the cohort start) joined to all 1,952 epoch-12 T4M-PROJ rows: **107 filled (5.5%), 1,845 never filled, 0 unverifiable.** P&L/bet: all rows **-0.053** (CI -0.148..+0.043); **real fills -0.403 (CI -0.650..-0.156, 41 games)**; paper-only -0.032. GG-300 RESOLVED → **GG-527 HIGH OPEN: what the cohort counts as is your call.** GG-228 guard live on the VPS: the rebuild never overwrites a changed or removed row; first real run Mon 10-12 14:20 UTC. |
| **60.2** NBA engine + addenda | ✅ **DONE** | #186: NBA under EXP-038 (looks 150/400, seed 20261006, preseason never counted); 12 NBA cells listed SEALED 0/150 on the VPS. Addenda appended to EXP-036/037 as authorized. GG-510/511/512/513 RESOLVED, GG-514 ACCEPTED UNCERTAINTY. Found live NHL T3 rows carried no confirmed flag → GG-530, fixed same day by #188 (new rows only). **GG-401 still OPEN** — closable once new T3 rows show the flag. New: GG-529 (EXP-038 date-triggered second look undefined; needed before 2027-01-31). |
| **60.3** Dashboard truth + gap-log hygiene | ✅ **DONE** | #184: Live Terminal always shows the NBA row ("no data - awaiting"); no 390px scroll on `/project` (verified live, 0 console errors). #187: session-start hook now prints the live OPEN count (was stale 176 — read the main tree, not the worktree; GG-426); generated Gaps-by-Arm index; severity parser fixed. GG-515/525/426 RESOLVED. **OPEN 136 → 130** at close. |

---

## Sequencing track

Legend: ✅ landed on main · ⚠️ done but NOT on main (branch / PR) · ✂️ cut short by operator · ❌ never ran · ⏳ in flight · ⬜ not started

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

## Queued next — not yet fired

**Landing block** — merge 52.A's PR (then 52.E's) when no MLB game is live; idle probe, Deploy, VPS HEAD, services, Live Terminal checks. **Terminal block for Wave 52's VPS-PENDING items** (NHL rows re-check, resolver VPS repro + ledger dry run, live crontab). **First NFL T1 shadow run** 5:05 PM PT tonight — read its output in that terminal block, not by watching. **NHL scoring readiness** (GG-401, GG-404, GG-405, GG-407) — before any NHL score is read. **NBA game markets.** **The board
survey** (after the history store completes — needs the detached-VPS-jobs line). **MLB winter disposition** after the World
Series. **Step 4 season-awareness** (GG-343..345). **PIPE-08 406s.** **T4M-PROJ and T3 disposition** (both MISFILED). **The
branch estate** (33+ unmerged). **Aged open paper positions** (9 T4, ~17 T1 — 51.1 reports on the T1 set). **Test-suite runtime.**

---

## Needs your decision

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
| **NEW — T4M-PROJ cohort (GG-527)** | 94.5% of the only ACTIVE cell's sample never filled on the demo venue. The 107 that did fill lose **$0.40/bet, CI excluding zero** — about 8x worse than the paper rows, the classic sign that resting orders fill mainly when the price is about to go against them. Options: (a) G6 counts real fills only (T4M-PROJ is then a demonstrated loser on n=107); (b) keep the paper rows as *model calibration* evidence but never as *execution* evidence — G6 needs fills; (c) stand T4M-PROJ down for the winter with MLB. **Window recommends (b) + (c):** keep the 1,952 rows as a calibration record, require fills for any execution claim, and stop placing T4M-PROJ paper stakes after the World Series. | Every day it runs adds paper rows that can't count toward G6. |
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
