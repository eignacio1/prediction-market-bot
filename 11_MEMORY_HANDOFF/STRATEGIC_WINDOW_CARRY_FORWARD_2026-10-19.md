# Strategic Window — Carry Forward

**Written:** 2026-10-19 (evening PT), at the close of the window that ran **Waves 61 → 80** (2026-10-08 → 10-19), plus the
pseudo-waves 80P and 80R and one-off blocks AP and 71.H1. Verified against `origin/main` at the handoff commit (GitHub REST +
tracked files + the box, read through the box bridge). Every figure in §4 was derived by running a command at write time; treat
each as a claim to re-verify.
**Previous version** (Waves 52 → 60): `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-10-08.md`.
**Handoff procedure:** `.claude/commands/strategic-handoff.md` (`/strategic-handoff`). Run it at your own handoff.
**This window was compacted once mid-way;** everything below is rebuilt from the repo (DECISION_LOG, handoffs, the error log,
box-bridge results), not from memory.

> The operating context for the strategic window: how the operator works, the traps, state at handoff, open decisions, and
> what this window got wrong. Read `04_EXECUTION/WINDOW_ERROR_LOG.md` BEFORE this file (ADR-0074).

---

## 0. North star

**CLAUDE.md § "What winning looks like — the operator's north star (four pillars)"** — never restated here. The distance table at
handoff (box, 2026-10-20 01:37Z) is the first table of the RUNNING SITREP in `04_EXECUTION/ACTIVE_QUEUE.md`. In one line each:
BREADTH 40/107 cells logging · DEPTH: NFL engine scaffold + 6/8 components, NBA event store + 3/8, 13 factors applied across
both, none REAL-NOT-PRICED · EXECUTION: fills still lose (T4 −$0.21/fill, fills win 25% vs non-fills 48%); the forward test has
thousands of orders and has not been read · PROOF: 0 cells at a scored look; next look NFL ~2026-11-02.

The doctrines this window added, in the operator's words (read them in full where they live; never compress them, W16):
- **The scale (ADR-0073, 10-13):** one deep engine per sport at Syndicate32-level granularity, pricing the whole board. `/vision`.
- **Edge = the betting architecture (ADR-0075, 10-14):** "data aggregation > data interpretation > data application ... cool
  info, so what?" across eight components; measured by D5.
- **The granularity index (10-16):** `02_ARCHITECTURE_DESIGN/GRANULARITY_INDEX.md`. An entry = the split, the rank against
  history at the same point in a season, the matchup cross, the market map, the application. His examples ("701st out of 701";
  the loaded/light-box run game) are illustrations, never build lists.
- **Retail flow first (10-16 08:18 PT):** "Beating Kalshi or institutions is a tall task - beating buddy off his phone placing
  parlays, that's the first step." With 77.2b: no new NFL game-market factor without a "thinner edge expected" pre-registration.

---

## 1. The role

The strategic window **directs; terminals execute.** It derives state from `origin/main`, GitHub and the box (never from a
terminal's prose or from recollection), writes paste-in blocks into `04_EXECUTION/ACTIVE_QUEUE.md`, verifies each finished block
against GitHub when the operator says it is done, keeps the RUNNING SITREP and its distance table current, and routes findings,
verdicts and decisions to him. **Never hand him commands to run.** Sandbox / paper / demo actions are plumbing — handle them.
**Only real capital is his.** Short, blunt answers; candor about pace and strategic error.

**Executors.** Local Claude Code terminals on his Mac (three by default, plus the standing gap-agent tab). When he says so, a
whole wave runs as a **pseudo-wave** in one Claude Code cloud session (one prompt, tasks in order, each pushed before the next;
it reaches the box only through the box bridge and the web only through the environment's allowed domains, which now include
`api.elections.kalshi.com`). **This window** runs in a cloud container with its own clone (`/home/claude/prediction-market-bot`),
pushes docs-only commits to main, opens/merges small PRs by REST, dispatches `deploy.yml`, and reads/acts on the box through the
box bridge.

**The box bridge (80R, #283-#285, #296):** push a file `04_EXECUTION/BOX_TASKS/requests/<UTC>_<x>_<task>.toml` with
`task = "<name>"` and `note = "..."`; the `box_tasks.yml` workflow runs ONLY the named command from the allowlist in
`scripts/box_tasks.py` over ssh and commits `04_EXECUTION/BOX_TASKS/results/<same>.md`. Read tasks: `budget_read`,
`silent_arms_read`, `deploy_truth_read`, `capture_readback`, `thin_depth_stats`, `nba_opening_preflight`, `distance_read`.
Act tasks: `capture_install` (refuses unless the budget is GREEN), `capture_uninstall`. New tasks land by PR. No free-form shell.

---

## 2. Protocols (operator — follow exactly)

Carried from earlier windows (still in force):
- **Load ACTIVE_QUEUE.md as a file card every time it changes.** Never point him at a folder.
- **Wave blocks and add-ins live in the queue only, never pasted in the chat** (10-14 22:12 PT).
- **RUNNING SITREP** at the top of the queue, kept at every wave close, spanning windows; it opens with the DISTANCE TO
  OPTIMUM table, recomputed every wave close from the generator (box values via `distance_read`) — W23 is what skipping costs.
- **MEDIUM blocks:** two parts, ~60 min target, 90 min hard ceiling; each part pushed and recorded before the next.
- **Three blocks per wave by default; more only when he asks** (10-16 06:51 PT: "3 block structure is easily the most
  efficient and can get a lot done if the blocks are prompted correctly"). The gap agent is not counted. Disjoint surfaces;
  every wave carries **Pushback / Surface / Dependencies** lines and every block a **PURPOSE** line (Hard Rules 12, 15).
- **Waves are sequential, never preset** (10-15 22:30 PT: "don't pre-determine what the next waves are going to be - we are
  committed to sequential processing as necessary"). Only fixed dates go in the arc.
- **No timing-bound blocks.** Every prompt ends with the END OF BLOCK line. ASCII inside fences. Common rules atop each fence.
- **Authorizations are blockquote lines** in "Needs your decision". A table row or a terminal's DECISION_LOG line is not one.
- **Never request delete permission; never sync his folder.**
- **$0 on GitHub and paid services** (10-10). The repo **stays public for now** (10-15 22:28 PT).
- **Expansion directive** (10-08: "we're trying to win"): more pre-registered arms, real demo fills. Pre-registration before
  a cell's first row never loosens; no score below judged n; no real capital; kelly 0.
- **Handoff only after the last wave is verified**; the handoff delivers the carry-forward, the paste-in and the queue as file
  cards plus the paste-in in a fence, unasked.

Added by this window:
- **Purpose before work** (10-09: "perfection isn't a dream, it's a protocol"): Hard Rule 12.
- **Process integrity (ADR-0074, 10-14):** runtime registry (CI-enforced), pattern sweep (Hard Rule 13), no new running
  component while a health signal is red (Hard Rule 14), the window logs its own mistakes the moment it learns of them in
  `WINDOW_ERROR_LOG.md` (Hard Rule 15).
- **Edge is the architecture (ADR-0075)** and **the granularity index** — every factor reports its stage and its five parts.
- **Examples are illustrations, not specs** (Cover 6, 10-14; Bo Nix, 10-16). Quote his words into canonical docs (W16).
- **Do not restate "the models don't beat the market"** in sitreps (10-12; repeated 10-16: "yeah I fucking get it ... we don't
  have a single substantive band built out yet - but we do have the architecture"). Report what moved.
- **Retail flow first; thinner markets** (10-16) — above.
- **MLB becomes the look-back corpus after the World Series; NBA is the engine's speed lane** (10-14).
- **Deep PAM tier** (10-15): QBs, WRs, RBs, TEs, OL and core defenders even foundationally — "We don't need to get to that
  anytime soon anyway." Multi-layer, his and Claude's.
- **The governance gap agent** (10-15): a standing tab beside every wave (`/loop /gap`, procedure in
  `.claude/commands/gap-agent.md`; launch line in the queue's STANDING GA section reads it from origin/main). It owns the
  cadence the lapsed GG-074 review lost, incl. doc staleness (GG-970).
- **Muse is the tactical operator for aggregation** under `02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/PARTNERSHIP_CHARTER.md` v2
  (10-19): Muse brings the split and the rank; the bot does the cross, the market map and the application; tickets go in
  `TO_MUSE.md` (R-NNN); nothing Muse reports feeds a model until the bot recomputes it (VERIFIED). The window is the watchdog at
  every wave close. Copy in the claude.ai project: `claude/MUSE_PARTNERSHIP_CHARTER_v2.md`.
- **When he says "no terminal work for now"** (10-16), write pseudo-waves for the Claude Code cloud side; box steps go through
  the bridge; anything unreachable is recorded PENDING for the window, never handed to him.

---

## 3. Traps

Carried: deploy rule (#158, GG-432: a push restarts t4-mlb only on a changed import AND no live MLB game) · statsapi 406s the
VPS (MLB data via GitHub Actions) · `SESSION_CLAIMS.md`/`.last_session_checkpoint` make PRs dirty (merge origin/main in) ·
concurrent GG-number collisions (claim at run time) · VPS RAM (GG-477): new cron minutes avoid other jobs' minutes ·
shadow-cron authorization covers NEW lines only · "logged" ≠ "flagged on the row" · "submitted" ≠ "filled" · a handoff's prose is
a claim · GitHub GraphQL is blocked in cloud sessions (use REST `gh api`).

New this window:
- **The box pulls on its own timer.** A bridge request pushed right after a merge can run the OLD code (80R: the capture
  reinstalled the old schedule twice). Read `deploy_truth_read`'s box HEAD first; retry after the pull.
- **The cloud proxy refuses** branch deletes, tag creation and repository-settings writes (79.4 ran on a terminal). REST PR
  create/merge and `deploy.yml` dispatch DO work; a dispatch's GG-432 policy restarts t4-mlb only when no MLB game is live.
- **The auto-mode safety check times out sometimes.** Retry in the same turn; file writes via the Write tool still work; never
  leave a wave unpushed and never send a stand-in to the operator unless the push is truly stuck (W19).
- **Merge only on a read CI result** (80.1 merged #291 red, main broke, #292 repaired it).
- **Kalshi keeps no historical order book.** Depth exists only from the capture's forward snapshots. The capture now windows on
  event time; before W80.1 it windowed on `close_time`, which trails the game by ~45 h, so the 10-16..19 books are IN-GAME only.
- **Python 3.9 on the box rejects Kalshi's 5-digit fractional ISO timestamps** — use the tolerant `parse_ts` (80.2 sweep found
  3 sites; a full `src/` sweep was not done).
- **The distance generator has three broken inputs** (handoff finding): D1 errors on the NBA points models' features
  (manifest); D4 says NBA "none" because `ARCHITECTURE_COMPONENTS.toml [[engine]]` was not updated after W79.3; P3's modal
  outcome is unavailable because `12_EXPLORATORY/NFL_FIRST_LOOK_EXPECTATIONS.md` is missing or unparseable on the box.
- **The forward-test report prints two unlabeled rows per sport** — control vs treatment cannot be read off the line. The
  code keys rows (book, sport, arm) and "control" sorts before "treatment", and the 10-14 read ("first settled fills NHL:
  control 29 vs treatment 1") matches first = control — so the 10-19 line most likely reads NFL control 2,816 fills of 5,138
  (s−p +0.01) vs treatment 1,000 of 6,236 (s−p +0.20), NHL control 618/1,364 (+0.08) vs treatment 82/1,428 (+0.35): the
  treatment fills far less and its fills look better. **That is an inference; label the report and confirm before any read.**
- **His terminals start in his local folder, which may lack commands added since its last sync** — launch lines read
  procedures with `git show origin/main:<path>` (W20).
- **Terminals record "operator accepted" in DECISION_LOG** (80.1, KXNFLPASSYDS). Confirm with him and record the blockquote
  authorization in the queue before anything logs against a pre-registration.

---

## 4. State at handoff (derived 2026-10-20 ~01:45Z)

| Fact | Value |
|---|---|
| origin/main | the handoff commit (window, 2026-10-20); last block commit `b7100315` (W80.1 close) |
| Highest GG / T / ADR / EXP | **GG-971** registered (claims reached GG-974) · **T-1032** · **ADR-0075** · **EXP-040** |
| Gap log | **195 OPEN** · parity 228 headers = 228 status lines · no duplicate ids (live + archive) |
| Gap agent | last tick **2026-10-16 02:00Z** — not running since; GA-2 and GA-3 never launched |
| Runtime | **75 live components**, 0 unreviewed, 10 no-alarm (each with a reason) · SURFACE BUDGET **GREEN** (box, 00:05Z) |
| Registry | **107 cells, 40 logging** (generator as of 10-13; NBA game cells flip on 10-20/21: 9 of 12 is the ceiling, GG-891) |
| Capital | **$0 real.** kelly 0.0 everywhere. Demo account topped up to **$19,635** (10-15); data before 2026-10-16T05:40Z is cash-starved |
| Books | T4M-PROJ (ACTIVE, flat demo stakes): 177 fills / 4,316, −$0.21/fill · T1 MLB: 85 / 485, −$1.50/fill |
| Forward test (ADR-0072) | ON since 10-13 23:58Z; report 10-19 11:25Z: NFL rows 5,138/2,816 and 6,236/1,000 · NHL 1,364/618 and 1,428/82 · MLB 107/8, 452/77 · NBA 242/40, 244/16 · turn-off none tripped |
| Shadow arms | NFL 12 (EXP-037, first look ~11-02) + NFL QB challenger · NHL 9 · MLB postseason 12 · NBA 12 (EXP-038) + points EXP-039 + EXP-040 challenger · **thin-market KXNFLPASSYDS T1 (THIN_MARKET_PREREGISTRATION_2026-10-20, frozen; acceptance to confirm)** |
| Thin-market capture | live, hourly at :51, event-time windowed, 743 markets listed at the fix; 500 books/run cap (243 backlog/run); books 10-16..19 in-game only |
| Engines | NFL: 27-season play-level store (1999–2026, PIT contract), whole-board simulation (parity, not better), granularity machine (#290). NBA: event store 2016–2026 on main + box (#278/#280), 13 factor classes mapped, pace/efficiency + rest interpreted, pace applied (REAL-AND-PRICED) |
| Docs | `00_ADMIN/DOC_REGISTRY.toml` 83 entries, staleness alarm in the governance scan; 9 of ~54 LIVING docs verified (GG-970) |
| Muse archive | `eignacio1/sports-intel-archive` (private): 34 commits, 2,059 claims, schema v1.1; Muse was on ice 10-15 → 10-19; R-004..R-007 open. Attach it read-only (add_repo) to watch it |
| Open PRs / branches | #149 only (stale, kept: its files are not on main) · ~34 remote branches; auto-delete on merge ON; 36 `archive/*` tags |
| In flight | **Nothing.** Wave 80 closed (80.2 Part A waits for the 10-20 games). Wave 81 is yours to write |

---

## 5. Where the arc is, and what Wave 81 should be

**Arc of Waves 61–80.** 61–67: expansion and the north star (distance table, PURPOSE lines, NBA arms, the forward test).
68–72: execution plumbing (cancel/shard fix, forward test re-armed, ledger safety, deploy truth, /vps retired). 73: the NFL engine
(play store + simulation). 74–75: process integrity (ADR-0074) and the betting architecture (ADR-0075: PAM core, seats, tensions,
D4/D5). 76–77: ledger integrity, kill switch drilled, the runtime map; four NFL game-market factors tested against the market —
all priced or invisible. 78–80: thinner markets (history, ranking, capture, first pre-registration), the NBA engine, the
granularity index, the box bridge, docs and branches cleaned.

**Fixed dates:** NBA opening night **10-20** (read-back 10-21) · NFL first look **~11-02** · World Series end → MLB final read
(`scripts/` one-shot from W80P.4, `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/MLB_2026_SEASON_LOOKBACK.md`) · GG-529 EXP-038 second
look must be defined before January.

**Wave 81 candidates (judgment, priority order — sequential, so let 81's results set 82):**
1. **Read the forward test (ADR-0072) — the only live EXECUTION measurement.** Label control vs treatment in the report, then
   score it exactly as pre-registered. NFL rows are past the ~550-fill judged n; fills cluster in a few correlated games
   (GG-624), so the unit of n matters — read the pre-registration before counting.
2. **NBA opening-night read-back** (80.2 Part A): flips, registry, T2/T3 rows, points cells, silent arms; close GG-570/890/891/892.
3. **KXNFLPASSYDS:** confirm his acceptance (§6), then the 30-minute pre-kickoff snapshot line (new shadow line, registry first)
   and logging; read pre-kickoff depth after the next NFL weekend.
4. **Generator and report repairs (PLUMBING, small):** D1 manifest (NBA points), D4 NBA engine entry, the P3 expectations file
   on the box, forward-report arm labels; plus the full `src/` sweep for the ISO-timestamp defect.
5. **Depth lane (one block every wave, ADR-0073):** the next index entries with all five parts — the light-box stuffed-rate
   trait on team rushing yards (80.3's pending line); NBA crosses not single traits (NBA-T7: rest × pace, lineup on/off;
   KXNBAPTS shows a lineup-window move 0.030 vs placebo 0.000, the first lead).
6. **Relaunch the gap agent** (GA-4) and give it GG-970 (verify the ~45 LIVING docs left blank).
7. **Muse:** watch R-006/R-007 answers; verify the two Bo Nix `index_fact` records by recomputing them; then the archive adapter.

---

## 6. Open operator decisions

| Item | State |
|---|---|
| **KXNFLPASSYDS thin-market pre-registration** | 80.1 froze it; a terminal wrote "Operator accepted" into DECISION_LOG (2026-10-20) but the file header still says NOT ACCEPTED and no blockquote authorization exists. **Confirm with him first**, then record the blockquote and update the header. |
| Muse charter v2 | In force (his direction, 10-19). Whether he pasted `MUSE_PASTE_IN_v2.md` into Muse is unconfirmed — watch STATUS.md for R-006. |
| L3 for the archive; new sports in the archive | His (charter v2 §9). |
| MLB winter | After the World Series: T1/T4 MLB idle; MLB becomes the look-back corpus (decided 10-14); the final read runs once. |
| GG-529 EXP-038 second look | Define the 2027-01-31 date-triggered look before January. |
| Repo visibility | Public "for now" (10-15). |
| Long-carried | GG-320 · GG-285 · GG-289 · GG-441 · GG-347 · T1 MLB postseason flag · EXP-034 · detached VPS jobs · Polymarket KYC · odds feed · APR-0035 · ADR-0063..0068 · APR-0034/0036. |

---

## 7. What this window got wrong

`04_EXECUTION/WINDOW_ERROR_LOG.md` is authoritative: **W1–W24** are this window's. Patterns: UNVERIFIED 8 (the one to fear:
asserting from a document, a log line or a plan instead of reading the thing — e.g. W24, "Sunday's NFL books are in" when they
were in-game only), NOTES 3, PROCESS 2, COLLISION 2, NO-PUSHBACK 2, and one each of LITERAL (Cover 6 as a spec), PRESET
(Waves 78-80 drafted ahead), REPEAT (restating the headline he knows), REDUCED (compressing "edge" into a slogan), SCOPE,
ESCALATED, and **FOREST (W23: the distance table not recomputed for ~13 wave closes; the gap agent's silence not flagged)**.

---

## 8. Standing DO NOT

- Never bypass, disable or work around a permission control. Record the command and refusal, hand back.
- No order against the production Kalshi account or with real funds. Demo only, always. No sizing / kelly change without an ADR.
- No scoring below judged n; never relabel a verdict or change a pre-registered parameter after seeing results.
- No live-ledger write without backup + dry-run diff. No edit of an existing cron line without his written line.
- No hand-pulls on the VPS; no manufactured rows, prices, fills or scores. No free-form shell through the box bridge.
- No new running component while a health signal is red (Hard Rule 14). Merge only on a read, green CI result.
- Pre-assign no T-/GG-/ADR- numbers. Never paste wave blocks into the chat. Never preset future waves.
- Never write the archive; never treat a REPORTED archive fact as a fact. No secrets in any repo, file or message.

---

## 9. First actions for the incoming window

1. Read `04_EXECUTION/WINDOW_ERROR_LOG.md` and name, in your first message, the pattern you are most at risk of repeating
   (this window would say UNVERIFIED, then FOREST).
2. `git fetch`; derive state (SHA, max GG/T/ADR/EXP, OPEN count + parity, surface) and run `distance_read` through the box
   bridge; diff against §4 and report drift in one short list.
3. Read ACTIVE_QUEUE.md top to bottom (sitrep, NOW, STANDING GA, Needs your decision). Load it as a file card. Attach
   `eignacio1/sports-intel-archive` read-only and check Muse's STATUS.md for R-006/R-007.
4. Short sitrep to him; confirm the KXNFLPASSYDS acceptance (§6); then write Wave 81 (three MEDIUM blocks) into the queue with the
   prompts inside, and load the queue again.
5. At your own handoff: `/strategic-handoff`.
