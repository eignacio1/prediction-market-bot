# Experiment Record — EXP-017D: A/B Edge-Delta Harness (build + first run)

**Status:** COMPLETE (framework is reusable/standing)
**Experiment ID:** EXP-017D (child of EXP-017C)
**Owner:** RL
**Hypothesis tested:** Do the candidate fixes from 017B/017C produce a DEFENSIBLE edge delta, or are they in-sample noise-fitting?
**Research question:** operationalize "the methodology is the asset" — a reusable activation gate for all future enhancers
**Started / Completed:** 2026-07-06

---

## Objective

Two jobs: (1) evaluate candidate fixes (YES-quarantine, min-edge/tail filter, edge-band filter, Platt recalibration); (2) stand up the reusable gate every future strategy change (PAM, psych gradients, multi-factor) must pass before live activation. Bar = bootstrap Δ CI excludes 0, n_B ≥ 30, and survives holdout.

## Data / Code Reference

| Item | Detail |
|------|--------|
| Portfolio | `logs/.vps_portfolio_cache_mlb.json` (n=151; holdout cutoff 2026-07-03 → train 50 / test 101) |
| Framework | `scripts/ab_harness.py` · Driver | `scripts/run_ab_experiment.py` · Spec | `scripts/README_ab_harness.md` |
| Base commit | e250a29 |
| Primary metric | pnl-per-$1-staked (sizing-neutral); paired bootstrap for nested (subset) strategies, independent otherwise |

## Results (Δ vs baseline, primary metric)

| Variant | in-sample | holdout | verdict |
|---------|-----------|---------|---------|
| quarantine_YES | Δ+7.8pp CI[+1.7,+15.0] P=99.6% | Δ+11.3pp CI[+2.4,+22.0] P=99.6% | **DEFENSIBLE (both modes)** |
| min_edge_0.10 | Δ+33pp CI[−10,+80] | Δ+30pp CI[−35,+96] n=11 | UNDERPOWERED (collapses OOS) |
| YESquar+min_edge_0.03 | Δ+8.3pp CI[−0.5,+18] | Δ+9.8pp CI[−3.2,+25] | INCONCLUSIVE |
| platt_recal_edge>0 | Δ+1.7pp CI[−6,+10] | Δ−6.5pp P=27% | INCONCLUSIVE→harmful |

## Interpretation

Only YES-quarantine clears DEFENSIBLE and survives holdout (P(kept>removed)=99.7–99.8%). The dramatic in-sample tail filter is noise (UNDERPOWERED, collapses OOS) — the harness's core value demonstrated: it kills the seductive in-sample winner. Edge-band filter adds nothing over the direction cut; recalibration is null→harmful (confirms EXP-017C). Methodological note: YES-quarantine reads DEFENSIBLE only under the *paired* bootstrap (correct for nested filters); naive independent bootstrap wrongly called it INCONCLUSIVE.

## Confidence

High that min-edge/recalibration are non-defensible (fail holdout). Medium-High that YES-quarantine is real (dual-mode, n_removed=11). High in the harness as the standing enhancer gate.

## Verification

Invariants pass (baseline n=151; train+test=50+101=151); determinism confirmed (md5 identical across runs); paired vs independent both implemented, nesting auto-detected.

## Follow-Up

| Action | Owner | Ref |
|--------|-------|-----|
| Operator/DS sign-off to adopt YES-quarantine flag | AO/DS | ADR-0042 / T-250 |
| Route future PAM/enhancers through harness holdout gate | RL | T-252 / GG-094 |
| Re-run 017B/C/D as sample grows toward Tier 2 | RL | T-251 |

## Links

- Findings: `exp_output/EXP-017D-ABHARNESS/FINDINGS_ab.md` · JSON: `exp_output/EXP-017D-ABHARNESS/exp017d_abharness_results.json`
- Parent: EXP-017C · Governance: ADR-0042, GG-004, GG-094
