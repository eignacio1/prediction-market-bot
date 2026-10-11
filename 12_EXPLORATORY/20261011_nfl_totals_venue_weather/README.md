# W68.3 — NFL totals: venue + weather challenger (EXPLORATORY; plan frozen BEFORE fitting)

Charter: `12_EXPLORATORY/CHARTER.md`. Reads public nflverse copies only; pre-2026 seasons; writes via `safe_out()`. Not evidence.
Question (D1): does adding roof/surface and kickoff wind/temperature to the frozen EXP-037 totals inputs improve totals pricing?

## Frozen incumbent
`nfl_pregame_v1` inputs (11 features), ridge λ=100 on total, Gaussian σ_total from calibration-season residuals, refit rolling-origin.
Margin model unchanged in every arm (ridge λ=100); only the TOTAL mean differs between arms.

## Arms (all add to the 11 frozen features)
| arm | adds | legality |
|---|---|---|
| `venue` | `p_indoor`, `p_turf` | stadium category from home team's prior ≤24 home games, gameday strictly earlier (retractable roofs use the club's prior tendency, never the game-day open/closed flag) |
| `venue_fcst` | `p_indoor`, `p_turf`, `wind_eff`, `cold_eff` | Open-Meteo Previous-Runs `*_previous_day1` at kickoff hour (run of prior UTC day, lead ≥24h ≥ T1 12h). Exposure-scaled by (1−p_indoor); missing → 0 effect. |
| `venue_obs` (UPPER BOUND, flagged) | as above with nflverse OBSERVED temp/wind | NOT point-in-time; never eligible for a verdict or pre-registration |
Controls: `frozen` (all history ≥2015, the real incumbent) and `frozen_w21` (same 2021+ training window as the weather arms, to separate window effect from feature effect).
Known limitation: neutral-site games (≈5/yr) carry the nominal home stadium's forecast; no location field in the cache. Kept, not hidden.

## Evaluation
Rolling origin, tests 2023–2025 (weather archive exists 2021+: train ≤T−2, calibrate T−1, test T; 2023 trains on 2021 only).
Families priced from the bivariate Gaussian (margin, total), ρ and σ from calibration residuals; strikes are a FIXED league-wide ladder (never market lines — circular, T-586 §5):
* game total over: 37.5, 40.5, 43.5, 46.5, 49.5, 52.5
* team total over (home and away): 14.5, 17.5, 20.5, 23.5, 26.5, 29.5 (team-total mean (μ_t±μ_m)/2, var (σt²+σm²±2ρσtσm)/4)
Metric: Brier per contract; paired differences vs frozen; **game-clustered** bootstrap (resample games, B=20000, seed 20261009).

## Multiplicity
m = 8 (NFL challengers already tested on these seasons, per W64.1's count) + 6 (this study: 3 arms × 2 families, game total and team total; the flagged upper-bound arm is counted though it cannot win) = **14**. α = 0.05/14 = 0.003571; CI level 99.6429%.

## Verdict rule (fixed now)
An arm "beats frozen" on a family iff Bonferroni CI upper limit < 0 on the pooled paired Brier difference AND better in ≥2 of 3 test seasons AND it also beats `frozen_w21` (same window). Otherwise: no.

## Expected outcome (stated in advance)
Modal: NO. Venue/weather matter for totals in principle (wind, cold, domes), but a 11-feature ridge on ~270 games/season over 3 test seasons has little power to detect a Brier gain of ~0.001; expect `venue` ≈ frozen, `venue_fcst` ≈ frozen within noise, `venue_obs` slightly better than `venue_fcst`. Kalshi totals comparison: **impossible** — `KALSHI_HISTORY_MANIFEST.md` states no pre-2026 total/team-total history exists. That is reported, not substituted.

## Look-ahead tests (`test_vw_features.py`)
1. Stadium category unchanged when any game ≥ the target gameday is altered.
2. Forecast guard rejects non-`previous_day1` columns and leads < 12h; every fetched lead ≥ 24h.
3. Forecast arm never reads observed `temp`/`wind` columns.
