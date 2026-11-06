# EXPLORATORY - W103.1 Part C: inputs for ADR-0076 s4 limit table. A draft of numbers, NOT the ADR, NOT a limit, NOT a Kelly.

Blanks stay blank. Every number below is from `RESULT.md` (same run, same caveats: day-resampled, flat cadence, 20-56 days, shadow books use a borrowed f-bar, T4M-PROJ spans epochs). Source: `result.json`. NHL/NFL shadow rows are suspect (GG-1775: fill win rate far above price).

| (book, sport) | worst observed day, % of stake | worst game VaR99, per $ staked | per-event $500 cap reads as | 12-mo P(20% kill) at Kelly .01 / .025 / .05 | cap binds on days (K .01) | limit to set |
|---|---|---|---|---|---|---|
| T4M-PROJ, MLB (YES) | -100% | 1.00 (bounded) | a likely worst game, not a remote one | 0.98 / 1.00 / 1.00 | 0% | blank |
| T1, MLB (YES) | too few (14 days) | too few | too few | too few | - | blank |
| T1, MLB (NO, mirror-priced) | -41% | 1.00 | as above | 0.34 / 0.61 / 0.92 | 0% | blank |
| shadow, NBA (YES) | -43% | 0.93 [0.77, 0.98] | $467 | 0.89 / 0.94 / 0.94 | 89% | blank |
| shadow, NHL (YES) | -13% | 0.98 [0.94, 1.39] | $492 | 0.00 / 0.02 / 0.10 | 17% | blank |
| shadow, NFL (YES) | -79% | too few games (47) | too few | 0.02 / 0.51 / 0.70 | 38% | blank |
| shadow, MLB (YES) | too few (4 days) | too few | too few | too few | - | blank |

Largest Kelly with 12-month kill odds at or under 5%: T4M-PROJ MLB: **none found** (even 0.01 gives 0.98); T1 MLB NO: below 0.01; NHL shadow: about 0.025 to 0.05 (0.02 to 0.10, interval to 0.57); NFL shadow: about 0.01 to 0.025 (0.02 to 0.51); NBA shadow: **none found** (cap-driven). Bisection to a finer figure was not run; this table gives the three tested points only.

## Plain-English line for the operator
For the two live-order MLB books, the 20% kill switch gets hit within a year even at the smallest Kelly tested, because of day-to-day swings (and, for YES, a negative average), not because of a rare big loss; a single game can lose its whole stake, so the $500 per-event cap is the likely worst game rather than a remote one. For the shadow books the 60% deployment cap, not Kelly, decides the risk, and NHL and NFL look milder only because their shadow fills show returns too good to trust (GG-1775). Nothing here sets a limit.
