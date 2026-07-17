# ADR-0046 — MLB-Native C7 Drift Baselines (BRIER_BASELINE_MLB / ECE_BASELINE_MLB)

**Status:** ACCEPTED — Earl Ignacio, in-session directive, 2026-07-16.
**Date:** 2026-07-16
**Session:** GG-easy-sweep (T-374)
**Addresses:** GG-044 (`03_DECISIONS/GOVERNANCE_GAP_LOG.md`), implementing APR-0026
  (`00_ADMIN/APR-0026_mlb-native-monitoring-baselines.md`, PENDING → this ADR closes
  its follow-on work item).
**Supersedes / relates:** Does NOT supersede ADR-0004 (NBA G4 TEST-set baselines,
  `BRIER_BASELINE=0.2416` / `ECE_BASELINE=0.0247`) — those remain correct and unchanged
  for NBA (dark/frozen, [[project_nba_deferred]]). This ADR registers a second,
  MLB-specific pair of constants alongside them; `c7_monitoring/monitor.py`'s
  `SystemMonitor.__init__` already accepts `brier_baseline`/`ece_baseline` as
  constructor parameters (no code change needed to support per-sport injection —
  confirmed by direct read, 2026-07-16), so this is additive, not a rewrite.

---

## Context

GG-044 (registered SESSION 90, 2026-06-27) found that C7's `SystemMonitor` drift-alarm
ladder (`get_drift_snapshot()` / `check_and_alert()`) uses `BRIER_BASELINE=0.2416` /
`ECE_BASELINE=0.0247` — values fitted on the NBA G4 TEST set (ADR-0004) — as the
reference point for MLB forecasts too, by default. MLB hit-prediction is a
structurally different classification problem (t=1 actual base rate ≈54.5%, t=2
≈18.4% vs. NBA's 30–50% scoring-threshold range), so an NBA-fitted baseline has no
principled reason to be the right drift reference for MLB. The gap's stated
precondition for resolution — "≥30 resolved MLB paper bets" — is now met by a wide
margin (see Derivation below). APR-0026 (drafted 2026-07-15) proposed the follow-on
work to close this; Earl authorized "Adopt as proposed" in-session, 2026-07-16.

## Derivation

Computed directly from the live resolved MLB paper portfolio
(`paper_portfolio_mlb.json`, pulled from the VPS 2026-07-16), mirroring
`c7_monitoring/monitor.py`'s own `_compute_brier()` / `_compute_ece()` methodology
exactly (mean squared error of `p_estimate` vs. realized `outcome`; Expected
Calibration Error over 10 equal-width bins on `[0, 1]`), applied to the directional
`(p_estimate, outcome)` frame already established by `run_mlb_calib_monitor.py`
(T-187F) and `run_exp017_mlb.py` — i.e., `p_estimate = model_p` for YES bets,
`1 - model_p` for NO bets; `outcome = 1` if the bet resolved WIN else `0`.

**Filter applied:** closed positions, `duplicate_of` excluded, `outcome ∈ {WIN, LOSS}`,
valid `model_p`, restricted to `threshold ∈ {1, 2}` (t=3 structurally excluded from
active scope per GG-042/T-187H — including it would contaminate the baseline with a
threshold the model is not scored on in production).

**Sample:** n=261 resolved positions (t=1: 147, t=2: 114) — well above both the
30-bet GG-044 precondition and ADR-0024's Tier-1 (n≥150) single-sport floor.

**Result:**
```
BRIER_BASELINE_MLB = 0.2190
ECE_BASELINE_MLB   = 0.0680
(mean_p = 0.5660, mean_actual = 0.4981, n = 261)
```

**Why `raw_n`, not `clean_n` (logic_epoch.py):** the `CURRENT_LOGIC_EPOCH` boundaries
(GG-087, GG-077, GG-113, GG-119, GG-123) all track bugs in the *approval/sizing*
write path — `fee_net_edge` / vig sign and magnitude conventions used at CHECK 3
gating (`risk.py`, `paper_trader.py::open_position()`) — which govern whether a bet
fires and at what size, not the value `model_p` itself. `model_p` is produced
upstream by the frozen C3 forecasting/calibration pipeline and is not touched by any
of the five epoch-boundary fixes. A Brier/ECE calibration baseline measures
"model_p vs. realized outcome" — a quantity the write-path bugs do not contaminate —
so restricting to `clean_n` would needlessly shrink the sample (epoch 6 is only
hours old as of this derivation) without buying any additional correctness. This is
a deliberate, disclosed methodological choice specific to baseline derivation; it
does not apply to and does not affect the separate `clean_n`-gated commercial-
validation framework (APR-0024/GG-004), which remains unchanged.

Reproducibility: derivation script run inline (not checked in as a standalone
script — a one-off computation over a pulled portfolio snapshot, mirroring
`monitor.py::_compute_brier`/`_compute_ece` line-for-line). Re-derive by pulling
`logs/paper_portfolio_mlb.json` from the VPS and re-running the same filter/transform
if this baseline needs to be refreshed later (e.g. after a C3 recalibration).

## Decision

1. **Register `BRIER_BASELINE_MLB = 0.2190`** and **`ECE_BASELINE_MLB = 0.0680`** as
   new module-level constants in `c7_monitoring/monitor.py`, alongside the existing
   NBA `BRIER_BASELINE`/`ECE_BASELINE` (both left unchanged).
2. **Wire them into `SystemMonitor` via the existing constructor parameters** at
   MLB's two production instantiation sites — `run_mlb_paper_trade.py` (PIPE-05) and
   `run_resolve_mlb.py` (PIPE-05R) — passing `brier_baseline=BRIER_BASELINE_MLB,
   ece_baseline=ECE_BASELINE_MLB`. NBA's instantiation sites (`run_paper_trade.py`,
   `run_resolve.py`) are untouched and continue to default to the NBA constants.
3. **Enable the MLB `calib_monitor` cron line** (`deploy/cron.conf:284`,
   `scripts/run_mlb_calib_monitor.py`, T-187F), now that this ADR is accepted, per
   APR-0026 item 3.

## A related, distinct finding surfaced during implementation (not fixed here)

Direct inspection of every call site (`grep -rn "record_forecast_outcome\|check_and_alert"
src/ scripts/`) found that **`SystemMonitor.check_and_alert()` / `get_drift_snapshot()`
— the methods that actually consume `brier_baseline`/`ece_baseline` to raise an
alarm — are never invoked from any production pipeline script, for either sport.**
`record_forecast_outcome()` (which feeds the rolling window `check_and_alert()`
reads) is referenced only in `monitor.py`'s own usage docstring. The only C7 method
actually called from `run_mlb_paper_trade.py` / `run_resolve_mlb.py` /
`run_paper_trade.py` / `run_resolve.py` is `check_portfolio_pnl()`, a separate
PNL-threshold check unrelated to Brier/ECE drift. Practically: wiring the correct
MLB baseline into `SystemMonitor`'s constructor (Decision #2 above) is necessary and
correct, but the Brier/ECE drift-alarm ladder itself is currently dead code in
production for both NBA and MLB — it will not fire regardless of which baseline is
configured, until something calls `record_forecast_outcome()` per resolved bet and
then `check_and_alert()`. This is a distinct problem from GG-044 (wrong baseline
value) — GG-044 is about to be resolved as "the configured value is now right for
MLB"; whether the alarm ever runs at all is a separate, newly-discovered gap.
Registered separately as **GG-124** rather than folded into this ADR's scope, since
wiring `record_forecast_outcome()`/`check_and_alert()` into a live per-resolution
call path is materially larger work than this ADR's mandate (deriving/wiring a
baseline value) and deserves its own sign-off.

## What this ADR does NOT do

- Does not touch NBA's baselines or NBA instantiation sites.
- Does not change `_HARD_LIMITS` in `risk.py` or any Kelly/exposure constant.
- Does not wire `record_forecast_outcome()`/`check_and_alert()` into any production
  pipeline — see GG-124 above.
- Does not change `run_mlb_calib_monitor.py`'s own `ECE_THRESHOLD=0.05` (ADR-0027
  policy value, already sport-agnostic) — that script is a separate temperature-
  derivation/ECE-diagnosis tool, not the C7 `SystemMonitor` this ADR concerns; only
  its cron line is being enabled per APR-0026 item 3.

## Evidence / reproducibility

- Governing gap: GG-044, GG-124 (new) — `03_DECISIONS/GOVERNANCE_GAP_LOG.md`.
- Proposal: `00_ADMIN/APR-0026_mlb-native-monitoring-baselines.md`.
- Source data: `logs/paper_portfolio_mlb.json` (VPS, pulled 2026-07-16), n=261
  resolved MLB positions, t∈{1,2}.
- Code: `src/prediction_market_bot/c7_monitoring/monitor.py` (constants +
  docstring), `src/prediction_market_bot/run_mlb_paper_trade.py`,
  `src/prediction_market_bot/run_resolve_mlb.py`, `deploy/cron.conf`.
