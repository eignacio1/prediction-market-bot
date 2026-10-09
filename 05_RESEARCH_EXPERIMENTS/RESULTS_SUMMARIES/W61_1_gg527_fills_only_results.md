# W61.1 - GG-527 built: fills-only execution evidence + T4M-PROJ stand-down gate

Status: DONE (one pending item: t4-mlb restart, see Part B). PRs #191 (Part A), #193 (Part B). VPS HEAD c9e231522150a5b108dc411d92c4bb32b75d37cb.

## Part A
- `src/prediction_market_bot/t4_fill_status.py`: classifier (function + CLI), logic lifted from W60.1. Sidecar `logs/t4_mlb_fill_status.jsonl`, append-only, first row wins, never rewrites the ledger.
- Kept current by `build_t4_resolved_ledger.py` (already in the Monday 14:20 cron; it self-loads VENUE_* from .env and skips gracefully). No cron line added or edited.
- Fills-only counting for T4M-PROJ in `run_power_calc.py`, `run_band_monitor.py`, `governance_scan.sh` (via `load_t4_ledger_execution`). All-rows figures print as "calibration only - not execution evidence". Other bands unchanged. Tests: `tests/test_t4_fill_status.py`.
- Dashboards: Live Terminal tiles "T4 P&L - REAL FILLS (n)" and "ALL ROWS (calibration, not execution)"; `/project` books row "Execution evidence (real fills only)" / "Calibration record". Verified on the VPS: `/api/data` carries `t4_execution` and the served page has the new labels. 390px not checked in a real browser (not done).
- VPS run, all closed T4 positions (incl. postseason): 4,220 classified = **166 CONFIRMED_FILLED, 4,054 CONFIRMED_NOT_FILLED, 0 UNVERIFIABLE**. Re-run appended 0 (idempotent). T4M-PROJ resolved: fills n=165, fills P&L -$42.17; all rows n=3,855, P&L -$121.60.
- Deploy decision #191: `not_needed` (no t4-mlb-imported file changed).

## Part B
- Gate `stake_stood_down(ticker)` in `run_t4_mlb_live.py`, after the cycle-log write and before placement: game year >= 2027 and `T4M_PROJ_POST_2026_REENABLE` False -> no stake; one counted warning per ticker. Tests `tests/test_t4_stand_down_gate.py` (2026 stakes, 2027 doesn't, re-enable stakes, one log line, ordering guard).
- Calibration record survives: real VPS cycle-log row (2026-10-09T00:46:24Z): `ts`, `ticker=KXMLBHIT-26OCT081700CLECWS-CLEBROCCHIO4-2`, `game_date=2026-10-08`, `player_id=677587`, `threshold=2`, `p_t4=0.168688`, `mip=0.09`. Outcome join key = ticker (+ game_date, player_id).
- Deploy decision #193: **skip_live_game** (CLE @ CWS in progress). Code is on the VPS; t4-mlb (running since 2026-10-07 06:13Z) is on old code. It picks the gate up at the next deploy that changes a t4-mlb-imported file outside a live game, or `systemctl restart t4-mlb`. Must be live before spring 2027; the post-World-Series registry-flip block should include the restart.

## Not done / handed back
- Denied by the permission classifier ([Sensitive Remote Exec]): a python edit of governance_scan.sh adding `ssh ... cat /opt/prediction-market-bot/logs/t4_mlb_fill_status.jsonl > logs/t4_mlb_fill_status.jsonl` (local mirror of the sidecar). Not retried or bypassed. Effect: a LOCAL governance scan sees no sidecar, so T4M-PROJ counts 0 fills locally; the VPS-side scan/dashboard read it directly. Hand-back: add a Bash permission rule for that ssh cat, or apply the mirror line.
- Registry flip of T4M-PROJ to DARK: after the World Series (stated on GG-527).
- Premise correction: T4 paths are `src/prediction_market_bot/run_t4_mlb_live.py` / `t4_mlb_execution_engine.py`, not the paths in the prompt.
