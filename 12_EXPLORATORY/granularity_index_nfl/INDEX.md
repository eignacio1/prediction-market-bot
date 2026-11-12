# NFL granularity index (W113.2, B-089) -- machinery once, not a list of examples (directive D-06)

25 entries built by `build_index.py` from one generic engine (`nfl_engine/granularity_index.py`): each is a Situation =
(metric, situation filter, unit side off/dfn). Every entry carries the five parts in `entries/<name>.json`: **split** (point-in-time
value), **rank** vs every team-season at the same games-played point (2022-2025), **stability** (split-half, Spearman-Brown, bootstrap
CI), **cross** (offence split x defence split, shrunk, with show-frequency) and **market map** (KXNFLTOTAL / TEAMTOTAL / SPREAD /
PASSYDS / RSHYDS). Part 5, **application**, is `leaf_scores.json` (`score_leaves.py`), filled below.

Free data, by season (checked 2026-11-12): pbp 2022-2026 wk1-9; FTN charting 2022-2026 (motion, play action, blitzers, box);
participation 2022-2025 only (defenders in box, offence personnel, man/zone, coverage type). **Registered gaps:** 2026 participation
(file 404 upstream, so every box / coverage / personnel split is a prior-season percentile for 2026 games); route trees by alignment,
motion direction and boundary side, pre-snap distances (paid / not published).

Operator-shaped questions the machinery answers: loaded vs light box (`rush_success_vs_loaded_box`, `..._light_box`, `loaded_box_rate_faced`);
cover-6 against 3-WR sets (`pass_success_allowed_cover6_vs_3wr`, thin at n=23 in 2025: stability false, registered); motion
(`*_with_motion`); coverage family (`pass_success_vs_man/zone/cover3`).

## Application (Part C)
Leaves = terciles of the mean of the two teams' 2025 percentiles (@total) or home-minus-away goodness (@side). 2026 shadow rows, 87
games (fit 60 earliest / test 27 latest), dedupe + retro_route arms, net after exact taker fee, game-clustered 90% bootstrap.
130 (entry x family x leaf) cells, 88 thin at fit, 21 routed and scored held-out, 0 clear BH q=0.10. 13 entries have a scored leaf and
are exported through the NFL adapter (`TESTED_SPLITS`); 12 are thin at this n and re-look as rows accumulate. Hypothesis closed
(EXP-W113.2-NFL-SPLITS-01, parked for R&D): no split localises an edge yet. MONEYLINE RIDE family lead (W110.5) held out at
+0.167 [+0.073, +0.258] n=81 g=27; inside the splits it sits in the `neutral` leaves (+0.11 to +0.22, same sign everywhere) and the
fit window picked FADE (held-out -0.15 to -0.23): a time-regime flip, not a split. Caveats: schedule lines are snapshot-time
(mild look-ahead), market-state leaves are coarse, shadow rows are paper rows (GG-527).
