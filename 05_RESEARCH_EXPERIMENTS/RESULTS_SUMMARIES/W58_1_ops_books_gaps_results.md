# W58.1 — Every arm logging, every book truthful, gap log shrinking

Session claim T-704..T-707, GG-493..GG-496. Branch: session/20261007T011626Z-w58-1-ops-books-gaps.

## Part A — MLB player-hits proof (GG-489) — DONE
- A1 GG-489 registered (was claimed by W57.1, never written). RESOLVED with evidence below.
- A2 VPS CSV: 51,982 rows, 661 players, max game_date 2026-10-06, 1.8% blank cells, file time 2026-10-07 00:55:40Z. Last writer: GitHub `MLB Features Sync` (workflow_dispatch run 37552551967, 22m44s). Before: 9,890 rows / 82 players / 2026-09-27.
- A3 T1 by hand (exact cron command): exit 0, passed PIPE-05, 12 players / 33 pairs live, 24 edge_decision rows (T1 cell), 0 bets, 21 C4 rejections. T2: no run due until 19:30Z (6 evaluated on 10-05; 0 on 10-06 while features were stale). T3 cron 01:17Z ran with no contract violation (0 CONFIRM/FADE/NEUTRAL signals).
- A4 PIPE-06pre HALTed 10-05 and 10-06 (no output). Re-run by hand: 29 players, 58 markets, 48 actionable, pregame_mlb_20261007.json written.
- A5 AUTHORIZED (queue line verified on origin/main, commit 1cfaace). VPS `30 22 * * *` line commented out; backup crontab_backup_20261007T011803Z_w58_1.txt; diff = one line commented + one comment line; mirrored in deploy/cron.conf.
- A6 GG-489 RESOLVED.
