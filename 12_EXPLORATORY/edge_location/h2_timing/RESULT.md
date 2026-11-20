# H2 timing — result (W123.2, 2026-11-20)

**Outcome: NOT SUPPORTED** on the pre-registered rule (HYPOTHESIS.md §3 H2). Hypothesis closed (H-EDGE-2, parked for R&D) — a routing
result: our model-minus-price signal does not predict the drift to the close at 24 h or 6 h, and the drift it would have to
capture is 12-24× smaller than the round cost. Nothing else closes; the arms stay logging.

Technique: game-clustered bootstrap (2,000 resamples, 90% percentile interval) over OLS of drift on signal, fit on the first 2/3
of games by start date, slope judged on the last 1/3. Definitions frozen in OPERATIONALIZATION.md (88b5a70) before any result was read.
Code `h2_timing.py`, known-answer tests `tests/test_h2_timing.py` (planted slope recovered and covered; null spans zero).
Numbers: `h2_result.json`, `part_a_clv.csv`. Re-run: `python3 h2_timing.py --orders … --shadow … --archive … --out …`.

**Data epoch:** all 2,176 arm orders are post-epoch (the log starts 2026-11-12; NO-side mirror pricing ended 2026-11-06T01:03:42Z).
No pre-epoch rows are used, none are mixed. Shadow rows are NBA and NFL from 2026-11-05; NHL has no shadow ledger, so NHL is in Part A only.

## Part A — closing-line value of arm orders (per contract, order's own side; close − entry; all orders, filled or not)

1,760 of 2,176 orders scored (393 games not yet started, 22 no start time, 1 no close snapshot). 60 games.

| Arm | all | <1 h | 1-6 h | 6-24 h | 24-48 h |
|---|---|---|---|---|---|
| ALL | +0.86¢ [+0.48, +1.27] n1760 | +0.02¢ [−0.49, +0.48] | +1.25¢ [+0.80, +1.68] | +0.73¢ [+0.29, +1.18] | +4.49¢ [+1.12, +7.25] n82 |
| RIDE | +1.43¢ [+0.84, +2.33] n534 | +0.86¢ | +0.99¢ | +0.92¢ | +5.78¢ (n54, 4 games) |
| FADE | +0.75¢ [+0.45, +0.97] n467 | +0.74¢ | +1.10¢ | +0.48¢ [−0.08, +0.88] | n5 |
| MODEL_FADE | +0.19¢ [−0.68, +1.30] n363 | +1.20¢ | −1.43¢ (n29) | +0.02¢ [−1.14, +1.45] | +2.07¢ (n23) |
| MOMENTUM | +0.86¢ [−0.31, +1.93] n396 | **−1.75¢** [−3.50, −0.33] | +2.09¢ [+1.22, +2.81] | +2.83¢ [+0.60, +5.44] | none |

Full intervals per cell: `part_a_clv.csv`. Reading: orders drift modestly our way on average (+0.86¢), but the mean Kalshi taker fee on
these entries alone is 1.08¢ (0.07·p·(1−p), n 2,176), before any spread. CLV is gross; it does not clear one fee, let alone a round trip.
The 24-48 h cell looks large but sits on 14 games (RIDE: 4 games); treat as unresolved. MOMENTUM <1 h is the one cell that is negative with an interval
off zero. Fill status is not conditioned on here; resting orders are adversely selected per D6, so CLV on all orders overstates fills.

## Part B — is the drift predictable? (drift = close mid − early mid; signal = model p − early mid)

| Horizon | rows / games (test 1/3) | b on held-out third [90%] | train b [90%] | implied CLV of trading the sign (gross) | round cost | break-even b |
|---|---|---|---|---|---|---|
| 24 h | 2,745 / 89 (530 / 30) | **−0.063** [−0.239, +0.035] | −0.038 [−0.101, +0.016] | −0.61¢ [−2.11, +0.26] | 4.31¢ | 0.80 |
| 6 h | 12,591 / 107 (4,611 / 36) | **+0.017** [−0.024, +0.056] | −0.044 [−0.085, −0.005] | +0.06¢ [−0.26, +0.37] | 3.46¢ | 0.54 |

- The H2 rule needs b > 0 with an interval excluding zero **and** implied CLV above one round cost. Neither horizon has an interval that
  excludes zero; the 24 h point estimate is negative; the 6 h train slope was significantly negative and flipped sign out of sample.
- Both upper bounds (0.035, 0.056) are far below the slope that would pay (0.54-0.80), so this is a firm null on the question asked, not an underpowered one.
  No n-needed is stated for that reason: no plausible n makes a slope under 0.06 pay a 3.5-4.3¢ cost.
- Arm-adjusted (router arm dummies, ref NO_BET): 6 h b +0.018 [−0.022, +0.057]; 24 h not estimable (only NO_BET rows carry a shadow arm at 24 h).
- Per arm at 6 h (descriptive): no arm's interval is above zero; MODEL_FADE is negative [−0.30, −0.10] on 10 games.
- Mean unconditional drift (held out): 24 h −0.19¢ [−1.35, +0.55]; 6 h −0.32¢ [−0.58, −0.07]; small and negative, far below cost.
- Consensus move: not available at 24 h / 6 h for NBA / NFL (closes only), so not regressed. Not zero; absent.

## What the data does not cover (written, not waited for)
- 24 h covers 8 NBA/NFL game families and has 30 held-out games; NBA player-points joins at 6 h only.
- No NHL, no MLB (idle), no pre-epoch window. NHL needs a shadow ledger on the box to enter Part B.
- Shadow rows are nearest-in-time (within 1 h) to the early snapshot; windows 22-26 h and 5-7 h, spread ≤ 0.10.
- Held-out split by date has few games per horizon (30 / 36); an interval this wide would miss a slope of 0.1, which is still 5× below break-even.

## Routing consequence
Entries earlier than the model's current horizon do not buy edge from our signal. The tested split "earlier entry, trade the sign of
model − price" is not added to the T1 tree. Reopen only with a new signal class (H-EDGE-1 attention / H-EDGE-3 news) at 24 h.
