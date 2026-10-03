# Session Handoff — 2026-10-03T02:50Z (cloud block 50.1)

<!-- session-meta
task_id: 50.1
tier: STANDARD
timestamp: 2026-10-03T02:50:00Z
one_line_summary: 50.1 (cloud): GG-419 claim-push guard, GG-427 deps, GG-428 network marker, scripts/lib/__pycache__ ignore, queue rotated (Wave 48 archived). On branch claude/peaceful-heisenberg-51g2ee, not on main.
gg_touched: GG-419, GG-427, GG-428 (Status line -> RESOLVED only)
plan_deliverable_moved: no
-->

**Base:** origin/main `7e808933` (my claim on top of 49.x close `2e0f493d`). Step 4 skipped (no VPS from cloud).

## Landed on the session branch (all items 1-5)
1. **GG-419** `scripts/claim_session.sh` refuses if `git rev-list origin/main..HEAD` is non-empty, so the
   `HEAD:main` push can only add the claim commit. New `tests/test_claim_session_head_guard.py` (real git,
   temp bare origin): fails pre-fix, passes post-fix; claim tests 17 passed.
2. **.gitignore** `__pycache__/` after `!scripts/lib/**`; `git check-ignore` confirms caches ignored, new sources not.
3. **GG-427** `pyarrow>=16.1.0`, `nba_api>=1.5.0` — lower bounds from `DEPENDENCY_LOCKS/requirements-base.txt`.
   That lock is stale vs pyproject (sklearn 1.4.2 vs >=1.8), so it is NOT a VPS truth source; VPS versions unverified.
   Fresh venv `pip install -e ".[dev]"` resolved pyarrow 25.0.1 / nba_api 1.11.4; collect-only 3663.
4. **GG-428** `network` marker; `tests/conftest.py` skips unless `PMBOT_NETWORK_TESTS=1`; CI workflow sets it, so
   CI behavior and the GG-179 skip ceiling (18) are unchanged. Full suite: **3620 passed, 43 skipped, 0 failed (6m20s)**.
5. Queue rotated: Wave 48 archived verbatim (ACTIVE_QUEUE_ARCHIVE.md), queue re-verified against 7e808933,
   Fire Now = local Arm+deploy, then GG-400..429 triage. Needs-your-decision rows copied unchanged + status lines.

## New discoveries (registered here only, Hard Rule 11 — no new GGs)
- GG-419/427/428 now `RESOLVED` but still in the live log; per T-420 they should move verbatim to the archive.
- `DEPENDENCY_LOCKS/requirements-*.txt` disagree with pyproject bounds (scikit-learn, scipy); CI installs from them.
- CI must keep `PMBOT_NETWORK_TESTS=1` or the GG-179 skip ceiling trips.

## LOCAL-SESSION CARRY LIST (do not attempt from cloud)
a) `bash scripts/arm_shadow_crons.sh` — will refuse 14 service-reachable files; review each, pass `--allow <path>` per file. Verify first-firing times it prints.
b) Deploy the dashboard NOT LIVE fix; restart `pmbot-web-dashboard` ONLY (standing authorization); re-run `scripts/browser_check_dashboard.py` and `browser_check_tunnel_drop.py` against the RUNNING process; verify `/api/data` `process.sha`. Set `PW_CHROMIUM` if Playwright's bundled Chromium is absent.
c) Needs operator authorization (do not act): `--include-postseason` on the existing T1 MLB cron; detached read-only VPS jobs; EXP-034 run-or-park; ADR-0070 accept/reject; who restarted t4-mlb.
d) Triage of GG-400..GG-429 (30 gaps, severity from source, not investigated).

## Unlanded branches (operator routes; not touched)
session/20261003T000917Z-eyes-and-nhl, session/exp037-nfl-land, session/exp037-nfl-land-rebased-0e,
session/20261002T222218Z-fly-nfl-pregame, and this block's claude/peaceful-heisenberg-51g2ee.
