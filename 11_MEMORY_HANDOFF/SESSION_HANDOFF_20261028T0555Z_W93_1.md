# Session Handoff — 2026-10-28T05:55Z (W93.1)

<!-- session-meta
task_id: T-1420
tier: STANDARD
timestamp: 2026-10-28T05:55:00Z
commit: e9c8cbb
one_line_summary: W93.1 NBA availability known before tip: interpreted (no demonstrable add beyond rotation, n=2008); applied blocked by data, GG-1420.
gg_touched: GG-1420
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D5(b) NBA B5/B6 interpreted -> applied; D4 NBA factor classes point-in-time 1 -> 2
gap_delta: D5(b) NBA B5/B6 unchanged at interpreted (applied blocked: no 2026-27 events, no pre-tip prices; results_W93_1.md @ e9c8cbb). D4 NBA availability class now built point-in-time (lead-0 cutoff, leak-tested).
pattern_sweep: n/a (no defect fixed)
surface_delta: 0
-->

**Trigger:** block boundary (CI pending on PR #364). **Last commit:** `e9c8cbb` on `session/20261028T053432Z-w93-1-nba-availability`.

## Strategic Decisions This Session
None — implementation-only session. No operator decisions.

## What changed
- `nba_availability.py` + 9 tests: last pre-tip report to P(played), expected lineup features, `AvailabilityLeakError`.
- Result: Questionable 0.514 [0.492, 0.536], Out 0.0008, Available 0.856. Known-at-tip availability adds 0.307 MSE [-0.235, 0.829] beyond rotation (n=2008): does not move. Expected missing minutes 2.641 [0.038, 5.082] is the lead.
- B5/B6 evidence and granularity index updated in `nba.toml` (stage stays interpreted); GG-1420 registered for the flex lane.

## One thing pending
Merge PR #364 once CI is green (merge only own PR), read the Deploy summary and record the t4-mlb decision (not yet read), then update this block's ACTIVE_QUEUE row. Bet count vs G6: not re-checked this close-out.

## Resume
`gh pr checks 364`; then `gh pr merge 364` if green.
