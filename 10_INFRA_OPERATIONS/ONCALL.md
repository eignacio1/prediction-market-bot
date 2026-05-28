# On-Call Protocol — Prediction Market Trading Bot

**Purpose:** Define the on-call responsibility model for this single-operator system. Establishes when the operator must be available, response time expectations, and escalation procedures when the operator is unavailable.  
**Owner (role):** Director/Sponsor (DS) + Infrastructure Operator (IO)  
**Last reviewed:** 2026-05-22  
**Next review:** G5 (paper trading begins — on-call becomes real); G6 (live capital — highest on-call obligation)  
**Staleness triggers:** Trading hours change; live capital activated; operator availability change  
**Upstream links:** SLA_SLO_SLI.md, RUNBOOKS/, RISK_APPETITE_CONSTRAINTS.md  
**Downstream links:** KNOWN_ISSUES.md, RID_LOG.md  
**Decision references:** ADR-0001  
**Confidence:** 8/10 — Protocol is clear; live capital on-call obligation is the highest risk in a solo system

---

## On-Call Model

This is a **single-operator system**. There is no secondary on-call rotation, no escalation to a team, and no 24/7 monitoring service. This creates a structural gap that must be explicitly managed.

The primary mitigation is: **the kill switch is the on-call stand-in for non-responsive periods.** Any scenario the operator cannot respond to in time must be handled automatically by C7 + kill switch.

---

## On-Call Obligations by Phase

### Phase 3-4 (Research / Batch Processing)

| Obligation | Detail |
|-----------|--------|
| Active monitoring required | NO — batch jobs only; no live positions |
| Response time required | None — next business day is acceptable for batch anomalies |
| Kill switch required | NO — no live capital or paper positions |
| Operator availability | Best effort; check results after each batch run |

---

### Phase 5-7 (Paper Trading)

| Obligation | Detail |
|-----------|--------|
| Active monitoring required | YES — during pipeline runs |
| Response time | P2 alerts: within 24 hours; P1 alerts: as soon as practicable |
| Kill switch | ACTIVE — C7 auto-triggers; operator should review within 24h |
| Operator availability | Check pipeline status at start/end of each trading session |
| Unattended operation | PERMITTED — C7 and kill switch are the unattended response |
| Minimum check cadence | Daily at minimum; after any P2 alert log |

**Paper trading on-call note:** Paper trading losses are simulated. The consequences of missing an alert are limited to learning value, not capital. The protocol is lower-stakes than live capital but establishes habits.

---

### Phase 8+ (Live Capital)

| Obligation | Detail |
|-----------|--------|
| Active monitoring required | YES — during all trading hours |
| Response time | P1: within 60 minutes of alert; P2: within 4 hours |
| Kill switch | ACTIVE and TESTED — must have passed TC-009, TC-010 drill before G6 |
| Operator availability | Must be reachable (phone/alert) during any period with open positions |
| Unattended operation | PERMITTED within a session — not for extended periods (>4 hours) with open positions |
| Overnight positions | PROHIBITED unless kill switch is confirmed active and drift monitoring is live |

---

## Alert Response Time Targets

| Alert Level | Phase 5-7 (Paper) | Phase 8+ (Live) |
|-------------|-------------------|-----------------|
| P1 (critical) | As soon as practicable | ≤ 60 minutes |
| P2 (alert) | ≤ 24 hours | ≤ 4 hours |
| P3 (watch) | Next cadence review | ≤ 24 hours |

---

## Unattended Operation Protocol

The pipeline may run unattended (operator not actively watching) only when:

1. C7 monitoring is confirmed active (heartbeat check on startup)
2. Kill switch has been drilled and passed ≤60s halt (TC-009, TC-010)
3. All hard limits in RISK_APPETITE_CONSTRAINTS.md are set in C4
4. No open investigation or drift event is active

**During extended unattended periods (>4 hours, live capital only):**
- All open positions must have a time-to-expiration that is either within the unattended window OR protected by stop limits
- Operator must check pipeline status immediately upon return
- If kill switch triggered during unattended period: treat as P1; full incident response before any restart

---

## Operator Unavailability Protocol

If the operator anticipates unavailability (travel, illness, etc.) during a period with open live positions:

1. **Preferred:** Close all positions before unavailability begins
2. **If positions cannot be closed:** Ensure kill switch is active; set conservative position limits in C4; notify C7 health check monitoring
3. **Do not leave open positions unattended for >24 hours** with live capital active
4. **Document in RID_LOG.md:** Any planned unavailability with open positions

---

## Escalation

In a solo system, "escalation" means explicit documentation that the operator has acknowledged an issue and is taking a specific action. There is no human team to escalate to.

For any P1 event:
1. Log to RID_LOG.md immediately (timestamp, event, operator acknowledgment)
2. If operator cannot respond in time: kill switch is the response (self-activates via C7)
3. After event: post-mortem in RID_LOG.md; consider whether on-call gap was exploited by the incident

---

## On-Call Checklist (Live Capital)

Before each trading session with live capital:

- [ ] C7 monitoring confirmed active
- [ ] Kill switch confirmed responsive (periodic drill check)
- [ ] No open P1 or P2 alerts from prior session
- [ ] Risk limits confirmed correct in C4
- [ ] Operator will be reachable for duration of session
- [ ] Session logged as started in C6

After each trading session:

- [ ] Review C6 audit log for anomalies
- [ ] Review C7 drift metrics for any L1/L2 movement
- [ ] Confirm no unexpected open positions at session end
- [ ] Log session end in operator journal (CHANGELOG or STATUS_REPORTS)
