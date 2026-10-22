<!-- session-meta
task_id: T-1070
tier: STANDARD
timestamp: 2026-10-22T00:50:00Z
commit: 564f772
one_line_summary: W83.2 PARTIAL: NBA lineup capture installed but report fetch 403s from box (GG-1030); play-type x absorption null
gg_touched: GG-1030, GG-1031, GG-1032
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D5(b) NBA
gap_delta: NBA lineup factor interpreted -> testable on paper only (not accruing, GG-1030); play-type x absorption interpreted, null n=131 (source: results_W83.md @ 1da11da)
pattern_sweep: n/a (no defect fixed)
surface_delta: +1 cron component (nba_lineup_window, registered), book snapshots only until GG-1030 fixed
-->

# Session handoff — W83.2 (2026-10-22 00:50Z)

vision_pillar: DEPTH
gap_measure: D5(b) NBA
gap_delta: lineup factor interpreted -> testable on paper (frozen pre-registration, cron installed) but NOT accruing: injury-report fetch blocked from the box (GG-1030). Play-type x absorption cross interpreted, null at n=131 (NBA-11). Play-type class graded PARTIAL.
pattern_sweep: n/a (no defect fixed)
surface_delta: +1 cron component (nba_lineup_window), book snapshots only until GG-1030 is fixed

Status: PARTIAL. PRs #313 (0aff806) and #317 (1da11da) merged on green CI. Deploy: the Test Suite runs showed only a `test` job; no t4-mlb restart observed (t4-mlb active on the box).
Read-back: crontab line present (line 648); first run 2026-10-22T00:33:05Z: book snapshot (KXNBAPTS, 14 events) taken; report none (403). No report snapshot exists.
Surface budget was RED at install (own-job staleness expected; the other reasons were not recorded) and the installer appended anyway.
Next: fix GG-1030 (free non-datacenter path, needs permission), then the scored looks at 30 and 60 games apply. Stage: NBA-10 testable (not applied); NBA-11 interpreted (null); NBA-7 play type none.
Operator decisions: none required; GG-1030 fix path is a window call.
