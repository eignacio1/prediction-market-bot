# EXP-W119.1-NHL-GOALIE-ST: goalie and special-teams splits (pre-registration)

Last reviewed: 2026-11-19 (W119.1). Committed before any outcome of these splits was read.

**Hypothesis (a routing test, not a gate).** Four new layer-3 splits, `goalie@side`, `goalie@total`, `special_teams@side`,
`special_teams@total`, route some NHL leaves to an arm with held-out net after costs above zero. A null closes only this test
("hypothesis closed, parked for R&D"); the splits stay in the adapter.

**Definitions (fixed here, not fitted).**
- Goalie: the team's LAST COMPLETED starter (the store has no pre-game lineup), his season save rate through that game shrunk to the
  league rate with 300 shots, NaN under 100 season shots. League percentile at puck drop. side = home minus away > 1/3 = edge;
  total = mean of (1 - percentile) terciles (weak goalies = high total).
- Special teams: rolling 20-game (min 5) mean of power-play goals scored and penalty minutes taken; goodness = (pp percentile +
  (1 - pim percentile)) / 2; total = mean of (pp, pim) percentile terciles.
- Point in time: `factors_w112.asof`, 4h buffer, so a game never sees itself.

**Scoring (same as W112.4 `score_leaves.py`).** Settled NHL shadow rows (deduped, moves added). Earliest 70% of games pick the arm per
(filter, family, leaf) from RIDE, FADE, MODEL_FADE, MOMENTUM, POT_OF_GOLD by best fit mean net after the exact fee (else NO_BET);
latest 30% score it, game-clustered bootstrap 90% interval, BH q = 0.10 across all reported leaves.
**KEPT** = not thin, arm is not NO_BET, held-out games >= MIN_TEST_GAMES, held-out mean net > 0. **DRAFT** additionally needs BH and a
lower bound above 0. Thin = under MIN_FIT_ROWS rows or MIN_FIT_GAMES games. Shadow rows are paper rows, not fills (GG-527).

**Modal outcome (stated now).** With about 340 store games and a 30% held-out slice, most leaves are thin or under MIN_TEST_GAMES.
Expected: few or no DRAFT leaves; KEPT leaves reported with their intervals and not read as validated.
