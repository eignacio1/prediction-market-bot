<!-- session-meta
task_id: W128.2
tier: STANDARD
timestamp: 2026-11-25T06:30:00Z
commit: 289bfef
one_line_summary: W128.2: one player-mean function (c2_means); C2 and combo legs read it; combo rows w128_2; forward look schedule
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D1 NBA props cells reading C2; D-07 places a player mean is computed
gap_delta: combo legs reading C2 means 0 -> 1 family; NBA props cells reading C2 4 -> 4 (already, W127.1); places computed: see below
pattern_sweep: grep -rn "redistribute\|absorb(" src scripts: the C2 forecaster and the combo were the only live callers outside frozen C1 and research scripts
surface_delta: +1 module (player_means.py), +1 read-only box task (props_c2_read); no new cron or service
-->
# Session handoff W128.2 — one player-mean function for props and combos
**Last reviewed:** 2026-11-25. PR #582 merged (289bfef), CI green (guard, test on head 6c53efa).

**Premise corrected.** C2 already priced all four props cells before this block (W127.1, `PM_PROPS_C2` default on). The real gap was the combo legs, which used raw trailing means with no Out shift.

## Measure moved
- **D1, NBA props, cells reading C2:** 4 of 4 stat cells before (points, rebounds, assists, threes) and 4 of 4 after. Combo player legs reading C2: 0 -> 1 (the combo pricer).
- **D-07, places a player mean is computed:** live paths 2 -> 1. Before: the props forecaster's own `_mu` (C2 rule inline) and the combo's `game_draws` (raw `roster()` means). After: `nba_engine/player_means.c2_means`, called through `NBAEnginePropsC2.team_means` by both. Frozen base (EXP-047 `_mu` identity) and C1 stay as challengers for hash and regression; research scripts (`run_retro`, `run_c2`) untouched.

## What changed
- `nba_engine/player_means.py`: pure `c2_means(base, p_play, attempts, lam)`; nobody Out returns `base` unchanged.
- `NBAEnginePropsC2._mu` and new `team_means(team, date, parsed, as_of)` use it; `nba_combo_shadow.make_forecaster` / `game_draws` and `combo_rfq_demo.py` feed `JointRoster.mu` from it.
- Frozen hashes unchanged (tested): C2 `MODEL_SHA256`, C1, EXP-047, `LAMBDA`. Combo rows: `model_id` `nba_combo_shadow_w128_2` plus `player_means_sha256` (= C2 hash); w126_4 rows are the raw-mean rows. Shadow only; no order path.
- Tests: `tests/test_w128_2_player_means.py` (same player-game, same mean through `c2_means`, `_mu`, `team_means` and the `JointRoster.mu` the combo builds), `tests/test_w128_2_props_c2_read.py`. 73 related tests green locally.

## Part C — forward look and descriptive read (box task `props_c2_read`, 2026-11-25 06:2xZ, result in BOX_TASKS/results)
- Rows since 11-25: 1 day, 2 games. Paired C2 vs EXP-047: points 146, rebounds 160, assists 136, threes 156. **0 differ**: no listed-Out player in those games, so C2 equals the plain average there (expected). Nothing to describe yet; no outcome read; no verdict.
- Schedule, games to put the 95% interval of the retrospective log-loss gain off zero, assuming the forward effect equals the retrospective one (2023-24, RESULT_C2.json): points 30, assists 50, threes 90, rebounds 902. Dates at the observed 2 games/day (one day only, so a floor on pace): points 2026-12-10, assists 12-20, threes 2027-01-09, rebounds 2028-02-19. At a full NBA slate the dates come in; re-run `props_c2_read` next week for a real rate.
- This is log-loss calibration, not the verdict. The router judges each leaf on net after costs per arm; those n come from its power calendar once leaf rows exist.

## Box
- Deploy read (`deploy_truth_read` 06:10Z): box HEAD 525184dd, status docs_only, t4-mlb and dashboard on box HEAD. The merge 289bfef was NOT yet on the box then; it deployed within ~5 minutes (props_c2_read ran after). **t4-mlb decision:** no restart needed; MLB idle until 2027 and the change touches no file t4-mlb imports.
- The next hourly combo shadow run writes w128_2 rows. The shadow install is still unapproved (W127.3), so no combo shadow rows exist until it is.

directive_conflicts: none
operator decisions: none new. (Open from W127.3: APPROVE nba_combo_shadow_install.)
Next: re-run `props_c2_read` after a full slate; then a first look at games with an Out player (V >= 0.10) where C2 and EXP-047 differ.
