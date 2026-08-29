# Active queue — the only prompt file to read

**Verified against `origin/main` = `d58c8dd`, 2026-08-29** (re-derived by the strategic window from the ref, not from the working tree — see the divergence warning below). Cell registry, imported live: **68 cells — 1 ACTIVE, 2 BLOCKED, 1 DARK, 64 NOT_IMPLEMENTED** across 14 market types; **18 `ExecutionBand` values are defined but only 6 carry any cell.** Gap log: **68 OPEN**, 82 entries, parity **82 = 82**, GG-ID uniqueness **CLEAN**. `git pull` before trusting a working tree. **Re-derive before citing any of it.**
**Free IDs:** T-503+ · GG-225+ · ADR-0061+ · APR-0034+ · EXP-026+
**Reserved per block — Wave 11 ONLY:** T-503/GG-225 · T-504/GG-226 · T-505/GG-227.
**Waves 12-13 carry NO pre-reserved GG numbers.** Assign at wave fire (GG-162, six instances).
**Spent in Wave 10:** GG-221 (T-500, OPEN) · GG-222 (T-501, OPEN) · GG-223 (T-502, RESOLVED) · GG-224 (T-502, OPEN — registered mid-repair, see below) · APR-0033 (drafted) · EXP-025 (used).

> **⚠ BRANCH DIVERGENCE, 2026-08-29.** The shared `main` checkout is **27 commits behind `origin/main`** (`d4c0ebf` vs `d58c8dd`) and carries this file uncommitted. **This file has never reached `origin/main`** — a worktree cut from the ref will not contain it, and `origin/main`'s copy still shows Wave 9.3 as "RUN NOW" and T-487 as merged. That is the tenth instance of GG-186's shape and it belongs to the strategic window, not to a terminal. **Installing this file is Deliverable 0 of block 11.3.** Until it lands, treat the pasted prompt as authoritative and this file as the draft of record.

---

## Read this first

**Prompt blocks below are the paste-in. Nothing else in this file is a task.** Block headings are wave coordinates — `# 11.1` is wave 11, slot 1 — so the sequencing track and the prompts share one numbering. Everything after "Needs your decision" is reference: read it to understand why the order is what it is, not to act on it.

**When a window closes, delete its prompt block and move its row up into the closed-wave table with a status marker and a one-line outcome.** The prompt text goes; the row stays.

**GG numbers are pre-allocated per block only for the wave that is about to fire.** Take the number your block names and no other. **A reservation is not an entry:** if your block registers nothing, say so in your CLOSED row and return the number.

**Deliverables parallelize; close-outs do not.** Each prompt carries a self-serialising close-out rule — do not remove it. Three-wide is the ceiling, not the target. **T-501 hit budget mid-close-out in Wave 10 and wrote a truncated stub before resuming** — budget the close-out, not just the work.

**Never write a merge status you did not confirm with `git merge-base --is-ancestor <branch> origin/main`.** Wave 10's three blocks all did this correctly and all three are confirmed ancestors. Keep it.

**New in Wave 10 — never repair a file that a running service owns without coordinating the service.** See GG-224. This is now a standing precondition, not a per-block detail. A **scoped** restart pre-authorization exists for 11.1 only (granted 2026-08-29, terms in the block) — it does not generalise to any other block or service action.

---

## Where the build actually is

**Nothing has accrued for 14 days and no terminal can change that.** Last resolved bet remains `game_date` 2026-08-14 / `resolved_at` 2026-08-15. GG-203 — Kalshi's demo-account order-write path rejecting every schema-valid, auth-valid order account-wide — is diagnosed, external, and **has no in-repo fix**. **Operator support ticket or demo-key regeneration. Still the single highest-value item on the board and still not code.** Compute the elapsed days at cite time; do not copy the 14.

**Wave 10 closed all three blocks and produced two findings that outrank the work they came from.**

**Finding 1 — GG-224: a live service silently reverted a completed, verified repair.** T-502 executed ADR-0055 D2 against `logs/paper_portfolio_mlb_t4.json`: correct backup, correct write, correct post-write assertions — and on a later check the repaired rows were **gone**, reverted to zero `repair_ref`-carrying rows. Cause: `t4-mlb.service` (`run_t4_mlb_live.py`) holds the entire portfolio object in memory and periodically flushes that in-memory copy back over the file, read-modify-write against its own state rather than re-reading from disk. The repair was redone and made durable only by restarting the service immediately post-write, under explicit operator authorization. **46/46 rows repaired, GG-223 RESOLVED.** But the general hazard is untouched: **GG-224 is OPEN, MEDIUM, and applies to every future external write to any service-owned ledger file.** This is the sixth instance of the Phase's own pattern — the instrument (a passing post-write assertion) was more wrong than the thing it measured, because it measured at the wrong moment. **Wave 11.1 writes 532 + 76 rows to the same file class. It does not proceed without the GG-224 protocol.**

**Finding 2 — Phase 2's NB refit landed in the same place, slightly worse.** T-500 pre-registered EXP-025 (committed `228a273`) **before** any NB code ran (`06639f2`) — order verified in git, which is the whole point of the pre-registration condition. NB1 with `phi=2.33` fixed by method-of-moments from T-487's own disclosed measurement, identical `mu_total`, identical `|model_p−mkt_p| > 0.010` rule, identical 214-game archive, selection re-derived from NB's own `model_p` rather than forced onto Poisson's game IDs. Result: **mean P&L/bet −0.0048 (vs Poisson's −0.0026), sd 0.3069 (vs 0.2425), `n*` = 44,220.** Verdict **INCONCLUSIVE — EXTEND ARCHIVE**, same state. Dispersion reconciled roughly: observed var/mean on the scored join (n=2,275) = 2.18 against the fixed 2.33.

> **What that means, stated plainly.** Correcting the distributional misspecification did not rescue the result — it moved the point estimate further negative and widened the spread. Two independent fits, one of them explicitly built to handle the defect blamed for the first, have now both produced a negative point estimate below HYP-010's entire pre-registered band of +0.005 to +0.025. **By the gate's letter this is INCONCLUSIVE and it stays INCONCLUSIVE — nobody relabels a pre-registered verdict after seeing it.** By its substance, the misspecification hypothesis is spent, and the case for spending another two MLB seasons of archiving on this family is now weak. **That is exactly the question APR-0033 puts to the operator, and it is the strongest reason the plan's existing FALSIFIED reroute — moneyline-first, LR, binary target, no distribution fit — deserves to fire.** No third model class was tried, per instruction; the block reported and stopped, which was correct.

**Register parity is closed and the checker had a bug of its own.** T-501 fixed both genuine GG-126-class misses — `APPROVALS_REGISTER.md`'s `APR-0032` row corrected to the 2026-08-21 D1/D2/D3 sign-off (the register was the stale side; document and superseding ADR-0056 were both right) and a new `ADR-0056` row added. The third reported mismatch was **a false positive in the checker itself**: `RESOLVED_PAT = re.compile(r"ACCEPTED|ADOPTED|COMPLETE|selected")` is an unguarded substring match, so ADR-0051's literal Status line `DRAFT — NOT ACCEPTED` matches "ACCEPTED". Latent since the checker's authorship 2026-07-17, ~6 weeks, surfaced only when a DRAFT happened to phrase itself that way. **GG-222 OPEN, LOW — the regex is not yet fixed.** Noisy, not silent: it produces false alarms, it does not hide real misses.

**`OPERATOR_CONSOLE.md` is stale.** It is generated, and on `origin/main` it still reports 4 blocked / 6 broken / 68 accruing = **78 total** against a gap log that now carries **82 entries, 68 OPEN**. Wave 10's three new entries are not in it. Regeneration is folded into 11.3 — **do not hand-patch a generated file.**

**Operator directive, 2026-08-27 — integrate every bucket and all T-4 sub-buckets across the new market lines. Work forward; do not decide in advance what calibrates.** The registry still cannot express this. `ExecutionBand` defines 18 values; cells exist for 6. `MLB_PLAYER_PROP_HITS` carries `T4M_PROJ`/`T4M_ARITH`/`T4M_FLOW`; each of the twelve game-market families carries a single generic `T4_IN_PLAY`. **`T4_STAGED`, `T4_EVENT`, `T4_LINEUP`, `T4_FLOW`, `T4_SENTIMENT`, `T4_PROJ`, `T4_ARITH`, `T4_BOUNDARY`, `T4_CORR` and `T4_EXIT` have zero cells anywhere.** That is 11.2, and T-491's now-landed `BAND_AXIS_ACTIVATION_PROPOSAL_GG172.md` is its design input.

**Distance to live capital:** 1 of 68 cells ACTIVE · every live band at `kelly_fraction=0.0` · zero accrual since 08-15 · epoch-12 figures still unrepaired for the 532 closed + 76 rejected rows · GG-157 fills-vs-book a G6 precondition whose figures were computed on the uncorrected ledger · NFR-03 measured failing at p50 66.955s against a 60s hard rule · C7's drift-alarm ladder never invoked from any production path (GG-125).

---

## Sequencing track — every block, run and unrun

**Status legend:** ✅ merged to `origin/main` · ⚠️ complete but NOT merged · ❌ assigned, never ran · ⏳ in flight · ⬜ not started
**Concurrency rule: fire one wave at a time, never mix waves.**

### ✅ PRIOR PHASE — Waves 4-9 CLOSED 2026-08-26 (T-482 → T-499, nineteen blocks, zero cells graduated)

Full detail: `11_MEMORY_HANDOFF/T499_PHASE_CLOSEOUT_CARRY_FORWARD_2026-08-26.md`, `SESSION_CLAIMS.md`, `DECISION_LOG.md`.

| Wave | Closed | Blocks | Outcome |
|---|---|---|---|
| 4 | 08-24 | T-482 · T-483 · T-484 · T-485 · T-486 | **GG-203 found** — engine alive, 100% order-submission failure since 08-15 |
| 5 | 08-25 | T-492 · T-486 · T-493 | GG-203 **root cause external**, 8 hypotheses ruled out. ADR-0058 PROPOSED — nine `(MarketType, T1)` game cells confirmed scaffolded |
| 6 | 08-26 | T-487 · T-495 · T-496 | Phase 2 gate scored. NHL **15 cells seeded**, only 3 real Kalshi series exist (GG-217). Venue 403 transient, not a jurisdiction flip |
| 7 | 08-26 | T-488 · T-490 | **First nonzero fill haircut.** Props $0.0101/contract; P&L/bet +0.2864 → **+0.2518**, edge survives. Game markets 3-5×, tail ~$0.42/contract. On the **uncorrected** ledger |
| 8 | 08-26 | T-489 · T-491 · T-497 | **NFR-03 FAILS on real data** — p50 **66.955s** vs a 60s hard rule; the session discarded its own passing harness. GG-209 registered. T1 stake wrapper built |
| 9 | 08-26 | T-494 · T-498 · T-499 | **Game-market ruin geometry** — σ MONEYLINE 0.097% / RUN_LINE 0.138% / TOTALS 0.103%, but **fill cost alone drives all three net-negative before model edge.** ADR-0060 drafted. Four ADRs signed |

### ✅ WAVE 10 — CLOSED 2026-08-29 · ran 3-wide · **all three confirmed ancestors of `origin/main` `d58c8dd`**

| # | ID | Task | Status | Outcome |
|---|---|---|---|---|
| 10.1 | T-500 / GG-221 | Land T-487 · pre-register + run the **NB** half of HYP-010 · route box 2.4 | ✅ **merged** (`92a172b`) | T-487 landed (`0ef39ab`, ancestor-check exit 0) after a real 6-file conflict resolution. **EXP-025 pre-registration committed `228a273` BEFORE the NB run `06639f2` — order verified in git.** NB1(phi=2.33): mean **−0.0048**, sd **0.3069**, `n*` **44,220** → **INCONCLUSIVE again**, worse than Poisson. Box 2.4 routed N/A with both verdicts recorded. **GG-221 OPEN · APR-0033 drafted.** No third model class fit — reported and stopped, correctly |
| 10.2 | T-501 / GG-222 | Land T-490 + T-491 · close the 3 register-parity mismatches | ✅ **merged** (`f3bb994`) | T-490 (`075c4ce`) and T-491 (`554b67b`) landed sequentially `--no-ff` — **GG-186 instances #6 and #7 closed.** Two genuine GG-126 misses fixed (APR-0032 row corrected, ADR-0056 row added; register was the stale side). **Third "mismatch" was a checker bug** — `RESOLVED_PAT` substring-matches "ACCEPTED" inside "NOT ACCEPTED", latent ~6 weeks. **GG-222 OPEN, regex not yet fixed.** Hit budget mid-close-out, wrote a stub, resumed |
| 10.3 | T-502 / GG-223 | ADR-0055 **D2** — the 46 stuck-open positions | ✅ **merged** (`3d483c9`) | **46/46 repaired, GG-223 RESOLVED.** Epoch 12 continued, not bumped. Provenance stamps applied. **But the first apply silently reverted** — `t4-mlb.service` flushed its in-memory portfolio copy back over the file. Made durable only by restarting the service post-write under explicit operator authorization. **GG-224 registered OPEN/MEDIUM — the general hazard is unaddressed** |

**The Wave-10 lesson worth carrying: a post-write assertion that passes can still be measuring the wrong moment.** T-502's verification was correct and the repair was still gone minutes later. Durability is a separate property from correctness, and nothing in this repo checked it until now.

### ⬜ WAVE 11 — LEDGER TRUTH UNDER LOAD + THE INTEGRATION BUILD · fire 3-wide

| # | ID | Task | Status | Outcome |
|---|---|---|---|---|
| 11.1 | **T-503 / GG-225** | ADR-0055 **D1 + D3** bundled — 532 closed + 76 rejected — **under the GG-224 protocol** | ⬜ | — |
| 11.2 | **T-504 / GG-226** | **Operator directive:** T-4 sub-buckets across the twelve game-market families. Registry scaffold only | ⬜ | — |
| 11.3 | **T-505 / GG-227** | Install this queue · regenerate `OPERATOR_CONSOLE.md` · fix the `RESOLVED_PAT` regex · draft **ADR-0061**, the external-repair-safety contract for GG-224 | ⬜ | — |

### ⬜ WAVE 12 — CELL-AWARENESS + POST-REPAIR RE-DERIVATION · fire 3-wide · **GG assigned at fire**

| # | ID | Task | Gate | Status |
|---|---|---|---|---|
| 12.1 | **T-506** | ADR-0054 **(a)** follow-ons — replay-harness `market_type=` (PRIORITY: silent wrong output, not an error), `assert_ledger_invariants.py` + `run_band_monitor.py` cell-awareness | 11.1 closed (12.1 edits the assertion script 11.1 must run) | ⬜ |
| 12.2 | **T-507** | ADR-0054 **(b)** — re-key `LogicEpochBoundary.bands_affected` to `(MarketType, band)`; twelve-boundary re-audit, **scope wider when uncertain**, per-boundary scope + justification recorded for all twelve | 11.2 closed | ⬜ |
| 12.3 | **T-508** | Re-run T-488/GG-157's fill-haircut figures against the **repaired** ledger. Named follow-on of ADR-0055 | **11.1 closed and durable** | ⬜ |

### ⬜ WAVE 13 — GATED, DO NOT FIRE YET · **GG assigned at fire**

| # | ID | Task | Gate | Status |
|---|---|---|---|---|
| 13.1 | **T-509** | Wire the nine ADR-0058 T1 game-market measurement cells into the live paper pipeline behind `measurement_stake.py`. **Pre-register the expectation of negative net edge** (T-494) or the result is unfalsifiable after the fact | **GG-203 RESOLVED** | ⬜ |
| 13.2 | **T-510** | Implement whichever NFR-03 remedy ADR-0060 selects; then unblock ADR-0054 **(d)** | **ADR-0060 SIGNED** | ⬜ |
| 13.3 | **T-511** | Implement ADR-0061's external-repair-safety contract in the owning services | **ADR-0061 SIGNED** | ⬜ |

### Value column — which of these actually shorten the distance to live capital

**Yes:** 11.1 (every epoch-12 figure is wrong until it lands) · 12.3 (G6 precondition currently computed on bad data) · 13.1 (the accrual path itself).
**Structural — necessary, not distance-closing:** 11.2 · 11.3 · 12.1 · 12.2 · 13.3.
**Not a block at all — operator only:** GG-203, and now APR-0033. Both outrank everything above.

---

# 11.1 — T-503 / GG-225 · ADR-0055 D1 + D3 UNDER THE GG-224 PROTOCOL

**Start when:** Wave 11 fires. Safe 3-wide. **Owns:** `logs/` ledger + backups, `scripts/t503_*`, `03_DECISIONS/ADR-0055*` (execution record only).

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "t503-adr0055-d1-d3-repair"
scripts/claim_session.sh "T-503: ADR-0055 D1+D3 -- repair 532 closed + 76 rejected under the GG-224 protocol" "T-503 / GG-225"

TIER: STANDARD, budget generously and BUDGET THE CLOSE-OUT SEPARATELY -- T-501 ran out mid-close-out
in Wave 10 and had to write a stub. ONE deliverable.

READ FIRST, in full, and do not work from this prompt's summary of any of them:
  03_DECISIONS/ADR-0055_epoch12-ledger-repair-preregistration.md
  APPROVALS_REGISTER.md's ADR-0055 row (the signed conditions)
  GOVERNANCE_GAP_LOG.md's GG-224 entry (the hazard that nearly voided Wave 10's repair)
  GOVERNANCE_GAP_LOG.md's GG-223 entry (what T-502 actually did, including the workaround)
  scripts/t502_repair_d2_stuck_open.py (T-502's helper -- reuse its shape, do not re-invent it)

SCOPE: **D1 (532 closed positions) + D3 (76 rejected-position mismatches), BUNDLED.** ADR-0055's signed
condition is explicit: one backup, one write, one verification pass -- not three. D2 is DONE (T-502,
46/46). Do not re-touch D2's rows; if you find yourself editing an open position, you have left scope.

*** THE GG-224 PROTOCOL -- THIS IS THE PART WAVE 10 LEARNED THE HARD WAY ***
T-502's first apply had a correct backup, a correct write, and correct post-write assertions -- and the
rows were GONE on a later check, because t4-mlb.service holds the whole portfolio in memory and flushes
that copy back over the file. **A passing post-write assertion proves correctness, not durability.**
  1. FIRST, identify every file your repair will write and, for each, the service that owns it.
     `systemctl` + the source. D2's file was logs/paper_portfolio_mlb_t4.json (t4-mlb.service). D1/D3
     may target that file, logs/t4_mlb_resolved_ledger.jsonl, or both -- DETERMINE THIS FROM ADR-0055
     AND THE DATA, do not assume, and state your finding before writing anything.
  2. For each owning service, plan the coordination BEFORE the write and state it: stop-write-start, or
     write-then-restart as T-502 did.
     *** OPERATOR PRE-AUTHORIZATION, GRANTED 2026-08-29, EARL IGNACIO -- read the scope exactly. ***
     You ARE authorized to restart `t4-mlb.service`, and any other service you identify as owning a
     file this block repairs, WITHOUT stopping to ask. The authorization is scoped to:
       - services you have identified, in writing, as owning a file THIS BLOCK writes;
       - the sole purpose of making THIS repair durable against the GG-224 flush hazard;
       - one restart per service, plus one retry if the first restart does not bring it back healthy.
     It does NOT authorize: restarting anything else; disabling, masking or reconfiguring a service;
     editing any service source or unit file; a stop that is not immediately followed by a start; or
     repeated restart attempts to force a repair through. **State the authorization you are acting
     under in your report, name every service you restarted, and if the scope above does not clearly
     cover an action you believe is needed, STOP and ask rather than reading it broadly.**
  2b. POST-RESTART HEALTH CHECK -- mandatory, this is a live trading service. After each restart
     confirm and paste: `systemctl is-active` and `NRestarts` for the service; that the cycle log has
     written a NEW row after the restart timestamp (the engine resumed evaluating, not merely that the
     unit is up); zero anchored staleness/`game_state_fresh` failures in a `tail -500`; and no new
     journal errors. **If the service does not come back healthy, STOP immediately, restore the backup,
     and report -- do not proceed to the durability check on a degraded service.**
  3. After the write AND the restart, verify durability ACROSS AT LEAST ONE FULL FLUSH CYCLE of each
     owning service -- not once, immediately. Re-read from disk at two separated intervals, the second
     of them provably after at least one flush has occurred, and confirm the `repair_ref`-carrying row
     count is unchanged at both. Report both timestamps, both counts, and your evidence that a flush
     actually happened in between. **A restart makes the revert less likely; it does not remove the
     need to prove durability. T-502's repair looked correct at the moment it was verified too.**
  4. If a revert is observed, STOP. Do not re-apply in a loop. Report it and hand back.

SIGNED CONDITIONS -- non-negotiable, from the operator's ADR-0055 sign-off:
  (i)   Backup written AND VERIFIED before any write. Verified means re-read the backup and confirm
        line count AND a content hash against the original. A backup you wrote but did not read back is
        not a verified backup.
  (ii)  The five pre-registered STEP-2 assertions re-run POST-WRITE AGAINST THE REAL FILE, not only in
        simulation. Simulation passing is not the same as the write having succeeded. Paste pre-write
        and post-write output.
  (iii) Per-row provenance: stamp `repaired_at` and `repair_ref` on every repaired row (D4's required
        mitigation), so repaired rows stay distinguishable from originals without an epoch bump.
  (iv)  **D4: CONTINUE epoch 12. Do NOT bump.** The repair corrects data to what it always should have
        been; no write-path logic changed. Bumping resets every band's clean_epoch_floor and zeroes
        clean_n, destroying the 719-row cohort the repair exists to rescue. If ADR-0055's own D4
        discussion argues for a bump, STOP and report the conflict -- do not silently override it.
  (v)   `python3 scripts/assert_ledger_invariants.py` before and after. Report the delta.
        **The NO_FORMULA (band, assertion) pairs are NOT clean -- they were never checked. Report them
        separately and never fold them into a clean count.**

CONSEQUENCE TO RECORD, not to act on: every epoch-12 figure moves once this lands. T-488/GG-157's
fill-haircut numbers were computed on the uncorrected ledger and must be re-run -- that is Wave 12.3,
already staffed. Name it in your close-out so it is not forgotten; do NOT run it here.

DO NOT: promote assert_ledger_invariants.py to --strict (alarm-only is a standing operator decision).
DO NOT: bump logic_epoch. DO NOT: touch any kelly_fraction. DO NOT: run any clean-vs-corrupted
comparison -- that needs its own pre-registration. DO NOT: quote any epoch-12 P&L or edge figure as
production-authoritative until this block has landed AND its durability check has passed.
DO NOT: edit run_t4_mlb_live.py or any service source -- the GG-224 structural fix is 11.3's ADR and
Wave 13.3's build, not this block's.

SCOPE FENCE: logs/ (ledger + backup), scripts/t503_* (new file, not an edit to an existing production
script), 03_DECISIONS/ADR-0055* (execution record only, not the body).
Self-serialising close-out: rebase onto origin/main immediately before writing GOVERNANCE_GAP_LOG.md
and DECISION_LOG.md. GG-186 ancestor-check before you write any CLOSED row.

REPORT BACK: the file->owning-service map you determined and how; every service you restarted under
the 2026-08-29 pre-authorization and its post-restart health-check output; backup path + line count and hash on both sides; rows repaired vs
532 and 76 expected; the five assertions' post-write output against the real file; the TWO separated
durability re-reads with timestamps and counts; the invariant-violation delta with NO_FORMULA pairs
stated separately; confirmation that logic_epoch was NOT bumped.
```

# 11.2 — T-504 / GG-226 · T-4 SUB-BUCKETS ACROSS THE TWELVE GAME-MARKET FAMILIES

**Start when:** Wave 11 fires. Safe 3-wide. **Owns:** `src/prediction_market_bot/c5_execution/market_type_registry.py`, its tests.

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "t504-t4-subbuckets-game-markets"
scripts/claim_session.sh "T-504: integrate T-4 sub-buckets across the twelve game-market families" "T-504 / GG-226"

TIER: STANDARD. ONE deliverable: registry scaffolding. **NO behaviour change of any kind.**

OPERATOR DIRECTIVE, 2026-08-27, this block's whole reason for existing: integrate every bucket -- and
all T-4 sub-buckets -- with the new market lines. **Work forward. Do not decide in advance which cells
will calibrate edge.** A family or band is never dropped from the build on the strength of one finding;
the engine discovers per-cell what works. This directive reaffirms and widens the 2026-08-21 per-sport
doctrine. If your analysis suggests a family or sub-band is hopeless, REGISTER THE FINDING AND KEEP THE
CELL.

THE GAP, verified live 2026-08-29 -- re-derive it yourself before acting:
  `ExecutionBand` defines 18 values. Cells exist for only 6.
  MLB_PLAYER_PROP_HITS carries T1/T2/T3/T5 + T4M_PROJ, T4M_ARITH, T4M_FLOW  (7 cells)
  NBA_PLAYER_POINTS carries T4_IN_PLAY only                                  (1 cell)
  Each of the TWELVE game-market families carries T1/T2/T3/T4_IN_PLAY/T5     (5 cells each = 60)
  Total 68. **T4_STAGED, T4_EVENT, T4_LINEUP, T4_FLOW, T4_SENTIMENT, T4_PROJ, T4_ARITH, T4_BOUNDARY,
  T4_CORR and T4_EXIT have ZERO cells anywhere in the registry.**
  The twelve families: MLB_MONEYLINE, MLB_RUN_LINE, MLB_GAME_TOTAL, MLB_TEAM_TOTAL, MLB_PARTIAL_GAME,
  NFL_MONEYLINE, NFL_SPREAD, NFL_GAME_TOTAL, NFL_TEAM_TOTAL, NHL_MONEYLINE, NHL_PUCK_LINE,
  NHL_GAME_TOTAL.

DESIGN INPUT, now landed on origin/main -- READ IT BEFORE DESIGNING ANYTHING:
  05_RESEARCH_EXPERIMENTS/ or 04_EXECUTION/ BAND_AXIS_ACTIVATION_PROPOSAL_GG172.md  (T-491, GG-172)
  T-490's --sport axis work through the power calc (box 3.4)
  03_DECISIONS/ADR-0053 section 6.3 -- the accepted delta, and note it says implementation is "a future
  Phase 3 build, not authorized by this acceptance alone."
  03_DECISIONS/ADR-0056 -- sport as a first-class attribute, ACCEPTED 2026-08-21.

**HARD STOP CONDITION, evaluate it explicitly and report your evaluation either way:** if adding these
cells requires anything beyond registry scaffolding -- a ledger schema change, a kill-switch change, a
`risk.py` change, a new correlation group, or any ADR-0053 section 6.3 delta item -- **STOP and report
rather than building it.** ADR-0053's acceptance does not authorize the delta. T-495's NHL seeding is
the precedent for what IS in scope: cells added, `NOT_IMPLEMENTED`, `kelly_fraction=0.0`, nothing wired.

WHAT TO DECIDE AND RECORD PER FAMILY -- this is judgment, not mechanical expansion:
  Which T-4 sub-buckets are STRUCTURALLY MEANINGFUL for a game-level market, and which are
  prop-specific artifacts? T4M_PROJ projects a player's remaining at-bats; there is no obvious
  game-level analogue. T4_LINEUP is lineup risk -- which is precisely the risk game markets do not
  carry. T4_FLOW, T4_EVENT, T4_BOUNDARY, T4_EXIT plausibly do transfer. **Do not guess and do not
  expand blindly to 18 x 12.** For every (family, sub-band) pair you create AND every one you decline,
  record a one-line justification. A cell you decline is a decision that must survive review; a cell
  you create costs nothing but must be defensible.
  If Kalshi does not list a real series supporting a family's in-play decomposition, say so from
  measured evidence -- T-495 checked /series and /events live and deviated from spec rather than
  fabricate a ticker, which was the correct call. Follow that precedent.

MANDATORY: report the before/after cell count and the full status breakdown, imported live, not read
from any document. Every new cell is NOT_IMPLEMENTED with kelly_fraction=0.0. Full test suite green
before close-out -- paste the pass/fail/skip line.

DO NOT: touch any kelly_fraction. DO NOT: promote any cell's status. DO NOT: wire anything into a live
pipeline. DO NOT: edit logic_epoch.py -- the (MarketType, band) re-key is 12.2 under ADR-0054(b).
DO NOT: recommend against a family or a sport on the strength of a finding.

SCOPE FENCE: src/prediction_market_bot/c5_execution/market_type_registry.py and its tests. Nothing else
under src/.
Self-serialising close-out: rebase onto origin/main immediately before writing GOVERNANCE_GAP_LOG.md
and DECISION_LOG.md. GG-186 ancestor-check before you write any CLOSED row.

REPORT BACK: before/after cell counts and status breakdown imported live; the per-family create/decline
table with a justification on every row; your explicit evaluation of the HARD STOP condition; any
family where measured Kalshi series data changed your decision; the test-suite line.
```

# 11.3 — T-505 / GG-227 · INSTALL THE QUEUE, FIX THE INSTRUMENTS, DRAFT ADR-0061

**Start when:** Wave 11 fires. Safe 3-wide. **Owns:** `04_EXECUTION/ACTIVE_QUEUE.md`, `03_DECISIONS/OPERATOR_CONSOLE.md`, `scripts/check_register_parity.py`, `03_DECISIONS/ADR-0061*`.

```
Run the CLAUDE.md session-start protocol in full, INCLUDING Step 4 if you have SSH. Paste outputs.
scripts/new_session_worktree.sh "t505-queue-install-instruments-adr0061"
scripts/claim_session.sh "T-505: install queue, regenerate console, fix RESOLVED_PAT, draft ADR-0061" "T-505 / GG-227"

TIER: STANDARD. FOUR deliverables, smallest first. This is the instrument-maintenance block -- the
Phase's own standing lesson is "before building a new check, verify the checks you already have
actually fire," and three of these are exactly that.

DELIVERABLE 0 -- INSTALL THE QUEUE. Do this FIRST; everything else in this Phase depends on the file
being real. `04_EXECUTION/ACTIVE_QUEUE.md` currently exists ONLY as an uncommitted modification in the
shared `main` checkout (which is ~27 commits behind origin/main). origin/main's copy is the superseded
T-499 version and still shows Wave 9.3 as "RUN NOW" and T-487 as merged -- both false.
  Copy the file from the shared main checkout into your worktree, commit, push.
  Then CONFIRM: exactly one ACTIVE_QUEUE.md exists in the tree (`find . -name "ACTIVE_QUEUE*.md"
  -not -path "./.git/*"`), it is at 04_EXECUTION/, its header reads origin/main = d58c8dd, and its
  Wave 10 table shows all three blocks merged. **Never leave a second copy anywhere** -- stale
  duplicates in 11_MEMORY_HANDOFF/ had the operator reading the wrong file for four exchanges in a
  prior Phase.

DELIVERABLE 1 -- REGENERATE OPERATOR_CONSOLE.md. It is a GENERATED FILE. Run
`scripts/generate_operator_console.py`. **Do not hand-patch it.** On origin/main it reports 4 blocked /
6 broken / 68 accruing = 78 total against a gap log that now carries 82 entries and 68 OPEN -- Wave
10's GG-221/222/224 are missing from it. Report before/after section counts.
  If the regenerated output still disagrees with a directly re-derived gap-log count, that is a
  classification-regex defect in the generator, not a file to patch -- register it and report.

DELIVERABLE 2 -- FIX check_register_parity.py's RESOLVED_PAT. GG-222, OPEN, LOW, found by T-501.
  Current: RESOLVED_PAT = re.compile(r"ACCEPTED|ADOPTED|COMPLETE|selected")
  Unguarded substring match. ADR-0051's literal Status line `**Status:** DRAFT — NOT ACCEPTED.` matches
  "ACCEPTED" and is reported as a parity mismatch. Latent since 2026-07-17, ~6 weeks.
  Fix with a negative lookbehind for a preceding "NOT " (and consider "NOT YET"), plus word boundaries.
  **Add a regression test for the exact ADR-0051 Status string** -- a fix with no test that pins the
  false-positive case is how this comes back.
  Re-run the checker and paste before/after. Expect ADR-0051 to drop out and the count to go to zero;
  if anything else changes, that is a finding -- report it, do not absorb it.
  Amend GG-222 with the resolution. This closes the checker-bug half only.

DELIVERABLE 3 -- DRAFT ADR-0061: external-repair-safety contract for service-owned files. **DRAFT ONLY.
Status PROPOSED. Do NOT implement, do NOT mark ACCEPTED, do NOT edit any service source.**
  The hazard, from GG-224 (OPEN, MEDIUM, discovered by T-502 mid-repair): t4-mlb.service holds the
  entire portfolio object in memory and periodically flushes that in-memory copy back over
  logs/paper_portfolio_mlb_t4.json, read-modify-write against its own state rather than re-reading from
  disk. An external repair with a correct backup, a correct write and correct post-write assertions was
  silently reverted on the next flush. It was made durable only by restarting the service post-write
  under explicit operator authorization.
  ENUMERATE FIRST, from source, not from assumption: every long-running service in this repo that owns
  a shared, externally-repairable file. t4-mlb.service is one. There may be others -- find them.
  PRESENT OPTIONS, DO NOT SELECT ONE. At minimum: (a) re-read from disk before each flush; (b) an
  advisory lock or lockfile the repair path must acquire; (c) a documented stop-repair-start operational
  runbook with no code change; (d) service-owned repair endpoints so external writes never happen.
  For each: blast radius, what it costs, what it does NOT solve, and whether it retires GG-224 fully or
  partially. Give a RECOMMENDATION with reasoning, clearly marked as a recommendation.
  EVIDENCE FOR OPTION (c) YOU MUST WEIGH: the operator granted a scoped restart pre-authorization on
  2026-08-29 for block 11.1, which is a runbook-shaped control working in practice. Assess honestly
  whether that generalises -- a per-repair human authorization does not scale to routine operation, and
  a runbook that depends on the operator being available is a different risk profile from a code fix.
  Do not treat the pre-authorization as evidence that (c) is sufficient.
  Hard Rule 3: a superseding ADR is required before any service change ships. This draft creates the
  decision, it does not make it.

DO NOT: touch any kelly_fraction, any ledger row, or any service source. DO NOT: hand-patch a generated
file. DO NOT: mark ADR-0061 ACCEPTED. DO NOT: close GG-224 -- Deliverable 3 is a draft, not a fix.
DO NOT: close GG-222 outright -- the register-parity half is already fixed, this closes the regex half.

SCOPE FENCE: 04_EXECUTION/ACTIVE_QUEUE.md, 03_DECISIONS/OPERATOR_CONSOLE.md (regenerate only),
scripts/check_register_parity.py + its test, 03_DECISIONS/ADR-0061* (new).
Self-serialising close-out: rebase onto origin/main immediately before writing GOVERNANCE_GAP_LOG.md
and DECISION_LOG.md. GG-186 ancestor-check before you write any CLOSED row.

REPORT BACK: the find output proving exactly one queue file and its committed SHA; console section
counts before/after; the checker output before/after plus the regression test name; ADR-0061's path and
its option table; the full list of services you found that own externally-repairable files.
```

---

## Needs your decision — no terminal can move these

| # | Decision | Status |
|---|---|---|
| (i) | **GG-203 — the Kalshi demo-account order-write fault.** Support ticket or demo-key regeneration. 14 days elapsed at 2026-08-29; every cell accruing zero; ADR-0058's accrual clock has not started; Wave 13.1 is gated on it. **Highest-value item on the board and it is not code.** | **OPEN — nothing competes with it** |
| (ii) | **APR-0033 — HYP-010's INCONCLUSIVE routing.** `00_ADMIN/APR-0033_hyp010-inconclusive-routing-decision-request.md`, drafted by T-500. **New evidence since you last saw this:** the NB refit, pre-registered before it ran and built specifically to handle the overdispersion blamed for Poisson's result, came back **−0.0048 / sd 0.3069 / n\* 44,220** — further negative, wider, same verdict. Two independent fits, both below the pre-registered +0.005…+0.025 band. The plan's own reroute (moneyline-first, LR, binary target, no distribution fit) exists and fires only on FALSIFIED. **My read: the misspecification hypothesis is spent and the reroute should fire. That is a recommendation, not a relabelling — the verdict stays INCONCLUSIVE in the record.** | **DRAFTED, awaiting you** |
| (iii) | **ADR-0060 — which NFR-03 remedy.** (a) shorten the T4 cycle: cheapest, costs API headroom, retires neither GG-038 nor GG-209 — and clears 60s while GG-038 says 60s is itself 12× too slow, i.e. buys compliance without safety. (b) revise NFR-03's bar per band: needs superseding-ADR authority and capital-exposure-derived justification. (c) out-of-band interrupt: cleanest, largest, **the only option creating the primitive GG-209 would reuse.** Your pre-position is **(c)**, overridable by T-498's own cost analysis. **Not urgent in risk terms** — every live band is at `kelly_fraction=0.0` and GG-203 blocks all order writes, so real exposure is zero. G6 precondition, not a live hazard. Gates 13.2 and ADR-0054(d). | **PROPOSED, unsigned** |
| (iv) | **How many of the 68 cells must clear `clean_n ≥ n*` + Tier 1/2 before live capital?** Created by ADR-0057, unanswered by design. With 1 of 68 ACTIVE and G6 now per-cell, "at least one" is a floor a single lucky cell could clear. **11.2 will raise the denominator** — worth setting the bar before it moves. | **OPEN** |
| (v) | **Service restart for the 11.1 repair.** — **GRANTED 2026-08-29.** Scoped in the block text: services identified in writing as owning a file 11.1 writes, solely to make the repair durable against GG-224, one restart per service plus one retry, with a mandatory post-restart health check and a stop-and-restore if the service does not come back clean. Not a standing authorization for service actions generally. | **CLOSED — pre-authorized** |
| (vi) | **T1 game-market measurement given T-494.** — **DECIDED 2026-08-27: proceed and measure.** Condition carried into 13.1: pre-register the expectation of negative net edge. | **CLOSED** |

## DO NOT — standing, carried forward

Don't unpark `SCALING_MANDATE_PARKED.md`. Don't promote `assert_ledger_invariants.py` to `--strict` (alarm-only, operator decision). **Don't touch sizing or any `kelly_fraction` without an ADR — including T1: ADR-0058 authorizes measurement stake at 0.0 and no sizing change.** A nonzero T1 Kelly needs ADR-0048's edge-conditional lookup table and a fresh signature, and T-494's result argues against it. Don't mark ADR-0060 or ADR-0061 ACCEPTED. Don't apply any epoch-12 repair without ADR-0055's conditions AND the GG-224 protocol. Don't quote any epoch-12 P&L or edge figure as production-authoritative until 11.1 lands and its durability check passes. Don't run any clean-vs-corrupted comparison without pre-registering it. Don't re-investigate GG-203 in-repo — the ruled-out list is exhaustive. Don't kill the price-archive cron (`deploy/cron.conf:347-348`) — it feeds T-488 and T-494, not just Phase 2. Don't relabel a pre-registered verdict after seeing it. **Don't recommend against a sport or a family on the strength of a finding — operator doctrine 2026-08-21, reaffirmed 2026-08-27: MLB, NBA, NFL and NHL are all being built; which cells calibrate edge is discovered per-cell by the engine, working forward, never decided in advance.**

**Retired instruction:** "Don't reopen T1." Superseded 2026-08-25. Kept here so a future window does not re-kill it from an old handoff.
