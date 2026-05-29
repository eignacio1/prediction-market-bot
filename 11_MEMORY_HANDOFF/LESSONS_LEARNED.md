# Lessons Learned — Prediction Market Trading Bot

**Purpose:** Document lessons from the prior iteration and any new lessons encountered during this build. Each lesson maps directly to a mitigation in the current architecture. This is a living document — new lessons are added as they are discovered.  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-05-29 (LL-008 conditional language; LL-009 pilot-before-infrastructure)  
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

### LL-008 — Conditional Language in Canonical Registers Is Not Documentation

**Observed / What happened:** During Phase 6 sprint (2026-05-29), the G6 evidence threshold was discussed and a DS decision was made to lower it from 50 to 30 bets. This was recorded in ROADMAP_MILESTONES.md as "The threshold *may* be revised downward to 30 resolved bets... via APR-0016 sign-off." APR-0016 was never created. In the next context window, the threshold appeared documented when it was not actually decided. The new session operated with the wrong G6 gate.

**Phase:** Phase 6 (2026-05-29)

**Impact:** New context window operated with the wrong G6 gate (50 bets, not 30). Strategic decision was lost. Required a full handoff audit to recover. Directly instantiates LL-001 (context rot) — the same failure mode that ended the prior iteration.

**Lesson:** "May be revised," "could be adjusted," "threshold may change," and all similar conditional language in APPROVALS_REGISTER, ROADMAP, or KNOWN_ISSUES is not documentation — it is a deferred decision that *looks* documented. Any conditional language in a canonical register is a governance flag. The decision must be formally made (DS sign-off, APR-XXXX) or the language must be replaced with "TBD — requires APR-XXXX before [date]." Conditional language that survives a context window transition is indistinguishable from a signed decision to the next context.

**Mitigation:**
- CHANGE_CONTROL.md: "Conditional Language Governance" section added — explicit red-flag list and resolution protocol
- MEMORY_BANK.md: Mid-Session Decision Protocol section added — write to DECISION_LOG immediately, not at session end
- /session-end: Step 1A updated to scan for conditional language in any artifacts modified this session
- APR-0016 signed retroactively (2026-05-29); all "50" references swept to "30"

**Status:** MITIGATED

---

### LL-009 — Pilot Experiment Before Infrastructure

**Observed / What happened:** During Phase 7 build-ahead (2026-05-29), full infrastructure components were built before experiments validated the hypotheses. TeamStatsStore + C1 schema extensions (T-075, 78 features FEATURE_VERSION 1.3.0) and ScoringDistributionModel (T-076) were fully implemented with 31+26 tests before EXP-012 and EXP-013 ran. Both hypotheses were falsified: HYP-006 (Δ Brier = 0.0000) and HYP-007 (NB Brier 0.2671 vs LR 0.2461). The infrastructure is sound but the hypothesis-specific use cases are stranded.

**Phase:** Phase 7 build-ahead (2026-05-29)

**Impact:** ~3-5 hours of implementation work on components whose primary use case was invalidated before they were built. FEATURE_VERSION reverted to 1.2.0. TeamStatsStore is dormant. The opp_def_rating feature is infrastructure without a home. The NB model's role is narrowed to multi-line pricing only.

**Lesson:** Run the minimal experiment to test the hypothesis BEFORE building the supporting infrastructure. A targeted script that evaluates the Brier delta on existing data is sufficient to confirm or falsify. Build the full component only if the hypothesis is confirmed. The sequencing rule is: hypothesis registered → minimal pilot experiment → CONFIRMED → full infrastructure build. Never build full infrastructure first, then test.

**Why this happens:** Building infrastructure feels productive. Experiments feel uncertain. The temptation is to "get the plumbing ready" so the experiment can run faster. But if the hypothesis fails, the plumbing is mostly wasted and the experiment queue advances without evidence.

**Mitigation:**
- /new-exp: Step 0 check added — confirm that supporting infrastructure is NOT being built ahead of pilot experiment confirmation
- DECISION_LOG: standing sequencing principle added (2026-05-29)
- Going forward: any T-0XX task that builds infrastructure for an unconfirmed hypothesis must be flagged as "contingent on EXP-YYY confirmation"

**Status:** MITIGATED

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
