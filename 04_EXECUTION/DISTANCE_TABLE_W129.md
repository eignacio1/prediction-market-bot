# Distance table — Wave 129 (for the SW-10 handoff)

**Last reviewed:** 2026-11-26 (W129.5). Recomputed by `scripts/distance_to_optimum.py` in the W129.5 worktree at 2026-11-26T00:17Z;
D6 is the newest box `d6_read` (one source). E and P are box-only sources: the values below are the newest the box has returned,
**dated, and stale where marked**. The RUNNING SITREP is not edited here (it is the window's).

| Measure | Value | Source | As of |
|---|---|---|---|
| B1 cells logging / registered | 61 / 129 | `market_type_registry.py` | 2026-11-24 |
| B2 families with a logging cell | 20 / 26 | `market_type_registry.py` | 2026-11-24 |
| B3 bands with a logging cell | 4 of 5 (missing T5) | `market_type_registry.py` | 2026-11-24 |
| B4 props · parlay families logging | 5 · 0 | `market_type_registry.py` | 2026-11-24 |
| D1 factor classes conditioned on | personnel, team, venue only; **none** of matchup, weather, qualitative (per model: mlb_game_pregame_v1 personnel+team; nfl_pregame_v1 team; nfl_qb_challenger_v1 personnel+team; nhl_pregame_v1 personnel+team+venue; nba_pregame_v1 team; nba_player_points_v1 and _minutes_v1 personnel+team+venue) | `distance_to_optimum_d1_manifest.json` + model metadata | 2026-10-13 (stale 44 d) |
| D2 largest pre-game feature set | 17 (`nba_player_points_minutes_v1`), 0 qualitative | `models/nba_player_points_minutes_v1.json` | 2026-10-13 (stale) |
| D3 challengers ready | 5 (nfl_pregame team -> team+personnel: 1; unspecified: 4) | pre-registrations naming a challenger | 2026-11-26 |
| D4 engine stage | NFL data+engine+test · NBA data+test · NHL data+engine+test · MLB data+engine+test | `ARCHITECTURE_COMPONENTS.toml` | 2026-11-25 |
| D5a components with a tested scaffold | NFL 8/8 · NBA 8/8 · NHL 7/8 · MLB 4/8 | `ARCHITECTURE_COMPONENTS.toml` | 2026-11-25 |
| D5b factors agg / interp / **applied** | NFL 2/5/**18** of 26 · NBA 2/3/**11** of 17 · NHL 0/0/**8** of 12 · MLB stub | `SEATS/<sport>.toml` | 2026-11-25 |
| **D6 wired end to end** | **18 / 129** — nba 7/28 · nfl 4/32 · nhl 7/21 · mlb 0/42 · multi 0/6. Layers 1-7 (all cells): nba 15/12/12/9/7/8/8 · nfl 13/12/12/9/9/9/4 · nhl 9/9/9/9/7/8/8 · mlb 12/12/0/3/0/0/0 | box `d6_read` `results/20261125T0500Z_w1271_d6_read.md` | 2026-11-25T04:34Z |
| E1 demo orders filled / closed | t4_mlb 177 / 4316 = 4.1% · t1_mlb 85 / 485 = 17.5%. **STALE: 2026-11-12, MLB only.** Fresher partial (2026-11-24, `placement_fill_read`): 3,214 arm orders, 3,211 resolved, 3 pending | box `distance_read` 20261112T061333Z; `placement_fill_read` 20261124T0544Z | 11-12 / 11-24 |
| E2 P&L per filled bet | t4_mlb −$0.21 (n=177, 69 games, 95% CI [−0.40, −0.03]) · t1_mlb −$1.50 (n=83, CI [−3.67, 0.63]); ledger-priced, not fill-priced. **STALE 11-12** | same | 2026-11-12 |
| E3 win rate fills vs non-fills | t4_mlb 25.4% vs 48.3% · t1_mlb 28.9% vs 52.1% (adverse selection). **STALE 11-12** | same | 2026-11-12 |
| P1 cells at a scored look / logging | 20 / 49. **STALE 11-12** | same | 2026-11-12 |
| P2 verdicts issued | 20, routed (7 closed hypotheses, 0 closed arms, 0 closed cells). **STALE 11-12** | same | 2026-11-12 |
| P3 next look and modal outcome | UNAVAILABLE: engine projects no first-look date (as of 11-12) | same | 2026-11-12 |

## What must be refreshed
- E1-E3 and P1-P3 are 14 days old and cover MLB only. Requests `20261126T0031Z_w1295_distance_read` and
  `20261126T0030Z_w1295_d6_read` ride in the W129.5 PR; on merge the box runs them, and this table's E/P rows are re-quoted from
  the results.
- D1/D2 are 44 days old (model metadata); D1 says no live model conditions on matchup, weather or qualitative.

## D6: two numbers, one source
Before W129.5 `distance_to_optimum.py` printed a repo-static 0 and the box printed 18. 117 vs 129 registered was W125.3 adding 12
NOT_IMPLEMENTED combo cells (e9bf88b, 2026-11-23) while the box checkout lagged. The distance table now reports the newest box
`d6_read` (with its date) and prints the repo-static count beside it labelled static (layers 6-7 read 0 by construction).
Open gaps affecting D6: GG-2010, GG-2011, GG-2012.
