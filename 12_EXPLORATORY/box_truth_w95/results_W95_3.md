# W95.3 results — the box tells the truth (2026-10-30)

Pillar: PLUMBING + EXECUTION. Code: PR #378 (merge 152f0763, CI green, deployed to box 14:04Z, t4-mlb restart decision `not_needed` — no file it imports changed).

## Part A — deploy path
- **How the box gets main:** cron `3-58/5 * * * * scripts/ops/vps_deploy.sh` (`deploy/cron.conf`) fetches origin/main every 5 min. Docs-only diffs (DOCS_ONLY_ROOTS): ff-pull, no gate, no restart. Otherwise: gate (`test_approval_path_invariants` + `test_golden_replay`, fail-closed) → dirty-tree guard → ff-pull → `deploy_restart_policy` (dashboard always restarts; t4-mlb only when allowed, else `skip_live_game` + pending marker). GitHub "Deploy to VPS" is manual-only since W67.3 (GG-1462).
- **Lag, 325 deploy rows (committer date → deploy row):** median 2.1 min, p90 4.7, max 37.4. Burst 10-29 00:26–01:43Z: 13–25 min (serial under flock, gate up to 23 min). Gate+pull, 149 runs: median 0.4, p90 1.7, max 23 min.
- **Alarm:** `deploy_truth.head_lag` — ALARM when box HEAD trails origin/main by more than 45 min (~2x worst gate+tick) for a file a service imports; BEHIND_UNRELATED does not alarm. Read back on box: `OK box HEAD 152f0763 = origin/main`. Measure: 0 → 1 alarm.
- **GG-1440:** `t4_mlb` first-row grace 0.5 h (`ArmSpec.start_grace_h`), t4_mlb only. Tests: 10-29 00:04Z replay → idle; GG-163-style outage → still SILENT; grace applies to no other arm. Read back on box: T4 MLB live `IDLE`.
- **Sweep (GG-1462):** "read the Deploy job summary" fixed in COMMON_RULES_W92/93/94, W89/W90/W91_BLOCKS, RUNBOOK_deploy-dirty-tree, `deploy_restart_policy.py` docstring. Left as dated history: GOVERNANCE_GAP_LOG, DECISION_LOG, SESSION_HANDOFF_*, ACTIVE_QUEUE(_ARCHIVE), W56_3 results, carry-forward, digest.

## Part B — demo `insufficient_balance`
- **Balance now (read-only GET, box, paper→demo host):** $3,287.58 cash, $210.84 portfolio. Not exhausted. A top-up already happened 2026-10-16T05:40Z.
- **Which books:** (1) **paper T4** (MLB, `$0.50` stakes): 2,000 rejected, game dates 10-26/27/28 (402/897/701); audit `kalshi_order_failed` 2,214 on 10-27→10-29, all `insufficient_balance`, only at 00–04Z (the evening game window). (2) **shadow** books: 3,743 of 115,028 shadow orders since 10-12; per day 10-15 1455, 10-16 402, 10-17 233, 10-19 312, 10-22 120, 10-23 341, 10-24 310, 10-25 75, 10-27 255, 10-28 202, 10-29 9, 10-30 0; zero on 10-11/18/20/21/26. Clustered at 16–19Z, 23Z, 00Z, 06Z.
- **Fills/day:** paper book 5 fills of 32 orders, all before the top-up, 0 orders since. Shadow fills after the top-up: NBA 16,635 control / 3,342 treatment; NFL 5,350 / 1,910; NHL 2,830 / 504; MLB 0.
- **Cause (partly pinned):** the W77.1 cash guard (`cash_skip_reason`) IS active in the t4-mlb process (`DEMO_FILL_PLACEMENT_RULE=book_anchor_cancel`) yet logged **0** `insufficient_demo_cash` skips. So balance reads at decision time showed cash ≥ $0.50 (or failed open) while the venue still rejected: consistent with cash reserved by resting 60 s-cancel shadow orders sharing the same demo account during evening peaks (daily placed stakes $5–11k vs ~$3.3k cash). **Not verified**; no balance time-series exists at 00–04Z.
- **No code change made.** The only guard-side fix (reserve in-flight exposure) alters order gating, which this block may not touch, and the cause is unproven. Registered GG-1481 with the measurement needed (log balance_usd on every rejection).
- **Operator step:** none. Demo is plumbing.

## Candidate gaps (registered, not fixed — Hard Rule 11)
GG-1480 (docs-only pushes touching `12_EXPLORATORY/` are not in DOCS_ONLY_ROOTS and run the full gate; gate up to 23 min), GG-1481 (insufficient_balance cause unproven).
