# EXP-025 — HYP-010 Phase 2, NB refit pre-registration

**Date:** 2026-08-28
**Session:** T-500 / GG-221
**Registered against:** HYP-010 (existing hypothesis — this is NOT a new hypothesis number)
**Predecessor:** EXP-022 / T-487 / GG-207 (Poisson half, verdict INCONCLUSIVE-EXTEND ARCHIVE, `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T487_EXP022_GATE23_RESULT.md`)

**PRE-REGISTRATION IS A HARD GATE, NOT A FORMALITY.** This document is committed
before any NB code is written or run. Every parameter below is fixed now,
against T-487's own already-disclosed measurement, not tuned against this
run's outcome. If the committed timestamp on this file is later than the
timestamp of any `scripts/exp025_*.py` run output, the gate was violated —
check for that directly, do not take my word for it.

---

## (a) NB parameterization and dispersion estimator

**Form: NB1 (linear mean-to-variance), not NB2.** `Var(Y) = phi * E[Y]`, phi
constant across all games (mean-independent dispersion ratio), as opposed to
NB2's `Var(Y) = mu + mu^2/r` (quadratic in the mean). NB1 is the direct,
literal generalization of "Poisson assumed var/mean=1, real data measured
var/mean=2.33" — it multiplies the Poisson variance by a constant factor and
nothing else. No other functional form is fit or compared.

**Dispersion estimate: phi = 2.33, fixed, method-of-moments, taken verbatim
from T-487's own disclosed measurement** (`var/mean=2.33` on n=3,954 real
2026 team-game runs, stated in `T487_EXP022_GATE23_RESULT.md`). This is not
re-estimated from the 214-game totals archive and not tuned against this
run's P&L outcome — using the same fixed constant T-487 already published
before this pre-registration was written is what keeps this a single-variable
test (distribution only) rather than a second free parameter search.

**Per-game construction.** The Poisson model's mean, `mu_total =
mu_home + mu_away` (unchanged — see (b)), is preserved exactly as computed by
`exp022_totals_backtest.py`'s `_blend()`. Home and away team runs are modeled
as independent NB1(mu_home, phi) and NB1(mu_away, phi) variables with a
**shared** dispersion ratio phi. Under NB1's `p = 1/phi` (constant) and
`r = mu/(phi-1)` (per-team) parameterization, two NB variables sharing the
same `p` sum exactly to another NB variable: `NB(r_home, p) + NB(r_away, p) =
NB(r_home + r_away, p)`. This gives a closed-form total-runs distribution:

```
p = 1 / phi                          # constant, phi=2.33 -> p ≈ 0.4292
r_total = mu_total / (phi - 1)       # varies per game with mu_total
model_p = 1 - NB_CDF(n_min - 1; r_total, p)   # P(total_runs >= n_min)
```

implemented via `scipy.stats.nbinom(r_total, p).sf(n_min - 1)`.

**Stated assumption, not verified here:** home and away team runs are treated
as conditionally independent given their L10 blend means, matching the
Poisson model's own independence assumption in `exp022_totals_backtest.py`
(`mu_total = mu_home + mu_away` with no covariance term). This NB refit does
not introduce or relax that assumption — it is inherited unchanged from
EXP-022 so that dispersion is the only variable under test.

---

## (b) Selected-subset rule — unchanged, and how NB changes what it selects

Identical rule, identical threshold, identical formula:
`abs(model_p - yes_mid) > 0.010` (`EDGE_THRESHOLD = 0.010`, unchanged from
EXP-022). Identical direction logic for buy-YES vs buy-NO. Identical
game-level aggregation (P&L averaged within `event_ticker` before computing
`clean_n`, `mu`, `sigma` — "independent unit is the game," per
`HYP010_PHASE2_PREREGISTRATION_2026-08-15.md` line 134).

**Resolved interpretation (this was flagged as ambiguous in this session's
prior research pass and is locked here before any code runs):** the rule is
re-applied mechanically to **NB's own `model_p`**, computed on the same fixed
input pool — the same 214 archived `KXMLBTOTAL` closing pregame snapshots,
the same outcome store join, the same `mu_total` per game. It is **not**
forced to reproduce the same 207 game IDs T-487's Poisson run selected.
Reasoning: `mu_total` (the mean forecast) is unchanged between Poisson and
NB — only the tail probability `model_p = P(total >= n | mu_total)` changes,
because NB puts more mass in the tails than Poisson at the same mean. Forcing
NB to inherit Poisson's selected game set would mean scoring NB's P&L on a
subset chosen by a different model's edge criterion, which is not "the same
selected-subset rule" applied to NB — it is Poisson's selection with NB's
P&L bolted on. Applying the identical formula to NB's own probabilities, on
the identical unchanged data pool, is what "same input, corrected
distributional assumption — the single variable under test" (per the
original task framing) actually requires. The resulting `clean_n` may differ
from 207; that is an expected, reported consequence of the corrected
distribution, not a rule change. No new archive data, no re-pull, no widened
date window, no changed threshold value, no changed aggregation — those are
held fixed. Only the distribution feeding `model_p` changes.

---

## (c) Primary metric, test, and gate — unchanged

Primary and only gating metric: **P&L per bet on the selected subset**,
game-level (per-game mean P&L across all qualifying rows in that game),
one-sided alpha=.05, power=.95. `n*` computed live from this run's own
observed mean/sigma via the identical formula already in use in both
`exp022_totals_backtest.py` and `scripts/run_power_calc.py`:

```
n* = ((z_alpha + z_beta) * sigma / mu) ** 2      # z_alpha = z_beta = 1.6448536269514722
```

**Brier score (paired delta-Brier, model vs. market) remains DESCRIPTIVE
SECONDARY ONLY.** It is computed and reported for comparability with T-487's
output but is never a gate condition and never substitutes for the P&L
verdict, exactly as in EXP-022.

---

## (d) Verdict states — unchanged, no fourth state

Exactly the three states EXP-022 used, no relabeling:

- **PASS** — `clean_n >= n*` and `mu > 0`.
- **FALSIFIED** — `clean_n >= n*` and `mu <= 0`.
- **INCONCLUSIVE-EXTEND ARCHIVE** — `clean_n < n*` (regardless of sign of `mu`).

---

## (e) Pre-registered effect band — unchanged from EXP-022 / the 2026-08-15 doc

Expected effect size **+0.005 to +0.025 P&L/bet**. A result **above +0.03 is
SUSPECT** and must be audited for leakage (e.g., outcome-store join drift,
lookahead in the L10 stats blend) before being believed, not reported as a
clean PASS. This band is not adjusted for the NB refit — the underlying
economic edge, if any, should not change by an order of magnitude just
because the tail-probability model changed; a jump into "suspect" territory
under NB specifically would itself be evidence of a leakage interaction with
the distributional change, not a stronger result.

---

## (f) Multiplicity / second-look disclosure

This is a **second model fit to the same 214-game archive and the same
resolved-outcome join** T-487 already scored once (Poisson, INCONCLUSIVE).
No new data is being introduced to buy a second roll. The pre-registered
justification for treating this as a legitimate second look rather than
p-hacking:

1. **The dispersion correction was disclosed and specified in advance, by
   the prior experiment itself**, not chosen after seeing this run's result —
   T-487's own results file named `phi ≈ 2.33` and NB as "the natural next
   step" before this document existed.
2. **The subset-selection rule, threshold, aggregation, effect band, and
   verdict states are all held identical** to EXP-022 — the only free
   variable is the distributional family, and even that has its parameter
   (`phi`) fixed externally rather than fit to this run's outcome.
3. **This does not reduce the multiplicity cost to zero.** Two models have
   now been tested against the same 214-game, 207-ish-bet archive under the
   HYP-010 umbrella. If NB also lands INCONCLUSIVE or FALSIFIED, per the
   task's explicit instruction this session does **not** proceed to fit a
   third model class — it reports and stops. That constraint is the
   multiplicity control: at most two distributional fits against this
   archive within HYP-010 Phase 2 before the archive must grow (the existing
   INCONCLUSIVE-EXTEND ARCHIVE path) rather than trying a third family on
   the same 214 games.
4. Neither this document nor the resulting run relabels or revises T-487's
   Poisson verdict. It stands as recorded, independent of what NB produces.

---

## What will be reported after the run

Verbatim, per the task instruction: NB mean P&L/bet (game-level); NB sd; NB
`n*` re-derived from NB's own mean/sd; the verdict (PASS / FALSIFIED /
INCONCLUSIVE-EXTEND ARCHIVE); the fitted/used dispersion parameter (phi=2.33,
fixed — not fit) and whether the resulting model behavior reconciles with the
measured var/mean=2.33; and the routing written into
`04_EXECUTION/MARKET_EXPANSION_ACTION_PLAN.md` box 2.4.
