# The granularity index machine (NFL) — W80.3

**Pillar:** DEPTH (D5a filtering mechanisms + cross-reference compatibility; D5b run-box entry). Code: `src/prediction_market_bot/nfl_engine/granularity_index.py`; tests: `tests/test_nfl_granularity_index.py` (11).

The operator's run-box example is the positive control, not the product. The product is one generic machine: any "unit X, by condition Y, on metric Z" entry goes through the same five parts.

## The five parts, as API

| Part | Function | What it returns |
|---|---|---|
| 1. Split | `split(plays, SplitSpec, season, before_week, games)` | per unit and bucket: value, n. Strictly point-in-time (`before_week`; leaky-control test) |
| 2. Rank against history | `rank(...)` | rank_league / of_league, rank_history / of_history, percentile_history |
| (gate) Stability | `stability(...)` | split-half (odd/even games) r, Spearman-Brown corrected, unit-season bootstrap CI; `trait = CI lower > 0` |
| 3. Matchup cross | `cross(off, dfn, league, freq, k, overall)` | `CrossResult(expected, baseline, delta, by_bucket)`; additive in the two shrunk deviations, so symmetric in roles; weights each bucket by the show frequency |
| 4. Market map | `market_map(tag, inventory)` | Kalshi families the entry can price, with event and settled-market counts |
| 5. Application | per-entry script (e.g. `part_b_apply.py`) | the entry's delta against market price and outcome, read-only |

Helpers: `estimate_k` (empirical-Bayes shrink constant per bucket; infinite k means the bucket is pure noise and shrinks to the league mean), `shrink`, `show_frequency` (how often a defense shows each bucket), `filter_entries(entries, tail=0.10, min_n=30, require_trait=True, mismatch_min=None)` (the filtering mechanism: keep only extreme, adequately sampled, stable-trait entries, optionally only where off and def deviations oppose).

## Adding an entry
1. Write a `SplitSpec(unit, by, metric, higher_is_better, min_n)`; `by` is any play column or derived bucket.
2. Run `stability` for its buckets. A bucket that is not a trait is not used (it shrinks to the league mean).
3. Add a `MARKET_TAGS` row naming the Kalshi families it maps to.
4. Run the cross over the schedule; run Part B (interpret on seasons before the application season, leave-one-season-out).
5. Register the factor row in `SEATS/nfl.toml` at the stage reached.

## Costs
Split/rank: seconds per season on 2022–2026 pbp. Stability bootstrap: tens of seconds. Cross over a season schedule: seconds. No new data source; the box count comes from FTN `n_defense_box` (free).

## Known limits
- Box count missing (0) for about 1.2% of rushes overall, up to about 12.5% in 2026; treated as NaN. 2026 participation is absent (GAP-1 / GG-730).
- Python 3.9 locally lacks `tomllib`; irrelevant to this module (CI is newer).
