# T-598 D1 — T4 cycle-log field inventory (decision-time availability)

Source: `t4_mlb_cycle_log.jsonl` read-only copy, 436,747 rows, sha256 `440df62ca9c5d95e2a7d76fbce22d63939d1a770cf347a38229ab831ae0b66a4`, first row 2026-07-02. **31 distinct keys** (the brief said 30). Game date below is always ticker-derived (GG-164).

| Field(s) | Coverage | Available at decision time? | Disposition |
|---|---|---|---|
| ts, cycle_id, session_id, player_name, player_id | 100% | identifiers | excluded (identifiers; player_id would let a model memorize batters) |
| game_date | 100% | yes, but wrong on ~70% of rows | excluded; ticker-derived date used |
| ticker, threshold | 100% | yes | ticker parsed for batter side only; threshold used |
| h_so_far, ab_so_far, inning, batting_slot | 100% | yes | INPUT |
| ab_remaining | 100% | yes, deterministic function of ab_so_far, inning, batting_slot | used only inside incumbent echo; not a separate input |
| mip, vig | 100% | yes (market-derived) | excluded: incumbent does not use them, comparison must be like-for-like |
| p_t4, gross_edge, net_edge | 92.9% | yes, but model/market echoes | excluded (p_t4 is the incumbent output; edges embed mip) |
| ba_l10 | 92.9% | yes | INPUT (fallback) |
| ba_l10_shrunk | 87.4%, from 2026-07-18 | yes | INPUT (primary) |
| vig_skip | 7.1%, from 07-03 | yes, a gate flag | excluded (not a probability input) |
| home_score, away_score, inning_half, outs, on_first/second/third, current_pitcher_id/name, pitcher_pitch_count | 0.9% (3,840 rows), only from 2026-09-29 | yes when logged | EXCLUDED: cannot reach 30 train + 30 test games (GG-323) |

Look-ahead check: every INPUT above is written by the live loop before the bet decision for that row; none is derived from the outcome, later rows, or the settlement. Outcomes come only from decoupled stores (T-421 / T-503), never from the ledger or the cycle log.
