# EXP-MLBSIM-001 result (W126.3) — REPORT, not a verdict
Engine: PA model (log5, shrunk, point-in-time) -> 9-inning sim (N=3000 draws/game) -> one joint board. Fit on PA before 2026-01-01; scored on 2,429 games of 2026. Source: `RESULTS_W126_3.json`.

**Calibration vs naive (Brier gain, 95% CI):** ML +0.0023 (-0.0007,+0.0053) · total -0.0001 · spread +0.0011 (+0.0006,+0.0016, only interval above 0) · team total -0.0003 · hits>=1 -0.0003 · hits>=2 +0.00004. Mean p vs mean y: ML 0.500/0.529, team total 0.335/0.368, hits>=1 0.640/0.606 (model under-prices home/team runs, over-prices hits).

**Vs Kalshi last pre-game mid (benchmark only; archive ~58 dates from 2026-08-04):** ML -0.0037 (n=753; W122.4 independent board was -0.0075) · total -0.0073 · spread -0.0019 · team total -0.0051. Model trails the market on all four.

**Stated limits:** no park / weather / home-field term; as-played lineup (small leak; live path uses the posted lineup); F3/F5/F7 not priced; KXMLBHIT market comparison not built (tickers need a player-name->batter-id bridge).

Routing read: engine price is one tree input. The home-run-environment and home-field terms are the next splits to test. Hypothesis "raw sim beats naive on every family" closed (EXP-MLBSIM-001, parked for R&D).
