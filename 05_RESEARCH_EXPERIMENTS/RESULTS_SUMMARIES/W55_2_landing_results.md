# W55.2 — Landing PR #160 + Live Terminal proof + t4-mlb self-restart (2026-10-05)

**Status: DONE.** No order/position/stake/kelly change. VPS reads were read-only.

## D1 — Merge
- PR #160 (`w52/landing`, head 5dbddb2, CI green, CLEAN) merged as merge commit **feec98f** (`--match-head-commit` pinned).
- Deploy run 37280527776 (success). Step "Decide t4-mlb restart (GG-432)": `restart -- t4-mlb imports changed: src/prediction_market_bot/c5_execution/market_type_registry.py; no MLB game in progress`. t4-mlb restarted 07:57:14 UTC (NRestarts=0), pmbot-web-dashboard restarted 07:57:11.
- A second deploy (49bf44c, a concurrent docs push) ran after; VPS HEAD at read time = 08332fe (W55.3 docs commit), which contains feec98f. Dashboard `process.sha` = `origin.running_sha` = 08332fe, `commits_behind=0`, started 07:57:12Z. (Literal equality with feec98f does not hold because later docs commits deployed; ancestry does.)
- PR #157 was already MERGED (07:55:53Z); no comment needed.

## D2 — Live Terminal proof (running dashboard `/api/data` + served `/` page)
- `shadow.cells` = **24** all `registry_status=shadow`: 12 NFL, 9 NHL, 3 MLB player-hits (rows_total 0, last_ts null — T1 shadow blocked by GG-453/470). Row counts/last-row times populated per cell (e.g. NHL T3 game total 736 rows, last 2026-10-05T00:40Z).
- Served page contains `(ledger only)` label path for non-shadow registry cells (line ~653).
- Drawdown tile now **`DRAWDOWN (REALIZED)`** = max(0, −total_realized_pnl)/initial = 106.0099/1000 = **10.60%**; the old formula (initial−bankroll)/initial gave 26.62%.
- T1 book labelled **FROZEN**: `portfolio.last_updated = 2026-08-06T00:05:01Z` (60 d ago); freshness `t1_mlb` level red, age 5.21M s. 26 open T1 positions (mlb_postseason panel) — booking is W55.1's scope.
- Note: `freshness.t4_mlb.age_s` was 17.5k s (~4.9 h) at read time: idle between games, level ok.

## D3 — GG-451 / GG-419
- `tests/test_close_session_claim_head_guard.py` + `tests/test_claim_session_head_guard.py`: 4 passed on the merged tree.
- GG-451 → RESOLVED (merge feec98f). GG-419 was already RESOLVED.

## D4 — Why t4-mlb restarted itself at 2026-10-05 01:31:28 UTC
- **OOM kill, not a deploy.** `01:30:25 t4-mlb.service: killed by the OOM killer ... status=9/KILL ... 'oom-kill'`; restarted after RestartSec 60.
- Kernel: `global_oom`, `CONSTRAINT_NONE` (host-wide; t4-mlb's 512 MB cgroup cap not hit). Host: 961 MB RAM, 0 swap, ~786 MB anon at the kill. Victim had ~137 MB anon-rss — a victim, not the hog.
- Lost cycle-log time: last row 01:29:59, next 01:31:36 = 96 s vs ~52 s normal → ≈44 s excess. No game live.
- Recurring: 2026-10-04 01:31:15 global OOM killed a cron.service python (victim job unidentified); 2026-09-23 05:04; 2026-09-10 01:39-01:51 (12 cgroup OOMs). Co-timed with 01:25 `run_pregame.py` and 01:30 `run_paper_trade.py` crons.
- Registered **GG-477** (OPEN, MEDIUM). Nothing changed or restarted.

## Operator decisions
1. GG-477 remedy: swap / stagger 01:25–01:30 crons / `OOMScoreAdjust` on t4-mlb / hunt the cron memory hog.
2. Which cron job died on 2026-10-04 (unidentified) and whether that run's output was lost.
