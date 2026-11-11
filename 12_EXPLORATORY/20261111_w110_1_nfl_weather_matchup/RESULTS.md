# W110.1 results: NFL weather + matchup, applied as tree splits (2026-11-10)

Data: nflverse schedules 1999-2026 (closing line proxy, one line only), nflverse pbp 2011-2025, Open-Meteo forecasts (temp 2021-25, wind 2024-25 only, precipitation 2021-25). All factors point-in-time; realised weather refused for pricing (`weather_factor.assert_priceable`).

## Verdict (per operator addendum 2026-11-10 21:35 PT: leaves, not Brier)
`study_leaves.py`: 3,543 games, seasons 2013-2025, thresholds fixed a priori so nothing is fitted and every season is held out. Per leaf (filter x market state), net units per bet at the book's own price for FAV (ride), DOG (fade), OVER, UNDER; NO BET = 0.
- **82 leaves scored (n>=40), 0 earn an arm** (95% CI lower bound > 0). Chance alone would give about 2.
- Baselines: FAV -0.045 [-0.077,-0.013], OVER -0.048 [-0.080,-0.017] (reliably losing), DOG -0.012, UNDER -0.012 (not distinguishable from 0).
- MOMENTUM is not scorable: nflverse has one closing line, no opening line or move. No NFL Kalshi spread/total history exists locally either (KXNFLGAME moneyline, 2025 season only), so "2026 vs the market" is not possible for spread/totals.

## Engine price arms (reported, not the verdict)
`study.py`, market line as base, rolling origin 2020-25, n=1615 games, paired dBrier vs market (game-clustered bootstrap): W_obs (observed weather, leak) -0.00006 [hi +0.00022]; W_fc +0.00005 [hi +0.00021]; X +0.00008 [hi +0.00028]; WX_fc +0.00015 [hi +0.00039]. All MATCHES, none beats. Mean absolute price shift: crosses 0.24 pts, forecast weather 0.09, observed 0.17. 2025 fitted effects: wind -0.185 pts/mph above 10; cold +0.026 (wrong sign, noise); pass-cross beta -0.02, rush +0.03, pressure -0.17 (errors-in-variables attenuation applies to forecast inputs).

## Limits
Forecast wind missing 2021-23 (null in the fetch); windy/cold leaves thin. Precipitation non-null only 538 of 1353 games, 26 wet. Modal outcome (null) as pre-expected. Thresholds were not tuned.
