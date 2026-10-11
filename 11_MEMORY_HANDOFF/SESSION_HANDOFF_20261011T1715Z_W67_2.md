# Session Handoff — 2026-10-11T17:15Z

<!-- session-meta
task_id: T-810
tier: STANDARD
timestamp: 2026-10-11T17:15:00Z
commit: 6897a3c
one_line_summary: W67.2 Part B landed: demo-listing skip before arm assignment + shadow-cell flat stakes (uuid id fix); Part A awaits 10-12 data.
gg_touched: GG-570, GG-571
adr_touched: none
plan_deliverable_moved: no
vision_pillar: EXECUTION
gap_measure: E1, E2, E3
gap_delta: shadow-cell accepted demo orders 0 -> 36 in first hour after fix (VPS logs/demo_fill_policy.jsonl 17:00-17:10Z; 261 rejected HTTP 400 before); E1 not yet measurable (needs 10-12 MLB game)
-->

**Trigger:** operator-initiated /session-end. **Last commit:** `6897a3c` (main; PRs #222, #225 merged).

## Strategic Decisions This Session
- NBA shadow cron NOT given demo_fill.env (credential-free guard test_nba_shadow_safety; NBA dark) -> GG-570 (operator decision). NHL shadow unstaked -> GG-571.
- Shadow client_order_id = uuid5(row id); listing skip = per-ticker 300s TTL cache, unknown fails closed, skip precedes arm assignment (both arms).

## What changed
- `kalshi_client.is_listed_on_demo`, `demo_fill_policy.listing_skip_reason`, paper_trader + shadow_flat_stake hooks (#222); uuid fix (#225). NFL/MLB shadow cron lines load demo_fill.env on VPS (backup /root/crontab.bak.w672.20261011T163328Z).
- Deploy: t4-mlb restarted 16:32:55Z (#222, no live game). #225 touched no t4-mlb import; not restarted.
- Tests: serial full suite 3986 passed/0 failed on the fix; 3 unrelated load flakes in parallel re-run (dashboard <2s assertion, Kelly property test) — not registered yet.

## Pending (Part A, after 2026-10-12 11:00Z)
Read policy log + fill sidecars; orders per book/arm, skips by reason, cancels, fills; E1 two ways (all vs demo-listed); ADR-0072 turn-off check; fills/arm/week projection (550/arm in 8 wks) with/without shadow; prove `kalshi_order_failed` 404s ~0 after the MLB game; then GG-564 RESOLVED, GG-536 on both dashboards; "Day one" in W65_2_forward_test_on_results.md; ACTIVE_QUEUE row 67.2 -> done.

**Resume:** `scripts/new_session_worktree.sh w67-2-day1-read` then read this file.
