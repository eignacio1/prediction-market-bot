# W68.3 — NFL totals: venue + weather challenger — RESULTS (EXPLORATORY, not evidence)

Plan frozen before fitting: `20261011_nfl_totals_venue_weather/README.md`. Code/data: same folder (`study.py`, `results.json`, `forecast_kickoff.json`). Run on 816 games (2023–2025 REG), rolling origin, game-clustered bootstrap B=20000 seed 20261009, m=14, corrected CI 99.6429%.

## Verdict: NO. No arm beats the frozen totals model on either family.
Brier (lower better), mean over contract ladders:

| arm | game total | team total |
|---|---|---|
| frozen (≥2015 history) | 0.21936 | 0.20104 |
| frozen_w21 (control, 2021+ window) | 0.22020 | 0.20122 |
| venue | 0.22161 | 0.20169 |
| venue_fcst (point-in-time forecast wind/cold) | 0.22089 | 0.20159 |
| venue_obs (OBSERVED weather, flagged upper bound) | 0.22110 | 0.20131 |

Paired Δ vs frozen (positive = challenger worse), corrected CI:
| arm | family | Δ | corrected CI | seasons better (23/24/25) |
|---|---|---|---|---|
| venue | game total | +0.00225 | (−0.0033, +0.0078) | no/no/no |
| venue | team total | +0.00065 | (−0.0020, +0.0034) | no/no/no |
| venue_fcst | game total | +0.00153 | (−0.0043, +0.0072) | no/yes/no |
| venue_fcst | team total | +0.00055 | (−0.0022, +0.0033) | no/no/no |
| venue_obs (flagged) | game total | +0.00174 | (−0.0043, +0.0079) | no/yes/no |
| venue_obs (flagged) | team total | +0.00027 | (−0.0025, +0.0032) | yes/no/no |

Every CI includes zero and every point estimate is on the wrong side. Even the non-point-in-time observed-weather upper bound does not help, so forecast error is not what limits the arm. Most of the gap vs `frozen` is the shorter training window (`frozen_w21` is itself +0.0008 worse on totals); the venue/weather features add a further ~+0.001 of variance, not signal.

## What this does and does not say
* Matches the stated modal outcome (README § Expected outcome). Not a statement that wind/cold/domes do not matter physically — a 2021+ ridge with ≤4 more standardized columns and ~270 games/season cannot learn a tail effect (few windy games) and pays variance for trying.
* Kalshi totals comparison **not possible**: `KALSHI_HISTORY_MANIFEST.md` — no pre-2026 total or team-total history was ever fetched. Not substituted with moneyline.
* Limitations: neutral-site games use the nominal home stadium forecast (no location field); 31 of 1353 forecasts null (zero-effect imputation); 99.3% forecast coverage in test seasons; the ≥2015 control uses an earlier fit window than weather arms, which is why `frozen_w21` was added.
* No pre-registration drafted: the corrected CI does not exclude zero. D3 does not move.

## Next mechanism (named)
Stop fitting weather coefficients on 2021+ only. **Train on observed weather over the full 2015–2025 history (labels are past, legal), serve with the previous-day forecast**, and constrain to one scalar `wind_eff`/`cold_eff` effect pair on the total mean (not all 11+4 ridge columns). That uses ~2x the windy/cold games. Cost: forecast-vs-observed measurement-error mismatch to be tested explicitly (error-in-variables). Only worth a block if the observed-weather coefficient on 2015–2022 alone is distinguishable from zero; that is a cheap precheck.
