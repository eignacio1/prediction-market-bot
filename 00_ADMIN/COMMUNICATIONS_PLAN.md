# Communications Plan — Prediction Market Trading Bot

**Purpose:** Define cadences, channels, escalation paths, and severity definitions for all project communications.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: verified current, no drift found. Cadence/escalation structure still matches practice; "Solo build" confidence note already covers the gap between the documented multi-role cadence and actual solo-operator execution.  
**Next review:** 2026-08-23  
**Staleness triggers:** New stakeholder added; cadence changed; channel deprecated; escalation path revised  
**Upstream links:** STAKEHOLDERS_RACI.md, PROJECT_CHARTER.md  
**Downstream links:** 04_EXECUTION/PLAN.md, 10_INFRA_OPERATIONS/ONCALL.md  
**Decision references:** ADR-0001  
**Confidence:** 8/10 — Solo build; structure ready for team scaling  

---

## Cadence Schedule

| Cadence | Frequency | Duration | Facilitator | Format | Output Artifact |
|---------|-----------|----------|-------------|--------|----------------|
| Execution Sync | Daily | 15 min | EL | Self-review | Updated TODO_NEXT.md + RID_LOG.md |
| Directory Integrity Review (DIR) | Weekly (Monday) | 60–90 min | DS | Self-audit | Directory Health Report (1 page) |
| Cross-Cutting Concerns Council (C4) | Weekly (Wednesday) | 60 min | AO / RCO | Self-review | New/updated ADRs, threat model, control mapping |
| Integration Review | Biweekly (Friday) | 60–120 min | AO | Self-review | Integration issues list; updated interface contracts |
| Gate Readiness Review | Monthly | 60–90 min | EL + DS | Self-review | Gate readiness decision (go/no-go) |
| Retrieval Drill + Retrospective | Quarterly | 90 min | DS | 10-question drill | Retrieval scorecard + remediation backlog |

---

## Escalation Path and Severity Definitions

| Severity | Definition | Examples | Response Time | Action |
|----------|-----------|----------|--------------|--------|
| P1 — Critical | System or governance integrity failure requiring immediate halt | Kill-switch trigger; capital loss exceeding daily limit; data contamination confirmed | Immediate | Halt execution; log incident; create postmortem |
| P2 — High | Material risk to delivery or governance without immediate system failure | Major assumption invalidated; gate blocker identified; ADR conflict | Within 1 hour | Create RID entry; escalate to relevant owner; schedule resolution |
| P3 — Medium | Quality or traceability issue that can be resolved in normal cadence | Stale artifact detected; broken link; missing ADR reference | Within 24 hours | Add to DIR agenda; assign owner + due date |
| P4 — Low | Minor cleanup or documentation gap | Typo; optional field missing; template deviation | Within 1 week | Add to TODO_NEXT; resolve at next DIR |

---

## Incident Channel

- **All P1/P2 events** are recorded in 10_INFRA_OPERATIONS/INCIDENTS_POSTMORTEMS/ within 24h of occurrence.
- **Incident record format:** See 00_ADMIN/TEMPLATES/TEMPLATE_RUNBOOK.md.
- **Post-incident:** Required updates to runbooks, architecture, monitoring plan, and/or ADR revision are recorded in the postmortem.

---

## Anti-Shadow-Doc Rule

Any document, spreadsheet, note, or artifact that is used to make a project decision must be moved into the directory or linked from MEMORY_BANK.md within **72 hours** of use. Undocumented decisions are treated as P3 events.
