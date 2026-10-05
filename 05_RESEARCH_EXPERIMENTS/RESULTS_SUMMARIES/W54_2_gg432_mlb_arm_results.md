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

## D4 — dispositions
- GG-432 RESOLVED (proof above). GG-453 stays OPEN (no rows exist; annotated with the blocker). New: GG-470 HIGH, GG-471 MEDIUM, GG-472 MEDIUM.

## Operator decision needed
How should the VPS get MLB game data? (a) add a per-date (`?date=`) refresh path plus a one-time cache seed built locally and copied over; (b) build/refresh locally and sync the parquet; (c) other. After that: a small helper fix (GG-471) and then the arm step as designed.
