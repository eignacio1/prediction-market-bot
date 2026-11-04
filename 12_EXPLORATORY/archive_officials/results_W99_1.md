# W99.1 — Muse's archive tested in an engine: officials into NFL and NBA totals (Parts A and B)

Date: 2026-11-04 UTC. Archive pinned at `2e2d3b2606a8b9a470d29fc38a67735449d38fef`, read only. Free data only. No frozen engine, runner or pre-registration touched; nothing written to the archive.
Purpose (Hard Rule 12): DEPTH + PROOF. Measure: archive slices tested in an engine 0 -> 2; D5(b) officials stage per sport.

## Verdict

| Slice | Result | Stage reached |
|---|---|---|
| NFL crews -> game total and team totals | **NULL.** Both features, 2019-2025 rolling origin, n=1871 games, paired game-clustered bootstrap CIs all span 0. | interpreted (tested path to a price; no edge found) |
| NBA referees -> engine v2 total and team totals | **NULL, upper bound.** Fit 2025 (n=1075), test 2026 (n=1072); all CIs span 0. | interpreted |
| Muse's NFL record vs nflverse play-by-play | **PARTIAL.** Penalty yards VERIFIED on three crew-seasons; penalty counts NOT reproduced (definition gap, below). | n/a |
| Muse's NBA record vs box officials / team box | **VERIFIED.** 236 of 239 referee-seasons matched; corr 1.00 on points/g and PF/g. | n/a |

A rigorous NO is a result. The crew term is not worth carrying into either engine as built.

## Part A — NFL crews into totals

Method. Each game's referee (nflverse `games.csv`) is joined to the crew's record from STRICTLY EARLIER seasons (archive `L3-split/nfl`, "season total" split: penalties logged, penalty yardage), shrunk to the league mean with K=16 pseudo-games. Unknown crew or first season = 0. Leakage test passes (`tests/test_nfl_crew.py`: nothing from the season being priced enters a feature). Because board v2 is a kernel-weighted library tilted so the market's total is the median, a crew effect can only enter as a shift of the anchor: `price_board(lib, spread, total + beta*x)`, beta fit on prior seasons (OLS through the origin of actual total minus total line on the feature). Base vs shifted priced on the same games; total ladder c+k for k in -10..10 step 2, team-total ladder around the implied team total.

Held-out 2019-2025 (n=1871 games), Brier gain = base minus shifted (positive favours the crew term):

| Feature | Total ladder gain [95% CI] | Team-total gain [95% CI] | corr(feature, residual) |
|---|---|---|---|
| penalties/g | -0.00001 [-0.00059, +0.00054] | +0.00002 [-0.00027, +0.00034] | -0.005 |
| penalty yards/g | +0.00007 [-0.00036, +0.00047] | +0.00007 [-0.00014, +0.00031] | -0.003 |

By season the sign flips (2020 corr +0.09, 2025 corr -0.11 for penalties): noise, not a trait. Feature is non-zero for 94% of games, so the null is not a coverage artefact. Assignment timing: nflverse carries the referee for each game; the league announces crews weekly, so the feature is knowable pre-price in principle (the test does not depend on the exact hour).

Verification against play-by-play (local `w99_1_nfl_verify.csv` (gitignored, not pushed), 2022-2024, 51 referee-seasons, play flag `penalty==1`):
- Penalty YARDS reproduce on the crew-seasons where game counts agree: Vinovich 2022 1045 vs 1044, 2023 1626 vs 1626; Cheffers 2022 1916 vs 1916. **VERIFIED on those three.**
- Penalty COUNTS do not: pbp is lower by 15-25% (archive 186 vs pbp 144 for Vinovich 2022). Consistent with the archive counting declined/offsetting penalties that nflverse's accepted-play flag omits, but that explanation is UNTESTED here. Across all 51, game counts match for 73% and the count correlation is only 0.24 (games the nflverse referee field assigns differently, playoffs). **Count: FAILED to reproduce as defined; the NFL penalties feature rests on an unverified definition.** The yards feature is the trustworthy one, and it is null too.
- Not done in this block: NFL 2026 vs Kalshi ladders (descriptive). No offline Kalshi NFL ladder file was in reach; carried to the next block.

## Part B — NBA referees into totals

Crew source and timing. The box `raw/officials` table is post-game with no assignment timestamp (GG-1390), and the bot-check probe of official.nba.com is not retried. So no free source was shown to give the crew before tip, and every NBA number is a **game-day-known UPPER BOUND**. (NBA posts crews on the day of the game, roughly 9am local, on official.nba.com; that is background knowledge, not verified here.)

Method. Prior-season referee record from the archive (`referees-<start-year>`: PF/g, FTA/g, total points/g; box_season = archive start year + 1), shrunk with K=30 games, crew feature = mean over the three officials. Match rate 98.6-99.1% of crew slots. Only box seasons 2025 and 2026 have a prior, so the fit window is ONE season (2025) and the test is 2026. Engine v2 gets the feature as a total factor via `fit_params(... total_factors)`.

Result (test 2026, n=1072): crew-prior vs total residual correlations 0.00-0.04; Brier gains on total and team-total ladders all have CIs spanning 0. The PF feature on team totals is slightly negative (-0.0010, CI -0.0020 to -0.00009). Unit-slope (no fit) total gain +0.00037, CI -0.0005 to +0.0012. Caveats: one fit season; no NBA market line offline, so no comparison to the market's own price.

Verification (local `w99_1_nba_verify.csv`, gitignored, not pushed): box officials joined to schedule points and team-box fouls vs the archive, 236 of 239 referee-seasons matched; median |games diff| 0, median |points/g diff| 0.02, median |PF/g diff| 0.03, corr 1.000 on both. E.g. Ray Acosta 2025 67 games, 226.8 vs 226.82. **VERIFIED** (well beyond three).

## Granularity index (five parts) and one line for Muse

NFL crews and NBA referees, same shape:
1. Split: crew-season penalty rate and yards (NFL); PF/g, FTA/g, points/g (NBA). Not split by situation.
2. Rank vs history: shrunk crew rate against all crews' prior-season record at the same point; ranks computed implicitly through the league-mean offset.
3. Matchup cross: NOT built. A crew effect should interact with the teams' foul-drawing and pace; the archive has no team-side foul split, so the cross is the missing piece.
4. Market map: total and team totals, direction = more penalties -> more clock stoppage and drive extension. Tested; no measurable move.
5. Application: the shifted-anchor path (NFL) and total_factors path (NBA) are the tested applications. Stage: **interpreted**, not applied, because the application found nothing.

Muse, NFL crews: yards/season is right to the yard; the penalty COUNT is defined differently from nflverse's accepted-play flag, so say whether it includes declined and offsetting penalties.
Muse, NBA referees: your register reproduces from the box to two decimals; add the per-game crew assignment with a posted-at time and it becomes usable before tip.

## Files
`src/prediction_market_bot/nfl_engine/crew.py`, `src/prediction_market_bot/nba_engine/crew_archive.py`, `tests/test_nfl_crew.py`, `tests/test_nba_crew_archive.py`, `12_EXPLORATORY/archive_officials/run_w99_1_{nfl,nba}.py`, `w99_1_{nfl,nba}_heldout.json`, `w99_1_nba_probe.json`, (verify CSVs kept local, gitignored).
