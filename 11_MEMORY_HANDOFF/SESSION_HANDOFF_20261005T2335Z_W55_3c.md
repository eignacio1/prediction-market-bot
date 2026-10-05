<!-- session-meta
task_id: T-683
tier: STANDARD
timestamp: 2026-10-05T23:35:00Z
commit: bdaff5a
one_line_summary: W55.3 - MLB shadow games cache refreshed off-box and synced to VPS (PR #164); 69 T1 rows written; GG-470/453 partial, GG-482 scheduler gap registered
gg_touched: GG-470, GG-453, GG-482
adr_touched: none
plan_deliverable_moved: no
-->

# SESSION HANDOFF — W55.3 close-out
Status: DONE (standing dependency) | PR #164 merged @ bf1afb0, CI green | t4-mlb restart not_needed.

## Strategic Decisions This Session
| Decision | Where |
|---|---|
| ESPN ruled out (no MLBAM ids); off-box refresh + stamped sync chosen | DECISION_LOG 2026-10-05 |

## What changed
- scripts/fetch_mlb_game_history.py, run_mlb_pregame_shadow.py (26h freshness guard), sync_mlb_games_cache.sh, tests; VPS T1 cron no longer passes --refresh.
- 69 T1 MLB shadow rows on disk; GG-470/GG-453 PARTIALLY RESOLVED; GG-482 opened.

One-thing-pending: operator runs scripts/sync_mlb_games_cache.sh daily from the Mac (or picks a scheduler) or MLB shadow cells fail closed after 26h.
Resume: GG-482 scheduler, then GG-472 (MLB settle script). close_session_claim.sh NOT run (GG-451 hazard).
