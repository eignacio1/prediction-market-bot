# SESSION HANDOFF — W109.5 FLEX (dashboard memory, MLB Features Sync off-season, surface budget)

vision_pillar: PLUMBING
gap_measure: PLUMBING (dashboard build memory; MLB Features Sync red days; surface-budget reds)
gap_delta: see MEASURE MOVED below
surface_delta: 0 new live components. One install task PREPARED (`dashboard_memmax_install`), not run.
pattern_sweep: Defect = "contract staleness HALT fires when the sport has no games." Other consumers of MLB_FEATURE_CSV_CONTRACT: `run_mlb_pregame.py:299` and `run_mlb_paper_trade.py:589` (box cron pipelines). Neither has an off-season skip. Not changed: the contract is not loosened on game days, and those pipelines would HALT off-season by design, which is a visible stop with no orders. Registered as a note here, not fixed. `.github/workflows/mlb_features_sync.yml` was the only CI consumer and is fixed (#462). Other instance of "silent partial failure of a rebuild": dashboard `_store()` now logs and retries (#464).

## Merged
- **#462 Part B (green CI):** `scripts/verify_mlb_feature_csv.py` `--skip-off-season`. Skips only when `staleness_halt` is the sole HALT and the MLB schedule API shows 0 games in `today - freshness_halt_days .. today`. Schedule fetch failure or any game keeps the fail-closed gate. Skip writes `skip=true` plus a reason to the step summary; SSH and push steps are conditioned on it. 4 new tests. Root cause: CSV 13 days stale vs the 7-day halt since the season ended; daily runs red 2026-11-05..11-10.
- **#464 Part A (green CI):** supersedes #458 and #461. Kept: streamed `/api/data` encode (iterencode into BytesIO), failed-rebuild log with last-good page kept and 15 s retry, fallback pages. Dropped: #458's HEAD-keyed cache and footer. #459's `_expire_on_new_head` untouched. #461 was closed on conflict (a force-push was DENIED by the classifier and not retried; a new branch and PR were used).
- **#468 (green CI):** prepares `dashboard_memmax_install` (see below). Prepared only.

## MEASURE MOVED (PLUMBING)
- **Dashboard build peak (box, fresh subprocess, post-change; `dashboard_build_peak_read`):** import baseline 113,252 kB; visual 170,800 kB; project 135,352 kB; data 260,684 kB. **No pre-change box reading exists, so there is no box before → after.** Only a local synthetic 51 MB encode: ~142 MB old vs ~51 MB new (not a box figure).
- **Cgroup (`dashboard_cgroup_read`):** MemoryMax 128 MiB; memory.events `max` 5,082; oom_kill 0; peak = limit. The `/api/data` build (260 MB) exceeds the cap, so the streaming change alone does not clear it. That is why MemoryMax must change.
- **MLB Features Sync red days → 0:** cannot be confirmed yet. The next scheduled run is 10:17 UTC and has not happened. Expected 0. Not claimed.
- **Budget reds:** `budget_read` (2026-11-11T01:13:40Z) GREEN: 93 live components, 0 unreviewed, 0 stale/down/behind, healthcheck HEALTHY with 0 faults and 0 warnings. Reds now: 0. The N before was not measured by this block.

## Deploy / t4-mlb decision (`deploy_truth_read`, 2026-11-11T01:29:49Z)
Box HEAD `123ff62d` = origin/main (#469). t4-mlb runs box HEAD code (started 01:23:45Z), dashboard runs box HEAD code (started 01:28:34Z). #462, #464 and #468 touch only the dashboard, a GitHub workflow and a box-task allowlist. **Decision: no t4-mlb restart needed.**

## Remaining reds, with owners (Part C)
- Surface budget: none (GREEN). Healthcheck: none.
- Dashboard 128M cgroup cap hit repeatedly (`max` 5,082): owner = the operator's approval of `dashboard_memmax_install`.
- MLB Features Sync: expected clean skip at next run; owner = next window to read the 11-11 10:17 UTC run.
- Not budget reds, for the record: 253 open GGs in the cached scan, 6 with UNSPECIFIED severity (governance-gap agent).

## Waiting on the operator (install tasks by name, NOT run by this block)
1. **`dashboard_memmax_install`** — new. Drop-in `/etc/systemd/system/pmbot-web-dashboard.service.d/w109-5-memory.conf` with `MemoryMax=384M`, daemon-reload, restarts only the dashboard unit, prints a readback. Uninstall = `python3 scripts/dashboard_memmax_install.py uninstall`. Approve by name in chat.
2. **`ride_board_install`** and the 22-series prop archive via **`archive_cron_install`** — the queue shows these installed on 11-10 16:27 PT (operator-approved) and the budget is GREEN since 00:45Z, so nothing is waiting on them now. Neither was run by this block.

## Honest notes
- Mid-session, `git checkout <branch> -- .` wiped my first Part B edits. Reapplied, tests re-run, carried-over Part A files removed from that branch.
- The full session-start protocol was not run in full; only `session_guard.sh`.
- #468 hit a merge conflict with main (box_tasks allowlist). Resolved by keeping both sides; no force-push.

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
