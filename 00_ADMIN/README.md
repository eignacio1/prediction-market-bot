# Prediction Market Trading Bot — Project Directory

**Purpose:** Navigation hub and canonical entry point for the Prediction Market Trading Bot project. Start here.  
**Owner (role):** Directory Steward (DS)  
**Last reviewed:** 2026-05-21  
**Next review:** 2026-06-04  
**Staleness triggers:** New module added; major scope change; phase gate passed; ownership transfer  
**Upstream links:** None (root artifact)  
**Downstream links:** All modules below  
**Decision references:** ADR-0001  
**Confidence:** 9/10 — Newly instantiated; content reflects Phase 0 baseline  

---

## What This Project Is

An automated prediction market trading bot, built from scratch with institutional governance, designed to progress from a research-only forecasting engine to a live-capital trading system. The bot ingests signals (starting with player/market attribute data), generates calibrated probabilistic forecasts, and — once promoted through formal gates — executes positions on prediction market venues. The previous iteration suffered severe context rot and data contamination; this directory is the primary countermeasure.

**Current phase:** Phase 0 — Directory Scaffolding + Governance Spine  
**Capital status:** Research-only. No real capital authorized. Live capital requires G6 Release Gate passage.

---

## Where to Find Things

| Need | Go to |
|------|-------|
| What the system does and why | [01_SPEC/VISION_OUTCOMES.md](../01_SPEC/VISION_OUTCOMES.md) |
| What is in and out of scope | [01_SPEC/SCOPE_IN_OUT.md](../01_SPEC/SCOPE_IN_OUT.md) |
| Hard risk limits and kill-switch conditions | [01_SPEC/RISK_APPETITE_CONSTRAINTS.md](../01_SPEC/RISK_APPETITE_CONSTRAINTS.md) |
| Full requirements + acceptance criteria | [01_SPEC/REQUIREMENTS.md](../01_SPEC/REQUIREMENTS.md) |
| System architecture and component map | [02_ARCHITECTURE_DESIGN/ARCHITECTURE_OVERVIEW.md](../02_ARCHITECTURE_DESIGN/ARCHITECTURE_OVERVIEW.md) |
| Data flow and lineage | [02_ARCHITECTURE_DESIGN/DATA_FLOWS_LINEAGE.md](../02_ARCHITECTURE_DESIGN/DATA_FLOWS_LINEAGE.md) |
| Interface contracts (schemas/APIs) | [02_ARCHITECTURE_DESIGN/INTERFACES_CONTRACTS.md](../02_ARCHITECTURE_DESIGN/INTERFACES_CONTRACTS.md) |
| Why decisions were made | [03_DECISIONS/DECISION_LOG/](../03_DECISIONS/DECISION_LOG/) |
| What's being worked on right now | [04_EXECUTION/TODO_NEXT.md](../04_EXECUTION/TODO_NEXT.md) |
| Active risks, issues, dependencies | [04_EXECUTION/RID_LOG.md](../04_EXECUTION/RID_LOG.md) |
| Research questions and experiments | [05_RESEARCH_EXPERIMENTS/RESEARCH_QUESTIONS.md](../05_RESEARCH_EXPERIMENTS/RESEARCH_QUESTIONS.md) |
| How to run the system | [06_CODE_EXECUTION_REPRODUCIBILITY/RUN_INSTRUCTIONS.md](../06_CODE_EXECUTION_REPRODUCIBILITY/RUN_INSTRUCTIONS.md) |
| Test strategy and validation evidence | [07_TEST_VALIDATION_EVIDENCE/TEST_STRATEGY.md](../07_TEST_VALIDATION_EVIDENCE/TEST_STRATEGY.md) |
| Model documentation and monitoring | [08_MODEL_RISK_GOVERNANCE/MODEL_CARD.md](../08_MODEL_RISK_GOVERNANCE/MODEL_CARD.md) |
| Security, compliance, access controls | [09_SECURITY_PRIVACY_COMPLIANCE/POLICY_REQUIREMENTS.md](../09_SECURITY_PRIVACY_COMPLIANCE/POLICY_REQUIREMENTS.md) |
| Runbooks and kill switch | [10_INFRA_OPERATIONS/RUNBOOKS/](../10_INFRA_OPERATIONS/RUNBOOKS/) |
| **Canonical source-of-truth index** | [11_MEMORY_HANDOFF/MEMORY_BANK.md](../11_MEMORY_HANDOFF/MEMORY_BANK.md) |
| Latest handoff pack | [11_MEMORY_HANDOFF/CONTEXT_PACKS/CP-2026-05-21_baseline-handoff.md](../11_MEMORY_HANDOFF/CONTEXT_PACKS/CP-2026-05-21_baseline-handoff.md) |

---

## Canonical Artifacts (Current Phase)

| Artifact | Status | Last Updated |
|----------|--------|-------------|
| PROJECT_CHARTER.md | CANONICAL | 2026-05-21 |
| SCOPE_IN_OUT.md | CANONICAL | 2026-05-21 |
| RISK_APPETITE_CONSTRAINTS.md | CANONICAL | 2026-05-21 |
| ADR-0001_adopt-compass-os.md | CANONICAL | 2026-05-21 |
| ADR-0002_strategy-class-selection.md | CANONICAL | 2026-05-21 |
| MEMORY_BANK.md | CANONICAL | 2026-05-21 |

---

## Phase Gates

| Gate | Name | Status |
|------|------|--------|
| G0 | Intent | 🟡 In Progress |
| G1 | Spec | 🔴 Not Started |
| G2 | Architecture | 🔴 Not Started |
| G3 | Execution | 🔴 Not Started |
| G4 | Evidence | 🔴 Not Started |
| G5 | Operational | 🔴 Not Started |
| G6 | Release / Live Capital | 🔴 Not Started |

---

## Update Cadence + Owners

| Cadence | Activity | Owner |
|---------|----------|-------|
| Daily | TODO_NEXT + RID_LOG review | Execution Lead |
| Weekly | Directory Integrity Review (DIR) | Directory Steward |
| Weekly | Cross-Cutting Concerns Council (C4) | Architecture / Risk Owner |
| Biweekly | Integration Review | Architecture Owner |
| Monthly | Gate Readiness Review | Execution Lead + DS |
| Quarterly | Retrieval Drill + Workflow Retrospective | Directory Steward |

---

## Non-Negotiable Invariants

1. If it isn't in the directory (or linked from it), it does not exist for governance/handoff purposes.
2. Every artifact must have the Universal Header (Purpose, Owner, Last Reviewed, Next Review, Staleness Triggers, Links, ADR refs, Confidence).
3. Major changes require an ADR. Accepted ADRs are immutable; changes are made via superseding ADRs.
4. No real capital deployment until G6 Release Gate is formally cleared with evidence artifacts.
5. The `arb/` folder is a reference-only artifact. Nothing from it enters the canonical directory without a formal ADR.
