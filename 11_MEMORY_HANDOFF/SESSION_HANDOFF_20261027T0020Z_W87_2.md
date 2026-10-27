# SESSION HANDOFF — W87.2 (kill switch on every order path) — PARTIAL

vision_pillar: PLUMBING
gap_measure: GG-1082 / GG-441 (kill-switch coverage of order-capable books)
gap_delta: books feeding the gate 1 (T1 MLB) -> 2 live on box (MLB_T1, SHADOW); T4 MLB pending restart; submit_order now consults gate (LOG-ONLY)
surface_delta: 0 new components (no cron/service added); existing code paths changed

## State
- PR #334 merged as 360881a, CI green (test pass 5m44s; main Test Suite green). Box HEAD 360881ae.
- `GATE_MODE = "log"` (env `EXPOSURE_GATE_MODE`). Would-halts go to `logs/exposure_gate_logonly.jsonl` (file not yet created: no order since deploy).
- **t4-mlb restart decision: `skip_live_game`** (deploy log 2026-10-27T00:13Z; imports changed: exposure_gate, kalshi_client, paper_trader; Brewers @ Rays in progress). t4-mlb still runs pre-merge code (up since 2026-10-23). It must be restarted after games end; until then MLB_T4 has no writer.
- Box state file confirmed: MLB_T1 and SHADOW books present, no breaches.

## Next (undone)
1. Confirm t4-mlb restarted onto new code (next deploy cron tick with no live game, or manual per policy).
2. After one full game day, read `logs/exposure_gate_logonly.jsonl`; every would-halt reason must be explained (esp. `exposure_book_no_writer:*`, `exposure_band_unmapped:*`).
3. Separate reviewed PR flipping `GATE_MODE` to "enforce"; read back on box; only then close GG-1082 and GG-441.

## Assumptions to register (not yet in the gap log)
- SHADOW denominator is a nominal $1000 and open stake only (box reads $85,681 open flat-stake paper volume; not capital; excluded from breach).
- Cancelled shadow orders still count as open stake.
- Kalshi settled-status strings (`settled/finalized/determined/closed`) unverified against live responses.
- `test_web_dashboard_api ...nfl_files_absent` order-dependent flake; local py3.9 lacks tomllib (test_seat_interface/test_tensions).

## pattern_sweep
submit_order/order-placing callers and dispositions:
- PaperTrader.open_position with kill_band: run_paper_trade.py:222 (t1_nba, frozen, reported not summed); run_t4_mlb_live.py:1949 (t4_mlb, feeds after restart); run_mlb_paper_trade.py:483 (t1_mlb, feeds).
- shadow_flat_stake.maybe_place (band shadow): mlb/nba/nhl/pregame shadow runners and nba_player_points_shadow — feed via feed_exposure_gate().
- scripts/w65_2_cancel_canary.py:82: unlabeled band; logs exposure_band_unmapped in log mode, refused in enforce (demo-only canary).
- Other PaperTrader users (kalshi_client=None, no kill_band) place no orders; no feed.
