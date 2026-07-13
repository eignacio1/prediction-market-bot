**RETIRED 2026-07-12 (T-348/GG-107).** Superseded by `ITERATION_PLAN_v3.md`. Most workstreams closed: T-336 (regression-anchor fix), T-337 (full-suite cert), T-338 (`clean_n`/`n*` publication), T-339 (APR-0024, accepted 2026-07-12 — supersedes the flat 30/150/500 heuristic with per-band `clean_n >= n*`), T-341/T-342 (per-band monitor scheduling + T4M-PROJ flat-sizing MC, both DONE per `DECISION_LOG.md` 2026-07-11). **Two items remain genuinely open and are carried forward by v3, not closed by this retirement:** T-340 (GG-105 Component A tercile re-run — calendar-gated to ~2026-07-19/20, clean epoch must age first) and T-343 (C3 recalibration ADR — hard-gated on `clean_n >= n*`, not yet met for either active band as of 2026-07-12). Moved from repo root to `11_MEMORY_HANDOFF/` as a historical artifact; content below reflects 2026-07-11 planning-time state only.

---

# Iteration Plan v2 — Post-Verification Hardening & Edge-Verdict Path

**Author:** analytical-copilot session, 2026-07-11
**Status:** PROPOSAL — task IDs assigned **T-336 – T-343** (this session). Basis: highest T-in-use at
assignment was T-335, highest GG was GG-108. New gaps use **GG-109+**. **Not yet committed to
`SESSION_CLAIMS.md`** — formally reserve via `scripts/claim_session.sh` before starting, and re-check
highest-in-use at that moment (the v1 plan's IDs drifted once already — expect reassignment).

**Context:** v1 (T-320–335, Workstreams A–E) is complete and was audit-verified 2026-07-11: logic-epoch
provenance (238/238 positions tagged), per-band monitor, power calc, property/golden gate, ledger-driven
MC, and meta-hygiene all landed with correct math and correct schema fit. The audit surfaced **one real
defect** (a live-data regression anchor, see T-336) and could not run the full suite in-sandbox. This plan
greens the board, then converts the now-built tooling into an actual edge verdict — without tuning on an
inadequate sample.

**Governing principle (unchanged):** an item is DONE only when (a) covered by a test that failed before the
change, (b) reproducible from a clean checkout, and (c) leaves an audit trail. No item resolves on "looks right."

---

## Window 1 — Green the board (do first; unblocks trust in every downstream verdict)

### T-336 (N-01) — Kill live-data regression anchors
- **Do:** `tests/test_band_monitor.py::TestT1RegressionAnchor` asserts an exact Fisher p (0.246) against the
  *live, growing* `REAL_PORTFOLIO` file; it now reads 0.359 and fails. The verdict assertions still pass —
  the math is stable, the anchor design is wrong. Repoint the anchor to a frozen, registered `SNAP-*`
  fixture; assert **verdict + a p-value range**, not an exact float. Sweep `test_band_monitor.py`,
  `test_power_calc.py`, and any other new test for the same "exact-stat-against-live-file" pattern and convert.
- **Why:** violates the project's Data-Snapshot Discipline; anchors must be reproducible from frozen data.
- **Exit:** anchor reads a `SNAP-*` id; test green; a grep shows no remaining exact-stat assertions against
  live portfolio/ledger files.
- **Depends on:** none. **First.**

### T-337 (N-02) — Full-suite regression certification
- **Do:** Run the complete (~2,400) test suite on real hardware / CI (the sandbox 45s wall blocked it).
  Confirm green, capture the count, record it in the session handoff.
- **Exit:** full-suite green count committed; band-monitor + power-calc test files added to the CI job so they
  run every push (not just ad-hoc).
- **Depends on:** T-336 (so the run is actually green).

---

## Window 2 — Convert tooling into a decision (the strategic payoff)

### T-338 (N-03) — Publish clean_n vs n* per band
- **Do:** Run `scripts/run_power_calc.py` live; publish, per band, **clean_n vs n\*** (the variance-derived
  sample needed to distinguish edge>0 from edge=0) plus ETA-to-adequacy at observed cadence.
- **Exit:** a dated artifact + governance-hook/dashboard line showing `clean_n / n* / ETA` per band.
- **Depends on:** Window 1 green.

### T-339 (N-04) — Re-base the G6 gate on n* (needs APR)
- **Do:** Amend G6 to reference `clean_n ≥ n*` instead of the flat 30/150 heuristic. This is a gate revision
  → requires an APR (operator/DS sign-off), not a unilateral model change (Hard Rule 3).
- **Exit:** APR drafted + signed; G6 language updated in MEMORY_BANK/gate docs to the variance-derived target.
- **Depends on:** T-338.

### T-340 (N-05) — Close the GG-105 edge-formula audit
- **Do:** Complete Component A (tercile/Fisher re-run) once T4M-PROJ's clean epoch ages ~14 days / crosses
  the clean_n threshold the audit specified; land a verdict on GG-105.
- **Exit:** GG-105 → RESOLVED with a verdict artifact; DECISION_LOG entry.
- **Depends on:** clean-epoch aging (calendar-gated), not on other tasks.

---

## Window 3 — Make monitoring continuous, and cover the T4 sizing gap

### T-341 (N-06) — Schedule the per-band monitor + wire drift into C7
- **Do:** Cron/systemd-schedule the per-band anti-predictive + calibration monitor to emit a **dated verdict
  artifact** each run; wire an anti-predictive or calibration-slope breach into the C7 monitoring tier so it
  alarms automatically (warn-only first, per the existing GG-099 cadence pattern).
- **Exit:** scheduled job live; a synthetic anti-predictive fixture trips the C7 alarm in test.
- **Depends on:** Window 1 green.

### T-342 (N-07) — Forward MC for the T4M-PROJ flat-sizing regime
- **Do:** The current MC only models T1-style proportional compounding. T4M-PROJ bets ~$0.47 flat and has
  **no forward ruin/growth projection**. Extend the ledger-driven MC (or add a flat-stake mode) to cover it,
  and report its own {floor/operational/ceiling} band with bootstrap CIs.
- **Exit:** `mc_forward_projection.py` produces a T4M-PROJ projection from its own ledger; regression anchor
  vs the T1 baseline preserved.
- **Depends on:** none (D-workstream infra already exists).

---

## Window 4 — Calibration remediation (GATED — must not start early)

### T-343 (N-08) — C3 recalibration ADR *(conditional)*
- **Do:** **Only once `clean_n ≥ n*` (from T-338)** and *if* the per-band monitor shows T1 mis-calibration:
  open a C3 recalibration ADR (Platt refit / feature review). This is the real edge work.
- **Guard:** starting before the sample is adequate = tuning on noise, which the operator directive explicitly
  forbids. This item stays BLOCKED until T-338 clears the adequacy bar.
- **Exit:** ADR opened with a falsifiable recalibration hypothesis, or an explicit "no action — calibration
  adequate" decision logged.
- **Depends on:** T-338 (hard gate).

---

## Suggested sequencing (each row ≈ one terminal window)

1. **T-336 → T-337** — green the board (anchor fix, then full-suite CI certification)
2. **T-338** — clean_n vs n* published  *(parallel: T-342 flat-sizing MC, independent)*
3. **T-339, T-340** — gate re-base (APR) + GG-105 closure
4. **T-341** — continuous monitor + C7 wiring
5. **T-343** — recalibration, GATED on T-338

**Priority logic:** Window 1 must land first — a red suite makes every downstream verdict untrustworthy.
Window 2 is the strategic payoff (turns the sample question into a dated, gated decision). Window 3 hardens
monitoring and closes the T4 projection gap. Window 4 is the actual edge work and is deliberately gated.

## Assumptions | Risks | Validation | Confidence
- **Assumptions:** IDs reassign at claim-time (expect it). GG-105's clean-epoch aging threshold is as its
  scope doc specifies.
- **Key risks:** (1) T-343 is the tempting pull-forward — the gate on it is the whole point of v1's provenance
  work; honor it. (2) The anchor-fix pattern (T-336) must be applied everywhere, or the same red-test drift
  recurs. (3) T-339 is a gate revision — do not self-approve; route through APR.
- **Validation:** every window ends on a green full-suite run + a committed artifact; MC changes preserve the
  saved-baseline regression anchor.
- **Confidence:** HIGH that the v1 nodes are correct and schema-fit; the strategic edge verdict stays
  LOW-confidence and gated until `clean_n ≥ n*`.
