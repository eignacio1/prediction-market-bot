# Runbook: Model Drift Response — Prediction Market Trading Bot

**Purpose:** Step-by-step procedure for responding to detected model drift. Covers each level of the drift response ladder from L1 Watch through L4 Kill.  
**Owner (role):** Model Owner (MO) + Risk and Compliance Owner (RCO)  
**Last reviewed:** 2026-05-22  
**Next review:** After first live drift event; after G5 (monitoring wired in); update if thresholds revised  
**Staleness triggers:** Drift thresholds revised at G4; drift event reveals procedure gap; new drift metric added  
**Upstream links:** MONITORING_DRIFT_PLAN.md, MODEL_CARD.md, RUNBOOK_kill-switch.md  
**Downstream links:** RID_LOG.md, ARTIFACT_REGISTRY.md, 03_DECISIONS/ (if new ADR needed)  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 7/10 — Procedure defined; specific thresholds placeholders until G4 evidence

---

## Drift Response Ladder Summary

| Level | Metric Condition | Auto Action | Manual Required | Owner |
|-------|-----------------|-------------|----------------|-------|
| L1 — Watch | Brier rolling avg > baseline + 0.02 | Log alert | None required immediately | MO |
| L2 — Alert | Brier rolling avg > baseline + 0.05 | Auto-alert P2 | Review within 24h; evaluate halt | MO + RCO |
| L3 — Pause | Brier rolling avg > baseline + 0.10 | Auto-halt new positions | Manual review before re-enable | MO + RCO |
| L4 — Kill | Any kill threshold breach | Kill switch (RUNBOOK_kill-switch.md) | Full incident response | C7 (auto) |

---

## L1 — Watch Response

**Trigger:** Rolling Brier score > baseline + 0.02 over 30-event window.

### Procedure

1. **Log the L1 event** in RID_LOG.md:
   - Timestamp, rolling Brier value, baseline, delta
   - Recent event context (any unusual market conditions?)

2. **Increase monitoring frequency:**
   - Standard cadence: post-resolution Brier computation
   - L1 cadence: also compute after each new resolved event

3. **Observe for 10 more events:**
   - If Brier returns below baseline + 0.02: Log return to normal; L1 resolved
   - If Brier stays elevated or rises to L2: Escalate

4. **No trading halt required at L1.** Position sizing continues normally.

---

## L2 — Alert Response

**Trigger:** Rolling Brier score > baseline + 0.05 over 30-event window.  
**Time budget:** Aware within 60 seconds; manual review complete within 24 hours.

### Step 1 — Acknowledge and Log

```
RID_LOG.md entry:
- Level: L2
- Timestamp: <ISO-8601>
- Rolling Brier: <value>
- Baseline Brier: <value from MODEL_CARD.md>
- Delta: <value>
- Window: 30 events (events listed: <event IDs>)
- ECE (if available): <value>
- Mean edge: <value>
```

### Step 2 — Diagnose (within 24 hours)

Investigate potential causes:

| Hypothesis | How to Check |
|-----------|-------------|
| Market regime change (new information environment) | Review recent events for pattern shifts; compare event types in drift window vs training distribution |
| Feature distribution shift (data drift) | Check recent DS-01/feature distributions vs training; flag if attributes have shifted |
| Low event count (statistical noise) | Is 30-event window large enough? Brier variance at this sample size |
| Calibration failure (systematic over/under confidence) | Plot reliability diagram on recent events; check ECE |
| Outlier event distorting window | Remove single outlier; recompute Brier; if resolves, note in log |

### Step 3 — Evaluate Halt

After diagnosis:

| Diagnosis | Action |
|----------|--------|
| Statistical noise (confirmed by bootstrapped CI) | Resume; log noise finding; continue monitoring |
| Outlier event (one-off) | Resume with note; shorten window observation |
| Suspected feature drift | **Halt new positions**; do not escalate to L3 auto; log as voluntary L3 |
| Calibration failure | **Halt new positions**; initiate model investigation |
| Unknown cause | **Halt new positions**; conservative response |

**No bypass.** Any halt decision must be logged in RID_LOG.md before execution.

### Step 4 — If No Halt: Monitor and Set Resolution Criteria

Define in advance: "This L2 is resolved when rolling Brier returns below baseline + 0.02 for 10 consecutive events."

---

## L3 — Pause Response

**Trigger:** Auto-halt via C7 (Brier > baseline + 0.10) OR voluntary halt from L2 investigation.  
**State:** No new positions opened. Existing positions run to expiration or are manually closed.

### Step 1 — Confirm Halt State

```bash
# Confirm no new orders being submitted
python -m bot.status --check c5
# Expected: "C5 halted — new order submission disabled"

# Confirm existing positions
python -m bot.status --check positions
```

### Step 2 — Log L3 Event

```
RID_LOG.md entry:
- Level: L3
- Trigger: AUTO / VOLUNTARY
- Timestamp halt initiated: <ISO-8601>
- Rolling Brier at trigger: <value>
- Open positions at halt: <count, list>
- Estimated time to position expiration: <date>
```

### Step 3 — Root Cause Investigation

Required before any restart:

1. Pull all resolved events in the drift window from C6 audit log
2. Recompute Brier score independently (verify C7 metric is correct)
3. Plot reliability diagram on drift window events
4. Identify whether drift is in: (a) feature distribution, (b) model calibration, (c) edge calculation, (d) market structure
5. Document findings in RID_LOG.md

### Step 4 — Decision: Restart vs. New Model

| Finding | Path |
|---------|------|
| Transient drift (regime passed; Brier recovering) | Re-enable after Brier recovers; document as noise; monitor closely |
| Confirmed feature drift | New ADR required: feature re-engineering and model retrain (CHANGE_CONTROL.md Class A) |
| Confirmed model miscalibration | New ADR required: model version with recalibration (CHANGE_CONTROL.md Class A) |
| Model distribution shift (strategy no longer viable) | New ADR required: revisit strategy class (may supersede ADR-0002) |

**No restart without MO + RCO sign-off logged in RID_LOG.md.**

### Step 5 — If Restart Approved

```bash
# Re-enable C5 (paper or live)
python -m bot.execution --enable --reason "L3 resolved: <brief reason>" --operator "Earl Ignacio"

# Observe for 10 events before unattended operation
```

---

## L4 — Kill Response

**Trigger:** Kill switch auto-triggered by C7 on kill threshold breach.

**Procedure:** See **RUNBOOK_kill-switch.md**. This runbook takes over at L4.

After kill switch procedure is complete, return here for model drift root cause analysis (L3 Step 3 applies).

---

## New ADR Trigger Conditions

The following drift findings require a new ADR before any trading resumes:

1. **Feature distribution shift confirmed** → ADR for feature re-engineering
2. **Model recalibration required** → ADR for new model version
3. **Strategy class revisit** → ADR superseding ADR-0002
4. **Risk limit change in response to drift** → ADR for limit change

ADR process: CHANGE_CONTROL.md Class A. Requires G4-equivalent evidence for the new model or strategy.

---

## Drift Event Log Template

Every L2+ drift event gets an entry in RID_LOG.md:

```
## DRIFT-[YYYY-MM-DD]

**Level reached:** L2 / L3 / L4  
**Start date:** <ISO-8601>  
**Resolution date:** <ISO-8601 or OPEN>  
**Rolling Brier at peak:** <value>  
**Baseline Brier:** <value from MODEL_CARD.md>  
**Root cause (confirmed/suspected):** <description>  
**Action taken:** <resume / halt / new ADR>  
**ADR created:** <ADR ID or N/A>  
**Sign-off:** MO: <date> | RCO: <date>  
```
