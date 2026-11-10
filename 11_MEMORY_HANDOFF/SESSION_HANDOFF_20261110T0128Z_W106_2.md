<!-- session-meta
task_id: W106.2-B-057
tier: STANDARD
timestamp: 2026-11-10T01:28:00Z
commit: 6a387d5
one_line_summary: W106.2 B-057 cost wall measured (taker 1.5-2.3c/side, maker net negative in every bucket); demo-fee check blocked
gg_touched: none
adr_touched: none
plan_deliverable_moved: no
vision_pillar: EXECUTION
gap_measure: E2 / P2
gap_delta: net-of-cost rows 0->8; maker-positive cells 0 (12_EXPLORATORY/quant_w106_costs/RESULT.md @ 0e612b8)
pattern_sweep: n/a (no defect fixed)
surface_delta: 0
-->

# SESSION HANDOFF - W106.2 B-057 The cost wall
Status: PARTIAL | B-057: partial (wall measured; demo-fee confirmation blocked) | branch session/20261110T011344Z-w106-2-cost-wall | PR #448 merged (squash 1f2db70), CI test pass 4m57s read before merge
One line: a trade costs ~1.5-2.3c each way as taker (props 4-8c), maker nets -0.6 to -4.3c per fill in every bucket; only the 11 in-sample 89.2 hold-to-settle cells clear it.
MEASURE MOVED: EXECUTION E2 / PROOF - effects with a net-of-cost figure: 0 -> 8 rows (table B1); maker-net>0 cells with interval above 0: 0.
vision_pillar: EXECUTION
gap_measure: E2 / P2
gap_delta: net-of-cost rows 0->8; maker-positive cells 0
pattern_sweep: n/a (no defect fixed)
surface_delta: none (no new live component; read-only box aggregate via stdin)
Stage per factor (ADR-0075): spread/fee wall = interpreted (aggregated + priced); no factor reached applied.
Operator decisions: none. Recommendation only: forward hold-to-settle pre-reg of the 11 89.2 cells (not applied).

## Blocked / refused
- A1 demo-fee check: ssh write of a probe to the box /tmp plus sourcing .env was DENIED by the classifier ([Remote Shell Writes]). Not worked around. Remedy: allowlisted bridge task (PR to scripts/box_tasks.py TASKS + test) for read-only demo GET /portfolio/orders/{id} fee read, or the window runs it. Probe draft is in the session scratchpad only.
- WebFetch kalshi.com/fee-schedule returned HTTP 429; fee source remains R-068 cards (PDF 2026-07-07; web 2026-10-27 undated).
## Caveats
- tts is a calendar-day proxy (no game-start field). Post-epoch n = 0 (no fills after 2026-11-06T01:03:42Z pulled); everything is pre-epoch YES-only or non-fill-based.
- NFL/NBA/NHL maker fees understated in kalshi_fees.json (known table gap).
- Session-start protocol Steps 1-4 / Q1-Q7 were not run in full (worktree, guard, claim only; governance cache was 91h stale). Open thread.
- Part B uses 105.4/W92.2 nets as published, not recomputed; 103.2 gross sizes per contract not re-derived.
