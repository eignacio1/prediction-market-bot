# T-487 / GG-207 / EXP-022 — HYP-010 Phase 2, boxes 2.2+2.3 result

**Date:** 2026-08-26 · **Status:** RUN — box 2.2 (team run-total Poisson model) and box 2.3 (revised EV gate) executed once, gate parameters fixed by the pre-registration and its 2026-08-26 amendment (`HYP010_PHASE2_PREREGISTRATION_2026-08-15.md`), not tuned after seeing output.

## Verdict

**INCONCLUSIVE — EXTEND ARCHIVE** (explicitly not FALSIFIED: `clean_n=207` ≪ `n*=94,260`).

| Quantity | Value |
|---|---:|
| KXMLBTOTAL rows (27 archive files, 08-01..08-27) | 106,915 |
| Dropped by pregame filter (`run_ts >= close_time-72h`) | 14,006 (13.1%) |
| Closing pregame snapshots (distinct event×threshold) | 2,527 |
| Scored (joined to resolved outcome) | 2,275 |
| Qualifying bets, row-level (\|edge\| > 0.010) | 2,151 |
| Qualifying games (independent unit, per prereg amendment (c)) | 207 |
| Mean P&L/bet, game-level | −0.0026 |
| sd, game-level | 0.2425 |
| `n*` (one-sided α=.05, power=.95, from this run's own mean/sd) | 94,260 |
| Secondary: paired per-game ΔBrier (n=207) | −0.0045, 95% CI (−0.0229, 0.0139), measured power 0.017 |

## What this is evidence for

Per prereg amendment (e): this is a pregame, game-level, multi-day-horizon signal — a **T1** signal, mapping to the registry cell `(mlb_game_total, T1_MULTI_DAY)`, currently `NOT_IMPLEMENTED` per ADR-0058. This result is **not** evidence about any `T4M-*` cell and **does not activate** anything — no registry, `kelly_fraction`, or ledger changes were made (scope-fenced to `05_RESEARCH_EXPERIMENTS/` and `scripts/`).

## Model (box 2.2)

Poisson, fit via `MLBTeamStatsStore.get_opp_runs_scored`/`get_opp_runs_allowed` (existing C1 method, LL-009: no new C2 matrix). `mu_team = mean(own_offense_L10, opponent_defense_L10)`; `mu_total = mu_home + mu_away`; `model_p(YES) = P(total_runs >= floor_strike+0.5)` under `Poisson(mu_total)`. Both store methods verified against real 2026 data before use (4/4 sample team/date checks returned non-null series).

**Limitation, not corrected in this run:** measured var/mean on real 2026 team-game runs (n=3,954) is 2.33 — meaningfully overdispersed vs. Poisson's assumption of 1.0. A Poisson fit is overconfident in the tails; this plausibly contributes to the negative point estimate above independent of, or in addition to, real forecasting skill. An NB refit (method-of-moments dispersion ≈2.33) is the natural next step if Phase 2 is extended to box 2.4; not performed here (STANDARD tier, one deliverable, register-and-stop).

## Data provenance note (T-484 gap)

T-484 reported the 2026-08-18..08-22 outcome-store gap was closed by an untraced external process before its own run, which itself produced 0 new resolutions. Spot-checked 5 resolved rows from that window (`t4_mlb_totals_outcome_store.jsonl`, gamePks 824803/823341/823423/824398/824475) directly against the MLB Stats API `/api/v1.1/game/{pk}/feed/live` linescore: **all 5 matched exactly** on away_runs/home_runs/total_runs. n=5, not a full audit of the gap — flagging as a spot-check only, per the task instruction, not a clearance of the whole window.

## Reproduce

```
python3 scripts/exp022_totals_backtest.py
```

Reads `PRICE_ARCHIVE`, `logs/t4_mlb_totals_outcome_store.jsonl`, and `exp_output/MLB/cache/completed_games_2026.parquet` from the main repo tree (gitignored, local-disk-only, absent from this isolated worktree by design — see script docstring). Writes only under this worktree (`exp_output/MLB/cache/exp022_gap_games_*.parquet` gap-fill cache, `exp_output/MLB/exp022_gate23_result.json` machine-readable result — both gitignored, not committed; this document is the committed record).

## Next step if Phase 2 continues

Per the pre-registration's own consequence table: **INCONCLUSIVE → continue archiving, re-run at `n*`.** At the measured effect size, `n*=94,260` games is not reachable on any practical timeline at ~14 games/day — this should be read as strong evidence the effect size here is too small to ever power conventionally, not as a target to keep extending toward. Recommend the operator treat this as closer to a soft-FALSIFIED for practical purposes and weigh the plan's own fallback (reroute to moneyline-first, `KXMLBGAME`) rather than archiving toward `n*` as stated literally. That is an operator call, not resolved here.
