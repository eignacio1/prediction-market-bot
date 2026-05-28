# ADR-0001 — Adopt Compass OS as Project Governance Framework

**Status:** ACCEPTED  
**Date:** 2026-05-21  
**Deciders:** DS (Director/Sponsor), PO (Product Owner)  
**Supersedes:** None (new project iteration — previous iteration retired)  
**Superseded by:** N/A  

---

## Context

The previous iteration of the prediction market trading bot failed due to **severe context rot and data/process contamination**. Key failure modes identified:

1. Artifacts became stale without detection; documentation drifted from reality
2. Shadow documents accumulated outside the canonical directory
3. No formal gate process existed to prevent premature promotion of components
4. Handoff between sessions degraded because no Context Pack discipline was maintained
5. No audit trail for why decisions were made

A new governance framework is required that treats context integrity as a first-class engineering concern, equivalent in priority to model correctness and capital safety.

---

## Decision Drivers

| Driver | Weight |
|--------|--------|
| Prevent recurrence of context rot | CRITICAL |
| Enable solo-operator reproducibility across sessions | HIGH |
| Provide a gate process to prevent premature live capital deployment | CRITICAL |
| Minimal overhead relative to governance value | MEDIUM |
| Must be implementable without external tooling | HIGH |

---

## Options Considered

### Option A — Compass OS (Project Directory Compass OS Workflow)
A structured directory-based governance system with: universal artifact headers, anti-context-erosion invariants, six minimum enforcement controls, cadence structure (daily/weekly/biweekly/monthly/quarterly), seven integration gates (G0–G6), six health metrics (M1–M6), artifact lifecycle management, and Context Pack discipline for session handoff.

### Option B — Lightweight ad-hoc documentation
Maintain documentation informally; no formal gate process; no cadence structure. Lower overhead, higher recurrence risk.

### Option C — External project management tooling (Jira, Notion, etc.)
Use a commercial PM platform as the governance spine. Higher feature set; introduces external dependency; no guarantee of artifact co-location with code and data.

---

## Decision

**Option A — Compass OS** is adopted as the sole governance framework for this project.

**Rationale:**
- Option B is the root cause of the previous iteration's failure. It is explicitly rejected.
- Option C introduces an external dependency and splits the canonical record across two systems, reproducing the shadow-doc failure pattern.
- Compass OS co-locates all artifacts in the project directory alongside code and data, making context drift detectable through the directory itself.

---

## Consequences

**Positive:**
- Universal artifact headers make staleness detectable at a glance
- Gate process (G0–G6) prevents premature promotion
- Context Packs enable reliable session handoff regardless of conversation context window limits
- M1 freshness metric provides an objective health signal for the directory
- Immutable ADR record ensures no major decision is undocumented

**Negative / Trade-offs:**
- Solo operator must maintain cadences without peer accountability
- Initial directory build is significant upfront effort (intentional investment)
- Compass OS adds process overhead; some overhead is by design (anti-erosion)

**Constraints introduced:**
- All major decisions require ADRs (immutable once accepted)
- No real capital deployment until G6 Release Gate
- Anti-shadow-doc rule: any document used to make a decision must enter the directory within 72 hours
- M1 < 65% triggers gate freeze

---

## Follow-Ups

| Action | Owner | Due |
|--------|-------|-----|
| Instantiate full directory skeleton | DS | 2026-05-21 |
| Complete 00_ADMIN module | DS/PO | 2026-05-22 |
| Complete 01_SPEC module | PO | 2026-05-24 |
| Complete 02_ARCHITECTURE_DESIGN module | AO | 2026-06-13 |
| Initialize MEMORY_BANK.md | DS | 2026-05-25 |
| Run first DIR and produce health report | DS | 2026-05-28 |

---

## Revisit Triggers

- Compass OS framework is found to be insufficient for live capital governance (revisit at G5)
- New external tooling becomes available that provides materially better context integrity guarantees
- Solo-operator model changes (team scaling)

---

## Links

- Upstream: PROJECT_CHARTER.md, SCOPE_IN_OUT.md
- Downstream: All artifacts in 00_ADMIN through 11_MEMORY_HANDOFF
- Approval: APR-0001 (DONE 2026-05-21)
