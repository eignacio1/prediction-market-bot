# SESSION HANDOFF — T4M-PROJ Flat Measurement-Stake Reactivation (ADR-0050)

**Session:** `session/20260731T020022Z-t4-reactivate` (isolated worktree, pushed to origin)
**Parked:** 2026-07-31, under severe token-scarcity constraint (operator: "~10% left until session limit," heavy concurrent Opus usage). This handoff exists so a fresh session can resume or verify without re-deriving anything below.
**Status: task complete and pushed.** Nothing is mid-edit. Working tree is clean. If this window crashes right now, no work is lost.

---

## What was done (all committed and pushed)

Reactivated T4M-PROJ (MLB live in-game projection band) at a **flat $1.00 fixed-dollar measurement stake**, replacing the zero-Kelly full dark-out it had been under since ADR-0048 (2026-07-29). MAIN (T1/T2/T3) is untouched — still `kelly_fraction=0`. This is a deliberate, DS-approved (operator, 2026-07-30, pre-granted in-session) exception to ADR-0048's edge-conditional rule: GG-105's T4 edge is still unvalidated; the stake's only job is to accrue a clean, gate-fixed (post-ADR-0049 signed-edge check) T4M-PROJ cohort so GG-046 (T4 commercial validation) has data to eventually measure.

### Commits, in order, all on `session/20260731T020022Z-t4-reactivate` (pushed, branch up to date with origin as of this handoff):

1. `b7ff281` — `risk.py` (`fixed_stake_usd` bypass param on `evaluate_forecast()`) + `run_t4_mlb_live.py` (`T4_MEASUREMENT_STAKE_USD=1.00` wiring, `KELLY_T4` left at 0.0).
2. `c9c8263` — `logic_epoch.py` epoch-11 boundary (`resolving_gap="GG-046"`, `bands_affected={"T4M-PROJ"}` only — MAIN's clean_n floor stays at epoch 10) + `tests/test_c4_risk.py::TestFixedStakeMeasurement` (4 new tests).
3. `3463e67` — `ADR-0050` document + `DECISION_LOG.md` R3 entry + `GOVERNANCE_GAP_LOG.md` GG-046 status update (still OPEN — this is instrumentation, not a resolution) + `ITERATION_MC_PROGRESS.md` completion line.
4. `67674c7` — `SESSION_CLAIMS.md` closure row.

### Mechanism (for anyone reading only this file)

`risk.py::evaluate_forecast()` gained an optional `fixed_stake_usd: float | None = None` param. Default `None` is fully inert — every caller except `run_t4_mlb_live.py` omits it, so Kelly-derived sizing (and `kelly_size_zero`'s unconditional rejection when `kelly_fraction=0`) is bit-for-bit unchanged for T1/T2/T3. When `run_t4_mlb_live.py` passes `fixed_stake_usd=T4_MEASUREMENT_STAKE_USD` (1.00), the sizing step bypasses Kelly and approves at exactly that dollar amount — but only after every other gate (signed edge ≥ `MIN_EDGE_TO_APPROVE`, CHECK 4b direction-consistency, both kill switches, single-event cap, min-bet floor, aggregate deployment) has already passed unchanged. `sizing_mode` field (`"fixed_measurement"` vs `"kelly"`) added to approval records for traceability.

### Verified live-sizing check (this session, both surfaces):
- `execution_bands.py`'s `T4M_PROJ` `BandConfig` entry: **untouched** (comment confirms "ACTIVE — flat Binomial model, already running").
- `run_t4_mlb_live.py` line 1109: `evaluate_forecast(..., fixed_stake_usd=T4_MEASUREMENT_STAKE_USD, ...)` — confirmed via live grep.
- `KELLY_T4 = 0.0` (line 153) confirmed still in force, never engages.

### Test status
- `tests/test_c4_risk.py`: **83/83 passing** (79 pre-existing + 4 new `TestFixedStakeMeasurement`).
- `tests/test_backfill_logic_epoch.py` + `tests/test_check_epoch_activation.py`: **31/31 passing** (epoch-11 boundary well-formed).
- `scripts/check_epoch_activation.py --skip-vps`: non-blocking stacking warning only (epoch 9 and 10 both landed within the trailing 7 days) — assessed acceptable because epoch-11's band-scoping means it does **not** reset MAIN's clean_n, only T4M-PROJ's, which is the explicit intent.

## What was explicitly deferred (honest gaps — do not assume these are done)

1. **Full project test suite was not re-run this session.** Only the scoped files above were run, under the token-scarcity constraint. **Run `pytest tests/ -q` (or the project's standard full-suite command) as the first action of whichever session next touches this branch, before opening a PR or merging to main.** No regression is expected — the change is additive and default-inert — but this has not been confirmed against the full suite.
2. **The CLAUDE.md "ARE WE COMPROMISED?" Q3/Q5/Q6 adversarial-review section was not run this session.** This is a real, acknowledged protocol gap, not silently skipped — flagged here and in `SESSION_CLAIMS.md`'s closure row. A follow-on session should run Q3 (architecture coherence), Q5 (decision traceability grep against `DECISION_LOG.md`), and Q6 ("what are you actually worried about") before treating this reactivation as fully protocol-clean. One thing worth specifically checking under Q6: whether $1.00/bet at T4's measured throughput (GG-080: 3.67–5.75 bets/game-day) produces a daily-dollar exposure rate that anyone should sanity-check against the 15% daily-loss circuit breaker denominator — at current bankroll this is almost certainly negligible, but it was not explicitly computed this session.
3. **No PR opened.** Branch is pushed and clean; a PR from `session/20260731T020022Z-t4-reactivate` to `main` still needs to be created (by the operator or a follow-on session) before this can merge.
4. **VPS not touched.** This is a code-only reactivation in the worktree/branch; nothing has been deployed to the live VPS (`157.230.91.33`). Per the project's standing "deploy after push" feedback preference, a follow-on session should deploy once the PR merges to `main` — but confirm the full-suite gap above is closed first, since this touches the live T4 sizing write path.

## Where to look for more detail
- Full mechanism/rationale: `03_DECISIONS/ADR-0050_t4m-proj-flat-measurement-stake-reactivation.md`
- Narrative decision record: `03_DECISIONS/DECISION_LOG/DECISION_LOG.md`, entry dated `2026-07-30/31`, tagged `[R3 — ADR-0050: ...]`
- Governance gap status: `03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-046, final paragraph of the Status cell (dated "Update 2026-07-30/31 (ADR-0050)")
- Iteration tracker: `04_EXECUTION/ITERATION_MC_PROGRESS.md`, final line (`R3 (T4 REACTIVATED) DONE ...`)
- Claim/closure record: `04_EXECUTION/SESSION_CLAIMS.md`, final two rows

## Exit criteria for this measurement posture (from ADR-0050 §6, restated here for convenience)
- **Regress to ADR-0048's B2-frontier edge-conditional sizing** once T4M-PROJ's own variance-derived `n*` (APR-0024 standard, `scripts/run_power_calc.py`) is computable from its own clean-epoch mean/stdev and clears the power calc.
- **Revert `T4_MEASUREMENT_STAKE_USD` to $0** if, once that `n*` is reached, GG-105's edge fails the power calc (not statistically distinguishable from zero, or negative).
