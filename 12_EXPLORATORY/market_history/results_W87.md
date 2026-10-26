# W87.3 results — market history for the frozen models + NHL totals price check (2026-10-26)
Purpose: PROOF. Measure: frozen models with a market-referenced held-out Brier. Descriptive; the gate stays unwired.

## Part A
| model | market-referenced held-out Brier | skill weight (gate rule) |
|---|---|---|
| nfl_pregame_v1 | n=271: model 0.2193 vs market 0.2121 (W86.1, unchanged) | 0 |
| nhl_pregame_v1 | n=1,306 (2025-26): model 0.24734 vs market 0.24419; market−model −0.00315; **no clustered interval** | 0 |
| nba_pregame_v1, nba_player_points_v1, mlb_game_pregame_v1, nfl_qb_challenger_v1 | NONE | 0 |

- **Honest count: 1 → 2 of 6, not 1 → 6.** NHL is carried from W84.3's stored numbers (`nhl_engine/results/part_b.json`); its per-game rows and the Kalshi NHL store were not kept, so the game-clustered paired interval is NOT COMPUTED. Rebuilding that store plus the box-score features is the next step.
- Kalshi history EXISTS for NBA games (2025-04..2026-06), NBA points (2025-11..2026-06), MLB games (2025-04..2026-08) and NHL games (2025-04..2026-06). The blocker for the other models is the model-side feature data, not the market side. Reasons are in each `models/*_heldout_vs_market_w87.json`.
- Gate rule (`position_gate.skill_weight` = clip(1 − Bm/Bk, 0, 1)): every weight is 0. With weight 0 the adjusted probability is the mid, so net edge is minus (half-spread + fee) and the gate keeps **0 positions** under any bar ≥ 0. Not replayed; follows from the rule.

## Part B — NHL_GAME_TOTAL_T1 price integrity (no score read or computed)
Source: box `data/shadow/nhl/NHL_GAME_TOTAL_T1.jsonl`, read-only, price fields only. 1,485 rows, 162 events.
| check | share failing |
|---|---|
| full bid-ask width > 10 points | 65.2% (968) |
| one-sided book (bid 0 or ask 1) | 0.0% |
| missing bid or ask | 0.0% |
| strike > 1.5 goals from the event's own line (strike with mid nearest 0.5) | 67.0% (995) |
| stale quote age | NOT MEASURABLE: rows carry only the run time `ts_utc`, no quote or trade time |

Reading: the ladder carries many far strikes with wide books, so most rows price a thin tail, not the market's own line. Whether that explains the BH survivor is for the look; none read.
Thresholds (10 points, 1.5 goals) are mine, stated before the run. Script `price_integrity.py`, known-answer test `tests/test_market_history_price_integrity.py`.
Stage: market history aggregated; nothing interpreted or applied.
