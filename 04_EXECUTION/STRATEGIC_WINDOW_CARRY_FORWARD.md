# Strategic Window — Carry Forward

**Written:** 2026-10-08 ~00:40 UTC (5:40 PM PT 10-07), at the close of the window that ran Waves 52 → 59.
**Verified against:** `origin/main` at the commit that adds this file (GitHub API + tracked files). Every figure in §4
was derived by running a command at write time; treat each as a claim to re-verify.
**Previous version** (Waves 45 → 51): `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-10-03.md`. Its §5–§6
(empirical record, Wave 45–51 findings) and the 2026-10-01 version's §5 still stand.

> This file is the operating context for the strategic window: how the operator wants to work, the traps, state at
> handoff, open decisions, and what this window got wrong.

---

## 1. The role

The strategic window **directs; terminals execute.** It derives state from `origin/main` and GitHub (never from a
terminal's prose or recollection), writes paste-in blocks into `04_EXECUTION/ACTIVE_QUEUE.md`, verifies each finished
block against GitHub when the operator says it is done, updates the queue, and routes findings, verdicts and decisions
to him. **Never hand him commands to run.** Sandbox / paper / demo actions are plumbing — handle them. **Only real
capital is his.** He wants blunt, short answers and candor about pace and strategic error.

He runs blocks in local Claude Code terminal sessions on his Mac (repo at `~/Documents/Claude/Projects/Prediction
Markets`). He sometimes runs a whole wave in one Claude Code (cloud) chat instead — that executor has no VPS access.

---

## 2. Protocols (operator, this window — follow exactly)

- **Load ACTIVE_QUEUE.md into the chat as a file card every time it changes** (`SendUserFile`, display render). Never
  point him at a folder path. The queue always carries the next wave's prompt blocks inside it, under NOW.
- **Never request delete permission and never sync his folder.** (2026-10-04: "stop asking permissions to delete the
  entire fucking project folder".) The prompt can only name the whole folder. His terminals bring his folder current
  when they fetch. Read-only git on his machine.
- **LARGE blocks** (2026-10-06: "the terminals can handle plenty of weight"). Supersedes the old 30-minute rule. Each
  block is multi-part; every part is pushed and recorded in the queue before the next, so a cut never strands work.
- **Three blocks per wave**, disjoint surfaces; each block merges only its own PRs.
- **No timing-bound blocks** (2026-10-03: "Don't give me any timing blocks"). A block must run whenever he pastes it.
  Waiting is done by scheduled GitHub Actions jobs or VPS crons, never by a terminal.
- **Every prompt ends with `END OF BLOCK x.y. If you cannot see this line, the prompt reached you truncated`** — 53.3
  arrived truncated once. Prompts are ASCII-only inside fences.
- **Names:** **Visual Dashboard** = operational review of the whole bot (`/project`); "ERP" describes its purpose, not
  a rebuild — he likes its look. **Live Terminal** = what the bot is placing / evaluating, live, full black (`/`). Both
  open via `Open Dashboard.command` (SSH tunnel; it drops when the Mac sleeps — just re-run it).
- **"MLB can't go dark while games are going on"** (2026-10-05). MLB postseason arms must log every game day; nothing
  in their data path may depend on a manual step.
- **Calibration mode** (2026-10-06): the project's focus is now getting cells to verdicts honestly — not adding cells.
- When he says "proceed with the recommended choice", the window's stated recommendation is his decision: log it in
  DECISION_LOG with his words and build it.

---

## 3. Traps

- **Since #158 (GG-432, 2026-10-05) code can land at any hour.** A push to main restarts `t4-mlb` only if it changes a
  file in t4-mlb's import closure AND no MLB game is live; otherwise the restart is skipped and logged in the Deploy job
  summary. Blocks must record that decision for every merge.
- **statsapi.mlb.com 406s the VPS on every CDN cache miss** (GG-070/440/470/489). Anything MLB that needs statsapi runs
  on GitHub Actions and syncs to the VPS: `mlb_games_cache_sync.yml`, `mlb_features_sync.yml`. The VPS's old 22:30 UTC
  features cron was commented out (authorized 2026-10-06).
- **GitHub can't union-merge `SESSION_CLAIMS.md` / `.last_session_checkpoint`.** PRs go `dirty` whenever main moves;
  fix by merging origin/main into the PR branch locally (the repo's merge=union driver resolves them).
- **VPS has 961 MB RAM.** Crons starting on the same minute OOM-killed t4-mlb (GG-477, fixed by the stagger + 2 GB
  swap). New cron lines must avoid :00/:30 and the staggered minutes, and live in their own marked block.
- **Shadow cron authorization covers NEW lines only.** Editing or removing an existing cron line needs his written yes.
- **A handoff's prose is a claim.** Verify against GitHub (PR state, CI, merge commits) before closing a block.
- **GitHub GraphQL is blocked in cloud sessions;** use REST (`gh api`).

---

## 4. State at handoff (derived 2026-10-08 ~00:40 UTC)

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | GG-499 · T-720 claimed · ADR-0071 (ACCEPTED; ADR-0070 PROPOSED, widen+accept in 59.3) · EXP-038 |
| Gap log | **176 OPEN** (59.1 is the backlog block) |
| Registry (92 cells) | ACTIVE 1 (T4M-PROJ) · **SHADOW 24** (3 MLB player-hits, 12 NFL, 9 NHL) · BLOCKED 2 · DARK 1 · rest NOT_IMPLEMENTED. MLB postseason game cells (12) log + settle but are not registered SHADOW. NBA game cells registered NOT_IMPLEMENTED (flip after rows land, ~10-21). |
| Capital | **$0 real.** kelly 0.0 on every operating band. T4M-PROJ places flat paper measurement stakes, min($1, max-contracts × price) — ADR-0050. |
| Paper books | T1 MLB realized drawdown 12.44%, T4M-PROJ 13.45% (after ADR-0071 booking, 2026-10-05) vs 20% kill switch. NFL game-market book ARCHIVED (GG-490). |
| Shadow arms | NFL 12 cells (EXP-037, settling daily) · NHL 9 (EXP-036; T3 sealed by GG-401) · MLB postseason 12 (EXP-037, settling 11:41 UTC) · MLB player-hits (restored 58.1) · NBA (EXP-038, armed; rows from ~10-20; preseason excluded from judged n) |
| Calibration engine | Live (58.3): daily 13:49 UTC; Calibration section on /project; 33 cells, 0 at a look. **NFL first-look projection of 10-14 is wrong** (≈10-27) — fixed by 59.2. |
| Scheduled GitHub jobs | `mlb_games_cache_sync.yml`, `mlb_features_sync.yml`, `nhl_goalie_probe.yml` (writes branch `data/nhl-goalie-probe`, stops 10-14) |
| In flight | **Wave 59 issued, not yet run** (59.1 backlog, 59.2 calibration correctness, 59.3 NBA/NHL readiness + ADR-0070). |

---

## 5. Where the arc is

Waves 38–44 found no edge net of cost across 14 families. Since Wave 45 the strategy is breadth under
pre-registration ("start flyin"), and since 2026-10-06 the focus is **calibration**: get cells to their judged n and
read them honestly. Waves 52–58 were mostly plumbing that had to happen: the Waves 51–53 landing (#160), the deploy
rule (#158), Kalshi settlement as the paper resolution source (ADR-0071; 26 stuck positions booked), MLB data off the
blocked statsapi, OOM fix, truthful dashboards, NBA arm, and the calibration engine with sealed cells.

**Evidence clocks:** NFL first look at 60 settled games per cell (~late October — confirm with 59.2's projection);
NHL judged n ~2 seasons (PRELIMINARY labels allowed below it; T3 sealed until GG-401); MLB postseason banked for 2027;
NBA from 10-20.

**Wave 60 (judgment):** read 59's results; NBA cells flip to SHADOW once valid rows land (~10-21, the check 59.3
writes); NHL StarterProvider or pre-registration amendment from 59.3's verdict; whatever 59.1 ranks as top blockers;
then the **NFL first look** run with 59.2's report template the day the first cell crosses 60. MLB winter disposition
after the World Series (late October).

---

## 6. Open operator decisions

| Item | State |
|---|---|
| NHL T3 goalie (GG-401) | 59.3 gives the verdict; if (b), he chooses move T3 later vs amend the pre-registration. |
| MLB winter | After the World Series: stand T1/T4 MLB down or idle. |
| Detached read-only VPS jobs | Largely replaced by scheduled GitHub Actions jobs; line still unissued. |
| Long-carried | Polymarket KYC · odds feed · APR-0035 · ADR-0063..0068 · APR-0034/0036 — unchanged. |

---

## 7. What this window got wrong (so you don't)

1. **Asserted from documents instead of data**: told him the bot places nothing (T4 places paper stakes under
   ADR-0050), then called the stakes "flat $1.00" (they are capped by contracts: $0.05–$1.00).
2. **Synced his folder without checking delete permission** while his terminals were running — left a stale
   `.git/refs/remotes/origin/main.lock`. Now forbidden (§2).
3. **Drafted a block citing an authorization he had not yet given** (caught before issue). Gate on the written line.
4. **Read "ERP-esque" literally.** Ask what a word is for before building to it.
5. **Let the backlog ride last in blocks** wave after wave — it was always the part that got cut. 59.1 is the fix: the
   backlog as its own block.

---

## 8. Standing DO NOT

- Never bypass, disable or work around a permission control. Record the command and refusal, hand back.
- No order against the production Kalshi account or with real funds. Demo only, always.
- No sizing / kelly_fraction change without an ADR.
- No scoring of a cell below its judged n; never relabel a pre-registered verdict or change a pre-registered parameter.
- No live-ledger write without backup + dry-run diff (GG-228 / ADR-0071 §5).
- No edit of an existing cron line without his written line; new shadow lines only under the standing authorization.
- No hand-pulls on the VPS; no log rotation; no manufactured rows, positions, prices, fills or scores.
- Pre-assign no T-/GG-/ADR- numbers; blocks claim at run time.

---

## 9. First actions for the incoming window

1. `git fetch`; derive state from origin/main (refs, max GG/T/ADR/EXP, OPEN count, registry counts) and diff against §4.
2. Read ACTIVE_QUEUE.md (status-first) and, if Wave 59 has run, its three handoffs and results docs; verify each block
   against GitHub; close Wave 59 in the queue; load the queue into the chat.
3. Give him the sitrep, then write Wave 60 into the queue with the prompt blocks inside.
