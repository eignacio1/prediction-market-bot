# Active queue — the only prompt file to read

> **▶ WAVE 129 READY TO PASTE - seven blocks (Sonnet): 129.1 NHL depth on in shadow, 129.2 the PAM-3 x C2 props challenger, 129.3 MLB 2027 frozen before its first row, 129.4 PAM point-in-time state tables, 129.5 one D6 number + hypothesis registry, 129.6 NFL in-play feed, 129.7 NHL in-play feed (6-7 added 11-25 16:09 PT). Wave 128 closed. Three installs await approval. Window handoff after Wave 130.**

## 🔥 GAP BURNER — standing block, always here (paste into its own terminal any time, alongside any wave)

Target: OPEN gaps **174 (2026-11-19) → 150** (operator 11-17 21:17 PT: "250+ gaps is ridiculously high and we need to get it to 150").
It owns the status lines of existing gaps; wave blocks only append new ones. The window keeps this section at the top of the file.

```
GAP BURNER - STANDING - BURN OPEN GOVERNANCE GAPS TOWARD 150 - MODEL: Sonnet

FIRST: run `git fetch origin && git show origin/main:.claude/commands/gap-agent.md` and follow it (it binds this block: the never-list,
the classes, the state files 03_DECISIONS/GG_BURNDOWN.md and GG_AGENT_STATE.md, the stop rule). Read it from origin/main; do not
assume the local copy is current. Then read the newest 04_EXECUTION/WAVE_BLOCKS/COMMON_RULES_W*.md for which files the running wave
owns - never edit those files.

TARGET: OPEN gaps (`grep -cE "^\*\*Status:\*\* OPEN\b" 03_DECISIONS/GOVERNANCE_GAP_LOG.md`) down to 150 in this session.
BULK MODE (operator 2026-11-17 21:47 PT: 2 a tick is far too slow). For this session these pace rules replace gap-agent.md's; its
never-list still binds.
1) Bucket ALL OPEN gaps in one scripted pass: for every gap, extract the files, scripts, PRs, tasks and GG ids it names, and check them
   mechanically (exists, merged, an ancestor of box HEAD, duplicate). Write one table in GG_BURNDOWN.md: id, severity, age, class,
   one-line evidence. Classes: A fixed + evidence / B duplicate / D premise gone (names something that no longer exists, superseded by
   a later ADR or by the doctrine, or a one-season item the season has passed) / C small fix / L large / W owned by the running wave /
   O watch.
2) Close every A, B and D in batches of 20 per commit, each with its evidence line.
3) Then class C: up to 10 per tick.
4) L goes on the "Large (for waves)" list with a size; never start one.
If you stall above 150, report the count per class so the window can route the rest.

COEXISTENCE: a wave runs alongside. You own the status lines of EXISTING gaps; blocks append new ones. `git pull --rebase` right before
every push of the gap log; never rewrite another session's text; run scripts/lib/gg_id_uniqueness_check.py before pushing.

Run as `/loop` ticks if the terminal has it; otherwise tick back to back. Stop per the stop rule. Report each tick: OPEN before -> after,
closed by class, and the Large list.
END OF GAP BURNER
```

> **RULE: prompt text here is ONLY for blocks firing now.** Closed prompts move verbatim to
> `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md`; closed waves keep their ROWS in the Sequencing track below.

**Verified against:** `origin/main` at the Wave 101 close (2026-11-04 ~22:10 PT). Box facts from the box bridge, 2026-11-05 05:48Z (`04_EXECUTION/BOX_TASKS/results/20261105T054745Z_*`). **What is in scope, in order: the rolling backlog** (`04_EXECUTION/ROLLING_BACKLOG.md`).

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | see the gap log and SESSION_CLAIMS for the live numbers · **ADR-0076** accepted 10-27 · **EXP-043** frozen (ladder ride forward) |
| Gap log | **250 OPEN** · 298 headers = 298 status lines (window, origin/main 36f49a9, 11-05) · no duplicate ids (live + archive). Numbers are reserved in ranges per block; unused ones are skipped, never reused |
| Registry | **108 cells, 52 logging** (B1, box 10-28) |
| Surface (ADR-0074) | **88 live components** · budget **GREEN** · healthcheck HEALTHY · no silent arm · box HEAD = main (05:48Z) · **0 OOM kills since the T1/T2 lock (02:11Z), 375 MB available** (was 45 / 24 h, 223 MB) - memory still the constraint. Map: `02_ARCHITECTURE_DESIGN/RUNTIME_MAP.md` |
| Capital | **$0 real.** `kelly_fraction = 0.0` everywhere; flat demo stakes only (ADR-0050/0072). Kill switch ENFORCING on every order path (89.1) |
| Deploy | the box pulls main every 5 minutes (vps_deploy.sh, :03/:08/...). Installs run by the window only on the operator's named approval in chat (11-03) |
| W102.1 | **Part A DONE** (PR #425, 76b5e3d): root cause = OOM burst + no in-window retry; fix merged, cron install awaits operator approval of `nba_engine_catchup_install`. Parts B (NHL) / C (store lag) not started. |
| Silent arms | none (05:48Z); but **NBA v2 / v3 still miss without OOM**: 11-04 slate v1 56/56, v2 44/56, v3 38/56 markets, every miss "window_closed_without_a_successful_run" (nba_engine_coverage_read) - 102.1 |
| Open PRs | #149 only (stale, holds unlanded GG-279 work). Stray branches 35 -> 3 (102.5) |


---

## 🌲 RUNNING SITREP — the forest (kept by every strategic window; **current: SW-9, Waves 101 →, since 2026-11-04**; previous: SW-8, Waves 81–100. Register: `04_EXECUTION/WINDOW_REGISTER.md`)

*Updated by the strategic window at every wave close and at every handoff. Last update: **Wave 110 CLOSED, 2026-11-11, SW-9** (GitHub; box bridge last read 11-11).*

### 📏 DISTANCE TO OPTIMUM — read this first

*Generated by `scripts/distance_to_optimum.py` on the box via the bridge's `distance_read`, result
`04_EXECUTION/BOX_TASKS/results/20261106T022654Z_b_distance_read.md`, computed 2026-11-06T02:27Z. Unchanged against the Wave 100
close: Waves 101-103 moved measurement and execution correctness (GG-1771), not table rows - E3 above is still the as-logged figure.*

| Pillar | Measure | Now (generated, box, 2026-11-06 02:27Z) | At optimum | Moved, Waves 101-104 |
|---|---|---|---|---|
| **BREADTH** | B1 cells logging / registered | **52 / 108** (ruled-out-but-logging arms counted again, 100.2) | the whole board | 50 → 52 (count fix) |
| | B2 families logging / registered | **17 / 19** | 19 / 19 + parlays | 0 |
| | B3 bands logging | **4 of 5** (no T5) | 5 of 5, T4 sub-bands | 0 |
| | B4 props · parlays families logging | **2 · 0** | the board | 0 |
| **DEPTH** | D1 factor classes per pre-game model | NFL pregame: team · NFL QB challenger: personnel, team · NBA pregame: team · NBA points (both): personnel, team, venue · MLB hits: personnel, team, venue · MLB game: personnel, team · NHL: personnel, team, venue. **No live model uses matchup, weather or qualitative** (KXNFLPASSYDS's model uses matchup; it counts once it logs) | every class at every arm | 0 |
| | D2 largest pre-game feature set | **18** (MLB player hits, 0 qualitative) | coverage, not a count | 0 |
| | D3 challengers ready | **5** (NFL QB; EXP-041; EXP-044b; EXP-044c NBA engine v3, frozen not installed; one counted by the script) | ≥ 1 per arm | 0 |
| | D4 engine stage (ADR-0073) | **NFL: data layer + board engine + test, frozen forward test (EXP-045) · NBA: data layer + board engine; v1 / v2 / v3 logging; 11-04 slate v1 56/56, v2 44/56, v3 38/56 markets (no OOM - runs never succeed before the window closes, 102.1); v3 has no settled game yet · NHL: board engine v2 (late-game state; totals still low)** · MLB: none | each sport: data → factors → whole board | 0 |
| | D5 betting architecture (ADR-0075) | **(a) NFL 8/8, NBA 8/8, NHL 7/8, MLB 3/8** (W109) · **(b) applied NFL 14 / 23, NBA 11 / 17, NHL 8 / 12, MLB 0 (W110: NFL weather + matchup and NBA usage / crosses now router filters; scored per leaf, 0 leaves earn an arm yet)** | 8 / 8 per sport; every factor a tested split | NBA 4 → 8, NHL 2 → 7 (W109) |
| | **D6 cells wired end to end (ADR-0077, added 2026-11-11)** | **0** (layers: simulated prob · market state · factor filters as splits · tree choosing the arm · per-leaf net per arm · risk / sizing · execution). **3 / 117 ON THE BOX (d6_read 2026-11-17 00:57Z) - first wired cells, NBA**; NFL / NHL at 0 (no filter data on the box) → 115.3 | every registered cell | new |
| **EXECUTION** | E1 demo orders filled | **T4 MLB 177 / 4,316 = 4.1% · T1 MLB 85 / 485 = 17.5%** (MLB books idle since 10-20) | fills ≈ intended orders | 0 |
| | E2 P&L per filled bet | **T4 −$0.21** (n 177) · **T1 −$1.50** (n 83) | positive net of fees | 0 |
| | E3 win rate, fills vs non-fills | **T4 25.4% vs 48.3% · T1 28.9% vs 52.1%** · resting fills picked off; **entry cost measured (98.2): taking at the quote loses ~0.10 / contract in NBA and NFL - keep the frozen rule**; NHL unclear | fills ≥ non-fills | 0 |
| | Forward test (ADR-0072), per book and sport | **Restarted 2026-11-06T01:03:42Z** (GG-1771 epoch, operator "Restart"). Before it: NFL printed ADOPT on mirror-priced NO fills; on clean fills **INCONCLUSIVE** (YES-only a = +0.006 [-0.10, +0.11]); 102.4: ~18 of 19c was which orders fill. NBA / NHL: (a) held, (b) failed | ~550 markout-bearing fills per arm, per (book, sport), from the epoch | NFL ADOPT -> **INCONCLUSIVE, clock restarted** |
| **PROOF** | P1 cells at a scored look | **12 / 49** (the NFL first look, 2026-11-02) | every cell judged at its n | 0 |
| | P2 verdicts | **12, read (98.2): NFL game total T1 + T2 RULED_OUT (model ~0.016 Brier worse than the market); 10 KEEP ACCRUING (all slightly behind the market, slightly ahead of a naive baseline, none proven); 0 CANDIDATE** | a verdict per cell | 0 |
| | P3 next look | **2026-11-13** (NFL QB moneyline); modal outcome **KEEP ACCRUING ~91%** | — | 0 |

**Surface (box, 2026-11-10 06:05Z + 11-11 window checks):** dashboard redesigned and refreshing on pull (#457 / #459), memory near its cap
(134.07 of 134.2 MB at 05:37Z, then 111.6 MB after the restart) - 109.5; **budget GREEN since 11-11 00:45Z: ride board and the 22-series prop archive installed (operator-approved 11-10 16:27 PT)**; the never-approved news burst entry paused by the window 11-10. MLB Features Sync fails closed daily off-season
(109.5). **Routing inputs so far (EDGE_MAP, W108):** 40 single patterns tested on their own - each is now an input to the multi-arm tree, not a verdict; 2 held-out positive as stand-alone bets (MLB ladder ride, EXP-043, 2027). The tree that routes them (D6) is at 0 cells - that is the build. **Operator 11-10: "WE ARE SO FAR AWAY" - no "no edge" talk; losing to the market is a routing result (DOCTRINE.md §1b).** **Muse:** 11-10 ~92 chunks DONE / 24 NONE (NBA.com tables that do not
reproduce - Monday fix noted in 04_EXECUTION/MUSE_MONDAY_2026-11-16_NOTES.md), 2 BLOCKED (Akamai), snapshots running (goalies 4x, lineups, refs).

*Older window notes, the 10-08 scoreboard, the build history and the 10-19 calendar moved to `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md` (2026-11-04, operator: "edit the Active Queue cus it's too large right now").*

---

## ▶ NOW — WAVE 129 · WRITTEN 2026-11-25 ~07:30 UTC (11-24 23:30 PT) · SW-9 · seven blocks (129.6 / 129.7 added 11-25 16:09 PT) · MODEL: Sonnet · paste each into its own terminal

**Depth into the live path, and one D6 number before the handoff.** Wave 128 landed all five blocks:
- **NHL:** goalie, referee and availability splits are built behind `PM_NHL_DEPTH`, which is off. Judging needs about 370 games.
- **NBA:** props now use one player-mean function, and the combo legs read C2.
- **NFL:** the play-level test judged 74 leaves and earned 0, so those leaves route to ride or no bet. N24–N26 are applied.
- **H-DEPTH-PAM-3 SUPPORTED:** D +0.00201 [+0.00184, +0.00219], positive on 4 of 4 stats.
- **Muse offload:** 4 server scrapers are built, but the install waits for your approval. MLB boxscores still return 406, so they stay with Muse.

This wave does five things:
- puts NHL depth into the shadow rows with real inputs;
- turns PAM-3 into a props challenger;
- builds the PAM state tables;
- freezes MLB 2027 before its first row;
- makes D6 one number.

The window hands off to SW-10 after Wave 130.

| # | Lane | Block | Model | Status | Outcome |
|---|---|---|---|---|---|
| 129.1 | DEPTH / NHL | NHL depth switched on in shadow: Muse snapshots fetched at a pinned SHA, expected starters from the NHL event store, `PM_NHL_DEPTH` on after the surface check, leaves recounted | Sonnet | 🟡 PR open (W129.5): D6 from one source, DISTANCE_TABLE_W129.md, 73 registry rows (42 before), 0 unregistered PREREG | |
| 129.2 | DEPTH / NBA | EXP-047 shrunk-mean challenger (PAM-3 shrinkage × C2 usage shift): pre-registered on a population neither test read, built, logging in shadow beside C2 | Sonnet | 🟡 PR open (#595) | EXP-047-S SUPPORTED 11-25: pooled D +0.00172 [+0.00140, +0.00204], 4 of 4 stats, 2025-26 (not fresh, disclosed); PREREG 8d6b97e6; shadow beside C2 behind PM_PROPS_SHRUNK |
| 129.3 | PROOF / MLB | MLB 2027 forward pre-registration for the 12 game cells (frozen before the first row); daily-board install built with an arm-date alarm (GG-1957); a full 2026 slate dry-run through all seven layers | Sonnet | ⬜ | |
| 129.4 | DEPTH / PAM | PAM point-in-time state tables: `player_state`, `availability_profile`, `trait_reliability` (NBA backfill from the event store); H-DEPTH-PAM-4 (role security) pre-registered, not run | Sonnet | ⬜ | |
| 129.5 | PROOF / measurement | One D6 number (box 18 / 117 vs repo 0 / 129, reconciled); the distance table recomputed for the handoff; the hypothesis registry backfilled (B-110) with a check that flags unregistered pre-registrations | Sonnet | ⬜ | |
| 129.6 | BREADTH / NFL | NFL in-play: a free live game-state feed for the T4NFL cells (16 registered, none can log), replayed on recorded games, shadow behind PM_NFL_INPLAY, install built (added 11-25 16:09 PT) | Sonnet | ⬜ | |
| 129.7 | BREADTH / NHL | NHL in-play: a free live game-state feed (NHL API) for the T4NHL cells, replayed on recorded games, shadow behind PM_NHL_INPLAY, install built (added 11-25 16:09 PT) | Sonnet | ⬜ | |

- **Pushback:**
  - Only 129.2 can issue a verdict this wave, and only if an unread historical population exists for it.
  - 129.4 and half of 129.5 build no verdict.
  - Why run them anyway: SW-10 inherits a D6 that two sources disagree on, and a PAM that holds no state. Fixing both is cheaper now than after the handoff.
  - Alternative: drop 129.4 for the combo per-leaf look, which needs `nba_combo_shadow_install` approved first.
- **Surface:**
  - 129.1 switches on one shadow field path, and only on green health.
  - 129.2 adds a shadow log field beside C2.
  - 129.3 builds an install but does not run it.
  - No new live component.
  - Three installs wait on you (below).
- **Dependencies:**
  - None at merge.
  - `shadow_route.py` is owned by 129.1.
  - 129.5 merges last if a HYPOTHESIS_DOCTRINE edit is open elsewhere.
  - Full ownership is in COMMON_RULES_W129.
- **Plan after this wave:**
  - W130 is the handoff wave (B-125): doctrine stack review, distance table from 129.5, backlog groomed, error-log lessons, and combo per-leaf if its install is approved.
  - The H-EXEC-4 first look (12-01) and the weekly evidence look open SW-10's first wave.

### 129.1 - NHL DEPTH SWITCHED ON IN SHADOW WITH REAL INPUTS · MODEL: Sonnet

```
WAVE 129 - BLOCK 129.1 - DEPTH: NHL GOALIE / REFEREE / AVAILABILITY SPLITS LOGGING ON EVERY NHL SHADOW ROW - MODEL: Sonnet
PURPOSE: DEPTH D5(b) NHL (goalie@game, officials, availability: built -> logging on box rows with real inputs) and D6 NHL layer 3
(tested splits on box rows). Backlog B-122, Wave 128.1 handoff: inputs and filter built (filters/nhl_depth.py, nhl_depth candidate in
shadow_route.py, split_applied=False), PM_NHL_DEPTH off because NHL_MUSE_DIR is empty on the box and the expected starter came from
Muse-confirmed starts only (39 of 99 games "any_backup" = a sparse-history artefact, 53 unknown).

FIRST: run `git fetch origin && git show origin/main:04_EXECUTION/WAVE_BLOCKS/COMMON_RULES_W129.md` and quote its first line. Those rules
bind this block. Then read 11_MEMORY_HANDOFF/SESSION_HANDOFF_20261125T0617Z_W128_1.md, 12_EXPLORATORY/nhl_depth/ (its PREREG is frozen),
decision_trees/filters/nhl_depth.py, the nhl_depth candidate in decision_trees/shadow_route.py, c1_signal_ingestion's NHL event store reader, and
src/prediction_market_bot/archive_intake/fetch.py (how the bot reads Muse's archive at a pinned commit). Handoff: 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W129_1.md.

PART A - inputs on the box. An allowlisted READ-ONLY-to-the-repo box task (nhl_muse_fetch, writes only under NHL_MUSE_DIR) that pulls
Muse's NHL goalie and referee snapshot files at the pinned archive SHA through the GitHub API (never a clone; never a write to the archive),
idempotent, byte-capped, run under a memory cap. Run it; read back the file count per type and the date range.
PART B - expected starters from the NHL event store: starts per goalie per team strictly before the game (last-N and season share),
Muse's same-day confirmation layered on top when present. Known-answer test (planted backup start moves the leaf; no Muse file -> the
event-store prior alone, never "unknown" when the store has starts). Re-count the 2026-11-10..today join: both_expected / any_backup /
unknown, before and after.
PART C - Hard Rule 14 surface check (health_read, silent arms, deploy truth); if green, switch PM_NHL_DEPTH on in shadow through the
existing path (split_applied stays False; v1 and nhl_v2 byte-identical) and read back one slate's rows with split_leaves populated. If the
switch needs an *_install task, build it and put the approval line under `operator decisions:`. Write the date the frozen PREREG's judged
n (~370 games) is reached at the current NHL schedule.

Land: PR, CI green, merge; read the deploy back. Report: per COMMON RULES. MEASURE MOVED: D5(b) NHL classes logging on box rows (0 -> n),
unknown-starter share (53 / 99 -> x), first judged look date.
END OF BLOCK 129.1
```

### 129.2 - EXP-047 SHRUNK-MEAN CHALLENGER (PAM-3 × C2) · MODEL: Sonnet

```
WAVE 129 - BLOCK 129.2 - DEPTH: THE PROPS CHALLENGER PAM-3 LICENSED - SHRUNK PER-MINUTE RATES x SHRUNK MINUTES, WITH C2'S USAGE SHIFT
- MODEL: Sonnet
PURPOSE: DEPTH D3 (+1 pre-registered challenger for the NBA props arm) and D5(b) PAM class 3 at NBA player level (interpreted -> a
challenger on the path to applied). Backlog B-127. H-DEPTH-PAM-3 SUPPORTED (W128.4: D +0.00201 [+0.00184, +0.00219], 4 of 4 stats);
its PREREG section 7 names this challenger. C2 (stat-specific usage shift) SUPPORTED on unread 2023-24 and logs forward in shadow.

FIRST: run `git fetch origin && git show origin/main:04_EXECUTION/WAVE_BLOCKS/COMMON_RULES_W129.md` and quote its first line. Those rules
bind this block. Then read 12_EXPLORATORY/pam_stability/ (PREREG.md, PREREG_ADDENDUM_1.md, RESULT.md, trait_reliability_draft.json),
12_EXPLORATORY/nba_props_role/ (C2's PREREG and RESULT_C2.md), nba_engine/props.py (c2_means, W128.2), and
pregame_shadow/nba_engine_props*_forecaster.py. Handoff: 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W129_2.md.

PART A - PRE-REGISTER FIRST (12_EXPLORATORY/nba_props_shrunk/PREREG.md, committed and pushed before any judged row is read):
control = C2 as logged; challenger = C2's usage shift applied to PAM-3's shrunk rate x shrunk minutes (k values from
trait_reliability_draft.json, fitted on training seasons only, fixed). Judged population: a season or slice NEITHER C2 nor PAM-3 judged -
check both RESULT files and the H-DEPTH rows in HYPOTHESIS_DOCTRINE.md and name it with the check. 2025-26 was excluded by PAM-3 because
the operator's fantasy test used it (design motivation, not evidence): if it is the only unread season, use it and state that in the
PREREG. If no unread historical population exists, the judged set is forward 2026-27 rows and the PREREG states the judged n from
quant/inference.mde_paired. Metric, interval and rule in PAM-3's form; pre-stated modal outcome.
PART B - build the challenger with a known-answer test (planted reliability recovered; zero-noise case does not beat the raw mean), run it
once on the judged historical population if Part A named one: RESULT.md + results.json quoting the PREREG SHA, per-stat D with BH.
PART C - log it forward in shadow beside C2 behind PM_PROPS_SHRUNK (C2 and v1 byte-identical; no orders); switch on after the Hard Rule
14 check, or put the install line under `operator decisions:` if one is needed. Update the H-DEPTH-PAM-3 row and add this test's row in
HYPOTHESIS_DOCTRINE.md in the same PR.

Land: PR, CI green, merge. Report: per COMMON RULES. MEASURE MOVED: D3 NBA props (+1), P2 (+1 if Part B ran), D5(b) PAM class 3 stage.
END OF BLOCK 129.2
```

### 129.3 - MLB 2027 FROZEN BEFORE ITS FIRST ROW · MODEL: Sonnet

```
WAVE 129 - BLOCK 129.3 - PROOF: THE MLB 2027 FORWARD PRE-REGISTRATION, THE DAILY-BOARD INSTALL, AND A FULL-SLATE DRY RUN - MODEL: Sonnet
PURPOSE: PROOF P3 (the next MLB look and its modal outcome, written before the first 2027 row) and D6 MLB (layers each of the 12 game
cells reaches in a dry run). Backlog B-123. Wave 127.2: MLB engine counted (D4 first stage, D5(a) 3 -> 4), opening-day dry run 12 / 12
cells priced. GG-1957: the 2026 ledger is postseason only because the crons were armed late and a job exited silently.

FIRST: run `git fetch origin && git show origin/main:04_EXECUTION/WAVE_BLOCKS/COMMON_RULES_W129.md` and quote its first line. Those rules
bind this block. Then read 11_MEMORY_HANDOFF/SESSION_HANDOFF_20261125T0700Z_W127_2.md, 12_EXPLORATORY/mlb_engine/, mlb_engine/, the
GG-1957 entry, 02_ARCHITECTURE_DESIGN/HYPOTHESIS_DOCTRINE.md Part I, and the NHL / NBA forward PREREGs as the form to copy.
Handoff: 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W129_3.md.

PART A - the forward PREREG for the 12 MLB game cells (moneyline, run line, total, team total x bands): the engine price enters as a
layer-1 input to the router, never the bet; arms per leaf; judged n per cell from quant/variance.mde_clustered at the 2026 variance; look
dates in calendar 2027; gross, round cost and net side by side; the pre-stated modal outcome per family. Committed and pushed now - before
any 2027 row exists. Add the registry rows.
PART B - the daily-board install (scripts/mlb_board_install.py: gate / install / readback / uninstall, budget-gated like
archive_dense_install) with the two GG-1957 fixes as code: an arm-date check that alarms if the cron is not armed 7 days before opening
day, and a silent-exit alarm (a run that writes 0 rows on a scheduled game day is a FAIL in health.log). RUNTIME_REGISTRY entry, paused.
Tests. Do NOT run the install: its approval line goes under `operator decisions:` with the date it must be run by.
PART C - a full 2026 regular-season slate day (pick one with every family listed) replayed through all seven D6 layers in dry mode: per
cell, which layers are present. List what is missing per cell.

Land: PR, CI green, merge. Report: per COMMON RULES. MEASURE MOVED: P3 (MLB looks dated, 0 -> 12 cells), D6 MLB dry-run layers per cell.
END OF BLOCK 129.3
```

### 129.4 - PAM POINT-IN-TIME STATE TABLES (NBA FIRST) · MODEL: Sonnet

```
WAVE 129 - BLOCK 129.4 - DEPTH: PAM HOLDS STATE, NOT ONLY CLASSIFICATIONS - player_state, availability_profile, trait_reliability -
MODEL: Sonnet
PURPOSE: DEPTH D5(b) NBA PAM classes 1, 2 and 4 (absent -> aggregated, point-in-time) and D3 (+1 pre-registered test, H-DEPTH-PAM-4).
Backlog B-117, gaps GG-2005 (no point-in-time state table) and GG-2003. Design: 02_ARCHITECTURE_DESIGN/PAM_ATTRIBUTE_CLASSES.md §3 A-C
(the field lists are the spec; a change is a dated note in that file).

FIRST: run `git fetch origin && git show origin/main:04_EXECUTION/WAVE_BLOCKS/COMMON_RULES_W129.md` and quote its first line. Those rules
bind this block. Then read the design note, src/prediction_market_bot/pam/schema.py and store.py (the as_of(..., known_at=) contract to
copy), the NBA event store reader, player_availability.fit_play_rates, and 12_EXPLORATORY/pam_stability/trait_reliability_draft.json.
Handoff: 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W129_4.md.

PART A - the three tables as code in pam/ (new modules; schema.py / store.py add-only): every row carries as_of_ts, known_at, source,
version; one read path as_of(..., known_at=). Look-ahead tests: a row known after the decision time is never returned; a trade changes
team from its date.
PART B - the NBA backfill from the event store (2016-2026 box scores, injury reports 2023-26 where present): player_state rows per
player-game at the pre-tip decision time (usage_rate_shrunk with PAM-3's k, usage_rank_available, teammates_out, vacated_usage_share,
minutes_expected, minutes_share_full_roster; role_security and return_window left null and named), availability_profile per player-date
(gp_by_season, missed_by_body_part where reports exist, recurrence_flags), trait_reliability from the draft. Streamed, compressed,
run in the session (not on the box). Row counts and a spot-check of 10 rows against box scores.
PART C - PRE-REGISTER H-DEPTH-PAM-4 (12_EXPLORATORY/pam_state/PREREG_PAM4.md): role security (class 4, minutes lost when a displacing
teammate returns), fitted on training seasons, judged on seasons no earlier test judged, metric / rule / modal outcome stated. Do NOT
run it. Add its HYPOTHESIS_DOCTRINE row.

Land: PR, CI green, merge. Report: per COMMON RULES. MEASURE MOVED: D5(b) NBA PAM classes 1 / 2 / 4 stage, D3 (+1), GG-2005 status.
END OF BLOCK 129.4
```

### 129.5 - ONE D6 NUMBER, THE DISTANCE TABLE, THE HYPOTHESIS REGISTRY · MODEL: Sonnet

```
WAVE 129 - BLOCK 129.5 - PROOF / MEASUREMENT: D6 FROM ONE SOURCE, THE DISTANCE TABLE FOR THE HANDOFF, EVERY HYPOTHESIS REGISTERED -
MODEL: Sonnet
PURPOSE: PROOF P1 / P2 counted right and D6 reported once. Backlog B-110 and the handoff input for B-125. The box's d6_read says 18 of
117 (NBA 7, NHL 7, NFL 4; 20261125T0500Z_w1271_d6_read.md); scripts/distance_to_optimum.py says 0 of 129 from the repo's static
leaf_map.json. The window hands off to SW-10 after Wave 130 and a new window must not inherit two D6 numbers.

FIRST: run `git fetch origin && git show origin/main:04_EXECUTION/WAVE_BLOCKS/COMMON_RULES_W129.md` and quote its first line. Those rules
bind this block. Then read scripts/distance_to_optimum.py (D6 section), decision_trees/coverage.py (d6_layers), the newest d6_read and
d6_trace_read results under 04_EXECUTION/BOX_TASKS/results/, GG-2010 / GG-2011, and 02_ARCHITECTURE_DESIGN/HYPOTHESIS_DOCTRINE.md.
Handoff: 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W129_5.md.

PART A - D6 reconciled: why 117 vs 129 registered cells, and why 18 vs 0 wired (box rows vs static repo map; which layers each reads).
distance_to_optimum.py reports D6 from the newest box d6_read result with its date as the number, and the repo-static count beside it
labelled as such; a test for the parsing. Run a fresh d6_read on the box and quote it.
PART B - the distance table recomputed (every B / D / E / P measure with source and date) into 04_EXECUTION/DISTANCE_TABLE_W129.md for
the window's handoff. Do not edit the RUNNING SITREP (the window's).
PART C - the registry backfill (B-110): every hypothesis since EXP-001 / HYP-010, live or parked for R&D, in HYPOTHESIS_DOCTRINE.md's
registry form (id, claim, population, rule, verdict or look date, file, status); scripts/hypothesis_registry_check.py flags any PREREG in
05_RESEARCH_EXPERIMENTS/ or 12_EXPLORATORY/ without a registry row (alarm-only, run in Docs Guard). Merge after any other open W129 PR
that edits HYPOTHESIS_DOCTRINE.md, rebasing onto it.

Land: PR, CI green, merge. Report: per COMMON RULES. MEASURE MOVED: D6 sources 2 -> 1; registry rows before -> after; unregistered
pre-registrations found.
END OF BLOCK 129.5
```

### 129.6 - NFL IN-PLAY: A FREE LIVE GAME-STATE FEED FOR THE T4NFL CELLS · MODEL: Sonnet

```
WAVE 129 - BLOCK 129.6 - BREADTH: NFL IN-PLAY CELLS GET A LIVE GAME-STATE FEED AND LOG IN SHADOW - MODEL: Sonnet
PURPOSE: BREADTH B1 / B3 (NFL in-play cells logging; T4NFL-ARITH / T4NFL-FLOW bands with a logging cell, 0 -> n). Wave 122.3: 16
registered NFL cells are in-play and none can log, because the bot has no NFL live feed. Horizon doctrine (ADR-0068): in-play trees are
shallow and must be paid for in measured speed, so the feed's latency is measured, not assumed.

FIRST: run `git fetch origin && git show origin/main:04_EXECUTION/WAVE_BLOCKS/COMMON_RULES_W129.md` and quote its first line. Those rules
bind this block. Then read the W122.3 handoff, execution_bands.py (T4NFL-ARITH / T4NFL-FLOW), the NFL in-play cells in
c5_execution/market_type_registry.py, the MLB T4 live loop (run_t4_mlb_live.py and its staleness / contamination checks, GG-085, GG-163:
ESPN once 403'd the box for 43 h and nothing alarmed) and the NHL / NBA shadow runners as the logging pattern.
Handoff: 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W129_6.md. Added to Wave 129 after it started (operator 11-25 16:09 PT); 129.1-129.5
are running: stay inside your ownership line in COMMON_RULES_W129 and rebase before every push.

PART A - the feed: a free, server-reachable NFL live source (prove it from the box with a read-only task; never get past a bot check),
point-in-time game state per play (score, quarter, clock, down / distance / yard line, possession, timeouts) with fetch time recorded, a
staleness check, and a write-recency alarm (no rows while a game is live = FAIL in health.log). Known-answer test on a saved game.
PART B - the in-play pricer for the T4NFL cells from the NFL engine's pre-game price updated by game state (the arithmetic band first),
replayed over recorded 2026 games (no waiting for a Sunday): per cell, rows logged, Brier vs the Kalshi in-play price at the same
timestamp where the price archive has it, and feed latency vs the market's move.
PART C - shadow logging behind PM_NFL_INPLAY (no orders) with a RUNTIME_REGISTRY entry and an install task built, NOT run: its approval
line under `operator decisions:` with the budget gate result.

Land: PR, CI green, merge. Report: per COMMON RULES. MEASURE MOVED: B1 (NFL in-play cells able to log, 0 -> n), B3 (T4NFL bands), feed
latency measured.
END OF BLOCK 129.6
```

### 129.7 - NHL IN-PLAY: A FREE LIVE GAME-STATE FEED FOR THE T4NHL CELLS · MODEL: Sonnet

```
WAVE 129 - BLOCK 129.7 - BREADTH: NHL IN-PLAY CELLS GET A LIVE GAME-STATE FEED AND LOG IN SHADOW - MODEL: Sonnet
PURPOSE: BREADTH B1 / B3 (NHL in-play cells logging; T4NHL-ARITH / T4NHL-FLOW bands with a logging cell, 0 -> n). The NHL engine prices
the pre-game board; no NHL in-play cell logs. Horizon doctrine (ADR-0068): in-play trees are shallow and must be paid for in measured
speed, so the feed's latency is measured, not assumed.

FIRST: run `git fetch origin && git show origin/main:04_EXECUTION/WAVE_BLOCKS/COMMON_RULES_W129.md` and quote its first line. Those rules
bind this block. Then read execution_bands.py (T4NHL-ARITH / T4NHL-FLOW), the NHL in-play cells in c5_execution/market_type_registry.py,
the NHL event store (it already reads the NHL's own API), the MLB T4 live loop (run_t4_mlb_live.py and its staleness / contamination
checks, GG-085, GG-163) and the NHL shadow runner as the logging pattern. NHL domains carry Content-Signal ai-train=no: we fetch data,
we do not train AI on it. Handoff: 11_MEMORY_HANDOFF/SESSION_HANDOFF_<UTC>_W129_7.md. Added to Wave 129 after it started (operator 11-25 16:09 PT); 129.1-129.5
are running (129.1 owns the NHL depth files in nhl_engine/): stay inside your ownership line in COMMON_RULES_W129 and rebase before every push.

PART A - the feed: the NHL's free live endpoints (play-by-play / boxscore), proven from the box with a read-only task, point-in-time game
state per event (score, period, clock, strength / power play, empty net, shots) with fetch time recorded, a staleness check, and a
write-recency alarm (no rows while a game is live = FAIL in health.log). Known-answer test on a saved game.
PART B - the in-play pricer for the T4NHL cells from the NHL engine's pre-game price updated by game state (the arithmetic band first:
score, time left, strength, empty net), replayed over recorded 2026-27 games so far (no waiting for tonight): per cell, rows logged,
Brier vs the Kalshi in-play price at the same timestamp where the price archive has it, and feed latency vs the market's move.
PART C - shadow logging behind PM_NHL_INPLAY (no orders) with a RUNTIME_REGISTRY entry and an install task built, NOT run: its approval
line under `operator decisions:` with the budget gate result.

Land: PR, CI green, merge. Report: per COMMON RULES. MEASURE MOVED: B1 (NHL in-play cells able to log, 0 -> n), B3 (T4NHL bands), feed
latency measured.
END OF BLOCK 129.7
```

## Sequencing track

Legend: ✅ landed on main · ⚠️ done but NOT on main (branch / PR) · ✂️ cut short by operator · ❌ never ran · ⏳ in flight · ⬜ not started

### ✅ WAVE 128 — WRITTEN 2026-11-25 ~05:55 UTC · CLOSED 2026-11-25 ~07:30 UTC (operator 11-24 22:47 PT) · SW-9 · five blocks · verified on GitHub (#555 #582–#588 merged; handoffs W128_1..5; main Docs Guard green d8b31eaf) · moved: **P2 +1 (H-DEPTH-PAM-3 SUPPORTED, D +0.00201 [+0.00184, +0.00219], 4 of 4 stats); D5(b) PAM class 3 NBA absent → interpreted; NFL play-level 74 judged, 0 earned (ride / no bet), N24–N26 applied; NBA props on one mean function, combo legs on C2; NHL depth splits built (off, ~370 games to judge); 4 Muse families moved to server scrapers (install pending); D6 unchanged 18 of 117**

| # | Block | Model | Status | Outcome |
|---|---|---|---|---|
| 128.1 | NHL officials / goalie / availability | Sonnet | ✅ #585 | splits + PIT inputs built behind PM_NHL_DEPTH (off); D5(b) NHL unchanged; 39 of 99 "any_backup" is a sparse-history artefact → 129.1 |
| 128.2 | one NBA props engine | Sonnet | ✅ #582 #586 | c2_means is the one mean function; combo legs on C2; 0 prices differ on day 1 |
| 128.3 | NFL play-level | Sonnet | ✅ #583 #588 | EXP-NFLPLAYLEVEL-001: 74 judged, 0 earned (ride / no bet); N24–N26 applied |
| 128.4 | H-DEPTH-PAM-3 | Sonnet | ✅ #555 | SUPPORTED, 4 of 4 stats; trait_reliability draft written → 129.2, 129.4 |
| 128.5 | Muse offload | Sonnet | ✅ #584 #587 | 4 scrapers (MoneyPuck, NHL officials, NHL goalie logs, Savant), gate PASS 12 MB/day, peak RSS ~26 MB; mlb_boxscore 406 from the box → stays Muse; data_offload_install awaits approval |

### ✅ WAVE 127 — WRITTEN 2026-11-25 ~03:15 UTC · CLOSED 2026-11-25 ~07:00 UTC (operator 11-24 21:36 PT) · SW-9 · four blocks · verified on GitHub (#572–#581 merged; handoffs W127_1..4) · moved: **D4 MLB none → data layer + engine + test; D5(a) MLB 3 → 4 (dry run 12 / 12 cells); E1 combos 0 → 2 demo fills (3 of 12 RFQs quoted); C2 logging forward (shadow); dense capture 159.2 → 30.5 MB/day, gate PASS; D6 unchanged 18 of 117**

| # | Block | Model | Status | Outcome |
|---|---|---|---|---|
| 127.1 | D6 breaks + C2 on | Sonnet | ✅ #573 | prop ticker parse fixed; GG-2007 closed; PM_PROPS_C2 shadow ON (+1 ledger dir); D6 18 → 18; leaf map v2 promotion open (GG-2010) |
| 127.2 | MLB engine counted | Sonnet | ✅ #572 #579 | engine row + manifest; D4 MLB first stage; D5(a) 3 → 4; dry run 12 / 12; 2027 pre-reg + daily-board install before opening day |
| 127.3 | combos via RFQ | Sonnet | ✅ #575–#578 #580 #581 | 3 of 12 RFQs quoted, 2 demo fills (unsettled); nba_combo_shadow_install built, not run |
| 127.4 | dense capture fits | Sonnet | ✅ #574 | 159.2 → 30.5 MB/day; gate PASS; archive_dense_install awaits approval |

### ✅ WAVE 126 — WRITTEN 2026-11-24 ~07:10 UTC · CLOSED 2026-11-25 ~02:25 UTC (operator 11-24 18:27 PT) · SW-9 · five blocks · verified on GitHub (#565 #566 #567 #569 #570 #571 merged; #572 open = 126.3 MLB, lands in 127.2) · moved: **D3 +2 (EXP-047-C2 SUPPORTED on unread 2023-24, all four stats; combo arm pre-registered); D5(b) NFL seat N12 → applied, 5 of 5 splits to a verdict (0 earned); D6 18 of 117 (NHL 6 → 7); MLB engine built (12 known-answer tests), not yet counted; router ERROR rows were one bug fixed 11-17 (0 since 11-18)**

| # | Block | Model | Status | Outcome |
|---|---|---|---|---|
| 126.1 | every row to a leaf | Sonnet | ✅ #565 | ERROR rows = KeyError fixed by #503 (0 since 11-18); dense gate REFUSE 87.2%; NFL NO_BET question to operator |
| 126.2 | NBA props C2 | Sonnet | ✅ #566 #569 | SUPPORTED on unread 2023-24 (899 games): points -0.026, rebounds -0.001, assists -0.004, threes -0.003 log-loss; PM_PROPS_C2 off → 127.1 |
| 126.3 | MLB engine | Sonnet | 🟡 #572 open | PA model + joint sim + one-draw board; 2026 report trails Kalshi on 4 of 4 families (ML closest, -0.004 Brier); dry run + manifest → 127.2 |
| 126.4 | combo markets | Sonnet | ✅ #567 #571 | pricer + shadow writer (off); 59,453 of 61,000 combos unquoted (RFQ-style); COMBO_PREREG frozen → 127.3 |
| 126.5 | NFL splits | Sonnet | ✅ #570 | 5 of 5 splits to a verdict, 0 earned; seat N12 aggregated → applied |

### ✅ WAVE 125 — WRITTEN 2026-11-24 ~01:15 UTC · CLOSED 2026-11-24 ~06:45 UTC (operator 11-23 22:47 PT) · SW-9 · four blocks · verified on GitHub (#559 #560 #561 #563 #564 merged; #554 #556 landed as Part 0; #562 open = 125.2 partial; main CI green 5ea52b72) · moved: **P2 +2 verdicts (H-EDGE-5 NOT SUPPORTED: favourite-longshot gross real, below one round cost; pot of gold 0 of 18 leaves earned); B4 +4 combo families registered; E2/E3 fill model on 3,214 orders, no rule supported; D5(b) NBA-10 consumers 1 → 2 (usage shift improves NBA points props, hurts the other stats)**

| # | Block | Model | Status | Outcome |
|---|---|---|---|---|
| 125.1 | placement as a decision | Sonnet | ✅ #560 (+#554) | fill model live (3,214 orders); best cell 11 settled-filled games vs 20; ARM_PLACEMENT_POLICY stays current; GG-2008 |
| 125.2 | every row to a leaf | Sonnet | 🟡 #559 merged, #562 open | stall alarm counts both paths (GG-2006); router_error_read built; ERROR breakdown, D6 trace, gate read not done → 126.1 |
| 125.3 | H-EDGE-5 + pot of gold | Sonnet | ✅ #563 #564 | NOT SUPPORTED 0 of 7 testable cells; pot of gold 0 of 18 EARNED; Kalshi combo markets found and registered |
| 125.4 | NBA props usage shift | Sonnet | ✅ #561 | EXP-047-C1 INDETERMINATE: points -0.0273 [-0.0306, -0.0241] better; rebounds / assists / threes worse; PM_PROPS_C1 stays off |

### ✅ WAVE 124 — WRITTEN 2026-11-20 ~21:55 UTC · CLOSED 2026-11-24 ~01:00 UTC (operator 11-23 17:01 PT) · SW-9 · five blocks · verified on GitHub (#557 #558 merged; #554 #555 #556 open, unmerged — Docs Guard on main was red 00:43-01:02Z from the window's own gap entries, W64) · moved: **variance tools + power ledger (every open hypothesis dated); H-MEAS-1: CLV licensed in 1 of 50 families (MLB F3), median effective-sample multiplier ~410x where licensed, and the close shows the favourite-longshot signature on NHL ML (slope 1.71), NBA ML (1.26), NHL team total (1.10) → Wave 125.3**

| # | Block | Model | Status | Outcome |
|---|---|---|---|---|
| 124.1 | measurement core | Sonnet | ✅ #557 | variance.py (control variate, pairing, partial pool, clustered MDE, CLV); POWER_LEDGER: CLV swap is the largest shortening (H-EXEC-2 3,128 → 30 games) where licensed |
| 124.2 | H-MEAS-1 | Sonnet | ✅ #558 | LICENSED 1 (MLB F3), NOT LICENSED 19 (10 miscalibrated incl. NHL / NBA ML favourite-longshot), UNDERPOWERED 30 |
| 124.3 | H-EXEC-4 | Sonnet | 🟡 #554 open | pre-registered + look schedule (first look 12-01, O'Brien-Fleming; 2-6 h lead n 310 ~12-26); lands in 125.1 Part 0 |
| 124.4 | capture | Sonnet | 🟡 #556 open | built; its own gate refuses the install (projected 93.9% at 74% disk); lands in 125.2 Part 0 with a fresh dry run |
| 124.5 | H-DEPTH-PAM-3 | Sonnet | 🟡 #555 open | code + known-answer test; judged seasons not read; side project, B-115 NEXT |

### ✅ WAVE 123 — WRITTEN 2026-11-20 ~18:30 UTC · CLOSED 2026-11-20 ~21:40 UTC (operator 13:43 PT) · SW-9 · four test blocks (123.5 registry backfill not sent; carried as B-110) · verified on GitHub (#549 #550 #552 #553 merged; handoffs W123_1..4) · moved: **the four edge-location branches answered: H1 attention NOT SUPPORTED on 18 judged non-headline families, props UNDERPOWERED (no fit window); H2 timing NOT SUPPORTED (drift unpredictable; CLV +0.86c vs 1.08c fee); H3 news NOT SUPPORTED on NBA injury / starter news (+0.3-0.5c left at +5 min vs 1.9c cost, repriced < 1 min); H4 quoting NOT SUPPORTED (0 of 18 cells, gross negative). Intervals too wide where it matters → Wave 124 tightens the measurement**
- 123.1 H1 #553 · 123.2 H2 #549 · 123.3 H3 #550 #552 · 123.4 H4 (result in h4_execution/RESULT.md) · 123.5 not sent.

### ✅ WAVE 122 — WRITTEN 2026-11-20 ~15:55 UTC · CLOSED 2026-11-20 ~18:00 UTC (operator 10:00 PT) · SW-9 · four build blocks · moved: **NBA points priced and logging; pot of gold scored (0 earned, next look 12-10); NFL in-play cells need a live feed; MLB 2027 board priced, 12 game cells in the dry run, GG-1957 cause found**

| # | Lane | Block | Model | Status | Outcome |
|---|---|---|---|---|---|
| 122.1 | D6 · NBA props · 3 | NBA points priced by the engine; the earned points split fires on shadow rows; props D6 counted on the box | Sonnet | ✅ | NBA points priced and logging T1-T3 on the box (B4: points joins REB / AST / 3PT); props D6 0 (layer 2 missing on prop rows). |
| 122.2 | arms · 3 | The pot-of-gold arm re-scored on all data to date (NBA / NHL / NFL, props included) and logged beside v1 as a candidate | Sonnet | ✅ | Pot of gold: 0 earned · 17 IN_SAMPLE (15 MLB + 2 NFL) · 0 closed; forward sample 56 contracts; next look 12-10; candidate logged. |
| 122.3 | D6 · NFL · 3 | NFL board widened: engine prices for the 17 unpriced NFL cells; the weekend slate's D6 recount | Sonnet | ✅ | NFL PASS_YDS T1 priced at its own horizon; 16 NFL cells are in-play (T4 / T5) with no live NFL feed; recount after 11-22 / 23. |
| 122.4 | D6 · MLB · 3 | MLB 2027 board priced from the pitch store (game families x bands), every registered cell logging from opening day | Sonnet | ✅ | MLB board priced from the pitch store; 12 game cells log in the opening-day dry run (3 → 12); GG-1957 cause: crons armed late + a silent exit; #544. |

### ✅ WAVE 121 — WRITTEN 2026-11-19 ~06:55 UTC · CLOSED 2026-11-20 ~15:30 UTC (operator 07:38 PT) · SW-9 · four Sonnet blocks · moved: **weekly evidence look built, first look 0 arms on every map (next 11-24); NBA props scored - 1 earned split (points, unpriced); dollar ceiling per arm (top: NBA spread T3 FADE ~$831 / day at $10k, interval spans 0); Live Terminal panels; Mac weekly copy loaded**

| # | Lane | Block | Model | Status | Outcome |
|---|---|---|---|---|---|
| 121.1 | proof | Weekly look runs itself | Sonnet | ✅ #538 | First look (140,223 rows): 0 arms on every map; install awaits the operator. |
| 121.2 | D6 · props | NBA props through the tree | Sonnet | ✅ #540 | 14 kept, 1 earned (points; no engine price yet); nba_props candidate on REB / AST / 3PT. |
| 121.3 | execution | Capacity and dollar ceiling | Sonnet | ✅ #536 #539 | 51 cells with depth; FADE leads every sport; $25 event cap binds above $10k. |
| 121.4 | dashboards | Live Terminal panels; Mac job | Sonnet | ✅ #537 | 4 panels; Mac weekly copy loaded (Sundays 03:00). |

### ✅ WAVE 120 — WRITTEN 2026-11-19 ~05:20 UTC · CLOSED 2026-11-19 ~06:30 UTC (operator 11-18 22:40 PT) · SW-9 · four blocks · moved: **candidate maps (router v2, nba_depth, nhl_v2) logged beside v1 on box rows (approved 21:19 PT); NFL split verdicts on box rows (D6 NFL recount on the 11-22 slate); held readers read .gz (1.87 GB → compressible); Mac copy 7.2 → 5.7 GB; strategy and architecture docs match the doctrine**

| # | Lane | Block | Model | Status | Outcome |
|---|---|---|---|---|---|
| 120.1 | D6 · NFL | NFL layer 3 on box rows | Sonnet | ✅ | filter_splits lacked the W113.2 NFL entries; late weather dropped filters on 25 / 150 rows; both fixed; recount after the 11-22 / 23 slate. |
| 120.2 | depth · router | Candidate maps beside v1 | Sonnet | ✅ #534 #535 | router_candidates on every shadow row (ON); NBA 71 / NFL 73 rows in 72 h; NHL verdicts logged, not applied. |
| 120.3 | infra · io | Held readers; Mac copy compressed | Sonnet | ✅ | Held 1.87 GB → 0; Mac 7.21 → 5.70 GiB (~100-150 MB / month); weekly job awaits the operator. |
| 120.4 | docs | Docs to the doctrine; superseded PRs | Haiku | ✅ | STRATEGY / ARCHITECTURE overviews rewritten; #477 #458 closed. |

### ✅ WAVE 119 — WRITTEN 2026-11-18 ~06:30 UTC · CLOSED 2026-11-19 ~05:00 UTC (operator 11-18 21:01 PT) · SW-9 · four Sonnet blocks · moved: **D6 4 → 13 on the box (NBA 7, NHL 6); NHL store built (1,737 games); nba_depth wired behind its switch; registry = box (B1 60); ride-board log cut; FADE inside-spread forward test live; evidence copied off the box to the Mac (7.2 GB, sha-verified)**

| # | Lane | Block | Model | Status | Outcome |
|---|---|---|---|---|---|
| 119.1 | D6 · NHL | NHL store, splits, router v2 | Sonnet | ✅ | Store on the box (84.6 MB); goalie + special teams 8 held-out positive of 42 leaves, 0 BH; router v2 + prior arms 0 / 99; D6 NHL 6 / 21. |
| 119.2 | depth · NBA | Depth wired; registry truth; layer 4 | Sonnet | ✅ #527 | +nba_depth behind the switch (off); B1 by code 48 → 60 = box; D6 NBA 4 → 7. |
| 119.3 | execution | Ride-board log; FADE inside; re-fit | Sonnet | ✅ #526 #528 | Log cut to 12 fields; EXP-W119.3 FADE inside 50 / 50 (touch 22 / 342, inside 2 / 17 - counts only); GG-1943 fixed. |
| 119.4 | infra | Evidence to the Mac; readers .gz; disk | Sonnet | ✅ #529 | 7.2 GB / 5,827 files copied, sha match; ~45 readers on io_jsonl; 1.87 GB held behind 3 readers; weekly job written, not loaded. |

### ✅ WAVE 118 — WRITTEN 2026-11-18 ~05:40 UTC · CLOSED 2026-11-18 ~06:25 UTC (operator 11-17 22:21 PT; 118.3 cut short by session limits) · SW-9 · four Sonnet blocks + gap burner · moved: **MLB 12 cells routed NO BET (the 2026 ledger is postseason only, GG-1957); 5 NBA depth classes built from the archive, 12 kept leaves, not wired; NHL goalie lag closed (0.2c); disk retention as code (install run by the window); gap burner 264 → 174**

| # | Lane | Block | Model | Status | Outcome |
|---|---|---|---|---|---|
| 118.1 | proof · MLB | MLB 2026 through router v2 | Sonnet | ✅ #522 | Postseason only (22 games): v2 0 / 80 leaves armed; 12 cells NO BET provisional; always-FADE −0.078 [−0.124, −0.027]; frozen 2027 map + prereg. |
| 118.2 | depth · NBA | NBA archive factor classes as splits | Sonnet | ✅ #523 | S1 / S2 / S4 kept 12 leaves (best S2 SPREAD T3 MOMENTUM +0.155, lower +0.048, 16 games); 0 BH; S3 / S5 thin. |
| 118.3 | D6 · NHL | NHL store, goalie timing, router v2 | Sonnet | ✂️ #520 #524 | Goalie lag 0.2c (n 14): closed, NO BET. Store not built on the box yet; D6 NHL 0 → carried to 119.1. |
| 118.4 | infra | Disk measured, retention as code | Sonnet | ✅ #521 #525 | 87% (+1.54 pt / day); dry run frees ~3.36 GB; ride-board log 1.0 GB / week. |

### ✅ WAVE 117 — WRITTEN 2026-11-18 ~01:55 UTC · CLOSED 2026-11-18 ~05:15 UTC (operator 11-17 21:10 PT) · SW-9 · cleanup + four blocks (Sonnet / Haiku) · verified on GitHub (#509-#519 merged; handoffs W117_0..W117_4) + box (`20261118T05*`) · moved: **no arm-and-option clears zero after real costs (FADE crossed +0.166 [−0.016, +0.348], 20 games); NHL prior 1-7 weeks earlier, coarse leaves later; Kalshi ≈ books at the NHL moneyline close; D6 3 → 4; NHL store installed; healthcheck false FAIL fixed; live handoffs 644 → 42**

| # | Lane | Block | Model | Status | Outcome |
|---|---|---|---|---|---|
| 117.0 | cleanup · 2 | Land #508 #505 #506 #507 on green; prune remote branches (merged or nothing unlanded); prune worktrees | Sonnet | ✅ | #505-#508 merged on green; remote branches 16 → 10 + main; 8 kept with unlanded commits (12_EXPLORATORY/branch_cleanup_w117/LIST.md). |
| 117.1 | execution · 3 | Caps raised (approved); spread logged on every order + backfilled; FADE crossed measured with its real cost; frozen placement table, policy on (approved) | Sonnet | ✅ | #512 #514 #519 merged. Game-clustered with real spread: FADE crossed +0.166 [−0.016, +0.348] (105 orders / 20 games), RIDE +0.016, MOMENTUM +0.052 - no arm and option clears zero. Spread backfilled 454 / 486. NFL per-leaf → NO BET. Caps raised; policy on but table has 0 cells (no-op). |
| 117.2 | quant · 3 | NHL consensus history as a router-v2 prior; momentum and Kalshi-vs-books tests pre-registered; family vs leaf power calendar | Sonnet | ✅ | NHL prior: first arm 1-7 weeks earlier (NFL 7 with nflverse); coarse leaves 6-40 weeks LATER. Momentum closed (all intervals contain 0). Kalshi vs books, NHL ML n 1,312: gap +0.0016, riding consensus at ask −0.055. No first arm before 2027. |
| 117.3 | D6 · 3 | NBA layer 1 for moneyline + team totals; the named NBA layer causes; D6 recount on the box | Sonnet | ✅ | #511 #516 merged. D6 3 → 4 (NBA_TEAM_TOTAL T3 added); NBA layer 1 12 → 15; stump rule from box rows. Healthcheck false FAIL (SIGPIPE) fixed; NHL store installed by the window 05:04Z, builds 13:29Z. |
| 117.4 | hygiene · 3 | Every push to main checks the backlog and GG ids; handoffs older than 7 days archived; gaps with merged fixes resolved | Haiku | ✅ | docs_guard on every push (#510); handoffs live 644 → 42; health_read (#509); OPEN gaps 273 → 272. |

### ✅ WAVE 116 (OPUS) — WRITTEN 2026-11-17 ~06:30 UTC · CLOSED 2026-11-18 ~01:40 UTC (operator 11-17 17:39 PT) · SW-9 · three Opus blocks finishing the Fable wave · verified on GitHub (#503 #504 merged and deployed 00:54Z; #505 #506 #507 #508 green-ready after the window's backlog fix 7e97f1f, landed by 117.0; handoffs W116_1 / W116_2 / W116_2_APPROVALS / W116_3) + box (`20261118T00*`) · moved: **router v2 built and frozen (arms 0 leaves held out; v1 NFL −0.020 per row, interval below 0); power calendar - first arm 2027-07 at +2c; join lookups failed 244 → 0; FADE crossed +0.183 [+0.089, +0.277] before its crossing cost; router ERROR fixed; D6 3 / 117 (NBA); NHL store 2,049 → 270 MB**

| # | Lane | Block | Model | Status | Outcome |
|---|---|---|---|---|---|
| 116.1 | quant · 3 | Finish 115.1: evidence pipeline, three routers held out, power calendar, v2 map behind a switch, router v2 frozen | Opus | ✅ (#506 merged 2026-11-18, 5ddaf0d) | v2 arms 0 of 356 leaves (fit) / 365 (all); held out v1 −0.0064 [−0.0138, +0.0009], NFL −0.0201 [−0.0369, −0.0054]; ride every favourite −0.0256; Fable's e-process false claims 275/300 → 2/300 after a binary variance floor; calendar at +0.02 first 2027-07-21, median 2028-05-10; GG-1936..1938, GG-1954. |
| 116.2 | execution · 3 | Finish 115.2: placement model tests, settlement join, policy behind a switch, report per arm and option, ADR-0072 addendum | Opus | ✅ (#504, #505 a795d84, #508 3563e58 merged; ARM_BOOK_CAPS unchanged, 117.1 flips it) | Lookups failed 244 → 0 of 486. RIDE fills win 69% vs 81% unfilled (adverse), E2 −0.008 after fees; MOMENTUM 50 / 50, +0.075; FADE 6 of 111 filled, +0.106; option "cross" best for every arm, FADE +0.183 [+0.089, +0.277] - spread not logged. Operator approved the cap raise (after GG-1942) and the placement policy (after a frozen spread-logged table). |
| 116.3 | D6 · 3 | Finish 115.3: trace, fixes, row-level sizing, D6 recount; NHL store shrunk | Opus | ✅ (#503, #507 aa86608 merged; nhl_event_store_install NOT run, waits on operator approval) | Router ERROR = KeyError market_ticker (GG-1939), fixed; size_for on every routed row; D6 3 / 117 named (NBA_GAME_TOTAL T3, NBA_SPREAD T2 / T3); trace tables + 5 coverage findings (GG-1951); NHL store fits (270 / 318 MB), `nhl_event_store_install` awaits approval. |

### 🟡 WAVE 115 (FABLE) — WRITTEN 2026-11-17 ~01:30 UTC · STOPPED ~01:18 UTC on usage (operator addendum) · SW-9 · three Fable blocks, all PARTIAL · pushed: branches w115-1-evidence (73c3fa8), w115-2-placement (bdf2847); #502 merged 06:01Z (115.3 resumed at the 22:00 reset) · designed: pooled + sequential evidence rule; GG-1935 answered (the "breaker" is a placed-stake cap, not a loss); NHL rows routed · finished by Wave 116 (Opus)

| # | Lane | Block | Model | Status | Outcome |
|---|---|---|---|---|---|
| 115.1 | quant · 3 | Evidence design: pooled, sequential evidence so leaves earn arms; power calendar; routing v2 pre-registered | Fable | 🟡 PARTIAL | Stopped on the usage addendum. Branch `session/20261117T010343Z-w115-1-evidence` (pushed, no PR): pooling model + always-valid sequential test written and checked against closed forms. Not started: pipeline, three-router comparison, power calendar, leaf map v2, pre-registration. No measured result yet. Handoff: `11_MEMORY_HANDOFF/SESSION_HANDOFF_20261117T011739Z_W115_1.md` |
| 115.2 | execution · 3 | Execution as a decision: fill and adverse-selection model, placement policy per arm, the breaker, settled P&L per arm | Fable | 🟡 PARTIAL | stopped on usage. Branch `session/20261117T010348Z-w115-2-placement` @ bdf2847, no PR, nothing merged. Done: GG-1935 answered, demo arm-book caps separated from the real-money limits, order rows log the book at submit. Not done: GG-1934 join, placement tests / policy / switch, addendum proposal. Handoff W115_2 |
| 115.3 | D6 · 3 | One game end to end on the box, per sport: trace all seven layers, fix every break; 3 wired cells → every in-season sport | Fable | 🟡 PARTIAL | Stopped on the usage addendum. Branch `session/20261117T010353Z-w115-3-d6-one-game` @ 1ce79c5, PR #502 (CI pending, unmerged): NHL rows routed, NFL layer-3 rule fixed, router ERROR message logged, `d6_trace_read` task. D6 still 3 / 117; trace not run; NHL store needs 0.9-2.0 GB and does not fit the box as built. Handoff `SESSION_HANDOFF_20261117T0115Z_W115_3.md`. |

### ✅ WAVE 114 — WRITTEN 2026-11-13 ~00:35 UTC · CLOSED 2026-11-13 ~01:07 UTC (operator 11-12 17:07 PT) · SW-9 · four blocks, Sonnet, two parts · verified on GitHub (#494 #497 #498 #499 #500 #501 merged, main CI green) · moved: **Muse intake landed (NBA index 24 → 36); D6 measured ON THE BOX for the first time (0 / 117; 4 cells one layer short); arm orders: RIDE 162 / 21 fills, FADE 37 / 1, MOMENTUM 7 / 1; the orchestrator defers to the router (D-04)** · open: layer 3 on the box NBA only (GG-1898, GG-1933), NHL rows unrouted on the box, daily breaker skips (GG-1935), teammate-pool hypothesis closed (parked)

| # | Lane | Block | Model | Status | Outcome |
|---|---|---|---|---|---|
| 114.1 | data · 2 | Land PR #494 (Muse intake): resolve the conflict, CI, merge; wire the NBA distance filters | Sonnet | ✅ | #494 ae7562b, #500 499522d; NBA index entries 24 -> 36; 54 leaves scored, 5 kept, 0 BH; 14-day NBA RIDE 651 -> 382 (kept splits conflict) |
| 114.2 | proof · 2 | D6 counted on the box: arm_orders_read + d6_read box tasks; first real D6 and E1-E3 per arm | Sonnet | ✅ | #498 e8e06a1; D6 0/117 on the box; E1 fills RIDE 21/162, FADE 1/37, MOM 1/7, E2/E3 null (0 settled); NHL layer 3 = 0 (no NHL_EVENTS box job, Monday proposal in handoff); NFL layer 3 = 0 on box (GG-1933); GG-1934, GG-1935 |
| 114.3 | window · 2 | Doctrine leftovers: orchestrator defers to the router; scorers per leaf per arm; edge-map rows | Sonnet | ✅ | #497 c5b97f4, #499 e862d90, docs 330fbd2; E09 / E14 arm tables still open |
| 114.4 | engine · 2 | NBA joint teammate legs: shared usage pool so teammate PTS / AST co-move the right way | Sonnet | 🟨 | #501 d9db05a; latents built (default off), tested; held-out teammate PTS x PTS +0.0230 -> +0.0224 not closed, PTS x AST +0.0108 -> +0.0078; Brier unchanged; hypothesis closed (W114.4 team-pool latents, parked for R&D) |

### ✅ WAVE 113 — WRITTEN 2026-11-12 ~06:30 UTC (revised 23:03Z) · CLOSED 2026-11-13 ~00:18 UTC (operator 11-12 16:18 PT) · SW-9 · four blocks · verified on GitHub (#493 #495 #496 merged, main CI green; #494 conflicted) · moved: **layer 3 NFL 0 → 13 cells; 25 NFL index entries; D5(b) NFL 12 → 14 of 23; arm orders sized by size_for; same-player PTS x 3PM joint gap closed** · open: D6 uncountable from the repo (→ 114.2), Muse intake unmerged (→ 114.1), teammate legs (→ 114.4)

| # | Lane | Block | Status | Outcome |
|---|---|---|---|---|
| 113.1 | trees · 3 | First cells wired end to end (NBA, NHL): size_for in the order path, NHL filters supplied, layers 6 / 7 counted, D6 recounted | ✅ | #493 c097744: arm orders sized via size_for; NHL per-row filters (local only, GG-1898); D6 still 0 - uncountable without a box read of the arm-order log → 114.2 |
| 113.2 | NFL · 3 | NFL wired for Sunday: weather forecast store, MatchupBook, the NFL granularity index (box count, personnel, coverage) as tree splits, per leaf per arm | ✅ | PR #495 merged 9b3e25a, box deployed (6f40c9a7). Layer 3 NFL 0 to 13 cells; 25 index entries (13 scored); D5(b) 12 to 14 of 23. Handoff `11_MEMORY_HANDOFF/SESSION_HANDOFF_20261113T0000Z_W113_2.md` |
| 113.3 | engine · 3 | NBA joint: shared minutes / usage / pace latent so same-player and teammate legs price right; parlay pot-of-gold branch | ✅ PARTIAL (A,B,C built; PR #496 merged a5cffd2, CI green) | same-player PTSx3PM cov gap +0.086 -> -0.004; teammate PTS, PTSxAST teammates, WINxREB not closed; see SESSION_HANDOFF_20261113_W113_3.md |
| 113.4 | data · 3 | The bot reads Muse's archive (pinned, read-only), grades it by recompute, turns VERIFIED tables into index entries | ⚠️ | built on PR #494; merged in 114.1 (ae7562b); handoff SESSION_HANDOFF_20261112T2344Z_W113_4.md ✅ |

### ✅ WAVE 112 — WRITTEN 2026-11-12 ~01:15 UTC · CLOSED 2026-11-12 ~06:13 UTC (operator 11-11 22:13 PT) · SW-9 · four blocks · verified on GitHub (#486 #487 #488 #489 #492 merged, main CI green; handoffs W112_1..4) · moved: **D6 layer 3 NBA 0 → 9 cells; layer 6 built (size_for); layer 7 built and switched on in the repo (box DRY on an override — window clearing it); closed hypotheses replace closed arms (D-03 BUILT); D5(b) NHL applied 3 → 8 of 12** · open: 112.4 Part B (goalie timing), D6 wired still 0 (the pieces are not joined → 113.1)

| # | Lane | Block | Status | Outcome |
|---|---|---|---|---|
| 112.1 | trees · 3 | Layer 3: every runner hands its factor filters to the router as tree splits; D6 counted | ✅ PARTIAL | #488 merged d536a9c, CI green. NBA wired (layer 3 cells 0→9); NFL/NHL log why not wired. D6 wired still 0/117. |
| 112.2 | quant · 3 | Layer 6: a sizing rule per arm (Kelly 0, flat demo stakes, per-game and same-game correlation caps) + closed hypotheses, not closed arms | 🟡 PR open | Parts A+B+C code done (closed hypotheses 2; `arm_sizing.size_for`; replay script). 14-day replay NOT run on real rows (rows are on the box; needs a read task). Wiring into 112.3 is the window's. Handoff `SESSION_HANDOFF_20261112T0130Z_W112_2.md` |
| 112.3 | execution · 3 | Layer 7: the router's arm drives the demo forward test's orders; fills measured per arm (AUTHORIZED 16:51 PT) | 🔶 Parts A+B merged (#486); Part C: ARM_ORDERS=on merged (#492), box override (ARM_ORDERS=dry) cleared by the window 2026-11-12 06:43Z via demo_fill_rearm (authorized 11-11 16:51 PT): the box now runs ARM_ORDERS=on; first arm_order rows confirmed by 113.1 | W112.3 session |
| 112.4 | engine · 3 | NHL factor classes point-in-time from the shot store, applied as router filters | 🟡 Parts A+C merged (PR #489); Part B (goalie timing, Muse snapshots) open | D5(b) NHL applied 3 -> 8 of 12 |

### ✅ WAVE 111 — WRITTEN 2026-11-11 ~23:59 UTC · CLOSED 2026-11-12 ~00:45 UTC (operator 11-11 16:46 PT) · SW-9 · four blocks · verified on GitHub (#481 #482 #483 #484 #485 merged, main CI green; handoffs W111_1..4); box deploy read requested · moved: **D-02 / D-03 CONTRADICTED → BUILT (a losing look closes only the fade arm; 0 closed cells); 41 code decision points audited; router reads the leaf map; arms scored per leaf 4 → 6; leaf-map forward test frozen; NBA index 24 entries, D5(b) NBA 10 → 11** · D6 0 / 117 (layers 3, 6, 7 open)

| # | Lane | Block | Status | Outcome |
|---|---|---|---|---|
| 111.1 | proof · 3 | A losing look closes only the fade arm; NFL game total T1 / T2 reopen as SHADOW (D-02, D-03) | ✅ | PR #482 merged (c592dda, CI green on 351f659); handoff SESSION_HANDOFF_20261112T001539Z_W111_1.md; box deploy not read this session |
| 111.2 | window · 3 | Doctrine-conformance audit: every decision point in code vs DOCTRINE.md; fix what no block owns (D-04, D-05) | ✅ | A, B (PR #481 merged, CI green), C and edge-map wording done; 41 decision points audited; findings handed to 111.1 / 111.3 / backlog in the handoff |
| 111.3 | trees · 3 | D6: router reads the per-leaf arm map; pot of gold + momentum scored as arms; D6 scorecard; forward test frozen | ✅ | PR #483 de8b003, #484 7846dec, CI green, box at 7846dec1. D6 0/117 wired (layers 3,6,7 open); arms scored per leaf 4→6; forward pre-reg frozen (116 tests) |
| 111.4 | engine · 3 | The granularity index as tree splits, NBA: split · rank vs history · matchup cross · market map · application | ✅ | PR #485 3d59e57, CI green. 24 entries; 18 scored per leaf (85 leaves, 0 BH survivors, fit-picked arms routed NO_BET provisionally); `nba_filters(home_profile, away_profile)` for the router; seat B7 applied, D5(b) NBA 10→11 of 17. GG-1895. |

### ✅ WAVE 110 — WRITTEN 2026-11-11 ~05:30 UTC · CLOSED 2026-11-11 ~07:00 UTC · SW-9 · five blocks (four + 110.5 at the operator's ask) · verified on GitHub (#473 #475 #476 #478 #479 merged, main CI green; handoffs W110_1..5) · moved: **D5(b) NFL applied 10 → 12, NBA 5 → 10; 27 of 117 cells log a router arm; same-game correlation measured (right for game x points legs, wrong for same-player cross-stat); every settled shadow row scored by arm per leaf (365 leaves, 113 routed, 3 family-level leads)** · D6 still 0 (the router does not read the leaf map → 111.3)

| # | Lane | Block | Status | Outcome |
|---|---|---|---|---|
| 110.1 | engine · 3 | NFL: weather + matchup classes applied in the engine (D1, D5b) | ✅ MERGED PR #473 (567477f) | Weather PIT + matchup crosses exported as filters (`nfl_engine/filters.py`) for 110.3's router; D5(b) NFL applied 10→12. Per-leaf net after costs: 0/82 leaves earn an arm (~2 by chance); MOMENTUM unscorable (one closing line); no NFL Kalshi spread/totals history. Box deploy: t4-mlb not_needed. |
| 110.2 | engine · 3 | NBA: the 9 "interpreted" factors → applied through the tree (D5b NBA 5 → ?) | ✅ DONE (PR #475 merged @58c1cb1, CI green): D5(b) NBA applied 5 → 10 of 17 (B10, B12, B13, P1, P2). Held-out n=2268 vs realized outcomes: usage improves spread −0.0041 [−0.0063,−0.0019] and team total −0.0017 [−0.0026,−0.0009] Brier; geometry, officials null; PAM hindsight-only; ml no gain. No 2025-26 Kalshi spread/total quotes → no market comparison beyond 109.1's ml NULL. 12_EXPLORATORY/nba_applied_w110/RESULT_W110_2.md | — |
| 110.3 | trees · 5 | Every registered cell routed (ride / fade / momentum / pot of gold / no-bet), horizon depth, orders OFF | ✅ MERGED PR #476 (c57a496) | Coverage 27 of 117 registered cells routed (NHL 9/9, NFL 9/13, NBA 9/24, MLB 0/18). Shadow rows now log the router decision (branch, depth, reason; logging only). 14-day replay: 25,263 decisions, all NO_BET (null; n=0 scored) - bounded by date-only tickers and IN_SAMPLE cells, not by the router. |
| 110.4 | quant · 4 | Same-game correlation from the NBA engine (game lines + props), checked on settled games | ✅ DONE (PR 478) | Engine joint good for game x team/player pts; misses same-player cross-stat and teammate pts sign; no open Kalshi NBA combo. RESULT.md in 12_EXPLORATORY/sgp_correlation |
| 110.5 | proof + trees | RETRO-ROUTE: every logged shadow row + archived price through ride / fade / momentum / no bet, per leaf, held out | ✅ DONE (PR 479 merged) | 365 leaves: 189 thin, 113 routed, 1 BH lead (NHL ML T2, 11 games, below 15-game bar), 0 prereg drafts. ROUTING.md in 12_EXPLORATORY/retro_route/ |

### ✅ WAVE 109 — WRITTEN 2026-11-11 ~00:45 UTC · CLOSED 2026-11-11 ~05:30 UTC (operator 11-10 18:37 PT) · SW-9 · five blocks + 109.6 red · verified on GitHub (#462-#472 merged, main CI green 6a56768; handoffs W109_1..6) + box (re-arm check: epoch-gated trips none; RE-ARMED 02:39Z) · moved: **D5(a) NBA 4 → 8, NHL 2 → 7; +9 NBA prop SHADOW cells (EXP-047, install pending); props net of costs 3 of 3 sports measured, 0 of 22 net-positive; forward test stop found to be an artifact, gated, alarmed, re-armed**

| # | Block | Status | Outcome |
|---|---|---|---|
| 109.1 | NBA architecture | ✅ DONE | #463 8/8; applied path (ml) NULL: market Brier 0.1529 vs tree 0.1745, n 397 |
| 109.2 | NHL architecture | ✅ DONE | #465 7/8 (clusters wait for NHL archetypes); no 2023-25 market history |
| 109.3 | NBA props from the engine | ✅ DONE (install pending) | #466 EXP-047, +9 SHADOW cells; backtest market better on points / reb / ast / 3s |
| 109.4 | Props net of costs | ✅ DONE | #472 NBA / NFL not mispriced after costs, NHL underpowered; 0 of 22 net-positive |
| 109.5 | The reds | ✅ DONE (install pending) | #464 memory, #462 MLB sync skip, #468 MemoryMax install prepared; budget GREEN |
| 109.6 | Forward test silent | ✅ DONE | ARTIFACT (pre-GG-1771 markouts); #469-#471 gate + alarm; re-armed by window 02:39Z |

### ✅ WAVE 108 — WRITTEN 2026-11-10 ~03:40 UTC · CLOSED 2026-11-11 ~00:45 UTC (operator 11-10 16:14 PT) · SW-9 · four blocks + 108.5 red · verified on GitHub (#454 #455 #456 merged; #458 UNMERGED; window #457 #459 merged; handoffs W108_1 / 3 / 4 / 5) · moved: **edge map 40 rows, UNTESTED 5 → 4 (NBA / NHL ride board NO EFFECT NET); 22 prop series in the archive cron (not installed - Hard Rule 14); weather scoped: Kalshi beats a free forecast (Brier 0.098 vs 0.137), no build; /visual redesigned and refreshing on pull**

| # | Block | Status | Outcome |
|---|---|---|---|
| 108.1 | Untested rows + props in the archive | ✅ DONE (install pending) | L03, R09 NO EFFECT NET (Holm 0 of 12, 0 of 4); stale GG-1330 line fixed; #456: 22 NBA / NHL / NFL prop series, install refused (budget red) |
| 108.2 | News lag at trade resolution | ⏭ NOT RUN | carried: B-063 NEXT |
| 108.3 | Props net of costs | ◐ PARTIAL | settled-prop quotes public via batch candlesticks; Part B → 109.4 |
| 108.4 | Weather scoping | ✅ DONE (2 cities) | #454; NYC + CHI 1,038 markets: market Brier 0.098 vs forecast 0.137, toward-forecast -3.1c net; no build recommended |
| 108.5 | Red: stale /visual, memory cap | ◐ PARTIAL | #455 read tasks merged; #458 UNMERGED (memory) → 109.5; stale page fixed by window #457 / #459 |

### ✅ WAVE 107 — WRITTEN 2026-11-10 ~02:20 UTC · CLOSED 2026-11-10 ~03:40 UTC (operator 11-09 19:24 PT) · SW-9 · three blocks · verified on GitHub (#452, #453 merged; 107.3 be5c217 on main; main CI green 978172a; all handoffs) + box (`20261110T032445Z_*`: HEALTHY, 89 live, no silent arm, budget RED = ride board + news burst not installed) · moved: **edge map on one page and /visual (39 hypotheses: 0 survive costs forward; 14 accruing, 13 no effect net, 7 ruled out, 5 untested); information speed NO at 20-min resolution (injury news moves the moneyline +0.3c, below the 1.5-2.3c cost); v3 does not lead Kalshi (-0.06c). Exit test failed - strategy recommendation sent (Needs your decision)**

| # | Block | Status | Outcome |
|---|---|---|---|
| 107.1 | The edge map | ✅ DONE | #452: EDGE_MAP.md + /visual panel; its "NBA / NHL archive does not exist (GG-1330)" line is stale - fixed by 108.1 |
| 107.2 | Information speed | ✅ DONE | #453: 276 events / 128 games, +0.3c @20min CI [-0.0, +0.8] = NO net; burst capture PREPARED, not run |
| 107.3 | NBA availability lead | ✅ DONE | be5c217: 1,553 tickers / 42 games, drift toward v3 -0.06c CI [-0.27, +0.14]: no lead shown |

### ✅ WAVE 106 — WRITTEN 2026-11-06 ~06:20 UTC · CLOSED 2026-11-10 ~02:20 UTC (operator 11-09 18:07 PT) · SW-9 · four blocks · verified on GitHub (#447-#451 merged; main CI green 8bab993; all handoffs) + box (`20261110T020717Z_*`: HEALTHY, no silent arm, budget RED = ride board not installed) · moved: **pot of gold grafted (5 router branches); cost wall measured - maker negative everywhere, taker 1.5-2.3c / 4-8c; props not mispriced net (0 of 50); MLB lineup model loses to the market (w = 0); NBA coverage 3 of 3 every night**

| # | Lane | Block | Status | Outcome |
|---|---|---|---|---|
| 106.1 | rank 1 | Land #447; graft pot of gold | ✅ DONE | #447 + #451: router 4 -> 5 branches, 17 pot cells routed (paper, 0 orderable), ROUTER_TREE.md |
| 106.2 | quant | The cost wall | ✅ DONE | #448 quant/costs.py: taker 1.5-2.3c each way (game lines), 4-8c (props / team totals); maker net negative in every bucket; demo-fee check blocked |
| 106.3 | quant | Retail flow: props | ✅ DONE | #450: 0 of 50 MLB cells net positive held out; thin books lose 8-20c; props not more mispriced than lines |
| 106.4 | engine · 2 | MLB step 2 | ✅ DONE | #449: 4 PIT factor classes; beats naive +0.0016 Brier, loses to the market; blend w = 0 moneyline |

### 🟨 WAVE 105 — WRITTEN 2026-11-06 ~02:40 UTC · CLOSED 2026-11-06 ~06:20 UTC (operator 11-05 22:09 PT; some blocks cut short for the usage limit) · SW-9 · six blocks (3 + 3 added at the operator's ask) · verified on GitHub (#440-#444, #446 merged; #445 duplicate 105.5 closed unmerged; **#447 (105.6) open**; main CI green ee12477) · moved: **nothing measured survives costs - ride / fade cells 0 earned, pot-of-gold 0 of 17 orderable, no placement rule wins; NBA blend test frozen with looks 12-29..02-15; MLB pitch store 1.42M pitches; ride board built, orders OFF**

| # | Lane | Block | Status | Outcome |
|---|---|---|---|---|
| 105.1 | quant · 1 | Blend test pre-registered | ✅ DONE | #441 power module, frozen NBA pre-registration, 4 looks per cell (final 12-29 v3 .. 02-15), gated read task |
| 105.2 | quant | Order data + placement | ✅ DONE | #440 6 order fields, GG-1793 / 1794 / 1810 resolved; #443 no rule makes fills win; price cap < 0.50 cuts loss ~40% |
| 105.3 | engine · 2 | MLB data layer | ✅ DONE | #444 Savant pitch store, 2 seasons, PIT tables; held-out Brier vs naive spans 0 |
| 105.4 | ride · 1 | Ride / fade cells | ✅ DONE | #446 net of costs the fades LOSE held out (NFL team totals -0.08, NHL totals -0.52, NBA all negative); 0 cells earned |
| 105.5 | ride · 1 | Router wired to demo orders | ✅ DONE | #442 runner + order step, orders OFF; `ride_board_install` awaits your approval (#445 duplicate closed) |
| 105.6 | pot of gold · 1 | Longshot tree | 🟨 PARKED | 3 routes, 17 cells pre-registered, 0 orderable; PR #447 open, no CI -> 106.1 lands it |

### ✅ WAVE 104 — WRITTEN 2026-11-06 ~02:00 UTC · CLOSED 2026-11-06 ~02:40 UTC (operator 11-05 18:26 PT) · SW-9 · verified on GitHub (#433, #434, #436, #437, #438, #439 merged; main CI green b78cc2b; all W103 + W104 handoffs present) + box (`20261106T022654Z_*`: GREEN, no silent arm) · moved: **NBA blend weight w ~ 0 on 12 of 12 cells (0 beat Kalshi; ~30 games, unreadable intervals); fills -1.2c markout, E3 gap unexplained by logged fields; Wave 103's stranded quant landed; GG-1775 / GG-1783 closed**

| # | Lane | Block | Status | Outcome |
|---|---|---|---|---|
| 104.1 | quant | Fills and price impact | ✅ DONE | #439 quant/fills.py; fill model ECE 0.021 AUC 0.62; E3 gap explained -74% (CI -365..+191%, = 0); fills -1.2c 1-min markout, worse at high price; GG-1793 / 1794 |
| 104.2 | quant · 1 | Market-anchored blend weight | ✅ DONE | #437 quant/blend.py; NBA v1 / v2 / v3: w ~ 0 on 12 / 12 cells, 0 beat the market; NFL / NHL / MLB sealed, not read |
| 104.3 | urgent | Land W103's PRs; GG-1775; GG-1783 | ✅ DONE | #436, #434, #433 merged; W103.2 / W103.3 handoffs written; GG-1775 closed (scoring defect), GG-1783 closed (#438); GG-1810 |

### 🟨 WAVE 103 — WRITTEN 2026-11-05 ~06:50 UTC · CLOSED 2026-11-06 ~02:00 UTC (operator 11-05 17:43 PT) · SW-9 · four blocks (3 quant + red alert) · verified on GitHub (#431, #432, #435 merged; main CI green 53662ea; **#433, #434 conflicting + no handoff; #436 red**) + box (`20261106T014410Z_*`: 89 live, GREEN, no silent arm) · moved: **GG-1771 / GG-1770 fixed - NFL ADOPT INCONCLUSIVE on clean fills, forward-test clock restarted at the 01:03:42Z epoch (operator "Restart"); tails built (breach is day-variance, not tail)**

| # | Lane | Block | Status | Outcome |
|---|---|---|---|---|
| 103.1 | quant | Tails for the G6 limits | ✅ DONE | #432 quant/tails.py; 6 of 8 series fitted; every game tail bounded at the stake; T4M-PROJ MLB YES breaches 20% kill at 0.98 / 12 mo at Kelly 0.01; GG-1775 |
| 103.2 | quant | Overreaction and regimes | 🟨 NOT LANDED | #434 open, conflicting, no CI, no handoff -> 104.3 |
| 103.3 | quant | In-play NBA / NHL math | 🟨 NOT LANDED | #433 open, conflicting, no CI, no handoff -> 104.3 |
| 103.4 | RED ALERT | NO orders mirror-priced | ✅ DONE | #431 fix (6 of 6 paths); NFL ADOPT INCONCLUSIVE on clean data; #435 epoch 2026-11-06T01:03:42Z; GG-1783 open; main red from aae5e6c fixed |

### 🟨 WAVE 102 — WRITTEN 2026-11-05 ~06:10 UTC · CLOSED 2026-11-05 ~06:50 UTC (operator 11-04 22:35 PT) · five blocks (102.4 + 102.5 added at the operator's ask) · verified on GitHub (#422, #425, #426, #427 merged; #428 window, /visual picks panel) + box bridge (`20261105T063603Z_*`) · moved: **NBA misses root-caused (OOM burst; catch-up merged, install awaits approval); ADOPT gain split ~1c placement / ~18c selection; NFL ADOPT addendum PROPOSED, switch OFF; GG-1771 found (NO orders mirror-priced, HIGH); stray branches 35 -> 3**

| # | Lane · rank | Block | Status | Outcome |
|---|---|---|---|---|
| 102.1 | engine · 2 | NBA v2 / v3 misses; NHL goalie / rest; store lag | 🟨 PARTIAL | Root cause: OOM burst (481 kills since 10-30, invisible); #425 catch-up + attempt trace; `nba_engine_catchup_install` awaits your named approval; GG-1773 / 1774 open; B and C not started |
| 102.2 | proof · 1/4 | NFL ADOPT package; markout book key; GG-529 | ✅ DONE | ADR-0072 NFL addendum PROPOSED + switch OFF; markout rows carry book; GG-1750 (look day); EXP-038 second-look DRAFT |
| 102.3 | flex · 1/EXEC | Picks sheet; last settled night; demo refusals | ✅ DONE | #422 dedupe (259 -> 127 picks on 11-03); refusals 2,259, all 10-16..10-29, balance now logged (#426); **GG-1771 (HIGH) NO orders mirror-priced**, GG-1770 |
| 102.4 | quant · 4 | ADOPT decomposition; multiplicity ledger; calendar age | ✅ DONE | +0.190 = ~0.01 placement + ~0.18 selection; MULTIPLICITY_LEDGER.md; calendar-age panel (#427) |
| 102.5 | plumbing | Branch cleanup | ✅ DONE | 35 -> 3 stray branches (data x2 + #149) |

### 🟨 WAVE 101 — WRITTEN 2026-11-05 ~02:30 UTC · CLOSED 2026-11-05 ~06:10 UTC (operator 11-04 21:45 PT) · verified on GitHub (#417-#421, #423 merged, main CI green; **#422 open, conflicting, no CI**) + box bridge (`20261105T054745Z_*`) · moved: **the ADR-0072 NFL word read: ADOPT (first 11-02 11:25Z; not applied, operator's call); NHL totals challenger pre-registered, held-out NO; v3 coverage logged; proof calendar 65 rows with second-look state; branch list written (nothing deleted)** · partial: 101.1 D4 not measured and v3 read not run, 101.3 no handoff - both from the window's time-gated parts (W45)

| # | Lane · rank | Block | Status | Outcome |
|---|---|---|---|---|
| 101.1 | engine · 2 | NBA coverage after the lock; v3 first read; NHL totals challenger | 🟨 PARTIAL | #417 v3 coverage.jsonl, #418 nba_engine_coverage_read; #421 NHL spread-shrink challenger NO (TOTAL, TEAMTOTAL_AWAY better; TEAMTOTAL_HOME CI includes 0); coverage count + v3 read NOT run (gated 07:30Z - W45) |
| 101.2 | proof · 1/4 | The ADR-0072 NFL final word; 11-13 look ready; proof calendar | ✅ DONE | ADOPT: (a) +0.190 lo95 +0.088; (b) 0.376; (c) -0.012 [-0.033, +0.010]; code = addenda; NFLQB look ready (47 / 60 settled, fragile); #420 calendar aggregate + 65 rows |
| 101.3 | flex · plumbing/1 | Memory after the lock; picks night 2; branch list | 🟨 PARTIAL | #419 branch list (32 to delete, 2 data branches + #149 to keep, 1 your call) + box_memory_read_w101; #422 GG-1690 left open; memory + picks NOT done, no handoff (W45). Window read memory 05:48Z: 0 OOM kills since the lock, 375 MB available |

### 🟨 WAVE 100 — WRITTEN 2026-11-04 ~04:15 UTC · CLOSED 2026-11-05 ~02:30 UTC (operator 11-04 17:59 PT) · verified on GitHub (#413-#416, main CI green) + box bridge (`20261105T020020Z_*`) · moved: **EXP-042 cell 10 retired; NFL totals loss decomposed (72 games); NHL bias -0.080 → -0.059; B1 50 → 52 (count fixed)** · the T1/T2 lock install ran 11-05 02:11Z on the operator's named approval (17/17) · last wave of the Waves 81-100 window
| # | Block | Status | Outcome |
|---|---|---|---|
| 100.1 | B-029 + B-001 + B-030 engine | 🟨 | #414: NHL denominator fix (quarter of the bias); v3 412 rows, 5/11 games missed - box OOM |
| 100.2 | B-038 + B-035 + B-039 proof | 🟨 | #413: cell 10 retired; NFL totals loss = noise in disagreement; B1 52; calendar regen blocked (GG-1720) |
| 100.3 | B-026 + B-027 + B-040 flex | 🟨 | #415 #416: markers + Py3.9 fixed; T1/T2 lock merged NOT installed; picks night 1 read (GG-1690) |

### ✅ WAVE 99 — WRITTEN 2026-11-03 ~06:50 UTC · CLOSED 2026-11-04 ~04:15 UTC (operator 11-03 19:14 PT) · verified on GitHub (#405-#412 CI green) + box bridge (`20261104T040109Z_*`) · moved: **Muse archive tested in an engine (2 slices, null); verdicts applied; 13/13 frozen cells classified; all held installs live (85 → 88); OOM kills → 0**
| # | Block | Status | Outcome |
|---|---|---|---|
| 99.1 | B-032 + B-033 + B-029 engine | ✅ | #408: crews / referees null; NBA referee records 236/239 verified; NHL OT/SO exact, bias is regulation |
| 99.2 | B-034 + B-002 + B-035 proof | 🟨 | #406 #410: verdicts in registry; 13/13 classified; B-035 18/72 games (box cap) |
| 99.3 | B-036 + B-037 + B-017 flex | ✅ | #405 #407 #409 (+ window #412): gate fixed; reasons on 6 arms; installs run by the window on named approvals |
| M99 | Muse stress test + standing runs | ✅ | 46/50 done, 1 gate fail; 100 daily runs from 11-04 00:01 PT on QUEUE.md (359 chunks) |

### 🟨 WAVE 98 — WRITTEN 2026-11-03 ~03:30 UTC · CLOSED 2026-11-03 ~06:50 UTC (operator 11-02 22:33 PT) · verified on GitHub (#396-#404 merged, main CI green) + box bridge (`20261103T063449Z_*`) · moved: **the first verdicts read (2 RULED_OUT, 10 keep accruing); entry cost measured; frozen evidence 11/13 classified** · nothing installed (classifier) · box RED, 142 OOM kills / 24 h
| # | Block | Status | Outcome |
|---|---|---|---|
| 98.1 | B-030 + B-029 + B-031 engine | ✅ | #397 #403 #404: v1 misses = OOM kills; coverage ledger; NHL v2 spread better, totals unchanged; v3 indexed, no lift |
| 98.2 | B-005 + B-011 + B-002 proof | 🟨 | #396 #399 #400 #402: NFL game totals T1/T2 RULED_OUT, 10 keep accruing; keep entry rule; 11/13 DIFFERS (GG-1600) |
| 98.3 | B-027 + B-001/B-026 + B-028 flex | 🟨 | #398 #401: lock + stagger, picks task, reasons on 3 arms merged; nothing installed; GG-1630 |
| M98 / M98b | Muse live session; standing role | ✅ | Muse wrote the standing role into its README (4bf92d1) |

### 🟨 WAVE 97 — WRITTEN 2026-10-30 ~17:10 UTC · CLOSED 2026-11-03 ~03:30 UTC (operator 11-02 19:09 PT) · verified on GitHub (#388-#395 CI green) + box bridge (`20261103T030946Z_*`) · moved: **NBA engine priced real games (v1/v2); NHL board engine; D3 4 → 5; P1/P2 0 → 12 (NFL first look, on its own schedule)**; three partials · box RED (uninstalled lines + OOM)
| # | Block | Status | Outcome |
|---|---|---|---|
| 97.1 | B-001 + B-009 engine: v3 live, first nights, points leak-free | 🟨 | #391 #395 green: v1/v2 rows 1,645 / 2,008, 0 errors; v3 frozen EXP-044c, not installed (classifier); points: no win |
| 97.2 | B-002 + B-011 proof: frozen evidence resumable; entry cost | 🟨 | #388 green: resumable tasks; 2 of 20 units cached, ladder units time out at 900 s; Parts B, C not run |
| 97.3 | B-026 + B-006 + B-007 flex: the picks sheet; MLB winter; memory | 🟨 | #389 #392 #393 green: picks sheet built, cron not installed; MLB IDLE; 20 OOM kills / 90 min (GG-1581 HIGH); GG-1580 |
| 97.4 | B-012 engine: the NHL engine prices the whole board | ✅ | #390 #394 green: Poisson board engine; trails Kalshi at n 33; EXP-046 not earned |

### 🟨 WAVE 96 — WRITTEN 2026-10-30 ~15:50 UTC · CLOSED 2026-10-30 ~17:10 UTC (operator 09:46 PT) · verified on GitHub (#382-#387 CI green) + box bridge (`20261030T170102Z_*`) · moved: **NBA v3 interpreted (spread, team total); the rolling backlog live on /visual**; three partials
| # | Block | Status | Outcome |
|---|---|---|---|
| 96.1 | B-001 + B-009: NBA engine rows + v3; player points | 🟨 | #385 #387 green: v3 beats v2 held-out (spread −0.0079); not frozen (no live runner); no forward rows yet; points layer leaked, removed |
| 96.2 | B-002 (+ B-011 not pasted): frozen evidence | 🟨 | #383 #386 green: settlement cache complete; 0 of 13 classified (900 s limit, GG-1520); NFL regen input missing (GG-1521) |
| 96.3 | B-003 + B-004 (+ B-006 not pasted): backlog on dashboard; demo balance | 🟨 | #382 #384 green: backlog live on /visual; refusal logging live, no refusal since |

### 🟨 WAVE 95 — WRITTEN 2026-10-29 ~05:40 UTC · CLOSED 2026-10-30 ~15:50 UTC (operator 08:26 PT) · verified on GitHub (#377-#381 CI green) + box bridge (`20261030T152653Z_*`) · moved: **NBA engine arms installed (85 live); deploy-lag alarm; false red fixed**; three partials
| # | Block | Status | Outcome |
|---|---|---|---|
| 95.1 | Engine lane: NBA engine live on the box; v3 | 🟨 | #379 green: v1 + v2 + daily refresh installed 10-30 14:34Z; no rows yet; v3 not started |
| 95.2 | Proof lane: the frozen evidence reproduced | 🟨 | #377 #380 #381 green: harness + box tasks; n = 0 was local coverage; 0 of 13 re-run (settlements short); GG-1460 fixed |
| 95.3 | Flex lane: deploy path, false red, demo balance | 🟨 | #378 green: deploy-lag alarm + t4_mlb grace read back; insufficient_balance cause unproven (GG-1481) |

### ✅ WAVE 94 — WRITTEN 2026-10-29 ~00:15 UTC · CLOSED 2026-10-29 ~05:40 UTC (operator 22:25 PT) · four blocks + four Part C addenda · verified on GitHub (#367-#376 CI green) + box bridge (`20261029T052555Z_*`) · moved: **D3 3 → 4; both engines on frozen forward tests (EXP-044/044b/045); D5(a) NFL 8/8; E3 explained; proof calendar (64 rows)** · NBA runners not yet installed
| # | Block | Status | Outcome |
|---|---|---|---|
| 94.1 | Engine lane: NBA engine live + v2 challenger | ✅ | #368 #374 green: 56 games ingested; EXP-044 / 044b frozen; v2 beats v1 on moneyline held-out; runners merged, not installed (GG-1450) |
| 94.2 | Proof lane: NFL engine forward test; temporal evolution; play callers | ✅ | #367 #369 #371 green: EXP-045 frozen (look 2027-01-12); NFL 8/8; N11 interpreted, null on totals; GG-1460-1462 |
| 94.3 | Flex lane: T4 MLB silent; what a fill costs | ✅ | #370 green: false positive (first-row lag); resting fills -9..-17c, taker within 0.3c; demo insufficient_balance observed |
| 94.Q | Quant in tandem: exact fees, LADDER side, proof calendar, Bayesian weights | ✅ | #372 #373 #375 #376 green: nets redone; LADDER fixed; no model earns weight; PROOF_CALENDAR.md 64 rows; 2 frozen cells not reproduced locally |

### ✅ WAVE 93 — WRITTEN 2026-10-28 ~05:40 UTC · CLOSED 2026-10-29 ~00:15 UTC (operator 17:03 PT) · verified on GitHub (#362-#366 CI green) + box bridge (`20261029T000346Z_*`) · moved: **D4 NBA → board engine scaffold; D4 NFL → board priced from the line, tested; D5(b) NBA interpreted 7 → 9; NFL N15 interpreted** · 93.Q did not run · box RED at the close (T4 MLB silent)
| # | Block | Status | Outcome |
|---|---|---|---|
| 93.1 | NBA availability known before tip | ✅ | #364 green: built point-in-time; adds nothing beyond the rotation; applied blocked (no 2026-27 games in the store, GG-1420) |
| 93.2 | NBA travel, time zones, altitude, officials | ✅ | #362 #366 green: interpreted; margin no; altitude → total small; officials weak; GG-1390 |
| 93.3 | One model prices the whole NBA board | 🟨 | #363 green: joint-distribution engine beats its Gaussian twin held-out; vs Kalshi unestimable (0 settled rows) |
| 93.4 | NFL engine: the board from the line, key numbers right; travel | ✅ | #365 green: key number 3 within noise held-out; matches Kalshi's ladders, no edge; N15 interpreted |
| 93.Q | Quant in tandem | ❌ | did not run → 94.Q |

### ✅ WAVE 92 — WRITTEN 2026-10-28 ~05:00 UTC · CLOSED 2026-10-28 ~05:40 UTC (operator 22:24 PT) · verified on GitHub (#357-#361 CI green) + box bridge (`20261028T052642Z_*`) · moved: **sports in the price archive 2 → 4; surface truthful (phantom live 6 → 0); fees exact; NBA B7 interpreted (6 → 7); EXP-043 frozen**
| # | Block | Status | Outcome |
|---|---|---|---|
| 92.1 | NBA + NHL archive installed for real + a truthful surface budget | ✅ | #358 #361 green: 6 lines installed via archive_cron_install, rows for 8 series; budget excludes uninstalled entries |
| 92.2 | Exact fees (R-068); ladder cells into the ride table; EXP-043 | 🟨 | #357 #360 green: fee() exact; 2 LADDER cells HELD_OUT; EXP-043 frozen; per-trade recompute and LADDER side hazard → 93.Q |
| 92.3 | NBA engine: lineups and on/off, point-in-time | ✅ | #359 green: B7 interpreted (total: −4.04 MSE [1.92, 6.10], n 2,008); margin no gain; not applied (no NBA pre-game prices then) |

### ✅ WAVE 91 — WRITTEN 2026-10-28 ~00:40 UTC · CLOSED 2026-10-28 ~05:00 UTC (operator 21:32 PT) · verified on GitHub (#347 #353-#356 CI green) + box bridge (`20261028T043253Z_*`) · moved: **ride cells pre-registered 0 → 11 (EXP-042); ride tree is code; ladder ride measured (2 cells held out); ADR-0076 accepted** · 91.3 rerouted then partial (NBA/NHL lines not installed)
| # | Block | Status | Outcome |
|---|---|---|---|
| 91.1 | The ride cells: pre-registered (EXP-042), backward test, + ADR-0076 flip | ✅ | #355 green: EXP-042 frozen; backward VOID (overlap 83.8%; and no Kalshi sports before Aug 2026, Muse R-069); forward looks NFL ~12-21, MLB Apr-Jun 2027; ADR-0076 ACCEPTED |
| 91.2 | The ride tree as code + the ladder ride | ✅ | #353 #356 green: router RIDE 3,838 → 0; ladder net +0.7c [-0.2, +1.7]; 2 of 36 cells HELD_OUT (KXMLBTOTAL T0-2h tight) |
| 91.3 | REROUTED (Polymarket stopped): NBA + NHL into the price archive (+ #347) | 🟨 | #347 #354 green: 6 lines registered, NOT installed (ssh refused; wrongly sent to the operator); Part B not started → 92.1 |

### ✅ WAVE 90 — WRITTEN 2026-10-27 ~05:30 UTC · CLOSED 2026-10-28 ~00:40 UTC (operator 17:16 PT) · verified on GitHub (#349-#352 CI green) + box bridge (`20261028T001810Z_*`) · moved: **D5(a) MLB 0 → 2/8 (router); momentum measured in four sports (none); box RED → GREEN**; ride hold-out underpowered (0 candidates)
| # | Block | Status | Outcome |
|---|---|---|---|
| 90.1 | Finish 89.7, then the ride tree as code | 🟨 | #349 #352 green: 0 candidates, hold-out underpowered (1 of 1,850 cells testable, GG-1292); ride.py not built → 91.2 |
| 90.2 | The router: ride / fade / no-bet, doctrine + code + replay | ✅ | #350 green; doctrine ACCEPTED; NO-BET 97.66% / RIDE 2.34% (in-sample) / FADE 0 / MOMENTUM 0; D5(a) MLB 0 → 2/8 |
| 90.3 | Momentum, measured: follow or fade (Strategy J) | ✅ | #351 green: no momentum at 1-3 h (gross ≈ 0 every sport); net −4c to −17c; 0 contexts routable; momentum_looping = interpreted |

### 🟨 89.7 — ran 10-26 night, PARTIAL: PR #349 open (CI failed); remainder folded into 90.1 (operator 10-27 16:30 PT) | 🟨 |

### Waves 45-89
Rows moved to `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md` (2026-11-04).

---

## ⬛ STANDING WINDOW CHECK (SW-9, 2026-11-05, after W48) — THE DOCTRINE CHECK, EVERY WAVE CLOSE
At every wave close the window writes, in the RUNNING SITREP, two lines before the next wave: **(1) Premise** - the biggest assumption the
project is currently running on, and the strongest evidence against it; **(2) Said but not built** - one thing the operator has said he wants
(his words, dated) that no wave is building, and why not. If either line would be the same three closes running, the window raises it with
the operator unprompted. First entries: Premise - "edge must come from out-predicting the market" (against: 0 cells beat it; W89 longshot
bias; 103.2 fades) -> now being addressed by 105.4-105.6. Said but not built - parlays / big-hitter combos (09-25), waiting on the engines'
joint distributions.

## ⬛ OPERATOR DIRECTIVE, 2026-11-05 17:51 PT — RANKING UNCHANGED; NEXT WAVES QUANT-WEIGHTED; COMPOSITION IS THE WINDOW'S CALL
"We can go back to engine - but I agree with you that the subsequent waves should probably still primarily be quant. But again I'll let you
assess the full state of the project and decide from here - I'm hands off and not directing anymore." The 10-27 ranking stands (engine 2,
quant 4). SW-9 plan: Waves 105-106 = two quant blocks + one engine block (carrying maintenance); then the normal lane rule. Exit test by
Wave 107: quant (B-049 blend weights) has pointed engine work at named sport / family cells, or the window flags it. (DECISION_LOG 11-05 17:48 / 17:51 PT)

## ⬛ OPERATOR DIRECTIVE, 2026-11-04 22:01 / 22:03 PT — THREE BLOCKS STAYS STANDING; WAVE 103 = THREE QUANT + ONE RED ALERT
"Don't treat 5 as the operating procedure moving forward - it'll still be a standing 3, unless I request so. I want the next wave to be
all Quant + 1 red alert for whatever needs attention immediately. We've done a lot of engine work, I want to get the quant work moved up too"
Corrected 22:03 PT: "I want 3 quant plus a red alert". Wave 102's five blocks were a one-off. Wave 103 = FOUR blocks: three quant
(backlog B-044, B-045, B-046; B-010 rides in one) + one red-alert block for whatever is red at Wave 102's close; the lane rule is
suspended for Wave 103 only (DECISION_LOG 2026-11-04 22:01 / 22:03 PT).

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

## ⬛ OPERATOR DIRECTIVE, 2026-10-16 06:51 PT — THREE BLOCKS PER WAVE AGAIN (supersedes "operator sets the count", 2026-10-14)

"go back to making the default wave structure just 3 blocks. only if i request it otherwise should there be more. 3 block
structure is easily the most efficient and can get a lot done if the blocks are prompted correctly." From Wave 80: three blocks,
each substantive and MEDIUM-sized (below). More only when the operator asks. The standing gap agent (GA) is not a block and
does not count. Wave 79 (four blocks) was issued before this.

## ⬛ OPERATOR DIRECTIVE, 2026-10-07 18:58 PT — MEDIUM BLOCKS (amends the LARGE-block directive below)

**SUPERSEDED 2026-10-30 08:38 PT** (operator, "Yes" to the window's proposal): blocks are three parts, ~130 minutes; Part C is work a terminal can switch to while waiting on the box. The 10-07 text below is kept as history.

"You're making some of these tasks far too long. The terminals are coming back stating ETAs upwards of 3 hours which is
ludicrous from any one terminal to take on." Rule from Wave 60: each block is two parts, ~60-minute target, 90-minute
hard ceiling; a block whose own estimate exceeds 90 minutes does Part A only and hands Part B on. Still three blocks
per wave, still substantive - sized to finish, not to impress.

## Read this first (standing)

- **Protocol (operator, 2026-10-04):** every time this file changes, the strategic window loads it into the chat as a file card. He never has to dig through folders for it.
- **Add-ins (operator, 2026-10-19 21:55 PT):** an add-in to a running block goes to him IN THE CHAT as a short paste-in fence, and is logged here under its block. "I'm not repasting that entire massive block." Full wave blocks stay in this file only.

- **North star (2026-10-09):** CLAUDE.md § "What winning looks like" — four pillars, BREADTH / DEPTH / EXECUTION / PROOF.
  Every block's report and handoff names the pillar it moved (`vision_pillar:`; PLUMBING is a valid answer). The window
  updates the pillar scoreboard at every wave close and flags two pillar-less waves in a row.
- **PURPOSE before work (2026-10-09).** Every block prompt carries, right under its title, a `PURPOSE:` line naming the
  distance-to-optimum measure it moves (B1..P3, or PLUMBING) and the change it expects; its report and handoff state the
  measured change (`gap_measure:` / `gap_delta:` in the session-meta block). A terminal that cannot say what its task is
  for stops and asks before working.
- **Every wave = three terminal blocks + one Muse block (operator, 2026-10-19 22:25 PT).** The Muse block is written by the window, tied to an R-NNN ticket in `QUAL_ARCHIVE/TO_MUSE.md`, given to the operator in chat AND logged in the NOW section, and checked at wave close (charter v2 §8 watchdog).
- **Muse is never throttled (operator, 2026-10-21 07:17 PT: "It's never too much or too fast").** It will deliver faster than the bot consumes; that is the point. Every wave's depth lane names the Muse delivery it consumes (a card to capture, a record set to recompute, a split pair to cross), and the sitrep tracks Muse delivered vs consumed.
- **Three blocks per wave. Not four.** Operator directive 2026-09-15; relaxed 2026-10-14 (operator set the count); **restored as
  the default 2026-10-16 06:51 PT** - more only when the operator asks. The gap agent runs beside the wave and is not counted.
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

## THE ARC — sequential, not preset (operator 2026-10-15 22:30 PT)

> "Remember - don't pre-determine what the next waves are going to be - we are committed to sequential processing as necessary."

Each wave is set from the last wave's results and the calendar, when the last one closes. No wave content is drafted ahead.
Fixed dates the waves must respect: **NBA opening night 2026-10-20** (cells flip ~10-21) · **NFL first scored look ~2026-11-02** ·
**World Series end → MLB live betting idle, MLB look-back** · this window runs through Wave 80's finish (operator 10-15 17:33 PT).
Standing direction: ADR-0073 (one engine per sport), ADR-0074 (process integrity), ADR-0075 (the betting architecture), and the
10-16 call to move toward thinner markets.

What should reorder this, and what should stop it:

- **A shadow path that reaches an order, position or sizing function** stops everything shadow until fixed.
- **A dashboard that shows a number it did not read live, or a number that is not what its label says** is a defect of the same severity.
- **A kill switch that should have fired and did not** (51.1 verdict c) stops everything until understood.
- **Per cell, the pre-registered rules decide.** RULED_OUT at judged n is a completed cell.
- **Board-survey stop condition — pre-registered in Wave 45, carried unchanged.**

---

## Needs your decision

> **PENDING YOUR APPROVAL BY NAME (window recommends all three):**
> - `archive_dense_install`: gate PASS, 30.5 MB/day, one new cron, budget-gated.
> - `nba_combo_shadow_install`: one hourly cron, PM_COMBO_SHADOW=on, BOT_ENV=paper. It logs to exp_output/COMBO_SHADOW, places no orders, and is budget-gated.
> - `data_offload_install` (W128.5): gate PASS, 12 MB/day upper bound, peak RSS ~26 MB, one scraper at a time, off-peak, budget-gated. It fetches MoneyPuck, NHL officials, NHL goalie logs and Savant boards to the box.
>
> MoneyPuck's terms are free for non-commercial use, with credit to MoneyPuck.com. The bot is paper and demo only, and the credit goes in the data README. Approving `data_offload_install` accepts those terms.
>
> To approve, say "approve <task name>" for each one you want.

> **AUTHORIZATION - NFL NO_BET LEAVES STAY NO_BET (operator, 2026-11-24 18:33 PT: "Approved on rec for both", answering the window's
> recommendation to keep the W117.1 A3 per-leaf rule).** NFL cells routed NO_BET place no demo orders; D6 NFL stays where the rule puts
> it. No block changes the rule.

> **AUTHORIZATION - DENSE CAPTURE SHRINKS TO FIT; THE 80% DISK CEILING STAYS (operator, 2026-11-24 18:33 PT: "Approved on rec for both").**
> W127.4 cuts the capture to pass its own gate. `archive_dense_install` itself still needs "approve archive_dense_install" by name.

> **PROPOSED - NOT ACTIVATED (W125.4, 2026-11-23): `PM_PROPS_C1` (EXP-047-C1 forward log, default off).** Retro verdict INDETERMINATE: points better, rebounds / assists / threes worse. Recommendation: leave OFF; a points-only variant needs its own pre-registration first. Say "approve PM_PROPS_C1" only if you want the uniform rule logged forward anyway (shadow only, Kelly 0, one extra ledger dir under the existing registered runner).

> **PROPOSED - NOT ACTIVATED (W126.2, 2026-11-24): `PM_PROPS_C2` (EXP-047-C2 forward log, default off).** Retro on unread 2023-24: SUPPORTED, all four stats improve vs EXP-047 (points -0.026, rebounds -0.001 thin, assists -0.004, threes -0.003; 899 games); C2 beats C1 on rebounds, assists, threes. Recommendation: the window switches it ON as shadow logging beside EXP-047 (orders follow v1, Kelly 0). **Hard Rule 14 surface check:** no new cron or service; one extra branch inside the existing `run_nba_engine_props_shadow.py` (RUNTIME_REGISTRY cron `39 * * * *`) writing `exp_output/PREGAME_SHADOW_EXP047_C2/`; adds one extra pricing pass per run (same cost as C1); health signals must be green at activation; `surface_delta: +1 ledger dir, 0 components`. Not switched on by this block.

> **PROPOSED - APPROVAL NEEDED (W121.1): `evidence_weekly_install`.** Say "approve evidence_weekly_install" and the window runs that one task: it adds one crontab line (Tuesday 10:00 UTC, flocked, niced) on the paper box that runs the weekly evidence look on settled shadow rows for v1 and every candidate map, carrying the e-process forward and writing only `exp_output/EVIDENCE_WEEKLY/`. It places no order and touches no stake or Kelly. Install is refused while the surface budget is red; every prior crontab line is preserved and backed up; `evidence_weekly_readback` shows what it wrote and `evidence_weekly_uninstall` removes exactly that block. Registry entry is PAUSED until you approve.
> **PROPOSED - APPROVAL NEEDED (W118.4, B-102): `disk_retention_install`.** Say "approve disk_retention_install" and the window runs that one task: it adds one daily crontab line (14:17 UTC, flocked, nice/ionice) on the paper box that gzip-compresses old KALSHI_HISTORY raw files and .bak files (sha256-verified before the plain copy is replaced; nothing is ever deleted) and caps journald at 200M. Disk is 87% and growing about 1.5 points a day (90% in about 2 days, where the healthcheck FAILs and blocks every install). Target once installed: under 75%. Reversible with `disk_retention_uninstall`; the window reads the crontab back after install. Demo/paper only, no orders, no real capital, $0.

> **AUTHORIZATION - WEEKLY EVIDENCE LOOK INSTALL (operator, 2026-11-20 07:46 PT: "I approve evidence_weekly_install.").**
> `evidence_weekly_install` (W121.1): one cron line, Tuesdays 10:00 UTC. Run by the window with readback and a budget read.

> **AUTHORIZATION - WEEKLY EVIDENCE COPY TO THE MAC (operator, 2026-11-18 22:44 PT: "Yes", answering the window's "The weekly copy to
> your Mac: 5.7 GB now, growing about 100-150 MB a month compressed. Say yes and 121.4 installs it on your Mac.").** W121.4 runs
> scripts/ops/evidence_pull_launchd.sh install on the operator's Mac and reads it back.

> **AUTHORIZATION - CANDIDATE MAPS LOGGED BESIDE V1 (operator, 2026-11-18 21:19 PT: "yes I give approval", answering the window's
> "Approve with: 'Log the candidate maps beside v1.'").** Every pregame shadow row records the arm router v2, +nba_depth and nhl_v2 would
> pick - shadow only; demo orders keep following v1; the frozen ADR-0072 test is untouched. Built and switched on by W120.2.

> **AUTHORIZATION - DISK RETENTION INSTALL (operator, 2026-11-17 22:18 PT: "Yes", answering the window's "If you approve it now
> ('I approve disk_retention_install'), I'll run it the moment 118.4 merges it").** `disk_retention_install` (W118.4): journald cap and
> compression of old logs / archive files (nothing deleted). Run by the window with readback, disk_read and a health rerun.

> **AUTHORIZATION - THREE DECISIONS (operator, 2026-11-17 17:45 PT: "yes approve on all 3", answering the window's message naming
> `nhl_event_store_install`, NFL v1 per-leaf to no bet, and counting tested stumps at layer 3).**
> (a) `nhl_event_store_install`, which adds a crontab line on the paper box. Run by the window with its readback and a budget read, after
> 117.0 merges PR #507.
> (b) NFL v1 per-leaf demo orders route to NO BET: hypothesis closed (EXP-W110.5 NFL per-leaf, parked for R&D). NFL shadow rows keep
> logging. NBA / NHL v1 are unchanged and the frozen ADR-0072 file is untouched. Built by 117.1 (arm_orders).
> (c) D6 layer 3 is present when a cell's splits were tested on box rows and logged with their verdicts, kept or not (a tested stump).
> d6_read reports stumps separately from cells with a kept split. Built by 117.3 (coverage.py).

> **APPROVED 2026-11-17 PT by the operator ("Yes - I provide my approvals.") - DEMO ARM PLACEMENT POLICY ON (W116.2):** Turns on only when the frozen table exists (none yet). turn `ARM_PLACEMENT_POLICY=on` for router-arm demo orders, reading a frozen `config/placement_policy.json` fitted only on orders that logged their spread (30+ resolved per side of each cell), judged at 100 resolved orders per arm and option (ADR-0072 addendum proposal 2026-11-17). Today's read, before spread was logged: FADE cross +0.18 per order [+0.09, +0.28], n=100, with an assumed spread; RIDE and MOMENTUM within noise. Demo only, `kelly_fraction` 0.

> **APPROVED 2026-11-17 PT by the operator ("Yes - I provide my approvals.") - DEMO ARM BOOK CAPS RAISED (W116.2):** Turns on only after GG-1942 is fixed and merged. turn `ARM_BOOK_CAPS=raised` (25 per event / $2,500 a day / $1,500 per arm, demo only; about 50 -> about 2,200 demo arm orders a day) **only after GG-1942 is fixed** (ARM_ORDERS advisory in the exposure gate; otherwise about $200 of open demo stake halts every book). Same addendum proposal.

> **DECISION - ROUTER V2 ON FOR LOGGING (W116.1, 2026-11-17):** turn router v2 on for logging (v1 stays the frozen test). It sets `PM_LEAF_MAP_VERSION=v2` beside v1 in shadow logging only: no orders, `kelly_fraction` 0. Today v2 would log NO_BET on every row; it earns an arm only when a leaf's pooled P(net>0) >= 0.90 and its e-value >= 10 (pre-registered). Logging it now starts the forward clock its pre-registration scores. Reply "yes, router v2 logging" or not.

> **AUTHORIZED 2026-11-11 16:51 PT (operator, in chat: "yes I approve"):** D6 layer 7 - the router's arm drives the ADR-0072 demo forward
> test's orders (demo money only, flat demo stakes, `kelly_fraction` 0, kill switch and zero-orders alarm unchanged), recorded as a
> superseding addendum to the frozen ADR-0072 test (the frozen file untouched). Built and switched on by Wave 112.3 after its tests and a
> dry run pass.

> **AUTHORIZATION - BRANCH CLEANUP (operator, 2026-11-04 21:54 PT: "Yes proceed with the branch cleanup").** Delete the 31 branches in
> `12_EXPLORATORY/branch_cleanup_w101/LIST.md` "DELETE" tables (29 merged-PR + 2 with nothing unlanded), each only if its remote tip still
> equals the recorded SHA. KEEP `data/nba-injury-reports`, `data/nhl-goalie-probe`, #149's branch. `w83-3-nhl-data-layer`: operator
> 2026-11-04 21:59 PT, "just input whats recommended" -> the list's recommendation: check the dropped lines, register a GG if wanted, then delete
> (tip 8219b53bec recorded). The window's attempt was refused by its session proxy (HTTP 403 on ref deletion, 11-05 05:56Z); run by a terminal (block 102.5).

> **AUTHORIZATION - NBA ENGINE CATCH-UP INSTALL (operator, 2026-11-04 22:39 PT: "yes I approve the box-task request that runs
> nba_engine_catchup_install, which adds a crontab line on the paper box.").** Run by the window with its readback and a budget read.

> **AUTHORIZATION - RIDE BOARD + PROP ARCHIVE INSTALLS (operator, 2026-11-10 16:27 PT: "Yes approve for both", answering the window's two
> approval sentences: ride_board_install, which adds a crontab line on the paper box; archive_cron_install, which adds crontab lines on the
> paper box - the 22 NBA / NHL / NFL prop series of #456).** Run by the window, ride board first (it clears the budget red), then the archive,
> each with its readback and a budget read. **DONE:** ride board installed 2026-11-11 00:35Z (`20261111T003450Z_*`), prop archive 3 lines / 22 series installed 00:45Z (`20261111T004500Z_*`); SURFACE BUDGET GREEN, 93 live, healthcheck HEALTHY. (The two installs blocked each other under Hard Rule 14 - each exempts only its own reds - so the window paused the archive entries for the ride-board step and restored them for theirs.)

> **AUTHORIZATION - NBA PROPS SHADOW + DASHBOARD MEMORY (operator, 2026-11-12 15:04 PT: "Yes IO approve", answering the window's
> message naming `nba_engine_props_shadow_install` and `dashboard_memmax_install`).** Run by the window with readbacks and a budget read.
> **DONE 2026-11-12 23:05Z:** dashboard MemoryMax 384 MB (NRestarts 0, active); props-shadow cron line installed (backup crontab_20261112T230518Z.bak),
> registry entry flipped to live; SURFACE BUDGET GREEN, 93 live, healthcheck HEALTHY. The 9 NBA prop shadow cells log from the next :39.

**OPEN - waiting on you (not an authorization until you answer):**
1. **EXP-038 second-look definition (GG-529, DRAFT by 102.2):** `03_DECISIONS/EXP038_ADDENDUM_2026-11-05_second-look-definition-DRAFT.md`;
   due before January. Accept, or tell me what to change.
2. ~~**`nba_engine_props_shadow_install`**~~ APPROVED 11-12 15:04 PT (109.3, EXP-047: 9 NBA prop SHADOW cells - points, rebounds, assists, threes - one cron line,
   evaluate-and-log, no orders). Approve with: "I approve the box-task request that runs nba_engine_props_shadow_install, which adds a crontab line on the paper box."
3. ~~**`dashboard_memmax_install`**~~ APPROVED 11-12 15:04 PT (109.5: the dashboard service hit its 128 MB cap 5,082 times; raises it to 384 MB). Approve with:
   "I approve the box-task request that runs dashboard_memmax_install, which changes the dashboard service's memory limit on the paper box."
4. ~~**`nhl_event_store_install`**~~ APPROVED 11-17 17:45 PT · **INSTALLED 2026-11-18 05:04Z** by the window (first refused 02:35Z by a false healthcheck FAIL - SIGPIPE under pipefail, fixed by 117.3 #516; readback: 1 line, daily 13:29Z, store builds on its first run; disk 87% before, store ~325 MB, FAIL line 90%) (W116.3, 2026-11-18, PR #507): one paused cron line (13:29 UTC daily) that refreshes the NHL event store
   on the box (two seasons, streamed compile). Without it NHL has no filter data on the box, so no NHL cell can pass D6 layer 3. Measured
   locally: compile peak 2,049 -> 270 MB, NHL filter-state build 913 -> 318 MB (same output on 40 games). Risk: the box has ~126 MB free
   with swap in use, so the first run may swap; it runs under nice and flock, no orders, `kelly_fraction` 0. Approve with:
   "I approve the box-task request that runs nhl_event_store_install, which adds a crontab line on the paper box."
5. ~~**NFL v1 per-leaf orders → no bet**~~ APPROVED 11-17 17:45 PT (SW-9, 2026-11-18). Held out, v1's NFL per-leaf arms lose −0.020 per row [−0.037, −0.005],
   the interval wholly below zero (W116.1). Route NFL per-leaf demo orders to NO BET and record "hypothesis closed (EXP-W110.5 NFL
   per-leaf, parked for R&D)"; NBA / NHL v1 unchanged and the frozen ADR-0072 file untouched. Approve with: "Route NFL v1 per-leaf to no bet."
6. ~~**D6 layer 3 for a stump**~~ APPROVED 11-17 17:45 PT (SW-9, 2026-11-18). Today layer 3 needs a KEPT split, so a family whose splits were all tested and none
   helped (NFL: 0 of 28 kept) counts as unwired, though under ADR-0077 that null is a routing result - the tree is a stump that picks
   one arm, or NO BET, at the root. Proposed definition: layer 3 is present when the cell's splits were tested on box rows and logged
   with their verdicts, kept or not. It would raise D6 without any new edge, so it is your call. Approve with: "Count tested stumps at layer 3."
7. ~~**Candidate maps logged beside v1**~~ APPROVED 11-18 21:19 PT (SW-9, 2026-11-19; supersedes the 11-17 "router v2 on for logging" line above). Every pregame
   shadow row also records the arm router v2, +nba_depth and nhl_v2 would pick - shadow only; demo orders keep following v1 and the
   frozen ADR-0072 test is untouched. Without it, none of the maps built since W116 earns evidence on box rows. Approve with:
   "Log the candidate maps beside v1."
8. ~~**Weekly evidence copy to your Mac (W119.4 / 120.3)**~~ APPROVED 11-18 22:44 PT (121.4 installs it). Copies the price archive, Kalshi history and ledgers to
   ~/PredictionMarketEvidence every Sunday, sha-checked, kept compressed (120.3 measures the size first). The 120.3 terminal asks you
   before loading it.
9. ~~**`evidence_weekly_install` (W121.1)**~~ APPROVED 11-20 07:46 PT, run by the window. One cron line, Tuesdays 10:00 UTC: the weekly evidence look on box rows for v1 and every
   candidate map, carried forward. Its guarantee needs every look taken on schedule; the first look (11-17 cut) ran by hand. Approve
   with: "I approve evidence_weekly_install."
(Closed by your 11-09 21:29 PT answer: the window's strategy recommendation to stop new builds on liquid sports lines - WITHDRAWN. Operator: "We have quant, engine, scaffolding, governance, architecture, full bet suite, multi arm decision tree building - I can keep going and going ... it'll stay fkn negative for a while". The build continues on every lane; the frozen tests judge cells, they do not gate building.)
(Closed by your 11-05 answer "Restart": the NFL ADOPT addendum and the look-day question - the ADR-0072 clock now runs from the GG-1771 epoch.)

> **AUTHORIZATION - T1/T2 SHADOW-LINE LOCK (operator, 2026-11-04 18:10 PT: "I approve the box-task request that runs
> t3_lock_stagger_install, which edits the crontab on the paper box.").** Run by the window 02:11Z: 11 more lines wrapped (17 of 17),
> backup crontab_20261105T021134Z.bak, line count 670 -> 670, budget GREEN. Next: `box_memory_read` after a full NBA + NHL night.

> **AUTHORIZATION - RETIRE EXP-042 CELL 10 BEFORE ITS LOOK (operator, 2026-11-03 19:16 PT, asked by the window with the 99.2
> recommendation - "KXMLBTOTAL T0-2h 85-90c wide yes: frozen net .089 / lo .047, re-run .0383 / lo -.0301 ... needs ~370 judged games,
> against 19 frozen" - "Yes").** Cell 10 is retired before its look by a superseding addendum to EXP-042 (the frozen file is not edited);
> ride_cells.toml marks it retired with the reason and date. Cells 9 and 11 are NOT retired. Done by a terminal block (Wave 100).

> **AUTHORIZATION - THE WAVE 99 BATCH INSTALL (operator, 2026-11-03 19:16 PT: "I approve the box-task request that runs
> install_batch_w99_install, which adds crontab lines on the paper box.").** Run by the window 03:16Z with its readback.

> **AUTHORIZATION - THE STRATEGIC WINDOW RUNS BOX INSTALLS (operator, 2026-11-02 22:40 PT, asked by the window whether it may run
> box installs after the classifier refused it: "Yeah go ahead - fix the deadweights then I'm going to sleep").** The strategic window
> runs the allowlisted `*_install` bridge tasks named in a merged block's handoff (paper / shadow box only: no capital, no orders), each
> with its crontab backup and a readback. Hard Rule 14 still applies. Terminals still never run installs. **Status 22:45 PT: the
> classifier refused the window's install request again after this authorization ("Unauthorized Persistence"); nothing was pushed or
> run. The installs wait until the session's permissions allow them or the operator starts the Box Tasks workflow by hand.**

> **AUTHORIZATION - WHERE THE PASTES LIVE, AND WHEN THE SHARED FOLDER IS REFRESHED (operator, 2026-10-27 21:46 PT: "you don't need
> to waste my tokens putting it in this chat, just put it in the Active Queue file. Also - no need to keep updating my folders to catch
> it up after every wave - we'll just have you do it when we're doing handoffs from window to a new chat.").** Wave blocks live in the
> NOW section of this file (common rules in a file each block points to), never pasted into the chat. The operator's Mac folder is
> fast-forwarded only at a window-to-new-chat handoff (amends the 2026-10-21 19:39 PT shared-folder protocol below; the folder stays).

> **AUTHORIZATION - ADR-0076 ACCEPTED AS THE G6 DEFINITION (operator, 2026-10-27 17:30 PT, asked by the strategic window whether he
> accepts ADR-0076 with the blanks left blank until a positive Kelly is proposed: "Yes I accept").** G6 is qualified per (book, sport):
> a book qualifies when its cell WINS at its pre-registered judged n (ADR-0072; real demo fills only, GG-527), with the exposure gate
> enforcing, DS sign-off and the operator's acceptance of the limit table. Section 4's blank limits STAY BLANK until a positive Kelly is
> proposed (ADR-0048 Kelly 0 unchanged). No limit value, kelly_fraction, stake, order or ledger changes. No book qualifies today. The
> status flip and its references are done by a terminal (91.1 addendum).

> **AUTHORIZATION - THE SHARED FOLDER STAYS, AS A CURRENT READING COPY (operator, 2026-10-21 19:39 PT: "When I look through
> the project I check the folders not github - especially when I'm somewhere with no internet. I'd like to keep it going - we
> should probably just change the protocol for updating it so that it's not elongating the gap list just for the update. But I
> don't want to retire the shared folder.").** The operator's Mac folder is NOT retired. Protocol: the strategic window
> fast-forwards it to origin/main at every wave close (it is never a working tree for terminals; they use worktrees). Lag
> between refreshes is expected and is not a gap. Shared-tree drift gaps close under this protocol once the first refresh has
> landed. Local files the operator or a past session left untracked are never touched.

> **AUTHORIZATION - OBSERVATION RULE (operator, 2026-10-21 19:35 PT, asked by the strategic window: "Yes to observations stop
> counting as gaps").** A gap with nothing to fix (a measured fact, arithmetic such as GG-285, a known limitation of a source)
> is re-filed as `**Status:** WATCH ITEM` with its severity unchanged, its full record kept, and one line saying what would
> reopen it. WATCH ITEM is not counted as OPEN. The shared-tree retirement was NOT decided (the operator asked what it means).

> **AUTHORIZATION - THREE CALLS (operator, 2026-10-21 19:15 PT, asked by the strategic window with recommendations: "Log my
> acceptance for the recommended paths on the first 3").** (1) **PAM layer-1 taxonomies for NFL (draft2, 67 archetypes in 19
> position groups), MLB (24) and NHL (18) are ACCEPTED as working drafts**: thresholds are calibrated at each sport's mass tier
> from data, never fitted to outcomes. (2) **G6 is re-defined by a superseding ADR** (GG-204, GG-285): "ready for real money"
> is decided per book and sport, a cell qualifies when it WINS at its pre-registered judged n under ADR-0072's forward test,
> and the kill-switch fix in (3) is a precondition. The ADR is drafted by a block and comes back to the operator to accept.
> (3) **The kill switch counts open and settled-but-unresolved stake and persists its state** (GG-441), built as a block
> before any real capital. No real capital, stake or kelly_fraction changes under this authorization.

> **AUTHORIZATION - MARKET-ANCHORED PRICING, A REAL GATE, A POOLED TEST (operator, 2026-10-21 20:28 PT, on the strategic
> window's model stack assessment, items 1-3: "Good - I accept them").** (1) **Each arm's price starts from the market's
> probability plus adjustments from factors tested out of sample**; the frozen models become inputs and benchmarks and keep
> running beside it. Built as a NEW pre-registered challenger per sport, NFL first; each pre-registration is committed before
> its first row. (2) **A real gate**: one position per market per band; the model is pulled toward the market by its measured
> skill; an order goes in only when what is left clears the fee plus the model's measured error; a game's ladder counts as one
> exposure. This changes the running ADR-0072 forward test, so it lands as an amendment the operator sees before it goes live.
> (3) **One pooled market-anchored test per sport** (all families and bands, clustered by game, corrected for many cells), as
> a pre-registration amendment. Frozen arms, sealed looks and existing pre-registrations are not edited; demo only, $1 flat,
> kelly_fraction 0, no real capital. Assessment: Claude Docs "Model stack assessment" (2026-10-21).

> **AUTHORIZATION - ADR-0072 NFL SECOND LOOK (operator, 2026-10-20 ~23:05 PT, asked by the strategic window: "Keep running, one
> more look (Recommended)").** The forward test keeps running for NFL; one more pre-registered NFL read is taken when criterion
> (c) has markout-bearing fills at judged n (~550 per arm) on both arms; that verdict word is final for NFL. Nothing else changes.
> Addendum: `03_DECISIONS/ADR-0072_ADDENDUM_2026-10-21_nfl-second-look.md`.

> **AUTHORIZATION - ADR-0072 ADDENDUM: THREE PRE-REGISTRATION GAPS (operator, 2026-10-19 ~22:45 PT, asked by the strategic window
> before any score was read).** Verdict unit: "Per book and sport (Recommended)". Criterion (c), the 30-min post-fill markout, never
> collected: "Collect from now; judge (c) forward (Recommended)". Cash-starved days: "Exclude them (Recommended)" (fills before
> 2026-10-16T05:40Z are out of the verdict, reported separately). Covers: a dated ADR-0072 addendum with exactly these three
> decisions; a 30-min markout collector (registered first); the scored read under them. Not covered: seed, share, judged n, the
> placement rule, any switch. Used by 81.1 (add-in 81.1-B).

> **AUTHORIZATION - KXNFLPASSYDS THIN-MARKET CELL (operator, 2026-10-19 21:40 PT, asked directly by the strategic window,
> choosing "Yes, accept it (Recommended)").** Covers: marking `12_EXPLORATORY/THIN_MARKET_PREREGISTRATION_2026-10-20.md` ACCEPTED
> (status line only); building its pre-kickoff snapshot job (a NEW cron line, registered first) and a frozen strike model; logging
> SHADOW rows against it; flipping the KXNFLPASSYDS T1 cell NOT_IMPLEMENTED -> SHADOW once the frozen artifact and the first valid
> row exist. Not covered: any order, stake or kelly change; any change to the pre-registration's text or parameters (a new dated
> file); follow-on families (KXNFLRECYDS, KXNFLRSHYDS each need their own). Used by 81.3.

> **DECISION - MUSE L3 (operator, 2026-10-19 21:40 PT).** L3 is the split-level layer as Muse proposed ("Yes, as Muse
> proposed"): ticket R-008. *(The Nix ".283 vs .378" recompute was withdrawn 21:53 PT - the operator: "who fucking cares what his
> YPA on throws are lol it was an example". Window error W25.)*

> **OPERATOR DIRECTIVE (2026-10-09 00:14 PT):** "I want to have MLB wired to full cus of the limited games left - the
> translatebility should be mechanisms that we spent fucking months on with the MLB and should absolutely have already been
> integrated in the NFL - when are we finally getting towards math work?" Used by 63.1 (MLB coverage) and 63.2 (NFL depth).

> **AUTHORIZATION - GITHUB $0 (operator, 2026-10-10 20:49 PT: "I'm not spending a CENT on GitHub").** Covers: running the
> test suite on demand only (terminals run it locally before merging); trimming scheduled workflows; registering a repo-scoped
> self-hosted Actions runner on the VPS (own non-root user, systemd unit) and moving deploy.yml's jobs onto it with identical
> behaviour; changing scripts/generate_mlb_features.py to fetch postseason logs only for postseason players, proven
> byte-identical. Not covered: any paid service or plan, making the repository public, changing the deploy restart policy.
> Used by 66.1.

> **STANDING RULE - PERMISSIONS PRE-FLIGHT (operator, 2026-10-12 16:24 PT: "These blocks need to get the permissions before they
> actually run so they can fire off accordingly").** Every block lists, under PERMISSIONS, each command class it needs (VPS read,
> VPS cron install, service restart, PR/merge, demo order). The window issues a block only when each is covered by (a) an allow
> rule the operator has put in the terminals' Claude Code settings (auto mode drops `Bash(*)`; narrow rules survive it) and
> (b) a dated authorization line here. A refused action stops the block at once with the exact command; a block is never DONE on
> "merged" - DONE means the running process or cron was read back over ssh.
>
> *Amendment, window 2026-10-13:* (a) cannot come from a block. In 69.1 and 69.2 the terminal's classifier refused to write
> `.claude/settings.local.json` even with the operator's line pasted (Self-Modification) — correctly: Claude may not grant itself
> permissions. The allow list now lives in `scripts/operator_grant_permissions.py`; the operator runs it once (`!` prefix in any
> terminal, so it runs as him). Until he does, refused commands are recorded and skipped, never worked around.

> **AUTHORIZATION - GITHUB PUBLIC (operator, 2026-10-11 11:53 PT: "Fine fire it up - we'll make the github public").** Covers:
> the operator switching the repository to public (the window's token cannot); dispatching the MLB data workflows; restoring
> tests.yml's PR/push triggers; a governance-scan line for Actions status. Not covered: rewriting git history, any paid
> service, changing secrets. Used by 68.1.

> **AUTHORIZATION - DEMO CONFIG (strategic window, 2026-10-11, under the operator's standing rule of 2026-10-08: "Sandbox, paper
> and demo actions are plumbing: handle them. Only real capital is mine.").** Covers: pre-checking the demo listing before a demo
> order (unlisted ticker = logged skip, identical for both arms); editing the existing shadow pregame cron lines ONLY to load
> deploy/demo_fill.env (mirrored in deploy/); flat ADR-0050 demo stakes on SHADOW cells under ADR-0072. Not covered: any
> kelly_fraction or stake-size change, any non-demo host, any change to a registered forward-test parameter. Used by 67.2.

> **AUTHORIZATION - GITHUB $0, AMENDED (strategic window, 2026-10-11, under the operator's 2026-10-10 "not a cent on GitHub").**
> Adds: a VPS-side deploy (a NEW cron line that pulls main and runs deploy.yml's own steps and restart policy) replacing
> deploy.yml's push trigger; running the MLB feature generator from a NEW VPS cron line if statsapi answers the VPS with
> corrected request headers. Not covered: a self-hosted GitHub runner (refused by the classifier - do not retry), any paid
> service, making the repository public. Used by 67.3.

> **AUTHORIZATION - ADR-0072 ON (operator, 2026-10-10 19:13 PT, choosing "Accept, switch on (Recommended)").** Covers:
> marking ADR-0072 and its forward-test pre-registration ACCEPTED; ONE canary demo order (1 contract, priced where it cannot
> fill) placed and cancelled to verify the cancel call before anything else; then setting DEMO_FILL_PLACEMENT_RULE=
> book_anchor_cancel and SHADOW_FLAT_STAKE=on with the registered parameters (N=60 s, max mid gap 0.05, share 0.5, seed w64-2)
> through repo-mirrored config for the processes that place demo orders, restarted under the idle-window rule; the orders,
> cancels and flat ADR-0050 demo stakes those switches produce. Demo venue only. Not covered: any kelly_fraction or stake-size
> change, any non-demo host, changing a registered parameter (that restarts the test and needs a new line). Any session must
> unset the switches if a turn-off condition in ADR-0072 trips. Used by 65.2.

> **AUTHORIZATION - NFL QB CHALLENGER SHADOW (operator, 2026-10-10 19:13 PT, choosing "Accept, ship as shadow (Recommended)").**
> Covers: marking 12_EXPLORATORY/NFL_QB_SHRUNK_CHALLENGER_PREREGISTRATION_2026-10-09.md ACCEPTED (text otherwise unchanged);
> freezing the challenger artifact once; a shadow runner writing challenger rows beside the frozen EXP-037 rows; a NEW cron line;
> listing it in the calibration engine sealed below its judged n (984 games). Not covered: replacing or editing the frozen NFL
> model or its rows; promotion; any order or stake (the challenger's rows get no flat stake). Used by 65.3.

> **AUTHORIZATION - GG-536 (operator, 2026-10-10 19:13 PT, choosing "Same rule as GG-527 (Recommended)").** Covers: every T1 MLB
> paper row counts as model-calibration evidence only; any execution, P&L or G6 claim for T1 MLB counts CONFIRMED_FILLED rows
> only, labelled that way in the power calc, governance scan, band monitor and both dashboards, from the T1 fill sidecar (no
> live-ledger row rewritten). Not covered: T1 MLB winter posture, any stake or kelly change. Used by 65.2.

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
| **ADR-0072 demo-fill placement + forward test** | ✅ **ACCEPTED 2026-10-10 19:13 PT: switch on** — line above; 65.2 verifies the cancel call, then switches on. | — |
| **NFL QB-shrunk challenger** | ✅ **ACCEPTED 2026-10-10 19:13 PT: ship as shadow** — line above; 65.3. | — |
| **T1 MLB book counting (GG-536)** | ✅ **DECIDED 2026-10-10 19:13 PT: same rule as GG-527** — line above; 65.2 builds it. Original: 62.3 found the T1 MLB book shows the same pattern as T4M-PROJ: only 85 of 485 positions filled; fills lost −$1.50/bet at a 28.9% win rate, while non-fills "won" 52.1%. GG-527's decision covered T4M-PROJ only. **Window recommends the same rule for T1:** rows are a calibration record; any execution or G6 claim counts real fills only. | Until decided, T1's paper P&L can be read as execution evidence. |
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
