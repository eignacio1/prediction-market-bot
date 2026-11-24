# W125.1 RESULT - placement as a decision (B-095 / B-113)

**Source:** box task `placement_fill_read`, result `04_EXECUTION/BOX_TASKS/results/20261124T0544Z_placement_fill_read.md` (read 2026-11-24 05:49Z, code at main after #560).
**Label:** DESCRIPTIVE. Where it overlaps H-EXEC-4's frozen forward population (prereg, first look 2026-12-01) it is not a verdict on that test.
**Epochs, never pooled:** pre-epoch YES-only = 0 arm orders (arm orders began 11-12, after the 2026-11-06 epoch). Everything below is post-epoch, all sides.

## Part A - the fill model (3,214 arm orders; 3,211 resolved, 3 pending, 0 fill status unknown, 0 failed lookups)

Every cell below is read with the fee actually charged, 90% intervals clustered by game, partial pooling within an arm only.
**No cell reaches 20 settled-filled games** (best is 11, FADE spread <1h). So `supported` is False everywhere and no rule is licensed.

| Finding | Number | n |
|---|---|---|
| Team totals almost never fill at the resting touch | 5 fills of 538 orders (0.9%), all RIDE | FADE 123, MODEL_FADE 11, MOMENTUM 231, RIDE 173 orders |
| MOMENTUM fills most | spread 1-6h 33%, spread 6-24h 21%, total <1h 42% | 22 / 27 / 10 games |
| FADE fills little | spread <1h 15%, spread 6-24h 9%, total 6-24h 8%, spread 1-6h 4% | 18 / 17 / 22 / 13 games |
| RIDE fills little | spread (hours missing) 14%, total (hours missing) 13%, moneyline 6-24h 1.6% | 12 / 13 / 34 games |
| MODEL_FADE fills little | total 6-24h 0.2% (1 of 509), spread 6-24h 0.8%, spread <1h 14% | 39 / 9 / 20 games |
| Net per filled contract, only cells with an interval off zero | MOMENTUM spread 1-6h +0.132 [+0.007, +0.257] (9 games); MOMENTUM total hours-missing -0.268 [-0.424, -0.112] (3 games) | both below the 20-game bar |
| Markout at +5 / +30 min | every reported mean within 2 cents of zero (largest -0.017) | 1-13 fills per cell |
| Arm pools (net per filled) | FADE +0.179 (tau 0.42), MOMENTUM +0.099 (tau 0.19), MODEL_FADE +0.191, RIDE -0.033 | 5 / 7 / 2 / 2 cells |

Adverse selection (win rate and edge gap, filled vs unfilled) is mixed in sign across cells, with no cell supported. H-EXEC-1 stands as measured on 11-17; this read does not move it.
A hours-to-start bucket of "hours?" holds orders whose start time was missing at submit; it is its own bucket and not folded into any horizon.

## Part B - placement policy per arm (code landed, OFF)

`ARM_PLACEMENT_POLICY=current` (unset or any other value) is today's resting touch. `on` is the W116.2 frozen table. `rules` reads the W119.3 frozen table first (the FADE rest_inside 50/50 assignment keeps its arm until its look), then `config/placement_rules.json`.
That file is **empty on purpose**: a rule needs a cell with at least 20 games and a written measured reason, and no cell has one yet. So every arm keeps `rest_touch`.
Rule the data points toward and cannot yet license: team totals, where the touch fills under 1%, need cross or skip. That is 538 orders across 4 arms, in cells of 2-16 games each.

**Activation proposal (dated 2026-11-24, for the window; demo only, plumbing, nothing is on):** do not set `ARM_PLACEMENT_POLICY=rules` until `placement_rules.json` carries at least one supported cell. Next review is the 12-01 H-EXEC-4 look. Any arm covered by EXP-W119.3 keeps its 50/50 assignment until that look.

## Part C - skip reasons since 11-12, as numbers (125,920 decisions; 122,563 skipped; 3,214 placed)

| Reason | Orders removed |
|---|---|
| no_bet (router chose no bet) | 90,403 |
| unrouted | 11,913 |
| cap binds, stake 0: day | 9,486 |
| hypothesis closed (EXP-W110.5 NFL per-leaf, parked for R&D) | 6,069 |
| cap binds, stake 0: event | 2,452 |
| cap binds: same_game_cluster | 1,119 |
| daily_breaker (legacy label, see below) | 690 |
| mid_gap_above_threshold | 161 |
| cap binds: arm_budget | 152 |
| one_sided_or_crossed_book | 60 |
| cap binds: event + same_game_cluster | 28 |
| side_unavailable_or_disagrees | 16 |
| not_listed_on_demo | 14 |

Caps together removed 13,237 orders (day 9,486, event 2,452, cluster 1,147, arm budget 152). Stake placed per day pins at 50.00 on 11-14, 11-15 and 11-16 (base day cap bound), and is 150.00 on 11-12 (the old borrowed breaker). From 11-18 (raised caps, 2,500 per day) the busiest day is 714 and the cap no longer binds.
`daily_breaker` is no longer emitted by `src/`; the 690 are from the pre-W115.2 path (GG-1935). The arm path reads no real-money constant: its caps come from `c4_risk_engine/arm_sizing.py`.
**One borrower left:** the RIDE board's `ride_orders.py` 500 per event and 150 per day are copies of the real-money values. Orders are OFF by default and absent from `deploy/`, so it starves nothing today. Registered as **GG-2008**.
`unrouted` (11,913) overlaps GG-2007 (router ERROR skips); not re-derived here.
