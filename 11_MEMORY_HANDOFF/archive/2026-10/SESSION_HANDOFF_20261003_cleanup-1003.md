<!-- session-meta
task_id: T-637
tier: STANDARD
timestamp: 2026-10-03T20:10:00Z
commit: 42a7c74
one_line_summary: 50.2 cleanup: EXP-037 shadow crons armed, tree synced, PR #157 HELD (live games), GG-430..432 registered
gg_touched: GG-430, GG-431, GG-432
adr_touched: none
plan_deliverable_moved: no
-->

# Session handoff — 50.2 cleanup (local, 2026-10-03)

**Done:** EXP-037 shadow crons armed on VPS (VPS HEAD eb2d1434; crontab backup /root/crontab.bak.20261003T200240Z; T1 MLB line untouched; nothing restarted). Shared tree synced (9 files backed up to PM-scratch/20261003-cleanup/ with md5s; 4 restored to HEAD; ff-only pull). PR #156 closed as superseded. Dashboard real-browser checks clean (GG-431 aside). Gaps GG-430..GG-432 registered.

**Left:**
1. **PR #157 merge — HELD** (draft, touches code, deploy restarts t4-mlb). Head is 855a5f0, not the handoff's 31254a6; re-confirm green. Merge only when Stats API shows no game In Progress AND T4 cycle-log last row > 15 min old (earliest about 03:30Z after Padres@Brewers). Watch the Deploy run, confirm services and VPS HEAD == merge SHA.
2. **Step 5 (NHL cells NOT_IMPLEMENTED -> SHADOW via promote_cell_status)** — not done (code push, same live-game rule).
3. Dashboard process on VPS still runs 077558b (older code, docs-only delta); not restarted by design.
4. Operator decision: deploy.yml restart policy (GG-432, ties to GG-347).
5. Not investigated: dashboard bankroll drawdown 26.63%; GG-431 stale source.

**Notes:** tunnel process was killed by the drop test (re-open if needed); 5 untracked files remain in the shared tree.

**Strategic Decisions This Session:** none beyond holding PR #157 (live-game rule); deploy.yml restart policy left to operator (GG-432).
**Bet count vs G6:** not re-checked this close-out — see live governance scan.
**One thing pending:** merge PR #157 once no game is live (about 03:30Z+).
**Resume:** `scripts/new_session_worktree.sh "pr157-merge"`, then re-verify PR #157 green and the idle-window probe.
