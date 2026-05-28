# Lessons Learned — Prediction Market Trading Bot

**Purpose:** Document lessons from the prior iteration and any new lessons encountered during this build. Each lesson maps directly to a mitigation in the current architecture. This is a living document — new lessons are added as they are discovered.  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-05-22  
**Next review:** After each gate; after any incident or near-miss; at project close  
**Staleness triggers:** New lesson discovered; mitigation found to be insufficient; gate reveals new failure mode  
**Upstream links:** ADR-0001 (Compass OS adoption rationale), RESILIENCE_FAILURE_MODES.md  
**Downstream links:** OPEN_QUESTIONS.md, KNOWN_ISSUES.md, RID_LOG.md  
**Decision references:** ADR-0001  
**Confidence:** 9/10 — Prior iteration failures are well-documented; new lessons will be added

---

## Prior Iteration Failures

These are the identified failure modes from the prior iteration. Each has a direct mitigation in the current architecture.

---

### LL-001 — Context Rot: Undocumented Decisions

**What happened:** Decisions were made verbally or implicitly during development sessions. When a new context window was opened, the system had "forgotten" these decisions and would either repeat them (inefficiency) or contradict them (data contamination, scope drift).

**Impact:** Prior iteration was abandoned. Entire work product invalidated.

**Mitigation:**
- Every decision has an ADR or CHANGELOG entry (CHANGE_CONTROL.md)
- ADRs are immutable once accepted; no silent changes
- Anti-shadow-doc rule: any document used to make a decision enters the directory within 72 hours
- MEMORY_BANK.md is the first artifact read in any new context window

**Verification:** M3 (ADR coverage) and M5 (risk register currency) health metrics

---

### LL-002 — Data Contamination: No Temporal Integrity

**What happened:** Data handling in the prior iteration did not enforce temporal separation between features and outcomes. Look-ahead bias was possible and potentially present in experiment results.

**Impact:** Any model trained in the prior iteration may have inflated performance metrics due to data contamination. Results cannot be trusted.

**Mitigation:**
- TI-01 through TI-04 rules in DATA_FLOWS_LINEAGE.md are mandatory
- `temporal_cutoff` field is required on all features
- Outcome data has a separate ingestion path; never enters feature store (TI-03)
- TC-001 and TC-002 (automated temporal overlap check) required before any experiment
- RO-005 explicitly prohibits random shuffling of temporal data

**Verification:** TC-001, TC-002; hold-out test set date audit

---

### LL-003 — Scope Creep: arb/ Strategy Incorporated Without Validation

**What happened:** The prior iteration began incorporating arbitrage logic from the arb/ folder without a formal decision, validation of the strategy class, or assessment of how it changes the system's risk profile.

**Impact:** Unvalidated strategy in production code; no evidence base; scope undefined; risk limits not calibrated for arbitrage execution.

**Mitigation:**
- ADR-0002 explicitly adopts forecast-only strategy class
- arb/ folder designated reference-only (RO-001 in REJECTED_OPTIONS.md)
- Incorporating arb/ requires a new ADR (APR-0010 placeholder)
- arb/ appears in 7 artifacts as explicitly outside scope; invariant #1 in MEMORY_BANK.md

**Verification:** SCOPE_IN_OUT.md audit; SYSTEM_CONTEXT.md boundary check

---

### LL-004 — Missing Audit Trail: No Way to Reconstruct Decisions

**What happened:** The prior iteration had no structured logging of forecast decisions, position sizing calculations, or execution events. When performance was questioned, there was no audit trail to review.

**Impact:** Cannot diagnose model failures, identify bugs, or demonstrate that the system behaved as designed.

**Mitigation:**
- C6 (Audit Logger) is always active from Phase 3+ and logs all forecast, risk, and execution events
- Every log entry has a correlation ID chain (Snapshot ID → Feature run ID → Forecast ID → Risk eval ID → Order ID)
- TC-007 validates audit completeness before G5
- Data retention policy (CAT-04): minimum 2 years

**Verification:** TC-007; C6 implementation audit at G5

---

### LL-005 — Context Erosion: Each Session Reconstructed State Incorrectly

**What happened:** Each new context window in the prior iteration would re-read partial documentation and reconstruct a subtly different understanding of the system's current state. Over many sessions, these errors accumulated.

**Impact:** Decisions were made on incorrect premises; conflicting requirements emerged; prior decisions were overridden silently.

**Mitigation:**
- MEMORY_BANK.md is the canonical restore point — must be the first artifact read in any new context
- CP-YYYY-MM-DD (Context Packs) snapshot full project state at each gate
- Universal artifact headers with staleness triggers and next review dates
- Compass OS cadence: weekly review of all artifacts with staleness triggers
- M1 (artifact freshness) health metric tracks header currency

**Verification:** Weekly artifact freshness check; MEMORY_BANK.md currency review

---

## New Lessons (This Iteration)

*Populated as new lessons are discovered during Phase 1+.*

---

### LL-006 — Deferred Decisions: Precision Kills Velocity

**Observed:** During directory build, there was a temptation to specify exact values (Kelly fraction, Brier thresholds, risk limits) even though the evidence base for those values doesn't exist yet.

**Lesson:** Specifying false precision on values that require evidence is worse than leaving them as TBD. A TBD with a clear resolution path (gate + evidence requirement) is more honest and more useful than an invented number.

**Mitigation already applied:**
- All thresholds marked explicitly as "placeholder; confirmed at G4"
- Open questions (OQ-011, OQ-012) track what values need evidence
- G4 Evidence Gate is the formal requirement for threshold confirmation

---

### LL-007 — Solo Operator Governance: Role Separation is Conceptual, Not Structural

**Observed:** In a solo project, "role separation" (DS, RL, MO, RCO) is enforced only by discipline. There is no structural check preventing the operator from bypassing their own governance.

**Lesson:** Document this gap explicitly. The mitigation is not a structural control (there isn't one in a solo system) — it is explicit accountability through the ADR + APPROVALS_REGISTER process. The act of writing "DS: sign-off date" forces explicit acknowledgment, which is better than nothing.

**Mitigation:**
- STAKEHOLDERS_RACI.md acknowledges all roles held by one person
- APPROVALS_REGISTER.md requires explicit sign-off per gate
- Compass OS cadence creates a rhythm of review that is harder to skip than a one-time check
- This lesson is flagged as ASM-006 (solo operator cadences are sustainable)

---

## Template for New Lessons

When a new lesson is discovered, add it here:

```markdown
### LL-XXX — [Title]

**Observed / What happened:** <what happened>  
**Phase:** <when this occurred>  
**Impact:** <what it cost>  
**Lesson:** <what we learned>  
**Mitigation:** <what was changed or confirmed>  
**Status:** MITIGATED / MONITORING / OPEN
```
