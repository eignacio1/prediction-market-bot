# ADR-0050: T4M-PROJ Flat $1.00 Measurement-Stake Reactivation

**Status:** ACCEPTED (2026-07-30, DS sign-off = operator, pre-granted in-session). Applied live — GG-046, this session, `logic_epoch.py` 10→11.
**Date:** 2026-07-30
**Author:** Session `session/20260731T020022Z-t4-reactivate`
**Depends on:** ADR-0048 (R1, `kelly_fraction=0` for T1/T2/T3/T4M-PROJ), ADR-0049 (GG-142 signed-edge gate fix — T4M-PROJ bets now pass through a correct CHECK 3/4b before this stake applies), GG-105 (open — edge validity unresolved), GG-045 (Kalshi orderbook depth ceiling), GG-046 (T4 commercial validation gap — this ADR's tracking gap)

---

## 1. Problem

ADR-0048 zeroed `kelly_fraction` for all four bands, including T4M-PROJ, pending GG-105 resolution (edge validity unvalidated). Zero Kelly sizing means every T4M-PROJ evaluation that clears CHECK 3/4b still rejects downstream with `kelly_size_zero` — no bet is ever placed, so no clean T4M-PROJ cohort accrues under the post-ADR-0049 gate. GG-046 (T4 commercial validation) cannot progress without resolved bets to measure, and the longer T4M-PROJ sits fully dark, the longer GG-046 stays open for lack of data rather than for a negative result.

## 2. Decision

Reactivate T4M-PROJ at a **flat $1.00 fixed-dollar measurement stake**, not Kelly-proportional sizing, on every bet that clears the existing gate unchanged (signed edge ≥ `MIN_EDGE_TO_APPROVE`, CHECK 4b direction-consistency, kill switches, single-event cap, min-bet floor, aggregate deployment). This is a deliberate, explicit exception to ADR-0048's edge-conditional rule: GG-105's edge is still unvalidated, and this stake's only job is to accrue a clean, gate-fixed T4M-PROJ cohort large enough to measure that edge — it is not a claim that the edge is real.

**MAIN (T1/T2/T3) is untouched — `kelly_fraction` stays 0 for all three, unchanged by this document.**

### 2.1 Mechanism

`risk.py::evaluate_forecast()` gains an optional `fixed_stake_usd` parameter (default `None`, fully inert for every existing caller). When set, it bypasses Kelly-derived sizing (and the `kelly_size_zero` rejection that would otherwise fire unconditionally with `KELLY_T4=0.0`) and approves at exactly the flat dollar amount, provided the bet has already cleared every other gate check. The approval dict/log record gains a `sizing_mode` field (`"fixed_measurement"` vs `"kelly"`) for traceability. `run_t4_mlb_live.py` is the only caller that passes a non-default value: `T4_MEASUREMENT_STAKE_USD = 1.00`, replacing the prior GG-087 "1 contract at market price" policy.

### 2.2 Why $1.00

Far inside GG-045's estimated $500–$2,000 Kalshi orderbook depth per market — no risk of the stake itself moving the market or distorting fill price. Large enough, at T4's measured throughput (GG-080: 3.67–5.75 bets/game-day, n=2 game-days), to accrue a resolved-bet cohort at a meaningful rate without exposing capital disproportionate to the unvalidated-edge risk.

## 3. Why a new ADR, not an amendment to ADR-0048

Hard Rule 3: ADRs are immutable once accepted. ADR-0048's zeroing decision stands unchanged — `kelly_fraction=0` for T4M-PROJ is still true after this document; this ADR adds an orthogonal, band-scoped sizing path that only engages when a caller opts in, it does not revise or supersede ADR-0048's rationale or table.

## 4. Kill switches and gating — unchanged

Both kill switches (20% permanent max-drawdown, 15% daily circuit breaker) remain live and unaffected — `fixed_stake_usd` only determines the dollar amount of an already-approved bet; it does not bypass either kill-switch check, the single-event exposure cap, or the aggregate portfolio-deployment cap. Evaluation logging is unaffected — every evaluation (approved or rejected) continues to log full forecast context.

## 5. Epoch scope

`logic_epoch.py` epoch 11 (`resolving_gap="GG-046"`, `commit_sha=b7ff2812d5471a33460b3853b53ed63c9bc5ce07`) is recorded with `bands_affected=frozenset({"T4M-PROJ"})`, **not** `ALL_BANDS`. Although `risk.py::evaluate_forecast()` is shared code, `fixed_stake_usd` defaults to `None` and is behaviorally inert unless a caller explicitly passes a value; only `run_t4_mlb_live.py` (T4M-PROJ) does so. T1/T2/T3's code path through `evaluate_forecast()` is bit-for-bit unchanged, so their `clean_n` floor correctly stays at epoch 10 while only T4M-PROJ's clean_n resets to start a fresh, gate-fixed cohort at epoch 11.

## 6. Exit criteria

This is a measurement posture, not a standing sizing policy:

- **Regression to the B2-frontier sizing rule** (ADR-0048's per-band edge-conditional, variance-aware sizing) once T4M-PROJ accrues enough volume for its own power-calc `n*` (APR-0024 standard, `scripts/run_power_calc.py`) to be computed from real clean-epoch mean/stdev.
- **Revert `T4_MEASUREMENT_STAKE_USD` to $0** if, once that `n*` is reached, GG-105's edge fails the power calc (i.e., the measured edge is not statistically distinguishable from zero or is negative) — the same disposition T4M-PROJ was already under before this reactivation.

## 7. Verification

`tests/test_c4_risk.py::TestFixedStakeMeasurement` (4 cases, commit `c9c8263`): `fixed_stake_usd` approves at exactly the flat amount despite `kelly_fraction=0.0` (bypassing `kelly_size_zero`); the bypass is opt-in (`kelly_fraction=0.0` with no `fixed_stake_usd` still rejects `kelly_size_zero`, unchanged from pre-ADR-0050 behavior); `fixed_stake_usd` bypasses sizing only, not the edge-threshold gate (sub-threshold edge still rejects `insufficient_edge`); `fixed_stake_usd=None` (the default) leaves standard Kelly-derived sizing bit-for-bit unchanged for non-T4 callers. 83/83 passing in `tests/test_c4_risk.py`; `tests/test_backfill_logic_epoch.py` + `tests/test_check_epoch_activation.py` 31/31 passing (epoch-11 boundary well-formed, `check_epoch_activation.py --skip-vps` non-blocking stacking warning only, acceptable per §5's band-scoping). Full project test suite was **not** re-run this session under active token-scarcity constraints — see `DECISION_LOG.md` 2026-07-30 entry and the session handoff for this explicit, deliberate deferral.
