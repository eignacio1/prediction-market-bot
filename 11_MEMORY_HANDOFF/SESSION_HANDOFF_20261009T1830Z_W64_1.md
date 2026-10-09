# SESSION HANDOFF — W64.1 NFL deep challenger (QB-shrunk) — 2026-10-09

**Status:** DONE (Parts A + B) | branch session/20261009T173216Z-w64-1-nfl-qb-challenger | Part A merged PR #205 (CI green); Part B PR pending in this push
**Result:** challenger (frozen recipe + EB team rates + QB-shrunk EPA) beats frozen EXP-037 in backtest: Brier -0.0027, 99.375% CI [-0.0050, -0.0006], 6/7 seasons (2025 worse). Gain is all mechanism 1 (QB); EB does nothing. Neither model beats the 2025 Kalshi mid (n=182). Scoped to this feature set and 2019-2025.
**vision_pillar:** DEPTH
**gap_measure:** D3 (pre-registered challengers ready); D1 (nfl_pregame)
**gap_delta:** D3 0 -> 1 (`scripts/distance_to_optimum.py`, D3 line: "1 (nfl_pregame (team -> team+personnel): 1)"). D1 unchanged: nfl_pregame_v1 still "team" because the challenger is PROPOSED, not a live model; it moves only if the operator accepts and it ships.
**MEASURE MOVED:** yes, D3.
**t4-mlb restart:** Part A push: not_needed (no t4-mlb import changed). Part B is docs/12_EXPLORATORY only: expected not_needed.
**Operator decisions:** accept or reject `12_EXPLORATORY/NFL_QB_SHRUNK_CHALLENGER_PREREGISTRATION_2026-10-09.md` (PROPOSED). Judged n ~984 games (~3.6 seasons) vs frozen; market comparison cannot be judged at feasible n.
**Notes:** step-0 finding: VPS has NFL_FIRST_LOOK_EXPECTATIONS.md; 63.3's UNAVAILABLE was deploy timing. Next mechanism: injury-report QB-only (needs point-in-time snapshots). GG-548/549 not used.
