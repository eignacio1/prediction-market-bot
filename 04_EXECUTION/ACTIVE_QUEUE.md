# Active queue — the only prompt file to read

> **RULE: this file contains ONLY blocks that are currently firing.** Closed prompts move verbatim
> to `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md` BEFORE the queue rotates. Wave 47 is archived there.

**Verified against:** `origin/main = 48df4c4` (2026-10-02 17:01 PT). *This window cannot `git fetch` or push.*

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-356** · **T-615** (claimed through T-620) · **ADR-0070** (on a branch, PROPOSED) · **EXP-037** |
| Capital | **$0.** `kelly_fraction = 0.0` on every operating band. Demo venue only. SHADOW = evaluate and log. |
| Candles | **Validated** for archived-MLB market structure: EXP-035 Gate 2 PASSED 7/7 on KXMLBTOTAL (G7 by a floating-point margin). Part 1 stays FAILED. |
| NHL | **Flying.** Code, frozen model and cron on main/VPS; first T3 rows live. Pre-registration on a branch, not main. |
| NFL + MLB postseason | **Built, not flying.** Branch `session/exp037-nfl-land` green (3592 passed), not landed; nothing on the VPS; **NFL Week 5 kicks off Sunday 10-4.** |
| Dashboards | Live Terminal v2 + `/project` deployed — verified only in a stub DOM, never a real browser. |
| VPS | at `1e097e0`; `t4-mlb` keeps older code in memory. |

---

## ⬛ OPERATOR DIRECTIVE, 2026-10-02 17:03 PT — TIME-BOUNDED BLOCKS

> *"We added so many extra tasks to the windows that it was about to take over 2+ hours for each window to
> complete so I cut it short each way. I'm not letting windows run for hours on end — if there's a task that'll
> take that long, don't place it."*

> And minutes later, when this wave was first sized at ~75 minutes a block: *"Even 75 minutes is way too long —
> none of these tasks better take 75 minutes."*

**Every block is sized at about 30 minutes, hard stop at 45** — at the nearest pushed boundary, with a handoff
that names where the next session resumes. Scope is cut to fit the clock, never the reverse: one job per block,
done completely. Budget includes the one full test-suite run (~11 minutes) a block landing `src/` code needs.

**What does not belong in a window:** anything whose wall time is set by waiting rather than working — multi-hour
API back-captures at a rate cap, live samplers that must span hours, waiting for games to start or settle. Those
run unattended on the VPS (cron or a detached job, each under its own authorization) and a later block reads what
they produced. Wave 47's three overruns were all of this kind: a 1-hour fetch, a 2.5-hour sampler, and "hand-run
the slate as long as the session lasts."

---

## ⬛ WHAT WAVE 47 FOUND

- **Candles hold, scoped.** Gate 2 reproduced the archive on KXMLBTOTAL on all seven checks (G2 0.944, G3 0.999, B and H
  within 0.0002 / 0.0000). The only hard edge: G7's earliest bucket passed by floating-point margin on a 0.005 tick grid.
  Licensed: candle reconstruction for the same market structure. Not licensed: every other series by assumption.
- **NHL is the first new arm in the air.** Bivariate-Poisson goals model, frozen and hashed; held-out 2025-26: moneyline
  beats climatology by only ~0.002 Brier, an LR benchmark is better, totals under-predicted, away puck line and totals
  slightly worse than climatology — reported, not hidden. Cron installed; 15 T3 rows on night one; T1 abstains on some
  markets for reasons not yet investigated.
- **NFL and MLB are one push from flying.** 12 NFL cells + 12 MLB game cells built, pre-registered, frozen. Four NFL T1 cells
  flipped to SHADOW — on the branch only. **No stuck postseason positions** (the resolver fix was not needed).
- **The evidence clock is long, and the pre-registrations say so.** NFL: first look at 60 settled games per cell (~4 weeks),
  MDE ≈ 0.025 against a plausible true effect ≤ 0.02 — the modal first-look result is "keep accruing". NHL: judged n = 2,500
  games per cell (~2 seasons). MLB postseason rows are banked for 2027. **Breadth now; verdicts later.**
- **Dashboards deployed but unproven in a real browser** (47.1's own Q6). The operator relies on them; that gets fixed first in 48.3.

---

## ⬛ FIRE NOW — Wave 48, three blocks, concurrent

| Paste | Block | Budget | One-line purpose |
|---|---|---|---|
| **1st — now** | **48.1** | **~30 min** | **Make NFL and MLB fly before Sunday.** Land 47.2's work in one push, deploy, install the NFL + MLB shadow crons, dry-run them. |
| 2nd | **48.2** | **~30 min** | **Get long jobs off the terminals; settle the record.** A small detached-job runner for the VPS, the history back-capture launched on it (if authorized), queue + archive landed, Wave 47 gaps registered. |
| 3rd | **48.3** | **~30 min** | **The operator's eyes: both dashboards proven in a real browser, defects fixed, redeployed.** |

**48.1 first and now:** NFL T1 windows for Sunday games are open today and Saturday. Every hour it waits is rows that will never exist.

Surfaces are disjoint:
- **48.1 owns** `pregame_shadow/` (and its contract), NFL and MLB shadow modules and models, `market_type_registry.py`
  (sole owner, including NHL flips), `deploy/cron_exp037_pregame_shadow.conf`, the VPS pull, `scripts/generate_mlb_features.py`
  (already-built opt-in flag only), one results summary.
- **48.2 owns** `scripts/vps_job.py` + its tests (new), the history-store builder from 47.1 D4 (`scripts/kalshi_history_build.py`,
  `analytics/kalshi_history.py`), the shared tree's sync, the `04_EXECUTION/` record files, **`GOVERNANCE_GAP_LOG.md` /
  `DECISION_LOG.md`**, the ADR register row for ADR-0070, one results summary.
- **48.3 owns** `scripts/web_dashboard.py`, `Live Terminal.html`, `scripts/generate_project_state.py`, `Visual Dashboard.html`,
  `pmbot-web-dashboard` deploy/restart (standing authorization), one results summary.
- **The VPS pull:** 48.1 does it first. 48.3 pulls only after 48.1's pull is on record, by the same additive-check procedure.

**Exactly three fences. A fourth means something is wrong -- stop.**

---

## Read this first (standing)

- **Three blocks per wave. Not four.** Operator directive 2026-09-15.
- **Every block: ~30 minutes, hard stop at 45.** Operator directives 2026-10-02 17:03 and 17:09. One job per block, done completely. Waiting is not work: long fetches, samplers and slate-watching go to the VPS, not the window.
- **Deliverable 0 in every block: land any un-landed predecessor and confirm your base.**
- **Claim IDs at run time and re-verify after ANY release or retry** (GG-322). Claim real ranges, never "TBD".
- **A premise written in a block is a claim to verify, not a fact.** Including every number in this file.
- **Never bypass, disable, or work around a permission control.** Record the exact command and refusal text, then hand back.
- **Pre-register before scoring.** Frozen pre-registrations stay frozen. No scoring before a cell's judged n; between looks, counts only.
- **SHADOW means evaluate and log.** No order, position, paper fill, stake or `kelly_fraction` change.
- **A merge is a deployment here.** Production updates by `git pull` in `/opt/prediction-market-bot`. Before any pull: paste `HEAD..origin/main` on the VPS and confirm every runtime file reachable from `t4-mlb` or a cron job is additive and covered by the green suite. Never restart `t4-mlb`.
- **Paper and shadow work is plumbing** (operator's standing framing): landing green, tested shadow code to main needs no further go-ahead. Real capital is his.
- **The Live Terminal and the project view move with the bot.** Any block that adds a cell, ledger, data source or verdict makes it visible in the same block.
- **No background process outlives its session unrecorded.** And per the directive above: none should need to.
- Register-and-stop on any gap outside scope (Hard Rule 11) — registration goes to 48.2 via your results summary.

---

## Sequencing track

| Wave | Status | Outcome |
|---|---|---|
| 10-46 | CLOSED | see `ACTIVE_QUEUE_ARCHIVE.md` |
| **47** | **CLOSED — cut short at ~2h by the operator** | Gate 2 PASSED 7/7. NHL flying (cron live). NFL + MLB built, pre-registered, not landed. Dashboards v2 + `/project` deployed (unproven in a browser). EXP-034 corrected run: no verdict. History store partial. GG-340..356 registered. |
| **48** | **FIRING** | NFL + MLB flying before Sunday. Long jobs moved to the VPS. Dashboards proven in a browser. |

---

## Why this wave is shaped this way

**Three things were blocking, and none of them was hard — each was stranded.** NFL and MLB are green on a branch.
The history store is half-built in one worktree. The dashboards are deployed but nobody has looked at them in a
browser. Wave 48 lands each of those in a session-sized block, and moves the one class of work that blew the clock —
waiting — off the terminals for good.

**What is deliberately NOT here:** the full board survey (it needs the history store complete — a multi-hour fetch
that now belongs on the VPS), EXP-034's corrected run (a ≥2.5-hour live sampler — same), **NHL hardening** (team codes,
T1 abstentions, the contract switch — Wave 49), NBA (opens 10-20; Wave 49) and in-play arms. None was dropped; each
waits for a slot that fits the clock.

---

## WAVE 48 BLOCKS

---

# 48.1 -- MAKE NFL AND MLB FLY BEFORE SUNDAY - BUDGET ~30 MIN (HARD STOP 45)

```
TIME BUDGET: about 30 minutes. Hard stop at 45, at a pushed boundary, with a handoff.
One full suite run (~11 min) is in the budget; run it ONCE, on the combined NFL + MLB branch.
Do NOT hand-run slates or wait for games. The crons you install do the waiting.

Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
RESUME: scripts/new_session_worktree.sh "exp037-land-deploy", then read
  11_MEMORY_HANDOFF/SESSION_HANDOFF_20261002_2357.md on branch
  origin/session/20261002T222218Z-fly-nfl-pregame. It is your plan; this block is its execution.
Claim your own IDs at run time (GG-236); re-verify after ANY release or retry (GG-322). EXP-037 and
T-608 are the work you continue. Declare the block's whole arc as the deliverable at claim time.

YOU OWN, THIS WAVE, EXCLUSIVELY:
  src/prediction_market_bot/pregame_shadow/ (including contract.py), NFL and MLB shadow modules and
  models from EXP-037, c5_execution/market_type_registry.py (sole owner, NHL flips included),
  deploy/cron_exp037_pregame_shadow.conf, scripts/generate_mlb_features.py (only the opt-in flag
  already built on the branch), the VPS pull, one results summary.
YOU DO NOT WRITE: GOVERNANCE_GAP_LOG.md or DECISION_LOG.md (48.2), nhl_* or dashboard files (48.3).

THE STATE YOU START FROM -- verify, do not assume (handoff 2357):
  - session/exp037-nfl-land @ fc4180d: origin/main + NFL work; full suite 3592 passed, 28 skipped;
    two existing files touched, both additive. NOT on main.
  - session/20261002T222218Z-fly-nfl-pregame @ 574b85e: adds D0 harvest report, ADR-0070 (PROPOSED),
    MLB model/runner/pre-registration, --include-postseason. No full suite run on it.
  - VPS at 1e097e0. No EXP-037 cron installed. 4 NFL T1 cells flipped to SHADOW on the branch only.
  - No stuck postseason positions (D6(a)); no resolver change needed.
  - NHL (47.3) runs its own runner and a local Protocol fallback because contract.py is not on main.

DELIVERABLE 0 -- BASE. Paste origin/main SHA, the two branch tips, VPS HEAD.

DELIVERABLE 1 -- LAND NFL AND MLB IN ONE PUSH. The operator's standing framing makes landing green
  shadow code plumbing; no further go-ahead is needed. Rebase the 574b85e work (NFL + MLB + ADR-0070
  doc) onto current origin/main as one branch; relax the MLB NOT_IMPLEMENTED pin in
  tests/test_market_type_registry.py (~line 102) only as far as the cells you flip; run the full
  suite ONCE; push. If MLB is red and NFL green, land NFL alone and report MLB -- do not debug past
  your budget. Paste SHA and the suite summary line. ADR-0070 lands PROPOSED.

DELIVERABLE 2 -- DEPLOY AND ARM NFL. On the VPS: paste git log --oneline HEAD..origin/main; list
  every changed file reachable from t4-mlb's or any cron job's import graph; pull only if all are
  additive and covered by the green suite. No t4-mlb restart, no pip. Run the --refresh seed. Dry-run
  every cron line by hand. Install the NFL block from deploy/cron_exp037_pregame_shadow.conf under
  the 2026-10-02 shadow-evaluation authorization. Paste live crontab -l, then proof of the first
  SCHEDULED firing writing rows (do not wait past your budget for it -- if the next firing is beyond
  your budget, record when it is due and let 48.3 or Wave 49 confirm it).
  NFL T1 cells already shown valid: flip on main. T2/T3: flip only when a scheduled firing has
  written a valid row for them.

DELIVERABLE 3 -- ARM MLB POSTSEASON (if D1 landed it). Install the MLB game-market shadow cron
  lines in the same install as NFL (same authorization, same dry-run rule).
  ADDING --include-postseason TO THE EXISTING T1 MLB CRON LINE IS AN EDIT TO AN EXISTING CRON LINE.
  The shadow authorization does not cover it. Do it only if "Needs your decision" in this file holds
  an authorization line naming it; otherwise leave the line untouched and report T1 still matches 0.

DELIVERABLE 4 -- THE CONTRACT, FOR NHL. contract.py is now on main (D1). Report its SHA in your
  summary's first lines so 48.3 can switch NHL off its fallback. Flip NHL cells with valid rows to
  SHADOW per 47.3's results summary (NHL_MONEYLINE_T3, NHL_PUCK_LINE_T3, NHL_GAME_TOTAL_T3 at last
  report) and any T1/T2 cells the NHL cron has since written valid rows for.

DELIVERABLE 5 -- REPORT. Short results summary: landing SHAs, suite line, VPS pull record, crontab
  before/after, when each band's first scheduled firing is due, registry flips with SHAs, and GAPS
  FOUND -- FOR REGISTRATION BY 48.2 (paste 47.2's list from the handoff as-is; do not re-investigate).

DO NOT:
  - Hand-run slates or wait for games past your budget. Install, dry-run, record when it fires.
  - Edit the existing T1 MLB cron line without its own authorization line.
  - Restart t4-mlb or any service. Pull on the VPS without the additive check pasted.
  - Score any cell. No cell has reached its judged n.
  - Open a position, write to any pool, submit any order, or touch sizing or kelly_fraction.
  - Land anything red. Accept ADR-0070.
  - Write to GOVERNANCE_GAP_LOG.md or DECISION_LOG.md; edit nhl_* or dashboard files.
  - Submit any order against the production Kalshi account or with real funds. Demo only, always.
  - Bypass, disable or work around a permission control. Record the exact refusal and hand back.
```

---

# 48.2 -- GET LONG JOBS OFF THE TERMINALS; SETTLE THE RECORD - BUDGET ~30 MIN (HARD STOP 45)

```
TIME BUDGET: about 30 minutes. Hard stop at 45, at a pushed boundary, with a handoff.
This block LAUNCHES long jobs; it never waits for one to finish. vps_job.py is small -- keep it small.

Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "vps-jobs-and-record"
Claim your own IDs at run time (GG-236); re-verify after ANY release or retry (GG-322).
Highest seen at queue-write time: GG-356, T-615 (T-615..T-620 claimed by 47.1), ADR-0070, EXP-037.
You are the only block this wave that writes GOVERNANCE_GAP_LOG.md and DECISION_LOG.md.

YOU OWN, THIS WAVE, EXCLUSIVELY:
  scripts/vps_job.py + tests (new); scripts/kalshi_history_build.py and analytics/kalshi_history.py
  (47.1 D4's builder and reader); the shared main tree's sync; 04_EXECUTION/ACTIVE_QUEUE.md and
  ACTIVE_QUEUE_ARCHIVE.md (land as written); GOVERNANCE_GAP_LOG.md; DECISION_LOG.md; the ADR
  register row for ADR-0070; one results summary.

WHY: the operator cut every Wave 47 window at ~2 hours and set a rule -- no task that takes that long
goes in a window. Wave 47's overruns were waiting, not working: 47.1's Gate 2 fetch took 3,740 s at
the 3.3 req/s cap, its EXP-034 sampler needs >= 6 rounds x 21 min, and the NFL/NHL history store
(47.1 D4) is a multi-hour back-capture. Those jobs belong on the VPS, unattended.

DELIVERABLE 0 -- BASE. Paste origin/main SHA; shared tree HEAD and left/right count.

DELIVERABLE 1 -- LAND THE RECORD. The shared tree holds uncommitted Wave 46/47/48 queue and archive
  edits. From a fresh worktree off origin/main, copy ACTIVE_QUEUE.md and ACTIVE_QUEUE_ARCHIVE.md
  byte-for-byte from the shared tree, commit path-scoped, push; paste hash-object equality. Then
  fast-forward the shared tree exactly as 46.3 did (restore only the two files you landed; anything
  else blocking = stop and report; never stash, reset or clean).

DELIVERABLE 2 -- scripts/vps_job.py: A DETACHED-JOB RUNNER FOR READ-ONLY LONG WORK.
  launch <name> -- <command...>: runs on the VPS under nohup/setsid with a PID file, a log, a
    start record (UTC, command, code sha, rate cap), and a completion marker with exit code;
    refuses to start a second copy of the same name; never runs anything that imports an order,
    position, sizing or paper-trader path (test it, the way pregame_shadow's safety test does).
  status <name> / tail <name> / stop <name>.
  It is a launcher, not a scheduler: it creates no cron entry and needs none.
  Tests. Land.

DELIVERABLE 3 -- LAUNCH THE LONG JOBS, ONLY IF AUTHORIZED.
  Check "Needs your decision" for an authorization line naming DETACHED READ-ONLY VPS JOBS.
  If present, launch with vps_job.py and record each launch (name, PID, expected duration from
  call-count arithmetic, rate cap) in your summary, then MOVE ON -- do not wait:
    a) kalshi-history: finish 47.1 D4 on the VPS -- NFL series (moneyline, spread, total, team total)
       for 2025 and 2026 to date, and NHL (moneyline, puck line, total) for 2025-26 and 2026-27 to
       date, with settlements; idempotent; at or below 3.3 req/s; resumes from the partial KXNFLGAME
       work. The store lives on the VPS; the reader learns its path from one config line.
    b) exp034-d3: the EXP-034 corrected run from amendment fa29318, fresh round 0, as frozen. Only if
       the operator has NOT parked it (see "Needs your decision").
  If the line is absent: land vps_job.py, write each launch command into your summary ready to run,
  and stop there. That is a complete close.

DELIVERABLE 4 -- REGISTER AND LOG.
  - Register the gaps from: EXP036_NHL_PREGAME_SHADOW_RESULTS_2026-10-02.md (GAPS FOUND, 9), the
    EXP-037 D0 harvest report and SESSION_HANDOFF_20261002_2357.md's list, and 47.1's DECISION_LOG Q6
    concerns. Deduplicate against GG-329..356. One line of evidence each -- no investigation.
    48.1/48.3's lists are Wave 49's to register.
  - DECISION_LOG: the operator directives of 2026-10-02 17:03 and 17:09 (blocks ~30 minutes, hard stop
    45; long waiting work off the terminals), verbatim.
  - ADR-0070 (probit-Platt, PROPOSED) gets its register row once 48.1 lands the file. Check the
    number is unique across git log --all. 47.3 also deviated from ADR-0004 (bivariate Poisson +
    Platt) with no ADR: register that as a gap pointing at ADR-0070's decision, do not write a second
    ADR without the operator.

DELIVERABLE 5 -- REPORT. Results summary: landed SHAs, the runner, each launch (or the ready-to-run
  commands), registrations with GG numbers, and GAPS FOUND.

DO NOT:
  - Wait for a launched job to finish, or run a long job in the foreground of this window.
  - Launch any job without the authorization line. A launcher is not a scheduler; add no cron entry.
  - Run anything through vps_job.py that can reach an order, position, sizing or paper-trader path.
  - Relabel EXP-034's original FAIL or EXP-035 Part 1.
  - Stash, reset --hard, clean, or checkout any shared-tree path you did not land.
  - Restart any service. Touch any pool, position, sizing or kelly_fraction.
  - Submit any order against the production Kalshi account or with real funds. Demo only, always.
  - Bypass, disable or work around a permission control. Record the exact refusal and hand back.
```

---

# 48.3 -- THE OPERATOR'S EYES: DASHBOARDS PROVEN IN A REAL BROWSER - BUDGET ~30 MIN (HARD STOP 45)

```
TIME BUDGET: about 30 minutes. Hard stop at 45, at a pushed boundary, with a handoff.
One job: make both dashboards correct in a real browser. Targeted tests for scripts/; the full suite
only if you touch src/.

Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4. Paste outputs.
scripts/new_session_worktree.sh "eyes-and-nhl"
Claim your own IDs at run time (GG-236); re-verify after ANY release or retry (GG-322).

YOU OWN, THIS WAVE, EXCLUSIVELY:
  scripts/web_dashboard.py, "Live Terminal.html" (byte-identical to its embedded _HTML),
  scripts/generate_project_state.py, "Visual Dashboard.html", the pmbot-web-dashboard deploy/restart
  under the standing authorization, one results summary.
YOU DO NOT WRITE: market_type_registry.py, pregame_shadow/ (48.1), nhl_* (Wave 49),
  GOVERNANCE_GAP_LOG.md or DECISION_LOG.md (48.2).

THE STATE YOU START FROM -- verify, do not assume:
  - Live Terminal v2 and /project were deployed by 47.1 (4273c7f, 1e097e0) and verified ONLY in a
    JavaScriptCore stub-DOM harness, never a real browser (47.1's own Q6 concern 1).
  - /project rendered ~13.7 KB on the VPS because gitignored exp_output stores are absent there;
    "awaiting" panels must not read as healthy (GG-341 class).
DELIVERABLE 0 -- BASE. Paste origin/main SHA and the VPS's running process.sha for the dashboard.

DELIVERABLE 1 -- PROVE THE DASHBOARDS IN A REAL BROWSER.
  Through the SSH tunnel (the same one "Open Dashboard.command" opens), load / and /project in
  headless Chromium (Playwright). For each: full-page screenshot, every JS console error, every
  failed request, time to first data render. Check: no number appears without live data (kill the
  tunnel mid-test and confirm the page goes NOT LIVE rather than freezing on old numbers); freshness
  ages tick; the COVERAGE grid matches the registry; the SHADOW module shows NHL rows that exist on
  the VPS; PIPELINE tiles reflect real C1-C8 state. Fix every defect found, with tests; land; deploy
  and restart pmbot-web-dashboard ONLY by the standing procedure, pulling only after 48.1's VPS pull
  is on record; re-run the browser check against the RUNNING process. Commit the screenshots (or
  their sha256 if large) and put them in your summary so the operator can see what you saw.
  Copy the landed "Live Terminal.html" into the shared tree's project root; regenerate the static
  "Visual Dashboard.html" there from the generator.

DELIVERABLE 2 -- REPORT. Short results summary: screenshots and console results before and after,
  every defect and fix, the running-process verification, and GAPS FOUND (Wave 49 registers them).
  Anything you could not fix inside 45 minutes is a gap with a one-line description, not overtime.

DO NOT:
  - Show any number that is not read from a live source or generated from a tracked file.
  - Restart any service other than pmbot-web-dashboard, or restart it outside the standing procedure.
  - Pull on the VPS before 48.1's pull is on record.
  - Score any cell. Open a position, write to any pool, or touch sizing or kelly_fraction.
  - Edit market_type_registry.py, pregame_shadow/ or nhl_*. Write to GOVERNANCE_GAP_LOG.md or DECISION_LOG.md.
  - Submit any order against the production Kalshi account or with real funds. Demo only, always.
  - Bypass, disable or work around a permission control. Record the exact refusal and hand back.
```

---

## THE ARC — Waves 48 through 51

| Wave | The question it answers |
|---|---|
| **48** | *Are all 33 pre-game cells logging unattended, and can the operator see them?* NFL + MLB armed before Sunday; long jobs moved to the VPS; dashboards proven in a browser. |
| **49** | **NHL hardening** (team codes, T1 abstentions, contract switch, pre-registration landed). **NBA (opens 10-20)** — split into ~30-minute blocks. **The board survey** on the completed history store (now a read, not a fetch). Backtests of NFL/NHL cells against validated market history. EXP-034 verdict if its job ran. |
| **50** | First looks as cells reach judged n (NFL first: 60 games ≈ late October). A **flat-stake paper ADR** for SHADOW cells — yours to accept — so evidence becomes countable paper P&L. |
| **51** | In-play arms only where C5 / ADR-0068 shows speed is measured. Sizing only for a cell that cleared its gate and its capacity question. |

What should reorder this, and what should stop it:

- **A shadow path that reaches an order, position or sizing function** stops everything shadow until fixed.
- **A dashboard that shows a number it did not read live** is a defect of the same severity — it is the operator's instrument.
- **Per cell, the pre-registered rules decide.** RULED_OUT at judged n is a completed cell.
- **If every cell in a sport is RULED_OUT at its judged n**, the next question for that sport is the information set, not more cells.
- **Board-survey stop condition — pre-registered in Wave 45, carried unchanged:** if the survey finds nothing
  CANDIDATE-PENDING-CAPACITY and no surviving multi-leg cell, Kalshi is efficient net of cost and fee at the cadence
  measured, and the off-Kalshi question opens alongside the cell work.

---

## Queued next — not yet fired

**NHL hardening** (Wave 49): verify Kalshi team codes for all 32 teams, investigate T1 abstentions, switch to `contract.py`, land the pre-registration branch unchanged. **NBA game markets** (Wave 49). **The board survey** (after the history store completes). **MLB winter disposition**
after the World Series. **Step 4 season-awareness** (GG-343..345). **PIPE-08 406s.** **T4M-PROJ and T3 disposition**
(both MISFILED). **The branch estate** (33+ unmerged). **9 aged T4 and 17 aged T1/T2 open paper positions** and the T4
resolved ledger unwritten since 09-28 (47.2's findings — 48.2 registers them). **Test-suite runtime** (10m41s full).

---

## Needs your decision

**Nothing in Wave 48 is gated on a line here.** Three deliverables *expand* if you write one.

> **AUTHORIZATION — SHADOW-EVALUATION CRON JOBS (operator, 2026-10-02 15:22 PT: "Yes permission granted").**
> Blocks may install the cron entries that run their NFL, NHL and MLB **shadow-evaluation cron jobs** for the
> T1/T2/T3 pre-game bands, plus the settlement join for those shadow ledgers. Allowed: read-only market and sports
> data reads within each block's rate cap, model evaluation, appends to shadow ledgers. Not covered: any order,
> position, fill, stake or `kelly_fraction` change; any EXISTING cron line, capture window or service; the
> settlement/depth capture writers, the NFL pre-kickoff capture and the price archiver. Dry-run first; commit the
> lines in the same commit that is installed; verify from the live crontab and the first scheduled firing.

> **AUTHORIZATION — LIVE TERMINAL DEPLOY AND RESTART (operator, 2026-10-02 15:44 PT: *"I need this dashboard updated
> as the bot continues to get updated"*).** Standing. Any block that changes the dashboards may deploy and restart
> **`pmbot-web-dashboard` only**: suite green; VPS `HEAD..origin/main` pasted and runtime files reachable from `t4-mlb`
> or a cron job confirmed additive before pulling; restart; verify `/`, `/api/data` and `process.sha` from the
> RUNNING process. Not covered: restarting `t4-mlb` or any other service, any cron change, any order or sizing.

| Item | Plain English | What it costs while it waits |
|---|---|---|
| **NEW — detached read-only VPS jobs** | Long *read-only* work (the history back-capture, EXP-034's sampler) runs unattended on the VPS through `scripts/vps_job.py` instead of in a terminal: no cron, no orders, rate-capped, logged, stoppable. A line naming *detached read-only VPS jobs* lets 48.2 launch them. | The board survey and NFL/NHL market backtests stay blocked on a store no window can finish inside two hours. |
| **NEW — T1 MLB postseason flag** | Adds `--include-postseason` to the **existing** T1 MLB cron line so the player-hits run sees playoff games (0 players matched since 9-27). An edit to an existing cron line, so the shadow authorization does not cover it. | T1 stays blind for the rest of the playoffs. |
| **NEW — EXP-034 (non-sports control arm)** | Its corrected run needs a ≥2.5-hour live sampler. Run it as a VPS job, or **park** it while the sports cells fly? Window's recommendation: **park** — Gate 2 already validated candles, and the sports cells are the priority. | Nothing urgent either way. |
| **ADR-0070** | Model-class deviation from ADR-0004 (probit-Platt for NFL/MLB; NHL's bivariate Poisson is the same question). Shadow-only today; acceptance needed before any of these models touches a paper stake. | Nothing until Wave 50's flat-stake question. |
| **Who restarted t4-mlb?** | Unattributed manual restarts on 10-1 and 10-2 (GG-347/348). If it was you or a session you ran, that closes it. | An unexplained actor on the one live service. |
| **MLB winter** | After the World Series: stand T1/T4 MLB down, or let them idle all winter? | Daily false alarms in Step 4 until spring. |
| **Settlement + depth capture schedules · Polymarket KYC · odds feed · provenance allowlist · APR-0035 · ADR-0068 · ADR-0067 · 39.3 triage · ADR-0063/0064/0065/0066 · APR-0034/0036** | Unchanged. | — |

---

## DO NOT — standing

- **Never bypass, disable, or work around a permission control.** Record the exact command and the exact refusal text, then hand back. Absolute; no operator approval in a block overrides it — an approval authorizes a CHANGE, never a bypass.
- **Submit no order against the production Kalshi account or with real funds. Demo only, always.**
- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- Promote `assert_ledger_invariants.py` to `--strict`.
- Repair or backfill a DERIVED field without establishing provenance first (GG-228). Re-capturing a raw source from its own upstream is a different act — say which one you are doing.
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport, band or market family on one finding — and do not assume the rest of the board behaves like the cells that happened to be measurable.
- Modify or re-time an existing price-capture window. Additive sibling writers only.
- Rotate, truncate or clear a VPS log or journal.
- Restart a production service without a scoped, written authorization.
- Add a cron entry without explicit operator authorization, including for read-only capture writers.
- Pre-assign T-/GG-/ADR- numbers. Claim at run time; verify uniqueness across `git log --all`; **re-verify after any release or retry** (GG-322).
- Report a live fix RESOLVED without proving the RUNNING process contains it, not the file on disk.
- Manufacture a position, a row, a cohort member, a price, a fill, or a final score.
- Assume a fill the data cannot evidence.
- Revive `exchange_index` propagation — T-558 tested and disproved it.
- Delete, truncate or rewrite a live pool file. Work on copies.
- Weaken a predicate, or widen an allowlist without citation, to raise a count.
- Modify `p_hits_gte_threshold` — 1,694 rows' provenance citation rests on its source hash.
