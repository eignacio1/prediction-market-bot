<!-- session-meta
task_id: T-732
tier: STANDARD
timestamp: 2026-10-08T01:45:00Z
commit: 22ba387
one_line_summary: W59.3 done: NBA preseason shadow ledger + Live Terminal NBA season; NHL goalie verdict (b); ADR-0070 widened+accepted, GG-400 resolved
gg_touched: GG-400, GG-401
adr_touched: ADR-0070
plan_deliverable_moved: no
-->

# SESSION HANDOFF — W59.3 (2026-10-08 ~01:40Z)

**Status:** DONE | main @ 6e3927c (PR #180), earlier #179 | CI green both; Deploy t4-mlb decision `not_needed` for both.

**Result:** NBA preseason shadow ledger live on VPS (labelled, excluded from judged n); NBA in Live Terminal `_season_state`; NHL goalie verdict (b); ADR-0070 widened then ACCEPTED; GG-400 RESOLVED (archived); GG-401 stays OPEN.

## Operator decisions
1. Adopt the EXP-036 line-42 amendment (projected starter at every band, `confirmed=False`). Text: results doc Part B.

## Strategic Decisions This Session
| Decision | Where |
|---|---|
| ADR-0070 widened to NHL/NBA shadow, then ACCEPTED (operator 2026-10-07) | DECISION_LOG 2026-10-08 |
| NHL goalie verdict (b); amendment awaits operator | results doc Part B |

## Next undone
- Screenshots DONE (W59_3_screens/). Gap found: Feeds & Health tab shows no NBA row until a ledger exists; should say "no data - awaiting" (T-732 follow-up, not fixed per Rule 11).
- 10-21: run `ssh prediction-market-vps "cd /opt/prediction-market-bot && venv/bin/python scripts/w59_3_nba_flip_check.py"`; it prints the exact `promote_cell_status(..., superseding_reference="EXP-038")` calls. NBA cells NOT flipped.
- After 10-20: remove the `EXP-038 NBA PRESEASON` cron block (VPS and deploy/cron.nba_shadow_preseason).

## Notes
- Premise corrected: preseason rows were NOT being banked; built the labelled ledger.
- Rule slip: one unscoped `git stash` in my own worktree, popped immediately, nothing lost.
- #180 needed four merge-from-main rounds (concurrent W59.1 edits to the GG log/archive).
- No order/position/stake/kelly change; no live ledger writes.
