# W54.2 — GG-432 merge + VPS proof; MLB postseason shadow arming (GG-453)

**Date:** 2026-10-05 · **Claim:** T-672..T-675, GG-470..GG-474 · **Outcome:** GG-432 DONE and proven; D3 (arming) NOT done, blocked by GG-470.
No ledger, order, position, stake or kelly_fraction was touched. No crontab line installed. No VPS file written (one temp-dir fetch test, deleted).

## D1 — pre-merge checks
- PR #158: head `444b54f7` (matches expected), draft -> ready, CI `test` SUCCESS, MERGEABLE/CLEAN. Diff vs main = 3 files: `.github/workflows/deploy.yml`, `scripts/deploy_restart_policy.py`, `tests/test_deploy_restart_policy.py`.
- Decision logic run on #158's own diff vs main (detached checkout of the PR head): `t4-mlb restart decision: not_needed -- no file imported by t4-mlb changed in this push`. Import closure = 16 modules; neither `deploy.yml` nor the policy script is in it. `pytest tests/test_deploy_restart_policy.py`: 10 passed.
- VPS before merge (2026-10-05T06:56:49Z): HEAD `eb2d1434`; t4-mlb active, ActiveEnter **2026-10-05 01:31:28 UTC**, NRestarts=1; pmbot-web-dashboard ActiveEnter 2026-10-03 01:32:57 UTC, NRestarts=0.

## D2 — merge and proof
- Merged as merge commit `c2acddf4` (Deploy run 37275051112, success, 20s deploy job).
- Job log: `t4-mlb restart decision: not_needed -- no file imported by t4-mlb changed in this push`; `Restarting: pmbot-web-dashboard`.
- VPS after (2026-10-05T06:58:42Z): HEAD `c2acddf4 Merge pull request #158`; **t4-mlb ActiveEnter 01:31:28 UTC, unchanged**; pmbot-web-dashboard ActiveEnter 2026-10-05 06:58:28 UTC (restarted).
- GG-432 -> RESOLVED. Not yet observed: the `skip_live_game` branch in a real deploy (unit-tested only).

## D3 — MLB shadow arming: stopped at the prerequisite check
Read: `deploy/cron_exp037_pregame_shadow.conf` (NFL block), `scripts/run_mlb_pregame_shadow.py`, `scripts/arm_shadow_crons.{sh,py}`.
Findings, all verified on the VPS:
1. `run_mlb_pregame_shadow.py --dry-run` -> `games.parquet missing`. The cache (`exp_output/MLB_GAME/cache_w47/`) is gitignored and exists nowhere we deploy to. (GG-470)
2. The only builder, `fetch_mlb_game_history.py`, uses date-range queries; the VPS gets **HTTP 406** on every range query (2024 and 2026, curl and python), while `?date=` single-day queries return 200 and range queries return 200 locally. The runner's `--refresh` calls the same fetcher and aborts on failure. (GG-470)
3. Consequence: a cron with `--refresh` writes zero rows; without it, rows come from a frozen cache with stale results and probable starters and would pollute the EXP-037 MLB ledgers. Neither is arming.
4. `arm_shadow_crons.py` `dry_command()` and its allowlist regex do not recognise `run_mlb_pregame_shadow.py`; the arm script would abort at step (d). (GG-471)
5. No MLB settle script exists. (GG-472)

Not done: conf edit, push of the conf, `arm_shadow_crons.sh`, per-band manual runs, crontab diff. Crontab untouched (488 non-empty lines before; EXP-037 block still NFL-only).

## D3 (completed 2026-10-05, after operator said "proceed in full with the recommendation")
- Code: PR #162 (@ 2f9ac401, CI 37276909845, deploy 37277514484) per-date refresh (`fetch_day`/`refresh_recent`, retry+backoff, fail-closed, no partial write), `--refresh` TypeError fixed, GG-471 helper fix + tests. PR #163 (@ 33df54ab, CI 37278349178) refresh window starts at last Final game. No t4-mlb restart (deploy policy `not_needed`).
- Seed: `games.parquet` 28,122 rows copied to the VPS (`exp_output/MLB_GAME/cache_w47/`), checksum matched.
- Armed: 3 MLB lines added to the EXP-037 block (T1 `7 */6` with `--refresh`, T2 `12 * * * *`, T3 `3,13,...,53`). Crontab diff = 7 added lines, nothing else changed; backup `/root/crontab.bak.20261005T072628Z`. NFL lines byte-identical.
- Manual run of each band: T2 and T3 exit 0, wrote nothing (no event inside their windows at that hour). **T1 failed closed twice**: `REFRESH FAILED: stats api 406 ... games refresh failed -- refusing to run on stale data`.
- Finding: the VPS 406s are intermittent per-IP throttling, not tied to date or range form (same date flipped 200->406 in minutes). My earlier belief that single-date queries are reliable from the VPS was wrong. My probing may have worsened it.
- **Result: armed, but zero MLB ledger rows exist.** GG-453 stays OPEN.

## D4 — dispositions
- GG-432 RESOLVED. GG-471 RESOLVED (archived). GG-453 OPEN (annotated). GG-470 OPEN HIGH (partial: path + seed done, egress unreliable). GG-472 OPEN (no MLB settle script, out of scope). GG-473 new LOW (arm script fails on macOS bash 3.2 with empty ALLOW array; workaround `--allow <already-allowlisted conf>`).

## Operator decisions needed
1. Statsapi egress for T1: (a) let the 6-hourly cron run a few days and see whether any attempt gets through; (b) refresh `games_current.parquet` locally and sync to the VPS before each T1 window; (c) non-DigitalOcean egress/proxy.
2. Whether to staff GG-472 (MLB settlement) before the postseason ledgers matter.
