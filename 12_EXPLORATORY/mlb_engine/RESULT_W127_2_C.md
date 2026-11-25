# W127.2 Part C: engine price as a layer-1 input on the 2026 MLB look-back corpus (descriptive, no verdict)
Last reviewed: 2026-11-25. Label: DESCRIPTIVE. 2026 was the engine's held-out year and EXP-037 counts 2026 rows only; no look here is judged.

**What was asked:** score the existing MLB leaves (`mlb_2026_lookback.json`, key `sport|market_type|band|favprice_bin|move_bin`) per leaf with and
without the engine price: net after costs per arm, partial pooling, `quant/variance.py`.

**What the data allows: 0 of 22 corpus games can carry an engine price.**
- The look-back corpus is the 2026 postseason only: 22 settled games, 2026-10-05..10-28, 8,840 shadow rows (SPEC.md).
- The engine prices a game from the pitch store: point-in-time PA history plus that game's nine-man lineups and starters, and all of it comes from Savant pitch rows. The store ends 2026-09-27.
- Savant returns a header-only file for every October 2026 day under both the regular-season filter (`hfGT=R`) and a postseason filter (`F|D|L|W`), checked 2026-11-24 for 10-14 and 30 days of 09-28..10-30. The 30 empty day-files were removed from `~/mlb_store/raw`, so a later fetch retries them.
- So no leaf has an engine-price split to score. Scoring with a synthetic or imputed price would be a made-up number, so none was produced.

**What is on file instead (cited, not re-scored):** EXP-MLBSIM-001 `RESULTS_W126_3.json` market block, regular season 2026 with archive prices from 2026-08-04: moneyline n=753 Brier model 0.2409 vs market 0.2372 (gain vs market -0.0037, interval -0.0075 to +0.0001); total n=7,905 model 0.1864 vs market 0.1791. Those are model-vs-market and are not the verdict (ADR-0077); the engine price is one tree input.
Hypothesis "raw sim beats the market mid" closed (EXP-MLBSIM-001, parked for R&D). No cell, market or arm closes.

**Gross, round cost, net:** not computed for the engine split, since no leaf row has the input. The leaf-map numbers stay as `mlb_lookback/RESULT.md` states them.

## What a 2027 forward test needs (name it before the first 2027 row)
**EXP-MLBENGINE-SPLIT-2027** (to be written and committed by the operator-approved window before opening day; not frozen here):
- Input: `engine_gap = engine p_yes - market mid` from `mlb_engine/forecaster.py`, logged on every shadow row at each of T1-T3 (needs the board priced from the day's confirmed lineups, so a box job that fetches Savant through the prior day; build, not run; needs a named `*_install`).
- Split: `engine_gap` terciles added as a 6th leaf-key field under each existing leaf; arm per leaf chosen by router v2 on 2027 rows only.
- Score: per leaf net after the exact Kalshi fee at the ask, held to settlement, vs RIDE, partial pooling (`quant/variance.py`), judged n as in `mlb_lookback/PREREG_2027.md` (10+ held-out games, weekly looks, P(net>0) >= 0.90 and e-process >= 1/alpha, alpha 0.10).
- Out of scope: pooling 2026 rows in as evidence; any Kelly above 0; any order before a leaf is earned.
