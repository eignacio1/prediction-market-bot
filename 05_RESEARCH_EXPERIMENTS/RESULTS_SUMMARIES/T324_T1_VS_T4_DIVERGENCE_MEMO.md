# T-324 — T1-vs-T4M-PROJ Divergence Memo

**Date:** 2026-07-10
**Author:** Session (Workstream B3, T-322/T-323/T-324)
**Status:** Analysis only — no code changes. Feeds GG-004.
**Inputs:** `scripts/run_band_monitor.py` (T-322, clean_n only) and
`scripts/run_power_calc.py` (T-323), both run against a live VPS pull
(`logs/.vps_portfolio_cache_mlb.json`, `logs/t4_mlb_resolved_ledger.jsonl`),
2026-07-10.

---

## 0. The task's framing does not match what the clean data shows — correct that first

T-324 was scoped as: *"quantify why T4M-PROJ reads positive while T1 reads
negative/anti-predictive."* That premise came from CLAUDE.md's existing
narrative (raw, pre-clean_n reads). **On `clean_n` — the CURRENT_LOGIC_EPOCH
cohort, with GG-077/GG-087 write-path contamination excluded — the result is
inverted from that premise:**

| Band | clean_n (raw_n) | Edge-monotonicity verdict | Fisher p | Aggregate EV/bet | Win rate |
|---|---|---|---|---|---|
| **T1** | 65 (214) | **INCONCLUSIVE** | 1.000 | +$1.053 | 55.4% |
| **T4M-PROJ** | 271 (515) | **ANTI-PREDICTIVE** | 0.024 | +$0.047 | 65.7% |

T1 is not "negative" on clean data — it is inconclusive, and its raw aggregate
EV/win-rate are both positive. T4M-PROJ is not simply "positive" — its
aggregate EV/win-rate are positive, but its edge-monotonicity test fails
significantly. The rest of this memo quantifies why, and decomposes T4M-PROJ's
finding against the three candidate explanations the task specified: real
signal, sizing artifact, or pre-epoch bug residue.

---

## 1. T1: inconclusive is a structural property of the test, not evidence of "no problem"

T1's edge-monotonicity Fisher test compares win rate between positive-edge and
negative-edge bets. On clean_n=65: **64 positive-edge, 1 negative-edge.**
Fisher's exact test cannot produce a meaningful p-value from a 64:1 split —
`fisher_pvalue=1.0` here reflects a degenerate contingency table, not a
finding of "no relationship."

This is structural, not incidental: T1's own bet-placement rule is `model_p >
MIP + vig` (CLAUDE.md's edge condition) — the strategy only ever bets when it
computes a *positive* edge. A negative-edge case in the closed-position ledger
can only arise from post-decision drift (price moved between evaluation and
fill) or a fee-recomputation sign flip at settlement. Under this design, the
edge-monotonicity test as currently built is close to structurally unable to
produce a contrast group for any band that gates on positive edge — it needs
substantial edge-sign noise between decision-time and settlement-time to work
at all, and T1 mostly doesn't have that.

The tercile view (bins by edge magnitude among the 65) is the more informative
read for T1, and it is *not* monotonic in either direction:

| Tercile | n | edge_mean | win rate | pnl |
|---|---|---|---|---|
| 1 (smallest edge) | 21 | 0.037 | 47.6% | −$16.70 |
| 2 | 22 | 0.062 | 59.1% | +$39.15 |
| 3 (largest edge) | 22 | 0.094 | 59.1% | +$46.00 |

Win rate rises from tercile 1→2 then flattens 2→3 — consistent with *some*
positive relationship between edge size and outcome, but far too noisy at
n=21-22/bin to call. Calibration slope 0.82 ("overconfident") has a 95% CI of
[0.22, 1.68] that comfortably includes 1 — not a significant miscalibration
finding at this n. **T1's honest status on clean data: genuinely
underpowered to say anything, not quietly negative.**

---

## 2. T4M-PROJ: the anti-predictive finding is not a thin-cell artifact

The Fisher pos/neg split (252 positive-edge @ 63.9% win vs. 19 negative-edge @
89.5% win, odds ratio 0.208, p=0.024) could, on its own, be dismissed as noise
from a thin 19-count cell. **It cannot be dismissed that way once the tercile
breakdown is checked — the same inversion shows up as a clean, monotonic trend
across three roughly equal, non-thin bins:**

| Tercile | n | edge_mean | win rate | pnl |
|---|---|---|---|---|
| 1 (smallest edge) | 90 | 0.017 | **74.4%** | +$2.41 |
| 2 | 90 | 0.087 | **64.4%** | +$2.77 |
| 3 (largest edge) | 91 | 0.203 | **58.2%** | +$7.46 |

Win rate falls monotonically as the model's own computed edge *increases* —
90/90/91 bins, no small-cell dependency. This is the same direction of effect
as the Fisher test, now visible without relying on the thin negative-edge cell
at all. That convergence across two different statistical views of the same
clean cohort is what elevates this from "maybe noise" to "a real pattern in
the current live data."

Two things this pattern is *not*, given the diagnostics available:

- **Not a calibration-only problem.** Brier (0.198) is the best of any band
  measured this session, and REL/RES/UNC decomposition recomposes correctly
  (`recompose_ok=True`). The model's raw probability estimates are not
  obviously miscalibrated in aggregate (slope 0.73, CI [0.51, 1.01] — borderline,
  does not cleanly exclude 1). The anti-predictive signal is specifically in
  how *edge magnitude* relates to *win probability*, not in `model_p`'s
  calibration against the resolved outcome in general.
- **Not a P&L-driven artifact.** The Fisher/tercile tests are win/loss counts,
  unweighted by stake. Whatever is producing the inversion is present in the
  raw outcome data before Kelly sizing ever touches it.

---

## 3. Decomposition against the three candidate explanations

**(a) Real signal problem — most consistent with the evidence.**
T4M-PROJ's live edge computation (`model_p` from the live in-game Bayesian
update, minus current MIP, fee-adjusted) is producing its *largest* edges in
situations that go on to win *less* often, not more. Mechanically plausible
causes, none yet tested: the live-state features (h_so_far, ab_so_far, inning,
score state) may push `model_p` toward extreme values precisely in game states
that are structurally noisy (small remaining-AB samples, blowout score states)
rather than states where the market has genuinely failed to reprice — i.e.,
T4's core latency thesis ("the market hasn't updated yet, the bot has") may be
false in exactly the situations where the bot currently computes its biggest
edges. This is a testable, specific next step (see §4), not yet diagnosed.

**(b) Sizing artifact — ruled out for *this* finding, flagged as a compounding risk.**
The Fisher and tercile results are unweighted win/loss counts; bet size cannot
produce this pattern by construction. However, if T4M-PROJ's Kelly sizing
scales with computed edge magnitude (larger computed edge → larger stake) —
which ADR-0010/ADR-0039's Kelly-fraction design implies — then this
anti-predictive relationship, if real, means the band is currently *sizing up
into its worst bets*. The aggregate EV/bet (+$0.047) is barely positive; a
size-weighted view of this same inversion has not been run and should be, since
it could show a materially worse (or already-masked-negative) picture than the
unweighted numbers here.

**(c) Pre-epoch bug residue — ruled out by construction.**
This entire analysis used `clean_n` (CURRENT_LOGIC_EPOCH=3 only), which by
definition excludes every record touched by GG-087 (T4 YES-only signal-discard
bug) or GG-077 (fee_net_edge sign-convention bug). Edge values were also
independently recomputed via the audited `compute_fee_net_edge` helper in
`build_t4_resolved_ledger.py` (not read from any stored `edge`/`fee_net_edge`
field), which is the same defense-in-depth GG-100 established against
measurement-only sign errors. Nothing in this finding traces to either known
contamination boundary.

**Working conclusion: (a) is the leading explanation.** This looks like a
genuine, currently-unexplained anti-predictive relationship between T4M-PROJ's
live edge computation and actual win outcomes, on clean, bug-free data — not
an artifact of the two known historical bugs, and not explainable by sizing
mechanics alone (though sizing may be amplifying its P&L impact).

---

## 4. Caveats and what this memo does not establish

- **Not yet at G6 power.** Per T-323, T4M-PROJ's own clean cohort (n=271)
  is still below the n*=836 needed for 95%-power detection of `edge>0` vs
  `edge=0` at its observed effect size — and that power target is a different
  question (is mean P&L positive) from the anti-predictive finding here (does
  edge rank-order win probability correctly). A finding significant at
  p=0.024 with n=271 is real, but should not be treated as a final,
  large-sample verdict — it should be re-checked as clean_n grows.
- **Cadence caveat carries over from T-323.** The clean epoch is only ~4 days
  old for T4M-PROJ (2026-07-06 to 2026-07-10); this tercile pattern is drawn
  from a short, possibly non-representative window (e.g., a run of games with
  unusual score-state distributions). Re-run this decomposition as more
  clean-epoch days accrue before treating the trend as stable.
- **No live-state segmentation performed.** This memo did not break the
  tercile finding down by inning, score-differential, or ab_remaining — that
  is the natural next diagnostic step (hypothesis (a) above) and was out of
  scope for this analysis-only pass.

---

## 5. Recommendation

1. **Do not treat T4M-PROJ's positive aggregate EV as evidence the band is
   healthy.** A statistically significant, tercile-monotonic inversion between
   computed edge and win rate on clean data is a more specific and more
   concerning signal than a thin positive aggregate EV built on n=271. This
   should be surfaced to GG-004/G6 gate discussion directly, not folded into
   the existing DIRECTIONAL_POSITIVE narrative unchanged.
2. **Run a size-weighted version of this same decomposition** to check whether
   Kelly sizing is amplifying the inversion's P&L impact (candidate (b) above).
3. **Segment the T4M-PROJ tercile finding by live game state** (inning,
   score differential, ab_remaining) as the next diagnostic step toward
   candidate (a) — this is the most direct way to test whether large computed
   edges are concentrated in structurally noisy game states rather than
   genuine market-latency situations.
4. **Do not read T1's INCONCLUSIVE verdict as "T1 has no problem."** It reflects
   a structural limitation of the edge-monotonicity test on a band that gates
   on positive edge by construction, not a clean bill of health. T1's own
   tercile trend (47.6%→59.1%→59.1%) is mildly encouraging but far too small
   (n=21-22/bin) to draw a conclusion from.
