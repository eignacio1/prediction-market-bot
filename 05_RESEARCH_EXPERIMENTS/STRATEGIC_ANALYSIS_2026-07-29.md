# Strategic Analysis — MLB Prediction-Market Bot, End-to-End

**Date:** 2026-07-29
**Session:** isolated worktree `session/20260729T054746Z-fable-strategic-analysis` (claim: `analysis-only`)
**Scope:** MLB only. NBA is dark/frozen and out of scope. Multi-sport/multi-venue (G7–G9) out of scope.
**Mode:** Read/analyze only. No code change, no epoch bump, no sizing or kill-switch change, no live action.
**Data as of:** VPS ledger caches pulled 2026-07-29T06:0xZ (`logs/.vps_portfolio_cache_mlb.json`, `logs/.vps_portfolio_cache_mlb_t4.json`); governance scan run same session; `HEAD=406e16d` off `origin/main`.

---

## Executive Summary

**The headline finding is new, unregistered, and it changes the T4 verdict.**

T4's C4 approval gate rejects on `abs(edge) < MIN_EDGE_TO_APPROVE` (`c4_risk_engine/risk.py:594`). The `edge` it receives has **already been direction-resolved** upstream (`run_t4_mlb_live.py:1055-1065`) — at that point a negative value means "this bet is bad *in the direction we chose*," not "this bet is good in the other direction." Taking the absolute value converts a strongly-negative bet into an apparently-strong one. `recommended_direction` is carried in the record but is **never used to validate the edge's sign** (`risk.py:413,505,623` are all write-sites).

The mechanism fires precisely when **vig exceeds the model's raw signal**. Measured on T4's clean epoch-8 cohort (n=518): **239 bets (46.1%) fired on negative direction-effective edge. 239 of 239 have `vig > |model_p − mid|`. 0 of 279 legitimate bets do.** Mean vig on rescued bets 0.1058 vs 0.0407 on legitimate ones.

**Impact — this is the whole T4 loss:**

| Cohort | n | total P&L | P&L/bet | bootstrap |
|---|---|---|---|---|
| T4 epoch-8, full book | 518 | **−$25.67** | −0.0496 | — |
| `abs()`-rescued (edge<0) | 239 | **−$34.99** | −0.1464 | P(loss)=1.000 |
| Gate-valid (edge≥0.04) | 279 | **+$9.33** | +0.0334 | P(profit)=0.892 |

**T4's negative book is not evidence against the live-latency thesis. It is evidence of a broken gate.** Remove the defect and the surviving cohort is positive at 89% bootstrap confidence.

**Everything else confirms the pessimistic reading.** Under the governing APR-0024 standard, both active MLB books are negative on their clean cohorts, and my independent ledger computation reconciles *exactly* with the governance scan (T1: epochs 6+7+8 = 12+36+127 = 175 ✓; T4M-PROJ epoch 8 = 518 ✓):

- **T1/MAIN clean:** n=175, mean **−$0.4112/bet**, cadence 111.4/wk, `cadence_span_days=11.00`.
- `run_power_calc.py`: *"no finite n\* exists to confirm a positive edge from this sample's own effect size."*
- **T1 has already crossed `clean_n=175 > NEG_SIGN_CONFIRM_N=150`. Only `MATURE_CADENCE_SPAN_DAYS=14` holds it back. At current cadence T1's negative sign becomes governance-grade on or about 2026-08-01 — roughly three days from now.**

**The single most important strategic decision:** T1 and T4 are diverging and must be treated as separate decisions with separate verdicts, made in the next ~72 hours.

1. **T1 — stop sizing it.** Its edge signal is anti-predictive where it is worst (threshold=1 cohort is **monotonic-down**: −0.56 → −1.03 → −1.98 per bet across predicted-edge terciles), its negative sign goes governance-grade in ~3 days, and GG-135's MC shows MAIN self-terminates against the 20% drawdown ~100%/yr *even at zero edge*. T-400/A4 already reached the "shift off T1" conclusion from the modeling side; the ruin geometry and the imminent governance-grade crossing independently force the same answer. **ADR-0048 (`kelly_fraction=0`) is drafted, operator-confirmed, and still not applied — T-398 is the live blocker.** Until that edit lands in `execution_bands.py`, the VPS is trading the exact configuration GG-135 says self-terminates.
2. **T4 — fix the gate, then re-measure.** Do not write T4 off on a contaminated book. Fix `abs()`, bump the epoch, and let a clean cohort accrue.

**Three further findings registered this session.** **GG-143** — the T4 process goes silently blind to all in-progress games after any restart landing after 00:00 UTC (GG-058 fixed the in-loop rollover, left the cold-start path open); one observed night lost ~9,700 evaluation records, and 78 historical cold starts landed in the live-game window. **GG-144** — the mandatory Step 3 open-gap scan misses **12 of 26 OPEN gaps**, and the miss is systematically biased toward the most important ones (GG-105, GG-140, GG-046, GG-038) because emphatic entries bold their status marker out of the grep's reach. **And the protocol found none of this session's findings** — four of its checks are quietly stale.

**Commercial question: currently answered NEGATIVELY on the deployed configuration — but T4's answer is confounded by a fixable defect and should be treated as *unanswered pending re-measurement*, not as answered negatively.** That distinction is the difference between "this project has no alpha" and "this project has one broken line of code sitting on top of a possibly-real alpha."

---

## A — Thesis integrity (T1 vs T4 separation)

**Findings.** The T1/T4 separation is genuinely enforced in the architecture, better than most projects manage: `pool_isolated=True` (`run_t4_mlb_live.py:1084`) keeps T4 out of MAIN's bankroll on both entry and close (`paper_trader.py:183-203` docstring is explicit); `logic_epoch.bands_affected` scopes epoch boundaries per band; the governance scan reports the four bands separately; `run_power_calc.py` derives `n*` per band.

Two real leaks:

1. **Shared write path, band-gated formulas.** `paper_trader.py::open_position()` carries a four-branch `if direction/band` cascade (L462-468) with *different vig coefficients per band* — T4M-PROJ `−2.0*vig`, T1 `−1.0*vig`. This is correct today and carefully commented, but it is a shared function where a band-blind edit silently rewrites another band's ledger semantics. GG-077's own history is exactly that failure.
2. **The `abs()` defect (GG-142, new) is in the *sport-agnostic, band-agnostic* C4 gate.** It is architecturally in the one place that is supposed to be the common safety layer. It happens to bite T4 hard and T1 almost not at all (1/175 rows) purely because T4's NO-branch generates negative direction-effective edges in wide-vig markets and T1's doesn't.

**Framing drift:** the calibration-engine framing is holding well in the docs. The one drift I see is that "volume accumulation" has become an implicit goal in the operational cadence (111.4 bets/wk on MAIN) without a live check that the volume is landing in segments where edge could exist — see J.

| | |
|---|---|
| **Assumptions** | `bands_affected` epoch scoping is correctly applied historically; I verified epochs 2/3/4 entries directly but not all 8. |
| **Key Risks** | Shared `open_position()` is a single point of cross-band contamination; the C4 gate defect proves band-agnostic code can carry band-asymmetric harm. |
| **Validation Checks** | `grep -n "bands_affected" logic_epoch.py`; confirm each band's vig coefficient against its own producer's `gross_edge` definition. |
| **Confidence** | **High** on separation being real; **High** on the two leaks. |

---

## B — C1 Ingestion

**Findings.** Semantic oracles are working: `SemanticFloorViolation` count is 1, historical (2026-07-11) — the oracle fired, was caught, is not currently firing. Dashboard OOM probe (GG-118 class) clean: `NRestarts=0`, 0 oom-kills.

**But there is a second silent-dark hole, and it is live (registered here as GG-142's sibling — see Roadmap step 2).**

`run_t4_mlb_live.py:1357-1358` cold-starts with:
```python
_eval_date = date.today()
game_ids: list[str] = _espn_mlb_game_ids_today()
```
GG-058 fixed the *in-loop* UTC-midnight rollover by merging newly-discovered IDs into tracked ones (`_rollover_game_ids`, L460-479, L1407-1416). **The cold-start path has no such merge.** On a restart after 00:00 UTC, in-memory `tracked_game_ids` is empty, so carry-forward has nothing to carry; `_espn_mlb_game_ids_today()` queries the *new* UTC calendar date, whose games are all `STATUS_SCHEDULED`. The process is then blind to every game actually in progress for the rest of that night.

It fails **silently** — `systemctl is-active` = active, no HALT, no alarm, only INFO-level "not polling" lines.

Evidence chain:
- `audit_mlb_t4.jsonl` frozen at `2026-07-29T00:11:30.314Z` while `t4_mlb_live_cron.log` was live at 05:49.
- Restart cluster 00:40 / 00:42 / 00:47 / 00:52, then 05:39.
- The 01:00–04:00 UTC window on 07-29 contains only 3,696 `STATUS_SCHEDULED — not polling` + 231 `No live MLB batter states` lines.
- Prior night (07-28) wrote **10,837** post-midnight records; 07-29 wrote **1,052**. **~9,700 evaluation records lost in one night.**
- Historical frequency by UTC hour of cold start: 00=33, 01=7, 02=5, 04=7, 05=26 → **78 cold starts have landed in the 00:00–05:59 live-game window.**

GG-058's own text *describes* this restart case; its resolution only fixed the in-loop path. This is GG-049-class and it directly attacks the volume-accumulation strategy — it is silently deleting the very sample the G6 gate is waiting on.

| | |
|---|---|
| **Assumptions** | Log-line counts are representative; I did not reconstruct exactly which games were missed per night. |
| **Key Risks** | Sample accrual is being silently throttled; `clean_n` timelines in every plan are optimistic by an unmeasured margin. |
| **Validation Checks** | Compare `audit_mlb_t4.jsonl` record counts per UTC night against ESPN's actual game count; alert on restart-with-empty-tracked-set during 00:00–06:00 UTC. |
| **Confidence** | **High** — the code path, the log evidence, and the restart histogram all agree. |

---

## C — C2 Feature store

**Findings.** `ba_l10_shrunk` (ADR-0047, K=40, per-player `ab_sum`) is live and verified behaviorally active since 2026-07-18T18:07:19Z. **Critically: it is consumed only by T4M-PROJ's live Binomial calculation, not by the frozen T1 model** (`mlb_features.py:63-64`, Hard Rule 4). So GG-105's flagship remediation **does not touch T1 at all** — T1's anti-predictive threshold=1 cohort is untouched by the shrinkage fix and no planned work addresses it.

**GG-141 (registered 2026-07-29, T-400) is worse than "a gap":** `opp_sp_era_l5` / `opp_sp_k9_l5` / `opp_sp_bb9_l5` / `opp_runs_allowed_l10` are **100% blank across all 17,145 rows**, and `opp_sp_is_known` is hardcoded `0.0`. For a hit-props model, opposing-pitcher quality is arguably the single largest exogenous driver of a batter's hit probability. The model is blind to it. This is the most plausible *available* explanation for why rank-ordering is inverted: the feature set omits the dominant confounder, so the model's confidence ordering tracks something other than true hit probability.

No leakage found: features are rolling-window (`ba_l10`, `bb_rate_l10`) computed pregame; `h_so_far_at_entry`/`ab_remaining_at_entry` are live-state and null on T1 rows as expected.

| | |
|---|---|
| **Assumptions** | That opposing-pitcher quality would materially improve rank ordering — plausible and standard in baseball modeling, but **untested here**. Marked Assumption. |
| **Key Risks** | Continuing to test *transforms* and *interactions* of an incomplete feature set (A1/A2/A3 all did) cannot recover a missing dominant covariate. |
| **Validation Checks** | Backfill `opp_sp_*` for the resolved cohort and re-run the D1 what-if harness before any further model-class work. |
| **Confidence** | **High** that the columns are blank; **Medium** that filling them is the fix. |

---

## D — C3 Forecasting / calibration

**The question asked was: is there ANY cohort/band with a real, monotonic, positive edge? Stated plainly: no — but there is one cohort with a real, *flat*, positive edge, and that matters.**

Edge-tercile monotonicity, clean cohorts, `fee_net_edge` axis (verified as the true direction-effective edge: `|gross_edge| − fee − vig` reproduces the stored field exactly):

| Cohort | n | T1 | T2 | T3 | Verdict |
|---|---|---|---|---|---|
| MAIN clean (all) | 175 | +0.442 | −1.313 | −0.364 | non-monotonic (noise) |
| MAIN, threshold=2 | 80 | +1.132 | −0.848 | +1.251 | non-monotonic, positive total (+$42.41) |
| **MAIN, threshold=1** | 95 | −0.560 | −1.025 | **−1.977** | **MONOTONIC-DOWN — anti-predictive** |
| T4 epoch-8 (all) | 518 | −0.098 | −0.088 | +0.036 | monotonic-up *(artifact — see below)* |
| **T4, gate-valid only** | 279 | +0.040 | +0.023 | +0.038 | **flat, uniformly positive** |

Two things to read carefully:

1. **T4's apparent "monotonic-up, predictive" result is an artifact of the `abs()` defect.** The bottom tercile was populated by the rescued negative-edge bets. Restricted to gate-valid rows the ordering is **flat** (+0.040 / +0.023 / +0.038, spread −0.0025). So **T4's edge signal has no rank-ordering power — but its *gate* works.** Bets that genuinely clear 0.04 are profitable roughly uniformly, regardless of predicted magnitude. That is a real, if unglamorous, finding: T4 has a working *filter* and a non-working *scaler*.
2. **MAIN's threshold=2 positive total is not evidence of a working edge signal** — the ordering is non-monotonic and the bootstrap is inconclusive (95% CI [−1.73, +2.72], P(>0)=0.687). It is a directional/structural mispricing the model happens to be on the right side of, not a magnitude signal.

Significance:
- MAIN threshold=1 negative: 95% CI [−3.16, +0.88], **P(mean<0)=0.877**.
- MAIN threshold=2 positive: **P(mean>0)=0.687** — not actionable.
- T4 gate-valid positive: 95% CI [−0.020, +0.086], **P(mean>0)=0.892** — the strongest positive signal in the system, and still short of conventional thresholds.

**GG-140's structural finding is confirmed and I would extend it.** Temperature scaling, Platt, and isotonic are all strictly monotonic transforms and cannot repair inverted rank ordering by construction. A2/A3 (2026-07-24) and T-400/A1–A3 (2026-07-29) closed the raw-feature and one-step-interaction classes too. **What remains is not "a better transform" — it is a missing covariate (C/GG-141) or a genuinely different model class.**

| | |
|---|---|
| **Assumptions** | `fee_net_edge` is the correct ranking axis — verified algebraically against both the ledger formula and the gate formula, which are identical. |
| **Key Risks** | T4's flat-positive result rests on n=279 with a CI that includes zero; it is a hypothesis worth protecting, not a proven edge. |
| **Validation Checks** | Re-run all terciles on a post-`abs()`-fix epoch; backfill `opp_sp_*` and re-run D1. |
| **Confidence** | **High** on the tercile measurements; **Medium** on T4 gate-valid positivity (CI crosses zero). |

---

## E — C4 Risk / sizing

**Findings.** Hard limits (`risk.py`): `DEFAULT_KELLY_FRACTION=0.25` (L97, inert for MLB — `execution_bands.py` per-band values govern), `MIN_EDGE_TO_APPROVE=0.04` (L100), `MAX_DAILY_LOSS_PCT=0.15` (L113), `_HARD_LIMITS` = `max_single_event_exposure_usd=500.0`, `max_drawdown_pct=0.20`, `max_portfolio_deployment_pct` (L134-139).

Live `kelly_fraction` (`execution_bands.py`, **not** `c5_execution/execution_bands.py` — the CLAUDE.md protocol path is stale): T1_MULTI_DAY 0.061 (ADR-0040), T2_SAME_DAY 0.13, T3_PRE_TIP 0.07, T4M-PROJ 0.10 ACTIVE, T4M-ARITH 0.10 BLOCKED, T4M-FLOW 0.08 BLOCKED.

**The gate defect is a C4 defect, and it is the most severe risk-engine finding.** CHECK 3 is the *only* edge gate. `abs()` makes it structurally incapable of rejecting a confidently-wrong bet — and the worse the bet, the more certainly it passes. A direction-effective edge of −0.1359 sails through.

**Compounding: `VIG_CEILING=0.30` was calibrated on contaminated, pre-bidirectional data.** Its own comment (`run_t4_mlb_live.py:155-159`) sources it from **2026-07-02** production data — *before* GG-087 made the engine bidirectional (epoch 2, 2026-07-05). On that date only YES bets existed. The ceiling has **never been recalibrated for the NO side**, which is exactly where the defect lives and where wide vig does the damage. Max vig among rescued bets is exactly 0.300 — the ceiling is binding but set far too loose to help.

**T4 drawdown accounting — verified correct, with a residual caveat.** I initially suspected T4's frozen `bankroll_usd=1000.00` had blinded its kill switch. Traced: `_ledger_realized_pnl()` (`paper_trader.py:169-181`) sums **all** closed positions with **no `pool_isolated` filter**, so T4's drawdown *is* computed from its own realized P&L. The frozen bankroll is by design (`_ledger_bankroll()`, L183-203). **Residual concern retained:** `drawdown` divides by full-book `initial_bankroll` ($1,000) while only `bankroll_usd * T4_BAND_WEIGHT` is ever at risk (L627), so the 20% trigger sits at a higher effective percentage of T4's actual trading capital than the number implies.

**GG-135's ruin geometry verified against the source doc** (`MC_EMPIRICAL_BOOTSTRAP_2026-07-22.md`): MAIN hits 20% DD ~100% within a year **even at zero edge** (L57) — variance × cadence alone does it. T4 full-history cohort: **P(kill) 0.0% at 30d and 365d** (L64). This is the quantitative core of the T1-vs-T4 divergence: **MAIN is ruin-limited; T4 is edge-limited.** B2's frontier confirms Kelly-fraction reduction is the only lever with enough leverage (variance scales quadratically in stake, only linearly in cadence).

**T-398 is the live blocker.** ADR-0048 (`kelly_fraction=0` default for T1/T2/T3/T4M-PROJ) is drafted and operator-confirmed but **not self-executing** — DS sign-off and the `execution_bands.py` edit are both outstanding. Until it lands the VPS trades the configuration GG-135 says self-terminates ~100%/yr.

| | |
|---|---|
| **Assumptions** | ADR-0048 has not been applied — verified against live `execution_bands.py` values this session. |
| **Key Risks** | Every day of delay on T-398 is a day at a sizing GG-135 says is not survivable; the `abs()` defect makes the *worst* bets the *most likely* to be approved. |
| **Validation Checks** | Re-read `execution_bands.py` kelly_fractions before/after ADR-0048; recalibrate `VIG_CEILING` on post-fix bidirectional data. |
| **Confidence** | **High** throughout. |

---

## F — C5 Execution

**Findings.** **Fill realism is materially worse on MAIN than anyone's analysis assumes: 52 of 475 MAIN positions (10.9%) carry a FAILED Kalshi order status** (observed example: `"failed: HTTP 410"`) versus 0.5% on T4. These are recorded in the ledger as positions with P&L. In paper mode that is harmless bookkeeping; **at G6 with live capital it is a 10.9% phantom-fill rate**, and every P&L figure computed from this ledger silently includes bets that would not have filled.

**Stale unresolved positions bias realized P&L:** MAIN carries 39 opens dating to 2026-07-01 (27 days); T4 carries **429 opens — 19.6% of all T4 positions** — back to 2026-07-04. A resolution pipeline that leaves a fifth of the book unresolved means realized-P&L cohorts are a non-random subsample. Direction of bias unknown and unmeasured.

**The T4 "market is slow" thesis is asserted, not evidenced.** I found no artifact in the repo that measures market price movement *after* a T4 fire — no post-fire price-path capture, no realized-latency distribution, no comparison of MIP at t vs t+n. The thesis is architecturally embedded (45–90s re-evaluation cadence) but has never been directly tested. Given D's finding that T4's edge signal is *flat* (filter works, scaler doesn't), the latency thesis specifically deserves a direct test rather than continued indirect inference from P&L.

**ADR-0016 fee handling is correct**: `fee_per_contract = 0.07 * mid * (1 − mid)` (`paper_trader.py`), applied symmetrically, and verified to reproduce stored `fee_net_edge` exactly.

| | |
|---|---|
| **Assumptions** | `kalshi_order_status: "failed: …"` means no fill; the ledger nonetheless books P&L on these rows. |
| **Key Risks** | 10.9% phantom fills + 19.6% unresolved = the ledger both overstates executability and non-randomly samples outcomes. Both inflate confidence in every P&L number in this document, including mine. |
| **Validation Checks** | Recompute all cohort P&L excluding failed-order rows; age-out or force-resolve stale opens and re-measure. |
| **Confidence** | **High** on the counts; **Medium** on materiality (paper mode masks it today). |

---

## G — C7 Monitoring

**Findings.** **The Brier/ECE calibration ladder is not wired to anything live.** `grep` finds it only in `run_exp*.py` experiment scripts, `train_and_save_model.py`, and `run_sensitivity_tests.py` — **zero references in `scripts/*.sh`, `.claude/hooks/*.sh`, or any cron/systemd unit.** GG-125 flagged this; it remains true. **There is no live calibration monitoring on a system whose entire thesis is calibration.** A calibration collapse would be detected only when someone runs an experiment by hand.

Monitors that *do* work: semantic floor oracle (T1), contamination/staleness halt (T4), the governance scan's per-band `clean_n`/`n*` reporting, the dashboard OOM probe (added post-GG-118).

**Unmonitored failure modes, ranked:**
1. **Cold-start blindness (B)** — no alarm exists; `is-active` reports healthy throughout.
2. **`abs()` gate defect (E)** — logged as `insufficient_edge` never fires for these rows, so the audit trail shows them as *legitimately approved*. The monitoring cannot distinguish them.
3. **Calibration drift** — no live Brier/ECE.
4. **Resolution-pipeline stall** — 429 stale T4 opens accumulated with no alert.
5. **Failed-order rate** — 10.9% on MAIN, no threshold or alert.

GG-098's warn-only discipline is being observed (monitors warn, don't halt) — appropriate at paper stage, but items 1–2 above wouldn't even warn.

| | |
|---|---|
| **Assumptions** | My grep covered all invocation surfaces (`scripts/`, `.claude/hooks/`, systemd units referenced in the protocol). |
| **Key Risks** | The system's self-reported health is structurally unable to detect its two most material live defects. This is the audit-directive thesis ("self-reported health > reality") recurring. |
| **Validation Checks** | Wire the Brier/ECE ladder into the nightly cron; add a cold-start guard alarm; add stale-open and failed-order thresholds. |
| **Confidence** | **High.** |

---

## H — P&L and commercial validation

**Both books, clean cohorts, independently computed and reconciling exactly with the governance scan:**

| Band | clean_n | raw_n | mean P&L/bet | total | cadence |
|---|---|---|---|---|---|
| T1 (MAIN, ep 6-8) | **175** | 434 | **−$0.4112** | −$71.96 | 111.4/wk |
| T2 | 0 | 2 | — | — | — |
| T3 | 0 | 0 | — | — | — |
| T4M-PROJ (ep 8) | **518** | — | **−$0.0496** | −$25.67 | — |

`run_power_calc.py` verdict on T1: *"observed mean P&L/bet=−0.4112 ≤ 0 — no finite n\* exists to confirm a positive edge from this sample's own effect size. Negative sign NOT YET governance-grade: cadence_span_days=11.00 < MATURE_CADENCE_SPAN_DAYS=14."*

**T1 has already crossed `clean_n=175 > NEG_SIGN_CONFIRM_N=150`. The only remaining gate is the 14-day cadence span, currently 11.00. At current cadence this crosses on or about 2026-08-01.** That is a dated, forced decision point.

MAIN's per-epoch P&L/bet sign-flips wildly across epochs (+0.786, −1.204, −0.091, −2.049, +1.127, −0.692) — **variance-dominated, no stable edge**, corroborating GG-098.

**T4's per-bet magnitude is ~14x smaller than MAIN's**, corroborating the "T4 is edge-limited, not ruin-limited" claim from the opposite direction.

**Is the commercial question answered, unanswered, or answered negatively?**

- **T1: answered negatively**, pending only a ~3-day formality. The clean cohort is negative, the edge signal is anti-predictive on its largest sub-cohort, three remediation classes are exhausted, and the ruin geometry kills it independent of edge. I would not expect T1 to be rescued by anything short of the missing `opp_sp_*` covariate.
- **T4: NOT answered — the measurement is contaminated.** 46.1% of the cohort should never have been placed. The gate-valid subset is *positive* at P=0.892. **Reporting T4 as "negative edge" is currently incorrect**, and any document that does so (including `MC_EMPIRICAL_BOOTSTRAP_2026-07-22.md`'s "epoch-8 edge is negative on both books", L22) is describing a defect, not a thesis.

**EXP-017 / T4 validation (GG-046):** T4 still has no independent validation track distinct from its P&L ledger. Given the contamination, standing up that track *after* the gate fix is the only way to get a clean read.

| | |
|---|---|
| **Assumptions** | Governance scan's `clean_n=518` for T4M-PROJ is authoritative (local `run_power_calc.py` reported 0 because the scp'd T4 cache landed at a path its `--t4_ledger` arg doesn't consume — confirmed twice independently). |
| **Key Risks** | Every P&L figure here inherits F's 10.9% phantom-fill and 19.6%-unresolved biases. |
| **Validation Checks** | Re-run power calc post-gate-fix on a clean epoch; exclude failed-order rows and re-measure. |
| **Confidence** | **High** on T1 negative; **High** on T4 being contaminated; **Medium** on T4 being positive once fixed. |

---

## I — Governance

**26 OPEN gaps — not the 14 the Step 3 scan surfaces.** See GG-144 below. Ranked by materiality for MLB:

1. **GG-142 (new, this session)** — `abs()` edge gate. Live, silent, 46% of T4's book. Highest severity.
2. **GG-143 (new, this session)** — T4 cold-start blindness; silent sample destruction; ~9,700 records in one night; 78 historical occurrences.
3. **GG-135** — MAIN self-terminates ~100%/yr at any positive Kelly. Mitigation drafted (ADR-0048), **not applied** — T-398.
4. **GG-105 / GG-140** — anti-predictive rank ordering; recalibration class closed; feature/model-class rework is the open lever.
5. **GG-141** — `opp_sp_*` 100% blank. Unstaffed. Plausibly the *cause* of #4.
6. **GG-004** — commercial validation; now effectively decided negatively for T1 (see H).
7. **GG-045** — depth ceiling; not yet binding at paper sizing.
8. **GG-046** — T4 independent validation track absent.
9. **GG-124** — `clean_n` dip; self-resolving, now resolved in practice (T1=175, T4=518).

**ADR immutability (Hard Rule 3) is being respected** — ADR-0035's stale header was corrected in place (a status field, not a decision), ADR-0043/0047/0048 supersede rather than rewrite. Good discipline.

**GG-144 (new, this session) — the Step 3 open-gap scan is systematically blind to the most important gaps.** Step 3 runs `grep -n "| OPEN"`. Two Status formats coexist in the log: plain `| Status | OPEN — …` and emphatic `| Status | **OPEN — …`. The grep matches the first and not the second. Measured against `origin/main` immediately pre-session, counting anchored `| Status |` lines: **14 match, 12 do not — 26 gaps are genuinely OPEN and the protocol surfaces 14.** (Post-session: 17 plain + 12 bolded = 29, this session's three registrations all written plain.)

**Numeric correction, recorded rather than silently fixed:** an earlier draft of this section stated "12 of 28, protocol reports 16." That came from `grep -c "| OPEN"`, which counts every *line* containing the substring — including narrative prose inside other gaps' status cells — rather than anchored Status lines only. The anchored count is 26/14. The hidden set and the 12-hidden figure are unaffected; only the denominator moved. Flagged here because a strategic document that miscounts the thing it is criticising the protocol for miscounting has no standing to make the criticism.

**This is a recurrence, not a first discovery — which is the more serious finding.** The identical bug was found and fixed in `.claude/hooks/governance_scan.sh` on 2026-07-16 as **GG-122** ("OPEN-gap grep only matched literal `| OPEN`, undercounting bold-prefixed Status cells, 10 vs. true 19"), and the caveat was explicitly surfaced again on 2026-07-15 in T-370's `MEMORY_BANK.md` entry ("the grep methodology misses bold-prefixed `**OPEN` Status cells, undercounting the true OPEN backlog"). Both times the fix went into the *hook* and the *observation* went into a narrative log — and neither propagated to CLAUDE.md's Step 3, the one place the protocol declares mandatory. The hook has been format-tolerant for 13 days while the mandatory protocol command it shadows has not. That is the failure worth fixing: a known-and-named defect was repaired in the convenient copy and left standing in the authoritative one.

**The bias is the mechanism, and it inverts the check's purpose.** Routine gaps get a terse `OPEN.`; gaps the author considers severe get emphatic bolded status narratives — so the formatting that signals importance is exactly what removes the entry from the scan. The hidden set is: GG-037 (calibration collapse / inverted edge), **GG-038 (T4 kill-switch SLA 12× too slow for continuous evaluation — a live Hard Rule 6 tension)**, GG-039, GG-040, GG-041, GG-045 (depth ceiling), **GG-046 (T4 commercial validation untested)**, **GG-105 (the anti-predictive finding — the single most consequential open gap in the project)**, GG-125 (Brier/ECE never invoked), GG-132, GG-138, **GG-140 (recalibration class exhausted)**.

A session that trusted Step 3's output would conclude that GG-105, GG-140, and GG-046 are not open. This is the same shape as GG-108 (a Step 4 grep pointed at a nonexistent filename, returning empty output indistinguishable from healthy) and GG-001 (a stub that survived four gate clearances because no scan existed): a check that returns a clean-looking answer while being structurally unable to see what it was written to catch.

**Other process gaps found in the protocol itself:**
- Q4's grep targets `def approve` / `def execute` — **neither exists**. The interface-evolution check is partially a no-op.
- Q1's `execution_bands.py` path is documented as `c5_execution/execution_bands.py`; the file is at `src/prediction_market_bot/execution_bands.py`.
- **GG-138 fired exactly as registered** during this session: `run_power_calc.py` → `FileNotFoundError: logs/.vps_portfolio_cache_mlb.json` on a fresh worktree (missing `mkdir`, masked by a bare `except` in `pull_vps_cache`). Worked around manually. Still unfixed.
- Live T-400 claim row in `SESSION_CLAIMS.md` has no closure entry despite its work having landed on `origin/main`.

| | |
|---|---|
| **Assumptions** | 28 is the true OPEN count, from `grep -c "^| Status | OPEN"` + `grep -c "^| Status | \*\*OPEN"`; I verified the 12 hidden entries individually by walking back to each `### GG-` header. |
| **Key Risks** | The session-start protocol — the project's primary defense — now has **four** verified stale/no-op checks (Step 3 grep, Q4 grep, Q1 path, GG-138). It found none of this session's four findings. |
| **Validation Checks** | Repair the Step 3 grep to `^\| Status \| \*{0,2}OPEN` and add a count-reconciliation assertion; repair Q1/Q4; fix GG-138's `mkdir`; close T-400's claim. |
| **Confidence** | **High.** |

---

## J — Market strategy (MLB-only)

**Segment findings, clean cohorts:**

**MAIN (n=175):**

| Segment | n | win rate | P&L/bet |
|---|---|---|---|
| threshold=2 | 80 | 0.650 | **+0.530** |
| threshold=1 | 95 | 0.305 | **−1.204** |
| direction NO | 159 | 0.484 | −0.228 |
| direction YES | 16 | 0.250 | −2.236 |
| entry price 0.3–0.5 | 39 | 0.769 | **+2.548** |
| entry price 0.5–0.7 | 65 | 0.308 | **−1.595** |

**Two structural observations that matter more than the numbers:**

1. **MAIN has zero day-part diversity — all 175 clean bets entered at 11:00 UTC.** It is a once-daily pregame cron. "Day-part edge" is not measurable for T1 and never will be under the current schedule. Any strategy discussion premised on selecting favourable day-parts for T1 is inapplicable.
2. **For NO bets, win rate should *increase* with YES-side mid price. It doesn't** — it goes 0.537 (≤0.3) → 0.769 (0.3–0.5) → 0.308 (0.5–0.7) → 0.300 (>0.7). The collapse above 0.5 is another rank-inversion signature, consistent with D.

**T4 (n=518):** 77% of the book is NO, and **NO is the losing side** (−0.090/bet vs YES +0.087/bet). Hours 23 and 02 UTC are marginally positive; the bulk (n=340) sits at hour 00. Entry price >0.7 is the best bucket (+0.199/bet, n=47). **But all of this is confounded by the `abs()` defect, which is NO-specific** — 239 of 400 NO bets were illegitimate. **The apparent "NO side is bad" conclusion is very likely a restatement of the gate defect, not a market fact.** I would not act on any T4 segment finding until the gate is fixed.

**Efficiency-gradient fit:** the traded markets *are* the thin ones the strategy targets — KXMLBHIT player props on mid-week regular-season games, not primetime marquee events. Observed vig of 0.04–0.30 confirms genuinely thin books. **This is the strategy operating where it intended to.** The problem is not venue selection.

**GG-045 depth fit:** at paper sizing ($20 typical MAIN stake, ~$0.50 T4) against $500–$2,000 depth, the bot is far inside the market. Depth is not currently binding and won't be until well past G6.

**Is volume accumulation pointed at the right segments?** **Partially, and one segment is actively harmful.** MAIN's threshold=1 cohort is monotonically anti-predictive and is 54% of MAIN's clean volume — the system is accumulating its largest sample in the one segment where the signal is provably inverted. That is not neutral data collection; it is buying negative-information volume at −$1.20/bet.

| | |
|---|---|
| **Assumptions** | `kalshi_threshold` 1/2 correspond to 1+/2+ hit lines; `mid_price_at_entry` is YES-frame (verified consistent with the edge algebra). |
| **Key Risks** | Every T4 segment number is confounded by GG-142; acting on them now would encode the defect into strategy. |
| **Validation Checks** | Re-run all T4 segments post-gate-fix; test whether MAIN threshold=2-only is viable as a restricted strategy (currently P(>0)=0.687 — insufficient). |
| **Confidence** | **High** on MAIN segments; **Low** on T4 segments (confounded). |

---

## K — Strategic Synthesis

### 1. Where is the edge, really?

**T1/MAIN: no edge, and the search space is nearly exhausted.** Negative on the clean cohort, anti-predictive on its largest sub-cohort, three remediation classes closed (monotonic transforms per GG-140, raw features and one-step interactions per T-400), and ruin-limited regardless of edge per GG-135. The one untested lever is the missing `opp_sp_*` covariate (GG-141).

**T4: unknown, and more promising than the record shows.** Its gate works (+$9.33, P=0.892 on n=279 legitimate bets); its magnitude signal does not (flat terciles). Its variance geometry is survivable (P(kill)=0.0% on full history). **T4 is the only place in the system where a positive result currently sits.**

**By segment:** MAIN threshold=2 is positive but not significant; MAIN threshold=1 is reliably negative and should not be traded.

### 2. Highest-EV next move

**Fix the `abs()` gate.** It is one line, it is the difference between −$25.67 and +$9.33 on the measured cohort, and until it is fixed **every T4 number the project has — including those in the MC bootstrap doc and every strategic conclusion drawn from them — is measuring a defect rather than a thesis.** No other available action has comparable leverage per unit of effort.

### 3. Resource allocation

Stop spending modeling effort on T1. T-400/A4 reached this from the modeling side; ruin geometry and the imminent governance-grade crossing confirm it independently. **Allocate to: (a) the T4 gate fix, (b) the T4 cold-start fix, (c) `opp_sp_*` backfill** — (c) being the only remaining T1 lever *and* a likely T4 improvement, so it serves both books.

### 4. Realistic path to G6

**G6 is not reachable on the current configuration and should not be forecast until the gate is fixed and a clean cohort accrues.** Concretely: gate fix → epoch bump → T4 clean cohort re-accrues from zero. At T4's observed cadence (518 bets in ~10 days of epoch 8), a fresh 500-bet cohort is ~2 weeks of game-days *if* cold-start blindness is also fixed. Then re-run `run_power_calc.py` for a variance-derived `n*`. **Earliest credible clean read: mid-to-late August 2026.** Note that ADR-0048 §6 already records operator acceptance that the G6 clock pauses while bands sit at zero size.

### 5. Go/No-Go on continuing to accumulate volume

**Split decision.**

- **T1: NO-GO on accumulating further volume at nonzero size.** Apply ADR-0048 (`kelly_fraction=0`). Continue *logging* evaluations for research; stop sizing them. Rationale: the sample is already sufficient to answer negatively, and it is 3 days from being formally so.
- **T4: NO-GO until the gate is fixed; GO immediately after**, under these guardrails: (i) `abs()` → signed check with a direction-consistency assertion; (ii) `VIG_CEILING` recalibrated on post-fix bidirectional data; (iii) cold-start guard; (iv) live Brier/ECE wired in; (v) stale-open and failed-order alarms; (vi) size stays at ADR-0048's zero/minimal until a clean cohort reports.

### 6. Top 5 risks not in any document

1. **The C4 gate cannot reject a confidently-wrong bet — and the more wrong it is, the more certainly it passes** (`abs()`, GG-142). Registered this session; was in no document before today.
2. **The T4 process goes silently blind after any post-midnight-UTC restart** — 78 historical occurrences, ~9,700 records lost in one observed night, `systemctl` reports healthy throughout. GG-058 fixed the adjacent path and closed.
3. **`VIG_CEILING` was calibrated on pre-bidirectional data and has never been revisited** — it governs the exact NO-side path where the defect lives, and the calibration comment's own sourcing date (2026-07-02) predates bidirectionality (2026-07-05).
4. **10.9% of MAIN positions have failed Kalshi orders but carry P&L** — invisible in paper mode, a phantom-fill rate at G6, and silently inflating every historical P&L cohort.
5. **The mandatory Step 3 open-gap scan is blind to 12 of 26 OPEN gaps, systematically the most important ones** (GG-144) — including GG-105, GG-140, GG-046, and GG-038. The emphasis that marks a gap as severe is what hides it from the check.

*(Also live, and previously hidden by #5: **GG-038 — the 60s NFR-03 kill-switch SLA is 12× too slow for continuous T4 evaluation.** That is a standing Hard Rule 6 tension sitting unaddressed and unseen. And separately: 19.6% of T4 positions are unresolved, some for 25 days, so realized-P&L cohorts are a non-random subsample of unknown bias — which undermines the entire measurement basis, including this analysis.)*

*(Meta-risk: the session-start protocol found none of the four findings above. Its Step 3 grep misses the important gaps, Q4's grep is a no-op, Q1's path is wrong, and GG-138 broke the power-calc on a clean worktree. The project's primary defense has decayed in four independent places, and in each case it fails **quietly** — returning clean-looking output rather than an error.)*

### 7. Prioritized sequenced roadmap

| # | Action | Gate it clears | Owner/ID | Target |
|---|---|---|---|---|
| 1 | **Apply ADR-0048** — DS sign-off + `execution_bands.py` edit (`kelly_fraction=0`) | GG-135 (stops the ~100%/yr self-termination) | **T-398, live blocker** | **2026-07-29** |
| 2 | **Fix `abs()` gate** — signed check + direction-consistency assert; ADR + epoch bump | **GG-142** | new | **2026-07-30** |
| 3 | **Fix T4 cold-start** — merge prior tracked IDs on startup; alarm on empty-set restart 00:00–06:00 UTC | **GG-143** | new | 2026-07-30 |
| 3b | **Repair Step 3 grep** (`^\| Status \| \*{0,2}OPEN`) + count-reconciliation assertion; re-run the open-gap review against the true 28 | **GG-144** | new | **2026-07-29** — one line, and every prior session's gap review is void until it lands |
| 4 | **Recalibrate `VIG_CEILING`** on post-fix bidirectional data | GG-142 follow-on | new | 2026-08-01 |
| 5 | **Record T1's governance-grade negative** when cadence_span hits 14 | GG-004 / GG-046 | — | **~2026-08-01** |
| 6 | **Wire Brier/ECE ladder into nightly cron** | GG-125 | — | 2026-08-02 |
| 7 | **Backfill `opp_sp_*`**, re-run D1 harness on MAIN + T4 | GG-141 → GG-105 | T-384 adjacent | 2026-08-05 |
| 8 | **Stale-open + failed-order alarms**; force-resolve the 429 T4 / 39 MAIN opens | F, G | new | 2026-08-05 |
| 9 | **Accrue clean post-fix T4 cohort**, re-run `run_power_calc.py` | GG-004 / G6 | — | mid-late Aug 2026 |
| 10 | **Repair remaining session-start protocol decay** — Q4 grep, Q1 path, GG-138 `mkdir`, close T-400's claim | I | — | opportunistic |

**Steps 1–3 are the session-critical set. Steps 1 and 2 both touch live trading behaviour and both require DS sign-off; neither was performed in this analysis-only session.**

---

## Closing note on this analysis's own limits

Two findings undercut the reliability of every number above, including mine: **10.9% phantom fills on MAIN** and **19.6% unresolved T4 positions**. Realized-P&L cohorts are therefore a non-random subsample of intended activity. My cohort statistics reconcile exactly with the governance scan, which means we agree — not that we are unbiased. The gate-defect finding is robust to both (it is a code-path fact confirmed by a 239/239 mechanism match, not a P&L inference); the edge estimates are not.

**Analysis-only session. No code, sizing, epoch, or live state was changed.**
