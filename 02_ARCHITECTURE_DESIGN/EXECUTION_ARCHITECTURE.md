# Execution Architecture — Prediction Market Trading Bot

**Purpose:** Define the execution-layer design: how forecasts become orders, how risk is enforced, how paper and live modes differ, and what gates separate them.  
**Owner (role):** Architecture Owner (AO)  
**Last reviewed:** 2026-07-02 (documentation-remediation pass — this document described C4/C5 as "gated and not yet implemented" and multiple formula parameters as "TBD" for over five weeks after they were actually confirmed and live; see corrections below). Prior substantive review: 2026-05-22  
**Next review:** On any execution-layer change (should have triggered at ADR-0004 acceptance 2026-05-28 and did not)  
**Staleness triggers:** Venue API confirmed; position sizing formula finalized; risk limits confirmed at G4; paper→live promotion  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, INTERFACES_CONTRACTS.md  
**Downstream links:** 01_SPEC/RISK_APPETITE_CONSTRAINTS.md, 08_MODEL_RISK_GOVERNANCE/MONITORING_DRIFT_PLAN.md, 10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_kill-switch.md  
**Decision references:** ADR-0001, ADR-0002, ADR-0004 (**ACCEPTED 2026-05-28, APR-0012** — was listed "pending"), ADR-0005 (still pending — accurate, this is the real G6 blocker), ADR-0006/ADR-0012/ADR-0026 (hard limits, now live — see RISK_APPETITE_CONSTRAINTS.md)  
**Confidence:** 8/10 — C4/C5 are implemented and running continuously in paper mode on both MLB and NBA books (Phase 6/7 ACTIVE); the design below accurately describes what was built. Live-mode (Phase 8) specifics remain correctly gated/undetermined pending G6.
**Decisions logged:** true — T-093 logged 2026-06-02: paper fill assumptions (mid-price, zero slippage), idempotency key (ticker+game_date), execution mode gate sequence, T1 decision cycle ordering. See DECISION_LOG.md 2026-06-02.

---

## Execution Modes

The system operates in four distinct modes, each with a hard gate before promotion:

| Mode | Active Components | Orders | Capital | Gate Required |
|------|------------------|--------|---------|--------------|
| Research — Backtest | C1, C2, C3, C6 | None | None | Phase 3 entry |
| Research — Live Inference | C1, C2, C3, C6, C7 | None | None | Phase 5 / G5 |
| Paper Trading | C1, C2, C3, C4 (sim), C5 (sim), C6, C7 | Simulated | Simulated | ADR-0004 |
| Live Capital | C1, C2, C3, C4 (live), C5 (live), C6, C7 | Real | Real | ADR-0005 + G6 |

**No execution component (C4, C5) may be activated without the corresponding ADR being accepted.**

---

## Decision Cycle — From Signal to Order

```
1. DATA INGESTION (C1)
   └─▶ Schema validation + Snapshot ID assignment
       └─▶ Output: validated record → C2

2. FEATURE DERIVATION (C2)
   └─▶ Apply transformations per DATA_FLOWS_LINEAGE.md
       └─▶ Enforce temporal cutoff (TI-01 through TI-04)
           └─▶ Output: feature vector (event_id, snapshot_id, feature_version, features, temporal_cutoff)

3. FORECAST GENERATION (C3)
   └─▶ Model inference (pinned model version — immutable post-deployment)
       └─▶ Compute: p_estimate, confidence_interval
           └─▶ Compute edge: p_estimate - market_implied_prob - vig
               └─▶ Emit recommended_direction: YES / NO / PASS
                   └─▶ Output: forecast record → C5 (Phase 6+) or terminal (research)

4. RISK EVALUATION (C5) ── GATED: Phase 6+
   └─▶ Read current portfolio state + RISK_APPETITE_CONSTRAINTS.md limits
       └─▶ Check: single-event exposure ≤ hard limit
           └─▶ Check: daily loss ≤ hard limit
               └─▶ Check: drawdown ≤ limit
                   ├─▶ [ALL PASS] Compute fractional Kelly size → APPROVED → C4
                   ├─▶ [ANY FAIL] REJECTED → log reason → C6, no order
                   └─▶ [LIMIT BREACH] KILL_SWITCH signal → C7 broadcasts halt

5. ORDER EXECUTION (C4) ── GATED: Phase 6+
   └─▶ Receive APPROVED signal from C5
       └─▶ Verify idempotency_key not already submitted (deduplication log)
           ├─▶ [Paper mode] Simulate fill; log to C6; update paper portfolio
           └─▶ [Live mode, Phase 8 only] Submit order to Venue API
               └─▶ Confirm fill; log to C6; update live portfolio

6. AUDIT LOGGING (C6) ── Always active
   └─▶ Receives events from all components
       └─▶ Appends to structured JSON Lines log (immutable)
           └─▶ Preserves: trace_id, snapshot_id, model_version, all decision fields

7. MONITORING (C7) ── Active from Phase 5
   └─▶ Reads metrics from C1–C5
       └─▶ Checks SLOs per SLA_SLO_SLI.md
           └─▶ Checks risk limits independently of C5
               ├─▶ Alert P1/P2/P3 on threshold breach
               └─▶ Broadcasts kill switch signal if CRITICAL threshold exceeded
```

---

## Kill Switch Design

The kill switch is the **primary safety mechanism**. It is not optional and has no bypass path without a formal ADR.

### Trigger Conditions (Auto)
- C5 detects: daily loss > hard limit
- C5 detects: drawdown > hard limit
- C7 detects: any component non-responsive
- C7 detects: audit log gap (C6 silent > threshold)
- C7 detects: Brier score breach (rolling window)

### Trigger Conditions (Manual)
- Operator issues kill command at any time, no justification required

### Kill Switch Behavior
1. Kill signal broadcast to all active components (C1–C7) simultaneously
2. Each component independently checks kill flag (not dependent on any single message delivery)
3. All new order submissions blocked immediately
4. In-flight orders: cancel if venue API supports cancellation (Phase 8 only)
5. All components emit final state log entry to C6 before halting
6. System enters HALTED state — requires manual operator restart

### Recovery from Kill Switch
1. Operator reviews C6 audit log to identify trigger
2. Operator must resolve trigger condition
3. Restart requires written confirmation (logged to C6 with trace_id)
4. In Phase 8 (live): restart requires both operator confirmation AND risk limit recertification

**Runbook:** `10_INFRA_OPERATIONS/RUNBOOKS/RUNBOOK_kill-switch.md`  
**Test requirement:** Kill switch must be drilled at G5 before any live use (FM-06 mitigation).

---

## Position Sizing — Fractional Kelly

The fractional Kelly formula governs all position sizes in paper and live modes.

**Formula:**
```
f* = (p_estimate - market_implied_prob) / (1 - market_implied_prob)   [full Kelly for YES]
f_live = f* × fraction                                                  [fraction = DEFAULT_KELLY_FRACTION = 0.25, confirmed live in risk.py]
position_size = min(f_live × available_capital, max_single_event_exposure_usd)   [$500 flat cap, ADR-0006]
```

**Constraints on position size:**
- `position_size` ≤ single-event hard limit (see RISK_APPETITE_CONSTRAINTS.md — $500 flat, not a % of capital as this document's Kelly-only framing implies)
- If `edge ≤ 0`: size = 0 (PASS — no order submitted); `MIN_EDGE_TO_APPROVE = 0.04` also gates sub-threshold edges (ADR-0020)
- Confidence-interval-based size reduction: **not confirmed as implemented** during this remediation pass — flagged rather than asserted either way; verify against `risk.py` directly if this matters for a decision
- Kelly fraction confirmed unchanged from the original 0.25 starting assumption *(corrected 2026-07-02 — was listed "TBD at G4" for over a month after G4 closed)*

**⚠️ GG-071 (registered SESSION 113, 2026-07-02):** this formula, applied at real bet cadence with proportional compounding, produces materially elevated ruin risk (46.45% 1yr probability of tripping the permanent 20%-drawdown kill switch for T1 MLB) despite real positive edge. See RISK_APPETITE_CONSTRAINTS.md and GOVERNANCE_GAP_LOG.md GG-071 — this formula's correctness at the single-bet level does not resolve the cadence question.

---

## Paper Trading Specifics (Phase 6)

Paper trading simulates the full decision cycle with zero real capital:

- C4 receives APPROVED orders from C5 but submits to a **simulated fill engine**, not the venue API
- Fill assumptions: market order fills at market_implied_prob (no slippage model in v1; TBD at ADR-0004)
- Paper portfolio state tracked in memory + persisted to C6 audit log
- All risk limits enforced identically to live mode — paper trading is NOT a sandbox for risk bypasses
- Paper results must be collected for ≥30 resolved bets (APR-0016, revised from an original 50 due to NBA seasonal calendar constraint) before G6 promotion is eligible — count+sign threshold alone does not clear G6; EXP-017 commercial validation (GG-004) is the binding blocker. See 01_SPEC/ROADMAP_MILESTONES.md Phase 7 for current count on each book. *(This bullet previously said "[N events TBD]" — resolved 2026-05-29 per APR-0016 but never updated here until this 2026-07-02 pass.)*

---

## Live Capital Specifics (Phase 8) — Not Yet Active

**Gate:** ADR-0005 accepted + G6 Release Gate cleared + ACC-0002 approved + APR-0009 signed

- C4 submits orders to venue API (venue TBD — ADR-0003)
- `idempotency_key` required on every order submission
- Order confirmation loop: submit → confirm fill → log → update portfolio
- On network failure: wait for confirmation; do NOT retry without verifying order was not received (FM-05)
- Maximum retry attempts: TBD at ADR-0004 (design decision)
- No automated retraining in production — model version frozen at paper→live promotion

---

## Phase Gate Enforcement

```
Phase 3 Research ──▶ G5 Ops Gate ──▶ Phase 5 Live Inference
                                             │
                                      ADR-0004 accepted
                                             │
                                             ▼
                                      Phase 6 Paper Trading
                                             │
                               [≥N paper events, G6 evidence]
                                             │
                                      ADR-0005 accepted
                                      + G6 Release Gate
                                      + ACC-0002
                                      + APR-0009
                                             │
                                             ▼
                                      Phase 8 Live Capital
```

**No shortcutting this sequence.** Each gate requires explicit ADR acceptance. ADRs are immutable once accepted.
