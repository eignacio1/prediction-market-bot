# SESSION_HANDOFF W110.4 — same-game correlation from one engine (docs-only)

vision_pillar: PROOF (BREADTH groundwork)
gap_measure: B4 parlay families (groundwork only, no cell); joint calibration per leg-pair type
gap_delta: B4 unchanged (0 logging); 15 leg-pair types measured on 1,075 games / 59,014 pairs, 5 with a significant dependence gap
pattern_sweep: n/a (no defect fixed)
surface_delta: none (new pure functions + exploratory scripts; no running component)

**Status:** DONE (Parts A, B, C). **Ticket:** B-072, research complete; no cell opened.
**Code:** PR #478 merged, CI green on head efdd12d, squash 1a3df5f on main. Branch session/20261111T052931Z-w110-4-sgp-correlation.
**One line:** the engine joint beats independence on game-leg x team/player-points pairs, but misses same-player cross-stat dependence (points x threes real cov +0.091 vs engine +0.005) and gets teammate-points correlation the wrong sign (-0.016 vs +0.009), so it is worse than the naive product there.
**Part C:** Kalshi has KXMVENBASINGLEGAME same-game combo collections (196), none open today (last close 2026-10-08), settled last_price only, no quotes: no net-of-fee comparison possible. Needs: two-sided book, shared minutes/pace/usage latent in the player layer, market-line backtest, combo fee schedule, pre-registration.
**Stage per factor:** game-leg x team/player dependence = applied (research); same-player multi-stat and teammates = interpreted (gap measured).
**Caveats:** 2025-26 regular season only (2026-27 not pulled); lines at engine median; engine marginals biased low (109.3). Triples built, not scored.
**Operator decisions:** none. Candidate follow-up (not registered, no GG reserved): player layer shared latent.
**Result:** 12_EXPLORATORY/sgp_correlation/RESULT.md
