# Handoff — W120.2 (candidate maps logged beside v1)

<!-- session-meta
task_id: W120.2
tier: STANDARD
timestamp: 2026-11-19T06:20:00Z
commit: 96e9790
one_line_summary: W120.2: router v2, +nba_depth, nhl_v2 arms logged beside v1 on box shadow rows (ON, item 7 approved); NHL goalie/ST verdicts logged not applied.
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: box rows with candidate arms 0 -> NBA router_v2 71, NBA nba_depth 71, NFL router_v2 73, NHL 0 (box candidate_arms_read, 2026-11-19T06:15Z, 72h window)
gap_delta: D6 box read d6_read 05:46Z: 13 wired (NBA 7, NHL 6, NFL 0); NHL 6 -> 6, not moved this block
pattern_sweep: grep PM_CANDIDATE_ARMS src scripts tests deploy .claude -> only shadow_route.py + tests; no other consumer of router_fields reads the new key
surface_delta: 0 (one read-only box task candidate_arms_read added to the allowlist; no cron, no service)
-->

## Strategic Decisions This Session
None new. Queue decision 7 (log candidate maps beside v1) was APPROVED by the operator 2026-11-18 21:19 PT (d4cc5c3). Executed as approved.

## What shipped
- `shadow_route.py`: `candidate_fields` adds `router_candidates` {router_v2, nba_depth (NBA), nhl_v2 (NHL)} each with arm, branch, side, leaf_id, reason, map_version, map_sha256. The `router` (v1) block is byte-identical; orders follow v1 only. A map that errors logs arm=ERROR with its message and never blocks the row.
- Switch: default ON, `PM_CANDIDATE_ARMS=off` turns it off (PR #534). Shadow only, Kelly 0, no real capital.
- `scripts/candidate_arms_read.py` + box task `candidate_arms_read` (PR #535), read-only.
- NHL T1 layer 3: 42 goalie / special-teams verdicts appended to filter_splits.json, all `kept` false with `|logged_not_applied_to_v1` (8 hold a "kept" verdict in `verdict`). Applying them would flip 20 NHL kept flags and change v1 orders, so they wait for an operator-approved v1 change.

## Measured (box, source candidate_arms_read 06:15Z, 72h)
- NBA router_v2 71 rows (v1 agrees 61), NBA nba_depth 71 (agrees 71), NFL router_v2 73 (agrees 21), 0 ERROR. NHL 0: the NHL staked arm runs once a day at 14:00Z, so nhl_v2 rows appear after that run. Read it again then.
- Deploy: box HEAD 9ece917f = origin/main at 05:48Z (deploy_truth_read).

## Process notes (own mistakes)
- The first commit 8b49924 reached origin/main by push before any PR existed, and its CI run was cancelled by later pushes. Its code is covered by the green run on 505a51a and by PRs 534/535 (green on their own heads). Switch was OFF in that commit, so no behavior changed.
- PR 534 was built from the old branch (one commit, two files) after a blocked checkout; checked before merge.

## Open / next
- Re-read candidate_arms_read after 14:00Z for NHL nhl_v2 counts, then D6 NHL.
- Candidate-vs-v1 scoring per leaf (net after costs, held out) is the next look; no verdict is read below judged n.
- Tests: tests/test_w120_2_candidate_arms.py (9), tests/test_candidate_arms_read.py (1).
