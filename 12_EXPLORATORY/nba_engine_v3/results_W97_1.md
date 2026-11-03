# W97.1 results — NBA engine v3 (Part A), first nights (Part B), points without the leak (Part C)

Purpose: DEPTH + PROOF. Measures: NBA engine arms with rows 0→2 (v1, v2) and v3 frozen 0→1 (EXP-044c); player points from the engine, leak-free, held-out.

## Part A — v3 built, frozen, merged; NOT installed
PR #391 (`4e5cfd65`, CI green): `live_v3` runner, EXP-044c frozen at merge (spread + team total only; sha256 e7e2666f…a80a081; looks 2027-01-31 / 2027-04-20, judged n 300 / 1,200; modal outcome undecided/FAIL, total v3 not better than v2). Lead-60 held-out 2025–26 (n=2271), v3_all − v2_core Brier, game-clustered 95% CI: spread −0.00758 [−0.0104, −0.00484]; team total −0.00254 [−0.00353, −0.0015]; moneyline −0.00006 [−0.00394, +0.00402]; total +0.00023 [+0.00002, +0.00043]; all −0.00296 [−0.00419, −0.00172].
Deploy: box HEAD `50b07ee9` contains #391; t4-mlb runs box HEAD code (started 2026-10-30T16:06Z); no t4-mlb-imported file changed → no restart (`deploy_truth_read` 20261103T004321Z).
**Install: refused.** `gh workflow run box_tasks.yml -f task=nba_engine_v3_cron_install -f note="W97.1: install live_v3 cron …"` was denied by the Claude Code auto-mode classifier ("Production Deploy"). Skipped only that step; no workaround tried. `budget_read` (20261103T005036Z) said RED only on: the uninstalled v3 line itself, W97.3's uninstalled picks-sheet cron, and the v3 silent-arm alarm (silent because uninstalled); healthcheck HEALTHY, 0 faults, 0 stale. The v3 cron line is in `deploy/cron.conf` and the registry; installing is a one-line operator/permission action (`nba_engine_v3_cron_install`, then `nba_engine_v3_cron_readback`).

## Part B — first nights (box read 2026-11-03T00:52Z)
- v1 (EXP-044): 1,480 rows, 56 events; v2 (EXP-044b): 1,904 rows, 77 events. Silent-arms read: v1 OK and v2 OK on all 6 games that started in the last 12h; NBA regular-season shadow, player points, EXP-040 all OK. Runner error lines in last 500 log lines: 0.
- v3: SILENT (6 games, no rows) because the cron is not installed (above). GG-1450 resolves only on rows → stays open.
- Not resolved by this block: v1's event total (56) is below v2's (77), and the readback printed two `Killed` lines after the v2 status (likely the readback's own memory-heavy step). The allowlist has no task that reads per-game rows or box memory, so I could not diagnose either; both are handed forward, not dismissed. The tip-60 Kalshi quote archive was not readable with the allowlisted tasks.

## Part C — player points with no post-game information (B-009)
Study: `study_partc_w97.py`, folds {2025: train 2023 / cal 2024; 2026: train 2023–24 / cal 2025}, strikes 10/15/20/25, scored on player-games where the player played (as EXP-039), game-clustered bootstrap. New arm `engine_set`: share = mu_j / (mu_j + Σ p_i·mu_i) over the pre-tip candidate set (latest prior appearance for the team within 21 days), p_i = P(plays | injury status in the last report ≥ 4h before tip), fit on training seasons. Leakage test (hard assertion before the study): 6 sampled games rebuilt from data truncated to before the cutoff give identical candidates, statuses and features; every report slot passes `assert_pretip`. PASSED.
Brier, pooled (base / engine_pt / engine_set): 0.1103 / 0.1103 / 0.1234. Differences (game-clustered 95% CI):
| contrast | pooled | k=10 | k=15 | k=20 | k=25 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| engine_set − base | +0.0131 [+0.0106,+0.0158] | +0.0138 | +0.0127 | +0.0131 | +0.0127 | +0.0131 | +0.0130 |
| engine_set − engine_pt | +0.0131 [+0.0106,+0.0157] | +0.0145 | +0.0127 | +0.0124 | +0.0127 | +0.0127 | +0.0134 |
Star players (pts10 ≥ 15): +0.0191 [+0.0171,+0.0211]. engine_pt − base reproduces W96.1 (+0.00001 [−0.0003,+0.0003]).
**Verdict: the availability-conditioned engine share is worse than the existing arm at every strike and in both seasons. EXP-044d is NOT frozen.** One bug was found and fixed during the run (calibration/test-game candidates not populated before candidate means were built → shares capped at 0.95, Brier +0.39); the corrected run is the one reported, with no tuning after seeing its score. A plausible, untested reason (not a finding): conditioning on the scored player having played but weighting teammates by play probability inflates his share.
Stage per factor: availability / rotation — interpreted (tested path from fact to price, measured as a loser); applied only once forward rows log (v3 install pending).
