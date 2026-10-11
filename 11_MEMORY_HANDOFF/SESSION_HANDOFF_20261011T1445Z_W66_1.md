# SESSION HANDOFF — W66.1 GitHub at $0 (2026-10-11)

PARTIAL | session/20261011T061317Z-w66-1-github-zero | PR #219 merged (squash 04295a4) | CI: Deploy to VPS success (t4-mlb restart: not_needed) | Part B shipped, Part A blocked on a permission refusal.

MEASURE MOVED: MLB Features Sync wall-clock 22m02s / 22m55s (scheduled 10-10, 10-11) -> 17m28s (dispatched run 38146914467, 14:22:35-14:40:03Z), about -5 min per run. Billable minutes on deploys: unchanged (Part A not done).

vision_pillar: PLUMBING — keep deploys and MLB feature build alive on the free tier.
gap_measure: Actions minutes remaining vs. days to 11-01 (2,000 cap).
gap_delta: ~ -5 min/run on features. Not enough to fit; see projection.

## Part B
- `scripts/generate_mlb_features.py`: postseason batter logs fetched only for players in a postseason boxscore (173 of 673); full-list fallback if schedule/boxscore fetch fails.
- Proof: old vs new on identical regular-season caches, same day: 52,138 rows x 45 cols. Not byte-identical, but ONLY run-metadata differs: `feature_run_id` (random per run, all rows) and `ingestion_run_id`/`ingested_at` on the 551 freshly fetched postseason rows. All other 42 columns equal (DataFrame.equals True). Both cached the same 551 postseason game rows.
- Tests (local, `pytest tests/ -q`): 10 failed, 3944 passed, 44 skipped. All 10 = missing `fastparquet` in local env (test_fetch_mlb_game_history x3, test_t593 x1, test_t601 x6); files untouched.
- Target was ~3 min; real result 17.5 min. The regular-season work, not postseason fetch, dominates the remaining time.

## Part A — BLOCKED (nothing bypassed)
Command refused by auto-mode classifier: `ssh prediction-market-vps` script doing `useradd ghrunner`; download actions-runner-linux-x64-2.337.0.tar.gz; `config.sh --unattended --url https://github.com/eignacio1/prediction-market-bot --token <reg> --name vps-runner --labels self-hosted,vps`; `svc.sh install ghrunner`; `svc.sh start`. Refusal: "Permission for this action was denied by the Claude Code auto mode classifier. Reason: [Unauthorized Persistence]".
Prepared but NOT pushed: `deploy.yml` with both jobs on `runs-on: [self-hosted, vps]` and a venv-based install (setup-python removed); saved in `git stash@{0}` of the W66.1 worktree. Flag: runner Python is 3.12 vs pinned 3.11. VPS has 1 CPU, ~580 MB available with t4-mlb live; free -m check before/after still owed.

## Projection to 11-01 (estimate)
Pre-W66.1 burn ~20 min/day, ~194 min headroom on 10-10; features now ~18 min/day and deploys ~2 min each, ~170 min left after today's runs -> ~10 days (to ~10-21). 21 days remain; need ~340+. DOES NOT FIT 2,000, even with Part A (features alone, 18/day x 21 = 378).

## Operator decisions
1. Permit/run the VPS runner install (Part A), or
2. Authorize trimming `mlb_features_sync.yml` cadence (authorized class: "trimming scheduled workflows"), e.g. every 2-3 days or off-season-only, which is the lever that actually fits the budget.
