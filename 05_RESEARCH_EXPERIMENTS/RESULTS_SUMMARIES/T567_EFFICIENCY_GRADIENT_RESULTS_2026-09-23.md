# T-567 — Market-Efficiency-Gradient Ranking: Results

**Pre-registration:** `T567_EFFICIENCY_GRADIENT_PREREGISTRATION_2026-09-23.md` (same
directory, pushed immutable before any number below was computed). This
document reports what the pre-registered method found. It does not revise
the method, and it does not decide anything CLAUDE.md's Market Efficiency
Gradient section leaves as an open operator decision.

**Data:** local mirror of `exp_output/PRICE_ARCHIVE/` (`prices_*.jsonl`,
`depth_*.jsonl`), 2026-08-01 through 2026-09-23 for MLB, 2026-09-05 (price) /
2026-09-09 (depth) through 2026-09-22/23 for NFL. **Read-only for this task**
— no changes to the archiver, its cron schedule, or any capture window.

**Compute:** `scripts/efficiency_gradient_ranking.py`, 2,000-iteration
market-resampling bootstrap per family, run in full against the complete
archive (14 families, ~1.8M total price rows, ~15,700 usable depth rows).
Parallelized across forked worker processes for wall-clock speed only — same
2,000 total iterations, same per-iteration resampling algorithm, same joint
cross-family ranking as a single-threaded run would produce; this is an
engineering change, not a methodology change, and does not touch anything
the pre-registration fixed.

---

## Deliverable 2 — Full 14-family ranking, most to least efficient

ERI = mean of three per-dimension ranks (tightness, depth, participation),
lower = more efficient. `boot_med` / `ci90` = bootstrap median and 90%
percentile interval over 2,000 iterations resampling markets. Two families
whose 90% intervals overlap are reported as **tied**, per the pre-registered
rule — never as an arbitrarily broken order.

| Rank tier | Family | Coarse group | Sport | n markets | n price rows | Price date span | n depth (usable) | Tightness (med. rel. half-spread) | Depth (med. $ w/in 5c) | boot median ERI | 90% CI |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 (tie) | `KXNFLGAME` | GAME_WINNER | NFL | 96 | 13,908 | 09-05→09-22 | 201 | 0.0267 | $1,016.75 | 3.50 | [3.50, 3.83] |
| 1 (tie) | `KXMLBTOTAL` | GAME_TOTAL | MLB | 8,399 | 224,080 | 08-01→09-23 | 1,174 | 0.0299 | $3,828.01 | 3.83 | [3.50, 3.83] |
| 2 (tie, 8-way) | `KXMLBSPREAD` | RUN_LINE | MLB | 5,677 | 133,300 | 08-01→09-23 | 1,137 | 0.0465 | $582.12 | 5.50 | [5.33, 5.50] |
| 2 (tie) | `KXNFLTOTAL` | GAME_TOTAL | NFL | 957 | 69,367 | 09-05→09-22 | 191 | 0.0397 | $73.32 | 5.83 | [5.50, 6.83] |
| 2 (tie) | `KXMLBGAME` | GAME_WINNER | MLB | 1,492 | 109,416 | 08-01→09-23 | 2,428 | 0.0286 | $52.16 | 6.17 | [5.50, 6.50] |
| 2 (tie) | `KXNFLSPREAD` | RUN_LINE | NFL | 1,299 | 94,759 | 09-05→09-22 | 187 | 0.0719 | $139.52 | 6.33 | [6.17, 7.83] |
| 2 (tie) | `KXMLBF5TOTAL` | GAME_TOTAL | MLB | 4,886 | 133,371 | 08-01→09-23 | 1,052 | 0.0460 | $69.91 | 6.50 | [6.17, 7.00] |
| 2 (tie) | `KXNFLTEAMTOTAL` | TEAM_TOTAL | NFL | 1,299 | 62,803 | 09-05→09-22 | 182 | 0.0938 | $104.00 | 7.50 | [7.17, 7.83] |
| 2 (tie) | `KXMLBF5` | PARTIAL_GAME_WINNER | MLB | 2,094 | 57,012 | 08-01→09-23 | 1,129 | 0.0800 | $60.88 | 8.17 | [7.50, 9.17] |
| 2 (tie) | `KXMLBTEAMTOTAL` | TEAM_TOTAL | MLB | 9,856 | 294,000 | 08-01→09-23 | 2,129 | 0.0741 | $40.60 | 8.67 | [8.17, 8.83] |
| 3 (tie) | `KXMLBF5SPREAD` | RUN_LINE | MLB | 2,792 | 76,048 | 08-01→09-23 | 1,171 | 0.1143 | $22.73 | 10.17 | [10.17, 10.17] |
| 3 (tie) | `KXMLBHIT` | PLAYER_PROP | MLB | 33,285 | 441,927 | 08-01→09-23 | 1,733 | 0.1538 | $48.20 | 10.17 | [9.50, 10.50] |
| 4 (standalone) | `KXMLBF7` | *(never depth-sampled — §1 of pre-reg)* | MLB | 2,103 | 60,078 | 08-01→09-23 | 0 | 0.2400 | n/a | 10.75 | [10.75, 10.75] |
| 5 (standalone, least efficient) | `KXMLBF3` | PARTIAL_GAME_WINNER | MLB | 2,094 | 54,126 | 08-01→09-23 | 1,146 | 0.1333 | $0.77 | 10.83 | [10.83, 10.83] |

**Degenerate (point) 90% CIs for `KXMLBF5SPREAD`, `KXMLBF7`, `KXMLBF3`** are
not a computation error: each of these three sits far enough outside every
other family's dimension values (extreme tightness and/or depth outliers)
that no bootstrap resample of their underlying markets moves their *relative
rank* against the other 13 families — the resampled point statistic itself
still varies, but the resulting rank is stable across all 2,000 iterations.
This is a property of a family being an unambiguous outlier on its own
dimensions, not an artifact of insufficient resampling.

**Tie-group structure (5 groups, most to least efficient):**
1. `KXNFLGAME`, `KXMLBTOTAL`
2. `KXMLBSPREAD`, `KXNFLTOTAL`, `KXMLBGAME`, `KXNFLSPREAD`, `KXMLBF5TOTAL`, `KXNFLTEAMTOTAL`, `KXMLBF5`, `KXMLBTEAMTOTAL`
3. `KXMLBF5SPREAD`, `KXMLBHIT`
4. `KXMLBF7`
5. `KXMLBF3`

The middle tie group spans 8 of 14 families and both sports — at this
sample size and with equal-weighted dimensions, the method cannot
distinguish MLB's core-four markets from NFL's on efficiency grounds; they
occupy the same broad band.

### NFL rankability check (pre-registered rule, computed against final numbers)

Rule (fixed in advance): NFL is reportable only if every NFL family's
bootstrap 90% CI width is ≤ half the full observed cross-family ERI median
range (max median − min median across all 14 families).

- Full cross-family range: 10.83 − 3.50 = **7.33**; half = **3.67**.
- `KXNFLGAME` CI width: 0.33 — within threshold.
- `KXNFLTOTAL` CI width: 1.33 — within threshold.
- `KXNFLSPREAD` CI width: 1.67 — within threshold.
- `KXNFLTEAMTOTAL` CI width: 0.67 — within threshold.

**All four NFL families pass the pre-registered rankability threshold.**
This is reported as found: the pre-registration flagged NFL's much smaller
sample (n≈182–201 depth rows/family over 13 days vs. MLB's 1,000+ over 51
days) as a real risk to rankability, and that risk did not materialize into
unrankable CIs — NFL's point estimates land in narrow bands despite the
thinner sample. That does not mean the NFL estimates are as reliable as
MLB's in every other sense (see "What this does not establish" below); it
means the specific pre-registered CI-width test is satisfied.

---

## Deliverable 3 — Where `KXMLBHIT` sits, and where the core four would place the bot

**Does `KXMLBHIT` sit at the inefficient end, as CLAUDE.md's premise
requires? Directionally yes; strictly, no — two families are measurably
less efficient than it.**

`KXMLBHIT` — the only cell this bot has ever actually traded (T4M-PROJ) —
ranks in tie-group 3 of 5, tied with `KXMLBF5SPREAD` at boot-median ERI
10.17, CI [9.50, 10.50]. That places it in the bottom 3 of 14 families by
median rank, and its own CI does not overlap with tie-group 2 above it
(closest neighbor `KXMLBTEAMTOTAL` at 8.67, CI [8.17, 8.83] — no overlap
with `KXMLBHIT`'s [9.50, 10.50]), so its separation from the broad
core-markets tie group is real, not a coin flip.

But it is **not** the single least-efficient family. `KXMLBF7` (median
10.75, CI [10.75, 10.75]) and `KXMLBF3` (median 10.83, CI [10.83, 10.83])
both have CIs that do not overlap `KXMLBHIT`'s [9.50, 10.50] — they are
genuinely, not just nominally, less efficient than `KXMLBHIT` by this
measure. Both are MLB partial-game winner markets (first-7-innings and
first-3-innings winner, respectively), not player props. `KXMLBF3` in
particular has the lowest observed depth of any family in the data
(median $0.77 within 5c of mid — three orders of magnitude below
`KXMLBHIT`'s $48.20).

**Per the pre-registration's own instruction (§6): this is reported as a
direct, partial empirical challenge to CLAUDE.md's stated premise, not
smoothed over.** CLAUDE.md frames `KXMLBHIT`/player props as *the*
inefficient end the strategy is designed to exploit. The measured gradient
instead shows `KXMLBHIT` deep in the inefficient tail but not at its
absolute floor — two lower-liquidity, lower-attention MLB partial-game
markets sit further out. The premise that low-attention MLB windows are
inefficient relative to the core markets holds; the specific claim that the
one traded cell is uniquely or maximally inefficient does not hold at this
sample.

**Where would the core four place the bot?**

Both sports' core four (`GAME_WINNER`/moneyline, `RUN_LINE`/spread,
`GAME_TOTAL`/totals, `TEAM_TOTAL`) land almost entirely in tie-groups 1–2 —
the efficient half of the gradient, well separated from `KXMLBHIT`:

- **MLB core four:** `KXMLBTOTAL` ties for *most* efficient of all 14
  families (rank tier 1, boot median 3.83). `KXMLBSPREAD` (5.50) and
  `KXMLBGAME` (6.17) sit in the broad mid tie-group. `KXMLBTEAMTOTAL` (8.67)
  is the least efficient of the MLB core four but still ties into the same
  broad group, one full non-overlapping tie-group above `KXMLBHIT`.
- **NFL core four:** `KXNFLGAME` ties for most efficient of all 14
  (3.50). `KXNFLTOTAL` (5.83), `KXNFLSPREAD` (6.33), and
  `KXNFLTEAMTOTAL` (7.50) all sit in the same broad mid tie-group as MLB's
  core four — none of NFL's core four measurably separates from MLB's.

**Net effect on the coverage-target roadmap's own framing:** every core-four
cell, in both sports, measures as more efficient than the one cell that has
ever traded — most by a wide, non-overlapping margin. CLAUDE.md's
description of the core four as "the opposite end of the efficiency
gradient" from `KXMLBHIT` is directionally confirmed by this measurement.
Whether that gap is small enough to trade into, or too large, is exactly
the open operator decision this task does not resolve.

---

## What this analysis does not establish

(Restated from the pre-registration; unchanged by the results.)

- **Efficiency is not edge.** Nothing here measures whether this project's
  calibrated model has, or could have, an edge against any family — thin
  and wide-spread does not imply beatable; the sharpest counterparties often
  concentrate exactly in the thinnest markets.
- **This measures pricing structure, not the operator decision.** It does
  not recommend expanding into, or holding away from, any market family,
  and it does not resolve the tension CLAUDE.md's Market Efficiency Gradient
  section records as open.
- **Equal-weighting the three dimensions is a stated assumption, not a
  derived one.** A different, equally defensible weighting could reorder
  families whose ranks are already close — which is most of the 8-way
  middle tie-group. The tie rule exists precisely so this ambiguity is
  visible rather than hidden behind a single confident-looking rank number.
- **Sample coverage is uneven and time-bound.** MLB spans ~51–54 days deep
  into one regular season; NFL spans 13–18 days across two early-season
  weeks. Neither includes an off-season, a playoff push, or more than one
  season. This is one snapshot of these markets' behavior, not a structural
  constant — a resample at another point in either season could reorder the
  8-way middle tie-group without contradicting anything reported here.
- **The two excluded diagnostics (price-discovery-speed variance,
  open-window drift) were not folded into the composite** (ambiguous sign /
  not measurable from this archive — pre-registration §4) and are not
  reported here; their absence does not mean they would agree with this
  ranking if they could be measured.

---

*Compute artifacts: `scripts/efficiency_gradient_ranking.py`,
`exp_output/EFFICIENCY_GRADIENT/eri_report.json` (this branch). Raw local
archive mirror (`exp_output/PRICE_ARCHIVE_LOCAL/`) is scratch input, not
committed, per the task's scope fence.*
