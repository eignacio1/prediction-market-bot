# A/B Edge-Delta Harness — Spec & Usage

**Files:** `ab_harness.py` (framework) · `run_ab_experiment.py` (driver/registry)
**Purpose:** the standing gate every strategy/config change must pass before activation — including future PAM / psychological-gradient / multi-factor enhancers. "The methodology is the asset."

## The bar a change must clear

A change is **adopt-worthy** only if it produces a **DEFENSIBLE_IMPROVEMENT**: a bootstrap Δ(metric) 95% CI that **excludes 0**, on **n_B ≥ 30** (MIN_N, ADR-0005 paper floor), that **survives holdout** (rule fit/selected on train days, scored on unseen test days). In-sample gains are presumed noise-fitting until holdout confirms — EXP-017C showed realized P&L at n≈151 is variance-dominated, so in-sample "wins" are cheap and misleading.

## Concepts

- **Record**: EXP-017B loader dict — direction-aware `_fne` (recomputed per GG-077, never the stored field), `_model_p`, `_mip`, `_dir`, `_win`, `_pnl`, `_size`, `_thr`, plus reconstructed binary `_event`. `pnl`/`size` are immutable realized ground truth.
- **Strategy** (`ab_harness.Strategy`): `name`, `description`, **`hypothesis`** (pre-register the expected direction *before* running), `select(rec)->bool`, optional `rescore(rec,params)->model_p`, optional `_fitter(train)->params`. Rescoring changes selection + calibration metrics only, never a bet's pnl.
- **Primary metric**: `pnl_per_dollar` (Σpnl/Σsize) — sizing-neutral, so a variant can't win just by resizing. Also reports EV/bet ($), win rate, Brier, calibration slope.
- **Comparison**: paired bootstrap when B ⊆ A (nested — the normal case for filters), else independent. Paired preserves shared-bet covariance and is the correct, tighter test. Reports Δ point, 95% CI, P(Δ>0), and for filters the removed-vs-kept diagnostic (a filter is only defensible if the bets it drops are distinguishably worse).
- **Verdicts**: `DEFENSIBLE_IMPROVEMENT` / `HARMFUL` / `INCONCLUSIVE` / `UNDERPOWERED`.

## Usage

```bash
# default: in-sample + holdout on the live cached book, cutoff 2026-07-03
python3 scripts/run_ab_experiment.py

# tune holdout split, bootstrap depth, seed, portfolio
python3 scripts/run_ab_experiment.py --cutoff 2026-07-04 --boot 20000 --seed 17 \
    --portfolio logs/.vps_portfolio_cache_mlb.json
```

Output: console table + `exp_output/EXP-017D-ABHARNESS/exp017d_abharness_results.json`.

## Adding a new variant (e.g., a PAM enhancer)

In `run_ab_experiment.py::build_strategies()` append a `Strategy`:

```python
H.Strategy(
    name="pam_overlay_v1",
    description="Down-weight bets where PAM environment-classifier flags adverse park/weather.",
    hypothesis="PAM-adverse bets underperform -> excluding them IMPROVES $/staked.",  # pre-register!
    select=lambda r: not r.get("pam_adverse", False),   # requires the field to be logged
)
```

Then run in **holdout** mode and require `DEFENSIBLE_IMPROVEMENT` on the test split before proposing activation. If the enhancer needs learned params, supply `_fitter` (fit on train only) and `rescore`.

## Discipline rules

1. **Pre-register the `hypothesis`** string before looking at results.
2. **Holdout is the deciding mode.** In-sample is diagnostic only.
3. **Mind multiplicity.** Each variant×mode is a test; a lone ~95% result across many tests is weak. Prefer dual-mode agreement.
4. **Re-run as n grows.** Most verdicts are UNDERPOWERED/INCONCLUSIVE purely because n is small today; the harness discriminates far better toward Tier 2 (n≥500).
5. **A rejected variant is a logged result**, so it isn't silently re-proposed.

## Provenance

Reuses audited helpers from `run_exp017_mlb.py` (fee/edge, GG-077 direction-aware), `run_exp017b_decomp_mlb.py` (loader/buckets), `run_exp017c_calibration_mlb.py` (logit/sigmoid/IRLS). First run: EXP-017D (2026-07-06) evaluated quarantine_YES (DEFENSIBLE, both modes), min_edge_0.10 (UNDERPOWERED), edge-band filter (INCONCLUSIVE), platt_recal (null/harmful). See `exp_output/EXP-017D-ABHARNESS/FINDINGS_ab.md`.
