# W118.1 MLB 2026 look-back - frozen spec (written BEFORE any result is computed)

Corpus: exp_output/PREGAME_SHADOW/settled/MLB_*.jsonl on the box (12 cells: GAME_TOTAL, MONEYLINE, RUN_LINE, TEAM_TOTAL x T1-T3),
pulled read-only 2026-11-18. Date range 2026-10-05..2026-10-29 = the 2026 POSTSEASON ONLY (22 settled games). The block's
"regular-season two-thirds / postseason as its own look" cannot be built: no regular-season game-market row exists (Kalshi
sports series were not listed before August 2026; the shadow ledger starts 10-05). Operator chose the postseason-only look-back
(2026-11-18, "Proceed with recommendation").
- Dedupe, cost, arms, leaf key, game-clustered 90% bootstrap (2000, seed 110): exactly as quant/retro_route (W110.5).
- Split: games ordered by start time; earliest 2/3 fit, latest 1/3 held out (the block's fraction). Fixed here, before any read.
- Routers: v2 (pooled + e-process, no sportsbook prior: none exists for MLB), v1 (per-leaf fit-window rule), ride every favourite.
- Held-out intervals are reported at any n but a cell is NOT scored/judged below 10 held-out games (retro_route MIN_TEST_GAMES).
- Every cell leaves with a routing: an arm (v2 earned) or NO BET with its hypothesis closed and parked for R&D. Provisional.
