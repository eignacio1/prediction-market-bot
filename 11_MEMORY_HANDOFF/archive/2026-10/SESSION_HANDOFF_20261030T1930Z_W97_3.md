# SESSION HANDOFF W97.3 (flex lane) - PARTIAL, parked at token limit - 2026-10-30 ~19:30Z

vision_pillar: PROOF (visibility) + PLUMBING
gap_measure: games with a plain-English pick line on the Visual Dashboard per night
gap_delta: 0 -> builder produced 2978 picks / 152 games on a box dry run (2026-10-30); panel live on dashboard after deploy; nightly cron NOT yet installed, so not yet recurring
surface_delta: +1 cron (picks builder, registered in RUNTIME_REGISTRY.toml, NOT installed). Surface reads RED only for "NOT INSTALLED cron|37 5,22 * * *|scripts/build_picks_sheet.py"
pattern_sweep: n/a (no defect fixed); memory fix applied to tail_rows (streaming) in the new module only
Branch: session/20261030T184505Z-w97-3-picks-sheet. Claim T-1580..1582 / GG-1580..1582.

## Done
- PR #389 merged (CI pass): picks_sheet.py, scripts/build_picks_sheet.py, dashboard panel "Tonight's picks", tests/test_picks_sheet.py, deploy/cron.picks_sheet (`37 5,22 * * *`), registry entry.
- PR #392 merged as 5145feb7 (CI pass): builder streams ledgers. First box dry run peaked at 141 MB RSS (21 s) while the box has ~55-120 MB free and past OOM kills of ~130-160 MB python (dmesg). Re-measure after #392 is NOT done.
- Box deploy of #392 (cc23cd13) was in progress at 19:13Z; t4-mlb decision for #389 deploy: not_needed.

## NOT done (next session, in order)
1. Confirm box deploy of #392 finished (`logs/vps_deploy.log`, record t4-mlb decision). Re-run `nice -n 10 /usr/bin/time -v venv/bin/python scripts/build_picks_sheet.py`; peak RSS must be well under free memory (target < 80 MB); if not, lower `--tail-bytes` in the cron line and re-test.
2. Install `deploy/cron.picks_sheet` as a new BEGIN/END block (crontab backup first, no edit of existing lines) only if `scripts/runtime_registry.py live` is otherwise GREEN. Read panel back on the dashboard after the 22:37Z or 05:37Z run.
3. Register GG-1580: pick "reasons" unavailable because ledger rows hold only feature_row_sha256, not features; fix is a separate permissioned change to runner rows.
4. Part B: MLB arms read IDLE-with-reason when MLB has no games (silent_arms.py), keep the GG-163 alarm for regular-season days with games and no rows; explain T1 MLB SemanticFloorViolation (no-player-markets day vs defect -> GG). Tests via PR.
5. Part C: peak RSS table per runner + dashboard across an NBA night; overlap check; stagger/cap with a test, never by stopping an arm. Box top RSS now: nba_pregame_shadow T2 119 MB, mlb_pregame_shadow T2 98 MB, web_dashboard 77 MB, nba_engine.live 63 MB; swap 1.5 of 2 GB used.
6. Write 12_EXPLORATORY/picks_sheet_w97/results_W97_3.md.

## Ticket states (ROLLING_BACKLOG not edited)
B-026: PARTIAL (built, merged, cron not installed, no night read back). B-006: NOT STARTED. B-007: NOT STARTED (one data point: builder 141 MB before fix).
Operator decisions: none.
