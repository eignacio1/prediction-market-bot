# SESSION_HANDOFF — W93.3 NBA engine: one model prices the whole board

Status: PARTIAL | PR #363 merged (squash cfdc423), CI green | Deploy: library only, no running component, t4-mlb unaffected (no restart required)

vision_pillar: DEPTH (+PROOF)
gap_measure: D4 NBA; markets priced from one joint distribution; Brier vs Kalshi
gap_delta: D4 NBA data layer -> whole board priced from one engine (scaffold, tested) (tests/test_nba_engine.py, part_a.json); markets from one distribution 0 -> 4 (moneyline, spread, total, team total); Brier vs Kalshi n=0 -> n=0 (no settlements)
pattern_sweep: n/a (no defect fixed) (study scripts were routed through safe_out() before first merge to satisfy tests/test_exploratory_isolation.py)
surface_delta: none (library package + exploratory scripts; no cron, service or RUNTIME_REGISTRY entry)

## Result
Simulated joint score distribution; beats its Gaussian twin on held-out seasons 2021-26 (n=7,230, dBrier -0.0004, interval [-0.00054, -0.00025]). Moneyline underconfident (slope 1.83), same as Gaussian (shared shrunk ratings). Engine over-states score correlation by ~0.06-0.09. Vs Kalshi: 3 archive snapshots, 33 games, 0 settled, no NBA candles: paired Brier and skill weight w are unestimable. Implied-distribution comparison is descriptive only. **No edge claim.** Full: `12_EXPLORATORY/nba_board/results_W93_3.md`.

## Factor stages
B1/B2/B9 applied (in the means); B3 interpreted, B7 aggregated/interpreted (not in means); 93.1 availability and 93.2 geometry pending.

## Gaps registered
GG-1393 (no 2026-27 schedule/team_box), GG-1394 (no NBA candles), GG-1395 (too few snapshots, 0 settlements).

## Next
Re-run `study_b.py` when GG-1393/1395 clear; plug 93.1/93.2 into the means; consider correlation recalibration. Operator decisions: none.
