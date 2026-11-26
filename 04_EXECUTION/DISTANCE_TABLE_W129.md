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
| E1 demo orders filled / closed | t4_mlb 177 / 4316 = 4.1% · t1_mlb 85 / 485 = 17.5%. **STALE: MLB only; box ledgers as of 2026-10-29 (re-read 11-26).** Fresher partial (2026-11-24, `placement_fill_read`): 3,214 arm orders, 3,211 resolved, 3 pending | box `distance_read` 20261112T061333Z; `placement_fill_read` 20261124T0544Z | 11-12 / 11-24 |
| E2 P&L per filled bet | t4_mlb −$0.21 (n=177, 69 games, 95% CI [−0.40, −0.03]) · t1_mlb −$1.50 (n=83, CI [−3.67, 0.63]); ledger-priced, not fill-priced. **STALE (box ledger as of 10-29, MLB only)** | same | 2026-11-12 |
| E3 win rate fills vs non-fills | t4_mlb 25.4% vs 48.3% · t1_mlb 28.9% vs 52.1% (adverse selection). **STALE (box ledger as of 10-29, MLB only)** | same | 2026-11-12 |
| P1 cells at a scored look / logging | 25 / 49 | box `distance_read` `results/20261126T0031Z_w1295_distance_read.md` (engine_20261125T135336Z.json) | 2026-11-25T13:49Z |
| P2 verdicts issued | 25, routed (12 closed hypotheses, 0 closed arms, 0 closed cells) | same | 2026-11-25T13:49Z |
| P3 next look and modal outcome | UNAVAILABLE: engine projects no first-look date | same | 2026-11-25T13:49Z |

## What must be refreshed
- Box results landed 2026-11-26: `distance_read` (exit 0, ran 00:43Z) re-quoted P1-P3 above and confirms D6 18 / 129 from the same
  11-25T04:34Z read. `d6_read` (ran 00:43Z) **timed out: exit 124, empty output**, so there is no newer D6; the 11-25 read stands.
  Not yet diagnosed whether the timeout is a box-load or a script-runtime problem; re-request before relying on D6 as fresher.
- E1-E3 are MLB only and read ledgers last written 2026-10-29 (the box re-read did not move them). NBA/NFL/NHL demo fills have no
  E1-E3 line; the ADR-0072 forward-test log is the only place they show. Its latest line (2026-11-05) reads
  `TRIPPED treatment_markout_30m_worse_than_control`.
- D1/D2 are 44 days old; the box's D2 names `mlb_player_hits_t1` (18, 0 qualitative), the repo-side row above names an NBA model (17).
  Two sources disagree; unresolved here.

## D6: two numbers, one source
Before W129.5 `distance_to_optimum.py` printed a repo-static 0 and the box printed 18. 117 vs 129 registered was W125.3 adding 12
NOT_IMPLEMENTED combo cells (e9bf88b, 2026-11-23) while the box checkout lagged. The distance table now reports the newest box
`d6_read` (with its date) and prints the repo-static count beside it labelled static (layers 6-7 read 0 by construction).
Open gaps affecting D6: GG-2010, GG-2011, GG-2012.
