# Iteration Plan — Edge + Ruin Remediation (post-MC, 2026-07-22)
**Origin:** empirical-bootstrap MC (`05_RESEARCH_EXPERIMENTS/MC_EMPIRICAL_BOOTSTRAP_2026-07-22.md`) + GG-105/GG-124.
**Structure:** 4 parallel workstreams (one terminal window each). Each window launches its **own git worktree** (`scripts/new_session_worktree.sh <slug>`) and claims its ID range (`scripts/claim_session.sh`) per Hard Rule 10 — no shared-tree collisions.

## Problems this plan closes
1. **No edge (current epoch is negative on both books)** — overconfidence / anti-predictive calibration (GG-105).
2. **Can't measure** — epoch churn keeps resetting `clean_n` to 0 across all bands (GG-124).
3. **Ruin geometry (NEW)** — MAIN book's ~1%/bet variance × 15 bets/day trips the 20% DD kill ~100%/yr *even at zero edge*. Edge fixes alone won't survive the current sizing/kill-switch geometry.
4. **T4 is edge-limited, not ruin-limited** — clean T4 survives; it just doesn't have edge yet. Different fix than MAIN.

---

## Sequencing at a glance
```
NOW (parallel):   A1 ─┐        B1→B2 ──┐        C2, C3 ──┐        D1, D2 ──┐
                      │                │                 │                │
GATE 1 (needs A1+D1): A2 (refit + calibration gate) ─────┘                │
                      │                                                    │
GATE 2:               A3 (if A2 fails)      B3 (needs B2+A2)   C1 freeze (needs A2 lands)
                      │
RESUME G6 PURSUIT when: A2 passes calib gate  AND  B frontier admits survival  AND  C1 freeze lets clean_n → n*
```
Critical path is **A** (calibration). **B/C/D run fully in parallel now** and de-risk A.

---

## WINDOW A — Calibration / edge (critical path)
Slug: `a-calibration`. Owns the alpha fix. Sequential internally.

- **A1. Land `ba_l10` shrinkage in C2 (APR-0025).** Shrink noisy rolling stats toward a prior: `ba_l10_shrunk = (ab_sum·ba_l10 + K·PRIOR)/(ab_sum + K)`. Tune K on holdout. This is the leading-mechanism fix for overconfidence-at-extremes. *Do not deploy to a live epoch yet — evaluate via Window D first.* → blocks A2.
- **A2. Refit C3 (LR+Platt) on shrunk features; run the calibration gate.** Pass criteria: edge-tercile monotonicity **no longer anti-predictive** (Fisher p > 0.05, positive slope), calibration slope CI includes 1.0, Brier/ECE ≤ MLB baselines (ADR-0046). Needs A1 + D1 harness. → gates GATE 2 + resume.
- **A3. (Contingency) If A2 fails:** escalate model-class review superseding ADR-0004 — isotonic recalibration and/or feature-set expansion; re-run A2. Do **not** ship temperature scaling as the fix — the ledger what-if showed T-scaling *worsens* the tercile pattern.

## WINDOW B — Ruin geometry (parallel, uses the MC engine)
Slug: `b-ruin-geometry`. Independent of A. Tool = `scripts/mc_empirical_bootstrap.py`.

- **B1. Register the new gap:** current MAIN sizing/variance/kill-switch geometry trips 20% DD ~100%/yr at zero edge → risk config self-terminates before any edge can prove out. (GG entry + DECISION_LOG.)
- **B2. Compute the survivable-edge frontier** per book: min per-bet edge (given real variance + cadence) to hold 1yr P(kill) below target (e.g. ≤10%), and the max Kelly fraction / DD-switch width / cadence that lets a *true* positive edge survive. Sweep with the MC engine. → feeds B3 + resume gate.
- **B3. Draft ADR superseding ADR-0040** with variance-aware sizing: edge must clear a variance-scaled threshold; evaluate lower Kelly fraction, per-bet cap, reduced cadence, and/or a wider/rolling drawdown switch. Needs B2 + A2's post-fix edge estimate.

## WINDOW C — Measurement / stabilization (parallel)
Slug: `c-measurement`. C2/C3 start now; C1 waits on A2.

- **C2. Decouple bug-fix epochs from calibration-logic epochs (GG-124).** Only bump the logic epoch for the band actually touched, so a fix on one band doesn't zero every band's `clean_n`. Start now.
- **C3. Standing C7 monitor:** edge-tercile monotonicity + calibration slope per band, warn-only (GG-098 discipline), so a regression is caught live rather than at the next audit. Start now.
- **C1. Stabilization freeze (after A2 lands):** once the calibration fix is in, freeze that band's logic and let `clean_n` accumulate to its `n*` (GG-004). Define + document the freeze protocol; no logic edits during the window.

## WINDOW D — Validation harness (parallel, de-risks A & B)
Slug: `d-harness`. Start now; D1 unblocks A2.

- **D1. Offline replay/what-if harness:** re-score the resolved ledger under a candidate feature/model change **without deploying** (no epoch bump). This is the anti-churn lever — test the shrinkage on real bets before it ever touches a live epoch. → unblocks A2.
- **D2. Wire `mc_empirical_bootstrap.py` as the standard forward-risk gate** for any sizing or edge change (retire `mc_forward_projection.py` from that role). Any B3/A change must pass this MC before deploy.

---

## Resume-live-pursuit gate (all three required)
1. **A2 passes** the calibration gate (edge no longer anti-predictive).
2. **B frontier** shows the risk config admits survival at the post-fix edge (1yr P(kill) ≤ target).
3. **C1 freeze** is in force and `clean_n → n*` is accruing on the active band.

Until all three: no live capital, no external edge claim. Structural-green first, math-green second — in that order, no time limit.
