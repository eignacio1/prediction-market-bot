# W98.1 Part B — NHL engine v2 (end-of-game state model), held out 2023–2025

Exploratory; merged model unchanged. v2 = merged rates, first 55:00 at the merged rate scaled to keep expected goals, then two late windows (55–58, 58–60) whose goal rates depend on the score state (down 2+/1, tied, up 1/2+) fit on training seasons only (`nhl_engine/late_game.py`). Empty-net goals come from our event store (goalie flag 0): 0.37 per game (0.33/0.35/0.41/0.39 by season 2022–25). Table validated: late-table goal counts equal regulation goals for 5,572/5,572 games. R-095 had no STATUS; not waited on.
Applies when: regular-season scoring where the end-of-game state matters; not playoff OT.

Held-out Brier, 3,924 games (2023–25), game-clustered bootstrap 95% CI on the paired difference:

| Family | merged | v2 | climatology | v2 − merged | v2 − clim |
|---|---|---|---|---|---|
| ML | 0.2395 | 0.2395 | 0.2486 | −0.00002 [−0.00021, 0.00017] | −0.0091 [−0.0113, −0.0067] |
| SPREAD_HOME | 0.1973 | 0.1949 | 0.1981 | **−0.00247 [−0.00311, −0.00178]** | −0.0032 [−0.0050, −0.0014] |
| TEAMTOTAL_AWAY | 0.2348 | 0.2350 | 0.2386 | +0.00019 [−0.00002, 0.00041] | −0.0037 [−0.0059, −0.0016] |
| TEAMTOTAL_HOME | 0.2327 | 0.2325 | 0.2377 | −0.00019 [−0.00038, 0.00000] | −0.0052 [−0.0073, −0.0032] |
| TOTAL | 0.2210 | 0.2211 | 0.2213 | +0.00006 [−0.00007, 0.00021] | −0.0002 [−0.0020, 0.0016] |

Total-goals bias (predicted − actual settled total): merged −0.166/−0.123/−0.051; v2 −0.163/−0.122/−0.053 (2023/24/25). **The late-game state does not carry the totals under-prediction**: bias unchanged, TOTAL Brier unchanged and still not distinguishable from climatology. (A first version that did not preserve expected goals overshot the bias to +0.07..+0.21; fixed by `early_scale`.) Real gain is confined to the spread family (small, CI excludes 0).

EXP-046: **not frozen.** Engine v2 leaves totals at climatology, and the merged engine already trailed Kalshi on all four families (W97.4, 33 games); v2 does not change totals, so nothing earns a forward test. The 2026 Kalshi descriptive rerun was not repeated (no v2 totals movement to compare). Candidate cause still open: OT/SO credit and tie handling, not empty nets.
