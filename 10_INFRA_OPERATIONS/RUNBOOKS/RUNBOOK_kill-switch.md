# Runbook: Kill Switch — Prediction Market Trading Bot

**Purpose:** Step-by-step procedure for activating, verifying, and recovering from a kill switch event. This runbook governs both automatic (C7-triggered) and manual kill switch activation.  
**Owner (role):** Model Owner (MO) + Infrastructure Operator (IO)  
**Last reviewed:** 2026-05-22  
**Next review:** After first kill switch drill (G5); update after any real kill switch event  
**Staleness triggers:** Kill switch implementation changed; component added; recovery procedure revised; real event reveals gap  
**Upstream links:** EXECUTION_ARCHITECTURE.md (kill switch design), RESILIENCE_FAILURE_MODES.md (FM-04, FM-06), MONITORING_DRIFT_PLAN.md (L3/L4 response), SLA_SLO_SLI.md (C7 SLOs)  
**Downstream links:** RID_LOG.md, KNOWN_ISSUES.md, APPROVALS_REGISTER.md  
**Decision references:** ADR-0001, NFR-03  
**Confidence:** 8/10 — Procedure is well-defined; exact commands TBD until Phase 5 implementation

---

## Overview

The kill switch is the primary emergency response for this system. There is no other emergency override path. When triggered, it must halt all pipeline components within **≤60 seconds** (NFR-03).

**Kill switch = total halt. It is not a partial pause or a rate limiter.**

---

## Trigger Conditions

### Automatic Triggers (C7)

C7 monitors the following and auto-triggers without operator action:

| Trigger | Threshold | Source |
|---------|-----------|--------|
| Daily loss limit breach | Loss ≥ daily limit (RISK_APPETITE_CONSTRAINTS.md) | C4 → C7 |
| Session loss limit breach | Loss ≥ session limit | C4 → C7 |
| Maximum position size breach | Single position > limit | C4 → C7 |
| Simultaneous open positions > max | Count > max | C4 → C7 |
| Drift kill threshold | Rolling Brier > baseline + 0.10 | C7 drift calculator |
| C4 Risk Engine unavailable with open position | Any connectivity failure | C7 health check |
| C6 Audit Logger failure (write error) | Any write failure | C6 health check → C7 |

### Manual Triggers

Operator manually triggers kill switch when:
- Anomalous market behavior observed
- Suspicion of order duplication or execution error
- Venue API errors ≥ 3 consecutive
- Any situation where operator is uncertain system is behaving correctly
- **When in doubt, trigger the kill switch. Recovery is cheap. Unexpected live losses are not.**

---

## Kill Switch Activation Procedure

### Step 1 — Trigger (≤5 seconds)

**If automatic:** C7 has already triggered. Proceed to Step 2 to verify halt.

**If manual:**
```bash
# Manual kill switch command (exact command TBD at Phase 5 implementation)
python -m bot.kill_switch --trigger --reason "MANUAL: <reason>" --operator "Earl Ignacio"
```

The kill switch script must:
1. Send SIGTERM to all pipeline processes
2. Close all open network connections to venue API
3. Cancel any pending orders (if venue API is reachable)
4. Write kill switch event to C6 audit log

---

### Step 2 — Verify Halt (≤60 seconds from trigger)

Verify all components have stopped:

```bash
# Check for any running pipeline processes
ps aux | grep -E "bot\.(c1|c2|c3|c4|c5|c6|c7|pipeline|ingestion|forecast|execution)"

# Confirm no open orders (check C6 last entry)
tail -n 20 logs/audit.jsonl | python -m bot.audit.check_open_orders

# Confirm C5 Execution Engine is down
python -m bot.status --check c5
```

**Expected result:** Zero running pipeline processes. No open orders in flight.

**If processes are still running after 60 seconds:** This is a P1 SLO breach (SLA_SLO_SLI.md ALT-006). Kill processes manually:

```bash
# Force kill all pipeline processes (use only if SIGTERM failed)
pkill -9 -f "bot\.(pipeline|execution|forecast)"
```

---

### Step 3 — Log the Event (within 5 minutes)

Log the kill switch event immediately:

```
RID_LOG.md entry:
- Timestamp: <ISO-8601>
- Trigger type: AUTO (C7) / MANUAL
- Trigger reason: <specific reason>
- Halt time: <measured ms from trigger to full halt>
- Components confirmed halted: C1, C2, C3, C4, C5, C6, C7
- Open orders at time of trigger: <count>
- Open orders cancelled: <count>
- Open orders NOT cancelled (venue unreachable): <count>
- P&L at time of trigger: <paper> or <live>
```

---

### Step 4 — Assess Situation

Before any restart, the operator must assess:

| Question | Assess How |
|----------|-----------|
| What triggered the kill switch? | C7 alert log; C6 audit log |
| Were all orders successfully cancelled? | C6 last execution log; venue account check |
| Is there any open position at the venue? | Log into venue account manually; reconcile |
| Was the trigger a real risk event or false positive? | Review C7 drift metrics; review C6 P&L log |
| Is the system safe to restart? | All questions below answered affirmatively |

**Do not restart until all open positions are confirmed cancelled or reconciled.**

---

### Step 5 — Recovery Decision

After assessment:

| Trigger was... | Recovery path |
|---------------|---------------|
| Automatic limit breach (real) | Fix root cause (log to RID_LOG.md); ADR if risk limit change needed; manual restart after RCO sign-off |
| Automatic drift threshold (real drift) | Log drift event; follow RUNBOOK_model-drift.md; new ADR required before restart |
| C7/C6 component failure | Fix component; test in ENV-01; restart paper/live only after fix verified |
| Manual trigger (verified anomaly) | Resolve anomaly; log root cause; manual restart after operator sign-off |
| False positive (retrospective) | Log false positive; review thresholds with evidence; restart after 15-minute observation |

**Written decision required** for any restart logged in RID_LOG.md. No silent restarts.

---

### Step 6 — Restart (Only After Step 5 Complete)

```bash
# Restart pipeline in Paper or Live mode
python -m bot.pipeline --env ENV-02  # paper
# OR
python -m bot.pipeline --env ENV-03  # live capital (only if G6 cleared)

# Verify C7 is monitoring within 60 seconds of startup
python -m bot.status --check c7
```

Observe for 5 minutes after restart before returning to unattended operation.

---

## Kill Switch Drill Procedure (Pre-G5 Required)

The kill switch must be drilled and timed before any live use (TC-009, TC-010).

### Drill Setup
1. Start pipeline in paper trading mode (ENV-02) with simulated orders
2. Confirm C7 is active and logging
3. Verify test positions are open

### Drill Execution
1. Manually trigger kill switch
2. Start timer at trigger moment
3. Confirm halt time ≤ 60 seconds
4. Log result in TEST_STRATEGY.md (TC-009, TC-010)

### Drill Pass Criteria
- All processes halted: ✅ required
- Simulated orders cancelled: ✅ required
- Kill event in C6 log: ✅ required
- Halt time ≤ 60 seconds: ✅ required (NFR-03)

**If any criterion fails, drill is FAILED. Block G5 gate until drill passes.**

---

## Known Failure Modes

| Failure | Likelihood | Response |
|---------|-----------|----------|
| SIGTERM not received by subprocess | LOW | Add explicit subprocess kill in kill switch implementation |
| Venue API unreachable at kill time | MEDIUM | Log uncancelled orders; reconcile manually; never assume they lapsed |
| Kill switch script itself crashes | LOW | Add watchdog process; fallback: OS-level process kill |
| Kill switch triggered while C6 unavailable | LOW | Kill switch proceeds without log; restore log from other sources post-event |

---

## References

- NFR-03: Kill switch ≤60s halt requirement
- RISK_APPETITE_CONSTRAINTS.md: Hard limits that trigger automatic kill
- MONITORING_DRIFT_PLAN.md: Drift kill threshold (L4)
- RESILIENCE_FAILURE_MODES.md: FM-04 (API outage), FM-06 (kill switch failure)
- RID_LOG.md: All kill switch events logged here
- RUNBOOK_model-drift.md: Drift-triggered kill switch recovery
