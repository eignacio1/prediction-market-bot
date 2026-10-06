# W56.1 — MLB cache via GitHub Actions + GG-477 cron stagger (2026-10-06 UTC)

Claim T-692..T-694. Branch session/20261005T234924Z-w56-mlb-ops. No order/position/fill/stake/kelly change; no ledger writes.

## D1 — workflow (GG-482)
`.github/workflows/mlb_games_cache_sync.yml`, PR #165 (CI `test` green, merged de7f60a). Schedule 12:43 and 00:43 UTC + workflow_dispatch.
Steps mirror `scripts/sync_mlb_games_cache.sh`: seed games.parquet from VPS, `fetch_mlb_game_history.py --recent`, scp to `*.tmp`, atomic `mv`. `set -euo pipefail` everywhere; mv is last, so any failure leaves the VPS cache untouched.
Deploy job: **t4-mlb restart decision: not_needed** (no t4-mlb-imported file changed).

## D2 — proof
Dispatch run 37391603147: success. statsapi **accepted the GitHub runner** (no 406): `refreshed 2026-10-03..2026-10-09: 18 games fetched, 2480 season rows`.
VPS meta stamp: `{"refreshed_at":"2026-10-06T00:00:44Z","last_final":"2026-10-04","rows":2480}` == the run's time.
MLB T1 shadow, cron's exact command (`run_mlb_pregame_shadow.py --bands T1`, run_id 20261006T000113Z, exit 0):
written MLB_MONEYLINE:T1=10, MLB_RUN_LINE:T1=12, MLB_GAME_TOTAL:T1=21, MLB_TEAM_TOTAL:T1=28 (71 rows). Skipped outside_band_windows: 4/13/16/28.
Residual: seeding uses VPS games.parquet; refresh_recent fails closed if its last Final is >21d behind today (re-seed needed). Not hit now; watch late October.

## D3 — stagger applied
Before: swap 2G (223M used), RAM 961M (482 used, 479 available). Dry-run matched RULES counts exactly (2/2/1/2/2). Backup: `/root/crontab.bak.20261006T000156Z` (dry-run also left `...000148Z`).
APPLY=1 installed. Diff = 9 lines in 4 hunks (79-80, 97-98, 496-499, 507). Check: stripping the first (minute) field from both files yields zero diff; only minute fields changed.
Restore: `crontab /root/crontab.bak.20261006T000156Z`.

## D4 — persisted
PR #166 (CI green, merged; t4-mlb restart decision not_needed): same minutes in `deploy/cron.conf` (T3 pretip lines, the source of the VPS lines — not named in the block but required, otherwise a re-arm would revert them), `deploy/cron.nhl_shadow`, `deploy/cron_exp037_pregame_shadow.conf`. Not re-armed.

## D5 — status
- GG-482: **RESOLVED** (D2 evidence above). First scheduled run to confirm: 12:43 UTC 2026-10-06.
- GG-477: stagger applied; **stays OPEN** until a clean 01:30 UTC window (2026-10-06 01:30 UTC onward) — next wave reads it (t4-mlb NRestarts, `journalctl -k | grep -i oom` around 01:30).
