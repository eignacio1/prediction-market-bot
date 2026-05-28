# Runbook — [Service / Procedure Name]

**Purpose:** Step-by-step operational procedure for [service/event]. Executable by someone other than the original builder.  
**Owner (role):** Operations Owner (OO)  
**Last reviewed:** YYYY-MM-DD  
**Next review:** YYYY-MM-DD or after each incident that touches this procedure  
**Staleness triggers:** System architecture change; interface contract change; incident reveals gap; G5 gate review  
**Upstream links:** 10_INFRA_OPERATIONS/OBSERVABILITY.md, 02_ARCHITECTURE_DESIGN/RESILIENCE_FAILURE_MODES.md  
**Downstream links:** 10_INFRA_OPERATIONS/INCIDENTS_POSTMORTEMS/  
**Decision references:** [Relevant ADRs]  
**Confidence:** X/10  

---

## Service / Job Name

[What system component or process does this runbook cover?]

## Trigger / Symptoms

[What condition or alert triggers use of this runbook? Include metric thresholds if applicable.]

## Severity

`P1` | `P2` | `P3`

---

## Triage Steps

1. [First thing to check]
2. [Second thing to check]
3. [Decision point: if X → go to Mitigation A; if Y → go to Mitigation B]

---

## Diagnostics (Logs / Metrics)

| What to check | Where to find it | What to look for |
|--------------|-----------------|-----------------|
| | | |

---

## Mitigations

### Mitigation A: [Name]
```
[Commands / steps]
```

### Mitigation B: [Name]
```
[Commands / steps]
```

---

## Rollback

```
[Steps to undo the change or restore the previous state]
```

**Verification:** [How to confirm rollback was successful]

---

## Escalation

| Condition | Escalate to | How |
|-----------|------------|-----|
| Mitigation fails | [Role] | [Channel / method] |
| Data integrity concern | RCO | Immediate |
| Capital at risk | PO / RCO | Immediate — halt first, then notify |

---

## Post-Incident Actions

- [ ] Create incident record in 10_INFRA_OPERATIONS/INCIDENTS_POSTMORTEMS/
- [ ] Review: does this runbook need updating?
- [ ] Review: does RESILIENCE_FAILURE_MODES.md need updating?
- [ ] Review: does MONITORING_DRIFT_PLAN.md need a new alert?
- [ ] Review: does this trigger an ADR revision?
