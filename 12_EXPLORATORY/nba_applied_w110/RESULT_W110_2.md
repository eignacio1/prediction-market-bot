# W110.2 / B-068 — NBA factors interpreted → applied, through the 109.1 decision tree

**Status: PARTIAL on the market comparison, DONE on the applied paths.** Measure: D5(b) NBA applied 5 → 10 of 17 (SEATS/nba.toml: B10, B12, B13, P1, P2 promoted; B11 stays interpreted — W83 null).
Code: `src/prediction_market_bot/nba_engine/factors_applied.py` (+ 11 known-answer tests), `build_frame.py`, `study_w110.py`. Raw numbers: `result_w110_2.json`, `result_w110_2_rows.csv.gz`.

## Protocol
W96.1 study_v3 rolling origin. Test seasons 2025 and 2026 (= 2025-26). K chosen on season T-1; parameters on T-3..T-1; Platt on training predictions; season T never seen. Rows at v1's strikes. Complete case on geometry + officials + usage + v3 base columns so every variant scores the **same games**: n = 2268 games (1141 + 1127), 47,628 rows. Delta = Brier(variant) − Brier(v2_core), negative = better; interval = game-cluster bootstrap 95%.

## Results (pooled, paired vs v2_core)
| group | ml | spread | total | team_total | ALL |
|---|---|---|---|---|---|
| geometry (B12) | +.00114 [−.00049,+.00280] | +.00046 [−.00040,+.00133] | −.00023 [−.00135,+.00096] | −.00012 [−.00081,+.00059] | +.00005 [−.00063,+.00078] |
| officials (B13, upper bound) | 0 (acts on total only) | 0 | −.00024 [−.00123,+.00074] | −.00035 [−.00090,+.00021] | −.00022 [−.00071,+.00027] |
| usage / lineup cross (B10) | +.00066 [−.00303,+.00423] | **−.00409 [−.00634,−.00190]** | −.00020 [−.00078,+.00035] | **−.00173 [−.00258,−.00087]** | **−.00181 [−.00287,−.00082]** |
| PAM (P1/P2, HINDSIGHT) | +.00244 [+.00008,+.00477] (worse) | −.00140 [−.00276,−.00000] | +.00021 [−.00011,+.00055] | −.00043 [−.00095,+.00009] | −.00037 [−.00098,+.00029] |
| geometry+usage (point-in-time set) | +.00129 [−.00249,+.00498] | −.00365 [−.00595,−.00136] | −.00044 [−.00168,+.00087] | −.00175 [−.00282,−.00064] | −.00175 [−.00296,−.00054] |
| all four | +.00132 [−.00233,+.00511] | −.00506 [−.00763,−.00262] | −.00051 [−.00213,+.00123] | −.00255 [−.00383,−.00121] | −.00248 [−.00387,−.00106] |

Level for scale: v2_core Brier ml .2067, spread .2368, total .2419, team_total .2309. The 2026-only split agrees in sign and size (usage spread −.00544 [−.00837,−.00234]). Gains sit in spread and team-total; nothing helps ml; nothing helps total beyond noise.

## Limits, stated plainly
1. **No market comparison for spread, total, team total.** Kalshi history for those families exists only for Oct 2026; only KXNBAGAME has 2025-26 quotes (n=397, 109.1). These scores are against realized outcomes. A Brier gain over v2_core is **not** an edge over the Kalshi price, and the ml family, the only one comparable, got no better. 109.1's base tree already lost to the market on ml (market .1529 vs tree .1745). I did not rerun the ml market comparison with the new factors; the ml deltas are positive, so it cannot close that gap.
2. **PAM is hindsight.** All 100 PAM records carry recorded_at 2026-05-28, so every 2025-26 flag is look-ahead and the PAM row is an upper bound, not a point-in-time result. Forward 2026-27 use is point-in-time valid. Only ~3,900 of 14,168 games have any PAM player; the rest are 0.
3. **Officials are an upper bound**: crew assignment time is unpublished (GG-1390); the tree only lets the class act from 9h before tip (T2/T3).
4. Multiple comparisons: 7 variants × 4 families, no correction. Spread usage and team-total usage survive any reasonable correction; PAM spread (upper bound −.00000) does not.
5. Surrogate player-game table for usage (minutes × 60, `p_play` from status-rate map); not the live availability feed.

## Stage per factor (ADR-0075; "applied" = a tested path from the fact to a price, whatever the result)
| factor | stage before → after | result |
|---|---|---|
| B10 lineup cross / usage | interpreted → **applied** | real, spread + team total, realized-outcome scoring only |
| B12 geometry | interpreted → **applied** | null |
| B13 officials | interpreted → **applied** | null (upper bound) |
| P1/P2 PAM archetype, modifier flags | interpreted → **applied** | spread small, ml worse; hindsight |
| B11 absorber profile | interpreted (unchanged) | W83 null |

## Granularity index (five parts)
- **Usage:** split = share of strictly-prior 10-team-game usage (FGA + .44 FTA + TOV) missing, and creator-out share; rank = vs the player's own prior shares; cross = creator out × absorber depth (profile cross not built); market map = spread, team total; application = `FA.price` through the 109.1 filter + tree.
- **Geometry:** split = miles, last-4 density, road run, altitude gain; rank = vs history at the same point; cross = visitor altitude gain × back-to-back; market map = total (altitude), margin; application = tree class `venue`, T1.
- **Officials:** split = crew pace/FTA/foul deviation, shrunk, prior games only; map = total, team total; application = tree class `officials`, T2/T3.
- **PAM:** split = creator-archetype weight × expected minutes share, modifier count; map = spread/team total; application = class `qualitative`, T1.

## Operator decisions: none.
