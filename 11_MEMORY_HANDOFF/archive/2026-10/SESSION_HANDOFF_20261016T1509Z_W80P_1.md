# SESSION_HANDOFF — W80P.1 Surface-budget false red + thin-market depth capture (STANDARD)

<!-- session-meta
task_id: W80P.1
tier: STANDARD
timestamp: 2026-10-16
commit: 9544c98
one_line_summary: W80P.1 PARTIAL: "behind HEAD" made import-aware with one shared definition (deploy_truth.unapplied_changes), PR #281 merged CI green; thin-market depth capture built + tested + registered paused; box unreachable from this cloud session so GREEN read-back and install PENDING
gg_touched: GG-915 (registered, IN PROGRESS until box read-back)
adr_touched: none
plan_deliverable_moved: yes
vision_pillar: PLUMBING
gap_measure: SURFACE BUDGET red items (t4-mlb BEHIND false red); thin-market order-book capture running (no -> yes)
gap_delta: budget rule fixed in code (RED item expected 1 -> 0 on next box probe; NOT read - box unreachable); capture no -> built, not running (install gated on GREEN, PENDING)
pattern_sweep: two "behind HEAD" computations found (runtime_registry.probe_local import-blind; deploy_truth.staleness import-aware) -> both on deploy_truth.unapplied_changes; CLAUDE.md Hard Rule 14 text aligned; .claude/hooks/governance_scan_full.sh already reads deploy_truth (no change); session_guard.sh "behind" is checkpoint-vs-HEAD, unrelated
surface_delta: 0 (capture registered status=paused, not installed)
-->

**Status: PARTIAL** — code DONE and merged; activation PENDING (box unreachable).

PR [#281](https://github.com/eignacio1/prediction-market-bot/pull/281) squash-merged as `9544c98`, CI `test` green (run 38920928304).
**t4-mlb deploy decision:** `not_needed` — computed with `deploy_restart_policy.decide` on the merge's changed files (no t4 import changed). The box's own Deploy summary could not be read (deploys run on the VPS cron; no ssh here).

## Environment reachability (this cloud session, 2026-10-16 ~14:50Z)
| Target | Result |
|---|---|
| GitHub: git push, PR create/merge | OK (git over proxy; GitHub MCP for PRs; `gh` CLI token invalid: "Failed to log in to github.com using token (GH_TOKEN)") |
| VPS ssh `prediction-market-vps` / 157.230.91.33 | REFUSED: `timeout: failed to run command 'ssh': No such file or directory` |
| Kalshi public `api.elections.kalshi.com`, demo `demo-api.kalshi.co` | REFUSED: `curl: (56) CONNECT tunnel failed, response 403` (environment network policy) |
| Dashboard https://157.230.91.33 | REFUSED: same 403 |

## What changed
1. `scripts/ops/deploy_truth.py::unapplied_changes(proj, service, sha, head)` — the single definition of "behind": files the service uses (`relevant_files`: restart policy's import closure for t4-mlb) changed since its running SHA, plus the first such commit's time. `runtime_registry.probe_local` now calls it (was: every src/scripts commit). Tests: `tests/test_w80p1_import_aware_behind.py` (unrelated merge -> behind 0h, budget GREEN; imported change -> BEHIND, RED; same set as the restart policy).
2. `scripts/thin_market_depth_capture.py` + `deploy/cron.thin_capture` (`21,51 * * * *`) + registry entry `status = "paused"`. 17 NFL/NBA series; books for markets closing within 48h (<=6h every run, else every 3h, least-recent first); candles after close+3h; 500 books/run, 60 candle mkts/run, 80 MB/day, 4 GB total; flock; state.json. Tests: `tests/test_thin_market_depth_capture.py` (9).
3. CLAUDE.md Hard Rule 14 text; GG-915.

## PENDING (box unreachable) — exact commands for a session with box access
```bash
# 1. read the budget after the deploy picks up 9544c98
ssh prediction-market-vps 'cd /opt/prediction-market-bot && git log -1 --format=%h && venv/bin/python scripts/runtime_registry.py live'
# 2. ONLY if it reads GREEN: install the fragment and flip the registry entry
ssh prediction-market-vps 'cd /opt/prediction-market-bot && (crontab -l; cat deploy/cron.thin_capture) | crontab - && crontab -l | grep -c thin_market_depth_capture'
#    then PR: RUNTIME_REGISTRY.toml entry status = "live", alarm = "staleness: SURFACE BUDGET goes RED if logs/thin_capture_cron.log is older than 2h", max_age_h = "2"
# 3. read back the first capture (after :21 or :51)
ssh prediction-market-vps 'cd /opt/prediction-market-bot && tail -3 logs/thin_capture_cron.log && ls -la exp_output/KALSHI_HISTORY/thin_capture/'
```
If step 1 is still RED, do not install (Hard Rule 14) and record the red item.

Stage reached per factor: n/a (plumbing).
Operator decisions: none.
