# Session handoff — W122.4 · MLB 2027 board priced; every game cell logging from opening day (GG-1957)
Common rules first line quoted: "# Wave 122 common rules". PR #544 merged (Test Suite green; Docs Guard red on main too, same step `generate_gap_arm_index.py --check`, not this PR).

## MEASURE MOVED
- **MLB layer-1 game cells 3 → 12** in the replayed-date dry run (`tests/test_mlb_opening_day_dry_run_w122.py`): all 12 game cells (4 families x T1/T2/T3) write a row with model p, market state, v1 arm and the 2027 map's arm. Not live: nothing runs until the 2027 schedule exists.
- **Back-test** (`12_EXPLORATORY/mlb_engine/RESULTS_W122_4.json`, driver `run_w122_4.py`): one joint run grid prices ML, run line, total ladder and team totals. Trained on seasons before the tested year; as-played lineups (probable starters are the live input, a stated limit).
  - Vs naive, 2025 / 2026 (every rung): moneyline Brier gain +0.0016 / +0.0021 (CI above 0); spread +0.0012 / +0.0010; team total +0.0012 / +0.0013; total ladder ≈ 0 (CI spans 0).
  - Vs Kalshi last pre-game quote (≥10 min before start), **2026-08-04 on only** (archive start; 2025 has no prices): the model is behind the market on every family. Brier gap model−market: ML +0.0075 (n=753 games, CI excludes 0), total +0.0018, spread +0.0019, team total +0.0028 (rung observations; all CIs exclude 0). Reading: market is the better price; the engine's job is the tree's input (ride / fade split), not a standalone bet.
  - Contract units verified from outcomes: SPREAD suffix k = team wins by ≥k; TEAMTOTAL k = team scores ≥k (mids match realized frequency per rung).
- **GG-1957 cause:** no defect in the row writer. The 12 game-cell crons were not armed until after the regular season; the Stats API 406 + 26h stale-cache rule makes the runner exit before logging, and that exit left no record. Existing box rows (8,840, from 10-05) came from older runner code without router/reasons fields. **Fix:** `scripts/mlb_opening_day_preflight.py` (read-only; fails on stale cache, no games ahead, missing model, silent cells) and the runner now appends every fail-closed exit to `exp_output/PREGAME_SHADOW/_MLB_FAILCLOSED.jsonl`. Tests: `tests/test_mlb_preflight_w122.py`.
- Candidate wiring: the frozen 2027 leaf map is a shadow-only candidate (`mlb_2027`); the v1 default is unchanged.

## Opening-day checklist (on the box)
1. 2027 MLB schedule present in `exp_output/MLB_GAME/cache_w47/games_current.parquet`; stamp <26h (`scripts/sync_mlb_games_cache.sh`, off-box refresh).
2. `python3 scripts/mlb_opening_day_preflight.py` exits 0 daily; `_MLB_FAILCLOSED.jsonl` count reported.
3. `models/mlb_game_pregame_v1.json` present, sha `a57990a1…` (load verifies).
4. The 12 game-cell crons armed in RUNTIME_REGISTRY; `PM_CANDIDATE_ARMS` not `off`.
5. Pitch store (`~/mlb_store`) is local-only: the board pricer runs off-box; wiring it into the live runner (probable starters) is the next MLB block.
6. No `*_install` task is needed from this block; none run.

## Scope notes
- 14 non-game MLB cells (PARTIAL_GAME, PLAYER_PROP_HITS) are not covered by the shadow runner; unchanged.
- Game-id mismatch (25 vs 22 per cell) not reconciled; low priority.

surface_delta: 0 (one read-only script, no cron / service)
pattern_sweep: fail-closed exits in `src/ scripts/` shadow runners — only the MLB runner has the stale-cache SystemExit; recorded there. Archive-reader guard allow-list extended for the driver.
directive_conflicts: none found
Pushback: the engine is behind the market on every family on 2026 Aug–Sep; do not read it as a fade signal, route per leaf.
Surface: box HEALTHY per queue; no installs. Dependencies: 2027 schedule publication; probable-starter feed for live pricing.
