# Box task `distance_read` — 20261021T0439Z_b_distance_read

- request: `04_EXECUTION/BOX_TASKS/requests/20261021T0439Z_b_distance_read.toml`
- note: Wave 81 close: window verification
- ran: 2026-10-21T04:40:25Z on root@157.230.91.33:/opt/prediction-market-bot
- exit code: 0
- command (allowlisted, scripts/box_tasks.py): `PYTHONPATH=src:. venv/bin/python scripts/distance_to_optimum.py; echo; echo '--- forward-test report (tail)'; tail -n 60 logs/demo_fill_forward_report.log 2>&1`

```
DISTANCE TO OPTIMUM — computed 2026-10-21T04:40:25Z (alarm-only; values only from sources, never typed)
  B1  48 / 107
      source: src/prediction_market_bot/c5_execution/market_type_registry.py · as of 2026-10-13T00:16:34Z
  B2  17 / 18
      source: src/prediction_market_bot/c5_execution/market_type_registry.py · as of 2026-10-13T00:16:34Z
  B3  4 of 5 (missing: T5)
      source: src/prediction_market_bot/c5_execution/market_type_registry.py · as of 2026-10-13T00:16:34Z
  B4  2 · 0
      source: src/prediction_market_bot/c5_execution/market_type_registry.py · as of 2026-10-13T00:16:34Z
  D1  mlb_player_hits_t1: personnel, team, venue; mlb_game_pregame_v1: personnel, team; nfl_pregame_v1: team; nfl_qb_challenger_v1: personnel, team; nhl_pregame_v1: personnel, team, venue; nba_pregame_v1: team; nba_player_points_v1: personnel, team, venue; nba_player_points_minutes_v1: personnel, team, venue. Classes no live model conditions on: matchup, weather, qualitative
      source: scripts/distance_to_optimum_d1_manifest.json + model metadata · as of 2026-10-13T00:26:44Z
  D2  18 (mlb_player_hits_t1, 0 qualitative)
      source: models/mlb_v1_model_meta.json · as of 2026-06-24T19:11:31Z
  D3  1 (nfl_pregame (team -> team+personnel): 1)
      source: 12_EXPLORATORY/ + 03_DECISIONS/ (*challenger*.md with Status PROPOSED|ACCEPTED) · as of 2026-10-11T02:43:23Z
  D4  NFL: data layer + engine scaffold · NBA: data layer · NHL: none · MLB: none
      source: 02_ARCHITECTURE_DESIGN/ARCHITECTURE_COMPONENTS.toml [[engine]] · as of 2026-10-20T05:04:50Z
  D5a NFL 6/8 (decision_trees, filtering_mechanisms, cluster_designs, cross_reference_compatibility, structural_tensions, seat_interface) · NBA 3/8 (cluster_designs, structural_tensions, seat_interface) · NHL 0/8 · MLB 0/8
      source: 02_ARCHITECTURE_DESIGN/ARCHITECTURE_COMPONENTS.toml [[component]] · as of 2026-10-20T05:04:50Z
  D5b NFL 4 aggregated/2 interpreted/8 applied of 17 · NBA 0 aggregated/3 interpreted/5 applied of 10 · NHL stub (no factors) · MLB stub (no factors)
      source: 02_ARCHITECTURE_DESIGN/SEATS/<sport>.toml [[factor]] · as of 2026-10-20T05:34:36Z
  E1  t4_mlb: 177 / 4316 = 4.1% · t1_mlb: 85 / 485 = 17.5%
      source: logs/paper_portfolio_mlb_t4.json + logs/t4_mlb_fill_status.jsonl; logs/paper_portfolio_mlb.json + logs/t1_mlb_fill_status.jsonl · as of 2026-10-20T02:58:16Z
  E2  t4_mlb: $-0.21 (n=177, 69 games, 95% CI [-0.40, -0.03]; ledger-priced, not fill-priced) · t1_mlb: $-1.50 (n=83, 57 games, 95% CI [-3.67, 0.63]; ledger-priced, not fill-priced)
      source: logs/paper_portfolio_mlb_t4.json + logs/t4_mlb_fill_status.jsonl; logs/paper_portfolio_mlb.json + logs/t1_mlb_fill_status.jsonl · as of 2026-10-20T02:58:16Z
  E3  t4_mlb: fills 25.4% (n=177) vs non-fills 48.3% (n=4139) · t1_mlb: fills 28.9% (n=83) vs non-fills 52.1% (n=386)
      source: logs/paper_portfolio_mlb_t4.json + logs/t4_mlb_fill_status.jsonl; logs/paper_portfolio_mlb.json + logs/t1_mlb_fill_status.jsonl · as of 2026-10-20T02:58:16Z
  P1  0 / 49
      source: exp_output/CALIBRATION/engine_20261020T134947Z.json · as of 2026-10-20T13:49:02Z
  P2  0
      source: exp_output/CALIBRATION/engine_20261020T134947Z.json · as of 2026-10-20T13:49:02Z
  P3  2026-11-02 (12 cell(s), e.g. NFL_NFL_GAME_TOTAL_T1); pre-registered modal outcome (12_EXPLORATORY/NFL_FIRST_LOOK_EXPECTATIONS.md): KEEP ACCRUING ~91%
      source: exp_output/CALIBRATION/engine_20261020T134947Z.json · as of 2026-10-20T13:49:02Z

--- forward-test report (tail)
FORWARD-TEST (ADR-0072) 2026-10-13T11:25Z | paper/MLB: orders=22 fills=5 s-p=+0.07; paper/UNKNOWN: orders=0 fills=0 s-p=n/a; shadow/MLB: orders=363 fills=75 s-p=-0.06; shadow/NFL: orders=1135 fills=231 s-p=+0.40 | turn-off: none tripped
FORWARD-TEST (ADR-0072) 2026-10-14T11:25Z | paper/MLB: orders=30 fills=5 s-p=+0.07; paper/UNKNOWN: orders=0 fills=0 s-p=n/a; shadow/MLB: orders=29 fills=5 s-p=n/a; shadow/MLB: orders=383 fills=77 s-p=-0.06; shadow/NFL: orders=28 fills=5 s-p=n/a; shadow/NFL: orders=1163 fills=234 s-p=+0.40; shadow/NHL: orders=54 fills=29 s-p=+0.12; shadow/NHL: orders=48 fills=1 s-p=-0.47 | turn-off: TRIPPED cancel_fail_rate_gt_10pct_in_a_day
FORWARD-TEST (ADR-0072) 2026-10-15T11:25Z | paper/MLB: orders=32 fills=5 s-p=+0.07; paper/UNKNOWN: orders=0 fills=0 s-p=n/a; shadow/MLB: orders=77 fills=6 s-p=+0.35; shadow/MLB: orders=431 fills=77 s-p=-0.04; shadow/NFL: orders=51 fills=18 s-p=n/a; shadow/NFL: orders=1192 fills=236 s-p=+0.40; shadow/NHL: orders=54 fills=29 s-p=+0.12; shadow/NHL: orders=48 fills=1 s-p=-0.47 | turn-off: none tripped
FORWARD-TEST (ADR-0072) 2026-10-16T11:25Z | paper/MLB: orders=32 fills=5 s-p=+0.07; paper/UNKNOWN: orders=0 fills=0 s-p=n/a; shadow/MLB: orders=107 fills=8 s-p=+0.18; shadow/MLB: orders=452 fills=77 s-p=-0.04; shadow/NFL: orders=112 fills=44 s-p=-0.15; shadow/NFL: orders=1245 fills=237 s-p=+0.39; shadow/NHL: orders=256 fills=54 s-p=+0.14; shadow/NHL: orders=288 fills=16 s-p=+0.24 | turn-off: none tripped
FORWARD-TEST (ADR-0072) 2026-10-17T11:25Z | paper/MLB: orders=32 fills=5 s-p=+0.07; paper/UNKNOWN: orders=0 fills=0 s-p=n/a; shadow/MLB: orders=107 fills=8 s-p=+0.18; shadow/MLB: orders=452 fills=77 s-p=-0.04; shadow/NFL: orders=961 fills=306 s-p=-0.15; shadow/NFL: orders=2092 fills=336 s-p=+0.39; shadow/NHL: orders=443 fills=195 s-p=+0.07; shadow/NHL: orders=455 fills=24 s-p=+0.36 | turn-off: none tripped
FORWARD-TEST (ADR-0072) 2026-10-18T11:25Z | paper/MLB: orders=32 fills=5 s-p=+0.07; paper/UNKNOWN: orders=0 fills=0 s-p=n/a; shadow/MLB: orders=107 fills=8 s-p=+0.18; shadow/MLB: orders=452 fills=77 s-p=-0.04; shadow/NFL: orders=2840 fills=931 s-p=-0.15; shadow/NFL: orders=3878 fills=580 s-p=+0.39; shadow/NHL: orders=1246 fills=564 s-p=+0.10; shadow/NHL: orders=1307 fills=78 s-p=+0.37 | turn-off: none tripped
FORWARD-TEST (ADR-0072) 2026-10-19T11:25Z | paper/MLB: orders=32 fills=5 s-p=+0.07; paper/UNKNOWN: orders=0 fills=0 s-p=n/a; shadow/MLB: orders=107 fills=8 s-p=+0.18; shadow/MLB: orders=452 fills=77 s-p=-0.04; shadow/NBA: orders=242 fills=40 s-p=n/a; shadow/NBA: orders=244 fills=16 s-p=n/a; shadow/NFL: orders=5138 fills=2816 s-p=+0.01; shadow/NFL: orders=6236 fills=1000 s-p=+0.20; shadow/NHL: orders=1364 fills=618 s-p=+0.08; shadow/NHL: orders=1428 fills=82 s-p=+0.35 | turn-off: none tripped
FORWARD-TEST (ADR-0072) 2026-10-20T11:25Z | paper/MLB/unassigned_pre_test: orders=32 fills=5 games=5 s-p=+0.07; paper/UNKNOWN/unassigned_pre_test: orders=0 fills=0 games=0 s-p=n/a; shadow/MLB/control: orders=107 fills=8 games=3 s-p=+0.18; shadow/MLB/treatment: orders=89 fills=2 games=3 s-p=+0.45; shadow/MLB/unassigned_pre_test: orders=363 fills=75 games=3 s-p=-0.06; shadow/NBA/control: orders=1431 fills=284 games=14 s-p=n/a; shadow/NBA/treatment: orders=1458 fills=76 games=14 s-p=n/a; shadow/NBA/unassigned_pre_test: orders=0 fills=0 games=0 s-p=n/a; shadow/NFL/control: orders=5473 fills=3129 games=14 s-p=-0.00; shadow/NFL/treatment: orders=5415 fills=884 games=14 s-p=+0.15; shadow/NFL/unassigned_pre_test: orders=1135 fills=231 games=5 s-p=+0.40; shadow/NHL/control: orders=1671 fills=814 games=50 s-p=+0.08; shadow/NHL/treatment: orders=1755 fills=93 games=48 s-p=+0.32; shadow/NHL/unassigned_pre_test: orders=0 fills=0 games=0 s-p=n/a | turn-off: none tripped

```
