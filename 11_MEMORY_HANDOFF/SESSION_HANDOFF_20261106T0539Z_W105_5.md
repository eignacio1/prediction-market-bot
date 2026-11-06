# SESSION_HANDOFF — W105.5 / B-054 — ride/fade router wired to live markets + demo orders

```
vision_pillar: EXECUTION (E1) / BREADTH
gap_measure: E1 (demo order path for ride/fade) ; B1 (decisions logged on live NBA/NHL/NFL markets)
gap_delta: ride/fade decisions logged on live markets 0 -> N per run (fixture night: 3000 markets -> 3000 decisions incl. NO_BET); demo-order path built + tested (RIDE on HELD_OUT/FORWARD_PASSED only); order fills still 0 (nothing installed yet)
pattern_sweep: test_w100_3_installer_markers.py enumerated installers and conf files -> added ride_board; test_box_tasks.py writer allowlist -> added ride_board_install/uninstall; schedule_cancel daemon timer dies with a short-lived process (same pattern in any one-shot runner) -> sweep_cancels added here; no other runner using schedule_cancel was changed (registered below)
surface_delta: +1 cron line after install (deploy/cron.ride_board, registered, pillar EXECUTION); +0 now (not installed)
```

## What was built
- `scripts/run_ride_board.py`: reads `ride_cells.toml` at run time (never edits it), reads families with a cell (plus optional `logs/ride_board/skill.json` for FADE), builds a Situation per market (tier from game start, move_1h from archive tail <=4 MB), calls `router.route`, logs EVERY decision (NO_BET included) to `logs/ride_board/decisions.jsonl`, plus a `run_summary` row with `peak_rss_mb`.
- `src/prediction_market_bot/decision_trees/ride_orders.py`: demo order only if RIDE + cell HELD_OUT/FORWARD_PASSED, then in order: demo host, kill switch (global + band `ride_board`), exposure gate for RIDE_BOARD, per-event cap ($500, `_HARD_LIMITS`), daily breaker, kelly 0 flat ADR-0050 stake. First failure is the logged reason. IN_SAMPLE cells never reach it (router returns NO_BET). FADE/MOMENTUM routes carry no cell status, so they are paper rows only.
- NO side goes through unchanged `submit_order` with the YES-frame mid (NO priced 1 - mid); test asserts the price. Data epoch GG-1771/GG-1784 applies (pre 2026-11-06T01:03:42Z NO fills mirror-priced).
- `deploy/cron.ride_board` (ONE line, `9,29,49 17-23,0-2 * * *`, flock on `/tmp/ride_board.lock`, SKIP_LOCKED to `logs/t3_skips.jsonl`), `scripts/ride_board_cron_install.py`, `box_tasks` entries `ride_board_install|readback|uninstall`, RUNTIME_REGISTRY entry (reviewed), RUNTIME_MAP re-rendered.
- Cancel hygiene: the runner is short-lived so the 60s daemon cancel timer would die with it. `sweep_cancels` sweeps overdue cancels at start and waits out the delay + sweeps before exit when orders were placed.

## Things the operator should know
1. **Outside listed OWNS:** one line in `c4_risk_engine/exposure_gate.py` (BOOKS entry `RIDE_BOARD`, advisory, band `ride_board`) - the gate refuses an unmapped band. Existing gate tests pass. Also `tests/test_box_tasks.py` and `tests/test_w100_3_installer_markers.py` allowlists.
2. **Daily breaker is a proxy:** RIDE_BOARD has no ledger, so the breaker compares stake deployed today to `MAX_DAILY_LOSS_PCT * $1000` (same convention as SHADOW GG-1175).
3. **Real table has no live ride cells today:** only `KXNFLTOTAL` IN_SAMPLE (105.4 had not merged cells). Until 105.4 lands rideable cells, the runner logs decisions and orders nothing. New cells are picked up on the next run with no code change.
4. **Memory:** fixture of 3000 markets, peak RSS 74.1 MB on macOS (Python 3.9, no pandas/model). NOT yet measured on the box, and NOT yet compared with the smallest shadow runner there; that comparison is owed (box has 961 MB). Do it from `ride_board_readback` after the first run (`run_summary.peak_rss_mb` is logged every run).
5. **Demo dry run - PARTIAL:** with the local `.env` credentials and `BOT_ENV=paper`, `demo_host_ok()` was True, the real demo order path ran end-to-end (HELD_OUT cell -> price_yes 0.355 -> NO order, flat $1.00 stake, kelly 0) and the demo API returned `HTTP 401 authentication_error` - the local key is not a valid demo key. No order was placed, so nothing to cancel. The real order + cancel needs the box credentials; I did not run orders on the box without the operator's say-so. Ask: approve one dry-run order+cancel on the box, or accept the first live cron run as the proof.
6. Sweep note (registered, not fixed): other short-lived runners that call `schedule_cancel` have the same dead-timer exposure; only this runner was changed.

## For the operator - named approval needed
**`ride_board_install`** (box task, adds ONE cron line with crontab backup + readback + first-run exemption, surface +1). NOT run. Suggested order: merge -> approve `ride_board_install` -> `ride_board_readback` after the first game-window run.

## Verification
- 39 new/updated tests in `tests/test_w105_5_ride_board.py` (HELD_OUT fires one demo order with NO price; IN_SAMPLE logs only; kill switch, exposure gate, cap, daily breaker, production host each block; `--no-orders`; sweep) and `tests/test_w105_5_ride_board_install.py`; broader `-k registry/exposure/box_tasks/cron/ride/deploy` run: 387 passed, 1 skipped; installer-marker and picks-sheet tests pass with the new installer.

## CLOSE-OUT NOTE (TRUNCATED AT SCOPE, not budget)
Main already had a parallel W105.5/B-054 implementation (#442, fa0643c: same filenames, orders OFF by default, 5-min cron). This branch conflicts on 7 files and was NOT merged; PR #445 closed as superseded. Branch kept for a possible port of what #442 lacks: `sweep_cancels` (cancel timer dies with short-lived process), `RIDE_BOARD` exposure_gate BOOKS entry, install tests, registry entry. Not verified whether #442 already covers these. Dry run: demo API HTTP 401 with local creds; no order placed. `ride_board_install` NOT run.
one-thing-pending: operator picks drop / port-delta / replace for this branch.
