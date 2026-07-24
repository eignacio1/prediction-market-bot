# Monitoring and Drift Plan — Prediction Market Trading Bot

**Purpose:** Define how model performance is monitored in production, what constitutes drift, and what response is required.  
**Owner (role):** Model Owner (MO) + Risk and Compliance Owner (RCO)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review, resolving GG-095. `monitor.py`'s Brier ladder is a genuine **3-level** scheme (L1 watch / L2 alert / L3 pause) — the "L4" row in this document's Drift Response Ladder table below does not correspond to a Brier-driven auto-kill in `monitor.py`; real kill-switch authority is driven independently by `risk.py`'s `MAX_DAILY_LOSS_PCT`/`max_drawdown_pct` (confirmed firing correctly). GG-095's fix (T-247, 2026-07-07) also found and fixed a real bug: `get_drift_snapshot()` had been assigning `ALERT_L4_KILL` at the L3 threshold crossing, so a Brier-drift breach alone was auto-firing a full undocumented kill switch — now correctly assigns `ALERT_L3_PAUSE` at that crossing. **More importantly for this document specifically: the L3 row below claims "Auto-halt new position opens" — GG-095's resolution confirmed by direct grep across `risk.py`/`paper_trader.py` that no such enforcement exists (no `pause`/`halt_new`/`block_new` hits).** L3 currently only logs an ERROR-severity alert; it does not block new positions. This is a real gap between documented and built behavior, not yet closed — flagged to the operator per GG-095's resolution text as an open decision point (C4↔C7 wiring), not fixed in this pass. T-094 (2026-06-02)'s absolute 4-level Brier thresholds are superseded by monitor.py's relative-delta 3-level design per GG-095.  
**Next review:** G4 Evidence Gate (confirm drift thresholds with evidence); G5 (wire monitoring into C7)  
**Staleness triggers:** Drift threshold adjusted (requires evidence basis); new metric added; live deployment; incident reveals monitoring gap  
**Upstream links:** MODEL_CARD.md, RESILIENCE_FAILURE_MODES.md (FM-03), ARCHITECTURE_OVERVIEW.md (C7)  
**Downstream links:** 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_model-drift.md, SLA_SLO_SLI.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 6/10 — Monitoring design is complete; thresholds are placeholders pending G4 evidence
**Decisions logged:** true — T-094 logged 2026-06-02: L1–L4 Brier thresholds (0.255/0.265/0.275/0.280), win rate thresholds (54%/52%/48%), 30-event rolling window, Brier-over-log-loss metric choice. See DECISION_LOG.md 2026-06-02.

**⚠️ Corrected 2026-07-06 (GG-074 remediation) — confirmed directly against `src/prediction_market_bot/c7_monitoring/monitor.py`.** G4 and G5 have both closed, and this monitoring plan is live, not a design placeholder:
- **Thresholds are confirmed and implemented, not "placeholders pending G4 evidence"** (Confidence line and the "Drift Threshold Confirmation" section below both still use placeholder language). `monitor.py`'s module header states the confirmed G4 TEST-set baseline directly: `Brier=0.2416, ECE=0.0247`. The relative-delta ladder in this document's own "Drift Detection Metrics"/"Drift Response Ladder" tables (baseline+0.02 / +0.05 / +0.10 for L1/L2/L3) matches the production implementation (`BRIER_L1_DELTA`/`BRIER_L2_DELTA`/`BRIER_L3_DELTA` in `monitor.py`) — that mechanism is correct and live.
- **Discrepancy flagged above is now RESOLVED — GG-095, 2026-07-07, T-247 (superseded this correction note; see 2026-07-23 update below for the live state).**
- **C7/Monitoring Architecture table's "Phase 5+"/"Phase 3+" phase-active labels undersell current status** — G5 closed weeks ago; C7 monitoring, drift detection, and kill-switch wiring are live in production on the VPS, not merely phase-gated future work.
- This document remains sport-agnostic in its mechanism description and does not need re-derivation for MLB specifically, unlike some of the other files in this remediation pass — the baseline (0.2416/0.0247) is currently NBA-model-derived (per ADR-0004/G4); confirm whether MLB's T1 model has its own drift baseline computed separately before relying on this document for MLB monitoring specifics.

---

## Drift Detection Metrics

### Primary Metric — Rolling Brier Score

| Field | Detail |
|-------|--------|
| Metric | Brier score over rolling N-event window |
| Window | 30 events (placeholder; confirmed at G4) |
| Baseline | Brier score from held-out test set at G4 |
| Alert threshold | Rolling Brier score > baseline + 0.05 |
| Kill threshold | Rolling Brier score > baseline + 0.10 (2× alert threshold) |
| Rationale | Persistent Brier degradation indicates model is no longer tracking reality |

### Secondary Metric — Calibration Drift

| Field | Detail |
|-------|--------|
| Metric | Expected calibration error (ECE) on rolling window |
| Window | 30 events |
| Baseline | ECE from held-out test set at G4 |
| Alert threshold | ECE > baseline + 0.05 |

### Supporting Metric — Edge Distribution Shift

| Field | Detail |
|-------|--------|
| Metric | Distribution of `edge = p_estimate - market_implied_prob` |
| Alert condition | Mean edge drops below 0 on rolling window |
| Interpretation | Model is no longer generating positive expected value |

---

## Drift Response Ladder

| Level | Trigger | Response | Owner |
|-------|---------|----------|-------|
| L1 — Watch | Brier rolling avg > baseline + 0.02 | Log alert; increase monitoring frequency; no action | MO |
| L2 — Alert | Brier rolling avg > baseline + 0.05 | Auto-alert P2; manual review within 24h; evaluate halt | MO + RCO |
| L3 — Pause | Brier rolling avg > baseline + 0.10 | Documented response: auto-halt new position opens. **Actual shipped behavior (GG-095, confirmed 2026-07-07): ERROR-level alert only — no enforcement wiring exists to actually block new positions.** Manual review required before re-enabling | MO + RCO |
| L4 — Kill | Any kill threshold breach (see RISK_APPETITE_CONSTRAINTS.md) | Kill switch trigger; halt all pipeline. **Driven by `risk.py`'s `MAX_DAILY_LOSS_PCT`/`max_drawdown_pct`, not by this module's Brier ladder** (GG-095) | C7 (auto) |

**No bypass path for L3 or L4 without a written decision logged to C6 and RID_LOG.md.**

---

## Monitoring Architecture

| Component | Role | Phase Active |
|-----------|------|-------------|
| C7 — Monitoring | Real-time metric collection; threshold evaluation; alert emission; kill switch trigger | Phase 5+ |
| C6 — Audit Logger | Persists all forecast records with outcome data when available | Phase 3+ |
| Drift calculator | Post-resolution Brier score computation; fed to C7 | Phase 5+ |

**Monitoring requires event resolution data (DS-03).** Resolution data ingested separately per TI-03 (never in feature store).

---

## Model Lifecycle Under Drift

```
Normal Operation
     │
     ▼ [Brier > baseline + 0.05]
L2 Alert → Manual Review
     │
     ├─▶ [Transient / no real drift] → Resume + note in C6
     │
     └─▶ [Confirmed drift] → Halt new positions
                              │
                              ▼
                     New ADR required:
                     - Diagnose drift cause
                     - New model version OR
                     - Strategy class revisit (ADR-0002 supersession)
                     - G4-equivalent evidence for new model
```

---

## Drift Threshold Confirmation

**All thresholds marked as placeholders here.** Thresholds must be:
1. Proposed by RCO at G4 with Brier evidence from held-out test set
2. Confirmed by MO and MV with confidence interval analysis
3. Recorded in MODEL_CARD.md and here with the evidence basis documented

*Threshold confirmation is a G4 gate requirement.*
