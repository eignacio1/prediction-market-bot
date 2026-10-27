# SESSION HANDOFF — W89.2 (longshot bias and calibration of Kalshi sports prices)

vision_pillar: PROOF + DEPTH
gap_measure: Kalshi sports price families calibration-tested with BH; market-level adjustments surviving net of fee
gap_delta: families tested 0 -> 14 (1,258 testable cells, BH q=0.10 family-wise); surviving candidates 0 -> 11 cell rows (3 recommended for pre-registration; 0 from Part B). Source: 12_EXPLORATORY/longshot_bias/out/summary.json (CSVs local, gitignored), results_W89.md, 2026-10-27
pattern_sweep: n/a (no defect fixed). The exploratory write fence (tests/test_exploratory_isolation.py) failed on this block's own new code and was fixed in PR #345 by routing writes through _fence.safe_out; no other instance found.
surface_delta: 0 (nothing live; no cron, service or workflow added)

## Result
PR #345 merged (squash f50f49c), CI green on the 2nd run; Test Suite on main for f50f49c green. Docs follow-up 5f10c41.
- Part A: 73,662 settled tickers; 1,258 testable cells; 66 BH-flagged; 29 pass Bonferroni; 53 of 66 have net_lo <= 0; 11 survive (BH + split-half sign + net-of-fee lower bound > 0 + not NFL D0).
- Part B: 40 testable cells; every net negative; 0 survivors (descriptive only).
- Candidates for pre-registration (in-sample, not trades): KXMLBHIT T0-2h 20-25c YES; KXMLBF5TOTAL T6-24h 90-95c YES; KXNFLTOTAL D1 5-10c NO.

## Deploy / t4-mlb
No Deploy job ran for f50f49c (main run 40450763458 has only the `test` job). Nothing here runs live; t4-mlb untouched, no restart decision needed.

## Caveats
In-sample, no hold-out (GG-1254); MLB HHMM read as ET (GG-1253); NFL date-only tickers so D0 excluded (GG-1252); depth proxied by spread, not size; archive lacks NHL/NBA/parlays (GG-1250); candle history partial (GG-1251).

## Registered
GG-1250..GG-1254 (T-1250..T-1252 claimed, none opened). Stage per factor: market-price calibration aggregated and interpreted, not applied.

## Operator decision
Pre-register the 3 candidates above, or not.
