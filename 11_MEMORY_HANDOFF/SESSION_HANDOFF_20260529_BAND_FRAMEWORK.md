# Session Handoff — 2026-05-29 Band Framework Session

**Trigger:** Context compaction imminent — user-warned; forced handoff protocol
**Prior handoff:** SESSION_HANDOFF_20260529_2230.md (context summary was from that window)

---

## Status

- **Phase:** 6/7 ACTIVE (G0–G5 all closed)
- **Tests:** 533/533 (unchanged this session — no new tests written; existing tests still pass)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron running (dual-window + resolve; unchanged)
- **Paper bets:** 0/30 resolved — G6 gate (APR-0016, 30 bets required NOT 50)

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Band assignment is a structural requirement for all strategies (A–K) | T1–T5 existed as docs only; B–K unregistered; any strategy can be added without declaring band. Fix: StrategyBandSpec + BandRegistry | execution_bands.py + BAND_ASSIGNMENT_FRAMEWORK.md + DECISION_LOG 2026-05-29 | AO |
| band_status ACTIVE/SKELETON/BLOCKED is machine-readable — SKELETON strategies cannot execute bets | T2/T3 running on VPS cron unvalidated; machine-readable status is the only guardrail against silent activation | execution_bands.py StrategyBandSpec.band_status | AO |
| T2 and T3 are SKELETON — EXP-012 falsified T2 injury signal; T3 has no EXP | T2/T3 produce signals but do not drive bet sizing. T1 is the sole ACTIVE execution band for Strategy A | BAND_ASSIGNMENT_FRAMEWORK.md P3; DECISION_LOG 2026-05-29 | DS |
| ArbBandSignal is a separate schema from BandSignal — routed by ArbBandOrchestrator | BandSignal = directional YES/NO + Kelly; ArbBandSignal = multi-leg + net_profit_usd. Incompatible; cannot share orchestrator | execution_bands_orchestrator.py; DECISION_LOG 2026-05-29 | AO |
| Kalshi T3: max_api_calls_per_decision=1 (350ms P90 latency vs 500ms SLA budget) | Only 150ms headroom at T3. Any second API call violates SLA. Hard constraint in VenueBandConstraint, not just convention | execution_bands.py VENUE_BAND_CONSTRAINTS[V-001, T3] | AO |
| Checkpoint mechanism built as proactive structural protocol (/checkpoint command) | Context compacted in prior window without any handoff file written; /session-end was never invoked | .claude/commands/checkpoint.md + MEMORY_BANK.md invariant #10 | AO |

---

## Critical "Do Not Forget" Items

1. **T2/T3 are SKELETON — NOT validated.** Paper bets in this bot are T1-only. If anyone asks "are T2/T3 active?" — yes they run on cron, but their signals do not drive bet sizing. SKELETON status blocks execution.

2. **G6 threshold is 30 resolved paper bets, NOT 50.** APR-0016 signed 2026-05-29. Any document still saying "50" is stale.

3. **arb/ folder = reference-only.** Gate is APR-0010 (not yet signed). No arb code from that folder is incorporated into active pipelines.

4. **BAND_REGISTRY.validate() must be added to bot startup.** Currently the registry is populated but validate() is not called at startup. This is a TODO — add it to the startup sequence before G6 deployment.

---

## Tasks Completed This Session

| Block | Item | Result |
|-------|------|--------|
| Governance | /checkpoint command created | ✅ .claude/commands/checkpoint.md + TEMPLATE_CHECKPOINT.md |
| Governance | MEMORY_BANK.md invariant #10 added | ✅ No task block starts without checkpoint |
| Governance | session-end.md updated with /checkpoint distinction | ✅ |
| Governance | Anchored grep pattern fixed in TEMPLATE_SESSION_HANDOFF.md | ✅ |
| Arb review | ARB_FRAMEWORK.md created | ✅ CANONICAL; decisions_logged: true |
| Arb review | STRATEGY_OVERVIEW.md C/D/E rewritten | ✅ Band decision tree tables; detection ≠ execution |
| Arb review | EXECUTION_BANDS.md arb section added | ✅ |
| Arb review | DECISION_LOG: 3 arb entries | ✅ |
| Band framework | BAND_ASSIGNMENT_FRAMEWORK.md created | ✅ CANONICAL; PDTP 5-pass; 9/10 quality |
| Band framework | execution_bands.py: StrategyBandSpec + VenueBandConstraint + BandRegistry + BAND_REGISTRY + VENUE_BAND_CONSTRAINTS | ✅ All 11 strategies + G + H registered |
| Band framework | execution_bands_orchestrator.py: ArbLegSignal + ArbBandSignal + ArbBandDecision + ArbBandOrchestrator | ✅ Schema separation implemented |
| Band framework | DECISION_LOG: 5 band framework entries | ✅ |
| Band framework | CHECKPOINT_20260529_BAND_FRAMEWORK.md | ✅ |
| Checkpoints | CHECKPOINT_20260529_2345.md | ✅ Governance sprint |
| Checkpoints | CHECKPOINT_20260530_0015.md | ✅ Arb review block |

---

## Files Modified This Session

**New files created:**
- `02_ARCHITECTURE_DESIGN/ARB_FRAMEWORK.md`
- `02_ARCHITECTURE_DESIGN/BAND_ASSIGNMENT_FRAMEWORK.md`
- `11_MEMORY_HANDOFF/CHECKPOINT_20260529_2345.md`
- `11_MEMORY_HANDOFF/CHECKPOINT_20260530_0015.md`
- `11_MEMORY_HANDOFF/CHECKPOINT_20260529_BAND_FRAMEWORK.md`
- `11_MEMORY_HANDOFF/SESSION_HANDOFF_20260529_BAND_FRAMEWORK.md` (this file)
- `.claude/commands/checkpoint.md`
- `00_ADMIN/TEMPLATES/TEMPLATE_CHECKPOINT.md`

**Modified:**
- `02_ARCHITECTURE_DESIGN/STRATEGY_OVERVIEW.md` (C/D/E sections)
- `02_ARCHITECTURE_DESIGN/EXECUTION_BANDS.md` (arb section added)
- `03_DECISIONS/DECISION_LOG/DECISION_LOG.md` (+8 entries this session)
- `11_MEMORY_HANDOFF/MEMORY_BANK.md` (invariants #9, #10 + checkpoint protocol)
- `.claude/commands/session-end.md` (checkpoint distinction section)
- `00_ADMIN/TEMPLATES/TEMPLATE_SESSION_HANDOFF.md` (anchored grep fix)
- `src/prediction_market_bot/execution_bands.py` (+StrategyBandSpec, VenueBandConstraint, BandRegistry, BAND_REGISTRY, VENUE_BAND_CONSTRAINTS)
- `src/prediction_market_bot/execution_bands_orchestrator.py` (+ArbLegSignal, ArbBandSignal, ArbBandDecision, ArbBandOrchestrator)

---

## Outstanding Tasks (from TODO_NEXT.md + this session)

### Operator-Required (blocked on Earl)
- **T-077:** Polymarket KYC at polymarket.com → API key provisioning → V-002 VenueBandConstraint latency measurement
- **T-091:** C7 paper P&L alert (WARNING at total_pnl < -$50) — needs DS threshold sign-off first

### Governance Debt (pre-existing, low priority)
- **T-093–T-099:** Extract decisions from 7 canonical documents → DECISION_LOG

### From This Session (new TODOs)
- Add `BAND_REGISTRY.validate()` call to bot startup sequence
- Update CHANGE_CONTROL.md: "band assignment change" triggers ADR requirement
- Update EXECUTION_BANDS.md: add "Band Assignment Protocol" section linking to BAND_ASSIGNMENT_FRAMEWORK.md
- Update STRATEGY_OVERVIEW.md: add BandSpec summary table for A–K (user requested total alignment)
- Add Kalshi T3 API latency measurement task (empirical validation of 350ms P90 estimate)

### Paper Trading (ongoing)
- **T-070:** 0/30 resolved paper bets accumulated — G6 gate active; cron running on VPS

---

## G6 Gate Status

| Gate criterion | Status |
|---------------|--------|
| 30 resolved paper bets + positive P&L | 0/30 — NBA season (Finals ongoing; ~2026-06-22 end) |
| EXP-010 EV evidence | ✅ (+$0.0958/bet) |
| VPS deployed + cron stable | ✅ 157.230.91.33 |
| Kill switch tested | ✅ APR-0013 (KS-C8D7D90AF942) |
| ADR-0005 draft | ⬜ Dark period build target |

---

## Architecture State at Session End

### Code (src/prediction_market_bot/)
- `execution_bands.py`: ExecutionBand enum + BandConfig + BAND_CONFIGS + **StrategyBandSpec** + **VenueBandConstraint** + **BandRegistry** + **BAND_REGISTRY** (11 strategies) + **VENUE_BAND_CONSTRAINTS**
- `execution_bands_orchestrator.py`: BandSignal + BandDecision + MultiBandOrchestrator + **ArbLegSignal** + **ArbBandSignal** + **ArbBandDecision** + **ArbBandOrchestrator**
- All other modules: unchanged

**Bold = added this session.**

### Strategy Status Summary
| Strategy | Type | Band Status | Active Phase | Evidence |
|----------|------|------------|-------------|---------|
| A | model_edge | ACTIVE | Phase 6 | EXP-010 ✅ |
| B | model_edge | SKELETON | Phase 7 | Pending EXP |
| C | arb_lock | BLOCKED | Phase 7 | APR-0010 required |
| D | arb_spread | BLOCKED | Phase 8 | DS-02 required |
| E | arb_route | SKELETON | Phase 7 | EXP-014 ✅ (T1 only) |
| F | model_edge_joint | BLOCKED | Phase 7 | New ADR required |
| G | sizing | ACTIVE | Phase 6 | ADR-0004 + EXP-010 ✅ |
| H | risk_envelope | ACTIVE | Phase 6 | ADR-0004 + APR-0013 ✅ |
| I | model_edge | SKELETON | Phase 7 | EXP-013 incomplete |
| J | momentum | BLOCKED | Phase 7 | DS-02 required |
| K | execution_scalp | BLOCKED | Phase 8 | Phase 8 infra required |

---

## Security/Governance Invariants (PRESERVED — DO NOT LOSE)

1. arb/ folder = REFERENCE ONLY — do not incorporate into any active work until ADR accepted (APR-0010). See REJECTED_OPTIONS.md RO-001.
2. No real capital until G6 Release Gate formally cleared (APPROVALS_REGISTER.md, DS sign-off, ADR-0005 accepted)
3. ADRs are immutable once accepted. Changes require a superseding ADR. No silent changes to strategy, risk limits, or model.
4. No automated retraining in production. Frozen model policy.
5. Zero hardcoded secrets (NFR-05). Vault/env-var protocol only.
6. Kill switch must halt all components within ≤60 seconds (NFR-03).
7. G6 evidence gate = 30 resolved paper bets with positive P&L (APR-0016). NOT 50.
8. Strategic decisions made in holistic reviews must be captured in DECISION_LOG.md AND APPROVALS_REGISTER.md before session end.
9. No strategic or architectural document may be marked CANONICAL without `**Decisions logged:** true`.
10. No task block starts without a checkpoint for the block just completed.

---

## Next Session First Actions

1. Read this file + MEMORY_BANK.md + TODO_NEXT.md
2. Confirm: `grep -rn "^\*\*Decisions logged:\*\* false" 02_ARCHITECTURE_DESIGN/ 08_MODEL_RISK_GOVERNANCE/ 01_SPEC/` → check for new debt
3. Execute user's direction: update STRATEGY_OVERVIEW.md with BandSpec summary table for A–K (user: "incorporate across all quant strategies")
4. Update CHANGE_CONTROL.md + EXECUTION_BANDS.md with Band Assignment Protocol
5. Add BAND_REGISTRY.validate() to bot startup routine
