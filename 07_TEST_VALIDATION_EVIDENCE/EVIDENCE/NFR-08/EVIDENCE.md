# NFR-08 Evidence — Change Control (ADR for major changes)

**Requirement:** DIR check: zero major changes in last 4 weeks without ADR reference.

**Populated:** 2026-07-06 (GG-075 remediation).

## Evidence

- `03_DECISIONS/GOVERNANCE_GAP_LOG.md` — 91 governance gaps tracked as of this session (GG-001 through GG-091), each with a discovery/resolution trail.
- `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` — every strategic decision logged same-session per Hard Rule 7, including this remediation pass itself.
- ADR count: 38+ ADR slots tracked (per the ACCEPTANCE_CRITERIA.md/VALIDATION_PLAN.md 2026-07-02 note); recent examples directly traceable to major changes: ADR-0039 (T4 MLB sub-band architecture), ADR-0040 (Kelly fraction de-rating, GG-071), ADR-0031 (v2 model retrain).

## The recursive finding (already noted in ACCEPTANCE_CRITERIA.md/VALIDATION_PLAN.md, reaffirmed here)

**GG-074 itself is the evidence that NFR-08's underlying intent — catching drift — periodically fails without an explicit trigger.** The structured grounding docs (01_SPEC/, 02_ARCHITECTURE_DESIGN/, 08_MODEL_RISK_GOVERNANCE/) went 5+ weeks without review despite major changes landing throughout, even though every individual change was itself properly ADR/decision-logged. Per-change discipline and periodic-drift discipline are different guarantees; this project had the first and not the second until GG-074 registered it. **As of this writing GG-074's audit of the remaining stale grounding docs is still in progress (a background review, not yet concluded) — the recurring review-trigger process fix has not yet been designed or committed.** See GG-074's own entry in `03_DECISIONS/GOVERNANCE_GAP_LOG.md` for its current, live status; do not treat this file as having closed that gap.

## Status

**ONGOING, discipline actively maintained** — per-change ADR/decision-log discipline is strong and continuously exercised (this remediation pass is itself an instance of it). The periodic-drift gap that NFR-08 didn't originally catch is **not yet closed** — it is tracked by GG-074, which is still open pending its process-fix design. This file documents the recursive finding; it does not itself resolve it.
