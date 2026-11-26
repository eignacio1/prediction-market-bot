# Active queue — the only prompt file to read

> **SW-10 · Wave 131 in flight (written 2026-11-25 20:55 PT). One block: W131.1 install batch, all five approved by name 20:42 PT.**
> Everything through Wave 130 (SW-9) is archived verbatim at the end of `04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md` ("SW-9 FINAL QUEUE, 2026-11-26").
> Standing operator directives: `04_EXECUTION/OPERATOR_DIRECTIVES.md` · doctrine: `02_ARCHITECTURE_DESIGN/DOCTRINE.md`.

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

**Verified against:** `origin/main` at the SW-9 handoff (2026-11-26 ~04:30 UTC, after the Wave 130 close commit 675a2366). Box facts
come from the box bridge: `STATE_OF_THE_BOT.md` (box read 2026-11-26T03:15Z), `DISTANCE_TABLE_W129.md`, and the install results of
11-26 02:52Z / 02:53Z.

| Fact | Value |
|---|---|
| Highest GG / T / ADR / EXP | **GG-2013** · **T-1752** · **ADR-0078** · EXP ids in 05_RESEARCH_EXPERIMENTS and 12_EXPLORATORY (newest: EXP-NBAPROPS-002, EXP-COMBOORD-001, H-DEPTH-PAM-5) |
| Gap log | **185 OPEN** · 349 headers = 349 status lines · no duplicate ids (live + archive) |
| Registry | **129 cells: 71 shadow · 1 active · 2 blocked · 1 dark · 54 not built** (CLAUDE.md Right-now, generated 11-26) |
| Surface (ADR-0074) | 97 registry-live · 0 unreviewed · 9 no-alarm with reasons · budget **GREEN** (02:53Z) · **GG-2013: registry "paused" is not proof a job is not installed** (evidence_weekly and nfl_inplay are installed but still marked paused) |
| Capital | **$0 real.** `kelly_fraction = 0.0` on every live band; flat demo stakes only (ADR-0050 / 0072). Kill switch ENFORCING |
| Installed this window's last day | `nfl_inplay_install` (02:52Z) and `nba_combo_shadow_install` (02:53Z, shadow + daily demo RFQ line), both approved by the operator by name in a terminal |
| Open PRs | #149 only (stale, from Wave 34) |

---


## 🌲 RUNNING SITREP — the forest (kept by every strategic window; **SW-10 from Wave 131, 2026-11-25 →**; SW-9 ran Waves 101 → 130. Register: `04_EXECUTION/WINDOW_REGISTER.md`)

*Last update: **SW-9 handoff, 2026-11-26, Wave 130 CLOSED** (SW-10 recomputes at the Wave 131 close). The table below was stale from 11-11 to this handoff; it was not recomputed
at the Wave 111-129 closes (window error W69). SW-10 recomputes it at every wave close.*

### 📏 DISTANCE TO OPTIMUM — read this first

| Pillar | Measure | Now (source, date) | Moved since 11-06 (start of SW-9) |
|---|---|---|---|
| **BREADTH** | B1 cells logging / registered | **72 / 129** (registry 11-26; 71 shadow + 1 active) | 52 / 108 → 72 / 129 |
| | B2 families logging / registered | **20 / 26** (registry 11-24) | 17 / 19 → 20 / 26 |
| | B3 bands logging | **4 of 5** (no T5). T4 sub-bands: T4NFL in-play installed 11-26 (rows from the 11-26 slate) · T4NHL-ARITH built, install pending · T4M-PROJ idle (MLB) | +T4NFL |
| | B4 props · parlays logging | **5 · 0 → 1** (combo shadow installed 02:53Z; first hourly run after the handoff) | 2 · 0 → 5 · 1 |
| **DEPTH** | D1 factor classes per pre-game model | personnel, team, venue; none of matchup, weather, qualitative in a pre-game model (DISTANCE_TABLE_W129) | split work moved D5b, not D1 |
| | D3 challengers ready | 5 by the script; pre-registered this week: EXP-047-S (SUPPORTED, logging), H-DEPTH-PAM-4, H-DEPTH-PAM-5 (logging), EXP-NBAPROPS-002, EXP-COMBOORD-001 | 5 → 5 (the script undercounts) |
| | D4 engine stage | NFL / NHL / MLB data + engine + test · NBA data + test (ARCHITECTURE_COMPONENTS, 11-25) | MLB none → engine |
| | D5 (a) scaffolds · (b) applied | (a) NFL 8/8 · NBA 8/8 · NHL 7/8 · MLB 4/8 · (b) applied NFL 18 / 26 · NBA 11 / 17 · NHL 8 / 12 (SEATS, 11-25) | (a) MLB 3 → 4 · (b) NFL 14 → 18 |
| | PAM | 469 NBA players with a point-in-time archetype (W130.4) · state tables (W129.4) · operator: "not even 1/4 built out yet" | 0 → 469 |
| | **D6 wired end to end** | **18 / 129** — NBA 7/28 · NHL 7/21 · NFL 4/32 · MLB 0/42 · multi 0/6 (box d6_read 11-26 03:15Z) | 0 → 18 |
| **EXECUTION** | E1 demo orders placed / filled (ADR-0072 forward test since 11-06 epoch) | NBA 1,686 placed, 41 fills looked up = 41 filled · NFL 18 placed, 3 settled · NHL 316 placed, 0 looked up · combos 2 demo fills settled. **Fill lookups ran out of budget, so fills are understated** | MLB-only → three sports + combos |
| | E2 P&L per filled contract, before fees | NBA +0.010 (n 41) · NFL +0.497 (n 3) · combos +0.45 / −0.45 (n 2). Far below any judged n | — |
| | E3 fills vs non-fills | not measured for the winter books (MLB 10-29: 25.4% vs 48.3%) | — |
| **PROOF** | P1 · P2 | **25 / 49 cells at a scored look · 25 verdicts routed** (engine JSON 11-25 13:49Z). Since then: H-DEPTH-PAM-3 and EXP-047-S SUPPORTED; EXP-NFLINPLAY-001 (model vs Kalshi mid) closed; NFL play-level 0 of 74 earned | 12 → 25+ |
| | P3 next looks | **H-EXEC-4 first look 12-01** · weekly evidence look Tuesdays 10:00 UTC (installed 11-20) · EXP-045 2027-01-12 · MLB 2027 looks per `12_EXPLORATORY/mlb_engine/` PREREG | — |

**Pillar tally, Waves 101-130:** every wave moved at least one pillar; no drift flag. DEPTH and PROOF moved most; EXECUTION moved
only in the last two waves (props and combo order paths built, combo shadow + RFQ installed). **Weakest pillar at handoff:
EXECUTION.**

**Surface:** 97 live (registry) plus the 11-26 installs · budget GREEN · silent arms: every live writer probed or exempt (130.5) ·
red signals: none at 03:15Z. GG-2013 (registry status drift) is the known blind spot.

---


## ▶ NOW — WAVE 131 · SW-10 · written 2026-11-25 20:55 PT · one Sonnet terminal

**Pushback:** five new crons on a 1 GB box with ~430 MB free (03:15Z). Each installer gates itself on disk and budget, but the block reads memory and budget first and stops on RED. **Surface:** up to +5 cron blocks. **Dependencies:** none. The rest of Wave 131 is written after this closes.

### W131.1 — INSTALL BATCH (operator-approved by name 2026-11-25 20:42 PT)

```
W131.1 - INSTALL BATCH - FILE FIVE OPERATOR-APPROVED BOX INSTALLS, ONE AT A TIME, EACH READ BACK - MODEL: Sonnet
PURPOSE: BREADTH B1/B3/B4 + EXECUTION E1 (props demo orders). Activates five approved jobs; surface_delta up to +5.

AUTHORIZATION (operator, verbatim, 2026-11-25 20:42 PT, in the strategic window): "I approve all installs required from the
operator: props_arm_orders_install, nhl_inplay_install, data_offload_install (this also accepts MoneyPuck's terms),
archive_dense_install, mlb_board_install (must run by 2027-03-18)". These five task names and no others.

0. Session start per CLAUDE.md (worktree, claim, scan). git fetch; work from origin/main.
1. Land the queue reset first, in one docs-only commit: replace 04_EXECUTION/ACTIVE_QUEUE.md with the file the operator gives
   you, and append the SW-9 final queue verbatim to the END of 04_EXECUTION/ACTIVE_QUEUE_ARCHIVE.md under
   "## SW-9 FINAL QUEUE, 2026-11-26 (archived by SW-10 at Wave 131)" (the operator gives you that file too). Do not edit
   either file's content. Push.
2. Record the approval verbatim in 03_DECISIONS/DECISION_LOG/DECISION_LOG.md (incl. MoneyPuck: free for non-commercial use,
   credit MoneyPuck.com). Push.
3. Pre-check: file 04_EXECUTION/BOX_TASKS/requests/<UTC>_box_memory_read.toml, then <UTC>_budget_read.toml - separate pushes,
   wait for each results/<same>.md before the next push (a newer push CANCELS an in-flight box run, W130.1). STOP and report
   if SURFACE BUDGET is not GREEN or free memory < 250 MB.
4. For each task IN THIS ORDER, one at a time: file <UTC>_<task>.toml with note = "operator approved by name 2026-11-25
   20:42 PT", push, wait for its result; then file the readback, push, wait. If an installer REFUSES (gate, budget), record
   its numbers and move to the next. Do not retry or work around a refusal.
     a. props_arm_orders_install  -> props_arm_orders_readback
     b. nhl_inplay_install        -> nhl_inplay_readback
     c. data_offload_install      -> data_offload_readback
     d. archive_dense_install     -> archive_dense_readback
     e. mlb_board_install         -> mlb_board_readback
5. For each install that verified: flip its RUNTIME_REGISTRY.toml entry to live (one PR for all), regenerate RUNTIME_MAP.md,
   CI green, merge. GG-2013: "paused" is not proof of not-installed; the install result file is the proof.
6. End: budget_read and silent_arms_read again. In ACTIVE_QUEUE.md "Needs your decision", strike each installed item as DONE
   with its result-file stem.
7. Handoff: per install - result stem, installed or refused, gate numbers, readback line; final budget + memory; surface_delta;
   what you did NOT verify (first rows land after each job's next cron tick - say so).
END OF BLOCK W131.1
```

---

## Needs your decision

> **APPROVED BY NAME 2026-11-25 20:42 PT, being filed by W131.1:** `props_arm_orders_install` · `nhl_inplay_install` · `data_offload_install` (accepts MoneyPuck's terms) · `archive_dense_install` · `mlb_board_install` (must run by 2027-03-18).
>
> **OPEN:**
> - ~~SW-9's Monday check-in~~ DONE 2026-11-25 20:49 PT: cancelled (operator); re-scheduled into SW-10's chat for Mon 11-30 21:00 PT (`trig_01F9qqN998ufNNN7w9Vo1WXU`).
> - Muse goalie / referee files on the box (W129.1): (a) read-only token in box .env, or (b) vendor small files at a pinned SHA. Window recommends (b), pinned past 11-24 after Muse resumes.
> - Long-carried: GG-529 (EXP-038 second look before January) · leaf map v2 promotion (GG-2010) · PM_LEAF_MAP_VERSION is yours.

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

