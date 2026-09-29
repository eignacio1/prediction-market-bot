# T-583 — T4 A/B Harness: Results (Deliverables 2–4)

Design/shape decision and reasoning: `T583_t4_ab_harness_DESIGN.md` (pushed before any build code, commit cb552a4).

## What was built
- `scripts/ab_harness_t4.py` — holdout gate for T4 probability-model enhancers. Paired Δ-Brier (primary) and Δ-log-loss (secondary), game-clustered bootstrap via `clv_harness._block_bootstrap_mean_ci`.
- `scripts/t4_forbidden_cohort_manifest.json` — 879 tickers of the T4M-PROJ epoch-12 ledger (open+closed+rejected; 3,004 rows), derived from the committed `exp_output/T577_cohort_salvage/...20260922.json`. A test asserts it equals that ledger's ticker set.
- `tests/test_ab_harness_t4.py` — 13 tests.

## Input contract as implemented (all violations raise; no imputation, no silent drops)
| Rule | Exception |
|---|---|
| Required fields (`ticker, game_id, game_date, p_incumbent, outcome, resolution_source, cohort_band, logic_epoch`) + every caller-declared `required_state_fields` present and non-None | `MissingFieldError` |
| `outcome` ∈ {0,1} from `kalshi_settlement` / `boxscore_rederived` / `synthetic_ground_truth`; ledger-derived outcomes refused (GG-166) | `UnresolvedOutcomeError` |
| stored `game_date` == date embedded in ticker (GG-164) | `DateIntegrityError` |
| band=T4M-PROJ & epoch=12 by label, OR any ticker in the manifest (defeats relabelling) | `ForbiddenCohortError` |
| hypothesis pre-registered non-empty; train/test split by true date with no shared game | `PreRegistrationError` / `SplitError` |
| ≥30 train games, ≥30 test games, ≥30 test games where candidate ≠ incumbent | `InadequateCohortError` |

Verdict (only after all refusals pass): DEFENSIBLE_IMPROVEMENT = Brier-gain CI lower bound > 0 AND log-loss point > 0; HARMFUL = CI upper < 0; else INCONCLUSIVE. Synthetic runs return `gate_eligible=False`. The T1 `UNDERPOWERED` verdict is deliberately dropped: an inadequate cohort raises instead of returning a label.

## Proof
- **End-to-end (SYNTHETIC — machinery only):** 160 games × 8 rows, year-2027 tickers, seeded RNG, known truth. Incumbent carries a +0.12 bias on late rows; oracle candidate removes it → `DEFENSIBLE_IMPROVEMENT`; a candidate that worsens late rows → `HARMFUL`. This proves the harness detects a planted effect of both signs and that the game-clustered CI is materially wider than a row-iid CI (tested). It proves nothing about any real enhancer, real T4 data, or ADR-0065.
- **Refusals demonstrated (11 tests):** no-difference candidate; 40-game cohort; ADR-0065 state fields absent; ledger outcomes; non-binary/None outcome; stored-date/ticker mismatch; empty hypothesis; T4M-PROJ epoch-12 by label; same cohort by manifest with band label scrubbed.
- **T1 unchanged:** `git diff origin/main` on `ab_harness.py`, `run_ab_experiment.py`, `run_exp017b_decomp_mlb.py` is empty (files not touched). `test_band_monitor.py` + `test_clv_harness.py` = 62 passed at baseline; with the 13 new tests, 75 passed. Caveat: the T1 harness has no dedicated tests, so "unchanged" rests on untouched files, not behavioural tests.
- No real T4 cohort was scored. ADR-0065's candidate was not run and no verdict on it is reported.

## What the harness still cannot do
1. It cannot produce a real-data verdict today: no legitimate T4 cohort exists (see below).
2. It scores probability quality, not P&L. A Brier gain is necessary for ADR-0065 but not sufficient for a sizing/EV claim (Kelly is 0.0 for T4M-PROJ per ADR-0048).
3. It cannot judge candidates whose effect is on which bets are taken (selection filters); T1's harness owns that shape.
4. The candidate must supply its own fit-on-train logic; the harness enforces train-only fitting by calling `candidate(train)` but cannot stop a candidate closing over test data.
5. Real-cohort outcome sourcing (`boxscore_rederived` / settlement store) is a contract requirement, not something this module builds (T-421/T-437 own that).

## ADR-0065 candidate: conditions and calendar cost
Required before a valid run (each verified absent per T-580, not re-derived):
1. Game-state logged per evaluation row: `inning_half, home_score, away_score, outs, base_state, pitcher_id, pitch_count` (`WALKOFF_STATE_FIELDS`). Needs a logging change in `run_t4_mlb_live.py` — out of this task's scope, ADR-0065 activation requirement.
2. Rows from games with independent resolved outcomes and ticker-derived dates.
3. ≥30 train + ≥30 test games, and ≥30 test games in which the shrink actually changes p (bottom-9th+ only). Total games needed is therefore well above 60.
4. Cohort must exclude the 879 forbidden tickers — i.e. all 2026 epoch-12 T4M-PROJ games are out, including any play-by-play backfill of them.

Calendar cost: the 2026 regular season has ended, and the 2026 games carry no logged state and fall inside the forbidden manifest, so **no existing data can serve.** Measured T4 coverage was 3–4 games/day (2026-07-02/03, GG-080; n=2 days, not stable). If roughly half of covered games reach a differing bottom-9th+ state (my assumption, not measured), ≥60 differing games plus ≥30 train games needs on the order of 25–35 game-days *after* logging is deployed and validated. **Honest answer: not before the 2027 MLB season (opens ~late March 2027) unless T4 is running on another sport with live game-state logging in the interim; earliest plausible run is roughly May–June 2027.** The fraction-differing figure should be measured from the first two weeks of logged data before committing to that estimate.
