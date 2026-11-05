# W100.1 Part A: where the NHL regulation total comes from, and a new version (model_pit)

Held out 2023-2025 (walk-forward, fit on earlier seasons only). Exploratory; merged `model.py`/`inputs.py` unchanged. Scripts: `run_w100_1.py`, module `src/prediction_market_bot/nhl_engine/model_pit.py`, tests `tests/test_nhl_engine_model_pit.py`.

## Finding (plain)
The low total is a mix of three things, none of them shrinkage or half-life:
1. **Stale league denominator in the matchup cross** (fixable, fixed in `model_pit`). `lg_f5`/`lg_pp` come from earlier seasons (older xG vintage) while team rates come from the current vintage; the cross is scaled down by the vintage gap. Mean `lg_f5` vs mean team rate: 2.757 vs 2.676 (2023), 2.661 vs 2.555 (2024), 2.621 vs 2.605 (2025).
2. **Season-to-season xG drift** (not fixable here). Goals/xG in the event store: 0.966, 0.999, 0.989, 0.947 by season (about +-3%). League scoring moves with it.
3. **Early-season level error** (irreducible without new information). `level_adjust` prior_games=150 is about optimal on the noise/drift ratio (~178 games); bias is worst early in a season and in the lowest-predicted games.

Ruled out: shrinkage strength and half-life (grid: the merged setting hl=40, prior 3h has the best held-out log-likelihood; bias stays near -0.08 at every setting). Power-play and 5v5 time: expected vs actual seconds match within ~5% (2023 PP home 350 vs 352; 2024 335 vs 329; 2025 332 vs 346; 5v5 2861 vs 2858, 2862 vs 2915, 2882 vs 2879), no bias that could explain -0.1 goals.

Also seen: predictions are over-spread across games (slope of actual total on predicted total ~0.4-0.5, all settings). That is a calibration-slope issue on the rate, not a level issue; not addressed here (would need its own pre-registered challenger).

## Held-out regulation-total bias (predicted minus actual goals/game, after level_adjust)

| season | n | actual | merged | model_pit |
|---|---|---|---|---|
| 2023 | 1312 | 6.018 | -0.149 | -0.118 |
| 2024 | 1312 | 5.874 | -0.095 | -0.043 |
| 2025 | 1312 | 6.005 | +0.006 | -0.014 |
| pooled | 3936 | | -0.080 | -0.059 |

The fix removes about a quarter of the pooled bias. It is a partial fix, stated as such.

## Brier per Kalshi family (paired, game-clustered bootstrap, 2000 resamples; difference = model_pit minus merged, negative = better)

| family | n games | merged | model_pit | diff [95% CI] |
|---|---|---|---|---|
| ML | 3936 | 0.23929 | 0.23939 | +0.00010 [-0.00011, +0.00032] |
| SPREAD_HOME | 3936 | 0.19705 | 0.19699 | -0.00006 [-0.00021, +0.00008] |
| TEAMTOTAL_AWAY | 3936 | 0.23484 | 0.23495 | +0.00011 [-0.00011, +0.00033] |
| TEAMTOTAL_HOME | 3936 | 0.23282 | 0.23264 | -0.00018 [-0.00041, +0.00004] |
| TOTAL | 3936 | 0.22152 | 0.22138 | -0.00014 [-0.00041, +0.00013] |

Every interval includes zero: no family's Brier moves beyond noise. Applicability: regular-season frames from `game_features`; first games of a frame fall back to the original `lg_*`. 2026 vs Kalshi (descriptive): not run in this block; it needs the live 2026 archive and is left to the window.

## EXP-046
Not earned: bias shrinks but Brier does not move, and the remaining gap is not removed. No pre-registration filed. If the window wants one, the candidate is a rate-slope (over-dispersion) challenger, not this denominator.

## Parts B and C: NBA v3 first night and every-game coverage (read-only box readback, 2026-11-05 ~01:10Z)

**Cause of every miss: the box runs out of memory.** 961 MB, ~50 MB available, 1.1 of 2 GB swap used. `dmesg` holds 21 OOM kills in the last 2 h
(23:13Z to 01:04Z), all `python`, and `logs/nba_engine_live_cron.log` holds **151 bare `Killed` lines**. The engine runs themselves (v1/v2
chain, v3) are among the killed jobs: the 2.0 GB total-vm / ~60-110 MB RSS kills are the engine-sized processes. Competing processes at the
read: `run_pregame_shadow.py --refresh --bands T1` (65 min elapsed, 132 MB), the NBA pregame T2 (1 h 53 min) and T3 (49 min) shadows, the NBA
player-points T3, the NHL T3, `demo_cancel_sweeper`, `proof_calendar`. `logs/t3_skips.jsonl` shows 19 `SKIP_LOCKED` (11 NBA pregame T3,
6 NBA player points T3, 2 NHL staked T3) between 23:11Z and 01:01Z: runs overlap because earlier ones are still alive, thrashing on swap.

| Arm (tip window 00:00-02:00Z, the 11-04 evening slate, 11 games) | Games with all 4 families | Games with none | Notes |
|---|---|---|---|
| v1 | 11 of 11 | 0 | logged 7-58 min before tip |
| v2 | 5 of 11 | 0 | ATLWAS 2/4, PHIDET 1/4, CHABKN 1/4, CHINYK 2/4, MILBOS 2/4; first rows only 4-34 min pre-tip |
| v3 | 4 of 11 (CLEOKC, INDMEM, UTANOP, MINHOU) | **5 (ATLWAS, PHIDET, MILBOS, PORPHX, TORDEN)** | CHABKN and CHINYK 1/4; quote present 14.8-55.6 min before tip, never at 60 |

Precise v3 count: 0 families for ATLWAS, PHIDET, MILBOS, PORPHX, TORDEN; 1 of 4 for CHABKN and CHINYK; 4 of 4 for the other four. 412 rows in all.
**v3 never logged at tip-60** on any game (median lead 14.8 min): the cycle at :03/:13/... is the first that survives. **v3 has no
`coverage.jsonl` and its `status.json` has no `unlogged_past_tip`** (v1/v2 do), so v3's silent games are visible only by this readback.

`coverage.jsonl` (reason for every entry is `window_closed_without_a_successful_run`; no other reason is recorded):

| Arm | Before T3 lock (tips 11-03) | After T3 lock (installed 11-04 01:55Z), tips 11-05 UTC |
|---|---|---|
| v1 | 47 | 0 |
| v2 | 23 | 12 |
| v3 | no file | no file (5 games silent by the table above) |

Part B/C conclusion: the T3 lock did not end the misses; it moved them. v1 recovered fully (its run is first in the chain and gets the lock with
`flock -n`); v2 and v3 are starved by OOM kills and `flock -n` skips, not by a schedule or lock-wait bug in the code. **Nothing to fix in code
that a PR can reach: the cause is the box's memory budget against the number of concurrent jobs.** Not installed (prohibited); for the window:
(1) the memory budget: stagger or serialise the T1/T2/T3 shadow chains, cap the 65-minute `run_pregame_shadow.py --refresh` and the
1 h 53 min T2, or give the box more memory/swap; (2) give v3 a `coverage.jsonl` and `unlogged_past_tip` like v1/v2 (a small code PR, offered
for the next lane; not done here because the box would still be killing the runs); (3) re-read after (1) lands. Out-of-scope observations
(not fixed, per Hard Rule 11): the long-running T1/T2 jobs themselves.
