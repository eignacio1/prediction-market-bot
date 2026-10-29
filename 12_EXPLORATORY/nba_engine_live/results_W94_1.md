# W94.1 results — NBA engine on the live board (Parts A, B, C)

**Premise correction (Part A).** "No 2026-27 games in the store" was stale: the free sportsdataverse release assets carry 2027 (nba_stats schedule 1,274 rows / 123 played; pbp; ESPN team box 112 rows = 56 games; ESPN schedule with tip instants). Only `nba_stats_team_boxscores` 2027 is 404. `c1_signal_ingestion/nba_current_season.py` joins the three that exist into the same team-game shape on nba_stats ids; overtime minutes come from pbp periods.
**Measured (as_of 2026-10-29T00:24Z):** 56 regular-season games ingested, 0 dropped, last game 2026-10-27; known-answer check, 10 games vs raw ESPN box: max |total diff| 0.0, max |pace diff| 0.0 (pace is partly self-referential; total is the independent check). Daily refresh = `python -m prediction_market_bot.c1_signal_ingestion.nba_current_season`; **box read-back: not done — install waits for GREEN** (the 2026-10-29T00:04Z `budget_read` was RED on the T4 MLB silent arm; 94.3 has since shown that alarm was pre-first-pitch lag, but I did not re-read a GREEN budget).

**Part B.** `nba_engine/live.py` (thin entry; engine logic untouched, pinned `cfdc423`), `nba_engine/live_scoring.py`. Dry run on the 2026-10-28 archive with now = tip−50 min: 16 events, 408 rows (116 total, 152 team total, 132 spread, 8 moneyline), 0 skipped, params hash 9019981832b8b15d. Calibration (season 2026, 1,230 games): hca 1.74, tbias 1.67, s_p 5.32, s_e 10.48, K 10. Rating function cross-checked against the 93.3 `add_ratings`: diff 0.0. Tests: 13 pass. Pre-registration: `05_RESEARCH_EXPERIMENTS/EXP044_NBA_ENGINE_LIVE_PREREGISTRATION_2026-10-28.md` (judged n 300 full / 1,200 half effect; sigma_c approximate).
**Not done / waits:** runner and refresh cron lines are not added to `deploy/cron.conf` or `RUNTIME_REGISTRY.toml` (adding the line would install on deploy). The runner needs the pre-2027 history store (`--raw`) on the box; the install must ship `team_box`/`schedule`/`espn_schedule` parquet 2016–2026 (built here by `nba_event_store --only schedule espn_schedule team_box --min-season 2016`). Dry-run rows are not forward rows and are not scored.

**EXP-044 freeze:** merged in PR #368, commit `61ed3e08653a7628fdd03e2a79bf6f29b2305312` (CI green, run 40796331654). Pre-registration committed before any forward row.

## Part C — NBA engine v2 vs v1 vs Gaussian twin (held-out 2021-26)
`nba_engine/engine_v2.py` is a new version beside v1 (v1 untouched, as pinned in EXP-044). Protocol: rolling origin; for each season T, K picked on T-1, v1/Gaussian rows are the pinned W93.3 `study_a` rows, v2 parameters fit on seasons T-3..T-1 only and its Platt step fit on those seasons' own predictions; season T never seen. 7,230 held-out games. Brier deltas, negative = better, 95% game-clustered bootstrap (2,000 resamples). Code `study_v2.py`, outputs `study_v2_out.json`, `study_v2_out_rows.csv.gz`.

| Family | v2 − v1 | v2 − Gaussian | reliability slope v1 → v2 |
|---|---|---|---|
| moneyline | −0.00554 [−0.00704, −0.00398] | −0.00605 [−0.00761, −0.00442] | 1.831 → 0.992 |
| spread | +0.00004 [−0.00033, +0.00040] (tie) | −0.00005 | 0.988 → 0.960 |
| total | −0.00143 [−0.00202, −0.00084] | −0.00205 [−0.00271, −0.00137] | 1.058 → 1.039 |
| team total | −0.00058 [−0.00093, −0.00022] | −0.00100 [−0.00138, −0.00060] | 1.027 → 0.991 |
| ALL | −0.00087 [−0.00120, −0.00053] | −0.00126 [−0.00163, −0.00089] | 1.048 → 0.992 |

Absolute Brier (ALL): v1 0.23420, Gaussian 0.23460, v2 0.23333.

**What carried what.** Moneyline: the calibration step alone (raw v2 vs v1 on moneyline +0.00011, a tie; v1's slope of 1.83 means it under-states its own favourites, which the train-only logistic fixes). Total and team total: the estimated score correlation and residual SDs (raw v2 vs v1: total −0.00115 [−0.00175, −0.00056], team total −0.00049 [−0.00083, −0.00013]). Estimated rho by season 0.37 (2021) falling to 0.29 (2026), against v1's assumed value 0.06–0.09 higher. Spread: no change; its shape was already right.

**Factors tested against v2_core (none kept: every interval includes 0).**

| Factor set | ml | spread | total | team total | ALL |
|---|---|---|---|---|---|
| venue altitude → total | n/a | n/a | −0.00006 [−0.00039, +0.00024] | −0.00010 [−0.00028, +0.00008] | −0.00006 [−0.00022, +0.00009] |
| travel (miles, games in last 4, altitude gain) | +0.00029 [−0.00056, +0.00108] | −0.00034 [−0.00080, +0.00013] | −0.00003 [−0.00030, +0.00023] | −0.00017 [−0.00039, +0.00005] | −0.00016 [−0.00040, +0.00009] |
| all of the above | +0.00029 | −0.00034 | −0.00007 [−0.00051, +0.00033] | −0.00028 [−0.00056, +0.00001] | −0.00022 [−0.00052, +0.00008] |

Multiplicity caveat: 12 factor-family contrasts; the nearest to excluding zero (all factors, team total, upper bound +0.00001) would not survive a correction. Kept for EXP-044b: v2_core only.

**Not built (reported as undone):** 93.1 expected-missing-minutes availability, 92.3 lineups → total and officials. Their sources are not in the event store here; 93.2 had already called officials weak and unstable. Registered as GG gaps, not claimed.

**Granularity index, five parts, per factor class and stage.**
| Factor | split | rank vs history | matchup cross | market map | application | stage |
|---|---|---|---|---|---|---|
| Team scoring/pace rating (B1, B2) | per team, home/away, as-of | as-of vs prior seasons | team × team means | ml, spread, total, team total | v2_core prices all four | **applied** |
| Score correlation (B3/B9) | estimated per training window | season-over-season drift (0.37 → 0.29) | joint margin/total | total, team total | applied (rho from data, not assumed) | **applied** |
| Calibration (B7) | per family, train-only | slope vs 1 | none | ml mainly | Platt step | **applied** |
| Altitude (93.2) | venue | n/a | home altitude → total | total | tested, no gain | interpreted |
| Travel / rest geometry | per team | n/a | diff and sum of travel/games in 4 | margin, total | tested, no gain | interpreted |
| Availability, lineups, officials | — | — | — | — | not built | not started |

D5(b) NBA factor classes at **applied**: 4 → 4 (the four are unchanged in count; v2 improves their application, and altitude/travel stay interpreted-not-applied because they did not help). The addendum target of 7 is **not met**: 3 factor classes were tested and fell short; 3 more were not built.

## EXP-044b
`05_RESEARCH_EXPERIMENTS/EXP044B_NBA_ENGINE_V2_CHALLENGER_PREREGISTRATION_2026-10-28.md`, params hash `d50932902832762d`. Runner `nba_engine/live_v2.py` logs beside v1 to `exp_output/NBA_ENGINE_LIVE_V2/`. Tests: 15 pass across the v2 files. **Merged, install waits for GREEN**: nothing added to `deploy/cron.conf` or `RUNTIME_REGISTRY.toml`; no box read-back.
