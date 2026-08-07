# ADR-0050: T4M-PROJ Flat $1.00 Measurement-Stake Reactivation

**Status:** ACCEPTED (2026-07-30, DS sign-off = operator, pre-granted in-session). Applied live — GG-046, this session, `logic_epoch.py` 10→11.
**Date:** 2026-07-30
**Author:** Session `session/20260731T020022Z-t4-reactivate`
**Depends on:** ADR-0048 (R1, `kelly_fraction=0` for T1/T2/T3/T4M-PROJ), ADR-0049 (GG-142 signed-edge gate fix — T4M-PROJ bets now pass through a correct CHECK 3/4b before this stake applies), GG-105 (open — edge validity unresolved), GG-045 (Kalshi orderbook depth ceiling), GG-046 (T4 commercial validation gap — this ADR's tracking gap)

---

## 1. Problem

ADR-0048 zeroed `kelly_fraction` for all four bands, including T4M-PROJ, pending GG-105 resolution (edge validity unvalidated). Zero Kelly sizing means every T4M-PROJ evaluation that clears CHECK 3/4b still rejects downstream with `kelly_size_zero` — no bet is ever placed, so no clean T4M-PROJ cohort accrues under the post-ADR-0049 gate. GG-046 (T4 commercial validation) cannot progress without resolved bets to measure, and the longer T4M-PROJ sits fully dark, the longer GG-046 stays open for lack of data rather than for a negative result.

## 2. Decision

Reactivate T4M-PROJ at a **flat $1.00 fixed-dollar measurement stake**, not Kelly-proportional sizing, on every bet that clears the existing gate unchanged (signed edge ≥ `MIN_EDGE_TO_APPROVE`, CHECK 4b direction-consistency, kill switches, single-event cap, min-bet floor, aggregate deployment). This is a deliberate, explicit exception to ADR-0048's edge-conditional rule: GG-105's edge is still unvalidated, and this stake's only job is to accrue a clean, gate-fixed T4M-PROJ cohort large enough to measure that edge — it is not a claim that the edge is real.

**MAIN (T1/T2/T3) is untouched — `kelly_fraction` stays 0 for all three, unchanged by this document.**

### 2.1 Mechanism

`risk.py::evaluate_forecast()` gains an optional `fixed_stake_usd` parameter (default `None`, fully inert for every existing caller). When set, it bypasses Kelly-derived sizing (and the `kelly_size_zero` rejection that would otherwise fire unconditionally with `KELLY_T4=0.0`) and approves at exactly the flat dollar amount, provided the bet has already cleared every other gate check. The approval dict/log record gains a `sizing_mode` field (`"fixed_measurement"` vs `"kelly"`) for traceability. `run_t4_mlb_live.py` is the only caller that passes a non-default value: `T4_MEASUREMENT_STAKE_USD = 1.00`, replacing the prior GG-087 "1 contract at market price" policy.

### 2.2 Why $1.00

Far inside GG-045's estimated $500–$2,000 Kalshi orderbook depth per market — no risk of the stake itself moving the market or distorting fill price. Large enough, at T4's measured throughput (GG-080: 3.67–5.75 bets/game-day, n=2 game-days), to accrue a resolved-bet cohort at a meaningful rate without exposing capital disproportionate to the unvalidated-edge risk.

## 3. Why a new ADR, not an amendment to ADR-0048

Hard Rule 3: ADRs are immutable once accepted. ADR-0048's zeroing decision stands unchanged — `kelly_fraction=0` for T4M-PROJ is still true after this document; this ADR adds an orthogonal, band-scoped sizing path that only engages when a caller opts in, it does not revise or supersede ADR-0048's rationale or table.

## 4. Kill switches and gating — unchanged

Both kill switches (20% permanent max-drawdown, 15% daily circuit breaker) remain live and unaffected — `fixed_stake_usd` only determines the dollar amount of an already-approved bet; it does not bypass either kill-switch check, the single-event exposure cap, or the aggregate portfolio-deployment cap. Evaluation logging is unaffected — every evaluation (approved or rejected) continues to log full forecast context.

## 5. Epoch scope

`logic_epoch.py` epoch 11 (`resolving_gap="GG-046"`, `commit_sha=b7ff2812d5471a33460b3853b53ed63c9bc5ce07`) is recorded with `bands_affected=frozenset({"T4M-PROJ"})`, **not** `ALL_BANDS`. Although `risk.py::evaluate_forecast()` is shared code, `fixed_stake_usd` defaults to `None` and is behaviorally inert unless a caller explicitly passes a value; only `run_t4_mlb_live.py` (T4M-PROJ) does so. T1/T2/T3's code path through `evaluate_forecast()` is bit-for-bit unchanged, so their `clean_n` floor correctly stays at epoch 10 while only T4M-PROJ's clean_n resets to start a fresh, gate-fixed cohort at epoch 11.

## 6. Exit criteria

This is a measurement posture, not a standing sizing policy:

- **Regression to the B2-frontier sizing rule** (ADR-0048's per-band edge-conditional, variance-aware sizing) once T4M-PROJ accrues enough volume for its own power-calc `n*` (APR-0024 standard, `scripts/run_power_calc.py`) to be computed from real clean-epoch mean/stdev.
- **Revert `T4_MEASUREMENT_STAKE_USD` to $0** if, once that `n*` is reached, GG-105's edge fails the power calc (i.e., the measured edge is not statistically distinguishable from zero or is negative) — the same disposition T4M-PROJ was already under before this reactivation.

## 7. Verification

`tests/test_c4_risk.py::TestFixedStakeMeasurement` (4 cases, commit `c9c8263`): `fixed_stake_usd` approves at exactly the flat amount despite `kelly_fraction=0.0` (bypassing `kelly_size_zero`); the bypass is opt-in (`kelly_fraction=0.0` with no `fixed_stake_usd` still rejects `kelly_size_zero`, unchanged from pre-ADR-0050 behavior); `fixed_stake_usd` bypasses sizing only, not the edge-threshold gate (sub-threshold edge still rejects `insufficient_edge`); `fixed_stake_usd=None` (the default) leaves standard Kelly-derived sizing bit-for-bit unchanged for non-T4 callers. 83/83 passing in `tests/test_c4_risk.py`; `tests/test_backfill_logic_epoch.py` + `tests/test_check_epoch_activation.py` 31/31 passing (epoch-11 boundary well-formed, `check_epoch_activation.py --skip-vps` non-blocking stacking warning only, acceptable per §5's band-scoping). Full project test suite was **not** re-run this session under active token-scarcity constraints — see `DECISION_LOG.md` 2026-07-30 entry and the session handoff for this explicit, deliberate deferral. **Superseded by §8 below** — the deferred full-suite run happened in the same branch's next work block and found a second blocking bug this section did not catch.

## 8. Addendum (2026-07-30/31 — operator source-inspection corrections, applied same branch, commit `cafcf74`)

This section follows the established precedent of ADR-0040's dated addendum (Hard Rule 3: original decision/text above is unchanged; this is additive). The operator directly inspected `HEAD=00201fe` post-handoff and found two blocking defects and one pre-registration gap this ADR's original text had not addressed. Verbatim addendum on file in session transcript; summarized disposition below.

**(A) `fixed_stake_usd` plumbing — verified already correct, no code change needed.** The operator's concern (flat stake applied downstream of `evaluate_forecast()` rather than injected as a risk-engine parameter) was already the implementation in commit `b7ff281` — `RiskEngine.evaluate_forecast(fixed_stake_usd=...)` short-circuits `_compute_kelly_size` before `kelly_size_zero` can fire, exactly as required. Confirmed by direct code read; no fix required for this item specifically.

**(A′) A second, more severe blocking bug — found independently, not diagnosed by the operator's own addendum.** `StagedOrderStore.stage_order()` validated `0.0 < kelly_fraction <= 1.0`, rejecting `kelly_fraction=0.0` with `ValueError`. Every T4M-PROJ call passes `kelly_fraction=KELLY_T4==0.0` (unchanged by this ADR — see §2, MAIN and T4M-PROJ's Kelly fraction stays 0 throughout). `run_t4_mlb_live.py`'s `stage_order()` call sits inside a `try/except` that logs a warning and `continue`s on exception, *before* `trader.open_position()` is reached — meaning even with (A) correctly wired, every T4M-PROJ bet would have silently failed to record a paper position, via a completely different failure mode (staging-layer rejection, not risk-engine rejection) than anything either this ADR's original text or the operator's addendum diagnosed. This would have reproduced the exact "empty cohort that looks like a strict gate" failure mode the addendum's Part A warned about, from an unrelated cause. Fixed: bound loosened to `0.0 <= kelly_fraction <= 1.0`. See DECISION_LOG.md 2026-07-30/31 entry and GG-146 (registered) for full detail, including the two pre-existing tests this fix's blast radius required correcting.

**(B) Contract cap — implemented.** `measurement_stake_and_stratum(entry_price)` (`run_t4_mlb_live.py`) computes `stake = min(T4_MEASUREMENT_STAKE_USD, T4_MEASUREMENT_MAX_CONTRACTS * entry_price)`, **not** the addendum's own suggested `floor(stake/price)`-based pseudocode — that formula does not actually yield exactly $1.00 at non-round entry prices (verified: entry_price=0.395 under the floor formula produces a different result than the `min()` form). `T4_MEASUREMENT_MAX_CONTRACTS = 10`, flagged operator-overridable per the addendum's instruction; not changed unilaterally. Measured rationale carried forward from the addendum: on the epoch-8 gate-valid cohort (n=234, MIN_EDGE=0.04), 23% of bets (54/234) price below $0.10, and uncapped flat-dollar sizing at those prices produces ~15x higher per-bet variance (sd $43.90 vs $2.87 capped) carried by a handful of longshot payouts, directly working against this task's own purpose of accruing a clean cohort with tractable `n*`.

**(C) Pre-registered price stratum — implemented.** Every measurement position stamps `entry_price_paid`, `contracts`, and `price_stratum` (`LOW <0.10 | MID 0.10-0.70 | HIGH >0.70`, `T4_PRICE_STRATUM_LOW_MAX=0.10` / `T4_PRICE_STRATUM_MID_MAX=0.70`) at write time in `paper_trader.py::open_position()`, fixed in code before this cohort accrues any data. **Analysis rule, per the addendum's recommended default, fixed now:** the GG-046/EXP-T4-01 headline verdict will be reported on the pooled MID+HIGH stratum; LOW will be reported as a named secondary stratum, neither pooled into the headline figure nor discarded from the record. This rule is not to be revisited once LOW-stratum outcomes are known.

**(D) Verification — all four items complete.** D.1 (E2E `evaluate_forecast()`→approval→`StagedOrderStore.stage_order()` reaching `approved_size==1.00`) and D.2 (`approved_size==0.0` on the Kelly-only path) are in `tests/test_c4_risk.py::TestFixedStakeReachesStagedOrder`; D.3 (contract cap binds, reproducing the addendum's own worked example: entry_price=0.005 → $0.05/10 contracts, not $1.00/200 contracts) is in `tests/test_run_t4_mlb_live.py::TestMeasurementStakeAndStratum`. **D.4 (confirm first live game-day's placed sizes are exactly $1.00 for entry_price ≥ 0.10, and that `logic_epoch` on new rows reads 11, not 8) is documentation-only and cannot be satisfied by CI — it is an open follow-up for whichever session first observes live T4M-PROJ rows post-deploy.** Full project test suite (deferred at the point §7 was originally written) has now been run: **2784 passed, 8 failed, 28 skipped.** All 8 failures are in `tests/test_exp015_t3_simulation.py`, traced to `execution_bands.py`'s `T1_MULTI_DAY.kelly_fraction=0.0` (ADR-0048, predates this branch's divergence point) causing a `ZeroDivisionError`/silently-zeroed-P&L in `run_exp015.py`'s Monte Carlo simulation — confirmed via `git status` that none of the three implicated files are touched by this branch. Pre-existing, unrelated to T4M-PROJ reactivation, registered as GG-146 rather than fixed under this ADR's scope.

**(E) Documentation — this section constitutes the required record for (e) contract cap rationale, (f) the pre-registered stratification rule, and (g) the in-sample/out-of-sample caveat below.**

**(g) This cohort is the FIRST out-of-sample test of the GG-142 gate-valid filter result.** The prior +10.99%/+27.58% ROI readings cited elsewhere in this project's history for the post-GG-142 gate are **in-sample** — the signed-edge threshold was chosen with knowledge of the data it was measured against — and must not be cited as validated edge in GG-046's exit-criteria regression (ADR-0050 §6, "regression to the B2-frontier sizing rule"). The operator's own exit criterion is "regression-analyzed and moved to the B2 frontier"; if that regression treats the in-sample ROI figures as a validated prior rather than treating this flat-stake cohort as the first clean out-of-sample read, the purpose of accruing it is defeated. Any future session running that regression must partition on this boundary explicitly.

**(g) figure correction, 2026-08-05, GG-159:** the "+10.99%" half of this pairing was itself later found code-unverified — `PROJECT_ASSESSMENT_2026-07-30.md`'s §2 headline used a symmetric-vig reconstruction that does not match production's asymmetric cascade (`paper_trader.py::open_position()` L460-466). The code-verified in-sample figure is **+9.65%/n=388** (as-of-2026-07-30 cohort; +9.71%/n=404 current), not +10.99%/n=344. This does not weaken (g)'s caveat — the in-sample/out-of-sample partition still binds regardless of the exact magnitude — it only corrects which number is being partitioned away from. See GG-159, `05_RESEARCH_EXPERIMENTS/VC6_VIG_CASCADE_VERIFICATION_2026-08-04.md`.

## 9. Addendum (2026-07-31 — GG-149, offsetting-position cohort exclusion)

Following the same append-only precedent as §8 (Hard Rule 3: §§1-8 above are unchanged by this section). 161 T4M-PROJ tickers were found holding simultaneous open YES and NO positions — a wash trade under Kalshi's CFTC-DCM rulebook, no manipulative intent (the model re-evaluated live state and took the other side without closing the first position); 141 closed locked pairs / 374 legs, combined -$0.13 on $178.76 stake. This is a measurement-integrity gap this ADR's cohort-purity purpose (§6, §7's E2E verification, §8(g)'s out-of-sample framing) did not anticipate: 374 of 2,015 legs (18.6%) are deterministic wash pairs carrying zero edge information, and would silently contaminate any headline ROI/edge figure computed over the raw ledger.

**(h) Locked-pair cohort exclusion.** A locked pair is defined as two positions sharing the same `kalshi_ticker`, opposite `direction`, with overlapping open intervals (`entered_at` through `exited_at`-or-now). Both legs of every locked pair are **EXCLUDED from the measurement cohort**, retroactively (161 historical tickers, 425 legs across open+closed, tagged via `scripts/tag_locked_pairs_t4_mlb.py`) and prospectively (the `logic_epoch=12` intra-book suppression guard in `run_t4_mlb_live.py`, GG-149, prevents new locked pairs from forming going forward — see `logic_epoch.py` epoch 12 boundary). Exclusion is filter-based only: `locked_pair=true` + `locked_pair_counterpart=<position_id>` stamped onto affected rows in a tagged copy of the ledger; no P&L figure is deleted or altered, and the untagged ledger remains the full, unmodified historical record.

**(i) Suppression-event count is itself a reported metric.** The count of `t4_offsetting_suppressed` (intra-book, SKIP) and `t4_t1_cross_book_direction_conflict` (cross-book, alarm-only) audit events is not merely operational logging — it is reported alongside GG-046/EXP-T4-01's headline figures as a measure of how often the model's live-state re-evaluation would have produced a wash trade absent this guard. A rising suppression rate over time is itself a signal about model stability at short re-evaluation intervals, independent of the edge question §6/§7 exist to answer.

**Scope:** `bands_affected={"T4M-PROJ"}` only, matching every boundary since epoch 9 — MAIN (T1/T2/T3) is untouched by this addendum. DS sign-off: operator, 2026-07-31. See GG-149 (intra-book, resolved this branch), GG-150 (cross-book blocking variant, registered unstaffed — closing a locked pair by force rather than merely alarming requires a separate ADR-0018-governed decision, out of scope here), `logic_epoch.py` epoch 12, DECISION_LOG.md 2026-07-31.

## 10. Addendum (2026-08-05 — T-419, epoch-12 citation rule, GG-159 remediation)

Following the same append-only precedent as §§8-9 (Hard Rule 3: §§1-9 above are unchanged by this section). This addendum exists because GG-159 found a headline figure (`PROJECT_ASSESSMENT_2026-07-30.md`'s T4M-PROJ ROI) had been hand-reconstructed rather than computed from the real cascade, and that error survived one full documentation cycle uncaught. The epoch-12 measurement cohort this ADR created is exactly the kind of number future sessions will want to cite casually — this section makes that structurally hard to get wrong.

**(j) Citation rule — binding, not advisory.** Any session citing epoch-12 T4M-PROJ headline figures (n, P&L, stake, ROI, win rate, top-N concentration, LOW-stratum breakdown, direction-conflict count, sizing conformance) MUST regenerate them at cite time, not copy a number from a prior doc — including this one. The one exception is a citation explicitly scoped "as of `<timestamp>`" for historical/audit purposes (e.g. GG-159's own as-of-2026-07-30 figures), which may be quoted as a frozen point-in-time fact.

To regenerate:
```
python3 scripts/build_t4_resolved_ledger.py --pull    # refresh logs/.vps_portfolio_cache_mlb_t4.json from the VPS
python3 scripts/vc6_vig_cascade_verification.py        # section_epoch12_reproduction() prints the full table
```
Source of truth: `logs/.vps_portfolio_cache_mlb_t4.json`'s `closed_positions`, filtered to `logic_epoch == 12 and band == "T4M-PROJ"` (`section_epoch12_reproduction()`, `scripts/vc6_vig_cascade_verification.py:239-289`). That file is gitignored and mutates as the live cohort resolves — a number copied from a prior session's terminal output is already stale by the time it's read.

**(k) Live reproduction at this addendum's authoring time (2026-08-05T01:xx, cache `last_updated=2026-08-04T06:49:23.560Z`, pulled fresh this session):**

| Metric | 2026-08-04T03:28Z snapshot (operator-supplied, GG-159 reference) | This session's live pull |
|---|---|---|
| n closed | 141 | **148** |
| P&L | +$48.52 | +$51.37 |
| Stake | $122.25 | $129.25 |
| ROI | +39.69% | +39.74% |
| Win rate | 42.6% | 43.9% |
| Top-5-by-P&L share | 71.18% | 67.23% |
| Excl. top 10 by P&L | n=131, −$10.01/$115.70, **−8.65%** | n=138, −$7.16/$122.70, **−5.84%** |
| LOW stratum (<$0.10) | n=30, +167.78% ROI, 16.7% win | n=30, +167.78% ROI, 16.7% win (unchanged — no LOW-stratum bets resolved between snapshots) |
| Both-direction tickers | 0 of 83 | 0 of 87 |
| ADR-0050 sizing conformance | 141/141 | 148/148 |

The excl-top-10 figure moved 2.8pp in roughly 24 hours purely from cohort growth (n=141→148) — this is the concrete demonstration of why (j) requires live regeneration rather than citation of a fixed number: a 7-bet difference materially changed a headline figure. **The −8.84% figure that circulated in the 2026-08-03 strategic review (predating this cohort's growth and using a different denominator approximation) is superseded by both the −8.65% as-of-2026-07-30 figure and this session's −5.84% current figure — do not cite −8.84% going forward.**

Scope: documentation/citation-rule only. No `src/` change, no sizing change, no epoch bump — this section does not supersede §§1-9, it constrains how future sessions report the numbers those sections already govern.

## 11. Addendum (2026-08-06/07 — T-426/GG-166, UNVERIFIED-PENDING-GG-166 flag on §10's citation rule)

Following the same append-only precedent as §§8-10 (Hard Rule 3: §§1-10 above are unchanged by this section). §10(j)'s "regenerate at cite time" rule assumed the underlying outcome data being regenerated from was itself trustworthy. T-426 found otherwise: a shadow agreement check between the live ledger and an independently-built outcome store (T-421) found 44.2% `actual_hits` disagreement / 30.1% derived WIN/LOSS disagreement on the epoch-12 T4M-PROJ clean cohort (156 matched positions), root-caused to `run_t4_mlb_live.py:1519` stamping a UTC-wall-clock `game_date` at bet-entry that `run_resolve_mlb.py::_fetch_mlb_hits()` then consumes as an exact-match resolution join key — silently returning the wrong game's box score. Registered **GG-166 (CRITICAL, OPEN)**.

**(l) UNVERIFIED-PENDING-GG-166 flag — binding, additive to (j).** Regenerating an epoch-12 (or epoch-8, or any pre-fix epoch) T4M-PROJ figure via §10(j)'s procedure satisfies the *citation-freshness* requirement but does **not** by itself satisfy *correctness* — the regenerated number still rests on outcome data GG-166 found may be misresolved against the wrong game. Any citation of an epoch-12 or epoch-8 T4M-PROJ headline figure (including this ADR's own §9/§10 tables above, which predate GG-166's discovery and are not being retroactively edited per Hard Rule 3) must carry an explicit **UNVERIFIED-PENDING-GG-166** flag until T-429 (fix the write-time `game_date` derivation + re-resolve affected historical positions) lands and the cohort is re-verified. This does not retract §10's citation-rule mechanism — it adds a second, independent gate on top of it.

Scope: documentation/citation-rule only. No `src/` change, no sizing change, no epoch bump. See GG-166 (CRITICAL, OPEN), T-429 (unstaffed), `11_MEMORY_HANDOFF/MEMORY_BANK.md` 2026-08-06/07 Last reviewed entry.
