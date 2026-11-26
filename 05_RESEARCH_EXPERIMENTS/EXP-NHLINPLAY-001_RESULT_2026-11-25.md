# EXP-NHLINPLAY-001 — Result 1 (replay correctness + feed latency), W129.7, 2026-11-25

**Last reviewed:** 2026-11-25. Pre-registration: `EXP-NHLINPLAY-001_PREREGISTRATION_2026-11-25.md`. Shadow only, no orders, Kelly 0.
**This is NOT a market comparison.** Test 2 (vs the Kalshi in-play price) needs forward rows; none exist until `nhl_inplay_install` is approved.

## Test 1 — replay, 231 games of 2026-27, 7 checkpoints (1,617 rows per cell, game-clustered bootstrap)
| Cell | In-play Brier | Pregame-only Brier | Delta | 95% CI on delta |
|---|---|---|---|---|
| NHL_GAME_TOTAL (over 5.5) | 0.1302 | 0.2399 | -0.1096 | [-0.1279, -0.0906] |
| NHL_MONEYLINE (home win) | 0.1338 | 0.2362 | -0.1024 | [-0.1208, -0.0833] |
| NHL_PUCK_LINE (home by 2+) | 0.1347 | 0.2095 | -0.0748 | [-0.0955, -0.0548] |

Reading: the pricer uses the live state (score, time, strength, empty net) correctly: it beats the same lambdas with no state. That is a
correctness check, expected to be large late in games. Lambdas here are the walk-forward rating proxy, not the NHL engine's. Gross / round
cost / net are not applicable (no market price in a replay).

## Why no Kalshi comparison on the replay
The event store has game-clock time only; the price archive samples every ~20 minutes (W103.3). A same-timestamp comparison is not possible.
It comes from forward capture (Test 2).

## Feed latency — measured on 2026-11-25 evening, 8 live games, 880 fetches (read-only probe, `scripts/nhl_live_probe.py`)
- Request latency: p50 118 ms, p90 163 ms, mean 134 ms, max 3,096 ms. Staleness verdicts: 880 ok, 0 stale / frozen / regressed.
- The pbp clock is a snapshot: it advanced between consecutive 10 s samples in only 198 of 439 while-running pairs (45%). So
  `minutes_left_reg` can lag the true clock by tens of seconds; an extrapolation fix is a registered follow-up, not built.
- Feed vs market move: 2 goals seen in the window. One: the feed showed the goal, the Kalshi mid moved ≥ 2¢ **70 s later** (resolution ~10 s).
  Other: no ≥ 2¢ move inside the window. n = 2 goals, one with a move: this is an observation, not an estimate. It does not show the feed is
  faster than the market in general; it shows the feed was not slower in the one case measured. Test 2 collects the real distribution.

## Limits
Score effects unmodelled; ties and totals under-priced (W103.3); power-play window ignores the penalty timer; OT / SO abstain; FLOW not built.
No verdict on any arm. Nothing closed.
