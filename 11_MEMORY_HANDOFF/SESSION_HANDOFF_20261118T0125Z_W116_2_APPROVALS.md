<!-- session-meta
task_id: B-095
tier: STANDARD
timestamp: 2026-11-18T01:25:00Z
commit: bba152e
one_line_summary: W116.2 close: operator approved placement policy + arm-book cap raise (both still off); GG-1942 fix in PR #508
gg_touched: GG-1942 (fix PR #508, open)
adr_touched: ADR-0072 addendum 2026-11-17 PROPOSED -> APPROVED
plan_deliverable_moved: no
vision_pillar: EXECUTION
gap_measure: E1/E2/E3 per arm and option
gap_delta: none this continuation (approvals + precondition fix; no new box read)
pattern_sweep: GG-1942 - grep BOOKS consumers in src/ scripts/ tests/ (exposure_gate, paper_trader, t4_fill_status, distance_to_optimum use their own BOOKS or book_for_portfolio; none affected); advisory books now SHADOW, RIDE_BOARD, ARM_ORDERS
surface_delta: 0
-->
# Handoff W116.2 - approvals continuation (follows SESSION_HANDOFF_20261118T011000Z_W116_2.md)

## Strategic decisions this session
| When | Decision | Source |
|---|---|---|
| 2026-11-17 PT | Operator approved both W116.2 demo decisions: ARM_PLACEMENT_POLICY=on (after a frozen spread-logged table), ARM_BOOK_CAPS=raised (after GG-1942) | "Yes - I provide my approvals." DECISION_LOG 2026-11-18 01:15Z; queue lines marked APPROVED; addendum status APPROVED (bba152e) |

## Changed
- Docs (main bba152e): approvals recorded. Nothing turned on.
- PR #508 (session/20261118-gg1942-arm-advisory): ARM_ORDERS advisory in exposure_gate.BOOKS; arm orders still gate under SHADOW (tested). 60 gate tests pass locally.

## One thing pending
GG-1955 (main's ROLLING_BACKLOG duplicate order 16) reddens CI on #505 and #508. Once a backlog owner fixes it: merge origin/main into both, merge on green, deploy, then flip ARM_BOOK_CAPS=raised on the box (operator-approved, demo). Placement policy flips only after a table is fit on spread-logged orders (30+ per side).
G6: no real capital, Kelly 0; bet count not re-checked this close-out.

## Resume
Read this file, then `gh pr checks 508 505`.
