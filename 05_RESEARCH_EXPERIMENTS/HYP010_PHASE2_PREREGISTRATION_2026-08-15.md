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
