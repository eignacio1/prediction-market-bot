# PREREG EXP-MLBSIM-001 (W126.3) - the PA-level joint simulation, held-out 2026 report

Committed BEFORE any 2026 outcome is joined to the engine's prices. Last reviewed: 2026-11-24.

**What is tested.** `mlb_engine/{pa_model,sim,joint_board}.py`: league rates fit on PA with game_date < 2026-01-01 (2024-2025 in the store), frozen.
Every 2026 regular-season game with nine-man lineups and both starters is priced from one simulation (n = 3000 draws, seed 0).
Constants (K_B 150, K_P 300, K_PEN 600, runner-advance table in sim.py) are fixed by this commit; none is tuned on 2026.

**Families (calibration, every rung):** moneyline (home), total >= k (3..16), spread win-by >= k (1..7, each side), team total >= k (1..12, each side),
batter hits >= 1 and >= 2 (slots 1..9, each side). Score: Brier and log loss, each against NAIVE (train-window frequency per rung),
against the W122.4 independent-NB board (RESULTS_W122_4.json, same games/families where it exists), and, on the archive window
(2026-08-04 on, last pre-game quote >= 10 min before first pitch), against the Kalshi mid as BENCHMARK.
Game-clustered bootstrap (2000 resamples) for every gain CI. Also reported: mean p vs mean y per family (bias), same-game correlation of
the simulated legs vs the realized legs (sign check), runtime per game.

**Not a verdict.** Per ADR-0077 the market gap is a report and a tree input; nothing here routes, sizes or opens an arm. A loss to the market
closes only this hypothesis (EXP-MLBSIM-001, parked for R&D), never a cell. No orders, no cron, no registry status change.

**Stated limits, fixed in advance:** no park, weather or explicit home-field term; as-played lineups (small known leak, live path uses posted lineups);
no pinch hitters/steals; KXMLBHIT market comparison needs a player-name bridge not built here, so hits props are scored on outcomes vs naive only;
F3/F5/F7 series are not priced; archive coverage is ~58 game dates.

**Modal outcome (written first):** engine beats naive on every family; trails the market on moneyline by a Brier gap of the order of +0.005 to +0.01
(no park/home term), is closer on totals; hits >= 1 well calibrated vs naive; correlation signs correct.
