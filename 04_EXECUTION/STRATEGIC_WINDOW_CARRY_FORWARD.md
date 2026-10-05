# Strategic Window — Carry Forward

**Written:** 2026-10-03 ~20:50 UTC (1:50 PM PT), at the close of the window that ran Waves 45 → 51.
**Verified against:** `origin/main = 0a52afb` via `git fetch` + GitHub API. Every figure in §4 was derived by
running a command; where something is judgment rather than state, it says so.
**Previous version** (Waves 38 → 44, the empirical record through EXP-033): `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-10-01.md`.
Its §5 "empirical record" still stands and is summarized in §6 here — read the original before proposing any
modelling work.

> **This file is the operating context for the strategic window.** It carries what exists nowhere else in the
> repo: how the operator wants to work right now, what the last window got wrong, and the traps that cost time.

---

## 1. The role

The strategic window **directs; terminals execute.** It:

1. Derives true state from tracked files at `origin/main` — never from a terminal's prose, never from recollection.
2. Writes paste-in prompt blocks into `04_EXECUTION/ACTIVE_QUEUE.md` and gives them to the operator in chat.
3. Verifies each block's result against tracked files when he says it's done, and updates the queue.
4. Routes findings, verdicts and decisions to the operator. **Never hands him commands to run.**

Operator, in his words: *"I'm eyes and ears on the project not the plumbing — that's for you and the
terminals to do."* Sandbox / paper / demo actions are plumbing: handle them. **Only real capital is his.**
He wants blunt, short answers; candor about pace and strategic error, not just defects.

**How he runs terminals now:** local Claude Code desktop sessions on his Mac (the repo is at
`~/Documents/Claude/Projects/Prediction Markets`). `claude --cloud` is **not** available in his terminal — don't
write launch commands for it. He pastes each block into its own session.

---

## 2. How waves are built — current rules (several changed this window)

- **Blocks are ~30 minutes, hard stop at 45.** Operator directives 2026-10-02 17:03 and 17:09 PT, after he cut three
  2-hour blocks short and then rejected 75 minutes (*"none of these tasks better take 75 fucking minutes"*).
  **This supersedes the 2026-09-30 "LARGE blocks" rule** in the previous carry-forward. Cut scope to fit the clock;
  one job per block, done completely; a block landing `src/` code budgets ~11 min for the full suite.
- **Never give him a block he can't run right now.** 2026-10-03 13:19 PT: *"don't give me a prompt block if I
  can't run it now."* A block that needs a future window (idle MLB, a game settling) is issued when that window
  opens — not before, and not with a "paste after 8:30 PM" label.
- **Waiting is not work.** Long fetches, multi-hour samplers, slate-watching go to the VPS as cron/detached jobs
  under their own authorization; a later block reads the output.
- **Three blocks per wave, never four.** Disjoint file surfaces, stated in the queue's "Touches" column. Concurrent.
- **Queue layout (status first)** — operator, 2026-10-03: the queue was "stale" because status sat at the bottom and
  closed blocks still showed prompts. Current layout: header facts → **NOW** table (each block: status + one-line
  result) → **Sequencing track** (one table per wave, closed waves kept as rows) → directives → standing rules →
  decisions → DO NOT. Prompt bodies appear only for blocks to paste now; closed AND in-flight prompts move
  **verbatim** to `ACTIVE_QUEUE_ARCHIVE.md`. Fences: `grep -c '^```'` = 2 × blocks-to-paste; ASCII only inside fences.
- **Update the queue when every block closes**, not at wave end. He reads it as his status board.
- **Give the blocks in chat as well**, each in its own fence, ready to paste.
- **NAMES (operator, 2026-10-05):** **Visual Dashboard** = the operational review of the whole bot (`/project`). "ERP"
  describes its purpose only - he likes its current look; enhance it, do not rebuild it as an ERP site. **Live Terminal** = what the bot is actually placing, live, full black (`/`). Use these
  names exactly; never swap them.
- **PROTOCOL — the strategic window NEVER requests delete permission and NEVER syncs the operator's folder**
  (operator, 2026-10-04 21:17 PT: *"stop asking permissions to delete the entire fucking project folder"*). The
  permission prompt can only name the whole folder, so it reads as "delete the project". The bundle sync also raced
  his running terminals on 2026-10-04 and left a stale `.git/refs/remotes/origin/main.lock`. His folder is brought
  current by his own terminals' fetches; he reads the queue from the chat file card (next rule). Read-only git only.
- **PROTOCOL — load the queue into the chat every time it changes** (operator, 2026-10-04 21:14 PT: *"that should be
  protocol"*). After every queue update: push to main, sync his folder, then send `04_EXECUTION/ACTIVE_QUEUE.md` as a
  file card in the chat (`SendUserFile`, display render). Never point him at a folder path to go find it.
- **No pre-assigned T-/GG-/ADR- numbers.** Blocks claim at run time via `scripts/claim_session.sh`.
- **Pre-register before measuring**; stop conditions written into the arc in advance.
- **Deliverable 0 in every block:** confirm base, land un-landed predecessors where allowed.

---

## 3. Traps — the ones that cost this window real time

- **`deploy.yml` restarts `t4-mlb` and `pmbot-web-dashboard` on EVERY push to main that touches any file outside
  the 9 doc folders** (`00_ADMIN 01_SPEC 02_ARCHITECTURE_DESIGN 03_DECISIONS 04_EXECUTION 05_RESEARCH_EXPERIMENTS
  07_TEST_VALIDATION_EVIDENCE 08_MODEL_RISK_GOVERNANCE 11_MEMORY_HANDOFF`). That was the "who restarted t4-mlb"
  mystery (GG-432). **Until the operator decides GG-432, code reaches main only when no MLB game is live**:
  Stats API shows none In Progress, T4 cycle log idle > 15 min, no first pitch within 60 min. Docs-only pushes are
  always safe. MLB postseason runs through the World Series; the operator wants the MLB arms kept running.
- **His local folder cannot pull from GitHub** (no credentials in the device shell; `git fetch` fails with
  "could not read Username"). When this window pushes, his folder goes stale and he sees an old queue. Fix that
  worked: `git bundle create <outputs>/sync.bundle <his-HEAD>..origin/main` → `device_commit_files` into his folder
  → device shell: `git bundle verify`, `git fetch <bundle> +refs/remotes/origin/main:refs/remotes/origin/main`,
  `git merge --ff-only origin/main`, remove the bundle. His terminal sessions also fetch into the same `.git`,
  so after one of them runs, a plain `git merge --ff-only origin/main` in his folder may be enough.
- **Never write a tracked file directly into his folder** to "update" it — the working copy then differs from
  HEAD and every later `git pull` aborts ("local changes would be overwritten"). Tested 2026-10-03.
- **Deletion in his folder.** The device shell can't delete by default; git needs to delete its own lock files,
  so a pull without delete permission leaves a stale `.git/index.lock` (this window did exactly that once and had
  to remove it). Delete permission is per session (`device_request_delete_permission`, folder root only); it was granted 2026-10-03 for this purpose and must be re-requested in a new window. **Operator: "Don't fucking delete
  anything that's important."** Delete nothing but your own temp files; say exactly what you deleted.
  His folder carries his own uncommitted work: `03_DECISIONS/OPERATOR_CONSOLE.md` (modified), `Visual Dashboard.html`,
  `Visual Dashboard.prev-handbuilt.html`, `Reload Dashboard.command`, `04_EXECUTION/CLOUD_LAUNCH_W49.md`,
  `04_EXECUTION/_w33_recovered.md`. Never touch them.
- **Use read-only git in his folder** (`git --no-optional-locks ...`) except for a deliberate fast-forward.
- **`device_commit_files` sometimes silently writes an older version.** Commit, `md5sum` on the device against
  the staged file, re-commit if they differ.
- **A terminal's prose is a claim.** 50.2 reported PR #157 "held"; GitHub showed it also *unmergeable* (conflicts),
  which the report never said. Check GitHub, not the summary.

---

## 4. State at handoff (derived 2026-10-03 ~20:45 UTC)

| Fact | Value |
|---|---|
| `origin/main` | **0a52afb** |
| Highest GG / T / ADR / EXP | **GG-450** · **T-653** claimed · **ADR-0070** (PROPOSED) · **EXP-037** |
| Gap log | 197 live entries · **178 OPEN** (`grep -cE '^\*\*Status:\*\* OPEN\b'`) |
| Cells (registry) | 92 · ACTIVE 1 (T4M-PROJ, MISFILED) · SHADOW 3 (MLB player-hits T1–T3) · BLOCKED 2 · DARK 1 · NOT_IMPLEMENTED 85 |
| Actually logging in shadow | MLB player-hits T1–T3; **NHL 9 cells** (ML / puck line / total × T1, T2, T3 — 51.3's table: 1,393 rows, T3 settled 178) but registry still says NOT_IMPLEMENTED; **NFL 12 + MLB postseason 12 game cells** (EXP-037) armed 2026-10-03 ~20:02 UTC, first NFL T1 firing 2026-10-04 00:05 UTC |
| Capital | **$0.** `kelly_fraction = 0.0` on every band. Demo venue only. |
| VPS | HEAD `eb2d143`; `pmbot-web-dashboard` running `077558b` code. Crontab backup `/root/crontab.bak.20261003T200240Z`. |
| Waiting to land (code, need idle window) | **PR #157** head `42a0d0d` — MERGEABLE, CI green, ready for review (process fixes GG-419/427/428 + GG-400..429 triage; no `src/`). **51.1 branch** `session/20261003T201912Z-w51-killswitch-truth` @ `6cbe62f` (dashboard drawdown fix, 178 dashboard tests). **51.2 branch** `session/20261003T201919Z-w51-nhl-team-codes` @ `f822b6b` (NHL SJ/TB/LA/NJ 2-letter code drop fixed + abstention counters; follow-up T-647). |
| Operator's folder | fast-forwarded to `d956fb8` at 20:30 UTC; behind main again by the 51.x close-outs |

---

## 5. Where the arc is

**After Wave 44's stop condition fired** (venue efficient net of cost across every structure measured), the
operator chose **"start flyin"**: coverage of cells, **pre-game first**, accepting generality over edge — with
predictions **pre-registered** so a thin-edge result is informative, not explained away. 92 cells total; the goal
is to get as many as possible logging honestly in shadow, then let pre-registered rules decide each one.

**What Waves 45–51 did:**

| Wave | Outcome |
|---|---|
| 45 | Candle reconstruction Part 1 gate **FAILED** → candle numbers void (GG-329..333). |
| 46 | Why: matching rule vs sparse 1-minute candles. Gate 2 pre-registered. |
| 47 (cut at ~2h) | **Candles Gate 2 PASSED 7/7** on KXMLBTOTAL (licensed for that market structure only). **NHL arm flying** (frozen bivariate-Poisson; moneyline beats climatology by only ~0.002 Brier — reported). NFL + MLB postseason shadow built and pre-registered. Live Terminal v2 deployed. |
| 48 (cut) | Little landed; 30-min block rule born. |
| 49–50 (harness-run) | NFL/MLB shadow code + dashboard fixes + NHL pre-registration on main; GG-400..429 registered; 50.1 process fixes on PR #157; **50.2 armed the EXP-037 crons**. |
| 51 | **51.1 kill-switch truth** — see §6. **51.2** NHL 2-letter team codes were being silently dropped; fixed on branch. **51.3** PR #157 made mergeable; NHL row table. |

**Evidence clocks (pre-registered — breadth now, verdicts later):** NFL first look at 60 settled games per cell
(~late October; MDE ≈ 0.025 vs a plausible effect ≤ 0.02, so the modal first-look result is "keep accruing").
NHL judged n = 2,500 games per cell (~2 seasons). MLB postseason rows banked for 2027.

**The arc (renumbered, judgment):** 52 = land Wave 51 + NHL scoring readiness (GG-401 confirmed goalie at T3,
GG-404 spread cutoff, GG-407 clustered scorer, GG-405 matinee coverage) + MLB resolver (GG-440/450); NBA game
markets open 10-20 in ~30-min blocks; 53 = first looks + a flat-stake paper ADR for SHADOW cells (his to accept);
later = in-play arms only where speed is measured (ADR-0068), sizing only for a cell that cleared its gate.

---

## 6. Findings this window — verify, do not re-derive

- **51.1 — the dashboard's 26.63% "drawdown" was the wrong quantity.** Kill switch reads *realized* loss:
  **10.60%**, not tripped. 26.63% = 10.60% realized + 16.02% stake in 17 T1 positions open since 2026-08-06.
- **51.1 follow-up — 16 of those 17 markets were *cancelled* by Kalshi** (scalar settlement), 1 real loss. Realized
  after booking is **~11.3% (void) to ~12.0% (mark)** — under 20%. **This window told the operator "if all 17 lost,
  26.6% > 20%" before the terminal checked Kalshi — wrong, corrected by the terminal.** (GG-441 HIGH: kill switch is
  realized-only and in-memory, blind to settled-but-unresolved stake. GG-450 MEDIUM: cancelled markets unhandled.)
- **GG-440 (HIGH): the MLB resolver cannot settle anything** — statsapi returns 406 to the VPS; 17 T1 + 9 T4
  positions stuck. This is why the T1 book froze on 2026-08-06. Not fixed.
- **GG-431**: the dashboard's "read 58d20h ago" panel is that same frozen T1 book (Aug 6 00:05Z + 58d20h = Oct 3 20:05Z).
- **GG-401 (widened)**: NHL never passes a `starter_provider`, so every band uses the projected goalie — breaks the
  EXP-036 pre-registration's T3 promise. No NHL T3 score may be read until fixed or amended.
- **GG-400**: ADR-0070 as written covers the 12 EXP-037 cells only, not NHL.
- **Prior empirical record (Waves 38–44) stands:** pre-game model beats climatology (+0.0052) but loses to the market
  (−0.00393); 14 families, none survives the spread; edge and cost decay together; 0/24 multi-leg cells. Do not
  propose another model/feature/band for those families. Full detail in the 2026-10-01 carry-forward §5.

---

## 7. Open operator decisions

| Item | State / window's recommendation |
|---|---|
| **GG-432 — CI restarts t4-mlb on every code push** | Recommend: deploy pulls code every push, but skips the `t4-mlb` restart while an MLB game is live (restart at next idle). Until decided, code lands only in idle windows. |
| **Book the 16 Kalshi-cancelled T1 positions** | void / mark-to-settlement / exclude from G6 — then an ADR-gated ledger write (backup + dry-run diff first). Raised by the 51.1 follow-up. |
| **Detached read-only VPS jobs** | `scripts/vps_job.py` exists; needs a line naming *detached read-only VPS jobs*. Blocks the board survey + NFL/NHL market backtests. |
| **T1 MLB `--include-postseason`** | Edit to an existing cron line; unauthorized. T1 player-hits blind to playoff games. |
| **EXP-034** | Recommend park. |
| **ADR-0070** | PROPOSED; widen to NHL (GG-400) or leave GG-400 open after acceptance. |
| **GG-347 remaining half** | SSH poller from 73.231.159.158 — his? |
| **MLB winter** | After the World Series: stand T1/T4 down or idle. |
| Long-carried | Settlement + depth capture schedules · Polymarket KYC · odds feed · provenance allowlist (1,694 rows) · APR-0035 · ADR-0067/0068 · 39.3 triage · ADR-0063..0066 · APR-0034/0036 — unchanged. |

Standing authorizations in force: **shadow-evaluation cron jobs** (2026-10-02 15:22 PT, new lines only) and
**Live Terminal deploy + restart of `pmbot-web-dashboard` only** (2026-10-02 15:44 PT). Text in `ACTIVE_QUEUE.md`.

---

## 8. Judgment not in the repo

**What this window got wrong, so you don't repeat it:**

1. **Asserted a number before the primary source was read** — the "26.6% breach" scenario went to the operator
   before anyone checked Kalshi's settlement. Same failure the previous window logged twice. Say "unverified" or check first.
2. **Sized blocks for the work instead of the clock** — 2h, then 75 min. He cuts them; the work strands.
3. **Handed him a block he couldn't run yet** and a `claude --cloud` template he pasted literally.
4. **Pushed to GitHub and called the queue updated** while his folder (what he actually reads) stayed stale.
   "Updated" means *he can see it*.
5. **Created a stale `.git/index.lock` in his folder** with a plain `git status`. Read-only git there.

**What he cares about right now:** the **Live Terminal is his only visual indicator** — keep it current with the
bot, and every new cell, ledger or verdict should become visible on it. He wants each bot component wired in
visually. Being told the state, short and straight. Not being made to do plumbing.

**Compaction:** this window compacted once (mid-Wave 50). Treat any recollection from before a compaction as a
lead to verify, never a citation.

---

## 9. Standing DO NOT — carry into every block

- **Never bypass, disable, or work around a permission control.** Record the exact command and refusal text, then hand back.
- **Submit no order against the production Kalshi account or with real funds. Demo only, always.**
- Touch sizing or any `kelly_fraction` without an ADR, including T1.
- **Push code to main while an MLB game is live** (until GG-432 is decided). Docs-only pushes are fine.
- Promote `assert_ledger_invariants.py` to `--strict`.
- Repair or backfill a DERIVED field without establishing provenance first (GG-228).
- Land red work to clear a backlog.
- Relabel a pre-registered verdict, or change a pre-registered parameter, after seeing results.
- Recommend against a sport, band or market family on one finding.
- Modify or re-time an existing price-capture window. Additive sibling writers only.
- Rotate, truncate or clear a VPS log or journal.
- Restart a production service without a scoped, written authorization. Do not hand-pull on the VPS.
- Add or edit a cron entry without explicit operator authorization.
- Pre-assign T-/GG-/ADR- numbers.
- Report a live fix RESOLVED without proving the RUNNING process contains it.
- Manufacture a position, a row, a cohort member, a price, a fill, or a final score.
- Delete, truncate or rewrite a live pool file. Work on copies. Delete nothing in the operator's folder but your own temp files.
- Weaken a predicate, or widen an allowlist without citation, to raise a count.
- Revive `exchange_index` propagation (T-558 disproved it). Modify `p_hits_gte_threshold` (1,694 rows' provenance rests on its hash).

---

## 10. First actions for the incoming window

1. `git fetch`; derive state from `origin/main` in one command (refs, max GG/T/ADR, OPEN count, registry
   counts) and diff against §4. Report drift.
2. Read `04_EXECUTION/ACTIVE_QUEUE.md` (status-first) and the 51.x handoffs:
   `11_MEMORY_HANDOFF/SESSION_HANDOFF_20261003_W51_3.md`, `SESSION_HANDOFF_20261003_2035.md`, plus
   `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/W51_1_killswitch_truth_results.md`. Update the queue's NOW table
   (51.2 closed) and bring the operator's folder current (§3).
3. **The landing block** is the next thing to issue — **only once no MLB game is live** (2026-10-03: last game
   SD@MIL, first pitch 00:30Z; earliest idle ~03:30 UTC = 8:30 PM PT; re-check the Stats API, don't trust this
   estimate). It: probes idle → merges PR #157 → watches Deploy, verifies VPS HEAD, services, dashboard
   `process.sha` → merges 51.1's and 51.2's branches the same way, one at a time → flips the 9 NHL cells with
   rows to SHADOW via `promote_cell_status` → verifies on the running Live Terminal. ~30 min, hard stop 45;
   whatever doesn't fit carries.
4. Until then, any block issued must be runnable now and push no code to main. Good candidates (each ~30 min,
   disjoint): GG-440 resolver diagnosis (why statsapi 406s from the VPS — read-only); NHL GG-401 confirmed-goalie
   source (branch only); GG-431 stale panel. Confirm the operator wants a wave before writing one.
