# EXP-NFLINPLAY-001 — NFL in-play price (ARITH mode) replay, pre-registration

**Last reviewed:** 2026-11-25 (W129.6). Committed BEFORE any scored outcome is read. Shadow / replay only; no order, no stake, kelly 0.

## What is tested
`quant/inplay_nfl.py`: pre-game line updated by game state (score, seconds left, possession x field position via a FIXED
expected-points table, never fitted here). One pooled variance per minute `s2`, fitted on TRAINING games only.

## Population (no earlier test judged it)
- **Fit set:** 2026 regular-season games, ESPN weeks 1-6, status FINAL. Used only to fit `s2` (margin) and `s2_total`.
- **Scored set:** 2026 regular-season games, weeks 7-11, FINAL, with an ESPN pickcenter spread and total. States = every play
  with 0 < seconds-left-in-regulation <= 3600 (overtime plays excluded: the model does not apply). Outcome from the final score.
- **Market set (moneyline only):** 2025 games that have KXNFLGAME 1-minute candles in the local Kalshi archive (Oct 2025-Jan 2026,
  415 of 862 markets). SPREAD / TOTAL / TEAM_TOTAL have no archive candles: reported vs outcome only, and said so.
- Note: one week-11 game (ESPN 401873067) was opened to read the payload SHAPE for the feed fixture. No outcome was scored from it
  before this file; it stays in the scored set.

## Markets and thresholds
Moneyline: P(home wins). Spread: P(margin > M) with M = -spread (home). Game total: P(total > line). Team total: not scored
(no team-total lines in the free feed).

## Measures (reported per cell family)
Rows (states) scored; Brier vs outcome; Brier of the baseline "pre-game probability held constant" on the same rows; Brier vs the Kalshi
mid at the same timestamp (moneyline, market set only); **gross / round cost / net side by side where a price exists** (moneyline market
set only; cost = half the bid-ask spread each way from the candle); game-clustered bootstrap 95% CI (resample games, 2000 draws, seed 20261125).
Latency: on market-set games, seconds from each scoring play's ESPN `wallclock` to the first 1-min candle whose mid has moved >= 3c from the mid at
the wallclock (median, IQR). Live feed lag (fetch minus wallclock) cannot exist for a finished game and is measured only by the live logger.

## Modal outcome (stated before looking)
Model beats the held-constant pregame baseline on Brier (it has the score). Whether it beats the Kalshi in-play mid is NOT expected
(the market already prices score and possession); that is a routing result for the tree (ride / no bet in those leaves), not a stop.

## Closing rule
A look that loses closes only this hypothesis ("hypothesis closed (EXP-NFLINPLAY-001, parked for R&D)"). No cell, market or arm closes.
Replay uses the same code path as the live logger; the pricer, EP table and split above are frozen once this file is committed.

## Addendum 2026-11-25 (after the first scored look; disclosed, not hidden)
The first look fitted `s2` as mean(r^2/tau). Its fit-set value (5.97/min) was ~2.5x the line's own implied value (~2.3/min), because
near-zero-tau states dominate that mean. The estimator was changed to sum(r^2)/sum(tau) (v2) AFTER seeing scored-set Brier. Both
estimators are reported side by side in the result; v2 is the reported one only because v1 is a defect, and the scored set is therefore
no longer untouched for this estimator choice. A fresh, untouched look (weeks 12+) is the clean test. Everything else above is unchanged.
