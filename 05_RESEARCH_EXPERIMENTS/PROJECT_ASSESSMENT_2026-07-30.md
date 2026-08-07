# Comprehensive Project Assessment — 2026-07-30

**Mode:** Read/analyze only. No code change, no epoch bump, no sizing/kill-switch change, no commit to shared nav files.
**Scope:** Whole project, MLB-weighted (NBA dark/frozen). Written while two operator sessions are live (T4 measurement reactivation; G3/opp_sp cleanup) — findings here are deliberately non-overlapping with those, except where they constrain the T4 reactivation design.
**Data as of:** `logs/.vps_portfolio_cache_mlb.json` / `_mlb_t4.json`, last VPS pull `2026-07-30T06:35Z` / `06:46Z`. `HEAD=00201fe` on `main`.
**Prior baseline:** `STRATEGIC_ANALYSIS_2026-07-29.md` (Fable). This document does not restate it; it re-measures its two central claims one day and ~260 T4 bets later, and adds what changed after R1/R2 landed.

---

## Session-start protocol — results

| Step | Result |
|---|---|
| 0 — isolation/claims | Shared `main`, clean tree. Two live claims (2026-07-30). Read-only session; no shared nav file written. |
| 1 — doc debt | **0 hits** (`Decisions logged: false`) |
| 2 — stub scan | **CLEAN** (0 hits across `src/`) |
| 3 — open gaps | **25 OPEN** (plain 14 + bold 11, reconciliation asserts). Down from 28 at the GG-144 re-baseline — GG-141/GG-142/GG-144/GG-138 closed, GG-145 opened. Anchored scan working as repaired. |
| 4 — operational health | **NOT RUNNABLE from this environment** — no SSH route to `prediction-market-vps` from the Cowork sandbox. Substituted: direct analysis of the VPS portfolio caches (pulled 06:35/06:46Z today) plus `run_power_calc.py` run locally. This is a real coverage hole for any Cowork-hosted session and is noted below. |
| Q1–Q6 | See § 6. |

---

## 1. Bottom line

**Your instinct is right about the phase and wrong about the mechanism.**

You are correct that the project no longer needs another structural fix — the engineering is, on the evidence, in good order. But **the system as currently deployed cannot accrue anything.** As of R1 (ADR-0048, epoch 9) and R2 (ADR-0049, epoch 10), all four MLB bands are at `kelly_fraction=0.0`, and epoch 10 carries `bands_affected={*}`. The live measurement layer now reports:

```
[T1]        clean_n=0 (raw_n=461)
[T2]        clean_n=0 (raw_n=2)
[T3]        clean_n=0 (raw_n=0)
[T4M-PROJ]  clean_n=0 (raw_n=2015)
```
*(`scripts/run_power_calc.py`, run 2026-07-30)*

Every band's clean-epoch floor is 10. Every band's sizing is zero. Zero-size bets are rejected upstream (`kelly_size_zero` for T1/T2/T3; failed `stage_order()` for T4M-PROJ), so **no epoch-10 position will ever be written.** `clean_n=0` is not a transient blackout like GG-124 — it is a fixed point. Going hands-off from here accrues calendar time and nothing else.

This is not a criticism of R1 or R2 — both were correct and necessary. It is a consequence nobody sequenced: the ruin fix (zero the sizing) and the correctness fix (bump the epoch for everyone) landed within six hours of each other, and their intersection is a measurement system with no input.

**The one thing standing between you and a legitimate hands-off period is re-opening a data path.** That is what "T4 measurement reactivation" needs to be — and its design constraints are in § 4.

---

## 2. What the evidence actually says, band by band

### T1 / MAIN — negative, and the last day of data made it worse

Under the pre-epoch-10 floor (epoch ≥ 6, the cohort Fable measured):

| | Fable, 2026-07-29 | This assessment, 2026-07-30 |
|---|---|---|
| clean n | 175 | **202** |
| mean P&L/bet | −$0.4112 | **−$0.6289** |
| win rate | — | **45.5%** |
| total | — | **−$127.04** |
| cadence span | 11.00 d | **13 d** (2026-07-16 → 07-29) |

Per-epoch, the deterioration is monotone in the largest cohort: epoch 8 alone is n=154, 44.8% win rate, **−$143.01** (−$0.929/bet). Book-level, T1/MAIN is at **−12.2% realized drawdown** against a 20% permanent kill switch — 61% of the way to a terminal event, in six weeks, on a book that started fresh 2026-06-24.

`run_power_calc.py`'s verdict on the pre-reset cohort stands: *no finite n\* exists to confirm a positive edge from this sample's own effect size.*

**Two things follow.** First, T1's negative verdict is now past `NEG_SIGN_CONFIRM_N=150` by a wide margin (202) and one day short of `MATURE_CADENCE_SPAN_DAYS=14`. Second — and this is a governance trap worth naming — **the span is now frozen at 13 days and will never reach 14**, because no further T1 bets will be written. The stop-criterion for a losing band requires a data span that a zeroed band cannot produce. T1's negative sign will sit permanently one day short of governance-grade unless the criterion is evaluated against the frozen cohort by explicit operator/DS decision rather than waiting for the clock. *(This is not currently registered as a gap. It should be — see § 7.)*

Substantively, the answer on T1 is not in doubt. GG-105 → GG-140 → T9/A1-A3 → G3/opp_sp exhausted the raw-feature class, the one-step-interaction class, the monotonic-transform recalibration class, and the opponent-pitcher covariate. GG-135's Monte Carlo shows MAIN self-terminates against the 20% drawdown at roughly 100%/yr **even at zero edge**, purely from variance geometry. There is no candidate left that doesn't require a new model class or a new feature source. **T1 is correctly dark and should stay dark.**

### T4M-PROJ — the single genuine positive result in the project, and it strengthened

> **SUPERSEDED, 2026-08-05 — GG-159.** This section's Assumption 1 (§8) was verified false by `05_RESEARCH_EXPERIMENTS/VC6_VIG_CASCADE_VERIFICATION_2026-08-04.md` (T-413): the `−2.0·vig` reconstruction below does **not** match `paper_trader.py::open_position()`'s real cascade (L460-468), which is direction-asymmetric — YES carries no vig term at all; NO nets against `gross_edge` with only 1x vig pre-baked in, not the uniform symmetric `2.0·vig` this section applied to both directions. Row-level reproduction (778/778 and 799/799 exact matches, max_abs_diff=0.000000) found the code-true output is **n=388, ROI +9.65%** (as-of-2026-07-30 cohort; n=404, ROI +9.71% on the current cohort) — bit-for-bit identical to this section's own `raw − 1.0·vig` and `fee_net_edge (stored field)` rows below, not its headlined `raw − 2.0·vig` row (n=344, ROI +10.99%). The qualitative verdict (T4M-PROJ gate-valid is genuinely positive; the `abs()` defect, not the model, made it look negative) **survives and is not weakened**. Two things below do not survive: **(1)** the headlined `−2.0·vig` row is not merely an unvalidated assumption, it is the disproven one — every code-verified row shows the middle tercile dipping; tercile monotonicity does not hold under the real formula, full stop, not "under 4 of 5 alternate definitions." **(2)** the "five independent edge definitions" framing below is wrong: `fee_net_edge (stored field)` **is** the cascade's actual output, so it and `raw − 1.0·vig` are the same measurement expressed two ways, not independent corroboration — the table collapses to one verified number (`raw − 1.0·vig` / `fee_net_edge`, n=388/+9.65%) plus one genuinely independent row (`gross_edge`, n=161/+27.58%, pre-vig, still unverified against the real cascade). The original text below is left as-authored per this project's archive-in-place convention; read it through this correction, not as current fact.

Fable's GG-142 finding was that `risk.py`'s `abs(edge)` gate systematically rescued the bets the model was most confident were wrong. I reconstructed the direction-effective edge independently from the ledger (`model_p`, `mid_price_at_entry`, `vig_at_entry`, `direction`, applying the T4M-PROJ `−2.0·vig` coefficient) on the now-larger epoch-8 cohort — **n=778, up from Fable's 518.** The finding replicates and gets cleaner:

> **UNVERIFIED-PENDING-GG-166 (added 2026-08-06/07, T-426):** every dollar/ROI figure in this section and the table below is computed from ledger outcome data (`actual_hits`/WIN-LOSS) that T-426's shadow agreement check found may be misresolved. Root cause: `run_t4_mlb_live.py:1519` stamps a UTC-wall-clock `game_date` at bet-entry that `run_resolve_mlb.py::_fetch_mlb_hits()` then uses as an exact-match resolution join key against the MLB Stats API — silently returning a different game's box score (44.2% `actual_hits` disagreement / 30.1% derived WIN/LOSS disagreement found on the epoch-12 T4M-PROJ clean cohort; epoch-8 not separately re-checked by T-426 but not exempt from the same write-path bug, since the defect is in the write path itself, not epoch-specific). Registered **GG-166 (CRITICAL, OPEN)**, fix tracked as **T-429** (unstaffed). This is independent of, and does not retract, GG-159's vig-cascade formula correction above (§2 banner) — that fix corrects how P&L is *computed* from a given outcome; GG-166 concerns whether the outcome itself (which game's box score) is *correct*. Do not treat the n=778 headline or the table below as governance-grade for GG-004/G6 purposes until T-429 lands and the epoch-8 cohort is re-verified. See `03_DECISIONS/ADR-0050_t4m-proj-flat-measurement-stake-reactivation.md` §11, `05_RESEARCH_EXPERIMENTS/VC6_VIG_CASCADE_VERIFICATION_2026-08-04.md`, `11_MEMORY_HANDOFF/MEMORY_BANK.md` 2026-08-06/07 entry.

| Cohort | n | total P&L | P&L/bet | stake | ROI | Correction note |
|---|---|---|---|---|---|---|
| Full epoch-8 book | 778 | **−$28.81** | −0.0370 | — | — | — |
| `abs()`-rescued (edge < 0) | 434 | **−$44.27** | −0.1020 | — | — | — |
| Gate-valid (edge ≥ 0) | 344 | **+$15.46** | +0.0449 | $140.66 | **+10.99%** | †SUPERSEDED — GG-159: real cascade gives n=388, +9.65% |
| Gate-valid (edge ≥ 0.04, the real `MIN_EDGE`) | 234 | **+$11.10** | +0.0474 | $87.47 | **+12.69%** | not re-verified against real cascade — same reconstruction bug likely applies, treat as unverified pending re-check |

Bootstrap (10k resamples) on the gate-valid cohort: **P(profit) = 0.967**, 95% CI [−0.0034, +0.0917].

**Robustness test across five ~~independent~~ edge definitions** (this is Validation Check #4, run rather than deferred — the direction-effective edge has to be reconstructed, and the reconstruction's vig coefficient is an assumption worth attacking):

> **SUPERSEDED, 2026-08-05 — GG-159.** These five rows are not five independent tests. `fee_net_edge` (row 5) **is** `paper_trader.py::open_position()`'s real cascade output, verified by row-level reproduction (799/799 exact match, max_abs_diff=0.000000, `VC6_VIG_CASCADE_VERIFICATION_2026-08-04.md`). `raw − 1.0·vig` (row 2) is a hand reconstruction of that same cascade and lands on matching aggregate n/ROI — it is the same measurement approximated two ways, not corroboration from an independent source. `raw − 2.0·vig` (row 1, the row marked `monotonic? yes`) is not a competing-but-unvalidated definition — it is disproven; production code does not apply a symmetric 2.0x vig term to both directions (see the §2 banner above). What remains as genuinely distinct: **one verified number** (`raw − 1.0·vig` / `fee_net_edge`, n=388, +9.65%, per-row tercile figures below still only approximate the code cascade — treat the tercile shape as directionally informative, not exact) and **one genuinely independent row** (`gross_edge`, pre-vig stored field, n=161, +27.58% — never itself re-verified against the real cascade, still an open item). The `raw` row (no vig) is a degenerate control, not a sixth data point.

| Edge definition | gate-valid n | total P&L | ROI | P(profit) | terciles (ROI) | monotonic? |
|---|---|---|---|---|---|---|
| `raw − 2.0·vig` (T4M-PROJ ledger coeff) — **DISPROVEN, does not match production, see banner** | 344 | +$15.46 | ~~+10.99%~~ | 0.972 | +5.59 → +8.35 → +24.29 | ~~yes~~ **not code-verified** |
| `raw − 1.0·vig` — same measurement as row 5, not independent | 388 | +$15.02 | **+9.65%** | 0.954 | +11.60 → −0.87 → +23.14 | no |
| `raw` (no vig adjustment) — degenerate control | 778 | −$28.81 | −6.89% | 0.012 | −12.27 → −11.13 → +10.29 | *(= full book)* |
| `gross_edge` (stored field) — the one genuinely independent row | 161 | +$14.22 | **+27.58%** | **0.996** | +29.74 → +20.28 → +34.19 | no |
| `fee_net_edge` (stored field) — **this IS the production cascade output (GG-159)** | 388 | +$15.02 | **+9.65%** | 0.960 | +8.00 → +1.39 → +25.21 | no |

**Two findings, and they deserve different confidence.** *(Original text below; read against the banner above — the magnitude changed, the shape of both conclusions did not soften.)*

**(a) The filter is robust — this is the real result.** ~~Under every definition that applies *any* vig adjustment, the gate-valid subset is positive: ROI +9.65% to +27.58%, bootstrap P(profit) 0.954 to 0.996, on n between 161 and 388.~~ **Corrected:** the code-verified figure is one number, not a range — ROI +9.65%, P(profit) 0.954–0.960, n=388 — plus the still-unverified `gross_edge` row at +27.58%/n=161. The `raw` row is the control and confirms the mechanism — with no vig adjustment there is no filtering, and you get the full book's −6.89%. **The `abs()` defect, not the model, is what made T4 look negative.** That conclusion does not depend on my coefficient choice, and does not depend on the disproven `−2.0·vig` row either — it holds on the code-verified `fee_net_edge` figure alone.

**(b) The scaler is NOT robust — and this is now on firmer ground than my original retraction, not weaker.** I originally wrote that monotonicity "holds under exactly one of five definitions (`−2.0·vig`), which happens to be the one I picked first" — framed as if that row were a legitimate alternative that simply lost a coefficient-choice contest. It wasn't: GG-159 found `−2.0·vig` doesn't match production code at all. So the correct statement is stronger than my original one — **monotonicity holds under zero code-verified definitions.** The middle tercile dips under every row that actually corresponds to a real or hand-approximated production formula. Fable's characterisation — *"a working filter with a non-working scaler"* — doesn't just survive, it's the only characterization consistent with the verified data.

What *is* consistent across the code-verified rows: **the top tercile is the best** (+23.14–25.21% on `raw−1.0vig`/`fee_net_edge`; +34.19% on the still-unverified `gross_edge`). So the edge signal reliably identifies its strongest third but does not cleanly rank-order across the full range. That is a weaker claim than monotonicity — and still a meaningful one, because it is the *opposite shape* to GG-105's anti-predictive finding on the same band. Whatever GG-105 diagnosed, the gate-valid subset does not exhibit it.

**Worth a separate look:** the stored `gross_edge ≥ 0` subset (n=161) is the strongest cohort in the project — **+27.58% ROI, P(profit)=0.996** — at roughly half the volume, and remains the one row GG-159 did not re-verify against the real cascade (it's a pre-vig stored field, not a vig reconstruction, so the asymmetric-cascade defect doesn't directly implicate it — but it hasn't been positively checked either). If that survives out-of-sample, a tighter gate may beat a wider one. Not actionable on in-sample data; flagged as the first thing to test on epoch-10.

**How much weight overall: moderate on the filter, essentially none on the scaler.** The threshold was chosen knowing this data, so both splits are partly in-sample. This is a **hypothesis for epoch-10 data to confirm out-of-sample** — not a validated edge. The filter result, corrected, is still the strongest signal this project has produced (+9.65% ROI, n=388, code-verified) — it survived a 50%-larger sample and reproduction against the actual production cascade, which is a stronger check than the five-way sweep this section originally claimed. The scaler claim is fully retracted, not merely downgraded.

**T4's status is UNANSWERED-and-promising, not negative.** That distinction is the whole reason to keep the lights on.

### T2 / T3 — no data

`raw_n=2` and `raw_n=0` respectively. T2's two bets lost $29.38. There is nothing to assess and nothing to invest in.

### NBA — correctly frozen

$751.10 on $1,000, −24.9% realized, last activity 2026-06-17. Historical and adjudicated (GG-034/GG-037), not a live risk. Leave it until ~1 month pre-season.

---

## 3. Is the engineering over-built? — the honest answer

**No, and the record supports you.** I looked for the signature of over-engineering: dark code paths, provisional constants that never got calibrated, abstractions with one implementation. What I found instead:

- **Every structural fix in the last 30 days was triggered by a measured defect, not by anticipation.** GG-141 (dead `opp_sp` columns) → found by a feature scan. GG-142 (`abs()` gate) → found by a P&L decomposition. GG-143 (cold-start blindness) → found by a missing-records count. GG-145 (`park_factor` constant) → found by the tool GG-141 caused you to build. That is a healthy failure-discovery chain, not scope creep.
- **The stub scan is clean.** Zero `# stub|# placeholder|# TBD` in `src/`. For a system this size at Phase 6, that is unusual.
- **Test suite: 2,757 passing.** The 17 known failures are deliberate, documented Kelly-zero fixture fallout.
- **The C1–C8 separation holds.** T1/T4 pool isolation is real and enforced at the ledger level.

**Where the effort actually is over-invested is documentation and governance, not code.** CLAUDE.md is 44,888 bytes and has needed three self-remediation passes for its own staleness in four weeks. `SESSION_CLAIMS.md` rows now run to multi-paragraph essays. `TODO_NEXT.md` has ten stacked `Last reviewed (prior)` narrative blocks above the first actual task. GG-132 and GG-133 are both registered gaps *about the documentation system's own decay*. The governance layer has started generating work for itself at a rate comparable to the engineering it governs.

That is the thing to stop doing during a hands-off period — not the engineering.

**Still-provisional constants worth knowing about (not urgent, all in dark bands):** `execution_bands.py` carries eleven `PROVISIONAL` `kelly_fraction` values across T4 sub-bands (T4M-ARITH, T4M-FLOW, event/lineup/sentiment bands), each gated on an unrun EXP. None are live. They are correctly parked, not forgotten — but they are also the shape of a future over-build if any gets activated before its EXP runs.

---

## 4. What a real hands-off period requires

You cannot go hands-off from the current state, because the current state produces nothing. Three options, in order of my preference:

**Option A — shadow-mode measurement (recommended).** Keep `kelly_fraction=0` everywhere. Add a resolution pass over the T4 evaluation log so that zero-size evaluations still get outcome-joined and scored. This gives you full statistical accrual with literally zero capital risk.

*Constraint you need to know before choosing this:* `t4_mlb_cycle_log.jsonl` currently carries `p_t4`, `gross_edge`, `net_edge`, `ba_l10`, `mip`, `vig` and the live state — **but no outcome field.** 21,871 of 24,744 cached rows have the forecast side; none have the resolution side. So Option A is not free: it needs a join from the cycle log to actual per-player hit counts (the machinery exists — `actual_hits` is in the ledger schema and `post_game_resolve` already resolves markets). Estimated as the smallest of the three builds, and it is the *only* option that decouples measurement from risk permanently. If "T4 measurement reactivation" is not already this, consider making it this.

**Option B — nominal-stake reactivation of T4M-PROJ only.** Set T4M-PROJ to a token `kelly_fraction` (or a flat $0.10/bet cap), leave T1/T2/T3 at zero. Accrues real resolved bets under epoch 10 with the fixed gate. Simple, uses the existing path, needs no new code. Downside: reintroduces a live sizing parameter and re-opens a (tiny) ruin surface, and every future correctness fix re-zeroes `clean_n` again.

**Option C — do nothing.** Legitimate only if you accept that the project is paused, not accruing, and that the ~$0 risk is being bought with ~0 information. I don't recommend it for more than a week.

### Three constraints on whatever you reactivate

1. **`n*` is currently underivable.** With `clean_n=0` on every band, no sample-size target exists. Once epoch-10 data starts flowing, re-run `run_power_calc.py` weekly — the target moves with each band's own observed variance (APR-0024).
2. **Any correctness fix that lands during the accrual window with `bands_affected={*}` resets every band to `clean_n=0` again.** Epochs 9 and 10 both landed on 2026-07-30, five and a half hours apart, and between them wiped 461 T1 and 2,015 T4 raw bets out of clean status. **During a hands-off accrual period, treat an epoch bump as a decision requiring the same scrutiny as a sizing change**, and prefer band-scoped `bands_affected` over `{*}` wherever the diff genuinely permits it.
3. **T4's band budget does not ratchet down with losses.** By design (`_ledger_bankroll()` excludes `pool_isolated` positions, ADR-0019), the T4 portfolio's `bankroll_usd` is pinned at exactly $1,000.00 despite +$12.19 realized and $115.83 in open stake — the correctly-derived value would be $896.36. Consequence: `t4_band_budget = bankroll_usd × 0.27` is a constant $270 that never shrinks as the book draws down. The drawdown *measure* at `run_t4_mlb_live.py:866` uses `realized_loss / initial_bankroll` and does track correctly, so the kill switch itself is intact — but the budget cap is not loss-responsive. Harmless at zero size; **verify this explicitly before reactivating T4 sizing.**

---

## 5. What I would *not* build

Answering your actual question — where the over-engineering risk is:

- **Do not chase T1 further.** Four candidate classes are exhausted. Any further T1 work is a new model class or a new data source, and neither is worth it before T4 gives a verdict.
- **Do not activate any T4 sub-band** (ARITH, FLOW, event, lineup, sentiment) before T4M-PROJ produces a clean epoch-10 read. Each carries a PROVISIONAL Kelly and an unrun EXP.
- **Do not build the MLB PRF/qualitative layer (GG-094)** yet. It's a real gap, but it's a T1-side enrichment, and T1 is the band you're stepping away from.
- **Do not fix GG-145 (`park_factor`) as a priority.** It's real, it's one of five base features, and it did not change any qualitative verdict. Batch it.
- **Do not add governance tooling.** The governance layer is where the marginal effort is currently least productive.

---

## 6. Q6 — what I'd tell you in 60 seconds

1. **`clean_n=0` on all four bands, right now.** Nothing is accruing. That's the headline and it's less than a day old.
2. **T1's negative verdict can never reach governance-grade** under the current criterion, because the 14-day span requirement is frozen at 13 days by the zeroed sizing. Needs an explicit adjudication, not a wait.
3. **The T4 gate-valid cohort is positive under every edge definition I could construct** (five of them, ROI +9.65% to +27.58%, P(profit) 0.954–0.996). The `abs()` defect, not the model, is what made T4 look negative — and that conclusion is robust to the reconstruction assumptions. The tightest variant (`gross_edge ≥ 0`, n=161, +27.58%, P=0.996) is the single strongest cohort in the project and has never been examined on its own.
4. **VPS operational health (Step 4) is unverifiable from Cowork sessions** — no SSH route. Every Cowork-hosted session has been silently skipping the one protocol step that catches dark pipelines. This is a structural blind spot in the protocol, not a one-off.
5. **The VPS ran the old code for at least four hours after R1 merged** — 35 T4 positions entered 2026-07-30 00:01–04:09Z, all stamped `logic_epoch=8`, `approval_commit=f961fba6`. Deploy is push-triggered and generally fast, but epoch stamping is done in-process, so there is a real deploy-lag window in which positions get stamped with a superseded epoch. `logic_epoch.py` already documents this approximation for the epoch 2/3 boundaries; it just recurred at a 4-hour scale rather than a few minutes. Worth confirming what actually happened before those 35 rows are trusted as epoch-8-clean.
6. **The documentation system is decaying faster than it's being maintained** — GG-132 and GG-133 are both gaps about the doc system's own staleness, and CLAUDE.md has self-remediated three times in four weeks.

---

## 7. Recommended action plan

### 7.0 The constraint that decides the plan — Option B is ADR-blocked

The live reactivation worktree (`session/20260731T020022Z-t4-reactivate`, branch created 2026-07-31T02:00Z, currently carrying **only a claim row** — no implementation yet) is claimed against **GG-046 + ADR-0048**. That pairing forecloses the nominal-stake path, and it is worth being explicit about why before any code is written:

- **ADR-0048 §4** is a hard gate, not a formula input: `kelly_fraction(band) = 0` **unless the GG-105 monotonicity gate has passed for that band**, sized against *the specific edge figure that passing run reported*.
- **ADR-0048 §3** (T4 table) says so in its own words: *"The binding constraint for T4M-PROJ is GG-105 itself, not the sizing table."* Every row above `0×` requires a validated edge.
- **The gate cannot pass on existing data.** Epoch ≤ 9 is `abs()`-contaminated — that contamination is the entire reason R2 bumped to epoch 10. And on the post-hoc gate-valid reconstruction, tercile monotonicity survives **1 of 5** edge definitions (§ 2). That is not a Fisher-test pass; it is a coin-flip on reconstruction assumptions.
- **GG-046's own bar** is EXP-T4-01 re-run on **≥500 clean unique markets**. Current clean count: **0**.

**Therefore there is no ADR-compliant path to nonzero T4 sizing today, and won't be until a clean epoch-10 cohort exists.** Any reactivation that produces real stakes either violates ADR-0048 §4 or requires a gate run on data that does not exist. Conversely, **ADR-0048 §5 explicitly blesses the alternative**: *"The zero-size default state trivially satisfies D2 (a book placing no bets cannot be killed by variance), so no D2 run is required to remain at the default."*

**Option A (shadow mode) is not merely preferable — it is the only compliant way to accrue.** That resolves the § 4 fork.

### 7.1 The plan

| # | Action | Owner | Why now | Size |
|---|---|---|---|---|
| 1 | **Re-scope the live T4 session to measurement-only.** Keep `kelly_fraction=0`; build the outcome-join so zero-size evaluations resolve and score. Do **not** touch sizing. | live t4-reactivate session | The only ADR-compliant accrual path (§ 7.0) | **M** — the one real build left |
| 2 | Inside #1: confirm the T4 budget-ratchet point (§ 4.3) is understood but **not** fixed now — it only binds at nonzero size | same | Avoid scope creep into a dead constraint | XS |
| 3 | Land G3/opp_sp cleanup as-is | live cleanup session | In flight | — |
| 4 | Register the **frozen-span trap**: T1's 13-day cadence span can never reach `MATURE_CADENCE_SPAN_DAYS=14`, so a losing band stays permanently one day short of governance-grade. Adjudicate T1 against the frozen n=202 cohort by explicit operator/DS decision | new, small session | Closes T1 cleanly; unblocks the ADR-0024 stop-criterion | S |
| 5 | Register the **Cowork Step-4 blind spot** — no SSH route, so the one check that catches a dark pipeline is silently skipped in every Cowork-hosted session | same session as #4 | Protocol integrity | XS |
| 6 | Verify the 35 epoch-8-stamped rows entered 2026-07-30 00:01–04:09Z against the actual deploy time of `6be807f` | same session as #4 | Data provenance on the last pre-freeze cohort | XS |
| 7 | **Declare the freeze.** Write down: no `src/` changes, no new features, no band activations, no governance tooling, for a fixed window | operator | This is the hands-off period, made explicit so it survives the temptation to fix GG-145 | XS |
| 8 | **Then stop.** Weekly cadence only: `run_power_calc.py` + governance scan. Nothing else | operator | Accrual | — |
| 9 | At clean_n ≈ 300–500 on T4M-PROJ: re-run the § 2 five-definition sweep **out-of-sample**, plus the formal GG-105 Fisher gate. Test `gross_edge ≥ 0` (n=161, +27.58%, P=0.996) as a candidate tighter gate | future session | **This is the go/no-go.** First honest read on the commercial question | M |
| 10 | Only if #9 passes: ADR-0048 §3 lookup → §5 D2 re-run incl. §8.1–8.3 cascade checks → nonzero sizing | future session | The reactivation itself | M |

### 7.2 Explicit freeze list (what #7 forbids)

Do not, during the accrual window: fix GG-145 (`park_factor`), build the MLB PRF layer (GG-094), activate any T4 sub-band, resume T1 modelling, refactor CLAUDE.md, or add governance tooling. Batch them all behind step #9's verdict. **Exception — the only work that should break the freeze is a defect that corrupts the accruing measurement itself.** If such a fix is needed, scope its `bands_affected` narrowly; a `{*}`-scoped epoch bump mid-window resets `clean_n` to 0 and restarts the clock, which is precisely what happened on 2026-07-30.

### 7.3 Timeline

Step #1 is days, not weeks. Steps #4–#6 are one short session. Accrual then runs on T4's real cadence (~67 bets/day per B2's measurement, though recent observed cadence is lower). **Earliest credible clean T4 read: late August 2026** — consistent with Fable's estimate, and contingent on step #1 landing this week and no `{*}`-scoped epoch bump intervening.

### 7.4 What would make me change this plan

- If the outcome-join in #1 proves larger than an M — then Option B's ADR-block becomes the binding problem, and the honest move is to reopen ADR-0048 §4 deliberately (a superseding ADR with a documented measurement-only carve-out), not to quietly size up.
- If step #9's out-of-sample read is flat rather than positive — T4 joins T1, and the project's answer to the commercial question is negative across both alpha theses. That is a legitimate outcome and should be reachable by ~September rather than deferred.

---

## 8. Assumptions | Key Risks | Validation Checks | Confidence

**Assumptions**
- VPS caches (06:35/06:46Z today) reflect live VPS state; no bets between then and now that would change the figures materially.
- ~~My direction-effective edge reconstruction (`raw − 2.0·vig`) matches `paper_trader.py`'s T4M-PROJ formula. It reproduces Fable's independently-derived split direction and sign, which is corroborating but not proof.~~ **FALSIFIED, 2026-08-05 — GG-159.** It does not match; the real cascade is direction-asymmetric (1x vig on NO, 0x on YES), not the uniform `2.0·vig` this assumption asserted. See § 2 banner. The assumption that *does* hold, code-verified: `raw − 1.0·vig` / `fee_net_edge` matches production exactly (799/799 rows, max_abs_diff=0.000000).
- `run_power_calc.py` run locally against the cached portfolios gives the same `clean_n` the VPS-side governance scan would.
- R2's merge (`34735a4`, 18:27 PDT today) has deployed; not verifiable from here.

**Key Risks**
- **Measurement deadlock** (`clean_n=0` + zero sizing) persists unnoticed → weeks of zero information. *Highest-probability, highest-cost risk in the project right now.*
- **T4 positive result is an in-sample artifact** — the filter threshold was chosen knowing this data. Only out-of-sample epoch-10 data resolves it.
- **Epoch-reset churn**: another `{*}`-scoped bump mid-accrual restarts the clock.
- **T1's frozen 13-day span** leaves a losing band formally unadjudicated indefinitely.
- **Cowork sessions cannot run Step 4** → a dark pipeline could persist undetected across multiple sessions.

**Validation Checks (reproduce independently)**
1. `PYTHONPATH=src:scripts python3 scripts/run_power_calc.py` → expect `clean_n=0` × 4.
2. `python3 -c "from prediction_market_bot.logic_epoch import *; print(CURRENT_LOGIC_EPOCH, [ (b.epoch,b.bands_affected) for b in get_boundaries() ])"` → expect 10, epoch 10 = `{*}`.
3. `grep -n "kelly_fraction=0.0" src/prediction_market_bot/execution_bands.py` + `grep -n "KELLY_T4" src/prediction_market_bot/run_t4_mlb_live.py` → four bands + module constant at zero.
4. T4 edge reconstruction under five definitions — **done, § 2.** Filter result robust; scaler/monotonicity claim refuted and retracted.
5. On the VPS: confirm the deploy timestamp for `6be807f` against the 35 rows entered 00:01–04:09Z on 2026-07-30.
6. Re-run the § 2 robustness table against `paper_trader.py::open_position()`'s actual four-branch vig cascade (L462-468) rather than my reconstruction, to close the last assumption. ~~Not done — needs the live function, small.~~ **DONE, 2026-08-04 (T-413/VC6), GG-159.** Result: reconstruction was wrong (`−2.0·vig` does not match; `−1.0·vig`/`fee_net_edge` does, 799/799 exact match). See `VC6_VIG_CASCADE_VERIFICATION_2026-08-04.md` and the § 2 banner above.

**Confidence**
- `clean_n=0` deadlock — **High.** Directly measured, mechanically explained.
- T1 negative — **High.** Consistent across four independent candidate classes, 202 bets, worsening.
- T4 gate-valid positive, filter working — **Medium-High.** Corrected 2026-08-05 (GG-159): the five-definition sweep was not independent (`fee_net_edge` IS the cascade output) — code-verified figure is ROI +9.65%, P(profit) 0.954–0.960, n=388, plus the still-unverified `gross_edge` row at +27.58%/n=161. Replicated on a 50%-larger sample and confirmed against the actual production cascade (row-level exact match), which is a stronger check than the originally-claimed five-way sweep. Remaining discount is entirely for in-sample threshold selection.
- T4 edge signal as a scaler (tercile monotonicity) — **None. Claim fully retracted, 2026-08-05 (GG-159), on firmer ground than the original retraction.** The one row that showed monotonicity (`−2.0·vig`) is not a legitimate alternative definition that lost a coefficient contest — it does not match production code. Zero code-verified definitions show monotonicity. Only the top-tercile-is-best pattern survives.
- Engineering is not over-built — **Medium-High.** Clean stub scan, clean test suite, defect-driven change history.
- Governance layer is over-invested — **Medium.** Qualitative, but GG-132/GG-133 are the system's own admission.

---

*Prepared read-only. Uncommitted in the shared `main` tree — commit path-scoped (`git commit 05_RESEARCH_EXPERIMENTS/PROJECT_ASSESSMENT_2026-07-30.md`) once the two live sessions close, per Hard Rule 10.*
