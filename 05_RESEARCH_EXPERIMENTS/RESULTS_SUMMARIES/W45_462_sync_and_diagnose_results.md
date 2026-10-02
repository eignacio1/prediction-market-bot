# Wave 45 block 46.2 — sync-and-diagnose results (2026-10-02)

Claim: T-606 (no GG range). Deliverable: this summary. No GG/DECISION_LOG writes (46.1 owns them).

## D0 snapshot
14 files copied to session scratch (`d0_snapshot/`, untracked moved to `moved_untracked/`) with md5s recorded before any action.
Key md5: ACTIVE_QUEUE e39905ce…, ARCHIVE 92d20b0e…, SESSION_CLAIMS 979b689e…, CLAUDE.md b541f491…, _w33_recovered 5468f475…, Reload Dashboard.command 20c25f35…, Visual Dashboard.html d9dc3058….

## D1 stale lock
`.git/index.lock` held open read-only by the Virtualization XPC host (pid 33525 at 45.3; 76945 when checked, same program). No git executable running. Every D1 condition held and was pasted in-session; lock removed.

## D2 landed
- 7cdde16 queue + archive, byte-for-byte (hash-object verified)
- a261bfc T-601 CLOSED row appended to SESSION_CLAIMS.md

## D3 fast-forward
Shared tree HEAD == origin/main == b17c50d (left-right 0 0). Nothing lost. Remaining local state: `OPERATOR_CONSOLE.md` modified (governance hook regenerates it), untracked `_w33_recovered.md` (already in archive verbatim), `Reload Dashboard.command`, `Visual Dashboard.html` — left in place, not classified for removal.

## D4 ADR-0067 documents-only landing
Landed b17c50d: ADR-0067 (**Status: PROPOSED**), T589 results, SESSION_HANDOFF_20260930_0045. paper_trader.py, its tests and the bench script remain on `origin/session/20260930T001343Z-t4-ledger-durability`.
Test line on current main + candidate: `3455 passed, 28 skipped, 2 warnings in 641.36s (0:10:41)`.

## D5 Step 4 anomalies (read-only)
Evidence gathered on VPS from `paper_mlb_cron.log`, `schedule_validator_mlb.log`, `t4_mlb_cycle_log.jsonl`, `exp_output/PRICE_ARCHIVE/prices_*.jsonl`, crontab, journal.

1. **SemanticFloorViolation = 1 — EXPECTED (stale cumulative count).** The grep counts the whole log history, not a recency window; it is a historical hit, not a live failure.
2. **Two T1 MLB runs with 0 players matched — EXPECTED.** Regular season ended (feature CSV stuck at game_date 2026-09-27); the PRICE_ARCHIVE shows KXMLBHIT tickers existing only for the remaining postseason dates (10/01, 10/03), i.e. no matchable slate on the days of those runs. Postseason slate does not match the regular-season feature pipeline.
3. **T4 cycle-log age 16h — EXPECTED.** T4 writes a cycle row only with live batter state. No MLB game was live in that window. Startup log: "T4-MLB self-heal: no active games found — starting immediately", "Initial MLB game IDs: (none yet)".

Caveat: verdicts rest on log/archive evidence; I did not independently query the MLB schedule API for the exact windows.

### Off-season answer (no action taken)
Nothing stops either pipeline. T1 is a daily 11:00 UTC cron with no end date; it will run against an empty slate (0 players) every day all winter, which the Step 4 grep will report as a "signal failure" each time. T4 is a systemd `Restart=on-failure` unit that idles when no games are active; it does not exit. Expect permanent false alarms from Step 4 until it is season-aware.

## GAPS FOUND — FOR REGISTRATION BY 46.1 OR WAVE 47
1. PIPE-08 schedule validator HTTP 406 failures: 110 occurrences since 2026-07-03; MM/DD/YYYY URL returns 406, ISO date returns 200.
2. t4-mlb manually restarted repeatedly 10/2 (19:42, 21:09, 21:17, 21:45 UTC) and 10/1 (01:35–02:52 UTC) by an unidentified actor.
3. `t4-mlb.timer` inactive, no NEXT (last fired 2026-07-04).
4. SemanticFloorViolation check is a cumulative whole-log count, not recency-windowed (same defect class as GG-085).
5. `audit_mlb_t4.jsonl` CONTAMINATION_HALT = 162,168 events; unusable as a health signal.
6. Feature CSV stuck at 2026-09-27 post regular season.
7. `index.lock` created by Virtualization XPC host; recurrence unknown.
8. Step 4 has no season awareness: will false-alarm all winter (see off-season answer).
9. Three untracked files remain in the shared tree (see D3).
10. Q1–Q7 compromised-check was not run or shown in this session; not covered by this summary.
