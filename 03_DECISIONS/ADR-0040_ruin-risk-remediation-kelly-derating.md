# ADR-0040 — Ruin-Risk Remediation for Proportional Stake Sizing: Cadence-Aware Kelly De-Rating (ACCEPTED)

**Status:** ACCEPTED — 2026-07-04 (operator sign-off on the corrected target, execution_bands.py's T1_MULTI_DAY.kelly_fraction 0.10 → 0.061, via explicit choice among three sensitivity-table options).
**Date:** 2026-07-03 (corrected 2026-07-04, SESSION 118 continuation — see "Correction" note below)
**Session:** SESSION 117 (continuation); corrected SESSION 118 (continuation)
**Operator:** Earl Ignacio
**Scope:** `execution_bands.py` — `BAND_CONFIGS[ExecutionBand.T1_MULTI_DAY].kelly_fraction` (currently `0.10`, set by ADR-0010). This ADR, if accepted, **supersedes ADR-0010's T1 kelly_fraction value only** — ADR-0010's other band values (T2, T3, T4, T5) and its derivation methodology are untouched. Applies to any band using proportional/Kelly-style sizing (currently T1 MLB; would also apply to any future band inheriting the same mechanic).

**Correction (2026-07-04):** This ADR originally proposed editing `risk.py`'s `DEFAULT_KELLY_FRACTION` (0.25 → 0.14). That constant is a `RiskEngine.__init__` default parameter value only — the real T1 MLB production path (`run_mlb_paper_trade.py`) always explicitly passes `kelly_fraction=T1_KELLY`, sourced from `execution_bands.py`'s `T1_MULTI_DAY.kelly_fraction = 0.10` (set by ADR-0010), which overrides the `risk.py` default entirely. `DEFAULT_KELLY_FRACTION` is inert for T1 MLB. Had the originally proposed value (0.14) been mechanically applied to the real 0.10 baseline instead, it would have **increased** live stake sizing by 40% — moving further into the ruin-risk zone GG-071 identified, not away from it. The sensitivity analysis below is unchanged (it is expressed in terms of `stake_frac`, which is source-agnostic), but the Decision section's target file and target value are corrected accordingly.

---

## Context

GG-071 (registered 2026-07-02, SESSION 113 CONTINUATION) found via a forward-time compounding Monte Carlo that T1 MLB's real, positive edge (53.06% win rate at time of study) produces a permanent 20%-max-drawdown kill-switch breach probability of 17.05% by day 30, 43.5% by day 182, 46.45% by day 365 — under proportional-stake compounding at T1's real cadence (~26 bets/active day). This is not a code defect; it is a property of the current sizing mechanic (`_compute_kelly_size` in `risk.py`, fractional Kelly with `DEFAULT_KELLY_FRACTION = 0.25`, capped at `_HARD_LIMITS["max_single_event_exposure_usd"] = $500`) that had never been reviewed under a forward-time, compounding lens — all prior Monte Carlo work in this project answered "given the open book today, what's the P&L distribution," not "if this edge and cadence persist, what does a full year look like."

T-223 was registered to formally review the stake-sizing mechanic against this finding and recommend a remediation, per three candidate directions named in GG-071's Resolution field: (a) cadence-aware Kelly de-rating, (b) a formal max-P(kill-switch) target used to size `DEFAULT_KELLY_FRACTION`, (c) lowering the $500/bet hard cap.

**A note on the underlying script.** GG-071's original `mc_forward_projection.py` (SESSION 113) does not exist in the repository — a repo-wide search confirmed this before the current session began. This ADR's analysis is built on a script of the same name, recreated this session (`scripts/mc_forward_projection.py`, T-223) from GG-071's cited parameters (win rate, win/loss multiple, stake fraction, cadence, drawdown threshold, cap) rather than from the original source. The recreation reproduces GG-071's cited order of magnitude closely at the 1-month horizon (17.78% vs. cited 17.05%) and confirms the same qualitative finding at 6-month/1-year horizons (49.32% vs. cited 43.5%/46.45% — same double-digit-percent elevated-ruin conclusion, though the exact shape differs, plausibly because the original script drew per-bet odds from the real portfolio's distribution rather than a single averaged win/loss multiple). This ADR's recommendation rests on the *qualitative and directional* finding (real edge + this cadence + this sizing mechanic = material ruin risk; de-rating the sizing mechanic suppresses it, monotonically, at every horizon), which the recreation confirms robustly under its own test suite (`tests/test_mc_forward_projection.py`, 13/13 passing) — not on matching GG-071's exact percentages digit-for-digit.

---

## Sensitivity Analysis (T-223, `scripts/mc_forward_projection.py --sensitivity`)

Baseline (stake_frac=1.153%, cap=$500, starting bankroll $1,000): P(kill switch) = 17.52% (30d) / 49.18% (182d) / 49.18% (365d).

**(a) Cadence-aware Kelly de-rating** (divide the effective stake fraction by a de-rate factor, applied at every bet from day 1):

| De-rate | Effective stake frac | 30d | 182d | 365d |
|---|---|---|---|---|
| 1.0x (baseline) | 1.153% | 17.52% | 49.18% | 49.18% |
| 1.5x | 0.769% | 1.54% | 9.38% | 9.48% |
| 2.0x | 0.577% | 0.08% | 1.18% | 1.44% |
| 3.0x | 0.384% | 0.00% | 0.00% | 0.04% |

**(b) Formal max-P(kill-switch) target** (binary-search the stake fraction to hit a 1-year ceiling):

| Target (1yr) | Required stake frac | 30d | 182d | 365d |
|---|---|---|---|---|
| ≤10% | 0.788% | 1.82% | 10.90% | 10.96% |
| ≤5% | 0.706% | 0.72% | 5.42% | 5.60% |
| ≤2% | 0.620% | 0.14% | 1.96% | 2.26% |

**(c) Lowering the $500/bet hard cap alone** (stake fraction unchanged):

| Cap | Engages at bankroll | 30d | 182d | 365d |
|---|---|---|---|---|
| $500 (current) | ~$43,365 | 17.52% | 49.18% | 49.18% |
| $250 | ~$21,683 | 17.52% | 42.52% | 42.52% |
| $100 | ~$8,673 | 17.52% | 32.88% | 32.88% |
| $50 | ~$4,337 | 17.32% | 24.86% | 24.86% |

**Key finding driving the recommendation:** (c) has **zero measurable effect on the 30-day horizon** at any cap level tested — the cap only binds once a path has already compounded well past its (lower) engagement bankroll, so it cannot reduce the near-term ruin risk that dominates GG-071's finding. It has a real but comparatively weak effect at 6-12 months. (a) and (b), by contrast, act on every bet starting day 1 and are dramatically more effective per unit of expected-growth sacrificed — a 2.0x de-rate (stake_frac 0.577%, roughly half of `DEFAULT_KELLY_FRACTION`'s current 0.25 fractional-Kelly multiplier) reduces 1-year kill probability from 49.18% to 1.44%, a level consistent with the project's actual risk tolerance at this stage (pre-G6, paper trading, zero live capital at risk but real evidentiary cost to a permanently halted paper book).

(a) and (b) are mathematically nearly the same lever (both reduce the effective stake fraction uniformly); (b) is presented as a more principled framing — pick a target ceiling, solve for the implied fraction — while (a) is presented as the more implementable framing, since it maps directly onto an existing, named risk.py constant (`DEFAULT_KELLY_FRACTION`) rather than requiring a new search procedure to run before every parameter change.

---

## Decision (PROPOSED — awaiting operator sign-off)

**Recommend adopting a cadence-aware de-rating of `execution_bands.py`'s `T1_MULTI_DAY.kelly_fraction` for T1 MLB, targeting an effective stake fraction of ≈0.70% (the formal ≤5%-1yr-kill-probability target from sensitivity direction (b)), which the sensitivity table above shows brings 1-year kill-switch probability from ~49% to ~5.6%** — a level consistent with "this system should not have close to a coin-flip chance of permanently halting its own paper-trading evidence accumulation before G6 is reached," selected by the operator (2026-07-04) over the steeper 2.0x-de-rate (~1.2%/1yr) and the shallower 1.5x-de-rate (~9.5%/1yr) alternatives.

The observed 1.153% average stake fraction is a *function* of `kelly_fraction` combined with the real edge/odds distribution of fired bets, not a directly configurable constant itself, but `_compute_kelly_size` scales linearly in `kelly_fraction` — so a target of 0.704%/1.153% ≈ 0.610x of the current average implies **`T1_MULTI_DAY.kelly_fraction` ≈ 0.10 × 0.610 ≈ 0.061** (down from the current 0.10, set by ADR-0010).

**Do not lower `_HARD_LIMITS["max_single_event_exposure_usd"]` ($500 cap) as the primary remediation.** The sensitivity data show it is not effective at the horizon (30 days) where the largest share of the cited ruin risk materializes. It remains a legitimate secondary backstop and is not being removed.

**This ADR does not change any live parameter by itself.** Per Hard Rule 3 (ADRs immutable once accepted), ADR-0010 (which set the current 0.10 value) cannot be edited directly — this ADR, once accepted, supersedes ADR-0010's T1 kelly_fraction value specifically. The operator (Earl) must explicitly accept this document before `execution_bands.py` is edited. No code change has been made to `execution_bands.py` or `risk.py` in this session as of this correction.

---

## Consequences (if accepted)

- `execution_bands.py`'s `BAND_CONFIGS[ExecutionBand.T1_MULTI_DAY].kelly_fraction` changes from `0.10` to `0.061`, with the inline comment updated to reference this ADR as superseding ADR-0010's value for this field.
- `risk.py`'s `DEFAULT_KELLY_FRACTION` is left at `0.25` (unchanged) — it is inert for T1 MLB's live path and is not part of this remediation. If a future band is added that relies on `RiskEngine`'s default rather than an explicit `kelly_fraction` argument, that default's value should be reviewed on its own merits at that time, not coupled to this decision.
- T1 MLB would see roughly a 39% reduction in average stake size (0.061/0.10) and a correspondingly slower bankroll growth path — this is the deliberate tradeoff: EV/bet is unchanged, but variance and compounding-driven ruin risk both fall.
- G6's 30-resolved-paper-bet accumulation continues under the new sizing; no bet history is invalidated (this is forward-looking only).
- If accepted, T-223 closes and GG-071's status updates to RESOLVED with a reference to this ADR.
- `mc_forward_projection.py` (T-223) becomes a standing tool — re-run periodically (recommended: whenever `T1_MULTI_DAY.kelly_fraction`, real win rate, or real bet cadence materially shift) rather than a one-off artifact, since GG-071's core lesson is that this risk must be monitored under a forward-time lens, not just a terminal-P&L lens.
- **Not addressed by this ADR:** whether T4 MLB (flat 1-contract sizing per ADR-0023, not Kelly-scaled) carries an analogous compounding risk. T4's sizing mechanic is structurally different (flat, not proportional) and was out of scope for this review; if T4 sizing is ever changed to a proportional/Kelly mechanic, this analysis must be re-run for T4's own cadence (~1,000+ evaluations/game) before activation.

---

## Open items if this ADR is accepted

1. Update `execution_bands.py`: `T1_MULTI_DAY.kelly_fraction: 0.10` → `0.061`, with the inline comment updated to reference this ADR (superseding ADR-0010 for this field only).
2. Update `t4_execution_engine.py:961` and `tests/test_execution_bands.py:181` — both reference "`DEFAULT_KELLY_FRACTION = 0.25`" as if it were the governing T1 MLB ceiling; it is not (it's an NBA T4-PROJ-scoped literal ceiling unrelated to this change) — decouple the comments from `risk.py`'s constant to prevent future conflation of the kind this correction just resolved.
3. Update `scripts/run_monte_carlo.py:43`'s `DEFAULT_T1_KELLY = 0.25  # DEFAULT_KELLY_FRACTION in risk.py` comment — it already carries the same wrong-constant assumption; correct it to reference `execution_bands.py`'s real value.
4. Re-run `scripts/mc_forward_projection.py` against the new `kelly_fraction` once real T1 MLB bets have accumulated at the new sizing, to confirm the observed effective stake fraction lands near the targeted 0.70% (the relationship is linear in theory but real bet-level edge/odds distribution could shift the realized average).
5. Close GG-071 and T-223 with a reference to this ADR's acceptance.
