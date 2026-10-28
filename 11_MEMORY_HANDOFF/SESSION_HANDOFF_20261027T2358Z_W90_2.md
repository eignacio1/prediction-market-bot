<!-- session-meta
task_id: T-1330
tier: STANDARD
timestamp: 2026-10-27T23:58:00Z
commit: ce78de4
one_line_summary: W90.2 built the decision router (pure function, 10 tests) and replayed 164,354 situations; 97.66% NO_BET, 2.34% RIDE, FADE and MOMENTUM get none because no measured skill or transition table exists
gg_touched: GG-1330..GG-1334 registered
adr_touched: none
plan_deliverable_moved: no
vision_pillar: DEPTH
gap_measure: D5(a) filtering_mechanisms + decision_trees scaffolds (MLB); situations replayed through the router and share per tree
gap_delta: D5(a) MLB 0/8 -> 2/8 (NFL 6/8, NBA 3/8, NHL 1/8 unchanged), source scripts/distance_to_optimum.py 2026-10-27T23:33:52Z. Situations replayed 0 -> 164,354: NO_BET 97.66% / RIDE 2.34% / FADE 0 / MOMENTUM 0, source 12_EXPLORATORY/router_replay/out/replay.json
pattern_sweep: n/a (no defect fixed). Process note: safe_out() resolves paths against 12_EXPLORATORY/, so --out must be router_replay/out, not 12_EXPLORATORY/router_replay/out (doubled the directory once; corrected before commit). Not searched repo-wide for other callers passing a prefixed path.
surface_delta: 0
-->

# SESSION_HANDOFF W90.2 — the router (DONE)

PR #350 merged as ce78de4, CI green; no Deploy job ran, so no t4-mlb decision. Library only; nothing live.

## Strategic Decisions This Session
Routing doctrine (DECISION_ROUTING.md) written, then ACCEPTED by the operator as written ("Accept - proceed in full"), 840f767. Wiring needs its own pre-registration.

## Result
- Router `decision_trees/router.py`, 10 tests. Replay of 164,354 situations: NO_BET 97.66%, RIDE 2.34%, FADE 0, MOMENTUM 0.
- RIDE settled view (n=2,661, +0.0568 [+0.0424, +0.0718]) is in-sample, not evidence.
- Limits GG-1330..1334: no NBA/NHL archive, news timing and momentum table unmeasured, no shadow-ledger FADE replay, RIDE stub in-sample.

## Next
One thing pending: 90.1's ride.py replaces the stub table. Resume: /session-start, read 04_EXECUTION/ACTIVE_QUEUE.md.
