# EXP-NHLINPLAY-001 — NHL in-play arithmetic pricer (T4NHL-ARITH), shadow only

**Last reviewed:** 2026-11-25 (W129.7). **Committed before any forward row exists.** No order, no stake, `kelly_fraction` 0.
**Data rule:** NHL domains carry Content-Signal ai-train=no. The feed is fetched; nothing is trained on it. The pricer's state
multipliers were fitted on 2021-22..2024-25 only (W103.3) and are frozen here.

**What is built.** `nhl_live.py` (feed, staleness, write-recency) → `nhl_inplay.py` (Skellam + state multipliers, exact OT/SO abstain)
→ `scripts/nhl_inplay_shadow.py` (one row per open Kalshi game / spread / total market of a live game). Cells: NHL_MONEYLINE,
NHL_PUCK_LINE, NHL_GAME_TOTAL × T4NHL-ARITH. T4NHL-FLOW is not built (needs a book-flow feed).

## Test 1 — replay correctness (descriptive, run in this PR)
- Population: every 2026-27 regular-season game with play-by-play in the event store on 2026-11-25 (231 games). 7 game-clock checkpoints
  per game (P1 10m in / end, P2 10m in / end, P3 10m / 5m / 2m left).
- Measure: Brier of the in-play price vs the outcome, and vs the pregame-only price (same lambdas, no state), game-clustered bootstrap.
- This checks that the pricer uses the state correctly. It is **not** a market comparison: the event store has game-clock time only and
  the price archive samples every ~20 minutes (W103.3), so a same-timestamp Kalshi comparison is not possible on a replay.

## Test 2 — forward, vs the Kalshi in-play price (judged later; no look before n)
- Population: shadow rows written by the installed runner from its first row; rows before the install are not counted.
- Unit: one (market, game, pass). Clustered by game. Priceable rows only (REG periods, strength known, fresh state, two-sided book).
- Measure per cell: Brier(in-play model) − Brier(Kalshi mid at the quote's fetch time), paired, game-clustered bootstrap CI;
  gross, round-trip cost (half-spread both sides) and net side by side.
- Judged n: **≥ 40 games and ≥ 300 priceable rows per cell** before any read. Modal pre-registered outcome: the model does not beat the
  in-play mid net of costs (the market reprices on goals faster than a 2-minute poll); the result routes the arm (ride / no bet in
  these leaves), it closes nothing. A null is "hypothesis closed (EXP-NHLINPLAY-001, parked for R&D)".
- Feed latency: request latency (p50/p90/max) from every fetch; state-to-quote age per row; market-move lag from `nhl_live_probe`
  (goal seen by feed vs first Kalshi mid move of ≥ 2¢), reported with the number of goals observed.

## Known limits (stated, not hidden)
Score effects are not modelled; regulation ties and totals are under-priced (W103.3: 17-19% model vs 24.8% actual ties); the power-play
window ignores the penalty timer; the pbp clock is an event-refreshed snapshot, so `minutes_left_reg` can lag the true clock; OT / SO
abstain; pre-game lambdas in the replay are the walk-forward rating proxy, in the live runner the NHL pre-game engine's.
