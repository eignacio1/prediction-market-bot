# SESSION_HANDOFF W89.4 — NFL game simulation, whole board from one joint distribution

```
vision_pillar: DEPTH
gap_measure: D4 (NFL) + families priced from one joint distribution
gap_delta: NFL D4 "data layer + scaffold" -> whole board (ML, spread ladder, total ladder, team totals) read off ONE joint simulation, offline; families from one joint distribution 0 -> 4. Source: 12_EXPLORATORY/nfl_gamestate/results.json. NO edge claimed.
pattern_sweep: n/a (no defect fixed) -- the start_state bucket bug and the fence-test failure (write not routed through safe_out) were both in this session's own new code, fixed before merge.
surface_delta: none (offline exploratory; nothing live; no registry entry)
```

Status: DONE | PR #344 squash-merged as 1a741d5, CI green (second run; first failed on `test_exploratory_isolation`, fixed) | branch session/20261027T040537Z-w89-4-nfl-sim

## Result
Play-level absorbing chain (160 transient states x 8 absorbing classes), estimated on earlier seasons, tilted per matchup by a point-in-time points-per-drive rating. 2000 sims per game, 272 REG games each in 2024 and 2025.
- Paired Brier sim - market close: moneyline +0.021 [0.006,0.035] / +0.018 [0.005,0.030]; spread +0.011 [-0.002,0.026] / +0.019 [0.007,0.032]; total +0.005 [-0.007,0.016] / +0.008 [-0.003,0.020]. Never better than market.
- vs same-mean Gaussian: |diff| <= 0.005 -> no shape information added (consistent with W73.3).
- Quant bar partly missed: key numbers 7 and 10 reproduced; 3 is about half the actual frequency in both seasons. Chain under-scores 1st-and-10 by ~0.15 pts/drive; sim OT 3.4% vs 5.2-5.9%.
- Full detail and stage table: `12_EXPLORATORY/nfl_gamestate/results_W89.md`.

## Stage per factor
Down/distance/field, team strength (PIT), drive/clock: aggregated, interpreted, applied (no edge). Matchup, availability/QB, weather, venue, officials, coaching, qualitative: not built here.

## Proposed seat rows (window to apply)
D4 NFL: "whole board read off one joint simulation, offline; worse than close at the centre". Do not move the `[[engine]]` artifact (nfl_engine is statistically equivalent). Next cheapest DEPTH move: score-state + late-clock logic (fixes the 3 spike, OT, scoring level), then QB/availability in the rating.

## Not done
Kalshi 2025 KXNFLGAME candle comparison, frozen `nfl_pregame_v1` comparator, props/parlays (no free joined outcomes). Next block.

## Operator decisions
None.
