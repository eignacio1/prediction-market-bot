---
session: W77.2
status: DONE
vision_pillar: DEPTH
gap_measure: D5(b) NFL factors with market-side verdict
gap_delta: 0 -> 4 (team/QB base, F5/F6, F8, engine); power reported for all four families
pattern_sweep: n/a (no defect fixed)
surface_delta: 0
---
# W77.2 handoff — DONE
Branch session/20261016T004638Z-w77-2-nfl-market-tests; PR #272 squash-merged (81629b1), CI green on the final commit (first run failed the exploratory-isolation scan on `.to_json()`/`.replace()` — fixed, re-run green).
Results: `12_EXPLORATORY/nfl_engine/market_tests/results.md` (+ closing_line/power/timing .json). No registry/runner/ledger/cron/model change; no running component added.

- Power: fully-real F8 detected 19.8%/21.4%/20.6% (ml/spread/total); F5/F6 3–5% (floor). "No gain" was uninformative.
- Closing line: F8 b = 0.67 [0.45,0.87] spread, 0.34 [0.16,0.51] total, 0.094 [0.065,0.120] ml-logit; F5/F6 CIs span 0 and 1.
- Timing: inactives window slope −0.0009 [−0.0023,+0.0004] prob/pt (n=145) — no late drift. Friday-report window NOT testable (candles start ≈ report); no 2026 candles; spread/total/team-total series not fetched.
- Verdicts: base & engine REAL-AND-PRICED; F8 REAL-AND-PRICED (partly, remainder unproven); F5/F6 INVISIBLE. Stage per factor: all applied.
- Recommendation (not decision): stop adding game-market factors without a "thinner edge" pre-registration; cheapest next evidence = fetch Wed–Sun KXNFLGAME candles and test the Friday-report window; thinner markets need their own Kalshi series fetch first.
Operator decisions: (1) approve the pre-report candle fetch; (2) game-market factors vs thinner markets.
Caveats: normal-approximation injection; ko−90min approximated; terms.json (gitignored, regenerable via extract_terms.py) not committed.
