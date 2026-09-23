# T-567 — Market-Efficiency-Gradient Ranking: Pre-Registration

**Status:** IMMUTABLE once pushed. This file is written and committed before any
efficiency number in it has been computed. It is not edited after the ranking
(Deliverable 2) is run — corrections, if any are ever needed, go in a superseding
file, the same convention CLAUDE.md uses for ADRs.

**Purpose:** CLAUDE.md's Market Efficiency Gradient section asserts the strategy
is designed to exploit low-attention, thinly-priced MLB windows, then separately
records — as an unresolved open operator decision — that the coverage target
expands toward moneyline/spread/totals/team-totals, "the opposite end of the
efficiency gradient." That gradient has never been measured against the
project's own archived price/depth data; it has only been argued from priors
about public attention. This document fixes, in advance, what "more efficient"
means operationally and what ordering is expected, so the measurement that
follows (T-567 Deliverable 2) cannot be quietly reshaped after the fact to fit
whatever the numbers turn out to say.

**Scope:** evidence only. This document and its companion results file do not
decide, and are not written to be read as deciding, whether the operator should
expand coverage toward the efficient end of the gradient. See CLAUDE.md's
Market Efficiency Gradient section, "Open departure from this section."

---

## 1. Data sources (fixed, as they exist today)

Both sources are VPS-only production archives (`archive_market_prices.py`,
created 2026-08-01); no local mirror exists in this repo. Read-only for this
task — no write access, no changes to the archiver or its cron schedule.

- **`exp_output/PRICE_ARCHIVE/prices_YYYY-MM-DD.jsonl`** — one row per
  `(series_ticker, ticker, run_ts)` snapshot, `status="open"` markets only
  (the archiver's own fetch filter — see §3 for what this rules out).
  Confirmed live range at time of writing: **2026-08-01 through 2026-09-23**
  for all 10 MLB series; **2026-09-05 through 2026-09-23** for all 4 NFL
  series (NFL price archiving began with Week 1 deploy, GG-245/T-521).
- **`exp_output/PRICE_ARCHIVE/depth_YYYY-MM-DD.jsonl`** — orderbook-depth
  samples, `--depth-sample-per-family` cron flag, `usable` boolean gate.
  Confirmed live range: **2026-08-04 through 2026-09-23** for 9 of 10 MLB
  series (`KXMLBF7` is not depth-sampled — confirmed absent from every depth
  file checked, not a data gap in this analysis); **2026-09-09 through
  2026-09-22** for all 4 NFL series (NFL depth sampling was deliberately
  withheld until T-537/GG-265 to protect T4M-PROJ's read budget — this is
  the source of the task's "~201 rows per family" figure for NFL: 201 depth
  rows/family over 13 days, vs. MLB's 1,213–2,426 depth rows/family over 51
  days).

## 2. Family unit (fixed)

**A "family" = one `series_ticker`.** 14 exist in live data today: 10 MLB
(`KXMLBGAME, KXMLBSPREAD, KXMLBTOTAL, KXMLBTEAMTOTAL, KXMLBHIT, KXMLBF3,
KXMLBF5, KXMLBF7, KXMLBF5SPREAD, KXMLBF5TOTAL`) and 4 NFL (`KXNFLGAME,
KXNFLSPREAD, KXNFLTOTAL, KXNFLTEAMTOTAL`).

**Discrepancy noted, not silently absorbed:** the task brief's working number
was "eleven families." The live count is 14 at series-ticker granularity, or
10 if rolled up to the coarser `(sport, market_type)` label the codebase's
own classifier (`phase0_market_survey.py:FAMILY_PATTERNS`) already uses for
depth-sampling and survey purposes (MLB: `GAME_WINNER, RUN_LINE, GAME_TOTAL,
TEAM_TOTAL, PLAYER_PROP, PARTIAL_GAME_WINNER` = 6; NFL: the same four minus
`PLAYER_PROP`/`PARTIAL_GAME_WINNER` = 4; total 10). Neither figure is 11.
Series-ticker granularity is used here, not the coarser roll-up, because
collapsing `KXMLBTOTAL` (full-game total) into the same bucket as
`KXMLBF5TOTAL` (first-5-innings total) would average together two products
with materially different audiences, liquidity, and time-to-close — exactly
the kind of averaging that would obscure, not measure, the gradient this task
exists to locate. Deliverable 2 will report the real count found (14, or 10
at the coarser MLB/NFL-only roll-up shown alongside for cross-reference) and
will not force it to 11.

## 3. What this data cannot measure (fixed, decided before computing)

The archiver's own fetch call restricts to `status="open"` markets
(`archive_market_prices.py`, `_fetch_series_markets`). **No snapshot of any
market after it leaves `open` status is ever archived — there is no true
settlement/closing price in this data set, for any family.** This rules out
literally computing "distance from `last_price` to closing price" as the task
brief poses it; see §4 for the substitute and why it is weaker, and reported
only as a diagnostic rather than folded into the composite.

## 4. Observables considered, included/excluded decision, and why

Three included in the composite score; two considered and excluded, with
reasoning fixed now rather than after seeing results:

**INCLUDED — TIGHTNESS.** Median relative half-spread,
`2 * half_spread / yes_mid`, computed only over rows with `0.05 ≤ yes_mid ≤
0.95` (relative spread is mechanically inflated near 0/1 for reasons that
have nothing to do with market efficiency — a 1c spread on a 2c market is
50% relative spread and would otherwise dominate the metric). Lower ⇒ more
efficient. Source: price archive, `half_spread`/`yes_mid` fields (already
computed and stored by the archiver, not re-derived).

**INCLUDED — DEPTH.** Median `within_5c_usd_min_side` (dollar notional a
taker could absorb within 5c of mid, worst side) over `usable=true` depth
rows. Higher ⇒ more efficient. Per GG-155/T-411 (depth swings 10–100x
intraday), this is treated as a volatile time series: the whole available
sample is used, median (not mean) is the point statistic, and uncertainty is
reported via bootstrap (§5) rather than a single reading being trusted as
representative — the exact failure mode GG-155 was registered for.

**INCLUDED — PARTICIPATION.** Per market, take the maximum observed `volume`
and maximum observed `open_interest` across all its snapshots (both fields
are cumulative-since-open counters on Kalshi's `/markets` response, so the
max observed reading is that market's final tally while still open). Rank
families separately on median-max-volume and median-max-open_interest, then
average those two ranks into one participation rank — they are two readings
of the same underlying "public attention" concept CLAUDE.md's own efficiency-
gradient argument is built on, and averaging them here (rather than each
entering the composite as its own independent dimension) avoids double-
counting that one concept. Higher ⇒ more efficient.

**EXCLUDED — price-discovery speed (variance of `yes_mid` changes approaching
close).** Sign is theoretically ambiguous without trade-level or information-
arrival attribution this data set does not carry: high variance late in a
market's life could mean the market is efficiently incorporating real,
fast-arriving information (efficient), or it could mean the market is thin
and noisily ping-ponging on small, uninformed orders (inefficient) — the two
look identical in `yes_mid` alone. Folding an ambiguous-sign variable into a
composite risks manufacturing a directional finding out of noise. Computed
and reported as a diagnostic column only, never as part of the ranked score.

**EXCLUDED — distance from `last_price` to closing price.** Not measurable
from this archive at all (§3 — no post-close snapshot exists for any family).
The nearest available substitute — first-observed vs. last-observed `yes_mid`
while a market was still open — is confounded by how long before close each
family's markets typically open (a market open for six hours has structurally
more room to drift than one open for six minutes), and different families in
this data are not comparable on that axis without a normalization this
pre-registration is not going to invent post hoc. Computed and reported as a
diagnostic ("open-window drift") only, not part of the composite.

## 5. Composite score and uncertainty (fixed)

**Efficiency Rank Index (ERI)** = mean of three per-dimension ranks
(tightness-rank, depth-rank, participation-rank), each computed by ranking
all rankable families 1..N on that dimension (1 = most efficient) and
averaging equal-weighted — no principled basis exists yet to weight one
dimension over another, and asserting one without justification would be
exactly the kind of unstated assumption CLAUDE.md's adversarial protocol
exists to catch. This is stated as a limitation, not resolved by picking
weights that happen to produce a clean story.

**Uncertainty:** for each family, bootstrap resample its underlying markets
with replacement (2,000 iterations; resampling markets, not individual
snapshot rows, so within-market snapshot autocorrelation does not manufacture
false precision), recompute each dimension's statistic and the resulting ERI
per iteration, and report the median ERI with a 90% percentile interval.

**Tie rule (fixed):** two families whose 90% ERI intervals overlap are
reported as tied, not as an arbitrarily broken ordering. This is the literal
instruction in the task brief and is restated here so it cannot be softened
later.

**NFL rankability rule (fixed):** NFL depth data is n=201 rows/family over 13
days spanning two NFL weeks (§1) — a far thinner sample than any MLB family's.
If NFL's bootstrap 90% ERI intervals span more than half of the full
observed cross-family ERI range (rank 1 to rank N), NFL will be reported as
"not meaningfully rankable at this sample size," per the task brief's own
instruction to say so plainly rather than force a rank. This threshold is
fixed now, before the NFL numbers are computed, so it cannot be adjusted
after the fact to produce a more or less confident-looking result.

## 6. Expected ordering, stated before computing

Per CLAUDE.md's own stated thesis (Market Efficiency Gradient section): MLB
player props in low-attention windows are the intended inefficient end, and
NFL / full-game "core four" markets are explicitly named as the efficient,
high-attention end ("the most-attended, most-efficiently-priced markets on
the board"). The expected ordering, most-efficient to least-efficient:

1. NFL core four (`KXNFLGAME, KXNFLSPREAD, KXNFLTOTAL, KXNFLTEAMTOTAL`) —
   expected most efficient of all 14, if rankable at all (§5).
2. MLB core four (`KXMLBGAME, KXMLBSPREAD, KXMLBTOTAL, KXMLBTEAMTOTAL`) —
   expected more efficient than MLB's partial-game and player-prop families,
   less efficient than NFL's equivalents.
3. MLB partial-game markets (`KXMLBF3, KXMLBF5, KXMLBF7, KXMLBF5SPREAD,
   KXMLBF5TOTAL`) — expected to sit between MLB's core four and `KXMLBHIT`:
   lower attention than full-game markets, but structurally similar
   game-outcome products rather than player-level props.
4. `KXMLBHIT` — expected least efficient of all 14. This is the one cell
   that has ever actually traded (T4M-PROJ); CLAUDE.md's thesis requires it
   to sit at the inefficient end for the strategy's own premise to hold.

This ordering is a prediction, not a target. Deliverable 2/3 will report
whatever the data actually shows, including if `KXMLBHIT` does not turn out
to be the least efficient family — that would be a direct empirical challenge
to CLAUDE.md's stated premise (Deliverable 3's explicit question) and will be
reported as such, not smoothed over.

## 7. What this analysis will not establish (stated in advance, restated in
the final write-up per the task brief)

- **Efficiency is not edge.** A family ranking as "less efficient" by this
  index says nothing about whether this project's specific model has, or
  could have, a calibration edge against it. A thin market can be thin and
  still unbeatable (wrong-shaped signal, no repeatable pattern, adverse
  selection from sharper counterparties who also watch thin markets).
- **This is a measurement of pricing structure, not of the operator
  decision.** It does not recommend expanding into, or holding away from,
  any market family, and does not resolve the open tension recorded in
  CLAUDE.md's Market Efficiency Gradient section.
- **The composite's equal-weighting is a stated assumption, not a derived
  one.** A different, equally defensible weighting could reorder families
  whose ranks are already close; this is exactly what the tie rule (§5)
  exists to surface rather than hide.
- **Sample coverage is uneven and time-bound.** MLB spans 51-54 days deep
  into a single regular season; NFL spans at most 13-18 days across two
  early-season weeks. Neither spans an off-season, a playoff push, or more
  than one season — this is one snapshot in the market's life, not a
  structural constant.
