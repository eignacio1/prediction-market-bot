# W94.3 Part C: what a fill costs (EXECUTION, E3)

Code: `12_EXPLORATORY/fill_markout/fill_markout.py` (PR #370, read-only). Raw numbers: `raw_W94_3C.json`. Data: shadow-book collector `markouts.jsonl` (21,744 fills, epoch 2026-10-21T04:30Z, NBA/NFL/NHL only), `demo_fill_policy.jsonl` shadow_order events, PRICE_ARCHIVE prices+depth 2026-10-11..10-28 (334,213 consecutive-snapshot pairs, 171 events). MLB T1/T4 fill numbers are cited from W63.3 (`RESULTS_SUMMARIES/W63_3_distance_generator_fill_markouts_results.md`); the collector has no MLB rows. All intervals are game/event-clustered bootstrap (b=2000/1000, seed 20261002). Markout = held-side mid later minus price paid (positive = market moved toward the order).

## Known-answer test (passes)
Simulated book, jump ±4c, half-spread 1c, informed share 0.5. Maker markout −0.00996 (theory h − δ·π/(π+u) = −0.0100, SE 0.00008); uninformed taker drift +0.0001 (SE 0.00009), taker markout −0.0099 (= −h). Applies when flow is Glosten-Milgrom style; a real book also has stale quotes and trigger-conditioned entries, which this does not model.

## Task 1: markout after a resting fill (shadow books, h1/h5/h30 = 1/5/30 min)
| sport · arm | h1 | h5 | h30 |
|---|---|---|---|
| NBA control (rests) | −0.005 [−0.015,+0.006] n=7699/68g | +0.037 [+0.015,+0.056] | +0.038 [+0.015,+0.061] |
| NBA treatment (cancel 60s) | −0.010 [−0.012,−0.008] | −0.013 [−0.030,−0.004] | −0.002 [−0.007,+0.005] |
| NFL control | −0.001 [−0.011,+0.013] n=2021/15g | +0.018 [−0.022,+0.059] | +0.020 [−0.007,+0.053] |
| NFL treatment | −0.0055 [−0.0056,−0.0054] | −0.0054 | −0.0056 |
| NHL control | −0.009 [−0.026,+0.009] n=442/47g | **−0.107 [−0.176,−0.043]** n=203/39g | **−0.115 [−0.194,−0.046]** n=134/30g |
| NHL treatment | −0.008 [−0.010,−0.007] | −0.010 | −0.011 |

Reading: (1) NBA and NFL resting fills show **no** adverse markout; the positive h5/h30 is partly survivorship (h5/h30 exist only where a two-sided candle exists, n shrinks 7699→1917) and is not a claim of positive edge. (2) **NHL resting fills show a large adverse markout, −11c at 5-30 min**, in line with MLB W63.3 (T1 −0.09/−0.12, T4 −0.17, all CIs excluding 0). (3) Treatment fills (quick, cancel-after-60s) sit at about −0.5 to −1c, i.e. they are takers paying the spread, with no further drift. (4) Fill latency joined for only a minority of rows (10,025 of 21,744 "unknown": order not in the retained policy log), so the latency table is thin: >10m fills n=4,132 (h30 +0.051), 60s-10m n=59 (h30 −0.21 [−0.49,−0.00], 9 games), ≤60s n=29. W63.3's "fills >60s are worse" is directionally the same but not established here. No never-filled markouts exist for the shadow books, so filled-vs-never-filled can only be compared on settlement (W63.3), not on markout.

## Task 2: a taker at the quote (YES at ask, NO at 1−bid), from consecutive snapshots 2-30 min apart
| cut | still there at next snapshot | immediate-take markout | = spread cost | + mid drift |
|---|---|---|---|---|
| all (n=668k takes, 171 events) | 0.917 [0.908,0.926] | −0.0206 [−0.0236,−0.0182] | −0.0206 | −0.0000 |
| MLB YES / NO | 0.872 / 0.826 | −0.024 / −0.019 | −0.021 | −0.003 / +0.003 |
| NBA YES / NO | 0.883 / 0.870 | −0.021 / −0.019 | −0.020 | ±0.001 |
| NFL YES / NO | 0.937 / 0.926 | −0.019 / −0.018 | −0.019 | ±0.0003 |
| NHL YES / NO | 0.960 / 0.939 | −0.059 / −0.061 | −0.060 | ±0.001 |
| price ≥90c | 0.923 | −0.048 | −0.047 | −0.001 |
| price ≤10c | 0.908 | −0.012 | −0.014 | +0.002 |

Drift is the part that is adverse selection; it is within ±0.3c in every sport cut (largest MLB ±0.26c, CI excludes 0 but tiny). The cost of a take is the spread, about 2c (6c in NHL, 4.7c at ≥90c), which EXP-042/043 already pay by construction (entry at ask / 1−bid). The YES and NO drifts sum to zero by construction, so the all-row drift of 0 carries no information; the per-side values do.
Depth (archive depth samples, flat $1 stake): the touch holds the stake in 95.7-98.4% of samples for MLB/NBA/NFL and NHL NO; **NHL YES only 76.9%** (median touch 47 contracts, n=108). Median touch size 47-1198 contracts. Only a $1 stake was tested; larger stakes were not.

## Verdict for the window: is "taker at the quote" safe for EXP-042/043/044/045?
Mostly yes, with three stated limits. A taker entry shows no adverse selection after the fill (drift within ±0.3c), which is exactly the component that makes resting fills lose (MLB −9 to −17c at 1-30 min, NHL −11c, vs the 25-29% win rate of filled orders); the share of the filled-vs-never-filled settlement gap explained by post-fill markout is 22% for T1 (−0.10 of −0.45) and 48% for T4 (−0.17 of −0.35), the rest being selection of stale resting prices, which a taker pricing off the current ask does not carry. It therefore **does not overstate the frozen tests by the maker markout**. What it can overstate: (a) quote persistence is 83-96% at a 2-30 min lag, so up to roughly 4-17% of triggers could face a worse price, and the archive cannot resolve seconds-scale latency (the immediate-take drift here is an upper bound on a sub-minute latency, but the cadence is too coarse to measure it); (b) NHL YES at the touch holds a $1 stake only 77% of the time, so NHL cells should be read with a fill-feasibility haircut up to ~23%; (c) all numbers are unconditional on the cells' triggers (EXP-042 price buckets and the ladder trigger are not replicated), and stake size was not scaled. Net: safe for the verdict-level P&L of the frozen cells as written (spread already charged), not a licence to read demo fill rates off them; a real demo-fill test of a taker entry remains the only EXECUTION evidence (GG-527).

## Stage per factor
Fill-cost factor: aggregated and interpreted (markout, quote persistence, depth); not yet applied (no price-path change made).
