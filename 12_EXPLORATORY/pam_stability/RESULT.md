# H-DEPTH-PAM-3 RESULT (block 124.5, run 2026-11-23, one judged read)

Pre-registration `PREREG.md` frozen at **16fcd204d5e41995c761d8e3d27b71c121024620**, plus `PREREG_ADDENDUM_1.md` (committed 743a7e1, before any
2023-2025 row was loaded). Code `run_pam3.py`; raw numbers `results.json`. Fit 2016-2022 (dispersion 2017-2022), judged 2023, 2024, 2025,
regular season, 52,230 eligible player-games in 3,519 games, 4 stats x 5 thresholds = 1,044,600 scored rows.

## Verdict by the PREREG rule: **SUPPORTED**
Pooled D = log-loss(control) - log-loss(challenger) = **+0.00201**, 90% game-clustered bootstrap (2,000 resamples, seed 20261121)
**[+0.00184, +0.00219]**, wholly above 0, and D > 0 on 4 of 4 stats. All four survive BH at q 0.10.

| Stat | D | 90% interval | BH q 0.10 | D, 4-10 prior games | 11-30 | 31+ |
|---|---|---|---|---|---|---|
| points | +0.00204 | [+0.00179, +0.00228] | yes | +0.00906 | +0.00168 | +0.00027 |
| rebounds | +0.00137 | [+0.00121, +0.00152] | yes | +0.00730 | +0.00085 | +0.00004 |
| assists | +0.00139 | [+0.00121, +0.00159] | yes | +0.00752 | +0.00078 | +0.00008 |
| threes | +0.00324 | [+0.00282, +0.00368] | yes | +0.01714 | +0.00197 | +0.00017 |

Pooled by prior-games stratum: 4-10 **+0.01025** [+0.00927, +0.01130] (7,446 units);
11-30 +0.00132 [+0.00116, +0.00148] (18,936); 31+ +0.00014 [+0.00010, +0.00018] (25,848).

Log-loss / Brier, control -> challenger: points 0.3552 -> 0.3532 / 0.1127 -> 0.1123;
rebounds 0.3450 -> 0.3436; assists 0.3030 -> 0.3016;
threes 0.3874 -> 0.3842.

**Size, stated plainly.** The gain is about 0.6% of the control's log-loss (0.002 on ~0.35), almost all of it in a player's first 4-10 prior games of a season
(0.010); by 31+ games it is 0.0001. This is a calibration comparison of two probability inputs, gross, with no price, spread or fee in it. A tighter
interval does not create an edge, and nothing here says a bet clears costs.

## Decomposition (secondary, addendum A4)
"Raw rate x raw minutes" equals the control exactly (max abs difference 7.1e-15), so it cannot separate anything. The two partial arms do:
**rate-only** D = +0.00185 [+0.00170, +0.00202];
**minutes-only** D = +0.00018 [+0.00014, +0.00022].
About 92% of the gain is the shrunk rate; shrunk minutes add a small amount (assists minutes-only interval includes 0).

## Reliability (training seasons 2016-2022, players >= 1,000 minutes; FT% >= 200 attempts)
| Stat | r split-half | r full (Spearman-Brown) | r year-to-year (descriptive) | k, minutes (90% CI) | player-seasons |
|---|---|---|---|---|---|
| points | 0.936 | 0.967 | 0.869 | 60.1 (55.8-64.8) | 1876 |
| rebounds | 0.970 | 0.985 | 0.944 | 27.3 (25.0-29.4) | 1876 |
| assists | 0.967 | 0.983 | 0.910 | 30.2 (27.6-32.6) | 1876 |
| threes | 0.930 | 0.964 | 0.891 | 66.7 (60.9-71.2) | 1876 |
| blocks | 0.923 | 0.960 | 0.902 | 74.1 (66.3-80.6) | 1876 |
| steals | 0.737 | 0.849 | 0.777 | 316.0 (280.3-342.6) | 1876 |
| ft_pct | 0.875 | 0.933 | 0.897 | 23.3 (19.2-27.1) | 550 |
| mpg | 0.976 | 0.988 | nan | 0.8 (0.8-0.9) | 1876 |

The operator's fantasy-test figures (0.90 / 0.69 / 0.81) are descriptive and not comparable one for one: ours are full-season per-minute rates for players with
>= 1,000 minutes, so role and minutes noise are removed. By that measure points, rebounds, assists, threes, blocks and FT% are highly reliable; steals is the
least stable (k ~ 316 minutes). k for FT% is in attempts, for minutes per game in games.

## Pre-stated modal outcome (P3) vs what happened
Stated: SUPPORTED, gain concentrated in 4-10 prior games, largest for threes and assists, near zero for points by 31+.
Happened: SUPPORTED yes; concentrated in 4-10 yes (0.0103 vs 0.0001); threes largest yes (0.0032 pooled, 0.0171 in 4-10); **assists not** (0.0014 pooled, the
smallest with rebounds; points 0.0020 is larger); points near zero by 31+ yes (0.0003). Three of four parts matched.

## Consequence in routing words (PREREG §7)
SUPPORTED licenses an EXP-047 challenger (stability-weighted shrunk mean as the props arm's mu) with **its own pre-registration in a later wave**. It is not applied:
it enters the tree only when the router scores it per leaf on net after costs, held out. Nothing in a live path, model, runner, leaf map, cron or box changed.

## Power and limits
Per-game sd of the mean difference 0.0062, 3,519 games; MDE at 80% power 0.00026. Scored on thresholds from a
negative-binomial layer with dispersion fitted on training; prior games are the player's games with the same team in the same season. Effect is a prior-quality
effect, strongest early in a season, so its routing value is early-season and for players with few games.

## Block 128.4 verification and Part B (2026-11-24)
No judged season was re-read: the one judged run is W124.5's (2026-11-23, `--final` once). Block 128.4 re-checked `results.json` against this file (pooled D, per-stat D and
intervals, BH flags, strata and decomposition all match) and the PREREG §6 rule (interval wholly above 0, 4 of 4 stats positive), and rebased PR #555 onto main with PREREG.md
untouched (last commit 16fcd20). Known-answer test and exploratory-isolation test pass locally (237 passed).

**Part B, PREREG §7 (SUPPORTED).** Class 3 at NBA player level moves absent -> interpreted. `trait_reliability_draft.json` is the first set of rows (training seasons 2016-2022;
a draft, not read by any live path). Next: an EXP-047 challenger using the shrunk mu, with its own pre-registration, logged beside the live map and scored per leaf on net
after costs. It is not applied.
**C2 inputs.** C2 (`nba_props_role/RESULT_C2.md`) redistributes an Out player's usage on top of EXP-047's trailing average. Whether C2 should start from the shrunk rates and
shrunk minutes is a different test (shrinkage x absorption on a population no earlier test judged), so it needs its own pre-registration in a later wave. The gain here is mostly
4-10 prior games (0.0103), so the question matters most early in a season and for players with few games.
