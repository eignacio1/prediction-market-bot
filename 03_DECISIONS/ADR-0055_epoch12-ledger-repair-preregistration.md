# ADR-0055 — Epoch-12 Ledger Repair: Pre-Registered Method + Decision Request

**Status:** ACCEPTED (2026-08-26). D1, D2, D3, D4 all operator-signed — see §9 for the full sign-off record and conditions. **This document's acceptance authorizes the repair in principle; it does not itself constitute execution** — the actual write to `logs/t4_mlb_resolved_ledger.jsonl` is a separate, not-yet-performed follow-on task, gated on the conditions in §9 (pre-write backup, post-write assertion re-run on the real file).
**Date:** 2026-08-20
**Author:** Session T-477 (`epoch12-repair-preregistration` worktree)
**Registers/depends on:** `GG-166` (the original corruption), `GG-170` (authority settled — ticker date is ground truth), `GG-185`/`T-465` (root cause: 8.5-day VPS deploy gap, not a logic bypass), `GG-189` (register-and-stop split: item (a) 46 stuck-open positions, item (2) 76 rejected-position mismatches, outcome-store coverage gap), `GG-193`/`T-470` (closed the outcome-store coverage gap this repair depends on), `ADR-0052` §2.3 (G6 precondition: Kelly sizing and the drawdown kill switch both read `t4_mlb_resolved_ledger.jsonl` — a corrupted ledger corrupts both downstream, not just the reported P&L).
**Scope:** Design + dry-run simulation only. **No write to `logs/t4_mlb_resolved_ledger.jsonl`. No `game_date` correction. No re-resolution. No `kelly_fraction`, `logic_epoch`, or cell-status change.** Output is a proposal, evidence, and a decision request. This ADR stays PROPOSED regardless of how compelling the dry-run numbers look — D1–D4 (§7) are operator decisions.

**Reserved gap:** GG-196 — reserved for this session, not otherwise used.

---

## 1. Context

`T-470` (2026-08-20) extended `t4_mlb_outcome_store.jsonl` to 3,199 rows covering 2026-07-02..08-19, closing the 08-07..08-15 outcome-store coverage hole that had previously blocked any backfill of the 532 corrupted epoch-12 closed positions. Verified fresh in this session (§3, evidence below): all 532/532 join cleanly on `kalshi_ticker` against the store, all 532 resolve `resolved: true`. `T-470` correctly stopped there — it wrote only to the outcome store. No `game_date` was corrected, no position was re-resolved, no P&L was recomputed. This document is the next step: design and simulate the repair. It does not perform it.

**Why pre-registration, not just computation:** a 2026-08-19 strategic review computed a clean-vs-corrupted epoch-12 P&L comparison, found a headline 14x difference (corrupted mean far above clean mean), and had to withdraw it under adversarial review. The split was temporally confounded — clean rows cluster 07-31..08-03, corrupted rows cluster 08-08..08-14, separated by the GG-163 outage — and at n=187 the clean cohort's SE (~0.099) was wide enough that the two means sat inside each other's confidence intervals. A bigger dataset repeats that error harder if the analysis plan is decided after seeing the numbers. This ADR fixes the order: the plan is committed first.

---

## 2. Item (a) — the exact repair rule

For each of the 532 `logic_epoch == 12` closed positions in `t4_mlb_resolved_ledger.jsonl` whose `kalshi_ticker`-derived date disagrees with its stored `game_date`:

1. **Derive the correct `game_date`** from `kalshi_ticker` via `ticker_to_game_date()`, reused verbatim from `scripts/correct_t4_game_dates.py` (the GG-166/T-429 precedent, T-421-validated as 100% reliable across 2,021 tickers). This is the currently-committed version on `origin/main` as of this session's rebase (`16e8ddc`). **Dependency risk, noted not resolved:** `T-472` (claimed 2026-08-20T00:57, unmerged as of this writing) is concurrently reworking this exact function to be "series-agnostic and refusal-only." This repair's simulation uses today's committed regex-based version, scoped to `KXMLBHIT-` tickers only, which is the only series present in this repair's population (confirmed: 0 unparseable tickers in epoch 12, §3). If T-472 lands before D1 is decided, re-run the dry-run against the new function before any `--apply` pass — do not assume the two are equivalent without checking.
2. **Look up the outcome** in `t4_mlb_outcome_store.jsonl` keyed on `kalshi_ticker`, taking `actual_hits` from the store record where `resolved == true`. This is the T-421 decoupled outcome store, whose authority basis (T-437 Task 1: 69/69 fresh live re-fetches matched the store and disagreed with the ledger, 0% "neither") is not re-litigated here.
3. **Recompute `outcome`/`pnl`** using the formula reused verbatim from `scripts/t437_task3_rederive_outcomes.py::recompute()` — the GG-166 precedent for exactly this kind of re-derivation, itself reproduced read-only from `paper_trader.py::settle_position()` (that file is not imported or edited, matching both precedents' scope fence):
   ```
   yes_won = actual_hits >= threshold
   if direction == "YES":
       won = yes_won
       yes_ask = mip + vig / 2
       pnl = size_usd * (1 - yes_ask) / yes_ask if won else -size_usd
   else:  # NO
       won = not yes_won
       no_ask = (1 - mip) + vig / 2
       pnl = size_usd * (1 - no_ask) / no_ask if won else -size_usd
   pnl = round(pnl, 4)
   outcome = "WIN" if won else "LOSS"
   ```
   Field names here match `t4_mlb_resolved_ledger.jsonl`'s own schema (`threshold`, `direction`, `mip`, `vig`, `size_usd`) rather than the precedent script's `paper_portfolio_mlb_t4.json`-native names (`kalshi_threshold`, `mid_price_at_entry`, `vig_at_entry`) — same formula, different source file's field names. Verified in this session against two real ledger rows (one epoch-1 WIN, one epoch-12 corrupted-population WIN) before being trusted: both reproduce the ledger's own stored `pnl` to 4 decimal places from `threshold`/`direction`/`mip`/`vig`/`size_usd` alone.
4. **`size_usd`, `direction`, `mip`, `vig`, `threshold` are taken unchanged** from the existing ledger row. The repair changes what happened (the outcome), not what was staked or offered (the terms). This is why STEP 2's assertion checks total `size_usd` is invariant.
5. **All 532 rows get `game_date` corrected**, even the subset whose `actual_hits` coincidentally matches between store and ledger despite the wrong date (measured in §3: 165 of 532) — a coincidentally-right number resolved against the wrong day's data is still a corrected bookkeeping fact, and downstream joins on `game_date` (e.g. regime-boundary analysis, §4) need it right regardless of whether `pnl` itself moves.

No network calls. No modification to `paper_trader.py`, `run_resolve_mlb.py`, or any production entrypoint. A standalone one-shot tool, matching `correct_t4_game_dates.py` and `t437_task3_rederive_outcomes.py`'s established pattern.

---

## 3. Item (b) — what will be reported, and verification of the reference figures

Reported for the repaired epoch-12 cohort (n=719, `game_date` corrected across all mismatched rows): **n, mean P&L/bet, sd, win rate, and n\*** — n\* per APR-0024: `n* = ceil(((z_alpha + z_beta) * sd / mean)**2)`, one-sided alpha=0.05, 95% power (`z_alpha = z_beta = 1.6448536269514722`).

**Reference figures re-verified this session, independently, before any repair computation:**

| Cohort | n | mean P&L/bet | sd | win rate | n* |
|---|---|---|---|---|---|
| Epoch 12, all (pre-repair, stored values) | 719 | +0.2325 | 1.7412 | 43.3% pooled (44.0% corrupt / 41.2% clean) | 608 |
| Epoch 12, date-consistent subset ("clean") | 187 | +0.0163 | 1.3606 | 41.2% | 75,734 |
| Epoch 12, date-mismatched subset ("corrupted", pre-repair stored values) | 532 | +0.3085 | 1.8517 | 44.0% | — |

All three figures match the task's supplied reference (mean/sd to 4 decimals, n* exactly) — my numbers govern per the task's own instruction, and they agree, so no discrepancy to flag. Population counts also independently confirmed: 2,948 total ledger rows, epoch-12 = 719, 532 mismatched / 187 matched / 0 unparseable. Store-join coverage independently confirmed: 532/532 present in the outcome store, 532/532 `resolved: true`, 0 missing — T-470's claim holds. Of the 532, 367 have a store `actual_hits` that actually differs from the currently-stored ledger `actual_hits` (a real re-derivation, GG166-class in T-437's taxonomy); the remaining 165 coincidentally match (NEITHER-class — `game_date` still corrected, `pnl` unchanged).

---

## 4. Item (c) — the GG-163 outage is a regime boundary, reported split and pooled

The 2026-08-04..08-07 window is the GG-163 ESPN-403 outage (discovery began failing 2026-08-04 23:41 UTC, ran 43.5h+). This boundary is defined by the outage's own calendar dates, not by any feature of this repair's results, so it can be pre-registered without peeking:

- **Pre-outage bucket:** corrected `game_date <= 2026-08-03`
- **Outage/transition bucket:** corrected `game_date` in `[2026-08-04, 2026-08-07]`
- **Post-outage bucket:** corrected `game_date >= 2026-08-08`

STEP 3 reports n / mean / sd / SE / win rate for each bucket individually **and** the pooled 719, side by side. Values will never be silently averaged across the boundary as a single undifferentiated figure — if a bucket's n is too small for a meaningful SE, that will be stated explicitly rather than omitted.

---

## 5. Item (d) — what would make this suspicious

**Anchors:** clean-cohort baseline (date-consistent throughout, presumptively uncorrupted) = +0.0163/bet. Pre-repair corrupted-population stored figure (known artifact of wrong-date resolution) = +0.3085/bet.

**Pre-registered threshold:** a repaired-cohort mean P&L/bet **at or above +0.15/bet** — materially closer to the known-artifact figure (+0.3085) than to the clean-cohort anchor (+0.0163) — is SUSPICIOUS and triggers a leakage audit before being reported as a believable result, not accepted at face value. Candidate explanations to check, in order, if this threshold is crossed: (i) a bug in this repair's own join or recompute logic that reintroduces date-linked bias rather than removing it; (ii) the outcome store itself carries some of the same corruption the ledger does (T-437's 69/69 same-day-refetch validation was against a different, earlier population — not re-validated here for this specific 532); (iii) a real but implausibly large edge, which given `MIN_EDGE_TO_APPROVE = 0.04` and this strategy's documented history (GG-037: anti-predictive edge found against Kalshi in the NBA case; no MLB T4 edge yet demonstrated at gate-grade n) would itself be the least likely explanation, not the first one reached for.

A result **below +0.15/bet** is not automatically "clean" either — SE and n* (§2/§3) still govern whether it is distinguishable from zero. This threshold only gates against accepting an implausibly large number without scrutiny; it does not substitute for the n*/SE read in STEP 3.

---

## 6. Item (e) — what this is, and what it explicitly is not

**This is a measurement-integrity repair.** Its job is to make epoch 12's `game_date` and `outcome`/`pnl` fields describe what actually happened, so that a downstream edge test — the actual commercial question, per `CLAUDE.md` § "The commercial validation gap" — has correct inputs to work from. **Whether epoch 12 has edge is a separate question.** This document does not answer it, and the dry-run's descriptive statistics (§3, STEP 3) are reported as measurement-quality evidence, not as an edge verdict. Repairing the ledger only makes the edge question *askable* against trustworthy data; asking and answering it is out of this document's scope.

---

## 7. Decision request — D1 through D4 (operator decision, not resolved here)

**D1 — Authorize the in-place repair of the 532 closed positions?**
Repair rule is §2, evidence is §3/STEP 3 below. Recommendation: **authorize**, conditional on the dry-run's assertions (STEP 2) passing clean and the STEP 3 report not crossing the §5 suspicion threshold without a satisfactory audit. This is a recommendation, not a decision — D1 is the operator's to make.

**D2 — GG-189 item (a): the 46 stuck-open T4M-PROJ epoch-12 positions (100% mismatch, refused by the current resolve-path guard since 2026-08-16, live paper capital, Kelly-/kill-switch-relevant per ADR-0052 §2.3).**
`scripts/correct_t4_game_dates.py` is the GG-166-era precedent for OPEN positions specifically — its own docstring states the OPEN-position branch is "safe and complete on its own": correcting `game_date` in place on an unresolved position has no `outcome`/`pnl` to re-derive, because nothing has been computed yet. The *next* resolution attempt (via `run_resolve_mlb.py`, already hardened against this exact mismatch since GG-166's B2 guard) will resolve correctly once the date is fixed. **This script is reusable as-is for D2**, unlike the 532-position repair (which needed the new outcome-store join because those positions were already closed against the wrong day). Recommendation: since this population carries live capital and feeds Kelly sizing / the drawdown kill switch today, in its currently-*wrong* state, D2 should not wait for D1 — it is a smaller, independently-safe fix (game_date correction only, no re-resolution needed) and the case for urgency is stronger (ADR-0052 §2.3's exact concern: a corrupted ledger corrupts the kill switch that is supposed to catch it). Still the operator's call, not decided here.

**D3 — GG-189 item (2): the 76 rejected-position mismatches (data hygiene only, no capital).**
No live-capital or Kelly path reads rejected positions. Recommendation: defer — lowest urgency of the three GG-189 populations, no downside to leaving it for a dedicated hygiene pass. Operator's call.

**D4 — After a repair, does epoch 12 continue, or does the reset still bump the epoch?**
Not answered here. The repair makes the cohort *trustworthy*; it does not by itself resolve whether the existing epoch-12 boundary should stand or whether a fresh epoch should start. This interacts directly with `ADR-0054` §4 (per-cell epoch scoping, item (b), itself awaiting sign-off) — if epochs become per-`(market_type, band)` cell-scoped rather than band-scoped, that changes what "the epoch 12 reset" even means structurally. Answering D4 before ADR-0054 §4 is settled risks deciding it on the old, soon-to-be-superseded model. Recommendation: hold D4 open until ADR-0054 §4 is signed, rather than answering it implicitly by default (e.g., by silently treating a successful repair as grounds to continue the epoch). Operator's call.

---

## 8. What this ADR deliberately does not decide

- Whether epoch 12 (or the repaired cohort) demonstrates edge. Measurement-integrity only (§6).
- D1–D4 (§7) — presented with a recommendation each, decided by none.
- `T-472`'s in-flight rework of ticker-date derivation — noted as a dependency risk (§2 item 1), not adjudicated.
- GG-189's outcome-store-coverage-gap sub-item — already closed by T-470, referenced not re-litigated.
- Any `kelly_fraction`, `logic_epoch`, or cell-status value.
- An `APPROVALS_REGISTER.md` row — not needed while Status is PROPOSED, per `ADR-0054`'s identical precedent (§7 of that document).

---

## 9. Sign-off

**Status: ACCEPTED (2026-08-26).** D1–D4 (§7), all signed:

- **D1 — authorized**, conditional on: (i) a backup of `logs/t4_mlb_resolved_ledger.jsonl` written and verified *before* any write; (ii) the five pre-registered STEP-2 assertions (§Addendum A) re-run against the real post-write file, not only the dry-run output — a passing simulation is not itself a passing repair.
- **D2 — authorized**, and may execute first/independently of D1/D3 — `correct_t4_game_dates.py`'s OPEN-position branch is safe and complete on its own (no re-resolution needed), and this population carries live paper capital feeding Kelly sizing / the drawdown kill switch today in its currently-wrong state, per ADR-0052 §2.3's exact concern.
- **D3 — authorized**, bundled with D1 (one backup/write/verification cycle) per §7's own recommendation — no live capital, lowest urgency, no reason for a second write cycle.
- **D4 — CONTINUE epoch 12; do not bump.** The repair corrects data to what it always should have been — no forecasting or execution logic changed — so bumping would destroy the 719-row cohort for no logic-related reason. (Note: §7's own D4 discussion recommends holding the question open until ADR-0054 §4/item (b) is signed rather than answering it by default; ADR-0054 item (b) is signed as of this same close-out (see that ADR's §9), so this is a resolved decision, not an override of the ADR's own text.)

**Required mitigation, attached to D1/D3's execution (not yet performed):** the repair must stamp per-row provenance (`repaired_at` timestamp, `repair_ref` pointing to this ADR/the executing task) on every row it touches, so a future audit can distinguish originally-correct rows from repaired ones.

**Consequence for existing analysis, recorded not re-derived here:** every epoch-12 P&L/n*/win-rate figure computed before this repair executes is provisional and will move once D1 executes. `T-488`/`GG-157`'s fill-haircut figures were computed against the uncorrected ledger and must be re-run post-repair — named here as a required follow-on, not performed in this session.

Nothing in this sign-off itself writes to production ledger state — the write is a separate, gated follow-on task per the note under Status above.

---

## Addendum A — STEP 3 dry-run results (2026-08-20, computed after pre-registration commit `c51e7e4`)

Produced by `scripts/t477_dryrun_epoch12_repair.py` (committed `4745582`). All five STEP-2 assertions passed exactly as specified — 532 changed / 2416 unchanged, every changed row's `game_date` equals its ticker-derived date, zero changes outside `logic_epoch` 12, zero remaining ticker/`game_date` mismatches across every epoch in the repaired file, `size_usd` total invariant at $1,843.0750. Classification breakdown on the 532: 367 GG166-class (outcome/pnl actually changed), 165 NEITHER-class (only `game_date` changed). Source ledger untouched — output lives at `logs/t4_mlb_resolved_ledger.REPAIRED_DRYRUN.jsonl` (gitignored, local).

**Reported exactly per §3/§4's pre-registered plan — n, mean P&L/bet, sd, win rate, n\*, SE alongside every mean, split by regime boundary and pooled:**

| Cohort | n | mean P&L/bet | SE | sd | win rate | n* |
|---|---|---|---|---|---|---|
| Pooled, all epoch-12 (repaired) | 719 | +0.0652 | 0.0552 | 1.4800 | 41.3% (297/719) | 5,580 |
| Pre-outage (`game_date` ≤ 2026-08-03) | 187 | +0.0163 | 0.0995 | 1.3606 | 41.2% (77/187) | 75,734 |
| Outage/transition (2026-08-04..08-07) | 144 | **+0.3037** | 0.1382 | 1.6585 | 50.7% (73/144) | 323 |
| Post-outage (`game_date` ≥ 2026-08-08) | 388 | +0.0002 | 0.0741 | 1.4599 | 37.9% (147/388) | 477,198,245 |

Repaired `game_date` range confirmed: 2026-07-31 to 2026-08-13.

**Where the repaired mean lands:** the pooled figure (+0.0652) sits well below the pre-repair corrupted-population artifact (+0.3085) and above but on the same order as the clean-cohort anchor (+0.0163) — closer to clean than to the artifact, roughly 4x the clean baseline. Note the pre-outage bucket here (n=187, mean +0.0163) is numerically identical to the task's "clean" reference in §3 by construction — it is the same 187 date-consistent rows, unchanged by repair since they were never mismatched.

**Pre-registered suspicion check (§5, threshold +0.15/bet):** the **pooled** figure (+0.0652) does **not** cross the threshold — no leakage-audit trigger at the headline level. The **outage/transition bucket does cross it** — +0.3037, landing almost exactly on the pre-repair corrupted-population artifact figure (+0.3085), with an elevated win rate (50.7% vs. 41.3% pooled / 41.2% clean) that also stands out. Per §5's pre-registered commitment, this is flagged for a leakage/bias audit rather than accepted at face value — not performed in this session (Hard Rule 11: register and stop). **Registered as GG-196**: the 08-04..08-07 outage-window sub-bucket of the repaired epoch-12 cohort (n=144) shows anomalous mean P&L and win rate nearly matching the known pre-repair artifact; candidate causes per ADR-0055 §5(i)-(iii) — most plausibly the outcome store's own coverage/accuracy specifically for games played during the GG-163 ESPN-403 outage window, since that is exactly the window T-470 most recently backfilled — not yet investigated.

**n\* / gate-adequacy finding:** the live governance hook (`governance_scan.sh`'s "SAMPLE ADEQUACY" section, as of this session) currently reports `T4M-PROJ clean_n=719/n*=608 — MET`, triggering a GG-046 alert. That n\*=608 is computed from the **pre-repair, uncorrected** epoch-12 ledger (mean +0.2325, sd 1.7412 — exactly the "all-719" reference row in §3). Using the **repaired** pooled figures instead (mean +0.0652, sd 1.4800), n\* = 5,580 — clean_n=719 is **not met**, by a wide margin (4,861 short). **The gate is not cleared post-repair.** This is itself the central finding of this dry-run: the currently-displayed "MET" status is an artifact of the same corruption this ADR proposes to fix, not a real crossing. This does not, on its own, resolve whether epoch 12 has edge (§6) — it says the sample is not yet large enough to responsibly ask.

**Measurement-integrity framing preserved:** none of the above is an edge verdict. It is a statement about what the corrected numbers say and what they do not yet support.

---

## Addendum B — T-503 execution record (D1+D3 applied, 2026-08-31, under the GG-224 protocol)

**This addendum is an execution record only. It does not amend §1–§9's decision content or reopen D1–D4.**

**File → owning-service map, derived from source before any write (GG-224 protocol step 1):** `logs/paper_portfolio_mlb_t4.json` (the D1/D3 write target — `closed_positions`/`rejected_positions`) is held in memory and periodically flushed by the live `t4-mlb.service` (`run_t4_mlb_live.py`) — the exact GG-224 hazard class. `logs/t4_mlb_resolved_ledger.jsonl` was initially assumed to be the D1 target per ADR-0055 §2's literal text, but mid-session tracing (`build_t4_resolved_ledger.py`, `deploy/cron.conf` line 314) found it is not a source of record: it is wholesale-rebuilt every Monday 14:20 UTC from `paper_portfolio_mlb_t4.json`'s `closed_positions`, by a short-lived cron invocation, not a persistent service. A repair written only to the resolved ledger would have been silently discarded by the next Monday rebuild. Escalated via `AskUserQuestion` per this task's own "STOP and ask if out of scope" instruction; operator selected repairing `closed_positions` directly. This class of hazard — a scheduled batch regeneration overwriting a derived artifact, distinct from GG-224's live-service in-memory-flush class — is registered separately as **GG-228** (new this session; not covered by `ADR-0061`'s §2 hazard inventory, which enumerates only long-running `PaperTrader`-backed processes).

**Backup verification, both files, written and re-read before any write (condition i):**
- `paper_portfolio_mlb_t4.json`: verified-backup pattern per `t503_repair_d1_d3_epoch12.py` (snapshot → write backup → re-read → hash/line-count/byte compare) — backup confirmed byte-identical to the pre-write snapshot before the write proceeded.
- `t4_mlb_resolved_ledger.jsonl` (regenerated proactively post-repair, same tool the weekly cron uses): backup `logs/t4_mlb_resolved_ledger.pre_adr0055_d1d3_regen_20260831T235335Z.jsonl`, SHA256 `f54c594c3fdb3945be586469c62bdadab6952ae0a096f29788ecb8aa528eb1b2`, 2994 lines, 1770668 bytes — confirmed identical to the live file at snapshot time via `cp -p` + re-hash.

**Rows repaired vs. expected:** `closed_positions` 532/532 (D1), `rejected_positions` 76/76 (D3), both stamped `repair_ref = "ADR-0055 D1+D3 / T-503"` per §9's required mitigation. Re-verified post-restart, post-flush: `closed_repaired=532 rejected_repaired=76 closed_total=2994 rejected_total=12126`.

**Service restart + durability (GG-224 protocol steps 3–4):** `t4-mlb.service` restarted under the operator's 2026-08-29 scoped pre-authorization so the corrected file loads from disk on startup rather than being flushed over by stale in-memory state. Durability confirmed across two independently separated re-reads spanning a real flush cycle: file mtime progressed `23:44:30Z → 23:45:51Z → 23:52:56Z` on `paper_portfolio_mlb_t4.json` (file size 20,504,951 bytes at the final read), with a fresh `t4_mlb_cycle_log.jsonl` row appended at `23:52:56Z` confirming the live service continued operating normally post-restart, and both `repair_ref`-stamped counts held unchanged (532/76) across all reads. One read attempt mid-sequence hit a torn read (`JSONDecodeError` on a file caught mid-write) — diagnosed as a non-atomic read timing artifact, not a revert (no evidence any value had changed), and resolved by re-reading with a retry loop rather than treated as a GG-224 stop condition.

**Post-write assertions (condition ii), re-run against the real regenerated resolved ledger, not simulated (`scripts/t503_verify_post_write.py`):** all five ADR-0055 STEP-2 assertions PASSED — exactly 532 rows changed / 2,994 unchanged-set-minus-changed held consistent with the D1 population, every changed row's `game_date` equals its ticker-derived date, zero changes outside `logic_epoch` 12, zero remaining ticker/`game_date` mismatches across the regenerated file (all epochs), `size_usd` total invariant at $1,882.3750 before and after. Resolved ledger post-regen: 2,994 rows (row count unchanged), win=1,536/loss=1,458 (win rate 51.3%), Total P&L +$1.9763, SHA256 `8f79097027e7e869198122754311fcc234eb0276e3133ab1d15b40985e723e49`, 1,770,705 bytes.

**Invariant-check delta, pre vs. post (`scripts/assert_ledger_invariants.py`, condition v — NO_FORMULA pairs reported separately, never folded into "clean"):**

| Metric | PRE (`ledger_invariant_report.PRE_T503.jsonl`) | POST (`ledger_invariant_report.POST_T503.jsonl`) | Delta |
|---|---|---|---|
| T4M-PROJ `[A] ticker_date_matches_game_date` violations | 629 | 21 | −608 |
| `[GG-170 RECURRENCE]` alert, band=T4M-PROJ epoch=12 | present — 608 NEW mismatches at current epoch | **absent** | resolved |
| Cross-path agreement, epoch=12 (ledger vs. T-421 decoupled outcome store) | `hits_agree=52.0% outcome_agree=68.4%` | `matched=765/765 hits_agree=100.0% outcome_agree=100.0%` | fully converged |
| Overall SUMMARY, total violations across 54 band-scoped assertion runs | 630 | 22 | **−608** (exactly 532+76) |
| UNTAGGED band, epoch=3 `[A]` violation (unrelated, pre-existing) | 1 | 1 | unchanged — confirmed out of scope, not touched by this repair |
| NO_FORMULA coverage gap: 14 `(band, assertion)` pairs NOT EVALUATED, incomplete bands T1/T2/T4M-PROJ/UNTAGGED | present | present, identical | **unchanged — reported separately per condition v, not counted as clean either side** |

The delta (−608) matches the repair scope exactly (532 D1 + 76 D3), all out-of-scope bands/epochs/violations are confirmed unchanged, and the residual 21 T4M-PROJ mismatches + 1 UNTAGGED mismatch are pre-existing, out-of-scope items (other epochs / other bands), not new.

**`logic_epoch` not bumped (condition iv):** confirmed — maximum `logic_epoch` present across `open_positions`, `closed_positions`, and `rejected_positions` in the live portfolio is `12`, unchanged, per D4's signed decision (§9) to continue epoch 12 rather than bump.

**Explicitly out of this session's scope, named not performed:** `T-488`/`GG-157`'s fill-haircut figures (Wave 12.3) must be re-run against the now-corrected ledger — not run this session. The 2026-08-31 14:20 UTC `band_monitor_cron.log` C7 WARNING output, computed pre-repair, is now stale and superseded by this repair; it will be naturally corrected by the next scheduled `band_monitor_cron` run, no manual action taken here.

**One unscripted judgment call made this session, flagged for transparency per this project's "surface concerns, let the operator decide" norm:** during outcome-store cross-referencing, a new VPS-local file path (`t4_mlb_outcome_store.T503_local_copy.jsonl`) was used for a local pull of the outcome store rather than overwriting the pre-existing stale local copy — this avoided clobbering a file this session did not own, but was not itself pre-specified in ADR-0055 or the task assignment.

**Resolution status:** D1 and D3 execution is COMPLETE and durability-verified per the GG-224 protocol. This does not reopen or amend D1–D4's decision record (§9) — the decisions stand as signed; this addendum records only that the signed, conditional D1/D3 execution has now occurred and its conditions (i, ii, iii, iv, v) were met.

