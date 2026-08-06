# SESSION HANDOFF — T-426 (in-flight, token-limited parking point)

**Written:** 2026-08-06 05:30 UTC, mid-session, because the writing session's context window is about to run out — not a natural stopping point. This doc exists so a fresh session can resume T-426 without re-deriving anything above.

**Branch:** `session/20260806T051203Z-shadow-power-calc`
**Worktree:** `/Users/earlignacio/Documents/Claude/Projects/PM-worktrees/20260806T051203Z-shadow-power-calc`
**Task claimed:** T-426 (T-424 collided with an already-registered task; T-426 used instead — see `SESSION_CLAIMS.md`). Description: "shadow decoupled-store power-calc, Window H (agreement check + bet-vs-decline calibration)".
**Precondition doc (read, not re-derived):** `05_RESEARCH_EXPERIMENTS/DECOUPLED_MEASUREMENT_STORE_2026-08-05.md`

## What T-426 asked for (full brief, condensed)

Three tasks against `logs/t4_mlb_outcome_store.jsonl`, the decoupled outcome-measurement store built by `scripts/build_t4_outcome_store.py` (T-421/Window G, already merged):

1. **TASK 1 (gates 2 and 3)** — Agreement check: does the store's independently-fetched `actual_hits` match the ledger's own `actual_hits` for the T4M-PROJ epoch-12 clean cohort? If disagree, that discrepancy IS the deliverable and nothing downstream may be reported as governance-grade.
2. **TASK 2** — Full-population Brier + reliability bins over ALL 2,021 tickers / 64,396 rows, split fired-vs-declined (does the model calibrate worse on the bets it takes than the ones it declines — adverse selection check).
3. **TASK 3** — n-for-verdict: how many evaluations would the decoupled path need vs the ledger's n*=267, and what's the cadence speedup.

**Scope fence:** read-only, no `src/` edits, no edits to `run_power_calc.py` itself (build alongside it), shadow figures must not enter any governance decision until Task 1 passes.

**Two mandatory verbatim caveats for the final deliverable:**
- (a) The cycle log is FROZEN at 64,396 rows by GG-163 (ESPN 403s since 2026-08-04T23:41Z). A stable row count is NOT evidence the daily-refresh path works — it hasn't been exercised against a growing log.
- (b) The 78 unresolved tickers may be inflated further by GG-163's second consumer (`run_resolve_mlb.py`'s ESPN fallback shares the same blocked UA). 96.1% resolution is a floor, not a settled number. (Confirmed this session: GG-163 still OPEN — no dual-number reporting needed yet.)

## What's DONE

- Full CLAUDE.md session-start protocol run (Step 0 isolation/claim, Steps 1-4, ARE WE COMPROMISED Q1-Q6) — completed earlier in session, not repeated here.
- Ledger baseline established via a real run of `run_power_calc.py` (unmodified) after pulling the missing `logs/.vps_portfolio_cache_mlb.json` dependency (`ssh prediction-market-vps "cat /opt/prediction-market-bot/logs/paper_portfolio_mlb.json" > logs/.vps_portfolio_cache_mlb.json`). **This is the authoritative number Task 1 must reconcile against:**
  ```
  [T4M-PROJ] clean_n=157 (raw_n=2193), n*=267, needs 110 more.
  mean_pnl/bet=$+0.3793, stdev_pnl/bet=$1.8821, cadence=275.2/wk
  ```
  (`exp_output/T323-POWER-CALC/power_calc_results.json` now reflects this live run; the diff is tracked and safe to commit.)
- Confirmed via full read of `src/prediction_market_bot/logic_epoch.py` (585 lines): `CURRENT_LOGIC_EPOCH = 12`, `clean_epoch_floor_for_band("T4M-PROJ") == 12` (GG-149 boundary — T4 offsetting-position suppression). This is the exact filter Task 1's shadow script replicates.
- **Discovered a new exact row-level join** (not in the original precondition doc): `ledger.forecast_id` format `"T4-MLB-{cycle_id_part1}-{cycle_id_part2}-{player_code}-{threshold}"` — the middle two hyphen segments are byte-identical to the cycle log's own `cycle_id` field. Verified by direct sample: `forecast_id="T4-MLB-C0017-e3c02b-NOOTBAAR21-1"` ↔ `cycle_id="C0017-e3c02b"`. This lets Task 2's fired-vs-declined split use the EXACT evaluation row that fired a bet, not a ticker-level proxy.
- **Two analysis scripts written, reviewed, and believed correct — NOT YET RUN against complete data:**
  - `scripts/run_t426_shadow_power_calc.py` — Task 1. Loads ledger, filters resolved + clean (epoch≥12 for T4M-PROJ), joins each clean position's `kalshi_ticker` into the store, classifies matched/unmatched/unresolved-in-store, compares `ledger_actual_hits` vs `store_actual_hits` numerically AND independently re-derives WIN/LOSS from the store to compare against the ledger's recorded outcome. Reports shadow clean_n/mu/sigma restricted to the store-corroborated cohort.
  - `scripts/run_t426_full_population_calibration.py` — Tasks 2+3. `match_bet_rows()` builds the exact `(ticker, cycle_id)` fired set via the `forecast_id` join above. `build_full_population()` derives ground-truth outcome per row (`actual_hits >= row's own threshold`) for every cycle-log row whose ticker resolved in the store. `task2()` computes Brier + 10-decile reliability bins for full-population / fired / declined. `task3()` reuses `run_power_calc.py`'s own `z_for()` (imported, not reimplemented) to compute `n*` for the calibration-bias signal (`outcome - p_t4`), explicitly labeled as answering a DIFFERENT question than the ledger's $EV n*=267, plus cadence/speedup numbers derived from the cycle log's own timestamp span (~32.4 days observed). `ledger_n_star=267.0` and `ledger_cadence_per_week=275.2` are hardcoded literals sourced from the `run_power_calc.py` run above (comment cites this).
  - Both scripts were self-reviewed before execution; one sloppy placeholder line in the calibration script was caught and fixed (`Edit`) before any run.

## What's NOT done — the actual blocker

`python3 scripts/build_t4_outcome_store.py --pull` is running in the background in this worktree (PID 47070, started ~10:21PM local / still alive at last check). Progress as of this handoff: **600 / 2,021 tickers** written to `logs/t4_mlb_outcome_store.jsonl` (checkpointed every 25). This file and all pulled VPS caches are gitignored local artifacts — nothing to commit, nothing at risk, but the process itself is NOT saved by a worktree/commit; if the terminal session or machine is interrupted, **rerun the exact same command to resume** (`build_t4_outcome_store.py` is designed to be idempotent/resumable per-ticker — check its own resume logic before assuming a full restart is needed; it may already skip tickers already present in the store file).

**A `timeout` wrapper failed on macOS earlier** (`(eval):1: command not found: timeout` — no GNU coreutils by default) — do not re-wrap the build command in `timeout`; just run it plain with `run_in_background: true`, or use `gtimeout` if coreutils is installed.

## Exact next steps (in order, no reinterpretation needed)

1. Check `wc -l logs/t4_mlb_outcome_store.jsonl` and `ps aux | grep build_t4_outcome_store`. If the process died before completion, re-run `python3 scripts/build_t4_outcome_store.py --pull` (check its source for `--resume`/idempotent-skip behavior first so you don't redo 600 already-resolved tickers).
2. Once the store build is complete (or as complete as it's going to get — target ~1,943/2,021 resolved, 96.1%, per the precondition doc, treated as a floor per caveat (b) above):
   ```
   python3 scripts/run_t426_shadow_power_calc.py > /tmp/t426_task1.json
   python3 scripts/run_t426_full_population_calibration.py > /tmp/t426_task23.json
   ```
3. Read Task 1's output first. Check `hits_agree` vs `hits_disagree` and `outcome_agree` vs `outcome_disagree` counts. **If disagreement is non-trivial, STOP — write up the discrepancy as the finding, do not proceed to present Task 2/3 numbers as governance-grade** (explicit scope fence from the original brief). If agreement is clean, proceed.
4. Write the findings doc under `05_RESEARCH_EXPERIMENTS/`, following the naming convention of `DECOUPLED_MEASUREMENT_STORE_2026-08-05.md`. Must include, verbatim: both mandatory caveats (GG-163 frozen-log; 78-unresolved-may-be-inflated), Task 1's agreement numbers, Task 2's Brier/reliability tables (full-population / fired / declined), Task 3's n*/ETA/speedup figures with the non-conflation caveat already embedded in the script's `interpretation` field.
5. Commit the two scripts + findings doc on this branch (path-scoped, per Hard Rule 10 — do not `git add -A`).
6. Report back to the user exactly as originally requested: branch name + commit range, Task 1 agree/disagree result with numbers, bet-vs-decline calibration comparison.

## Currently uncommitted in this worktree (all safe, nothing at risk)

```
 M exp_output/T323-POWER-CALC/power_calc_results.json     <- tracked, safe to commit (live run output)
?? scripts/run_t426_full_population_calibration.py         <- new, ready to commit
?? scripts/run_t426_shadow_power_calc.py                   <- new, ready to commit
?? 11_MEMORY_HANDOFF/SESSION_HANDOFF_T426_INFLIGHT_20260806_0530.md  <- this file
```
All `logs/*.jsonl` / `logs/.vps_*` data artifacts are gitignored (verified via `git check-ignore -v`) — no risk of accidentally committing large pulled data.

## Task list state at parking time (mirror into TaskCreate/TaskUpdate on resume)

1. [completed] Read run_power_calc.py, run_band_monitor.py, build_t4_outcome_store.py schemas
2. [in_progress] Task 1 — Agreement check: shadow clean_n/mu/sigma vs run_power_calc.py — **blocked only on store build completion, script is done**
3. [pending] Task 2 — Full-population Brier/calibration, bet vs decline split — **script is done, blocked on same dependency**
4. [pending] Task 3 — n-for-verdict comparison, decoupled vs ledger path — **script is done, blocked on same dependency**
5. [pending] Write findings doc + commit
