# ADR-0007 — Governance Gap Logging: GOVERNANCE_GAP_LOG.md as a Required Artifact

**Purpose:** Mandate a new governance artifact that registers process failures — decisions missed, thresholds that survived gate reviews wrong, and architectural coherence gaps — and extend the session-start protocol to catch the class of failure that produced GG-001 through GG-003.  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-06-01 (accepted)  
**Next review:** After any new gap is registered; at each gate  
**Staleness triggers:** New gap class discovered not covered by current scans; ARE WE COMPROMISED? questions need revision  
**Upstream links:** ADR-0001 (Compass OS), GOVERNANCE_GAP_LOG.md, LESSONS_LEARNED.md (LL-010–012)  
**Downstream links:** MEMORY_BANK.md (session-start protocol), TODO_NEXT.md  
**Decision references:** GG-001, GG-002, GG-003 (GOVERNANCE_GAP_LOG.md)  
**Confidence:** 10/10 — DS sign-off 2026-06-01

---

## Status

`ACCEPTED` — DS sign-off 2026-06-01

---

## Context

The current governance system (Compass OS + DECISION_LOG + gate reviews + session handoffs) was designed to prevent context rot — undocumented decisions that cause the next session to operate on wrong premises. It largely works for that problem.

It was not designed to catch a different failure class: **architectural coherence drift** — where a correctly-made early decision becomes *wrong* because the system architecture grew past the assumptions that underpinned it.

**GG-001 through GG-003** are three instances of this failure in a single incident:
- A stub set at G4 (`max_concurrent_positions: 10`) survived three gate clearances undetected
- The T1–T5 execution architecture was built piecemeal over multiple sessions without any check that the risk framework was updated to match
- No artifact or protocol existed to ask: "Does the current architecture still fit inside the risk framework we designed at G4?"

The prior session's governance scan asked:
1. Are there documents with `decisions_logged: false`?

It did not ask:
2. Are there `# stub` or `# placeholder` comments in source code that predate Phase 5–7?
3. Does every hard limit in `_HARD_LIMITS` still make sense given the current execution architecture?
4. Has any component built since G4 rendered a G4 decision obsolete?

---

## Decision

**Mandate two new governance mechanisms:**

### 1. GOVERNANCE_GAP_LOG.md (new required artifact)

Location: `03_DECISIONS/GOVERNANCE_GAP_LOG.md`

Registers every discovered governance process failure with:
- What decision/value/check was absent or wrong
- When it should have been caught
- Why it survived (which governance mechanism failed to catch it)
- Impact
- Resolution ADR/APR

Distinct from:
- `DECISION_LOG.md` — records decisions *made*
- `KNOWN_ISSUES.md` — records runtime bugs and technical debt
- `LESSONS_LEARNED.md` — records patterns for future avoidance

**Invariant**: Every governance gap must be registered here *before* remediation work begins. The registration is load-bearing — it documents the process failure independently of the fix.

### 2. ARE WE COMPROMISED? — Strategic Integrity Check

A mandatory 5-question check at session start, immediately following the governance scan. Lives in MEMORY_BANK.md. Cannot be skipped.

Questions (see MEMORY_BANK.md for the authoritative text):
1. Capacity check: does the C4 risk framework account for the full execution capacity currently deployed?
2. Stub survival check: any `# stub` / `# placeholder` / `# TBD` in src/ — was it set before Phase 5–7?
3. Architecture coherence check: have the 3 largest builds since G4 been reviewed against G4-era limits?
4. Interface evolution check: has any component interface evolved since risk limits were last calibrated?
5. Decision traceability check: is every threshold in `_HARD_LIMITS` traceable to a DECISION_LOG entry with a derivation methodology?

Any "no" answer to any question is a governance gap. Register it in GOVERNANCE_GAP_LOG.md before proceeding.

### 3. Extended session-start scan (3-step)

Step 1 (existing): `grep -rn "^\*\*Decisions logged:\*\* false"` in architecture/governance/spec dirs  
Step 2 (T-103): `grep -rn "# stub\|# placeholder\|# TBD\|# todo" src/`  
Step 3 (new): `grep -n "| OPEN" 03_DECISIONS/GOVERNANCE_GAP_LOG.md`

---

## Consequences

**Positive:**
- Future sessions that open this project will immediately see the full history of governance failures and know not to repeat them
- The ARE WE COMPROMISED? check creates a habit of asking strategic coherence questions, not just tactical "does this build?" questions
- GOVERNANCE_GAP_LOG.md separates "we fixed the bug" from "we fixed the system that allowed the bug"

**Risk:**
- Overhead at session start increases. Mitigation: the ARE WE COMPROMISED? check is 5 questions — approximately 2–3 minutes. The cost of another GG-001 incident is an entire session of remediation work and a live betting system running on wrong architecture.

---

## DS sign-off

Earl Ignacio, 2026-06-01
