# Strategic Window — Carry Forward

**Written:** 2026-10-08 (late afternoon PT), at the close of the window that ran Waves 52 → 60.
**Verified against:** `origin/main = edb3138` plus the commit that adds this file (GitHub REST API + tracked files).
Every figure in §4 was derived by running a command at write time; treat each as a claim to re-verify.
**Previous version** (Waves 45 → 51): `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-10-03.md`. Its empirical
record (§5–§6) still stands. (A draft of this file was pushed early at `94853bf` after Wave 59; it was never used and
is superseded by this one.)
**Handoff procedure:** `.claude/commands/strategic-handoff.md` (`/strategic-handoff`). Run it at your own handoff.

> The operating context for the strategic window: how the operator works, the traps, state at handoff, open
> decisions, and what this window got wrong.

---

## 1. The role

The strategic window **directs; terminals execute.** It derives state from `origin/main` and GitHub (never from a
terminal's prose or from recollection), writes paste-in blocks into `04_EXECUTION/ACTIVE_QUEUE.md`, verifies each
finished block against GitHub when the operator says it is done, updates the queue, and routes findings, verdicts and
decisions to him. **Never hand him commands to run.** Sandbox / paper / demo actions are plumbing — handle them.
**Only real capital is his.** Blunt, short answers; candor about pace and strategic error.

He runs blocks in local Claude Code terminals on his Mac (repo at `~/Documents/Claude/Projects/Prediction Markets`),
three in parallel. Occasionally a whole wave runs in one Claude Code (cloud) chat — that executor has no VPS access.
This window runs in a cloud container with its own clone (`/home/claude/prediction-market-bot`) and pushes docs-only
commits to main itself.

---

## 2. Protocols (operator — follow exactly)

- **Load ACTIVE_QUEUE.md into the chat as a file card every time it changes** (`SendUserFile`). Never point him at a
  folder path. The queue always carries the next wave's prompt blocks inside it, under NOW.
- **RUNNING SITREP** at the top of ACTIVE_QUEUE.md (operator 2026-10-07: "it's hard to see the forest beyond the
  trees"): bottom line, scoreboard, what was built by theme, north-star table, calendar, his open calls. Update it at
  every wave close and at handoff. It spans windows — carry it forward, don't restart it.
- **MEDIUM blocks** (2026-10-07 18:58 PT: "you're making some of these tasks far too long ... ETAs upwards of 3 hours
  which is ludicrous"). Two parts, ~60-minute target, **90-minute hard ceiling**; a block estimating > 90 min does
  Part A only and hands Part B on. Each part pushed and recorded in the queue before the next. Wave 60 held to it.
  (Supersedes the 2026-10-06 LARGE-block rule; the 30-minute rule before that was too small.)
- **Three blocks per wave**, disjoint surfaces, runnable in parallel; each merges only its own PRs.
- **No timing-bound blocks** (2026-10-03). A block runs whenever he pastes it; waiting is done by scheduled GitHub
  Actions jobs or VPS crons.
- **Every prompt ends with `END OF BLOCK x.y. If you cannot see this line, the prompt reached you truncated`.** ASCII
  only inside fences. Common rules go at the top of each fence (template: Wave 60 in `ACTIVE_QUEUE_ARCHIVE.md`).
- **Authorizations are blockquote lines** in "Needs your decision" (`> **AUTHORIZATION - <NAME> (operator, <date>:
  "<his words>")**` + what it covers / does not cover). A prompt that depends on one says so and tells the terminal
  that the table row describing a decision does NOT count. Never draft a block citing an authorization not yet given.
- **When he says "proceed with the recommended choice"**, the window's stated recommendation is his decision: log it
  in DECISION_LOG with his words and build it.
- **Never request delete permission and never sync his folder** (2026-10-04). His terminals bring his folder current.
- **Names:** **Visual Dashboard** = operational review of the whole bot (`/project`; "ERP" describes its purpose, not
  a rebuild — keep the look). **Live Terminal** = what the bot is placing / evaluating, live, full black (`/`). Both
  open via `Open Dashboard.command` (SSH tunnel to localhost:8050; drops when the Mac sleeps — re-run it).
- **"MLB can't go dark while games are going on"** (2026-10-05).
- ~~Calibration mode (2026-10-06): do not add cells~~ — **superseded 2026-10-08 by the expansion directive** ("we're
  trying to win"): more pre-registered arms, demo fills, standing authorizations, bigger VPS. See ACTIVE_QUEUE.md.
- **North star:** CLAUDE.md § "What winning looks like — the operator's north star (four pillars)". Every block reports the pillar it moved; the forest check at every wave close updates the
  sitrep's pillar scoreboard and flags two pillar-less waves in a row (2026-10-09).
- **Handoff only after the last wave is verified** (2026-10-07: "AFTER wave 60 is finished then we'll handoff"), and
  the handoff always delivers the operational doc + paste-in + queue as file cards and the paste-in in a chat fence,
  unasked (2026-10-08). `/strategic-handoff` does this.

---

## 3. Traps

- **Deploy rule (#158, GG-432):** a push to main restarts `t4-mlb` only if it changes a file in t4-mlb's import closure
  AND no MLB game is live; otherwise skipped and logged in the Deploy job summary. Blocks record the decision.
- **statsapi.mlb.com 406s the VPS on CDN cache misses.** MLB data needing statsapi runs on GitHub Actions
  (`mlb_games_cache_sync.yml`, `mlb_features_sync.yml`) and syncs to the VPS.
- **GitHub can't union-merge `SESSION_CLAIMS.md` / `.last_session_checkpoint`.** Dirty PR → merge origin/main into
  the branch locally, push, CI, merge.
- **Concurrent claims collide on GG numbers** (60.2 hit two collisions before finding a free range). Blocks claim at
  run time; the queue never pre-assigns numbers.
- **VPS has 961 MB RAM** (GG-477): new cron lines avoid :00/:30 and the staggered minutes, in their own marked block.
- **Shadow-cron authorization covers NEW lines only.** Editing/removing an existing line needs his written line.
- **"Logged" is not "flagged on the row."** 60.2 found NHL T3 rows lacked the confirmed flag even though the model used
  the projected goalie (GG-530, fixed for new rows by #188). Check the stored rows, not the code path.
- **"submitted" is not "filled."** T4 positions record `kalshi_order_status="submitted"` and nothing re-polls; the
  demo venue's `/portfolio/fills` history is the truth (60.1).
- **A handoff's prose is a claim.** Verify PR state, CI, merge commits, results docs before closing a block.
- **GitHub GraphQL is blocked in cloud sessions;** use REST (`gh api`).

---

## 4. State at handoff (derived 2026-10-08 at `edb3138`)

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-530** · **T-746** · **ADR-0071** · **EXP-038** · ADR-0070 ACCEPTED (2026-10-08) |
| Gap log | **130 OPEN** · parity 157 headers = 157 status lines · no duplicate ids across live + archive · hook prints the live count (GG-426 fixed) |
| Registry | **104 cells:** ACTIVE 1 (T4M-PROJ) · SHADOW 24 (3 MLB player-hits, 12 NFL, 9 NHL) · BLOCKED 2 · DARK 1 · NOT_IMPLEMENTED 76 (incl. 12 NBA). MLB postseason game cells log + settle but are not registered SHADOW. |
| Capital | **$0 real.** kelly 0.0 on every operating band. T4M-PROJ places paper measurement stakes min($1, max-contracts × price) — ADR-0050. |
| T4M-PROJ truth (60.1) | Epoch-12 cohort 1,952 rows: **107 filled on demo, 1,845 never filled, 0 unverifiable.** P&L/bet all -0.053 (CI -0.148..+0.043, 176 games); fills -0.403 (CI -0.650..-0.156, 41 games). GG-527 OPEN HIGH = his call. |
| Paper books | T1 MLB drawdown 12.44%, T4M-PROJ 13.45% (2026-10-05, after ADR-0071 booking) vs 20% kill. NFL game-market book archived. |
| Shadow arms | NFL 12 (EXP-037, first look ~11-02) · NHL 9 (EXP-036 + addenda; PRELIMINARY all season, GG-514 accepted) · MLB postseason 12 · NBA 12 (EXP-038; preseason to `PREGAME_SHADOW_PRESEASON/`, cron line to remove after 10-20) |
| Calibration engine | Daily 13:49 UTC; sealed; frozen release manifests; NHL B=10,000 per-game; NBA looks 150/400, seed 20261006. 0 cells at a look. |
| Settlement | Kalshi cross-check: 1,229 / 1,229 NFL + MLB settlements agree (59.2). |
| Resolved-ledger guard | Live (#185). First real run **Mon 10-12 14:20 UTC**; a trip writes `t4_mlb_resolved_ledger.rebuild_<UTC>.jsonl` + WARNING in `band_monitor_cron.log`. |
| Scheduled GitHub jobs | `mlb_games_cache_sync.yml`, `mlb_features_sync.yml`, `nhl_goalie_probe.yml` (branch `data/nhl-goalie-probe`, stops 10-14) |
| VPS | Last deploy `056428f` (#188), success; t4-mlb untouched by Waves 59–60. |
| Open PRs | Only stale ones from Waves 30–34 (#133, #144, #146, #149). |
| In flight | **Nothing.** Wave 60 closed; Wave 61 is yours to write. |

---

## 5. Where the arc is, and what Wave 61 should be

Waves 38–44 found no edge net of cost across 14 families. Since Wave 45 the strategy is breadth under
pre-registration; since 2026-10-06 the focus is **calibration**. Waves 52–60 were the plumbing that makes a verdict
mean something: landing + deploy rule, Kalshi settlement, MLB data off statsapi, OOM, truthful dashboards, NBA arm,
the calibration engine, a re-verified gap log, and — Wave 60 — the truth about T4M-PROJ's sample.

**Operator's stated horizon (2026-10-07):** he wants long stretches on edge calibration — research, wiring variants,
feature extraction. The window's view, given to him: the calibration clock runs on settled games, not sessions; until
NFL's first look (~11-02) the work is keeping data clean. Research on a **separate exploratory track** (archived
prices, past seasons, never touching frozen models or pre-registered cells) can start beforehand, so pre-registered
challengers are ready when first verdicts land. Not yet built; candidate for Waves 61–62.

**Wave 61 candidates (judgment, in priority order):**
1. **Route GG-527 first** (window recommends (b) keep the rows as calibration evidence only, G6 requires fills, plus
   (c) stand T4M-PROJ down after the World Series). Then a block implementing whatever he picks — no cohort, status or
   ledger change without his line.
2. **NBA flip on/after 10-21** — `scripts/w59_3_nba_flip_check.py` prints the exact `promote_cell_status` lines; and
   remove the preseason cron line after 10-20 (its own block; it was added under the new-line authorization).
3. **GG-401 closure check** — new NHL T3 rows since #188 must carry `confirmed=False` + `starter_source`; then RESOLVE.
4. **NFL first-look readiness** — dry-run the real release on the day a cell crosses 60, using 59.2's REPORT renderer.
5. **Exploratory research track** design (above), if he wants it.
6. **MLB winter posture** decision → block. **Retire** the 4 resolved entries still in the live gap log.

---

## 6. Open operator decisions

| Item | State |
|---|---|
| **GG-527 T4M-PROJ cohort** | Routed 2026-10-08 with recommendation (b)+(c). The most important open call. |
| MLB winter | After the World Series: stand T1/T4 MLB down or idle. |
| GG-529 EXP-038 second look | Define the 2027-01-31 date-triggered look; needed before January. |
| GG-320 · GG-285 · GG-289 · GG-441 · GG-347 | T4M-PROJ band placement · reachable P&L gate · self-modifying script approvals · unresolved stake in kill switch · unexplained SSH poller. |
| T1 MLB postseason flag · EXP-034 · detached VPS jobs | Unchanged; EXP-034 park recommended. |
| Long-carried | Polymarket KYC · odds feed · APR-0035 · ADR-0063..0068 · APR-0034/0036. |

---

## 7. What this window got wrong (so you don't)

1. **Asserted from documents instead of data** — told him the bot places nothing, then called the stakes "flat $1".
2. **Synced his folder without delete permission** while terminals ran (stale `origin/main.lock`). Now forbidden.
3. **Drafted a block citing an authorization not yet given** (caught before issue).
4. **Read "ERP-esque" literally.** Ask what a word is for before building to it.
5. **Sized Wave 59 blocks at 2–3 hours each.** He had asked for weight, not marathons. MEDIUM (60/90) fixed it.
6. **Handed off a wave early** — read "finish up that wave then wrap it up" as "issue 59 and leave". Ask when the
   handoff point is ambiguous; the default is after verification.
7. **Wrote an authorization phrase verbatim inside a decision-table row**, which a terminal could have read as the
   authorization itself. Conditional prompts now require the blockquote form.

---

## 8. Standing DO NOT

- Never bypass, disable or work around a permission control. Record the command and refusal, hand back.
- No order against the production Kalshi account or with real funds. Demo only, always.
- No sizing / kelly_fraction change without an ADR.
- No scoring of a cell below its judged n; never relabel a pre-registered verdict or change a pre-registered
  parameter after seeing results (dated addenda before judged data, with his line, are the only route).
- No live-ledger write without backup + dry-run diff (GG-228 / ADR-0071 §5).
- No edit of an existing cron line without his written line; new shadow lines only under the standing authorization.
- No hand-pulls on the VPS; no log rotation; no manufactured rows, positions, prices, fills or scores.
- Pre-assign no T-/GG-/ADR- numbers; blocks claim at run time.

---

## 9. First actions for the incoming window

1. `git fetch`; derive state from origin/main (SHA, max GG/T/ADR/EXP, OPEN count + parity, registry counts) and diff
   against §4. Report drift in one short list.
2. Read ACTIVE_QUEUE.md top to bottom (sitrep, NOW, Needs your decision). Load it into the chat as a file card.
3. Short sitrep to him; route GG-527 if he hasn't answered it; then write Wave 61 (three MEDIUM blocks) into the
   queue under NOW, with the prompts inside, and load the queue again.
4. At your own handoff: `/strategic-handoff`.
