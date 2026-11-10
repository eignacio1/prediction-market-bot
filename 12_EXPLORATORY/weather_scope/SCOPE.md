# Weather markets vs free forecasts — scoping memo (W108.4, B-065)

*Research only. Recommendation to the window, not a decision. Weather as a direction is the operator's call alone. No cell, no pre-registration, no order, nothing running. Date: 2026-11-10.*

## Plain English

**Is there a gap?** On the one city measured so far (New York daily high), no. Kalshi's price at 6pm Eastern the evening before beat a free weather-model forecast on both Brier score and log loss, and betting toward the forecast lost money after fees.

**How big?** Held-out later 30% (2026-08-09 onward), 513 strike-markets over 86 city-days:

| | Brier | Log loss |
|---|---|---|
| Kalshi price | 0.091 | 0.281 |
| Forecast model (causal trailing-30d bias/sd) | 0.123 | 0.385 |
| Forecast model (bias/sd fit once on the earlier 70%) | 0.131 | 0.413 |

Market minus model Brier gain: **-0.032, 95% city-day-clustered interval [-0.045, -0.019]** — the model is worse, and the interval excludes zero.

Net per contract trading toward the model after exact Kalshi fee plus a spread proxy (mean half-spread about 0.7¢ where measurable, 2¢ default otherwise): edge>0: **-3.3¢** [-6.1, -0.2], n=447; edge>3¢: **-6.2¢** [-11.1, -1.0], n=267; edge>10¢: **-7.4¢** [-13.6, -0.3], n=162. The bigger the model "disagrees" with the market, the worse it does: those are mostly the model being wrong.

**Read:** pricing here is sharp relative to a single free global model. This is a result for NYC only, one forecast model (GFS), one snapshot time. It is not a verdict on weather.

## Update: two cities (NYC + Chicago, daily high)

Pooled held-out (cut 2026-08-06), 1,038 strike-markets over 174 city-days: Brier market **0.098** vs model **0.137**; log loss 0.305 vs 0.427. Market-minus-model Brier gain **-0.038, 95% city-day-clustered [-0.047, -0.029]**. Net per contract trading toward the model after fee and spread proxy: edge>0 **-3.1¢** [-5.0, -1.1] n=914; >3¢ -4.3¢ [-7.0, -1.3]; >6¢ -4.2¢ [-7.2, -0.8]; >10¢ -6.0¢ [-9.8, -2.5] n=382. Same answer as NYC alone: the price is sharper than one free model, and the bigger the disagreement the worse the trade. Miami, Austin, Denver, LA, lows, rain, a second model and a second snapshot time were NOT run (operator ended the session); they remain the open list in the recommendation below.

## What exists (Part A)

- **Kalshi weather**: 501 series in Climate & Weather (144 daily). Daily families: highest/lowest temperature (about 45 US and international cities each), rain yes/no (about 15 US cities). Quadratic fee, multiplier 1.
- **Structure**: one event per city-day, 6 markets (four 2°F buckets plus two tails), integer °F, settled mostly on The Weather Company reading (some on NWS climate reports). Settled value is readable in `expiration_value`, so ground truth is free. NYC high has 1,917 settled events back to Aug 2021.
- **Volume**: hundreds to ~47k contracts per market, open interest up to ~30k on the central buckets. Real but small; capacity per market is a few hundred dollars, not thousands.
- **Free forecasts**: Open-Meteo *previous-runs* API gives the forecast issued 24h earlier (point-in-time for D-1). Used here. Open-Meteo's historical-forecast API is stitched, not point-in-time. NWS API has no historical archive. NOMADS/HRRR archives, IEM MOS, and multi-model blends were **not** probed — a registered gap, not a finding.
- **Cannot reconstruct**: historical bid/ask. Kalshi gives trade prints only, so spread is proxied from the bounce between taker-yes and taker-no prints. Prices are last trade before 23:00Z on D-1, not an executable quote.

## What a build would take

A weather arm would reuse the existing shadow path: a fetcher for the forecast, `quant/weather_calib.py` (built, tested, PR #454), one pre-registered cell per series family, shadow logging only. Roughly 2–3 blocks for one city family; the rain family and lows need their own forecast target. Data cost is $0 for what was used. A multi-model ensemble (the likely minimum bar) is a larger build and is where the open question sits.

## Risks

1. **One city, one model, one snapshot.** The result could flip with a better blend or a different time of day. It has not been tested.
2. **Settlement mismatch.** Forecast is for a grid point; Kalshi settles on a specific station reading from The Weather Company. Part of the 3–4°F error is this, not forecast skill.
3. **Spread is a proxy.** Real quotes could be worse or better than assumed.
4. **Efficiency.** Weather is a market where other participants use the same free models; the sharpness measured is consistent with that. This is the same hostile-efficiency concern CLAUDE.md raises for attended markets, though weather is plausibly less watched than sports.
5. **Capacity.** Even with an edge, per-market depth caps dollars per day. This is a breadth/proof play, not a P&L engine.
6. **Seasonal error.** Forecast error flipped sign through the year (about +5°F November, -3°F July). Any model needs a causal bias term; the one used here was only a trailing average.

## Recommendation to the window

Do **not** build a weather arm on this evidence. If weather is wanted for BREADTH, the cheapest next step is one more research block: add a second model (NWS/HRRR or an ensemble), the other five cities already in `fetch_weather.py`, and a second snapshot time, then re-run `analyze.py`. Expected modal outcome, stated in advance: still no edge net of cost. Proof value is a rigorous NO on a new family. The operator decides.

## Reproduce

`python3 12_EXPLORATORY/weather_scope/fetch_weather.py` then `analyze.py`. Results: `results.json`. Tests: `tests/test_quant_weather_calib.py`.
