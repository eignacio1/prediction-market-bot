# W86.2 results — what the market's ladders imply, and where they contradict themselves

Measure only. No order, model, ledger, pre-registration, registry cell or stake was touched.
Code: `12_EXPLORATORY/ladder_implied/` (PR #331). Data: shadow-arm jsonl copies (Part A, 2026-10 pre-game
T1/T3 snapshots) and a read-only copy of the non-HIT PRICE_ARCHIVE, 2,032,857 rows, 2,692 ~20-min runs,
2026-08-01..2026-10-23 (Part B). NHL is not covered (shadow files not pulled; no NHL series in the archive).
Intervals are 95% bootstrap resampling GAMES/EVENTS, never snapshots.

## Strike rule (verified, not assumed)
Ticker suffix N on a SPREAD / TOTAL / TEAMTOTAL contract = `floor_strike` N−0.5, `strike_type` greater, pays on
X > N−0.5. Checked on 27 settled tickers (NFL/NBA/MLB) via public Kalshi GET.

## Part A — implied distribution per game

Fit: normal to survival points S(x)=P(X>x) read from ladder mids; NFL margin also a key-number-aware fit.

| Sport / market | games | market σ at T1 [95% CI] | our fixed σ | refit of our model | between-game SD of σ (CV) |
|---|---|---|---|---|---|
| NFL margin | 45 | 12.12 [12.07, 12.22] | 13.2 | 13.20 | 0.21 (1.7%) |
| NFL total | 45 | 13.08 [12.86, 13.13] | 12.8 | 12.76 | 0.38 (2.9%) |
| NBA margin | 28 | 13.81 | none quoted | 14.21 | 0.43 (3.1%) |
| NBA total | 28 | 18.07 [17.96, 18.16] | 18.5 | 18.46 | 0.47 (2.6%) |
| MLB run line | 19 | 3.49 [3.40, 3.58] | 4.4 | 4.38 | 0.14 (4%) |
| MLB total | 19 | 3.62 | none quoted | 4.29 | 0.18 (5%) |

1. **The market also uses nearly one width per sport.** Between-game CV is 2–5%. "One width for every game" is
   not what separates us from the market; a *level* difference is (our fixed σ minus the market: NFL margin +1.1, MLB run line +0.9 runs).
2. **T1→T3** (paired by game): NFL margin −0.045 [−0.086, −0.002], NFL total −0.068 [−0.104, −0.030],
   NBA total −0.38 [−0.63, −0.17], MLB run line +0.057 [0.034, 0.077]; NBA margin and MLB total include 0.
   All small against the level: the width barely moves as the game nears.
3. **Width vs center** (mean |Δ| per strike, decomposed; width share of center+width): NFL margin 14%, NFL total 6%,
   NBA margin 7%, NBA total 23%, MLB total 24%, **MLB run line 61%**. Counterfactual (give our model the market's σ):
   NFL margin 4,066 of 4,442 positive-net rows stay positive; NFL total 3,265 of 3,293; MLB total 458 of 519;
   **MLB run line 121 of 283, and ~100% of summed edge disappears.** So: the NFL/NBA/MLB-total "edges" are CENTER
   disagreements, not width artifacts; the MLB run-line "edges" are a width artifact. (Row-level edges are
   correlated inside a game; counts are not independent evidence.)
4. **NFL key numbers** (45 games, latest T1 snapshot): market mass at exact margin vs the normal fit, ratio
   [CI]: |3| 2.55 [2.47, 2.62]; |7| 1.86 [1.79, 1.93]; |2| 0.72 [0.67, 0.77]; |5| 0.64 [0.59, 0.69]; |4| 0.90
   [0.82, 0.97]; |6| 1.04 [0.96, 1.11]. Key-number-aware fit cuts SSE 72% (0.391→0.111) and gives σ 13.20, our fixed value.
   The best weight for 3 sits on the grid edge (3.0), so the pmf ratios are the primary read, not the weights.
   Our 13.2 is a key-number-inclusive spread; a plain normal fit reads 12.1. Mixing the two conventions
   manufactures a ~1-point "width disagreement".

## Part B — coherence inside one snapshot

Conventions follow EXP-033 (frozen prereg 2026-10-01): fee 0.07·p(1−p) on every leg at the price paid (ADR-0016),
asks as crossing cost, same-run_ts legs only, active markets only, zero-quote guard (bid>0, 0<ask<1).
NFL moneyline treated as non-exhaustive (ties) so only its bids>1 side is tested. Persistence = consecutive runs
of the same legs with net>0 (lower bound on duration; an archive gap ends the streak).

Per 1,000 strike-snapshots (raw → net of fees); CI by event. Size column: net survivors whose displayed size
could be checked / could not (depth is sampled; unknown is never imputed).

| Series · type | raw | net>0 (CI) | net, size known≥1 / unknown | streak median / max (runs) |
|---|---|---|---|---|
| NFL TEAMTOTAL monotonic | 0.449 (100) | 0.404 [0.035, 0.96] (90) | 0 / 90 | 1 / 15 (64 streaks, 95% len 1) |
| NFL SPREAD monotonic | 0.212 (57) | 0.007 (2) | 0 / 2 | 1 / 1 |
| NFL TOTAL monotonic | 0.071 (14) | 0.005 (1) | 0 / 1 | 1 / 1 |
| NFL GAME excl bids>1 | 3.939 (152) | 0 | – | – |
| MLB TEAMTOTAL monotonic | 0.042 (14) | 0.042 [0.015, 0.075] (14) | 0 / 14 | 1 / 2 |
| MLB SPREAD monotonic | 0.039 (6) | 0.013 (2) | 0 / 2 | 1 / 1 |
| MLB SPREAD vs GAME (zero strike) | 0.020 (3) | 0.020 (3) | 0 / 3 | 1 / 1 |
| MLB F5 SPREAD monotonic | 0.092 (8) | 0.080 (7) | 0 / 7 | 1 / 1 |
| MLB F5 TOTAL monotonic | 0.026 (4) | 0.020 (3) | 0 / 3 | 3 / 3 |
| MLB TOTAL monotonic | 0.016 (4) | 0 | – | – |
| MLB GAME excl bids>1 / asks<1 | 4.208 (518) / 7.360 (906) | 0 / 0.008 (1) | 0 / 1 | 1 / 1 |
| MLB F3 excl bids>1 / asks<1 | 4.380 (272) / 11.078 (688) | 0.032 (2) / 0.097 (6) | 0 / 8 | 1–2 |
| MLB F5 excl bids>1 / asks<1 | 4.051 (265) / 3.898 (255) | 0.015 (1) / 0.031 (2) | 0 / 3 | 1 / 1 |
| MLB F7 excl bids>1 / asks<1 | 1.885 (130) / 3.291 (227) | 0.058 (4) / 0.058 (4) | 0 / 8 | 1 / 1 |

- **Same-contract (yes_ask+no_ask<1, yes_bid+no_bid>1): 0 violations — and the test is vacuous on this feed.**
  `no_ask = 1 − yes_bid` holds in every sampled row, so the feed derives NO from the YES book. Not evidence of coherence.
- **Fees erase almost everything.** Exclusive-set raw counts are large (MLB F3 asks<1: 688) and fall to single
  digits after fees; the fee on 3 legs near 1/3 each is ~0.14 per set.
- **The only ladder with a persistent net signal is NFL TEAMTOTAL**: 90 net violations, 64 streaks, longest 15
  runs (≈5 h), 95% last one run. Same cell EXP-033 flagged (111 net of 8,465; placebo 220; Holm p=1.0, NOT
  DISTINGUISHABLE FROM TIMING/COST). This block has no placebo, so it neither confirms nor overturns that verdict;
  the CI on the rate [0.035, 0.96] is wide because few games carry it.
- **After size: 0 of the net survivors have a size we can confirm.** Every one is "unknown". That is a limit of the
  depth sample, not a finding that size is absent. The block cannot say any survivor was tradeable.
- Total net survivors across all types: about 150 of ~2.0M strike-snapshots (~0.07 per 1,000). Nothing here
  contradicts EXP-033's 0 of 24 cells SURVIVE.

## Quant bar (three parts per technique)

| Technique | Known-answer test | Applies / does not apply | Measured on our data |
|---|---|---|---|
| Normal fit to ladder survival points (`fit_normal`) | `test_ladder.py`: recovers planted μ,σ; our model's refit reproduces 13.20/12.76/18.46/4.38 | Applies: ≥4 strikes spanning the 10–90% range of a continuous outcome. Not for discrete small-support outcomes (MLB run line, ~6 strikes) without caution | market σ NFL margin 12.12 [12.07, 12.22], n=45 games |
| Key-number-aware fit (`fit_keynum`) | planted 3/7 mass recovered in test | Applies to NFL margins (3 and 7). Not to totals, or sports without key numbers | |m|=3 ratio 2.55 [2.47, 2.62], n=45; SSE −72% |
| Center / width / residual decomposition (`decompose`) | `test_ladder.py`: pure shift reads as 100% center, pure scale as 100% width | Applies when both are normal on the same strikes. Not when either is multimodal | width share 14% NFL margin … 61% MLB run line, n=19–45 games |
| Monotonic / exclusive / dominance checkers (`coherence.py`) | `test_coherence.py` (6): planted violations found, clean books clean, fee-erased violation shows gross>0 net<0, non-exhaustive NFL set not flagged | Applies to one run_ts of one event, arithmetic only. Not a fill model, no leg-in risk, no timing | NFL TEAMTOTAL net 0.404 per 1,000 [0.035, 0.96], 90 rows over 107 events |
| `sized` | `test_coherence.py`: unknown depth returns None, min across legs | Applies only where a same-run_ts depth sample exists; buy leg uses the `no` side, sell leg the `yes` side (my reading of the Kalshi book, not verified against the venue) | 0 of ~150 net survivors have a known size |

## Caveats that move the reading
- PRICE_ARCHIVE has no start times, so in-play snapshots are mixed in. In-play ladders move fast and could create
  or erase violations. Not separated.
- Part A rows within a game are correlated; NBA is preseason/early season (provisional).
- MLB run-line ladders have ~6 strikes: the fit is thin and the width comparison is least reliable there.
- Depth is sampled (21,746 rows), so size-adjusted counts are mostly unknown by construction.
- Run cadence assumed 20 minutes; durations are lower bounds in runs, not minutes.

## Stage reached per factor (aggregated / interpreted / applied)
- Market-implied width and center per game, 3 sports: **interpreted** (measured against our fixed values, with a
  decomposition). Not applied: nothing here changes a price.
- NFL key-number mass: **interpreted**; the application (price spreads through a key-number pmf) is not built.
- Ladder coherence: **aggregated** (counted); interpretation limited by unknown size.

## Granularity index (five parts)
1. **Split:** sport × market kind × band (T1/T3) × team vs event ladder.
2. **Rank vs history at the same point in a season:** not done; 2026 only (archive from 2026-08-01). Registered as a gap, not faked.
3. **Matchup cross:** not done. Per-game σ is available to cross against matchup features next wave.
4. **Market map:** ladders per sport and family (NFL/MLB spread, total, team total, F3/F5/F7); NBA only in Part A.
5. **Application:** none. Candidate: replace fixed σ with the market's per-sport σ and, for NFL margin, the key-number pmf.

## Helpers recommended for the quant core (next wave)
`parse_ticker`, `survival_points`, `fit_normal`, `fit_keynum`, `decompose`, a tolerant `parse_ts` (Python 3.9 on the
box rejects 5-digit fractional ISO seconds), and the `coherence.py` checkers (`fee`, `monotonic`, `exclusive_set`,
`dominates`, `sized`). They stay in `12_EXPLORATORY/ladder_implied/` until 86.1's `quant/` owner takes them.

## Operator decisions
None.
