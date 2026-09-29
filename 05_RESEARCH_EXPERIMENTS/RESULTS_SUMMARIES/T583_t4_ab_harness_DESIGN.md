# T-583 — T4 A/B Harness: Shape Decision (Deliverable 1)

**Session:** `session/20260929T050106Z-t4-ab-harness` · **Tier:** STANDARD · **Base:** `cdd568e` (= `origin/main` tip; D0 satisfied)
**Status:** written and pushed BEFORE any build code, per the assignment. Nothing below has been implemented yet.

## 1. What I read, and what is actually reusable

| Piece | Claimed / assumed | Verified finding |
|---|---|---|
| `scripts/ab_harness.py` `compare()` / `metrics()` / `run_matrix()` | Generic A/B gate | **T1-shaped.** Statistic is Δ(P&L per $ staked) between taken-bet sets with B ⊆ A. Requires records with `_pnl,_size,_win,_event,_dir,_fne,position_id`. A T4 candidate rewrites `p_t4` on *every evaluation row*; there is no "taken subset" and no realized P&L per row. Wrong statistic, not just wrong schema. |
| `ab_harness.load()` → `run_exp017b_decomp_mlb.load_records()` | — | Hard-wired to one portfolio JSON schema (`model_p`, `mid_price_at_entry`, `kalshi_ticker`, dedup by ticker). Default file `logs/.vps_portfolio_cache_mlb.json` has never existed in the repo. |
| Bootstrap inside `ab_harness` | i.i.d. | **Wrong for T4.** Bootstraps *bets* as independent. T4 emits ~460–920 evaluation rows per game-day-game (GG-080), serially correlated inside a game. An i.i.d. bootstrap over rows would report a CI far too tight, i.e. it would manufacture `DEFENSIBLE_IMPROVEMENT`. The independent unit is the **game**. |
| `holdout_split` (date string compare) | generic | Reusable in spirit (10 lines); depends on `game_date` being right, which the cycle log's own field is not (GG-164, wrong on 70.2% of rows). |
| `MIN_N=30`, verdict vocabulary, "CI excludes 0" rule | ADR-0042 D2 | Reusable as *convention*. |
| T-572 `compute_clv_row` | "market-type-agnostic" | **Half true.** Signature is ticker-keyed and side-agnostic, but it requires a T4 cycle-log `TickerSeries` and measures *market drift after entry*, not the quality of a probability. Not the candidate metric. |
| T-572 `cohort_aggregate` | "market-type-agnostic" | **Not agnostic.** Typed to `ClvRow` (reads `.clv .ticker .game_id .size`). |
| T-572 `_block_bootstrap_mean_ci(values, cluster_keys)` | — | **Genuinely generic and exactly what is needed**: cluster bootstrap of a mean. Feeding it per-row score *differences* keyed by game gives a paired, game-clustered Δ CI. (Private name; I will import it and pin it with a test rather than fork it.) |
| Tests protecting T1 harness | "existing tests" | `ab_harness` has **no dedicated test file**. Only `tests/test_band_monitor.py` imports it. Baseline today: `test_band_monitor.py` + `test_clv_harness.py` = 62 passed. |

## 2. Choice: PARALLEL harness, T1 untouched, generic primitive imported

New module `scripts/ab_harness_t4.py` with its own explicit input contract. `ab_harness.py`, `run_ab_experiment.py`, `run_exp017b_decomp_mlb.py` are **not edited** (proven by `git diff` empty + byte hashes + the 62-test baseline unchanged).

**Why not generalize the existing harness:** the statistic differs (paired probability score vs. bet-subset P&L), the resampling unit differs (game vs. bet), the refusal semantics differ, and T1's harness has no test net. Editing it means changing code that gates ADR-0042 D2 with nothing that would notice a regression. The assignment says a generalization that breaks T1 is a regression, not a refactor; with no characterization tests I can't show it wouldn't.

**Why not a full shared core with adapters now:** it is the right eventual shape, but it needs ≥2 real adapters to find the true seam, and extracting it now would mean editing `ab_harness.py`. Rule of three: build the second one in parallel now, extract when a third (NFL/NHL T4, or a T2/T3 enhancer) arrives. The verdict names and the `MIN_N=30` convention are kept identical so a later merge is mechanical.

## 3. Statistic (pre-registered here, before results)

- Unit of analysis: **game**. Rows are clustered by `game_id`.
- Primary: `brier_gain = Brier(incumbent) − Brier(candidate)` per row, mean with game-clustered bootstrap 95% CI. Positive = candidate better.
- Secondary: log-loss gain, same procedure. `DEFENSIBLE_IMPROVEMENT` requires primary CI lower bound > 0 **and** secondary point estimate > 0.
- Holdout only for gate-eligible verdicts (train days strictly before test days by *true* game date). Candidate `fit()` sees train only.
- Because the ADR-0065 candidate is byte-identical to the incumbent outside the bottom-9th+ window, **rows where `p_candidate == p_incumbent` carry no information**. The harness reports the differing-row/game count and gates on *differing games*, not total games.
- Inadequate cohort ⇒ **exception, never a verdict.** The T1 harness's `UNDERPOWERED` verdict is deliberately not carried over.
