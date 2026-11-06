# W103.2 (B-045) — overreaction and regimes in Kalshi prices

Status: PRE-REGISTRATION written and pushed BEFORE any forward price was looked at (see git history for the timestamp). Results are appended below it.

## Pre-registration (frozen when this commit is pushed)

Data: `yes_mid` snapshots from `exp_output/PRICE_ARCHIVE` (see INVENTORY.md). Family = `series_ticker` (23). Cluster = `event_ticker` (one game).

1. **Step move** = change in `yes_mid` of one market between consecutive snapshots, kept only when the gap is <= 30 minutes (cadence is 20; a longer gap is an outage).
2. **sigma_f** = root-mean-square of ALL step moves of the family (pooled, mean not removed). **Big move = |step move| > k * sigma_f with k = 3.** k is fixed here, before outcomes; no other k is tried or reported as a result. (A k = 2 and k = 4 sensitivity may be shown afterwards labelled "sensitivity, not the finding".)
3. A move counts only if the market's price BEFORE the move was in [0.05, 0.95] (a market near its bounds cannot revert by construction).
4. **Refractory:** after an accepted event on a market, further big moves on that market within the next 60 minutes are skipped (overlapping windows would count one episode twice).
5. **Reversion at horizon h** = -sign(move) * (price at h - price after the move). **Family statistic R_h = sum(reversion) / sum(|move|)** (ratio of sums; 0.4 = 40% of the big moves was given back; negative = the price kept going). Horizons: **next snapshot (20 min +/- 5), 60 min (+/- 10), and the settlement proxy** (last snapshot, only if <=0.03 or >=0.97). No interpolation; an event without a snapshot at the horizon drops out of that horizon only.
6. **Interval and p:** game-clustered bootstrap (whole games resampled, 2,000 draws, seed 20261105), 95% percentile interval, two-sided bootstrap p. **n_events and n_games stated for every cell; a cell with < 15 games is FLAGGED "interval undercovers", not read.**
7. **PRIMARY test = R at 60 minutes, per family, with Holm (family-wise 0.05) and Benjamini-Hochberg (q = 0.10) over all families with >= 15 games** using `quant/multiplicity.py` (the MULTIPLICITY_LEDGER method). The 20-minute and settlement-proxy horizons, the pre-game (prior days) vs game-day split, and the tight-book split are SECONDARY and reported without adjustment, labelled as such.
8. **Pre-game vs in-play:** calendar proxy only (ticker date vs snapshot date; prior days vs game day) — see INVENTORY.md for why. "Game day" is NOT called in-play.
9. **Tight-book robustness:** repeat the primary with events whose `half_spread` <= 0.01 at the event snapshot, to see whether reversion is bid-ask bounce.
10. **Regime:** per market-hour, label **jumpy** if the hour holds >= 1 big move (same k, sigma_f), **calm** otherwise; hours with < 2 step moves are unlabelled. Stability = P(jumpy next hour | jumpy now) vs P(jumpy next hour | calm now). Reversion by regime uses the label of the hour BEFORE the event's hour (known at the time; the event's own hour is jumpy by construction).
11. **Fade/follow wording:** an R whose 95% interval excludes 0 on the correct side AND survives the primary Holm/BH is a "measured overshoot (fade)" or "measured drift (follow)"; anything else is "no distinguishable effect at this n". All results are gross of fees and spread; none is a trading edge claim, no cell is opened.
12. **MEASURE:** families with a measured overshoot / reversion ESTIMATE (R_60 with interval) X of N (N = 23). Estimate availability is separate from significance.

## Results
(appended after the run)
