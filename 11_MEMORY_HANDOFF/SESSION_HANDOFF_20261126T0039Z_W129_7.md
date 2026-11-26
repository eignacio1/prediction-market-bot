# SESSION HANDOFF — W129.7 NHL in-play feed + shadow cells (Sonnet)
**Last reviewed:** 2026-11-25. Branch `w129-7-nhl-inplay` (worktree). Shadow only, no orders, `kelly_fraction` 0.

## Built
- C1 feed `c1_signal_ingestion/nhl_live.py` (score, period, clock, strength, empty net, shots, fetch time, request latency; staleness; write-recency).
- C3 pricer `c3_forecasting/nhl_inplay.py` (Skellam + state multipliers; ML / puck line / total; OT/SO abstain).
- Runner `scripts/nhl_inplay_shadow.py` behind `PM_NHL_INPLAY`; read-only `scripts/nhl_live_probe.py` (box task `nhl_live_probe`).
- 3 cells NHL_MONEYLINE / PUCK_LINE / GAME_TOTAL x T4NHL-ARITH promoted SHADOW (EXP-NHLINPLAY-001). T4NHL-FLOW stays NOT_IMPLEMENTED.
- Health: check 12 in `deploy/healthcheck.sh` (live game, no row 10 min = FAIL). Known-answer test on saved game 2026020386.
- Install `scripts/nhl_inplay_install.py` + `deploy/cron.nhl_inplay` + 3 box tasks (install / readback / uninstall): BUILT, NOT RUN.

## Results (05_RESEARCH_EXPERIMENTS/EXP-NHLINPLAY-001_RESULT_2026-11-25.md)
- Replay, 231 games, 7 checkpoints: in-play Brier 0.130 (total) / 0.134 (ML) / 0.135 (PL) vs pregame-only 0.240 / 0.236 / 0.210; delta CIs exclude 0. Correctness check, NOT a market comparison.
- Kalshi comparison on a replay is not possible (game-clock-only store, ~20 min archive). It comes from forward rows after install.
- Feed: 880 fetches, p50 118 ms, p90 163 ms, max 3,096 ms; 0 stale. pbp clock advanced in only 45% of consecutive 10 s samples (snapshot lag).
- Market lag: 2 goals; 1 Kalshi move 70 s after the feed, 1 no move. n 2, observation only.

## operator decisions:
> **PROPOSED - APPROVAL NEEDED: `nhl_inplay_install`.** Say "approve nhl_inplay_install". Budget gate: SURFACE BUDGET GREEN, box HEAD 3f1cf4ac (2026-11-26T00:18Z); re-run by the task. Run before the next NHL slate.

## Required fields
- surface_delta: +1 paused cron component (registry entry), +4 box tasks (probe, install, readback, uninstall); 0 live until approved.
- pattern_sweep: grep src/ scripts/ tests/ deploy/ .claude/ for NHL cell-count assertions; updated 3 tests (registry, shadow total 60->63, NHL shadow 9->12).
- vision_pillar: BREADTH B1 (+3 NHL in-play cells able to log, 0 -> 3, logging starts at install), B3 (T4NHL-ARITH has a logging cell once installed; T4NHL-FLOW none); feed latency measured.
- gap_measure: none opened; clock-snapshot lag is a registered follow-up (extrapolate `minutes_left_reg`).
- directive_conflicts: none (D-11 in-play arms PARTIAL, moved).

## Not done / next
- CLAUDE.md Right-now block still says 60 shadow: regenerate at wave close (`scripts/claude_md_now.py --write`); the window owns it.
- Pre-game lambdas in the live runner come from the NHL pre-game engine; 129.1 owns `nhl_engine/` depth files, untouched here.
- Test 2 judged at >= 40 games and >= 300 rows per cell; modal outcome: model does not beat the in-play mid net of costs.
