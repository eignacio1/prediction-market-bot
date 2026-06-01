# Lessons Learned — Prediction Market Trading Bot

**Purpose:** Document lessons from the prior iteration and any new lessons encountered during this build. Each lesson maps directly to a mitigation in the current architecture. This is a living document — new lessons are added as they are discovered.  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-06-01 (LL-010 stub survival; LL-011 architecture coherence drift; LL-012 ARE WE COMPROMISED? watchdog)  
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

### LL-010 — Stubs Set at an Early Gate Survived Undetected Through Three Subsequent Gate Clearances

**Observed / What happened:** `_HARD_LIMITS["max_concurrent_positions"] = 10.0` was placed in `risk.py:94` at G4 with an explicit `# 10 concurrent open (stub)` comment and a module-level docstring note reading `MAX_CONCURRENT_POSITIONS — open position count limit (TBD at G4)`. The G4 gate review confirmed that the check *worked* — it was syntactically correct and the tests passed. It never asked whether 10 was the right number. Three subsequent gate clearances (G5, G6, G7) passed without the value being revisited. The system ran the first real game with 9/10 positions filled and one slot remaining before the count gate would have silently rejected Finals G2 bets.

**Phase:** G4 (stub set 2026-05-28) → G5 → G6 → G7 readiness sprint (gap discovered 2026-05-31)

**Impact:** Count gate was architecturally wrong for an 80-player, multi-band, multi-game system. Would have silently suppressed bet accumulation on every multi-game regular season night. Live gate check passed because the stub hadn't fired yet — not because it was correct.

**Lesson:** A governance scan that asks "does this work?" is not the same as a governance scan that asks "is this value correct for the architecture we just built?" Code stubs with `# TBD at G4` survive gate reviews when the gate review confirms *functionality* but not *architectural coherence*. Every stub that is set as a placeholder must be registered with a named gate for its resolution — and that gate must actually resolve it, not just clear the surrounding code.

**Mitigation:**
- Session-start scan Step 2 added: `grep -rn "# stub\|# placeholder\|# TBD\|# todo" src/` — any match is a governance debt
- GOVERNANCE_GAP_LOG.md (ADR-0007): gaps registered permanently so future sessions see this history
- ARE WE COMPROMISED? check (MEMORY_BANK.md): question 2 asks explicitly whether any stub predates Phase 5–7

**Status:** MITIGATED (ADR-0006: count gate deleted; ADR-0007: watchdog added)

---

### LL-011 — Architecture Built in Phases Without Coherence Checkpoints Against Phase-Zero Constraints

**Observed / What happened:** The T1–T5 execution band architecture, multi-band orchestrator, 80-player cohort, dual-window cron, and VenueRouter were all built across multiple sessions in Phases 5–7. Each was correct in isolation and passed its tests. No session asked: "The risk framework (C4) was designed at G4 for a smaller system — has any component we just built exceeded the assumptions C4 was built on?" The answer, had anyone asked, was yes: `max_concurrent_positions: 10` was set when the system had 10 players and one execution band. By Phase 7 it had 80 players, five bands, two cron windows, and 15 possible games per night.

**Phase:** Phase 5–7 build-out (2026-05-28 to 2026-05-31)

**Impact:** The system was operationally live with a risk framework that was 6x smaller than the execution architecture it was supposed to govern. This class of failure — architecture outgrowing its constraints — is invisible to standard governance scans that look for undocumented decisions. The decision *was* documented (the stub comment was there). What was missing was a mechanism to ask whether that documented decision was still valid.

**Lesson:** Incremental architecture build requires incremental coherence checkpoints. After any major Phase 5+ build, before the next gate review, ask: which Phase 0–4 decisions did we just render potentially obsolete? The cost of this question is 5 minutes. The cost of not asking is a live system running on wrong architecture.

**Mitigation:**
- ARE WE COMPROMISED? check (MEMORY_BANK.md) question 3: "Have the 3 largest builds since G4 been reviewed against G4-era hard limits?"
- ARE WE COMPROMISED? question 4: "Has any component interface evolved since risk limits were last calibrated?"
- Mid-session checkpoint trigger updated: any major component build now prompts a coherence check before the next task block

**Status:** MITIGATED (ARE WE COMPROMISED? watchdog added to session-start protocol)

---

### LL-012 — Context Rot Watchdog: ARE WE COMPROMISED?

**Observed / What happened:** The prior iteration failed to context rot → hallucination → contamination. The current iteration built Compass OS, ADRs, decision logs, gate reviews, session handoffs, and checkpoint protocols — all of which address the *documentation* dimension of context rot. None of them address the *architectural coherence* dimension. GG-001 through GG-003 (see GOVERNANCE_GAP_LOG.md) are proof that the documentation system was working — the stub comment was there, the `# TBD at G4` was there — but the architecture had grown past what the documented decision assumed, and nothing asked whether the document was still valid.

**Phase:** Discovered 2026-06-01 during T-102 remediation discussion

**Impact:** The system ran its first real game (NBA Finals G1, 2026-05-31) with a risk architecture that was incoherent with its execution architecture. The misalignment would not have been caught by any automated governance scan. It was caught by an operator asking: "Does this limit make sense given everything we've built?"

**Lesson:** Governance documentation is necessary but not sufficient. What is also required is a periodic *architectural integrity* question: does the current system, as a whole, make sense? Are there values, thresholds, or interfaces that were calibrated to an earlier, smaller version of this system and were never revisited? This question cannot be automated — it requires human judgment about coherence. It can, however, be prompted structurally.

**The question to ask at every session start:** ARE WE COMPROMISED?

This is not a rhetorical question. It has 5 specific sub-questions (see MEMORY_BANK.md — ARE WE COMPROMISED? section). Any "no" answer is a governance gap requiring registration in GOVERNANCE_GAP_LOG.md before implementation proceeds.

**The error this is designed to prevent:**
- Building a system that passes every test but fails at runtime because a G4-era assumption no longer holds
- Clearing gates because the code works, without asking whether the *values* are still correct
- Completing a session feeling productive because 10 tasks were checked off, while a structural misalignment accumulates

**What this is NOT:**
- A mandate to revisit every decision at every session — that would be paralysis
- A requirement that everything be correct before any work proceeds — the ARE WE COMPROMISED? check is a triage, not a freeze

**Mitigation:**
- ARE WE COMPROMISED? strategic integrity check added to MEMORY_BANK.md (mandatory, 5 questions, before any implementation)
- GOVERNANCE_GAP_LOG.md created (ADR-0007) — permanent record of process failures visible to every future session
- LL-010 and LL-011 in this file — specific past failures with their root causes, readable at session start

**Status:** MITIGATED (ARE WE COMPROMISED? watchdog added; GOVERNANCE_GAP_LOG.md created)

---

### LL-013 — Cohort Scope Not Matched to Competition Scope

**Observed / What happened:** The NBA Finals began NYK vs SAS. The EXP-005 feature matrix (the live inference data source) contained zero SAS players. Victor Wembanyama was registered in cohort.py (v2, 2026-05-29) but the feature pull was never run for v2 players — the matrix was built from the v1 50-player pull on 2026-05-28, one day earlier. Result: the bot placed paper bets exclusively on NYK players for Finals G1 with zero SAS-side coverage. The scope gap was not caught during any gate review because no gate checklist asked: "does the cohort cover all teams in the active competition?"

**Phase:** Discovered 2026-05-31, Finals G1 (Jun 3) prep

**Impact:** All Finals bets are structurally one-sided (NYK only). The G6 evidence being accumulated is unrepresentative — the bot cannot demonstrate edge on Finals participants from both sides. This reduces the value of paper trading evidence for the live capital decision.

**Lesson:** The cohort and feature matrix must be kept in sync with the active competition bracket. When the competition scope changes (playoff round advances), the following checklist must run before the next game day:
1. Who are the new matchup participants?
2. Which of those players are in `cohort.py`?
3. Which of those players have feature data in the active feature matrix?
4. For any gap in (3): run a targeted data pull and update the matrix.

This is not a model correctness issue — it is a **coverage protocol** failure. The model generalizes to unseen players; the pipeline simply never saw them.

**Mitigation:**
- Standing pre-round protocol: before each playoff round, run `python -c "check_finals_coverage.py"` (check cohort vs. bracket participants)
- Targeted pull script (`run_add_players.py`) created 2026-05-31 for quick roster expansion
- DECISION_LOG updated: all prior paper bets invalidated; G6 counter reset to 0/30
- Feature matrix updated with SAS roster before Finals G1 (2026-06-03)

**Status:** MITIGATED (targeted pull executed 2026-05-31; matrix updated before Finals G1)

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
