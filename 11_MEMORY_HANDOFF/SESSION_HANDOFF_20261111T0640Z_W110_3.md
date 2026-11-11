# SESSION_HANDOFF W110.3 (B-071) - every registered cell routed

vision_pillar: DEPTH (BREADTH touched)
gap_measure: D5(a) decision trees per sport; cells routed / registered
gap_delta: routed 27 of 117 registered cells (source: decision_trees/coverage.py at c57a496, 2026-11-11). Shadow rows from the 6 shadow scripts now log the router decision. This is logging coverage, not new orders.
pattern_sweep: n/a (no defect fixed)
surface_delta: none. No new running component; the `router` field on shadow rows is additive. RUNTIME_REGISTRY needs no entry.

Status: DONE (B-071 for this block; ROLLING_BACKLOG.json not edited per rules). PR #476, CI green, merged c57a496.

## Results
- A: 117 cells (64 pre-game, 53 in-play). Routed 27: NHL 9/9, NFL 9/13, NBA 9/24, MLB 0/18 pre-game.
- B: `decision_trees/shadow_route.py` + additive call in `pregame_shadow/runner.py::run_once`. Reachable branches today: RIDE, POT_OF_GOLD, NO_BET. FADE and MOMENTUM stay pending evidence (shadow rows have no skill record or 1h move). Tests: 4 new, shadow/router suites green.
- C: 14 archive days (2026-10-29..11-11), 25,263 decisions, 100% NO_BET, no RIDE/POT_OF_GOLD. Gross/net per branch: n=0, not computable. Reasons: date_only_game_day 10,673; price outside pot-of-gold buckets 9,908; no longshot cell 1,732; no two-sided book 1,946; started/unparseable 897; IN_SAMPLE not orderable ~107. Null result. Data-epoch rule (NO-side fills before 2026-11-06T01:03:42Z) does not apply: a book replay uses no fills.

## Stage per factor
No factor class advanced; this block routes, it does not add factors.

## Flags
1. PERMISSION TENSION: `pregame_shadow/runner.py` is nominally read-only; edited minimally per Part B's explicit instruction. Reviewer should confirm.
2. Tier mismatch: NFL ride cells use date-only tiers (D0/D1/D2+); the shadow hook uses hours-based tiers.
3. Cell tables bound coverage: NBA/NHL/NFL game families have no orderable ride/longshot cells. MLB game families are outside the board scan, so they route NO_BET with an explicit reason.
4. Pre-existing env issue: tests/test_approval_path_invariants.py fails collection (pyarrow needs NumPy 2, found 1.26.4). Not mine; not registered here.
5. Branch history was rebased and force-pushed with lease (own branch) before merge.
6. Session-start Steps 1-4 / Q1-Q7 were not formally pasted; the hook scan showed 1 comment-only stub hit (quant/inplay_nhl.py:37), 253 open of 578 GGs, no duplicate GG ids (cached scan).

Operator decisions: none.
