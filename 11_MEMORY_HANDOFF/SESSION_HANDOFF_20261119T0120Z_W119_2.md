# Session Handoff — 2026-11-19T04:50Z (W119.2 close)

<!-- session-meta
task_id: W119.2
tier: STANDARD
timestamp: 2026-11-19T04:50:00Z
commit: 109c469
one_line_summary: W119.2: NBA depth splits wired behind switch, 12 NBA game cells SHADOW in code, layer-4 stump rule; D6 NBA 4 -> 7 (PR #527)
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D5(b) NBA applied, B1 code==box, D6 NBA
gap_delta: B1 by code 48 -> 60 (market_type_registry @ 109c469, = box); D6 NBA 4 -> 7 wired (d6_read box 04:25Z); D5(b) NBA: S1/S2/S4 splits wired, switch off
pattern_sweep: registry-status mirrors - grepped seat toml/md, shadow-count test, autoflip test for not_implemented/48; fixed nba.toml, NBA_SEAT.md, test_pregame_shadow_framework in 88c7a64
surface_delta: 0
-->

**Trigger:** operator /session-end. **Last commit:** `109c469` (main, PR #527 squash-merged, both checks green on own head `04945f7`; box deployed).

## Strategic Decisions This Session
None — implementation-only session.

## What changed
- A: `nba_depth` wired behind `PM_LEAF_MAP_VERSION=+nba_depth` (S1/S2/S4 split, S3/S5 logged; archive SHA pinned; v1 unchanged; nothing flipped).
- B: 12 NBA game cells SHADOW in code; seat toml/md + shadow-total test (60) updated.
- C: `coverage.stump_root` layer-4 stump rule (>=30 pooled rows); tests `test_w119_2_stump.py` (5).

## Caveats
- NBA_MONEYLINE T1-T3 not credited: v1 leaves have empty fit.
- S3/S5 have no runtime snapshot source on the box (logged "unknown").
- CLAUDE.md Right-now block RED until window regenerates at wave close.
- Local full-suite log errored at collection on test_approval_path_invariants (unexamined, likely env); CI full suite passed.

## Pending (one thing)
Window: regenerate Right-now block at wave close; decide whether to flip `+nba_depth` after shadow rows accrue.

## Resume
`bash .claude/hooks/session_guard.sh` then `scripts/session_delta.sh "$(cat 04_EXECUTION/.last_session_checkpoint)"`
