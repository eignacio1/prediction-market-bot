# Session Handoff — 2026-10-30T15:00Z

<!-- session-meta
task_id: T-1500
tier: STANDARD
timestamp: 2026-10-30T15:00:00Z
commit: ffb5847
one_line_summary: W95.1 PARTIAL: NBA engine v1+v2 cron + daily refresh installed on box (#379); no rows yet, GG-1450 open; Part B not started
gg_touched: GG-1450
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH, PROOF
gap_measure: D4 (NBA engine live), P-forward rows
gap_delta: NBA engine arms installed 0 -> 2, rows read back 0 (box nba_engine_cron_readback 2026-10-30T14:4xZ)
pattern_sweep: n/a (no defect fixed)
surface_delta: +2 cron lines (registered), 0 services
-->

# SESSION_HANDOFF W95.1 — NBA engine live on the box (PARTIAL)

Status: PARTIAL | branch session/w95-1-part-a-readback | PR #379 merged f6bb0c7, CI green (test pass 6m12s) | Part A installed, Part B not started.

**Result:** EXP-044 v1 and EXP-044b v2 runners plus the daily refresh are installed on the box (14:34Z) and read back: crontab block present, store 67 games to 2026-10-28, v1 status.json present, both silent-arm specs IDLE (no game within 12h). **No forward rows exist yet**; the first can only appear at tonight's tip−60 pass, so GG-1450 stays OPEN.

MEASURE MOVED: NBA engine arms logging live 0 → 2 *installed*, 0 rows read back (box `nba_engine_cron_readback` 14:4xZ) — not counted as logging until rows. Games in store: refresh scheduled daily; last game date 2026-10-28 at 10-30 (source lag, unexplained). Input factor classes 4 → 4 (Part B not run).
Stage per factor: availability / lineups / officials — none reached (not built into v3).

vision_pillar: DEPTH + PROOF
gap_measure: D4 (NBA engine live), P-forward rows
gap_delta: installed, rows pending
pattern_sweep: n/a (no defect fixed); premise correction only (GG-1450 "ship the store")
surface_delta: +2 cron lines (+2 registry entries), 0 services; budget red only on own keys at install.

**Next (first thing):** after tonight's NBA games, request `nba_engine_cron_readback` and read: rows per family for v1 AND v2 (all four families, every game that night, archive quote at tip−60), `logs/nba_engine_live_cron.log` error count, and v2 `status.json` (never run yet; v2 memory unmeasured). If rows are missing for a game that tipped, that is a silent arm — diagnose before anything else. Then resolve GG-1450. Part B (v3: availability 93.1, lineups 92.3, officials only if crew known pre-price, GG-1390; paired game-clustered held-out Brier per family vs v2; freeze EXP-044c only if v3 wins somewhere) remains to be done; v1/v2 untouched.

Observed, unregistered: runner 517MB RSS on a 961MB box (sequential under one flock mitigates); store last_game_date lag; weak hash registry key for the refresh line.
Operator decisions: none.
