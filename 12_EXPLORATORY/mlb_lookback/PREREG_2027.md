# MLB 2027 forward test — pre-registration (frozen before the first 2027 row)
Last reviewed: 2026-11-18. Map: `leaf_maps/mlb_2026_lookback.json` (sha pinned in tests/test_mlb_lookback_map_w118.py); not the router default.
- **What is tested:** per cell (12 game cells, T1-T3), arm net per row after the exact Kalshi fee at the ask, held to settlement, vs RIDE.
- **Judged n:** a cell is judged only at 10+ held-out games under the W110.5 rule (70/30 by game, 20 fit games / 60 fit rows). The calendar
  (`results.json` -> `power_calendar_2027`, ~90 games/week assumed, ledger coverage to verify in April) puts the first earned arm if the true
  net is +0.04/row at: game / team totals 2-3 weeks, run line 6, moneyline ~34. At +0.02 it is 5-10 weeks (totals), 21-23 (run line), never inside a season (moneyline). The weeks are a floor.
- **Look rule:** weekly looks anchored at 2026-01-06, router v2 (P(net>0) >= 0.90 and path-averaged e-process >= 1/alpha, alpha 0.10). No peeking between looks; no score read below judged n.
- **Opening day:** every cell starts NO BET (shadow rows log, no orders, Kelly 0). A leaf arms only when v2 earns it on 2027 rows; the 2026 postseason map is a prior for nothing. The 2026 postseason is not pooled in as evidence.
- **Hypotheses parked for R&D (not closed cells):** FADE and MODEL_FADE on every cell (negative on the look-back); RIDE on TEAM_TOTAL T2/T3 is the lead to test first.
- **Out of scope:** regular-season game-market rows before 2026-10-05 do not exist in the shadow ledger (logged as a gap).
