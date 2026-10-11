# Session handoff — W67.3 GitHub at $0 (2026-10-11)

vision_pillar: operational reliability — keep the MLB pipeline running inside the free GitHub budget
gap_measure: Actions minutes projected to 2026-11-01 vs free 2,000
gap_delta: deploys 0 min/push (was per-push); features run ~9.7 min -> measuring (cold dispatch 38159884120, warm pending). Full projection still needs the other workflows measured.

## Done
- Part A: scripts/ops/vps_deploy.sh + cron line (PR #221), deploy.yml push trigger removed (PR #224). Proofs: docs-only 96s, code push ~4 min, 0 Actions runs.
- Part B: PR #227. VPS cannot call statsapi people/* (406 on the DigitalOcean IP, any headers), so fallback: cache regular-season starters + SP logs (key mlb-2026-regular-season-v2), fetch postseason live. Old-vs-new CSV equal except snapshot_id/ingestion_run_id/feature_run_id/ingested_at.

## Open
- Read dispatch 38159884120 (cold) and dispatch once more (warm); record minutes/run. Mac warm run was 372s, above the 3-min target.
- Project all workflows (tests.yml, post_game_resolve, tss_daily_sync, mlb_games_cache_sync, nhl_goalie_probe) to 11-01.
- Register: VPS IP 406-blocked by statsapi people/*; a skipped t4-mlb restart is never retried (GG numbers to be claimed).
- DECISION_LOG entry not yet appended.

## UPDATE 17:50Z — BLOCKER: Actions minutes/spend exhausted
- Cold dispatch 38159884120 succeeded (17:29:52 -> 17:46:25, 16.5 min; fills v2 cache).
- Warm dispatch 38161115474 failed in 6s, no steps ran. Annotation: "The job was not started because recent account payments have failed or your spending limit needs to be increased."
- Consequence: no GitHub workflow can start. The scheduled mlb_features_sync (10:17 UTC) will not run, so the 11:00 PIPE-05 CSV will be stale. Warm-run timing NOT obtained.
- Options for the operator (no paid service was taken): wait for the monthly reset, or raise the spending limit himself/herself. A VPS-side generator is blocked by the statsapi 406 on people/*.
