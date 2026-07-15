# APR-0025 decision brief (T-366) — one page for Earl

**What this is:** APR-0025 (`00_ADMIN/APR-0025_gg105-ba_l10-shrinkage-remediation.md`,
Status PROPOSED) proposes a fix for GG-105 (T4M-PROJ MLB's anti-predictive/miscalibration
pattern). This brief distills the tradeoff so you don't have to parse the full APR + its
upstream chain (T-333 → T-344 → T-359 → T-361).

## The proposal

Shrink `ba_l10` (a noisy ~10-game rolling batting average, currently used as a fixed,
unregressed per-AB probability) toward the cohort's own observed-mean prior (0.2512) at the
point it feeds `p_hits_gte_threshold()` in `run_t4_mlb_live.py` (and the dark
`t4_mlb_execution_engine.py:174`). Strength is controlled by a pseudo-count `k` — higher k
pulls every player's `ba_l10` harder toward the cohort average.

## The dose-response tradeoff (T-359, n=666, epoch-3 frozen cohort)

| k (shrinkage strength) | Fisher p (anti-predictive test) | win-rate gap (pos-edge / neg-edge) |
|---|---|---|
| 0 (no shrinkage — status quo) | <0.0001 | 0.530 / 0.716 |
| 40 | 0.0045 | — |
| 80 | 0.0797 | — |
| 160 (most aggressive tested) | 0.1552 (INCONCLUSIVE) | 0.563 / 0.619 |

Reading it: more shrinkage → weaker statistical signal that the pattern is anti-predictive.
The gap between pos-edge and neg-edge win rates compresses as k rises. This is real,
monotonic support for shrinkage as a mechanism — not a forced conclusion.

**APR-0025 does not pick a k for you.** It names k=40 as "the lightest-touch value that
already reaches conventional significance" — i.e. the smallest nudge that changes the
statistical picture — but explicitly declines to recommend it as *the* answer. Choosing k is
your call.

## The catch — read this before signing off

**Shrinkage attenuates the pattern. It does not eliminate it, even at k=160, the most
aggressive setting tested.** The anti-predictive direction survives every k value tried.
APR-0025 states this plainly rather than glossing over it: this is a **partial mitigation**,
not a fix. A second, untested mechanism — H2, blending T1's calibrated `p_t1` into `p_t4`
rather than discarding it — is flagged as the necessary follow-on investigation. Signing off
on APR-0025 buys attenuation, not closure of GG-105.

## AB_WINDOW=37 — checked this session, not resolved

APR-0025 also flags that the sweep above used a fixed `AB_WINDOW=37` assumption (stated, not
fitted) instead of each player's real rolling AB count. T-365 (this window, same session)
checked whether that's fixable from data already on disk: **it isn't** — the real number is
computed transiently and never persisted anywhere; getting it requires ~75 live MLB Stats API
calls (one per unique player in the cohort), not done this session. This doesn't block your
decision — APR-0025 already disclosed the heuristic as unverified and didn't build k=40's
case on 37 being exactly right — but the dose-response table above hasn't been re-validated
against real AB counts. Registered as follow-on (T-367).

## Adjacent, not blocking: GG-119 (Window 1, same day)

Separately, Window 1 confirmed a **different, related bug in T1** (not T4M-PROJ, not GG-105) —
the same vig-sign-flip pattern GG-113 fixed for T4M-PROJ also exists in T1's
`_directional_edge()`. Quantified: 74 of T1's 248 resolved NO bets (28.6% of the whole T1
book) only cleared the edge-approval floor because of the bug; that subgroup lost -$48.26
net. T2 was checked and ruled out (no NO-direction branch exists in its formula). This is a
**separate open decision** awaiting your sign-off (GG-119, T1-scoped fix mirroring ADR-0043) —
unrelated to APR-0025's shrinkage question except that both are entries in the same "vig-sign
bug family" this project keeps finding. Doesn't change anything about the APR-0025 decision
above; flagged here only so you have both open asks in one place if you're doing sign-offs
in one sitting.

## Bottom line

Three independent decisions on the table, only the first is what APR-0025 itself asks for:
1. **APR-0025:** authorize shrinkage as a partial mitigation for GG-105, and pick a `k`
   (or request H2 be tested first before committing to any k).
2. **T-367 (optional, not blocking #1):** authorize the live AB_WINDOW re-pull to validate
   the sweep against real per-player AB counts.
3. **GG-119 (separate gap, not part of APR-0025):** authorize a T1-scoped sign-fix mirroring
   ADR-0043, same shape as the GG-113 decision you already made.
