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

PR #350 merged as ce78de4, CI green. Post-merge run was the Test Suite only; no Deploy job ran for this SHA, so there is no t4-mlb decision to record. The change adds a library nothing imports. Nothing live.

## Strategic Decisions This Session
Routing doctrine written as DRAFT in `02_ARCHITECTURE_DESIGN/DECISION_ROUTING.md`. Awaiting operator acceptance.

## Result
- Router: `src/prediction_market_bot/decision_trees/router.py`, tests `tests/test_decision_router.py` (10 pass).
- Replay (DESCRIPTIVE): 164,354 situations, MLB and NFL only. FADE traffic is 0, also under a synthetic confident-model stress run. No tree gets traffic without measured evidence.
- RIDE settled view (n=2,661, 993 games, mean +0.0568 [+0.0424, +0.0718]) is in-sample against the same data that chose the cells. Not evidence.
- Limits: no NBA/NHL archive (GG-1330), news timing unmeasured (GG-1331), no momentum table (GG-1332), no shadow-ledger FADE replay (GG-1333), RIDE in-sample (GG-1334). RIDE evidence is a hard-coded stub of the W89.2 survivors; swap for 90.1's `ride.py` when it lands.
- Stage: filtering and routing factors are built and tested (aggregated/interpreted); none is applied against a market with an out-of-sample result.

## Operator line
Accept the routing doctrine as written (FADE only on measured skill; RIDE only on a net-positive table cell; same-side agreement goes to RIDE; opposite sides go to NO-BET; T3 as a FADE-only overlay; news timing excluded), or change it.

## Next
90.1's ride.py replaces the stub table; 90.3 supplies a momentum transition table; archive NBA/NHL series to replay them.
