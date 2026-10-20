# W81.2 Part A - lineup cross, parts 1-3 (EXPLORATORY, not a verdict)

Absorber-games: clean=110454 single-absence=11542. Clean-control mean effect (should be ~0): pts -0.232 min -0.491 fga -0.184

## 1. Split: net uplift of the absorber by the absent player's role

| role of absent | absorber-games | team-games | d_pts net [95% CI] | d_min net | d_fga net |
|---|---|---|---|---|---|
| creator | 1742 | 310 | +1.75 [+1.46,+2.06] | +1.72 | +1.43 |
| starter | 5857 | 1013 | +1.00 [+0.84,+1.18] | +1.59 | +0.84 |
| rotation | 3943 | 648 | +0.34 [+0.14,+0.54] | +0.76 | +0.32 |

## 2. Rank against history and stability

Split-half (odd/even game) Spearman of pair-level uplift, creator absences, absorber-team-seasons with >=6 creator-absence games: r=0.117 [-0.267,0.482] over 30 pairs.

Year-to-year Spearman (same absorber, >=3 creator-absence games in each of two consecutive seasons): r=0.435 over 25 absorber-season pairs.

Distribution of absorber-team-season mean uplift (pts) over 30 comparable cases: p5=-3.49, p25=-1.23, p50=+0.95, p75=+2.31, p95=+5.41.

## 3. Matchup cross: creator-absence uplift by opponent defence and pace tercile

| opp defence | n | d_pts net [95% CI] |
|---|---|---|
| good D | 425 | +1.06 [+0.50,+1.68] |
| mid | 558 | +1.29 [+0.75,+1.81] |
| weak D | 623 | +2.55 [+2.07,+3.08] |

| opp pace | n | d_pts net [95% CI] |
|---|---|---|
| fast | 557 | +2.57 [+2.05,+3.13] |
| mid | 568 | +1.06 [+0.58,+1.54] |
| slow | 481 | +1.52 [+0.90,+2.20] |

Frequency (share of team-games in the analysable set): creator=1.6%, starter=5.4%, rotation=3.4%; clean=89.5% (n team-games=19203).

## Reading (Part A stage: INTERPRETED, with a noise caveat on the player-level cut)

* Role-level redistribution is real and ordered: a creator out lifts a rotation absorber ~+1.75 pts (+1.7 min, +1.4 FGA) over the
  clean-game control; starter out ~+1.0; rotation out ~+0.3. CIs (resampling whole games) exclude zero.
* Player-level redistribution (who absorbs how much) is mostly noise at this sample: split-half r=0.12, CI crosses zero (30 cases);
  year-to-year r=0.44 on only 25 absorber-season pairs. The role cut is a trait; the individual cut is not established.
* Matchup cross: the creator-out uplift is larger against weak defences (+2.55 vs +1.06 vs good D) and fast opponents (+2.57 vs ~+1.1-1.5).
  Descriptive, tercile cuts pre-registered over all team-games; not an interaction test.
* Frequency: creator-out single-absence games are 1.6% of analysable team-games (310 games in ten seasons), starter 5.4%, rotation 3.4%.
* Limits: absence defined by box-score DNP with Injury/Illness comment (post-game fact; announcement time NOT in this table - Part B's
  point-in-time question). Clean control mean is negative (-0.23 pts) because rotation filters select players near a local high; the net
  figure subtracts it. Regular season only; 2016-2025.
* Reproduce: `python3 lineup_cross.py <NBA_EVENTS/raw> ` (about 9 min); `--reuse` reads events.parquet.
