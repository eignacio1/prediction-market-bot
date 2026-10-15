# NFL engine stage 2 -- one factor class, aggregation to price (W75.2)

**Status:** PART A pushed; Part B pending. EXPLORATORY. **Decisions logged:** n/a (no strategic decision).
**Pillar:** DEPTH · D5(b) NFL factor class applied · D4 NFL factor classes point-in-time. Operator add-in applied (22:06 PT): the Cover 6 question
shows the granularity; the deliverable is the chain on one reusable factor builder.

**The operator, 2026-10-14:** "If I ask you what teams runs the most cover 6 against 3 wide out sets that's motioned to the boundary, matched with volume
and success rate - then I ask you to tell me what it means - you better be able to tell me. but that's not even the hardest part. data aggregation > data
interpretation > data application. Whats the hardest? I'll make it easy - data application is the basic question: cool info, so what?"

## Class chosen, and why
**F5/F6: coverage shell (and man/zone) x offensive personnel x pre-snap motion.** It is the one class where all three of coverage (participation),
personnel (participation) and motion (FTN) are in the free store, point-in-time, with 34-36k plays per season. Builder: `factors.py`
(`build_play_table` + `factor_values(plays, as_of, FactorSpec)`): event store + as_of -> per (unit, cell) n, share, EPA/play, success, opponent-adjusted EPA
(subtracting the facing offense's PIT baseline), empirical-Bayes shrunk. Point-in-time = kickoff + 4h <= as_of. A new class (pressure vs protection) is a new
`FactorSpec` over the same play table.

## Part A -- aggregation and interpretation
**Motion direction: GAP (GG-800).** No free field carries the direction or the boundary side (`starting_hash` is the ball's hash). Motion is motion yes/no only.
Fill (from `part_a.json`): shell on 53-61% of scrimmage plays 2018-2025; motion 2022+ only (GG-801).

**The question, literally (one illustration, 2025):** share of a defense's snaps in 11 personnel with pre-snap motion that were Cover 6. League rate
5.5%. Top (shrunk, k=40): SF 10.3% (30 of 273 snaps), LA 8.8% (28 of 302), ARI 7.7% (16 of 195), SEA 7.5% (24 of 308), HOU 6.9% (20 of 282).
Success when it was Cover 6: SF EPA +0.44/play (60% success on 30 snaps), LA +0.08 (46%), ARI +0.17 (44%), SEA +0.13 (50%), HOU -0.14 (45%). Volume is 15-30
snaps a team.

**Is it a trait or noise?** Two different answers, which is the point:
- *How often a defense shows a shell is a trait.* Split-half (odd vs even games, same season) correlation of shell share: Cover 1 0.80, Cover 2 0.79,
  Cover 3 0.77, Cover 4 0.69, Cover 6 0.66 (full-season reliability via Spearman-Brown 0.80-0.89). Year over year: Cover 1 0.46, Cover 2 0.45,
  Cover 4 0.39, Cover 6 0.32, Cover 3 0.30. Share of shell within a personnel group persists YoY at r 0.42-0.83.
- *How well an offense or defense does in a specific shell/personnel/motion cell is noise at one season.* Year-over-year correlation of raw cell EPA allowed
  (shell x personnel, n>=30 both years) is 0.04, 0.11, 0.05, 0.08, -0.04 for 2020-2024. The shrunk values correlate higher (0.13-0.69) only because both years are
  pulled toward the same league cell mean; that is shrinkage, not signal, and is not counted. The EB shrinkage strength hit its cap (k = 5000 plays), i.e. the
  data say team-specific cell success carries no usable variance.

**What it means for an offense facing it, plain words:** an offense can expect to see a defense's coverage mix before the snap and the mix is stable, so the "so what" is
about what the shell mix does to the offense's personnel groupings, priced at league cell values: a defense that is Cover-6-heavy against 11 personnel moves the expected EPA by the
difference between Cover 6 and the shell it displaces times the share. League EPA for 11 personnel: with motion +0.046, without +0.035 per play, so motion is worth about
a hundredth of a point per play before shell is considered. The Cover-6 "success" numbers above (SF +0.44, NO -0.82 on 15 snaps) are small-sample and must not be read as
a team trait. The tendency is real; the team-specific payoff is not measurable at this n. The application therefore prices the tendency (stable) at league payoff (stable),
not at the team's own cell success (noise).
