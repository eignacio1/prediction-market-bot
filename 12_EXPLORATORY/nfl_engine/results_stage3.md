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
