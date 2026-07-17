# APR-0026 — Derive MLB-Native C7 Drift Baselines and Enable the MLB calib_monitor Cron

**Status:** ACCEPTED — Earl Ignacio, in-session directive, 2026-07-16 ("Adopt as proposed").
**Addresses:** GG-044 (`03_DECISIONS/GOVERNANCE_GAP_LOG.md`)
**Drafted:** 2026-07-15, Terminal 3 (GG-burndown-even session), branch
`session/20260715T145447Z-gg-burndown-even`
**Approved by:** Earl Ignacio, 2026-07-16, in-session directive
**Implemented by:** ADR-0046 (`03_DECISIONS/ADR-0046_mlb-native-c7-drift-baselines.md`),
  GG-easy-sweep session (T-374), 2026-07-16 — `BRIER_BASELINE_MLB=0.2190`,
  `ECE_BASELINE_MLB=0.0680`, n=261.

---

## Why This Escalation Is Required

`monitor.py`'s `SystemMonitor` (C7) uses two module-level drift baselines — `BRIER_BASELINE = 0.2416` and
`ECE_BASELINE = 0.0247` — to decide whether the rolling forecast window has drifted enough to alarm. Both
values are NBA G4 TEST-set constants, fitted on 80-player NBA scoring-threshold outcomes (base rates
30–50% depending on line). MLB hit-prediction is a structurally different classification problem — lower
base rates (t=1 ≈ 27%, t=2 ≈ 6.5%) and a different score distribution — so an NBA-fitted Brier/ECE baseline
has no principled reason to be the right drift threshold for MLB forecasts.

GG-044 registered this gap at MLB pre-G1 (SESSION 90, 2026-06-27) and correctly scoped it as **low urgency
at the time** because the MLB `calib_monitor` cron line was — and still is — commented out in
`deploy/cron.conf` pending derivation of MLB-specific values. The gap's own stated precondition for
resolution was "≥30 resolved MLB paper bets," so an empirical MLB Brier/ECE could be computed. That
precondition is now met — MLB T1 alone has clean_n=81 (and raw_n well above 30) as of the 2026-07-11 pull
cited in CLAUDE.md's commercial-validation section. The gap is no longer blocked on data availability; it is
blocked only on someone deriving the values and someone authorizing the cron to go live against them.

This is squarely a Hard Rule 3 item: enabling a monitoring alarm that can independently affect operational
behavior (drift alerts, potential kill-switch-adjacent decisions) is a threshold change, not a bug fix. This
session's mandate is to escalate to the DS, not to compute and ship the values unilaterally.

---

## What Is Being Proposed

1. **Derive `BRIER_BASELINE_MLB` and `ECE_BASELINE_MLB`** empirically from the resolved MLB paper portfolio
   (T1 clean_n=81 today, growing), following the same methodology used to fit the original NBA constants —
   i.e., compute realized Brier score and Expected Calibration Error across the resolved MLB paper bets and
   register the result as the MLB baseline.
2. **Register the values via a superseding ADR** (not this APR directly — this APR authorizes the *work*;
   the resulting constants get their own ADR entry per GG-044's original resolution path), either as
   sport-specific `BRIER_BASELINE_MLB` / `ECE_BASELINE_MLB` constants or by parameterizing
   `SystemMonitor.__init__` to accept sport-specific baselines.
3. **Enable the MLB `calib_monitor` cron line** (`deploy/cron.conf:284`, currently commented out) only after
   the baseline ADR is accepted — not before.

## What This APR Does NOT Do

- Does not compute or ship the actual `BRIER_BASELINE_MLB` / `ECE_BASELINE_MLB` values — that is follow-on
  work gated on this APR's acceptance.
- Does not touch NBA's existing baselines, which remain correct for NBA (dark/frozen, [[project_nba_deferred]]).
- Does not change `_HARD_LIMITS` in `risk.py` or any Kelly/exposure constant — this is a C7 monitoring
  threshold only, unrelated to C4 risk sizing.

---

## Decision Requested of the DS

Authorize a follow-on task (proposed T-370, next available per `TODO_NEXT.md`) to:
(a) compute MLB-native `BRIER_BASELINE_MLB`/`ECE_BASELINE_MLB` from the current resolved MLB paper book,
(b) draft the superseding ADR registering those constants, and
(c) enable the `calib_monitor` cron line for MLB once that ADR is accepted.

If the DS prefers to wait for a larger MLB sample before fitting these constants (analogous to the
sample-adequacy concerns already governing GG-004/APR-0024), that is also a valid disposition — this APR
asks for a decision, not a specific answer.

---

## Disposition Record

| Date | Action | By |
|---|---|---|
| 2026-07-15 | Drafted, submitted PENDING | GG-burndown-even session (even-numbered gap sweep) |
| 2026-07-16 | ACCEPTED — "Adopt as proposed", in-session directive | Earl Ignacio |
| 2026-07-16 | Implemented via ADR-0046: `BRIER_BASELINE_MLB=0.2190`/`ECE_BASELINE_MLB=0.0680` (n=261) derived and wired into `run_mlb_paper_trade.py`/`run_resolve_mlb.py`; calib_monitor cron enabled; GG-044 closed RESOLVED; GG-124 registered as a distinct follow-on gap (dead C7 alarm-ladder finding) | GG-easy-sweep session (T-374) |
| 2026-07-17 | Renumbered at merge time: the in-session "GG-124" collided with an independent already-merged upstream session's own GG-124 — this session's gap is now **GG-125** (project renumbering precedent; unmerged side renumbers). See `DECISION_LOG.md` Numbering note. | GG-easy-sweep session (T-374) |
