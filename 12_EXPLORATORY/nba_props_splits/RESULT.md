# EXP-NBAPROPS-001 — result (W121.2)

**Last reviewed:** 2026-11-20. Pre-registration: `PREREG.md` (commit ec39007, frozen before any outcome was read).

## What was scored
Layer-1 market state (price, move, ladder gap, time to tip) x player point-in-time splits (minutes trend, rest, opponent shot-zone
defence, pace) on NBA prop rows. Leaf = (sport, market_type, band, fav-price bin, move bin). Fit on the earliest 70% of games, scored on
the latest 30%, game-clustered. Thin leaf (fit rows < 60 or fit games < 20) routes to NO_BET.

| Count | Value |
|---|---|
| Leaves | 143 |
| Split cells scored | 1206 |
| BH-tested (q = 0.10) | 42 |
| Kept (not thin, arm != NO_BET, >= 10 held-out games, held-out mean net > 0) | 14 |
| Earned (kept and BH-significant) | 1 (POINTS only) |

Non-kept splits are logged with their verdict (stump rule). Disagreeing kept splits change nothing (conflict rule).
Hypotheses that lost are "hypothesis closed (EXP-NBAPROPS-001, parked for R&D)"; no cell, market or arm closes.

## Live coverage (what can actually fire)
- The live prop runner covers REB, AST and 3PT: 9 shadow cells. Points is dark and has no engine model p, so the points cell is unwired
  for that one cause; the only earned split is points-only and cannot fire live.
- Kept splits that can fire live: 3 on assists, 2 on threes, 1 on rebounds, all unearned.
- Candidate map `nba_props` is shadow only, under `PM_CANDIDATE_ARMS` (off-switch `off`). v1 router output is byte-identical (tested).

## Deviations from PREREG (disclosed)
1. Tip time is estimated from the last price snapshot, not a schedule feed.
2. P1 as implemented marks most leaves "flat".
3. P2 is unknown for REB and AST.
4. Bootstrap used 2000 draws against 10,000 in the PREREG.
5. Settled outcomes and ESPN box scores came from public GETs, not box data.
6. Live move bin uses the previous logged mid; the scored move bin used a snapshot >= 6 h earlier. The two differ, so live leaf
   assignment can differ from the scored one.

## Not yet measured
D6 for prop cells needs rows produced on the box after deploy and one slate; `scripts/d6_read.py` was not runnable in this session.
