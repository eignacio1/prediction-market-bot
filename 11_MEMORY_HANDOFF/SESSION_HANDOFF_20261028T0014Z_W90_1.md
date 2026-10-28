# SESSION HANDOFF — W90.1 (2026-10-28T00:14:43Z) — PARTIAL
vision_pillar: PROOF (+ DEPTH planned)
gap_measure: families testable out of sample; candidates tested out of sample; D5(a) decision_trees
gap_delta: testable families MLB+NFL -> +NBA/NHL game-market data in (source: results_W90_1.md); candidates tested out of sample 0 -> 0 (1 of 1,850 cells testable); D5(a) unchanged (no ride.py)
pattern_sweep: LA/LAR alias collision fixed and tested (NFL ALIAS); other sports' ALIAS checked by the same known-answer pattern; write-fence scanner gap registered GG-1291; safe_out used for all scan outputs
surface_delta: none (no new running component; exploratory scripts only)
gg_touched: GG-1290 resolved; GG-1291, GG-1292, GG-1293 open

## Done
PR #349 merged 2757a20, PR #352 merged be44377 (both CI green on head SHA; no t4-mlb restart). Candles for spread/total/team-total fetched (NBA, NHL, NFL). Hold-out scan: 0 candidates, underpowered.

## Next undone
1. Longer candle fetch per family, then rerun holdout_scan.py (GG-1292).
2. MLB re-tests, GG-1253, props candles (GG-1293).
3. Part B: decision_trees/ride.py + cells table + tests (table empty until survivors exist).

Operator line: no ride survivors held out of sample; Wave 91 has nothing to pre-register as a ride tree yet.
