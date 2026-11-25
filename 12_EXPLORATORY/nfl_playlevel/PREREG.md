# EXP-NFLPLAYLEVEL-001 — NFL play-level personnel / coverage / motion crosses as tree splits (pre-registration)

**Last reviewed:** 2026-11-24 (W128.3, B-120). **Status:** pre-registered, committed before any market outcome (score, margin, total, price)
is joined to any leaf. Docs + Part A aggregation only (Part A reads play EPA, not market outcomes). Doctrine: DOCTRINE.md §1 (ADR-0077), COMMON_RULES_W128.

**Measure moved:** DEPTH D5(b) NFL factor classes by stage. A factor is *applied* when it is a tested split scored per leaf on net after costs,
held out, per arm. A tested null counts as applied: it is a routing result.

## 1. Data (Part A, free nflverse, point-in-time)
`part_a.py` -> `team_game_playlevel.csv`: per (game, team) counts over regular-season pass and run plays (kneels, spikes excluded).
Sources: pbp; pbp_participation (offense personnel, coverage type, man/zone); ftn_charting (motion). **Coverage of the sources, stated plainly:**
participation personnel 2016-2025, **coverage type 2018-2025**, FTN motion 2022-2026, **participation is not served for 2026** (404).
2026 rows therefore have no personnel/coverage of their own; their tendencies are **carried** (the trailing window simply holds the last 17 games
that have data) and flagged `carried`. 2026 motion is real. Nothing is fabricated or imputed.

Per team-game counts: offense personnel mix (`11` = 1 RB 1 TE, `12`, RB>=2), plays vs two-high shells (COVER_2, 2_MAN, COVER_4, COVER_6) and
one-high shells (COVER_0, 1, 3, 9) with EPA on each, plays with motion, EPA / success, EPA on 11-personnel vs two-high; defense coverage mix
(two-high count, man count of dropbacks with a coded coverage). COMBO / BLOWN coverage is excluded from shell counts.

## 2. Tendencies (point-in-time)
Tendency of a team at a game = pooled ratio over its **previous 17 games with data** (any season), games strictly before the game date
(same-day games never seen), **minimum 6 games, else `unknown`**. Ratios: o1 = 11-personnel share of plays; d1 = two-high share of coded
dropbacks (defense); o2 = motion rate (FTN); d2 = man share of coded dropbacks; o3 = offense EPA per dropback-vs-two-high play, shrunk to the
league mean with k = 60 plays; d3 = d1. The `PITViolation` guard rejects any aggregate dated on or after the priced game.

## 3. The three crosses (matchup of the team's offense tendency against the **opposing** defense tendency)
| Cross | Offense tendency | Defense tendency | Reads as |
|---|---|---|---|
| X1 PERSONNEL x SHELL | o1 11-personnel share (3 WR sets) | d1 two-high share | 3-WR offense into a two-high shell |
| X2 MOTION x MAN | o2 motion rate | d2 man share | motion into man coverage |
| X3 SUCCESS x SHELL | o3 EPA vs two-high (shrunk) | d1 two-high share | offense that beats two-high into a two-high defense |

A team's cross leaf = (o high/low) x (d high/low), cut at the **median over the fit seasons' team-games** (fixed before 2025 is read):
`hi_hi`, `hi_lo`, `lo_hi`, `lo_lo`; any `unknown` tendency -> `unknown` (counted, never scored). Game-level leaf (spreads, totals):
AS = `home_only` / `neither_or_both` / `away_only` by which side's offence is `hi_hi`; AT = `none` / `one` / `both` `hi_hi` offences.
TT rows read the team-level leaf of the team whose total it is. (The 2x2 is the operator's "this offense set into this shell" cell, kept coarse
enough to hold >= 40 judged games per leaf; finer cells such as cover 6 x motion-to-boundary are registered as the next split, not tested here.)

## 4. Markets, prices, arms, costs (same as EXP-NFLSPLITS-001 s2, reused unchanged)
Markets TT (team total, both teams), AS (alternate spread, home side), AT (alternate total); rungs round(consensus) + {-6,-3,0,3,6} (TT) and
{-7,-3,0,3,7} (AS, AT); `board_v2` pmf anchored to the closing spread and total, library from earlier seasons only. **Proxy prices, not
tradable quotes** (no Kalshi history for these series before 2026). Arms per leaf: RIDE (buy the side priced >= 0.50), FADE (buy the other),
NO BET. Net = gross - `quant.costs.taker_entry_cost(series, side price, half_spread)`; half-spreads fixed at the archive medians
(AS 0.005, AT 0.010, TT 0.015), sensitivity at the means (0.0155, 0.0248, 0.0222). Leaf = cross bucket x market x price band (`mid` 0.25-0.75 YES
price, else `wing`). Gross, cost, net printed side by side.

## 5. Fit, judge, pooling, multiplicity
- **Fit seasons 2020-2024** for X1 and X3 (coverage exists from 2018; 2018-2019 only build the 17-game window). **X2 fit 2023-2024** (FTN from 2022;
  2022 builds the window). Fit is never read for the judge season.
- Per (cross, market, arm): game-clustered mean net per leaf (`variance.clustered_mean`), **partial pooling** over the leaves
  (`variance.partial_pool`). Arm per leaf = the better shrunk fit arm if its 90% shrunk lower bound > 0, else NO BET. Fixed before 2025.
- **Judge set 1: 2025 REG** (held out). Judged = leaf x arm with a fit route, >= **MIN_N = 40 games**. 90% game-clustered bootstrap
  (B = 2000), one-sided `pooled_cluster_test`, **BH q = 0.10** across the family of fit-routed judged rows. Both arms are always printed for every
  leaf (descriptive) so a fit NO BET leaf still shows whether either arm would have cleared. Verdict words: *arm earned in this leaf* (net > 0,
  interval excludes 0, BH significant) / *routed to ride / no bet in this leaf* / *not judged: n below MIN_N (n=...)* / *not judged: inputs unknown*.
- **Judge set 2: 2026 REG rows to date**, same fit routing, same proxy prices (library built before 2026), **descriptive, no BH, never pooled with 2025**.
  Personnel / coverage leaves in 2026 are `carried` (see s1); the 2026 look is therefore a look at carried tendencies and is labeled so.
- **Shadow forward look:** none produced by this block (Part B ships default off: `PM_NFL_PLAYLEVEL`). The forward look is pre-registered for when
  `variance.games_needed` (2025 SD and ICC) is met; not read before then.

## 6. Modal outcome, and what each result does
**Expected: no arm earned**, most leaves routed to ride / no bet, X2 thin (two fit seasons) and several `hi_hi` leaves not judged for n at 2025's 272
games. The consensus lines already carry public pace, personnel and coverage information, so a null on proxy prices is the modal case, not a failure.
If a leaf earns an arm it is reported as "arm earned on proxy prices", not tradable. A losing look closes only this hypothesis ("hypothesis
closed, EXP-NFLPLAYLEVEL-001, parked for R&D"); no cell, market or arm closes. Seat stages move only for crosses with >= 1 judged leaf.

## 7. Overlap with earlier looks (stated, not hidden)
W126.5 (EXP-NFLSPLITS-001) tested team-level qb / rest / officials / weather / matchup on the same markets and prices: 0 earned. The N20/N21 coverage
and pressure work (nfl_engine/coverage_gap) scored coverage mix against totals at team-game level. This test is new in crossing a personnel / motion /
success tendency with the opposing coverage tendency as a 2x2 leaf on these markets; X1-X3 reuse no leaf from W126.5.

## 8. Part B contract (code, default off)
`decision_trees/filters/nfl_playlevel.py`: leaf functions from pre-game tendencies only (`PITViolation` on any aggregate dated at or after kickoff
day, `unknown` for missing tendencies, `carried` flag when the team's newest participation game is before the current season). Candidate
`nfl_playlevel` in `shadow_route.CANDIDATES` behind `PM_CANDIDATE_ARMS` and `PM_NFL_PLAYLEVEL` (default off). Shadow only; orders follow v1;
`kelly_fraction` untouched.
