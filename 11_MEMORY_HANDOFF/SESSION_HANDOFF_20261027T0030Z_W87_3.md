# SESSION_HANDOFF W87.3 — market history for frozen models + NHL totals price check
vision_pillar: PROOF
gap_measure: models with a market-referenced held-out Brier (of 6)
gap_delta: 1 -> 2 (NHL added from W84.3 stored numbers n=1,306; NO clustered interval). Skill weights all 0.
pattern_sweep: n/a (no defect fixed)
surface_delta: 0 (no running component added; one read-only script + test)

Done: PR #332 (CI green, merged). Results `12_EXPLORATORY/market_history/results_W87.md`; `models/*_heldout_vs_market_w87.json` (6 files).
Part A: NHL scored (model 0.24734 vs market 0.24419; weight 0). NBA game, NBA points, MLB game, NFL QB: NONE. Kalshi history exists for NBA/MLB/NHL; the missing piece is model-side feature data (NBA 2024-25 games, MLB games and starters), plus the NHL Kalshi store and box scores to get a game-clustered interval.
Part B: NHL_GAME_TOTAL_T1, 1,485 rows/162 events: 65.2% wide (>10 pts), 0% one-sided, 67.0% strike >1.5 from the event line, stale age NOT MEASURABLE (no quote time in rows). No score read.
Next: rebuild NHL store (kalshi_history_build fetch --sport nhl) + box scores from box data/raw/nhl, clustered paired CI via quant/; MLB 2025 and NBA 2025-26 backfills; add a quote-time field to shadow rows for the stale check (GG, not fixed here).
Operator decisions: none.
