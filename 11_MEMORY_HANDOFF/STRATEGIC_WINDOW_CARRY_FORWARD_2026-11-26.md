# Strategic Window — Carry Forward (SW-9 → SW-10)

**Written:** 2026-11-26 ~04:30 UTC (11-25 ~20:30 PT), at the close of **SW-9, Waves 101 → 130 (2026-11-04 → 11-26)**. Verified against
`origin/main` at the handoff commit: GitHub REST, tracked files, and the box read through the box bridge (`04_EXECUTION/STATE_OF_THE_BOT.md`,
box read 2026-11-26T03:15Z). Every figure in §4 was derived by running a command at write time. Treat each one as a claim to re-verify.
**Previous version** (SW-8, Waves 81 → 100): `11_MEMORY_HANDOFF/STRATEGIC_WINDOW_CARRY_FORWARD_2026-11-04.md`.
**Handoff procedure:** `.claude/commands/strategic-handoff.md` (`/strategic-handoff`). Run it at your own handoff.
**This window was compacted many times.** Everything below is rebuilt from the repo (DECISION_LOG, handoffs, the error log, box-bridge
results, Muse's archive), not from memory. SW-9's own review of its work: `04_EXECUTION/SW9_WINDOW_REVIEW.md`.

> Read `04_EXECUTION/WINDOW_ERROR_LOG.md` BEFORE this file (ADR-0074), then this file, then `02_ARCHITECTURE_DESIGN/DOCTRINE.md`, then
> the rolling backlog (`04_EXECUTION/ROLLING_BACKLOG.md`), then `04_EXECUTION/STATE_OF_THE_BOT.md`, then `ACTIVE_QUEUE.md` top to bottom.

---

## 0. North star

**CLAUDE.md § "What winning looks like — the operator's north star (four pillars)"** — never restated here. The distance table at
handoff is the first table of the RUNNING SITREP in `04_EXECUTION/ACTIVE_QUEUE.md` (recomputed 2026-11-26 from box sources). One line each:
- **BREADTH:**
  - B1 72 / 129 cells logging.
  - B2 20 / 26 families.
  - B3 4 of 5 bands (no T5); T4NFL in-play installed 11-26.
  - B4 5 props families; parlays 0 → 1 (the combo shadow was installed 11-26 02:53Z).
- **DEPTH:**
  - D1: no pre-game model conditions on matchup, weather or qualitative factors.
  - D5(b) applied: NFL 18 / 26, NBA 11 / 17, NHL 8 / 12.
  - D6: **18 / 129** wired end to end (NBA 7, NHL 7, NFL 4, MLB 0).
  - PAM: 469 NBA players with a point-in-time archetype.
- **EXECUTION:** the ADR-0072 demo forward test places orders in all three winter sports, but the fill lookups ran out of budget, so
  fills are understated.
  - NBA: 41 of 41 looked-up orders filled, +0.010 per contract before fees.
  - NFL: 3 settled, +0.497.
  - Combos: 2 demo fills, +0.45 / −0.45.
  - **The weakest pillar.**
- **PROOF:**
  - P1 25 / 49 cells at a scored look; P2 25 verdicts routed (engine JSON 11-25). Since then: PAM-3 and EXP-047-S SUPPORTED,
    EXP-NFLINPLAY-001 closed, NFL play-level 0 of 74 leaves earned.
  - P3: **H-EXEC-4 first look 2026-12-01**.

**The doctrine in force** lives in `02_ARCHITECTURE_DESIGN/DOCTRINE.md` (Last reviewed 2026-11-24; **review it at your first wave close —
it goes RED on 12-08**). This window wrote most of it:
- **ADR-0077, multi-arm routing (11-10 / 11-11):** the bot is layered trees choosing ride / fade / momentum / pot of gold / no bet per
  leaf. "Does not beat the market" is a routing result, never a stop. A factor is applied only as a tested split scored per leaf on net
  after costs.
- **ADR-0078:** per-arm cell state, closed arms.
- **The words (11-11 16:51 PT):** a losing look closes "THAT SPECIFIC HYPOTHESIS"; text says "hypothesis closed (EXP-id, parked for
  R&D)". Never "no edge".
- **HYPOTHESIS_DOCTRINE.md:** the scaffold, plus a registry of every hypothesis (73 rows, W129.5). It is updated in the same PR as any
  PREREG or result.
- **PAM's origin, in GRANULARITY_INDEX.md (11-24 23:00 PT):** "it's so valuable like unbelievably valuable that's the literal
  inception of my "granularity index" idea and it was made on like day 2". And: "it's not even 1/4 built out yet - it's almost common
  sense like obviously Zubac's 10 rebounds aren't the same as Wembys 10 rebounds".

**Doctrine check (read this aloud in your first message):**
- **The project's biggest running premise:** depth (finer factors, deeper engines, more leaves) will produce leaves whose held-out net
  after costs is positive, and accumulation across arms will add up.
- **The strongest evidence against it:** across Waves 101–130, **no arm clears zero after real costs.**
  - The edge-location program (H1–H4, H-EDGE-5) found gross effects that fall below one round cost on the most-watched lines.
  - NFL play-level: 0 of 74 leaves earned.
  - The NFL in-play model only ties Kalshi's mid.
  - The props and combo results so far are calibration gains (Brier, log-loss), not money.
  - NBA demo fills: +0.010 per contract **before** fees.

  The bet the project is making now is retail flow (props, parlays via RFQ) and execution quality. 130.2 / 130.3 built those order
  paths; the first real numbers arrive in SW-10.
- **What the operator has said he wants that no wave is building:**
  - Matchup, weather and qualitative factor classes inside a pre-game model (D1 is empty for all three).
  - The T5 band.
  - PAM piped into every engine. It is NBA props only so far; NFL has a WR mass tier, and MLB / NHL have no records.
  - Parlays beyond NBA same-game combos (NFL / NHL combos, big-hitter longshots).
  - Muse's qualitative archive applied as a split. Only officials were tested, and the result was null.

---

## 1. The role

The strategic window **directs; terminals execute.**
- **Where state comes from:** derive it from `origin/main`, GitHub and the box, never from a terminal's prose or from recollection.
- **Writing waves:** write paste-in blocks into `04_EXECUTION/ACTIVE_QUEUE.md` and **send the file as a file card every time it changes**.
- **Closing waves:** verify every block against GitHub when the operator says it is done. Keep the RUNNING SITREP and its distance
  table current **at every close** (W69).
- **Keeping the books:** own the rolling backlog, watch Muse, and route findings, verdicts and decisions to the operator.
- **Never hand him commands.** Sandbox / paper / demo actions are plumbing — handle them. **Only real capital is his.**
- **How to talk to him:** short, blunt, plain English; he reads on his phone. Lead with the answer.
- **Reporting:** report what was verified AND what was not (W65). Never a bare "all set".

**Executors:**
- **Terminals:** local Claude Code terminals on his Mac. SW-9's waves ran **five Sonnet blocks** at the operator's ask (W129 grew to
  seven). Wave size follows his message: "give me 5", "back to 4".
- **Models: Sonnet by default.** Never Opus or Fable in terminals unless he orders it (W56: Fable cost several times Sonnet).
- **This window:** runs in a cloud container (worktree `/home/claude/pmb-main`, push `git push origin HEAD:main` in a rebase-retry
  loop), opens and merges small PRs by REST, and acts on the box through the box bridge.

**The box bridge:**
- **How:** push `04_EXECUTION/BOX_TASKS/requests/<UTC>_<task>.toml` with `task=` and `note=`. The workflow runs only allowlisted commands
  (`scripts/box_tasks.py`) and commits `results/<same>.md`.
- **Read tasks used at every close:** `state_of_the_bot_read` (new, W130.5 — read this first), `d6_read`, `distance_read`, `budget_read`,
  `silent_arms_read`, `deploy_truth_read`, `box_memory_read`.
- **Install tasks (`*_install`) run only after the operator approves that exact task by name.** On 11-25 he approved two by name in
  terminals and the terminals ran them; the result notes record it. A general "go ahead" does not count.
- **Output caps at ~60 KB per result.**
- **A newer push cancels an in-flight box task run** (W130.1: the first install requests were cancelled and had to be re-filed).

---

## 2. Protocols (operator — follow exactly)

**Carried from earlier windows (still in force):**
- Distance table recomputed at EVERY close.
- Waves are sequential, never preset.
- Every wave carries **Pushback / Surface / Dependencies** lines; every block carries a **PURPOSE** line and an END OF BLOCK line.
- Authorizations exist only as blockquotes in "Needs your decision".
- $0 spend; no Polymarket build work.
- Pre-registration before a cell's first row; no score below judged n; kelly 0; no real capital.
- His examples are illustrations, not specs; quote his words into canonical docs, never compress them.
- Log your own mistakes the moment you learn of them; search memory, project docs and the repo before asking him anything.
- Delivery: blocks go inside ACTIVE_QUEUE.md and never into chat unless he asks. One `COMMON_RULES_W<n>.md` per wave; each block's
  FIRST line makes the terminal read it from origin/main and quote its first line. **W130 is the latest template.**

**Added by SW-9 (date, his words where short):**
- **The routing doctrine (11-10 21:35 / 21:41 PT, ADR-0077):** "Does a quant - that finds through rigorous testing and scaffolding that a
  certain betting pattern doesn't beat the "market" keep going? no he fucking routes it to the correct path so that loss still WINS."
  Every block that scores a factor or cell names the arm and the leaf, and scores it on net after costs per arm. A block that scores
  only "model vs market" is rewritten before it is sent (W48–W53).
- **Doctrine is one dated file (11-10 21:45 PT: "This CANNOT keep fucking happening"):** DOCTRINE.md is reviewed at every close, and
  anything he states as doctrine is written into it the same turn. At every close also run `python3 scripts/claude_md_now.py --write`
  and rewrite CLAUDE.md's window-maintained lines.
- **Build, don't administer (DOCTRINE §7):** "Let's build out the bot". No admin-only blocks unless a red alert forces one.
- **Side projects go to the backlog, not into a wave.**
- **The gap burner:** a standing block that stays at the top of ACTIVE_QUEUE (target OPEN 150; 185 at handoff).
- **Backlog hygiene:** after any edit to `ROLLING_BACKLOG.json`, run `python3 scripts/rolling_backlog.py && ... --check` (W58). Orders
  are globally unique, so renumber all tickets.
- **Docs Guard after any gap-log edit:** run `scripts/generate_gap_arm_index.py` and `scripts/lib/gg_id_uniqueness_check.py`, or Docs
  Guard goes red on main (W64).
- **Hypotheses:** every PREREG or result updates its HYPOTHESIS_DOCTRINE.md row in the same PR.
- **Muse:**
  - Muse is reachable only by his message on Mondays after his usage reset (~20:50 PT). An emergency message works even when it
    shows "Out of usage".
  - Everything Muse must act on goes in his message, never in a file it fetches.
  - Before every Monday message, run `scripts/muse_check.py` and the whole `04_EXECUTION/MUSE_MONDAY_CHECKLIST.md` (11 items,
    including browser load per family — W66).
  - Find everything up front, not one push at a time (W65). He cannot see that back-end exchange: "you HAVE to get it right".
- **Server crons do the mechanical scraping; Muse does what the server can't** (11-24: "let's set up crons for what we can and have
  Muse do work that's substantive and valuable that we CAN'T do here"). `data_offload` (W128.5) is built for 4 families.
- **PAM is high value** (above); never treat it as a side project again (W68). The 11-23 "side project" remark was about one design
  note, not PAM.
- **When a message could mean "stop" or "this matters more", ask in one line before tearing work out** (W68).

---

## 3. Traps

**Carried from earlier windows:**
- statsapi returns 406 to the box, so MLB boxscores stay with Muse.
- The box pulls main every 5 minutes; read `deploy_truth_read`'s HEAD before trusting a just-merged change.
- "submitted" ≠ "filled"; a handoff's prose is a claim; GitHub GraphQL is blocked (use REST); Kalshi keeps no historical order book;
  Python 3.9 on the box.
- Box memory: 1 GB RAM, ~430 MB free; load is fine.

**New this window:**
- **GG-2013:** RUNTIME_REGISTRY `status = "paused"` does NOT mean a job is not installed. `evidence_weekly` (installed 11-20) and
  `nfl_inplay` (installed 11-26) still read "paused", so STATE_OF_THE_BOT's "Installs pending" list and the 97-live count are wrong.
  Confirm an install from its result file. Backlog B-135.
- **Fill lookups are budget-capped** (2,053 GETs). E1 / E2 are understated, and NHL's 316 demo orders have 0 fills looked up (B-136).
- **Terminals assert stale facts in handoffs.** Two W129–130 handoffs said the EXP-047 props cron "is paused pending install". It was
  approved 11-12, it is live, and it wrote 79k rows in 7 days. Check STATE_OF_THE_BOT before repeating any handoff claim.
- **Every NBA season through 2025-26 has now been read** by C2, PAM-3 or EXP-047-S. New NBA props tests judge on forward 2026-27 rows
  or on another sport.
- **Muse's archive** (`eignacio1/sports-intel-archive`, master):
  - On 11-24 Muse pushed a commit that deleted the archive. The window restored it to `ab9951c3` (29,196 entries) with a two-parent
    commit, because GitHub API writes return 403 through the proxy and a single-parent push failed as too large.
  - Muse must drop its own commit `804e69e3` and add a mass-delete guard; this is in the 11-30 draft.
  - Read the archive only through the gh API; never clone it whole.
- **Muse's weekly allowance went in ~24 h** at full parallelism. The 11-30 draft cuts parallel jobs to ~15–25 and logs usage % in every
  HEARTBEAT line.
- **The old "Muse daily sweep" scheduled task is disabled** (`trig_01JAiX7XERTuC9CJgs3DaqTW`). The archive was attached to it and cloned
  at setup, so it failed nightly. The check now runs in-session (`scripts/muse_check.py`).
- **A pending check-in fires into SW-9's chat (not yours) on Mon 11-30 22:00 PT** (`trig_017F41iPy2qhDQEL9BAAtJ5Z`). Ask the operator
  whether to cancel it once you own Monday.
- **Overwriting the NOW section loses the prompts** unless they are moved to ACTIVE_QUEUE_ARCHIVE.md first (W69; W123–130 were recovered
  from git at this handoff).

---

## 4. State at handoff (derived 2026-11-26 ~04:30Z)

| Fact | Value |
|---|---|
| origin/main | the handoff commit (window); last block commit `675a2366` (W130.5 session close) |
| Highest GG / T / ADR | **GG-2013** · **T-1752** · **ADR-0078** |
| Gap log | **185 OPEN** · 349 headers = 349 status lines · no duplicate ids (live + archive) |
| Registry | **129 cells: 71 shadow · 1 active (T4M-PROJ, MLB, idle) · 2 blocked · 1 dark · 54 not built** |
| Box (03:15Z) | budget **GREEN** · every live writer probed or exempt · NBA and NHL arms writing · NFL in-play cron installed (rows from the 11-26 slate) · combo shadow + daily demo RFQ installed (first rows after handoff) |
| Capital | **$0 real.** kelly 0.0 on every live band. Kill switch ENFORCING |
| Forward test (ADR-0072, epoch 2026-11-06T01:03Z) | NBA 1,686 YES-side demo orders · NFL 18 · NHL 316. Fills understated (lookup budget) |
| New order paths | **EXP-NBAPROPS-002** (14 kept props leaves, flat $1 demo; `props_arm_orders_install` pending) · **EXP-COMBOORD-001** (combo RFQ, demo, installed) |
| Shadow challengers logging | EXP-047 props v1, C2, S (SUPPORTED), PAM5 · NBA engine v1 / v2 / v3 · NHL depth (PM_NHL_DEPTH on) |
| Frozen / fixed looks | **H-EXEC-4 first look 12-01** (frozen at #554) · weekly evidence look Tuesdays 10:00 UTC (installed 11-20; whether the 11-24 run produced output is **unverified**) · EXP-045 2027-01-12 · MLB 2027 forward PREREG (12 cells; `mlb_board_install` must run by **2027-03-18**) |
| Rolling backlog | 33 tickets. NOW: B-121 (H-EXEC-4 look), B-136 (fill lookups), B-135 (GG-2013). NEXT: B-134 (Muse files), B-119 / B-128 (installs) … |
| Muse | Out of usage until **Mon 11-30 20:50 PT**. Archive restored, master `ab9951c3`+. Queue ~3,900 chunks, floor 500. One-message draft for 11-30: `04_EXECUTION/MUSE_MONDAY_2026-11-30_DRAFT.md` (finish it with the checklist; item 6, the retire list, goes in only if `data_offload_install` is approved and its first nightly run succeeds) |
| Open PRs | #149 only (stale, Wave 34) |
| In flight | **Nothing.** Wave 130 closed. Wave 131 is yours |

---

## 5. Where the arc is, and what Wave 131 should be

**Arc of Waves 101–130:**
- **101–110:** memory fights, the forward test restarted (GG-1771 epoch), the routing doctrine (ADR-0077, DOCTRINE.md), D6 defined,
  same-game correlation priced (W110).
- **111–122:** the router wired to demo arm orders, ride and longshot cells, the weekly evidence look, NBA props splits (14 kept
  leaves), NFL / NHL depth seats, the Muse queue scaled.
- **123–126:** the edge-location program (H1–H5, H-MEAS-1): gross effects die at the round cost on the most-watched lines, so the build
  turns to retail flow, depth and MLB.
- **127–128:**
  - MLB engine counted.
  - H-EXEC-4 frozen.
  - Combos through RFQ: 2 demo fills.
  - PAM-3 SUPPORTED.
  - Muse's mechanical families moved to server scrapers.
  - Muse's archive deleted by Muse and restored by the window.
- **129–130:**
  - EXP-047-S SUPPORTED.
  - MLB 2027 frozen.
  - PAM state tables, then 469 point-in-time archetypes.
  - NFL and NHL in-play feeds.
  - Props and combo demo order paths.
  - Every live writer probed.
  - D6 one number (18 / 129).
  - STATE_OF_THE_BOT.md.

**Wave 131 candidates (judgment — let the first read decide):**
1. **Execution first (the weakest pillar):**
   - B-136, a complete fill join so E1 / E2 / E3 are real per book.
   - `props_arm_orders_install` readback once he approves it.
   - The first combo RFQ day read (EXP-COMBOORD-001).
   - The NFL in-play live feed lag from the 11-26 slate (130.1 Part B — the window can run its readback).
2. **H-EXEC-4 first look on 12-01** (B-121). Frozen; read it at its date, and route the result per leaf.
3. **Depth, using what the operator flagged:**
   - PAM archetypes into the props tree as splits, scored per leaf on net. H-DEPTH-PAM-5 is forward only, so build the split now and
     judge it at n.
   - PAM into NFL (WR mass tier exists).
   - A pre-game model that conditions on matchup / weather / qualitative factors (D1 is empty).
4. **Surface truth:** GG-2013 (B-135) as a small block; and verify the 11-24 weekly evidence run actually wrote output.
5. **Muse on 11-30:** run the checklist and send one message (draft ready).

---

## 6. Open operator decisions

| Item | State |
|---|---|
| `props_arm_orders_install` (W130.2) | pending — window recommends approve (flat $1 demo, kelly 0, own caps) |
| `nhl_inplay_install` (W129.7) | pending — recommend approve |
| `data_offload_install` (W128.5) | pending — recommend approve; accepts MoneyPuck's terms (free non-commercial, credit MoneyPuck.com) |
| `archive_dense_install` (W127.4) | pending — gate PASS 30.5 MB/day |
| `mlb_board_install` (W129.3) | not needed until 2027; **must run by 2027-03-18** |
| Muse goalie / referee files on the box (W129.1) | (a) read-only token in box .env, or (b) vendor small files at the pinned SHA — **window recommends (b)**; pin past 11-24 after Muse resumes |
| The SW-9 Monday check-in (`trig_017F41iPy2qhDQEL9BAAtJ5Z`) | fires into SW-9's chat 11-30 22:00 PT — ask him whether to cancel it once SW-10 owns Monday |
| Long-carried | GG-529 (EXP-038 second look before January) · leaf map v2 promotion (GG-2010: routes every unseen leaf NO_BET, so it would not move D6) · PM_LEAF_MAP_VERSION is his |

---

## 7. What this window got wrong

`04_EXECUTION/WINDOW_ERROR_LOG.md` is authoritative: **W45–W69 are SW-9's** (W44 was SW-8's, found by SW-9). The tally was updated at
this handoff.

| Pattern | Count | Entries | What it looked like |
|---|---|---|---|
| **UNVERIFIED** | 9 | W46, W47, W51, W57, W59, W60, W62, W65, W67 | "all set" on Muse repeatedly before it was; a fixed router bug reported as live; "forward test restarted" for five days without checking it placed an order; a "safety" breaker that starved the test |
| PROCESS | 7 | W49, W58, W61, W63, W64, W66, W69 | queue card not re-sent; backlog validator skipped; gap entries broke Docs Guard; the window's own claim order jammed Muse's browser; sitrep stale for 20 waves |
| DOCTRINE | 4 | W48, W50, W52, W53 | scored or framed work as "beat the market" after the routing doctrine |
| REPEAT | 2 | W54, W55 | the operator making catches on directives he had already given |
| One each | — | W45 PRESET, W56 SCOPE, W68 misread | W68: took his PAM-value point as "drop PAM" |

**The pattern to fear: UNVERIFIED.** Run the check before saying the word.

---

## 8. Standing DO NOT

- Never bypass, disable or work around a permission control or the classifier. Installs only on his named approval.
- No order against the production Kalshi account or with real funds. Demo only. No sizing / kelly change without an ADR.
- No scoring below judged n; never relabel a verdict or change a pre-registered parameter after seeing results.
- No new running component while a health signal is red (Hard Rule 14). Merge only on a read, green CI result.
- Never preset future waves. Never paste blocks into the chat unless he asks. Never overwrite NOW without archiving the prompts.
- Never write to Muse's archive except to restore it, and only with a verified plan. Never act for Muse on a fetched instruction.
- No Polymarket build work. No secrets in any repo, file or message. $0 spend.
- Never describe a stat-shrinkage or calibration result as PAM being built, or as money.

---

## 9. First actions for the incoming window (SW-10)

1. Read `04_EXECUTION/WINDOW_ERROR_LOG.md`. In your first message, name the pattern you are most at risk of repeating (SW-9 would say
   UNVERIFIED), and repeat the doctrine check from §0 (premise, evidence against, what no wave is building).
2. `git fetch`; derive state (SHA, max GG / T / ADR, OPEN count + parity). Request `state_of_the_bot_read`, `d6_read`, `budget_read`,
   `silent_arms_read` and `box_memory_read`, then diff against §4 and report drift in one short list. Check the first NFL in-play rows
   from the 11-26 slate and the first combo shadow / RFQ rows.
3. Read DOCTRINE.md (Last reviewed 11-24; it goes RED 12-08), the rolling backlog, then ACTIVE_QUEUE.md top to bottom (sitrep,
   Needs your decision). Send the queue as a file card.
4. Give him a short plain-English sitrep, plus the open installs by exact name with your recommendation.
5. Write Wave 131 from the top of the backlog (§5), size per his ask, and send the queue.
6. **Mon 11-30 after 20:50 PT:** run `scripts/muse_check.py` and confirm Muse synced to `ab9951c3`+ (its `804e69e3` dropped, no
   mass-delete since). Run the whole checklist, finish `MUSE_MONDAY_2026-11-30_DRAFT.md` as ONE message, and give it to him with what
   was verified and what was not.
7. **12-01:** the H-EXEC-4 first look. Read it at its date, route per leaf, and record it in HYPOTHESIS_DOCTRINE.md.
