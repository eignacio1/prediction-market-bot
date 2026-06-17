# ADR-0027 — Probability Calibration Layer (Temperature Scaling)

**Status:** ACCEPTED — 2026-06-16
**Decision makers:** DS (Earl Ignacio) / operator directive (SESSION 64)
**Amends:** ADR-0004 (model class — LR+Platt as the nominal C3 model), ADR-0015 (opponent-adjusted Poisson T1 probability). The production T1 probability now passes through a calibration layer before the edge gate and Kelly sizing read it. ADR-0004/ADR-0015 remain in force.
**Supersedes:** —
**Closes:** GG-037 (calibration half — the overconfidence). **Does NOT close** the GG-037 edge-inversion / GG-004 alpha question (see Consequences).
**Related:** GG-008 (Poisson per-threshold p_est), ADR-0024 (sample adequacy), ADR-0016 (fee-net edge), GG-004 (commercial validation).

---

## Context

### What GG-037 found

The full-database assessment of the re-frozen 158-bet NBA Finals dataset
(`data/nba_finals_clean_dataset.csv`) showed the model is **systematically
overconfident**: directional Brier 0.2308 (a coinflip is 0.25), mean stated
confidence **0.799** vs realized win rate **0.601** — ~20 points overconfident,
worst in the high-confidence buckets (72 of 158 bets predicted 0.97, realized
0.79). Because Kelly sizing is monotone in the probability, the overconfidence
directly **inflated stakes on the worst-calibrated bets**.

### Where the overconfidence actually lives

The production T1 betting probability is **not** the LR+Platt model
(`prod_model.joblib`). That model only produces `p_estimate_lr` for C6 logging on
cohort players. The probability that drives the edge gate and Kelly sizing is the
**pure Poisson** survival probability:

```
p_threshold = 1 − Poisson_CDF(threshold − 1, adj_λ)      # game_state_model._poisson_cdf
```

(`run_paper_trade.py`, T-129 Path B / ADR-0015). Poisson assumes **variance =
mean**. NBA player scoring is **over-dispersed** (var > mean — documented in
`c3_forecasting/scoring_distribution.py`, which already implements a Negative
Binomial path that the production T1 loop does *not* use). A Poisson on the mean
therefore produces tail probabilities that are too extreme — the exact
overconfidence measured. **Recalibrating the Platt model would have been a no-op
on live behavior.**

---

## Decision

**Apply temperature scaling to the production model probability before any
downstream consumer (edge gate, direction, Kelly sizing) reads it.**

```
p_cal = sigmoid( logit(p) / T )
```

* `T = 1.0` → identity. `T > 1` → shrink toward 0.5 (reduce confidence).
* Monotone and **frame-symmetric**: calibrating the YES-frame probability and
  taking the directional complement equals calibrating the directional
  probability (`logit(1−p) = −logit(p)`, `sigmoid(−x) = 1−sigmoid(x)`). So it is
  applied to the raw YES-frame `p_threshold` directly.

Implemented in `src/prediction_market_bot/c3_forecasting/calibration.py`
(`calibrate_probability(p, sport)`); wired at the single production probability
site in `run_paper_trade.py`. The pre-calibration value is retained in the
forecast record as `p_estimate_raw` for audit.

### Per-sport registry — fail-safe identity

Calibration is regime-specific. `CALIBRATION_TEMPERATURE` is keyed by sport and
**any sport without resolved data falls back to `DEFAULT_TEMPERATURE = 1.0`
(identity)**. Launching MLB cannot silently inherit NBA's shrink. Current:

| sport | T | basis |
|---|---|---|
| nba | **2.05** | provisional — see below |
| mlb | 1.0 (identity) | no MLB resolved data yet; toggled when the dark-period dataset exists |

### Why T = 2.05 for NBA (not the in-sample 3.10)

`scripts/derive_calibration.py` fits T by minimizing log-loss. The full-sample
in-sample optimum is **T = 3.10**. The **out-of-sample** estimate (fit on G2–G4,
validated on G5) is **T = 2.05**, and it generalizes: G5 Brier 0.315 → 0.282,
mean confidence 0.807 → 0.731 vs realized 0.537. The OOS-validated value is the
more conservative, defensible choice for a single-series n=158 sample; both
agree directionally (substantial shrink). It is **provisional** — re-derive on
NBA regular season per GG-037.

### Re-derivability

`scripts/derive_calibration.py <dataset.csv>` derives the recommended T for any
resolved dataset and prints the reliability buckets + edge-realization deciles
(the GG-037 monitor). It does **not** write T back into `calibration.py` — that
is a model change requiring an ADR amendment. This is how NBA regular season and
MLB get their own T.

---

## Institutional verification

`scripts/derive_calibration.py data/nba_finals_clean_dataset.csv`:

| | Brier | LogLoss | mean confidence | realized |
|---|---|---|---|---|
| Raw Poisson | 0.2308 | 0.7888 | 0.799 | 0.601 |
| Calibrated (T=3.10 in-sample) | 0.2054 | 0.5995 | 0.660 | 0.601 |
| OOS (fit G2–G4 → test G5) | 0.315 → **0.282** | — | 0.807 → **0.731** | 0.537 |

Tests: `tests/test_c3_calibration.py` — 14 tests (identity at T=1, 0.5 fixed
point, shrink/sharpen direction, monotonicity, frame symmetry, known value
p=0.9/T=2 → 0.75, extreme clamping, invalid-T raise, per-sport lookup,
unknown-sport fail-safe identity, MLB identity). Full suite: **988 passed**.

---

## Consequences

**Positive:**
- The model no longer reports confidence it has not earned; Kelly stakes are no
  longer inflated by Poisson overconfidence.
- Calibration is per-sport and fail-safe — a new sport defaults to identity.
- Re-derivable and monitored via one script (closes the GG-037 monitor item).

**Negative / the hard truth — recalibration disproved the "miscalibration"
hypothesis:**
- **Recalibration does NOT create alpha.** After calibration, the model's
  residual edge vs the Kalshi price is still **anti-predictive**: bets where the
  calibrated model says "underpriced" (edge>0) win **0.356** of the time vs
  **0.747** for edge≤0; highest-edge tercile 0.346 vs lowest 0.792. The edge
  inversion (GG-037) **survives calibration** — it was never just overconfidence.
- Calibration makes the bot honest, which makes it **decline most bets** (only
  ~46 of 158 clear the 0.04 edge gate post-calibration). That is correct
  behavior given no demonstrated edge — but it does not make this strategy
  profitable on the Finals data.
- Therefore **GG-037 stays OPEN** for the edge-inversion / no-alpha finding, and
  **GG-004 (commercial validation) is unaffected** — recalibration was a
  correctness fix, not evidence of profitability. The alpha question is deferred
  to EXP-017 at scale (MLB dark period + NBA regular season).
- The NBA T=2.05 inherits the n=158 single-series limitation (ADR-0024). It is
  provisional and must be re-derived on an adequate sample.

---

## G6 obligation

`CALIBRATION_TEMPERATURE["nba"]` must be re-derived on an ADR-0024-adequate
sample (regular season) before any live-capital reliance, alongside the hard
limits in ADR-0026. The calibration *mechanism* is permanent; the per-sport
temperatures are provisional until re-derived on adequate data.
