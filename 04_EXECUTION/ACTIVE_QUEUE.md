# Active queue — the only prompt file to read

**Verified against `origin/main` = `8916355`, 2026-08-26.** Waves 4-6 closed; Wave 7 in flight. `git pull` before trusting a working tree. Cell registry, imported live: **68 cells — 1 ACTIVE, 2 BLOCKED, 1 DARK, 64 NOT_IMPLEMENTED** across 14 market types (MLB/NBA/NFL/NHL) and 8 bands. Gap log: **60 OPEN**, of which **2 CRITICAL** (GG-166, GG-170) and 7 HIGH (now including **GG-203**). Re-derive before citing any of it.
**Free IDs:** T-496+ · GG-216+ · ADR-0060+ · APR-0033+ · EXP-025+
**Reserved per block:** T-492/GG-205 · T-486/GG-215 · T-493/GG-213 · T-487/GG-207 · T-495/EXP-024 · T-488/GG-208 · T-490/GG-210 · T-489/GG-209 · T-491/GG-212 · T-494/GG-214.
**Already spent:** GG-216 (T-496) · GG-217 (T-495, took the number reserved for T-497 — T-497 reassigned to **GG-218**) · GG-203 (T-482) · GG-204 (T-485) · GG-206 (T-484) · GG-211 (T-483).

---

## Read this first

**Prompt blocks below are the paste-in. Nothing else in this file is a task.** Block headings are wave coordinates — `# 5.1` is wave 5, slot 1 — so the sequencing track and the prompts share one numbering. Everything after "Needs your decision" is reference: read it to understand why the order is what it is, not to act on it.

**When a window closes, delete its prompt block and move its row up into the closed-wave table with a status marker and a one-line outcome.** The prompt text goes; the row stays. A closed wave that disappears from the table forces the next reader to comb git to work out what already ran — the exact failure this file exists to prevent. Full detail lives in `SESSION_CLAIMS.md`, `DECISION_LOG.md` and git; the table carries status + outcome only.

**GG numbers are pre-allocated per block, including for blocks not expected to need one.** Take the number your block names and no other. **A reservation is not an entry:** if your block registers nothing, say so in your CLOSED row and return the number.

**Deliverables parallelize; close-outs do not.** Each prompt carries a self-serialising close-out rule — do not remove it. T-482/T-483/T-484 hit two rounds of append-order merge conflicts in `GOVERNANCE_GAP_LOG.md` and `DECISION_LOG.md` on 2026-08-24 running three-wide; the rule works but it is not free.

---

## Where the build actually is

**The bot is alive and has been failing 100% of its order submissions for ten days.** T-482 ran Step 4 for real and found what three sessions of ledger-staring could not: `t4-mlb` is `active`, `NRestarts=0`, the cycle log and audit log are writing in real time — and since **2026-08-15T00:06:20Z** every single `risk_eval_approved` event is followed by a `kalshi_order_failed`, 1:1, daily counts matching exactly (372/372, 692/692, 281/281, 445/444, 1056/1057, 534/534, 180/180, 420/420, 1212/1212). **Roughly 5,200 approved bets, zero submitted.** Two distinct HTTP 404 bodies: `market_not_found` (first, 08-15) and `user_not_found` (most recent, 08-24), both from `component: "C5-PAPER"`. Two different reasons across the window means this is probably not one static misconfiguration — credential or session state, or a market-lookup path that fails differently by ticker. **GG-203, OPEN, HIGH. Registered and stopped. T-492 fixes it and it is the top of the board.**

That is worse than the dark-pipeline hypothesis this queue previously carried, and it kills that hypothesis: it is not GG-143's cold-start blindness. A correctly-evaluating process whose execution layer fails every time is invisible to every health probe except a manual read of the order-outcome audit trail. **Every liveness check the project owns reported healthy for ten days.**

**Operator directive, 2026-08-25 — T1 reopens.** T1 was zeroed by ADR-0048 on GG-135's ruin geometry and then frozen at `clean_n=0` by epoch-10's `ALL_BANDS` reset (GG-153). The directive is that the incoming market arms need it. **That reasoning holds and this queue previously had it wrong.** T1 is the multi-day pregame band, and it has only ever been measured on `KXMLBHIT` — player props, the worst possible market for a multi-day horizon: lineup risk, late scratches, rest days, thin books. The markets now being added — moneyline, spread, run line, totals — are game-level, priced days ahead, with no lineup risk at the game level, materially lower per-bet variance, and vastly greater supply. **GG-135's ~100%/yr kill-switch trip probability was computed on prop variance and does not automatically describe game-market variance.** It has to be re-measured, not assumed in either direction — that is T-494.

**Three facts that make the reopen cheap.** (1) The T1 cells **already exist**: the registry carries `T1` cells for `mlb_moneyline`, `mlb_run_line`, `mlb_game_total`, `mlb_team_total`, `mlb_partial_game`, `nfl_moneyline`, `nfl_spread`, `nfl_game_total`, `nfl_team_total` — all `NOT_IMPLEMENTED`, all scaffolded, none needing construction. (2) **Reopening T1 does not require un-zeroing any Kelly.** ADR-0050's flat measurement stake is exactly how T4M-PROJ accrues evidence at `kelly_fraction=0.0`; T1 can reopen on the same pattern, taking zero ruin exposure while its cells accrue. (3) **GG-153 dissolves under per-cell epoch scoping** — ADR-0054 (b), already sitting in the signature bundle. T1's frozen global cohort stops mattering once each cell carries its own clean floor.

**The convergence nobody has stated: Phase 2's model is a T1 model.** Boxes 2.2/2.3 fit NB/Poisson to team run totals and score against archived `KXMLBTOTAL` — a pregame, multi-day-horizon, game-level forecast. That is not a T4M-PROJ signal; T4M-PROJ is an in-play projection band and you cannot run it on a pregame distribution fit. **If gate 2.3 passes, the cell it activates is `(mlb_game_total, T1)`.** The plan never said so because the plan has no band axis at all — which is GG-172, and which is now T-491's central case rather than a scope footnote.

**Distance to live capital, unchanged by any of the above:** 1 of 53 cells ACTIVE · every live band at `kelly_fraction=0.0` · T4M-PROJ `clean_n=719` against `n*≈5,580` (13%), and it has accrued **nothing since 08-14** because of GG-203 · every paper fill ever recorded assumed at mid, never validated against the book (GG-157, an explicit G6 precondition) · ≤60s kill-switch SLA documented as 12× too slow for continuous evaluation (GG-038) · C7's drift-alarm ladder never invoked from any production path (GG-125) · every `_HARD_LIMITS` value carrying an unmet 2026-05-29 obligation to be revised via ADR at G6.

---

## Sequencing track — every block, run and unrun

**Status legend:** ✅ merged to `origin/main` · ⚠️ complete but NOT merged · ❌ assigned, never ran · ⏳ in flight · ⬜ not started
**Concurrency rule: fire one wave at a time, never mix waves.** Blocks inside a wave have disjoint file surfaces and are safe three-wide at most. **Every block writes `GOVERNANCE_GAP_LOG.md` and `DECISION_LOG.md` at close-out and those are not `merge=union`** — the self-serialising close-out rule in each prompt handles it, but T-482/483/484 still hit two rounds of append-order conflicts running three-wide on 2026-08-24. Three is the ceiling, not the target.

### ✅ WAVE 4 — closed 2026-08-24 (do not re-run; prompt blocks deleted per the rule)

| # | ID | Task | Status | Outcome |
|---|---|---|---|---|
| 4.1 | T-482 | Session-start Step 4 + T4 liveness | ✅ **merged** (#110/#111) | **Found GG-203** — engine alive, 100% order-submission failure since 08-15 |
| 4.2 | T-483 | Install queue + nav housekeeping | ✅ **merged** (#107/#108), **truncated at budget** | Installed an earlier draft; 10 `TERMINAL_PROMPTS_*` files left behind → T-486 |
| 4.3 | T-484 | Commit + extend `KXMLBTOTAL` outcome store | ✅ **merged** (#109/#112/#114/#115) | 239→329 rows, 224→307 resolved; GG-206 OPEN |
| 4.4 | T-485 | ADR-0057 — re-scope G6 off T1 | ⚠️ **NOT MERGED** — branch `ba09980` | ADR-0057 + GG-204 exist only on the branch; CLOSED row written for unlanded work → T-486 |
| 4.5 | T-486 | Install rebuilt queue | ❌ **never ran** — no claim, no branch | Re-issued below as Wave 5 |

### ✅ WAVE 5 — closed 2026-08-25 · ran 3-wide, all three landed

| # | ID | Task | Status | Outcome |
|---|---|---|---|---|
| 5.1 | T-492 | GG-203 — restore order submission | ✅ **merged** (`d05bdb6`) | **Root cause external.** Kalshi demo-account order-write fault, account-wide, 8 hypotheses ruled out with evidence. **No in-repo fix.** GG-203 → PARTIALLY RESOLVED. `C5-PAPER` submission deliberate per ADR-0008, not a live-capital leak. GG-205 returned unused. → **operator action, still open** |
| 5.2 | T-486 | Install queue · land T-485 · finish cleanup | ✅ **merged** (PR #117) | All 5 items: T-485 landed (PR #113), queue installed, 10 `TERMINAL_PROMPTS_*` removed, ADR-0057 premise note added, GG-186 amended (5th CLOSED-without-merge). GG-215 returned unused |
| 5.3 | T-493 | ADR-0058 — reopen T1 on the game-market axis | ✅ **merged** (PR #116) | ADR-0058 PROPOSED. All nine `(MarketType, T1_MULTI_DAY)` cells confirmed NOT_IMPLEMENTED — **promotion, not construction**. GG-153 CLOSABLE-ON-ADR-0054(b). **Caveat: ADR-0050's safety wrapper is T4-shaped, needs a T1 equivalent → T-497.** GG-213 returned unused |

### ✅ WAVE 6 — closed 2026-08-26 · ran 3-wide, all three landed (`origin/main` `9533a75`)

| # | ID | Task | Status | Outcome |
|---|---|---|---|---|
| 6.1 | T-487 | Phase 2 boxes 2.2 → 2.3 (EXP-022) | ✅ **merged** | Model fit + gate scored; first evidence toward the `(mlb_game_total, T1)` cell |
| 6.2 | T-495 | NHL skeleton spike (reduced rigor) | ✅ **merged** (`eb6c6cf`) | **15 cells** seeded (3 families × 5 bands, all NOT_IMPLEMENTED, `kelly_fraction=0.0`). Measured live against Kalshi `/series` + `/events`: only **three** real NHL series exist (`KXNHLGAME`, `KXNHLSPREAD`, `KXNHLTOTAL`; date-tail grammar, no HHMM). Deviated from the 4-family spec rather than fabricate a ticker — **correct call**; missing team-total family registered as **GG-217** (OPEN, LOW) |
| 6.3 | T-496 | Venue compliance — the 403, egress jurisdiction | ✅ **merged** (`bd068af`) | **Reading (a): transient Kalshi-side 403, NOT a jurisdiction flip.** Unanimous **New Jersey** geolocation across 3 independent providers (ipinfo.io, ip-api.com, ipwho.is; ipapi.co rate-limited, not dissenting); stable DigitalOcean droplet since 2026-05-29, no IP/region change around 08-17/18. Confirmed jurisdiction was **never tracked as a venue constraint** before this session — **GG-216** registered, `VENUE_REGISTRY.md` updated. Live-capital geo worry closed |

### ✅ WAVE 7 — closed 2026-08-26 · 2-wide, both landed (`origin/main` `6a0bd9e`)

| # | ID | Task | Status | Outcome |
|---|---|---|---|---|
| 7.1 | T-488 | GG-157 — fills vs the book | ✅ **merged** (`fcd4370`) | **First nonzero haircut measurement.** Props: 605/765 epoch-12 positions joinable, mean **$0.0101/contract**. Resolved cohort n=559: P&L/bet **+0.2864 → +0.2518** (−12.1%) — **directional edge survives**. But **n\* rises 437 → 560 against n=559** — cohort flips MEETS → short by one bet. **Game markets (synthetic $1 flat stake): 3–5× props' median haircut, tail fills to ~$0.42/contract.** All figures on the **uncorrected** ledger (D1 still PROPOSED). Method explicitly weak: family-level nearest-in-time join (exact-ticker join has 0 overlap, T-428) |
| 7.2 | T-490 | `--sport` axis through the power calc (box 3.4) | ❌ **NOT MERGED** (T-499 sweep, 2026-08-27: branch `session/20260826T043303Z-t490-sport-axis-power-calc` HEAD `9e95194` confirmed not an ancestor of `origin/main` — GG-186, 6th instance) | GG-210 returned unused. Work: stopped before implementation, ADR-0054(b) start-gate unsigned (commit `7f5172c`). Docs-only diff, no `src/`/`scripts/`/`kelly_fraction`. Left unmerged — operator to decide fast-forward vs. lapse |

**Two results that change what follows.** (1) The n\* flip is **noise, not a gate crossing** — a sample-adequacy verdict that turns on a single bet is not a verdict, and D1 will move it again. Do not report T4M-PROJ as newly-inadequate. (2) **The game-market haircut is 3–5× props on markets whose median half-spread is 0.0050** (round-trip 0.010). That attacks the cost side of the T1 game-market thesis, which this queue argued from the *variance* side only. T-494 must now answer both.

### ✅ WAVE 8 — closed 2026-08-26 · 3-wide, all three landed (`origin/main` `9cd602d`)

| # | ID | Task | Status | Outcome |
|---|---|---|---|---|
| 8.1 | T-489 | GG-038 — kill-switch SLA | ✅ **merged** (`54e1fd0`) | **NFR-03 FAILS on real production data.** Band-level (T4M-PROJ): 200-trial harness p50 **22.3s** / p90 42.7s / max 51.2s → PASS; but real 48-cycle VPS data p50 **66.955s** / p90 74.7s / max 81.2s → **FAIL from p50 upward**. The harness's structural sleep+cycle model undershoots live latency (unmodeled network I/O) — **reported as FAIL against real data, harness PASS discarded**. System-level (C7 `trigger_kill_switch`): sub-millisecond, p50 ~0.027ms. **GG-209 registered: T1 has no force-close path** |
| 8.2 | T-491 | GG-172 — band axis, T1 as live case | ❌ **NOT MERGED** (T-499 sweep, 2026-08-27: branch `session/20260826T045905Z-t491-gg172-band-axis` HEAD `554b67b` confirmed not an ancestor of `origin/main` — GG-186, 7th instance) | GG-212 returned unused. Work: authored `BAND_AXIS_ACTIVATION_PROPOSAL_GG172.md` (band-axis activation boxes, T1 worked example). Docs-only diff, no `src/`/`scripts/`/`kelly_fraction`. Left unmerged — operator to decide fast-forward vs. lapse |
| 8.3 | T-497 | T1 flat-stake safety wrapper | ✅ **merged** | `c5_execution/measurement_stake.py` — ADR-0050's mechanism generalised to T1's nine ADR-0058 cells, same formula and price strata, **plus a mechanism T4 never needed: a live-measured fill-cost bound (`T1_MAX_HAIRCUT_PER_CONTRACT_USD=0.10`, grounded in T-488) that raises `MeasurementStakeRefused` rather than silently assuming zero haircut.** HARD STOP evaluated against code and NOT triggered. No `kelly_fraction`, cell-registry, `risk.py` or ledger change; nothing wired live |

**The result that outranks the rest: NFR-03 is a CLAUDE.md hard rule and real production misses it at the median.** This is a live-capital blocker discovered by measurement, and it was only caught because T-489 refused to accept its own passing harness over real data. **Do not silently fix it** — the remedy is a cadence change, an SLA revision, or an architecture change, and each is a decision. That is 9.2.

### ⏳ WAVE 9 — FINAL WAVE · 9.1 and 9.2 ✅ closed 2026-08-26 (`origin/main` `8916355`) · **9.3 runs now, ALONE**

| # | ID | Task | Status | Outcome |
|---|---|---|---|---|
| 9.1 | T-494 | GG-135 re-derivation — variance **and** net-of-cost edge | ✅ **merged** (`8c8a062`) | Per-family net-of-haircut per-bet σ from archived Kalshi prices joined to 307/329 resolved games: **MONEYLINE 0.097%, RUN_LINE 0.138%, TOTALS 0.103% — 2.4–3.4× T4M-PROJ's real σ, well below MAIN's.** But the headline: **fill cost alone turns all three families' net edge NEGATIVE before any model edge** (RUN_LINE worst, −0.021%/bet). **Edge-independence does NOT transfer.** GG-135 amended in place; reused its own MC harnesses unmodified so figures are comparable by construction |
| 9.2 | T-498 | **ADR-0060** — NFR-03 kill-switch latency (decision request) | ✅ **merged** | Note the number: **ADR-0060**, not 0059 (0059 was taken). Three remedies presented: (a) shorten T4 cycle — cheapest, costs API headroom, retires neither GG-038's throughput claim nor GG-209; (b) revise NFR-03's bar per band — honest but needs superseding-ADR authority and capital-exposure-derived justification; (c) out-of-band interrupt — cleanest, largest, **only option creating the primitive GG-209 would reuse** and wiring the inert system-level `SystemMonitor` in |
| **9.3** | **T-499** | **PHASE CLOSE-OUT — reconcile everything, record sign-offs, write the carry-forward** | ⬜ **RUN NOW, ALONE** | — |

**T-494 is the most consequential measurement of the Phase and it cuts against this queue's own thesis.** This window argued the T1 game-market reopen from the variance side and was directionally right — game-market σ really is 2.4–3.4× T4M-PROJ but far below MAIN. **It was wrong to treat that as sufficient.** At measured fill costs, all three families are net-negative *before the model says anything*. The reopen stays signed — measurement at `kelly_fraction=0.0` on a $1 flat stake is exactly how you learn this cheaply, and T-497's wrapper already refuses fills above $0.10/contract — but **nobody should now expect these cells to show positive net edge without a fill-cost improvement.** That is a decision owed, not a gap.

### Value column — which of these actually shorten the distance to live capital

**Yes:** T-492 (nothing accrues without it) · T-493 (opens the band the new arms need) · T-488 (explicit G6 precondition) · T-489 (NFR-03 hard rule) · T-494 (gates nonzero T1 Kelly).
**No — evidence or scope work:** T-486 · T-487 (generality evidence, and the first T1 cell's case) · T-490 (blocks cell #2, not deployment) · T-491 · T-495 (supply for later).

---

# 9.3 — T-499 · PHASE CLOSE-OUT · make the record true

**Start when:** 9.1 and 9.2 have both CLOSED. **Runs alone — nothing else in flight.** This is the last block of the Phase.

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "t499-phase-closeout"
scripts/claim_session.sh "T-499: Phase close-out -- reconcile plan, registry, gap log, carry-forward" "T-499 / GG-220"

TIER: STANDARD (budget generously -- this is a reconciliation, not a build). ONE deliverable: a Phase
record that is TRUE rather than approximately true -- which now includes recording the operator's
2026-08-26 sign-off on four ADRs -- plus the carry-forward for the next strategic window. Register-and-stop on any defect you find; do not fix code.

RECONCILE, each by re-derivation and not by reading the last summary:
1. MARKET_EXPANSION_ACTION_PLAN.md -- walk EVERY box in Phases 0-4. Check each against what actually
   landed this Phase (T-482 through T-498). Correct any box whose text no longer matches reality.
   Phase 2 in particular: T-487 ran boxes 2.2 and 2.3 -- record the verdict in the box, not just in a
   claim row.
2. Cell registry -- import it live and report the real counts by status and by sport. The header of
   THIS file says 68 cells / 14 market types; verify or correct it.
3. Gap log -- re-run the anchored OPEN count (it moved 59 -> 65 this Phase), the GG-ID uniqueness
   check, and the header/Status parity check. Move every RESOLVED entry to
   GOVERNANCE_GAP_LOG_ARCHIVE.md verbatim per T-420 -- roughly 13 had re-accumulated before this
   Phase and more have since. Report the before/after counts.
4. SESSION_CLAIMS.md -- run the claim/CLOSED lifecycle assertion. Every T-4xx claim from this Phase
   must have a CLOSED row and every CLOSED row must name a merge that is genuinely an ancestor of
   origin/main. GG-186 has now recorded FIVE CLOSED-without-merge instances; if this sweep finds a
   sixth, that is the finding.
5. Housekeeping this Phase left behind: commit 04_EXECUTION/ACTIVE_QUEUE.md (modified-uncommitted in
   main's tree since 2026-08-26); delete 11_MEMORY_HANDOFF/_to_delete/; run `git worktree prune`;
   confirm no ACTIVE_QUEUE copy exists anywhere outside 04_EXECUTION/.
6. Reserved-but-unused GG numbers -- GG-205, GG-213, GG-215 and any others returned this Phase must be
   confirmed absent from the log and genuinely back in the pool. State the true next free GG.

OPERATOR SIGN-OFF -- RECORD THESE FIRST, BEFORE THE RECONCILIATION SWEEP.
Earl signed off on 2026-08-26. Record each verbatim in APPROVALS_REGISTER.md with the date, then flip
each ADR's Status field. Hard Rule 3 stands: do NOT edit any ADR's body or reasoning -- Status field
and a sign-off line only. If an ADR's own text contradicts a condition below, STOP and report it
rather than reconciling it yourself.

  ADR-0054 -- items (a), (b), (d) SIGNED. Item (c) was already signed 2026-08-17. Document Status
    PROPOSED -> ACCEPTED.
    (a) ratifies the one-file/`market_type`-column design already running. Conditions: the three
        named blind spots must be carried as STAFFED follow-ons, not just named --
        `assert_ledger_invariants.py` has zero cell-awareness; `run_band_monitor.py` is not
        cell-aware; and the replay harness calls `open_position()` without `market_type=`, silently
        attributing every replayed position to MLB_PLAYER_PROP_HITS (GG-184). Record that third one
        as the priority of the three: it produces confidently wrong output rather than an error.
    (b) per-cell epochs SIGNED. Operator condition on the twelve-boundary re-audit: **the failure
        mode is asymmetric.** A boundary scoped too WIDE only costs sample; a boundary scoped too
        NARROW silently leaves dirty rows inside a "clean" cohort. **Scope wider when uncertain, and
        record the per-boundary cell scope and its justification for all twelve.** Write this
        condition into the implementing task, not only into the ADR.
    (d) per-family kill switches SIGNED **with implementation deferred until ADR-0060 is decided.**
        T-489 measured the band-level halt path failing NFR-03 at the median; wiring per-cell
        granularity into a too-slow mechanism adds precision to the wrong thing, and ADR-0060
        option (c) would change what (d) wires into. Record the deferral explicitly in the ADR's
        sign-off line so a future window does not read (d) as ready to build.

  ADR-0055 -- D1, D2, D3, D4 ALL SIGNED. Document Status PROPOSED -> ACCEPTED.
    D1 (apply the in-place repair of the 532 closed positions) SIGNED. Conditions, non-negotiable:
        backup written AND verified before the write; the five pre-registered assertions re-run
        POST-WRITE against the real file, not only in simulation. Simulation passing is not the same
        as the write having succeeded.
    D2 (the 46 stuck-open positions) SIGNED. May be executed first and alone -- independently safe
        from D1.
    D3 (the 76 rejected-position mismatches) SIGNED. Bundle with D1: one backup, one write, one
        verification pass -- not three.
    D4 SIGNED as **CONTINUE epoch 12 -- do NOT bump the epoch.** Rationale to record: an epoch marks
        a LOGIC change; this repair changes data to what it always should have been and no write-path
        logic changed. Bumping would reset every band's clean_epoch_floor and zero clean_n, destroying
        the exact 719-row cohort the repair exists to rescue. **Required mitigation: the repair must
        stamp per-row provenance (a `repaired_at` / `repair_ref` field) so repaired rows remain
        distinguishable from originals without an epoch bump.** If ADR-0055's own D4 discussion argues
        for a bump, STOP and report the conflict -- do not silently override the document.
    CONSEQUENCE TO RECORD: every epoch-12 figure moves once D1 executes. **T-488/GG-157's fill-haircut
    numbers were explicitly computed on the uncorrected ledger and must be re-run afterwards.** Name
    that as a follow-on task so it is not forgotten.

  ADR-0057 (G6 re-scoped off T1 onto the cell registry) SIGNED. Status PROPOSED -> ACCEPTED.
    Record the question this creates WITHOUT answering it: G6 stops being one event and becomes a
    per-cell threshold, so **how many of the 68 cells must clear before live capital** is now an open
    operator decision. Register it as a decision owed, not as a gap.

  ADR-0058 (reopen T1 on the game-market axis at measurement stake) SIGNED. Status PROPOSED ->
    ACCEPTED. Record two expectation-setters so they are not later mistaken for defects:
    (i) T-497's wrapper bound is T1_MAX_HAIRCUT_PER_CONTRACT_USD=0.10 while T-488 measured
        game-market tail fills at ~$0.42/contract, so `MeasurementStakeRefused` will fire OFTEN and
        the T1 cells will accrue slowly. **That is the wrapper working, not failing.**
    (ii) Nothing accrues at all until GG-203 is resolved. Signing 0058 does not start a clock.

  ADR-0060 -- NOT SIGNED. **Drafted by T-498 (PROPOSED). Note the number: it is ADR-0060, not 0059 --
    0059 was already taken.** **Operator pre-position, record it
    as such and not as a decision:** the operator's lean is **option (c), decouple halt from the
    cycle**, because it is the only remedy that also resolves GG-209 (T1 has no force-close path),
    while (a) spends API budget against ADR-0005 and (b) requires changing a hard rule's text.
    **T-498's cost analysis may override this -- if (c)'s blast radius comes back larger than assumed,
    say so plainly rather than deferring to the pre-position.**

7. DECISIONS OWED -- register each in APPROVALS_REGISTER.md as a decision request awaiting the
   operator. These are NOT gaps and must not be filed as gaps:
   (i) **ADR-0060 (NFR-03 kill-switch latency) is unsigned.** The operator's pre-position is option
       (c). T-498 notes (c) is the only remedy creating the primitive GG-209 would reuse, but also
       that it does not solve everything -- surface that limitation verbatim, do not paraphrase it away.
   (ii) **Does T1's game-market measurement still proceed given T-494?** ADR-0058 is signed and stays
       signed, but T-494 measured fill cost alone driving MONEYLINE/RUN_LINE/TOTALS net-negative
       before any model edge. Measuring at $1 flat stake is still how you learn cheaply -- but whether
       to spend the accrual on it is the operator's call, not a session's. Frame it as: proceed and
       measure, proceed only after a fill-cost improvement, or park the T1 cells.
   (iii) **How many of the 68 cells must clear before live capital** (created by ADR-0057).
   (iv) **GG-203 -- the Kalshi demo-account order-write fault.** No terminal can touch it. Zero
       accrual since 2026-08-15. State the elapsed days as of close-out, computed not copied.

8. THE PHASE'S OWN VERDICT -- write it, do not soften it. This Phase set out to expand coverage and
   instead spent itself on measurement integrity, and that was correct: three of its measurements
   (T-488's fill haircut, T-489's real NFR-03 failure, T-494's net-negative game-market families)
   each falsified something the project believed. Record which beliefs died. Specifically:
   - the T1 game-market reopen was argued from variance alone and T-494 showed variance was the
     wrong sufficient condition
   - the accrual stall was hypothesised as GG-143 cold-start blindness and was externally caused
   - a passing test harness (T-489's) was structurally undermeasuring reality, and the only reason
     that surfaced is that the session refused its own PASS
   The generalisable lesson belongs in the carry-forward: **this project's instruments have twice now
   been more wrong than the things they measure.** Say so plainly.

THEN WRITE THE CARRY-FORWARD to 11_MEMORY_HANDOFF/, same shape as
STRATEGIC_WINDOW_PDTP_2026-08-24.md. It must carry:
  - the Phase's verified end state (SHA, counts, phase-plan position), re-derived not copied
  - the decision state AFTER this block: ADR-0054, ADR-0055, ADR-0057 and ADR-0058 SIGNED 2026-08-26
    and ACCEPTED; ADR-0060 outstanding with the operator pre-positioned on option (c). Carry the
    CONDITIONS attached to each signature, not just the fact of it -- (d)'s deferral until 0059,
    D1's post-write assertion re-run, D4's provenance stamp, (b)'s scope-wider-when-uncertain rule
  - the operator item no terminal can touch: GG-203, the Kalshi demo-account order-write fault, zero
    accrual since 2026-08-15
  - the FOUR measured results this Phase produced that must not be re-derived: T-488's fill haircut
    (props edge survives at +0.2518/bet; game markets 3-5x, tail ~$0.42/contract); T-489's real
    NFR-03 failure (p50 66.955s vs a 60s hard rule); **T-494's game-market ruin geometry (per-family
    net-of-haircut sigma MONEYLINE 0.097% / RUN_LINE 0.138% / TOTALS 0.103%, 2.4-3.4x T4M-PROJ and
    well below MAIN -- but fill cost alone drives all three net-negative before model edge, and
    edge-independence does NOT transfer)**; and the pregame KXMLBTOTAL Brier decomposition
    (reliability 0.0001, no recalibration edge)
  - the errors this Phase made, in descending cost, including: a strategic window that proposed
    GG-143 cold-start blindness as the accrual-stall mechanism and was WRONG (T-482/T-492 found an
    external Kalshi fault); a GG number reserved for an unrun block and taken by a running one
    (GG-217); and stale duplicate copies of ACTIVE_QUEUE.md that had the operator reading the wrong
    file for several turns
  - an explicit instruction to the next window: DO NOT TRUST THIS DOCUMENT. Re-derive before citing.

SCOPE FENCE: nav files, 03_DECISIONS/ (archive moves only), 04_EXECUTION/, 11_MEMORY_HANDOFF/. Do NOT
touch src/, scripts/, any kelly_fraction, or any ADR's Status field.
GG-220 reserved.

Session-end budget does not apply to the reconciliation itself, but DOES apply to your own close-out.
GG-186 before CLOSED.

REPORT BACK: the four ADR Status flips and their APPROVALS_REGISTER rows; every before/after count;
which plan boxes you corrected; whether the claim sweep found a sixth GG-186 instance; the true next
free IDs; the carry-forward's path; any condition above you could NOT satisfy.
```
