# NFL engine -- stage 3: F8 unit-level starter availability (EXPLORATORY, W76.2)

Paper/exploratory only. No order, stake, registry, runner or live-model change. Numbers: `part_a_avail.json` (Part A), `results_stage3.json` (Part B).

## Part A -- choice, orthogonality, interpretation

**Choice (five lines, one test: what does it know about THIS game that season-to-date team EPA cannot?)**
1. Team EPA/points rates are season averages over whoever played. They cannot know that *this week's* left tackle, slot receiver or top corner is out.
2. The final weekly injury report is public before kickoff for Sunday/Monday games (Thursday/Friday/Saturday games are excluded by the point-in-time contract, GG-732), so the information is knowable and arrives after the rating inputs are frozen.
3. QB is deliberately excluded: projected-starter QB EPA is already an arm-B input. This factor is the *rest of the roster*: OL, skill (WR/TE/RB), DL, CB, back seven.
4. Pressure-vs-protection (the other candidate) is built from the same play table the ratings use, so it re-expresses information the rating layer partly holds; availability is a different data source.
5. So the measurable claim is: expected snap-weighted starters lost, by unit, moves team points beyond what the ratings and the QB already say.

**Build.** `availability.py`: `AvailabilityFactor` on the existing `rate_layer.Factor` protocol (no second builder; the play-table `FactorSpec` cannot express a roster-state factor, so it is a Factor, not a FactorSpec). Per flagged non-QB player: usual starter share = mean snap pct over his last <=6 appearances (>=3, within 400 days, kickoff + 4h <= target kickoff, floor 0.40); weight = P(absent | status) estimated on training seasons only; units OL, SK, DL, CB, BK. Term = sum of unit coefficients x (lost - training mean) over the team's own offense units and the opposing defense units. Reports unusable (Thu/Fri/Sat game, or no report rows that team-week) return None = league average, never 0.

**Orthogonality, measured before fitting** (3,754 team-game sides, 2018-2025, 89.9% of team-games have a usable report; 12,257 flagged starter-games):

| Check | Value |
|---|---|
| max abs corr of any unit loss with any rating-layer input (EB off/def EPA, PF/PA, QB EPA, opp QB) | 0.10 (CB loss vs opp PA) |
| R2 of the fitted composite term on all rating inputs + arm-B mean points | 1.3% |
| corr of the composite term with arm-B mean points | 0.09 |
| term SD (points), coefficients fit on seasons <=2022 | 0.56 (stage 2's F5/F6 term: ~0.2) |
| out-of-sample (2023-25) corr of the term with arm-B team-point residual | +0.065 |

Verdict: ~99% of the term's variance is information the ratings do not hold. The first candidate passes; no fallback to pressure-vs-protection needed.

**Interpretation -- trait or noise, and what it means for the price.**
- *It is a state, not a trait.* A team's season-mean loss in one year predicts the next at r = 0.04 (OL), 0.18 (SK), -0.09 (DL), 0.02 (CB), 0.10 (BK). Who is hurt is a week-to-week fact; nothing to carry from last year.
- *Reliable pieces:* status is honest. P(absent | Out) = 0.9996, Doubtful 0.989, Questionable 0.30 (seasons <=2022; 4,621 / 740 / 6,896 flagged starters).
- *Offense units have stable-signed prices.* Stand-alone slope, points per starter-equivalent lost: OL -0.57 (<=2022) / -0.69 (2023+); skill -1.16 / -0.64. One missing starting lineman is worth about -0.6 of a team's points; one missing skill starter about -0.6 to -1.2.
- *Defense units are unstable.* DL 0.05 -> 1.86, BK -0.28 -> +0.71 (sign flips), CB +0.87 -> +1.97 (right sign, size doubles). These are the noise in the term.
- *So what for the price.* A typical week moves a team's mean by 0.56 points SD (about 0.3 points of margin once offsets cancel); a game with an unusually depleted line moves it 1-2 points. At an NFL margin SD near 13, a 1-point shift is ~3 pts of win probability -- real, but the same size as the vig and smaller than a Kalshi spread tick, and sportsbooks post injury-adjusted lines by Friday. Whether the Kalshi mid already carries it is Part B's market comparison; Part A claims only that the ratings do not.

## Part B -- the one fit (plan frozen in PLAN.md addendum W76.2, commit 1217dfb, before this run)

Rolling origin T = 2020..2025, 1,612 games, 40,000 draws/game, every family priced from the same simulation. F8 populated on 89.1% of games (rest = Thu/Fri/Sat or no report -> league average). `study_stage3.py`; raw in `results_stage3.json`. Environment: pandas 2.x (pandas 3 breaks `factors.eb_k`; not touched). One edit outside the new files: `factors.kickoff_utc` now tolerates a NaN `gametime` (a future-dated schedule row crashed the play-table build; no past row changes).

**Mean shift the term makes:** F8 moves a team's mean by 0.45 points on average (max 3.3), vs 0.10 for F5/F6 -- about 4.5x more movement, in a factor the ratings do not hold.

**ΔBrier, arm minus baseline (negative = better), game-cluster bootstrap 95% CI; upper limit decides (BEATS < 0, MATCHES < +0.0010):**

| Family | vs v0 (E-B): Δ [95% CI] | decision | vs v0+F5/F6 (F-C): Δ [95% CI] | decision |
|---|---|---|---|---|
| Moneyline | -0.00070 [-0.00189, +0.00051] | MATCHES | -0.00073 [-0.00192, +0.00050] | MATCHES |
| Spread | -0.00069 [-0.00174, +0.00040] | MATCHES | -0.00067 [-0.00173, +0.00043] | MATCHES |
| Total | +0.00032 [-0.00067, +0.00126] | **NO** | +0.00032 [-0.00066, +0.00126] | **NO** |
| Team total (own line) | -0.00046 [-0.00113, +0.00022] | MATCHES | -0.00047 [-0.00113, +0.00021] | MATCHES |

Control: F5/F6 alone (C-B) is inert again (|Δ| <= 0.0001 on every family), reproducing stage 2. F8 on top of F5/F6 changes nothing relative to F8 alone, so the two classes neither help nor interfere.

**Per season (E-B, ML):** 2020 -0.0023, 2021 -0.0002, 2022 **+0.0009**, 2023 -0.0004, 2024 -0.0017, 2025 -0.0006. Five of six seasons point the right way; 2022 is the exception on every family.

**Coefficients by fold (points per expected starter lost):** skill -1.19..-1.65 and OL -0.0..-0.41 are sign-stable in all six folds; CB is positive (+0.64..+0.94 after 2020), which is the wrong sign for "a missing corner helps the offense" only if read as causal -- it is the same noisy defensive piece Part A flagged; DL and BK change sign across folds (DL -0.38..+0.53, BK -0.12..+0.57). The SD of the term is 0.57-0.77 points per fold.

**Market comparison (reported, never judged).** 2025 KXNFLGAME moneyline mid at kickoff-30 min, n = 182 (MDE ~0.04 Brier): Brier B 0.2221, C 0.2223, E 0.2204, F 0.2207, mid 0.2115. E-B = -0.0016 [-0.0052, +0.0021]; E-mid = +0.0090 [-0.0052, +0.0222]. The market is still better than every arm by ~0.009; F8 closes ~0.0016 of that, well inside the noise. No spread/total/team-total mid exists in the archive for 2025.

### Verdict and stage (ADR-0075)
- **Stage reached: APPLIED** -- aggregated (Part A), interpreted (Part A), and run through the rate layer on a frozen plan with a measured ΔBrier on all four families. "Applied" means the chain ran once, point-in-time, with no leakage; it does not mean the term adds value.
- **Result:** MATCHES on moneyline, spread and team total (point estimates -0.0005 to -0.0007, CIs include 0, so not BEATS); **NO on totals** (upper limit +0.00126 > the +0.0010 margin). A NO on one family is a result: the unit coefficients shift both teams' means in the same direction (a depleted skill group lowers a team's points), and the total is the sum of two noisy shifts, so the fold-to-fold coefficient instability shows up there first. It was the pre-registered possible NO.
- **Plain reading.** The information is real and not already in the ratings (Part A), and the direction is right in 5 of 6 seasons on game sides, but the effect is about 0.0007 Brier, one-third of the noise in a 1,612-game sample. Offense-side starters (skill, OL) carry it; defense-side units are noise. It is a candidate for a thinner OL+skill-only term, not a pricing improvement we can claim. That reduced term is a post-hoc choice and would need its own frozen plan.
- **What did not happen:** no registry, runner, ledger, cron, order or model change. The seat file is not edited.
