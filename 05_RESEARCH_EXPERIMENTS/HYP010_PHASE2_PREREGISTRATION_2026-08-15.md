# HYP-010 — Phase 2 pre-registration + gate 2.3 power analysis

**Date:** 2026-08-15 · **Window:** strategic (Cowork) · **Status:** DRAFT — awaiting operator sign-off, not yet an accepted hypothesis
**Operator decision this rests on:** 2026-08-16, Option A — *Phase 2 is buying GENERALITY, not edge.* Thinner edge is expected and accepted; a weak result is a finding, not a failure.
**Reproduce:** `python3 05_RESEARCH_EXPERIMENTS/hyp010_power_analysis.py` (stdlib only, seeded, deterministic)

---

## Why this document exists

The operator's Option A decision is recorded. **The prediction is not.** Without a specific, numeric, pre-registered expectation written before the experiment runs, any Phase 2 result gets explained after the fact, the experiment cannot fail, and it teaches nothing.

Writing that prediction surfaced a prior problem that has to be settled first: **gate 2.3 as currently written cannot fail honestly either — it fails almost regardless of the truth.**

---

## Finding 1 — the Phase 2 test data already exists

Gate 2.2 says *"score Brier against a historical `KXMLBTOTAL` price sample."* That sample is already on disk and nobody had counted it.

Measured 2026-08-15 from `exp_output/PRICE_ARCHIVE/prices_2026-08-*.jsonl` (16 files, 2026-08-01 → 2026-08-16):

| Series | Observations | | |
|---|---:|---|---|
| `KXMLBHIT` (traded today) | 119,190 | | |
| `KXMLBTEAMTOTAL` | 83,776 | | |
| **`KXMLBTOTAL`** | **64,969** | 214 distinct game-events · 16 dates · 12 lines/game (totals 3–14) | |
| `KXMLBF5TOTAL` | 37,793 | | |
| `KXMLBSPREAD` | 37,755 | | |
| `KXMLBGAME` (moneyline) | 30,302 | | |

Phase 2's minimal experiment is **not blocked on ingestion**. Four of the five coverage-target market types already have live price history accumulating daily.

## Finding 2 — totals are 3–6× more efficiently priced than the market the bot trades

Half-spread, `status=active`, mid ∈ (0.05, 0.95):

| Series | n | median | mean | p90 |
|---|---:|---:|---:|---:|
| `KXMLBTOTAL` | 57,814 | **0.0050** | 0.0095 | 0.0150 |
| `KXMLBHIT` (baseline) | 76,235 | **0.0150** | 0.0591 | 0.1550 |

This is the first direct quantitative confirmation of the efficiency-gradient tension that CLAUDE.md § "Market efficiency gradient" flags as an open departure. The expansion target really is priced 3× tighter on median and 6× on mean. **Option A's "expect thinner edge" is now a measured expectation, not an intuition.** Round-trip cost on totals ≈ 2 × 0.0050 = **0.010**, the vig figure used throughout below.

## Finding 3 — gate 2.3's metric is underpowered by roughly an order of magnitude

Effective independent unit is the **game (214)**, not the (game, line) row (2,568): twelve lines on one game resolve off a single realized run total and are heavily correlated. Scoring rows as independent would inflate power ~12× and produce a threshold that cannot honestly fail.

Null is *"model is an independent forecaster of equal skill"* — not *"model == market"*, which has zero variance and is degenerate. Model is set to **near-perfect** (noise 0.005): an upper bound on achievable skill.

| Market noise | mean ΔBrier | crit (5%, 1-sided) | power | games for 80% power |
|---:|---:|---:|---:|---:|
| 0.030 *(matches observed 50bp)* | +0.00099 | 0.0047 | **0.03** | ~10,573 |
| 0.050 | +0.00267 | 0.0079 | 0.06 | ~4,066 |
| 0.080 | +0.00669 | 0.0127 | 0.13 | ~1,671 |
| 0.120 | +0.01482 | 0.0192 | 0.28 | ~776 |
| 0.200 | +0.03849 | 0.0316 | 0.70 | ~311 |

**A perfect model reaches power 0.03 at the observed efficiency level.** Gate 2.3 as written returns FALSIFIED with near-certainty whether or not the model has real skill. A full MLB season is 2,430 games — the efficient case is unreachable this season and the mildly-soft case is not reachable either.

Under Option A this is the worst available outcome: the plan's own note reroutes a falsified 2.3 to moneyline-first, so the current gate would trigger a real strategic reroute **on a null result carrying no information**.

## Finding 4 — the selected-subset EV metric needs 7–11× less data for the same question

Gate on P&L-per-bet over the subset where |model_p − market_p| > vig, powered via the APR-0024 variance-derived `n*` (95% power, α=.05, one-sided) — the same instrument every other band is already gated on.

| Market noise | Model noise | bets from 214 games | P&L/bet | sd | `n*` | verdict |
|---:|---:|---:|---:|---:|---:|---|
| 0.03 | 0.005 | 1,881 | −0.0081 | 0.470 | n/a | negative — selection artifact, see caveat |
| 0.03 | 0.020 | 2,006 | +0.0095 | 0.469 | 14,966 | short ~1,597 games |
| 0.05 | 0.005 | 2,173 | +0.0214 | 0.472 | 3,003 | short ~296 games |
| 0.05 | 0.020 | 2,168 | +0.0195 | 0.477 | 3,701 | short ~365 games |
| 0.08 | 0.005 | 2,316 | +0.0422 | 0.471 | 769 | **POWERED by archive** |
| 0.08 | 0.020 | 2,347 | +0.0482 | 0.477 | 605 | **POWERED by archive** |

**Data requirement vs. the Brier gate, same market-efficiency assumption:**

| Market noise | Brier gate | EV gate | ratio |
|---:|---:|---:|---:|
| 0.03 | ~10,573 games | ~1,597 games | 6.6× cheaper |
| 0.05 | ~4,066 games | ~365 games | 11.1× cheaper |
| 0.08 | ~1,671 games | powered at 214 | ~8× cheaper |

**Correction, stated because I got this wrong once already.** An earlier unseeded exploratory run of this same simulation showed the EV gate powered by the existing archive at market noise 0.05, and I reported that to the operator in those terms when asking which metric to adopt. The seeded, reproducible run above does **not** support that: at 0.05 it is short ~296–365 games. The recommendation is unchanged — the EV gate is 6.6–11× cheaper in data either way — but "powered right now" was over-read from a single unseeded run. Reproducing a figure from the same source is reproducibility, not verification.

**Caveat on row 1.** The mkt=0.03 / model=0.005 row shows negative edge for a near-perfect model. That is a **selection artifact of this simulation, not a finding**: when model noise is far below market noise, |model − market| is dominated by *market* noise, so raw-disagreement selection selects on the market's error and pays vig on it. Real selection would condition on model confidence. The powered/underpowered conclusion does not depend on this row.

## Finding 5 — **no team run-total outcome source exists. Phase 2 is blocked on ingestion.**

Checked directly rather than assumed, and it is the binding constraint:

- `logs/t4_mlb_outcome_store.jsonl` (T-421's decoupled store, 2,021 rows) is **player-hits only**. Its schema is `actual_hits` / `player_id` / `player_name` / `threshold`, tickers are all `KXMLBHIT-…`. It cannot resolve a team run total.
- The price archive itself carries **no** outcomes: all 64,969 `KXMLBTOTAL` rows are `status: "active"`. The archiver snapshots live quotes and never captures settlement.

**Consequence for sequencing.** The first deliverable of the Phase 2 window is not fitting a model — it is a **team runs-scored outcome source** for the 214 archived game-events (MLB StatsAPI final scores; one API, well-defined, cheap). Until that exists, nothing above can be scored, and every power figure in Findings 3–4 is a projection rather than a measurement.

This also means the archived-game count is the ceiling, not the floor: outcomes must be backfilled for games already archived, and the archiver must keep running to grow toward `n*`. Both, not either.

**Cross-check that should happen at the same time:** resolving those 214 games yields the market's *realized* Brier, which collapses the entire assumed-market-noise dimension of Findings 3–4 to a single measured row. Do that before trusting any projected `n*`.

---

## The pre-registration

### HYP-010 — Team run-total forecasts transfer to a materially more efficient market

| Field | Detail |
|-------|--------|
| Research Question | Phase 2 / coverage-target generality: does the methodology transfer off the single traded cell (`KXMLBHIT`, T4M-PROJ)? |
| Framing | **Option A (operator, 2026-08-16): this buys GENERALITY, not edge.** Thinner edge than props is the expectation, not the disappointment. |
| H0 (Null) | A team run-total model fit on `MLBTeamStatsStore`'s existing `get_opp_runs_scored` / `get_opp_runs_allowed` series produces **P&L per bet ≤ 0** over the selected subset where \|model_p − mkt_p\| > 0.010, on archived `KXMLBTOTAL` prices. |
| H1 (Alternative) | P&L per bet > 0 on that subset, with `clean_n ≥ n*` where `n*` is derived live from the realized mean/sd via `scripts/run_power_calc.py` (APR-0024). |
| Test method | Fit NB/Poisson to team runs using the **existing** store — no new C2 matrix, no new ingestion (LL-009). Score against `exp_output/PRICE_ARCHIVE/prices_2026-08-*.jsonl` `KXMLBTOTAL` rows. Bet-selection filter: \|model_p − yes_mid\| > 0.010. |
| **Primary gate (2.3, revised)** | **P&L/bet > 0 AND `clean_n ≥ n*`, one-sided α=.05.** If `clean_n < n*` the verdict is **INCONCLUSIVE — extend archive**, explicitly *not* FALSIFIED. |
| **Pre-registered expectation** | **P&L/bet in the range +0.005 to +0.025, i.e. materially below `KXMLBHIT`'s realized figure.** Rationale: totals' median half-spread is 3× tighter (0.0050 vs 0.0150) and mean 6× tighter, so the same forecasting skill converts to proportionally less edge. A result above +0.03 should be treated as **suspect and audited for leakage before being believed**, not celebrated. |
| Falsification condition | P&L/bet ≤ 0 at `clean_n ≥ n*`. |
| Secondary (descriptive, **not** a gate) | Paired per-game ΔBrier vs market-implied, reported with its CI and its measured power. Pre-registered expectation: **indistinguishable from zero** — the power table above says a perfect model would also be indistinguishable at this n. Reporting it as a gate would be a false-negative machine. |
| Consequence if confirmed | Methodology transfers off the single traded cell. Phase 2 proceeds to 2.4 (team-game C2 matrix). First evidence for the coverage-target thesis. |
| Consequence if falsified | **Phase 2 does not terminate** (plan's own note). Reroute to **moneyline-first**: `KXMLBGAME`, 30,302 observations already archived, a binary target where the production LR class (ADR-0004) applies with no distribution fit. |
| Consequence if INCONCLUSIVE | Continue archiving; re-run at `n*`. ~14 games/day ⇒ ~296–365 additional games ≈ **3–4 weeks** at market noise 0.05. Do not build C2 in the interim. |
| Status | ⚪ PRE-REGISTERED, not yet run |
| Experiment(s) | EXP-022 (assigned T-461, 2026-08-17 — verified free against `RESULTS_SUMMARIES/RESULTS_INDEX.md` and repo-wide grep; EXP-017 through EXP-021 pre-reserved/taken) |

---

## Amendment — 2026-08-26 (T-487/GG-207), pre-fit

Five gaps in the pre-registration above, closed **before** box 2.2/2.3 were run, per this session's explicit instruction that deciding these after seeing a result is a forking-path risk. All five answers were fixed by the task brief itself, not chosen after inspecting output.

**(a) Benchmark timepoint.** The pre-registration never named which pregame price the model competes against. **Named: the closing pregame snapshot** — the last archived quote strictly before the 72h-prior game-start cutoff in (b), per (event_ticker, threshold) ticker. Justification: it is the sharpest, hardest-to-beat pregame price (most information has already been priced in by the time it's taken), so a PASS against it is the least-deniable result; a PASS against an early snapshot would be a weaker claim dressed as a strong one.

**(b) Pregame filter, asserted in the harness.** `game_start = close_time − 72h`. Implemented in `scripts/exp022_totals_backtest.py::load_totals_rows()`: any row with `run_ts >= game_start` is dropped before the closing snapshot is selected. **Measured on the full run (27 daily archive files, `prices_2026-08-01.jsonl` .. `prices_2026-08-27.jsonl`, all `KXMLBTOTAL` rows, not restricted to resolved events):** 106,915 total rows, **14,006 dropped (13.1%)**, 58,011 kept pregame, collapsing to 2,527 distinct (event, threshold) closing snapshots. This is a wider and more current window than Finding 1's original count (16 files, 08-01→08-16) and is restricted to `KXMLBTOTAL` only, not all-series-combined — the two figures are not directly comparable; this is the number that actually governs the box 2.3 run in this document.

**(c) Independent unit is the game.** Finding 3 stated this for the Brier gate; it applies identically to the EV gate and was not previously stated for it — up to 12 lines settle off one realized total, so scoring bets as independent rows inflates `clean_n` ~12×. **Implemented:** all qualifying bets within an `event_ticker` are averaged to one signed P&L observation before `n*`/`clean_n` are computed (`per_game_pnls` in `exp022_totals_backtest.py`). The row-level qualifying-bet count is reported separately and is not the gate input.

**(d) Revised prior.** Measured pregame market Brier decomposition on `KXMLBTOTAL` (Reliability 0.0001, Resolution 0.0658, Uncertainty 0.2457) shows a market already calibrated to measurement precision — no exploitable miscalibration signal for a recalibration-style edge. **Predicted here, before running:** P&L/bet lands at the bottom of the pre-registered +0.005..+0.025 band or below zero. Under Option A, a result at or below zero is a **finding about generality under an efficiently-priced market**, not a failure of the harness — but only because it was predicted here first.

**(e) Name the band.** This model is pregame, multi-day-horizon (median snapshot-to-first-pitch lead time 20 min pre-filter, but the *decision* uses only data available well before that, per (a)/(b)), game-level — it is a **T1 signal**, not T4M-PROJ. Per `ADR-0058` (PROPOSED, T-493, 2026-08-25), the cell `(mlb_game_total, T1_MULTI_DAY)` already exists in the registry at `NOT_IMPLEMENTED`. A PASS on gate 2.3 below is evidence for that specific cell — **it is not evidence for, and does not touch, any `T4M-*` cell, and does not activate anything.** Activation of `(mlb_game_total, T1_MULTI_DAY)` requires its own ADR per ADR-0058's process; this experiment does not initiate that. This closes part of GG-172 (the plan silently assuming T4 with no band axis) for this one cell — GG-172 itself remains open for the rest of the coverage matrix.

---

## Amendment — 2026-08-26, box 2.2/2.3 results

**Model (box 2.2):** Poisson, not NB. `mu_team = mean(get_opp_runs_scored(team, as_of), get_opp_runs_allowed(opponent, as_of))` (10-game window, min 3, TI-01-safe via the store's existing `as_of_date` filtering), `mu_total = mu_home + mu_away`, `model_p(YES) = P(total_runs >= floor_strike + 0.5)` under `Poisson(mu_total)`. Verified `get_opp_runs_scored`/`get_opp_runs_allowed` against real 2026 data before use (`verify_store()`, 4/4 sample team/date checks returned non-null series — see run log).

**Documented limitation, not corrected in this run (STANDARD tier, register-and-stop):** measured var/mean ratio on real 2026 team-game runs (n=3,954, both teams' games) is **2.33**, i.e. real team-game run totals are meaningfully overdispersed relative to Poisson. A Poisson fit is overconfident in the tails, which likely pulls `model_p` away from 0.5 more aggressively than a correctly-dispersed NB would at extreme thresholds — this plausibly explains part of the selected-subset's negative point estimate below rather than (or in addition to) a lack of real skill, mirroring the "selection artifact" caveat already on Finding 4's row 1. An NB refit (method-of-moments dispersion from this same 2.33 ratio) is the natural next step if this experiment is extended into 2.4; not done here.

**Box 2.3, executed exactly as revised in the pre-registration table above (no parameters changed after seeing output):**

| Quantity | Value |
|---|---:|
| Scored (event, threshold) rows | 2,275 |
| Skipped (no resolved outcome) | 252 |
| Skipped (insufficient team history) | 0 |
| Qualifying bets, row-level (\|model_p − yes_mid\| > 0.010) | 2,151 |
| Qualifying **games** (independent unit) | 207 |
| Mean P&L/bet, game-level | **−0.0026** |
| sd, game-level | 0.2425 |
| `n*` (one-sided α=.05, power=.95) | **94,260** |
| `clean_n` | 207 |
| **Verdict** | **INCONCLUSIVE — EXTEND ARCHIVE** (not FALSIFIED: `clean_n` ≪ `n*`) |

The point estimate is negative and at/below the pre-registered band's floor — consistent with the (d) prediction made before running. Because `clean_n < n*` by ~450×, the gate rule (INCONCLUSIVE below `n*`, regardless of sign) applies and this is explicitly not a falsification. At the measured effect size, reaching `n*` via archive growth alone (~14 games/day per the original Finding 5 cadence) is not a near-term timeline — this is a materially harder bar than Finding 4's projected 605–769 games and should be read as informative about how weak this particular effect size is, not as a target to keep extending toward.

**Secondary (descriptive, not a gate) — paired per-game ΔBrier**, closest-to-money line per game, n=207: mean **−0.0045**, 95% CI (−0.0229, 0.0139), measured power **0.017** at α=.05. Indistinguishable from zero, as pre-registered.

**Spot-check of externally-added rows (T-484 gap note).** T-484 reported the 08-18..08-22 outcome-store gap was closed by an untraced external process before its own session started. Sampled 5 resolved `t4_mlb_totals_outcome_store.jsonl` records with `game_date` in 2026-08-18..2026-08-22 and cross-checked `home_runs`/`away_runs`/`total_runs` against the MLB Stats API `gamePk` linescore for each: all 5 matched exactly (see run notes below). No corruption detected in the sampled rows; this is n=5, not a full audit of the gap.

Reproduce: `python3 scripts/exp022_totals_backtest.py` (deterministic given fixed input files; reads `PRICE_ARCHIVE`/`logs/t4_mlb_totals_outcome_store.jsonl`/`exp_output/MLB/cache/` from the main tree, writes only under this worktree).

---

## What I did NOT check

- ~~Whether the archived `KXMLBTOTAL` games have resolved outcomes attached.~~ **CHECKED — and it is a confirmed blocker. See Finding 5.**
- Whether `MLBTeamStatsStore.get_opp_runs_scored` / `get_opp_runs_allowed` actually return usable series — the plan asserts they exist; I did not run them.
- Real market noise. Every power figure is conditional on an *assumed* market-noise parameter. The observed 50bp spread motivates 0.03 but does not measure forecast error. **Measuring realized market Brier on resolved games would collapse this whole table to one row** and should be step one of the experiment.
- The full test suite (box 1.7) — not runnable from Cowork; needs a terminal window.
- Step 4 of the session-start protocol (VPS health) — no SSH route from Cowork (GG-154).
- Whether 214 games is contaminated by the T4 outage windows (GG-163/GG-179) — archiver and trader are separate paths, but I did not verify the archiver ran continuously across all 16 dates.

---

## Not decided here

Adopting the revised gate 2.3 changes `04_EXECUTION/MARKET_EXPANSION_ACTION_PLAN.md`. The operator selected the metric swap on 2026-08-15; **the plan edit itself, the HYP-010 entry in `HYPOTHESES.md`, and the EXP ID assignment are not made in this document** and belong to a terminal window with commit access. Cowork is reads-only for git (`.git/index.lock` incident, carry-forward).
