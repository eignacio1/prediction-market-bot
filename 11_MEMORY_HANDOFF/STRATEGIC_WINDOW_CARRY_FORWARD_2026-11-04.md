# Strategic Window — Carry Forward

**Written:** 2026-11-04 (evening PT, handoff ~02:30 UTC 11-05), at the close of the window that ran **Waves 81 → 100**
(2026-10-19 → 11-04) — the longest window the operator has run in months. Verified against `origin/main` at the handoff commit
(GitHub REST, tracked files, and the box read through the box bridge at 2026-11-05 02:00Z, `04_EXECUTION/BOX_TASKS/results/20261105T020020Z_*`).
Every figure in §4 was derived by running a command at write time; treat each as a claim to re-verify.
**Previous version** (Waves 61 → 80): `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-10-19.md`.
**Handoff procedure:** `.claude/commands/strategic-handoff.md` (`/strategic-handoff`). Run it at your own handoff.
**This window was compacted several times;** everything below is rebuilt from the repo (DECISION_LOG, handoffs, the error log,
box-bridge results, Muse's archive), not from memory.

> The operating context for the strategic window: how the operator works, the traps, state at handoff, open decisions, and
> what this window got wrong. Read `04_EXECUTION/WINDOW_ERROR_LOG.md` BEFORE this file (ADR-0074), then this file, then the
> rolling backlog (`04_EXECUTION/ROLLING_BACKLOG.md`), then `04_EXECUTION/ACTIVE_QUEUE.md` top to bottom.

---

## 0. North star

**CLAUDE.md § "What winning looks like — the operator's north star (four pillars)"** — never restated here. The distance table at
handoff (box, 2026-11-05 02:00Z) is the first table of the RUNNING SITREP in `04_EXECUTION/ACTIVE_QUEUE.md`. One line each:
- **BREADTH** B1 52 / 108 cells logging · B2 17 / 19 families · B3 4 of 5 bands (no T5) · B4 2 props · 0 parlays.
- **DEPTH** D2 18 features (MLB T1, 0 qualitative) · D3 5 challengers · D4: NFL data layer + whole-board engine + frozen forward
  test (EXP-045); NBA data layer + board engine, three versions logging (EXP-044 / 044b / 044c); NHL data layer + board engine
  (Poisson, not earned); MLB none · D5(a) NFL 8/8, NBA 4/8, NHL 2/8+, MLB 3/8 (router).
- **EXECUTION** T4 MLB 177 fills / 4,316 (−$0.21/fill); fills win 25% vs non-fills 48% (resting orders get picked off); entry
  cost measured — keep the frozen rule.
- **PROOF** P1 12 / 49 · P2 12 verdicts (NFL first look 11-02: GAME_TOTAL T1 + T2 RULED_OUT, 10 KEEP ACCRUING, 0 CANDIDATE) ·
  P3 2026-11-13 (NFL QB moneyline).

The doctrines in force, in the operator's words (read them in full where they live; never compress them — W16, W29):
- **The scale (ADR-0073, 10-13):** one deep engine per sport at Syndicate32-level granularity pricing the whole board. `/vision`.
- **Edge = the betting architecture (ADR-0075, 10-14):** aggregation > interpretation > application, eight components, D5.
- **The granularity index (10-16):** `02_ARCHITECTURE_DESIGN/GRANULARITY_INDEX.md`; examples are illustrations, never specs.
- **Market-anchored pricing (10-21) — rank 1.** Price from the market's own line; the model moves it ("conviction"). Project
  memory: `areas/market-anchored-pricing.md`. EXP-041 (NFL) froze it; it added nothing on NFL, so the engines carry the weight.
- **Green means the cell WINS (10-19 22:06 PT)** — at its judged n, against the market. Not "logging".
- **G6 per (book, sport) (ADR-0076, ACCEPTED 10-27 17:30 PT):** blank limits stay blank until a positive Kelly is proposed.
- **The conceptual layer (11-02 21:40 PT):** "the raw table stats are a starting place that we'll be able to build on once we
  start hitting conceptual data aggregation, ie mid range jumper shooting archetypes during 2-4 minute close games on the road
  with your primary point guard hurt against a team that plays zone ... The interpretative data should be able to feed each
  other as each branch gets built - exponentially making each branch easier to build." Drawn on the aggregation web as each
  sport's "Compound splits" spoke.

---

## 1. The role

The strategic window **directs; terminals execute.** It derives state from `origin/main`, GitHub and the box (never from a
terminal's prose or from recollection), writes paste-in blocks into `04_EXECUTION/ACTIVE_QUEUE.md`, verifies each finished block
against GitHub when the operator says it is done, keeps the RUNNING SITREP and its distance table current, maintains the
**rolling backlog**, watches Muse, and routes findings, verdicts and decisions to him. **Never hand him commands to run.** Sandbox
/ paper / demo actions are plumbing — handle them. **Only real capital is his.** Short, blunt, plain English ("Plain fucking
english bro", 10-30) — he reads on his phone; lead with the answer.

**Executors.** Local Claude Code terminals on his Mac: **three blocks per wave by default** ("get back to 3", 11-02); more only when
he asks (Wave 89 had six, Wave 94 four + addenda, Wave 97 four). **Muse** (Meta's model, his account) is the data aggregator on
scheduled runs (§2, §4). **This window** runs in a cloud container with its own clone (`/home/claude/prediction-market-bot`),
pushes docs-only commits to main, opens / merges small PRs by REST (#412 was the window's), and reads / acts on the box through
the box bridge. It can also reach his Mac through the device bridge when the desktop app is linked (used only for the folder
refresh at handoffs).

**The box bridge:** push `04_EXECUTION/BOX_TASKS/requests/<UTC>_<x>_<task>.toml` with `task = "<name>"` and `note = "..."`; the
`box_tasks.yml` workflow runs ONLY allowlisted commands (`scripts/box_tasks.py`) and commits `.../results/<same>.md`. Requests run
in filename order. Read tasks the window uses every close: `distance_read`, `budget_read`, `silent_arms_read`, `deploy_truth_read`,
`box_memory_read`, `nba_engine_cron_readback`, `picks_sheet_read`. **Install tasks (`*_install`) are refused by the auto-mode
classifier for terminals AND the window — they run only after the operator approves the exact task by name in chat** (§2).
Output is capped at ~60 KB per result (GG-1720 family) — design read tasks to aggregate.

---

## 2. Protocols (operator — follow exactly)

Carried from earlier windows (still in force): RUNNING SITREP + DISTANCE table recomputed at EVERY wave close from `distance_read`
(W23) · waves are sequential, never preset (W21) · every wave carries **Pushback / Surface / Dependencies**, every block a
**PURPOSE** line (Hard Rules 12, 15) · END OF BLOCK line, ASCII in fences · authorizations exist only as **blockquotes** in the
queue's "Needs your decision" · $0 on GitHub and paid services · expansion directive guardrails (pre-registration before a cell's
first row, no score below judged n, no real capital, kelly 0) · don't restate "the models don't beat the market" — report what
moved · retail flow first · Muse is watched every wave close · handoff only after the last wave is verified.

Added or changed by this window (date, his words where short):
- **Delivery (10-27 22:33-22:37 PT, W35):** "UPDATE IT HERE IN THE ACTIVE QUEUE THAT I CAN CLICK AND OPEN AND COPY AND PASTE IN
  THIS DESKTOP APP." Every wave's blocks go INSIDE `ACTIVE_QUEUE.md` (NOW section, one fenced paste per block), and the file is
  sent with `SendUserFile` every time it changes. **Never paste blocks into the chat** ("don't waste my tokens") — EXCEPT when he
  asks (11-03 19:44 PT: "the file got too big so just give me the paste in this chat and remove it from the active queue").
- **Common rules file per wave:** `04_EXECUTION/WAVE_BLOCKS/COMMON_RULES_W<n>.md`; each block's first line tells the terminal
  to read it with `git show origin/main:...` and quote its first line. W100 is the latest template.
- **His Mac folder refreshes only at window-to-window handoffs** (10-27 21:46 PT), never per wave. Delete only exact items, never
  untracked files you haven't checked byte-for-byte; never leave `.git/*.lock` files ("just don't fucking break anything").
- **The ranking (10-27, agreed) — compose every wave by it:** 1 market-anchored pricing · 2 one engine per sport · 3 granularity
  index · 4 quant · 5 betting architecture · 6 PAM · 7 Muse · 8 expansion.
- **The lane rule (10-27):** every wave = one **engine** block + a **proof** block + a **flex** block; quant runs in tandem; a new
  directive takes a lane, not a whole wave. Each wave header names each block's lane and the rank it serves (W36).
- **Block size (10-30 08:38 PT, "Yes"):** three parts, ~130 minutes; Part C is something a terminal can switch to while waiting
  on the box (W37: never shrink blocks because parts stalled on waiting).
- **The rolling backlog (10-30 08:26 PT):** "a rolling backlog of tickets ... a birds eye view of what needs to be addressed and
  we can move tickets up or back accordingly dependent on my mandates or what the project needs ... it puts all blocks in scope at
  once. Ensure it gets placed in the visual dashboard." `04_EXECUTION/ROLLING_BACKLOG.json` (window-only), render with
  `python3 scripts/rolling_backlog.py` then `--check`; shown on /visual. Waves draw from its top by lane.
- **No Polymarket build work (10-27 17:31 PT):** "we're not building shit for polymarket yet". A curiosity question is not a
  directive (W31).
- **RIDE needs out-of-sample evidence (10-27 17:26 PT).** The router (`decision_trees/router.py`, `ride.py`, `ride_cells.toml`)
  fires RIDE only for HELD_OUT or FORWARD_PASSED cells; it is not wired to orders.
- **Installs (11-03):** the classifier refuses `*_install` for everyone. The window runs one only after the operator approves the
  exact task by name, e.g. "I approve the box-task request that runs t3_lock_stagger_install, which edits the crontab on the paper
  box." A general "go ahead" does not pass (11-02 22:40 PT failed). Never work around it. Hard Rule 14 still binds.
- **Frozen artifacts are his:** retiring a frozen cell is his call (11-03 19:16 PT "Yes" → EXP-042 cell 10, by addendum).
- **Muse (charter v3, `02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/PARTNERSHIP_CHARTER.md`; project copy `claude/MUSE_PARTNERSHIP_CHARTER_v3.md`):**
  - Role (11-02 21:33 PT): "we're still gonna run it as a data aggregator bc it's far from getting to the type of stats/pulls I'm
    envisioning". Every card names the engine and factor it feeds and whether the bot can capture the source itself.
  - Runs (charter §1b rule 3, 11-03): "as many daily runs as Earl schedules". Scheduled runs are on a separate ledger from his chat
    usage (11-03 18:17 PT, from his contact on the Muse team). Stretch target 200 (11-04 16:29 PT: "I want to stretch it to its
    absolute limits until they inevitably pull the curtains back"; 16:31 PT: "Sit on it for now - the next window upon handoff
    will need to operate on it") → backlog B-042.
  - **Anything Muse must ACT on goes in his message, never in a fetched file** (W42: Muse's safety check refused fetched
    instructions). TO_MUSE.md is backlog and record. Muse may read its own archive (QUEUE.md, CLAIMS.md) safely.
  - The window is Muse's watchdog every wave close; R-ticket backlog ≥ 30 open (43 at 11-02 + R-112 split queue).
- **Write plain-English summaries for him** of any result he will act on (11-02: "a whole bunch of nothing" — say the answer).

---

## 3. Traps

Carried: deploy rule (GG-432: a push restarts t4-mlb only on a changed import AND no live MLB game) · statsapi 406s the VPS ·
SESSION_CLAIMS / `.last_session_checkpoint` make PRs dirty · GG-number collisions · shadow-cron authorization covers NEW lines
only · "logged" ≠ "flagged" · "submitted" ≠ "filled" · a handoff's prose is a claim · GitHub GraphQL is blocked (use REST) ·
Kalshi keeps no historical order book · Python 3.9 on the box.

New this window:
- **Box memory is the binding constraint (961 MB, 1 core).** 142 OOM kills / 24 h on 11-03; lock + stagger on the T3 lines
  (installed 11-04 01:55Z) cut it, but 45 kills / 24 h and 223 MB free at handoff; NBA v2 / v3 missed 5 of 11 games on 11-04.
  The T1/T2 lock (#416) was installed 11-05 02:11Z on his named approval (17 of 17 lines locked); the next full night's `box_memory_read` is the test. Every new arm costs memory — Hard Rule 14 in spirit even when the budget reads GREEN.
- **The silent-arm spec alarms on zero rows, not partial coverage** — read `coverage.jsonl` (NBA engine) for missed games.
- **The box pulls main every 5 minutes** (`vps_deploy.sh` at :03/:08/...). A request pushed right after a merge can run old code;
  read `deploy_truth_read`'s box HEAD first (the window's #412 retry).
- **The install gate:** each install exempts only its own first-run reds; batches exempt only the batch's reds, each step reading
  its own conf (#405, #412). A "STALE ... no write found" red right after an install is its first-run state.
- **Box task output caps at ~60 KB** — aggregate on the box (GG-1720: the proof calendar could not be regenerated on the box).
- **A terminal's sweep can list branches that do not exist** (11-04: w89-* .. w91-*). `git ls-remote --heads origin` is the source.
- **Muse's scheduler:** recurring jobs carry `catchup=latest` — creating them fires a burst of catch-up runs (11-03: chunks claimed
  four times). Muse now creates them disabled with a one-time enabler. Removing a job does not stop a run already in flight.
- **Muse at volume:** single-table jobs never strained; multi-source / ~560-row player tables overrun one run, get reclaimed after
  6 h and redone; C-105's held pages failed a live spot-check. Conditions must be checked against the source before queueing (W40).
- **Merge only on a read CI result** — #400 merged red (fixed by #402); disclose it.
- **His Mac folder:** git there may leave `.index.lock` / `ORIG_HEAD.lock`; delete permission is per session and only for exact items.

---

## 4. State at handoff (derived 2026-11-05 ~02:30Z)

| Fact | Value |
|---|---|
| origin/main | the handoff commit (window, 2026-11-05); last block commit `07924a28` (W100.3 session close) |
| Highest GG / T / ADR / EXP | **GG-1720** · **T-1712** · **ADR-0076** · **EXP-045** (+ EXP-044b / 044c; EXP-046 NOT frozen) |
| Gap log | **250 OPEN** · parity 298 headers = 298 status lines · no duplicate ids (live + archive) |
| Box (02:00Z) | HEAD `07924a28` = main · **88 live**, 0 unreviewed, 9 no-alarm with reasons · budget **GREEN** · healthcheck HEALTHY · no silent arm · **45 OOM kills / 24 h, 223 MB free** · 30 lock skips logged |
| Capital | **$0 real.** kelly 0.0 everywhere. Kill switch ENFORCING (W89) |
| Books | T4M-PROJ (ACTIVE, flat demo): 177 fills / 4,316, −$0.21/fill · T1 MLB: 85 / 485, −$1.50/fill. MLB arms IDLE for the winter |
| Forward test (ADR-0072) | running; NFL read INCONCLUSIVE (W82), keep running; entry style: keep the frozen rule (98.2: taking at the quote costs ~0.10/contract) |
| Frozen tests | EXP-037 (NFL first look done 11-02: 2 RULED_OUT, 10 accruing) · EXP-041 (NFL market-anchored) · EXP-042 (11 ride cells, **cell 10 RETIRED** 11-04; looks ~12-21) · EXP-043 (ladder ride) · EXP-044 / 044b / 044c (NBA engine v1 / v2 / v3, logging) · EXP-045 (NFL engine vs Kalshi ladders, look **2027-01-12**) |
| Engines | NFL: 27-season play store, board engine, priced from the line, 8/8 components. NBA: event store (refresh 12:33Z + 15:46Z), board engine v1 / v2 / v3 (v3 = availability + lineups known before tip). NHL: shot store, Poisson board engine v2 + `model_pit.py` (bias −0.080 → −0.059), trails Kalshi at n 33. MLB: none (spring) |
| Picks sheet | live since 11-04 03:30Z (`scripts/build_picks_sheet.py`, 05:37Z + 22:37Z); night 1: 134 games, 2,614 picks, reasons on 90%; panel "Tonight's picks" on /visual; GG-1690 (duplicate presentation) |
| Rolling backlog | 29 tickets (as of 02:30Z): NOW B-027 (T1/T2 lock install), B-030, B-001, B-039, B-026 · NEXT B-041, B-042, B-029, B-043, B-008, B-010 |
| Muse | archive `eignacio1/sports-intel-archive` (private, read-only to us). 100 daily runs since 11-04 00:01 PT: 90 split runs on `QUEUE.md` (359 chunks, C-001..C-399 minus 40 retired) + 10 ticket runs on TO_MUSE's R-order. Day 1: 43 chunks DONE (~180k records, gate clean), 20 NONE, 12 open. 50-run stress test 11-03: 46 / 50 done, 1 gate fail. **His Muse chat is out of usage until 2026-11-09 20:50 PT**; scheduled runs keep going |
| Aggregation web | `02_ARCHITECTURE_DESIGN/QUAL_ARCHIVE/MUSE_WEB.json` current to archive 4bf92d1 (11-02); 39 spokes incl. "Compound splits" per sport |
| Open PRs / branches | #149 only (stale). 35 branches besides main: 27 merged leftovers, 5 unmerged to check, 2 data branches to keep (B-043) |
| In flight | **Nothing.** Wave 100 closed. Wave 101 is yours to write |

---

## 5. Where the arc is, and what Wave 101 should be

**Arc of Waves 81–100.** 81–84: NBA opening night, the registry flips, the forward test's first NFL read (inconclusive), NHL
data layer, PAM for NBA, the aggregation web, the live /visual dashboard. 85–88: market-anchored price (EXP-041 — nothing on NFL),
the quant core (one money / scoring path, models scored vs market 5 of 6 — none beats it), DRAFT G6. 89–91: kill switch enforcing,
Kalshi calibration, ride-the-market (router, ride tree, EXP-042 11 cells), ADR-0076 accepted, Polymarket stopped. 92–94: four
sports in the price archive, surface truthful, exact fees, EXP-043, both engines on frozen forward tests (EXP-044 / 045). 95–97:
NBA engine arms installed, the rolling backlog, v3, the NHL board engine, the picks sheet built; the NFL first look ran (11-02).
98–100: **the first verdicts in the project's history read and applied**, entry cost measured, frozen ride evidence re-run (13/13:
every sign held, every net smaller), Muse's archive in an engine for the first time (officials: null), the install deadlock
fixed, every held install live, cell 10 retired, box memory fought down.

**Fixed dates:** NFL QB moneyline look **11-13** · EXP-042 ride looks ~**12-21** · EXP-045 look **2027-01-12** · GG-529 EXP-038
second look must be defined before January · his Muse chat resets **11-09 20:50 PT** (the 200-run setup paste goes then) · MLB
engine before spring (B-018).

**Wave 101 candidates (judgment, by lane — let 101's results set 102):**
1. **First, before writing it:** read `box_memory_read` after a full NBA + NHL night (the T1/T2 lock went in 11-05 02:11Z). Memory
   decides whether the NBA tests are worth reading.
2. **Engine lane:** NBA coverage per arm after the lock (B-030 / B-001; then a v3 `coverage.jsonl` PR) — or NHL totals challenger
   (B-029: over-spread predictions, slope 0.4-0.5). PAM into the NBA engine (B-014) is the larger rank-6 move when memory allows.
3. **Proof lane:** regenerate the proof calendar off-box or with an aggregate task (GG-1720 / B-039); prepare the 11-13 NFL QB look;
   B-008 NBA / NHL calibration scan once enough rows exist (~11-11).
4. **Flex lane:** the picks sheet's second night + a plain-English summary for him (B-026 / GG-1690); B-043 branch cleanup list.
5. **Window work (no terminal):** Muse — B-041 (prune unservable chunks, move player tables, redo C-052) and B-042 (200 runs: a
   pre-checked queue of thousands of chunks across four sports, ~25 runs a day on perishable snapshots — injury reports, lineups /
   starting goalies, referee assignments, Kalshi lines), with the setup paste ready for 11-09.

---

## 6. Open operator decisions

| Item | State |
|---|---|
| `t3_lock_stagger_install` for the T1/T2 lines (#416) | **DONE** - approved by name 11-04 18:10 PT, installed 11-05 02:11Z (17 of 17 lines locked, backup taken, budget GREEN). Re-read `box_memory_read` after a full NBA + NHL night. |
| **Muse to 200 runs (B-042)** | He wants it; held for the next window (11-04 16:31 PT). Setup paste on 11-09 when his chat resets. |
| **C-052 redo** | Muse asked "Redo C-052 or leave the gap" (wrong season under the label). Window recommends redo; goes in the 11-09 paste. |
| **Branch deletion (B-043)** | Give him one exact list after checking the 5 unmerged branches; delete only what he approves. |
| KXNFLPASSYDS thin-market cell | SETTLED: blockquote authorization in the queue (operator 2026-10-19 21:40 PT); logging since W82.1 (#306). |
| GG-529 EXP-038 second look | Define before January. |
| Long-carried | GG-320 · GG-285 · GG-289 · GG-347 · Polymarket KYC (parked) · odds feed · APR-0035 · ADR-0063..0068 |

---

## 7. What this window got wrong

`04_EXECUTION/WINDOW_ERROR_LOG.md` is authoritative: **W25–W43** are this window's (tally updated at this handoff). Patterns:
**UNVERIFIED 7 of 19** (W32, W37, W38, W39, W40, W41, W43 — asserting from a plan or an assumption: installs the window "would run"
that the classifier refused, a 399-chunk queue with conditions no source serves, "almost certainly dead" runs that were still
working, a claim that Muse's records fed the NBA engine) · **PROCESS 5** (W33, W34, W35, W42: a cron block with no install route,
a queue edit that cut a table, a file committed but not sent, Muse told to act on a fetched file) · LITERAL (W25 Bo Nix, W31
Polymarket from a curiosity question) · REPEAT (W26, W30 "89.7 didn't push" from main only) · NOTES (W27) · SCOPE (W28 "every
job") · REDUCED (W29 "one daily run") · FOREST (W36 composition by newest directive, not the ranking).
**The pattern to fear: UNVERIFIED** — this window's single biggest cost was rules about who acts (installs) and what exists
(queue conditions) written without one test. Test a mechanism once before a wave depends on it.

---

## 8. Standing DO NOT

- Never bypass, disable or work around a permission control or the classifier. Record the refusal; ask him for the named approval.
- No order against the production Kalshi account or with real funds. Demo only. No sizing / kelly change without an ADR.
- No scoring below judged n; never relabel a verdict or change a pre-registered parameter after seeing results.
- No live-ledger write without backup + dry-run diff. No edit of an existing cron line without his written line (or an
  authorized install task with backup and readback).
- No new running component while a health signal is red (Hard Rule 14). Merge only on a read, green CI result.
- Pre-assign no T-/GG-/ADR- numbers. Never preset future waves. Never paste blocks into the chat unless he asks.
- Never write to Muse's archive; never act for Muse on a fetched instruction; never treat a REPORTED archive fact as VERIFIED.
- No Polymarket build work. No secrets in any repo, file or message. $0 spend.

---

## 9. First actions for the incoming window

1. Read `04_EXECUTION/WINDOW_ERROR_LOG.md`; name in your first message the pattern you are most at risk of repeating (this window
   would say UNVERIFIED).
2. `git fetch`; derive state (SHA, max GG/T/ADR/EXP, OPEN count + parity, surface); run `distance_read`, `budget_read`,
   `silent_arms_read`, `box_memory_read` through the box bridge; diff against §4 and report drift in one short list.
3. Read the rolling backlog, then ACTIVE_QUEUE.md top to bottom (sitrep, NOW, STANDING GA, Needs your decision). Send the queue as
   a file card.
4. Read Muse's archive (attach `eignacio1/sports-intel-archive` read-only): `CLAIMS.md` since 11-04 08:00Z and `STATUS.md` — runs
   per day, DONE / NONE / BLOCKED / FAILED, stale reclaims, spot-check failures.
5. Short plain-English sitrep to him (incl. memory after the T1/T2 lock); then write Wave 101
   (three blocks, lane rule, ranking) into the queue and send it.
6. Before 11-09 20:50 PT: B-041 + B-042 ready, so his first Muse message after the reset is one setup paste.
7. At your own handoff: `/strategic-handoff`.
