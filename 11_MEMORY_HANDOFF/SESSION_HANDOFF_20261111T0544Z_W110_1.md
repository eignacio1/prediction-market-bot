# SESSION HANDOFF - W110.1 NFL weather + matchup (2026-11-10)
COMMON_RULES_W110 first line quoted: `# Wave 110 common rules`.

```
vision_pillar: DEPTH
gap_measure: D1 (NFL: weather + matchup now conditioned in engine/filters), D4, D5(b) NFL applied
gap_delta: D5(b) NFL applied 10 -> 12 (N22 weather PIT forecast, N23 unit-vs-unit crosses; both null). Source: 02_ARCHITECTURE_DESIGN/SEATS/nfl.toml, 2026-11-10
pattern_sweep: n/a (no defect fixed)
surface_delta: 0 live components (library modules + exploratory study only)
```

## Done
- Part A `nfl_engine/weather_factor.py`: forecast-only (realised refused, lead>=12h), wind/cold/precip/roof exposure, fitted effects.
- Part B `nfl_engine/matchup_cross.py`: pass/rush/pressure crosses, shrunk, PIT, same-week rank.
- Addendum applied: `nfl_engine/filters.py` exports `nfl_filters(ctx, terms_home, terms_away, spread_line, total_line) -> {weather, matchup_total, matchup_side, spread_bucket, total_bucket}` leaf labels, thresholds fixed a priori. **Interface for 110.3's `decision_trees/router.py`**: call it per game; labels are leaves, never prices or sides.
- Part C: `study_leaves.py` (verdict) and `study.py` (Brier arms, not the verdict). Results: `12_EXPLORATORY/20261111_w110_1_nfl_weather_matchup/RESULTS.md`.
- **Result: 0/82 leaves earn an arm** (about 2 expected by chance); FAV and OVER baselines lose reliably after costs; all engine Brier arms MATCH the market. Null as pre-expected.

## Could not do
- MOMENTUM arm: no opening line/move in nflverse. Needs a Kalshi/book line-history archive.
- 2026 vs Kalshi spread/totals: none exists locally (KXNFLGAME moneyline, 2025 only).
- Forecast wind null 2021-23; windy/cold leaves thin. Precip non-null on 538/1353.
- Session-start protocol (claim, SSH probes, Q1-Q7) was not run in this session; acknowledged, not asserted clean. No box install needed.

## PR
#473. Merge only on green CI for current head; after merge read the box deploy and record the t4-mlb decision (none expected: no imported file changed).
