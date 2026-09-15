# GG-271 activation session — in-progress handoff (parked, session limit)

**Branch:** `session/20260915T003404Z-gg271-activate-ring-buffer`
**Claimed IDs (unverified-final, pending T-number/GG-number confirmation next session):** working GG-278, T-547 — re-verify uniqueness via `git log --all` before writing to GOVERNANCE_GAP_LOG.md/DECISION_LOG.md, per GG-236/GG-256 (do not trust these numbers as still free).
**Status:** Diagnosis complete. No production actions taken. No restart performed by this session. Not yet written to GOVERNANCE_GAP_LOG.md / DECISION_LOG.md / SESSION_CLAIMS.md closure row.

## Key finding — task premise was stale before this session started acting

The task assumed `t4-mlb` had run continuously since 2026-09-11T14:44:21Z and still held pre-GG-271-fix code in memory. Direct VPS evidence contradicts that:

- `systemctl show t4-mlb -p ActiveEnterTimestamp` = **2026-09-15 00:12:01 UTC** (not 2026-09-11).
- `journalctl -u t4-mlb` around that timestamp shows a clean, deliberate `Stopping→Deactivated→Stopped→Starting→Started` sequence — not a crash/OOM loop.
- VPS checked-out commit is `61b51f2` (git-committed 2026-09-15 00:10:45 UTC), which IS the GG-271 fix's merge commit (PR #129).
- `04_EXECUTION/SESSION_CLAIMS.md` shows session T-542 closing out at 2026-09-15T00:15:00Z: "merged to origin/main via PR #129 ... T-542/GG-271 bounded rejected_positions ring buffer ... live VPS migration verified."
- Conclusion: **T-542's own close-out deploy already restarted `t4-mlb` and activated the fix**, independently of and prior to any action by this session. This session's scoped restart authorization target (activate the fix via restart) already appears fulfilled by someone else's incidental action.

## Empirical proof the cap is live in the RUNNING process (not just on disk)

- Live file `/opt/prediction-market-bot/logs/paper_portfolio_mlb_t4.json`: `rejected_positions` count = **exactly 2000** (down from 7,654 measured pre-restart at 2026-09-15T00:06Z per the task's own briefing) — behavioral proof `_save()`'s trim executed.
- Confirmed process identity, not just file-on-disk: `systemctl show t4-mlb -p MainPID` → PID 2532761; `/proc/2532761/cwd` = `/opt/prediction-market-bot`; cmdline = `venv/bin/python src/prediction_market_bot/run_t4_mlb_live.py` (checkout-based, not a shadow/installed package).
- Re-imported `paper_trader` using the SAME venv+cwd combination the live process uses (`cd /opt/prediction-market-bot && venv/bin/python3 -c "..."`) → resolved to `/opt/prediction-market-bot/src/prediction_market_bot/c5_execution/paper_trader.py`, `MAX_REJECTED_POSITIONS = 2000`. Rules out a stale shadow install.
- Live file stats at last check (~2026-09-15T00:39:40Z UTC): `open_positions=0`, `closed_positions=2994`, `rejected_positions=2000`, size=7,352,883 bytes.

## Coordination note received mid-session (honor going forward)

A second, unrelated actor ("25.2") is expected to restart `t4-mlb` once more, later, for Kalshi credential rotation — completely unrelated to GG-271. A future `ActiveEnterTimestamp` change beyond the 00:12:01 UTC one already found should be attributed to that, NOT treated as contradicting this diagnosis or as grounds for this task's STOP clause. The ring-buffer cap lives in `_save()` and is restart-persistent by construction, so it survives that future restart too.

## Deliverable status at park time

1. **Diagnosis** — DONE (see above). Task's assumed starting state (continuous pre-fix process) was stale; actual state is better than assumed (already fixed + already restarted by T-542).
2. **Prove running process has the fix** — DONE (module-resolution + empirical trim proof above). No restart by this session was needed or performed.
3. **Backup verification + hold-through-a-write-cycle monitoring** — NOT DONE. Still need to: (a) take/verify a fresh backup of the current (already-bounded) live file and confirm it loads with matching `open_positions`; (b) re-check `rejected_positions` count after a real write cycle (hours later) to confirm it HOLDS at 2000 rather than this being a one-time post-trim snapshot. `scripts/gg271_bound_t4_rejected_positions.py` was read in full — it is safe to re-run against an already-compliant file (it backs up, verifies open_positions match, then calls `PaperTrader._save()` under `_lock`/`_file_lock()`, which is idempotent when `len(rejected) <= MAX_REJECTED_POSITIONS`), but running it is likely unnecessary now since the live `_save()` path already performed the real migration naturally — re-running it would just produce a fresh backup + a no-op trim. Leaning toward: do NOT re-run it; instead take a plain read-only backup (`cp`) for Deliverable 3's evidence trail, and schedule/perform a later re-check of the count.
4. **Correct GG-271's disposition in GOVERNANCE_GAP_LOG.md + register new gap (working GG-278) + DECISION_LOG.md entry** — NOT DONE. Still needs: rebase onto origin/main first (self-serialising close-out rule), re-read GOVERNANCE_GAP_LOG.md fresh (do not trust this note's line/section numbers from before compaction), verify GG-278/T-547 still unclaimed via `git log --all`, then edit.

## Also outstanding from session-start protocol

- Step 4: one `SemanticFloorViolation` line found in `paper_mlb_cron.log` (T1 MLB) — recency (recent vs. historical) not yet resolved. Low priority relative to GG-271 but should be checked or explicitly deferred (register GG/T if unresolved) before close-out.
- "ARE WE COMPROMISED?" Q3 and Q6 narrative answers not yet written.

## Explicit non-actions (by design, not oversight)

- Did NOT restart `t4-mlb` myself — evidence shows the fix is already active; a second restart of a live production trading service was judged unnecessary risk (Hard Rule 11: minimal necessary action) pending confirmation this reasoning is accepted.
- Did NOT touch `paper_trader.py` — Deliverable 1 did not find the cap defective (opposite: proven working), so it stays out of the scope fence.
- Did NOT re-run the migration script against the live file.
- Did NOT write to GOVERNANCE_GAP_LOG.md / DECISION_LOG.md / SESSION_CLAIMS.md yet — pending rebase + fresh re-read per Hard Rule 10, and pending final GG/T number reconfirmation.

## Next steps on resume

1. `git -C <worktree> fetch origin && git -C <worktree> rebase origin/main` (or re-derive the worktree fresh if this one is gone) then re-read `GOVERNANCE_GAP_LOG.md` fresh.
2. Re-verify GG-278 / T-547 (or whatever numbers are chosen) are still unclaimed: `git log --all --oneline | grep -E 'GG-278|T-547'` plus a grep of both gap-log files.
3. Take a fresh timestamped backup of the live `paper_portfolio_mlb_t4.json`, verify it loads + `open_positions` match.
4. Re-check `rejected_positions` count several hours after 2026-09-15T00:12:01Z to confirm it holds at 2000 through a real write cycle (attribute any new `ActiveEnterTimestamp` to 25.2's expected credential-rotation restart, not a re-diagnosis trigger).
5. Write the corrected GG-271 entry + new GG-278 entry + DECISION_LOG.md entry + SESSION_CLAIMS.md closure row, commit path-scoped, push.
6. Produce the final REPORT BACK per the task's original requirements.
