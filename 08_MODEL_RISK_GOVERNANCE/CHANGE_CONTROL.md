# Change Control — Prediction Market Trading Bot

**Purpose:** Define what changes require formal approval (ADR) versus lightweight documentation. Prevents silent changes to model, risk limits, or strategy from undermining governance.  
**Owner (role):** Director/Sponsor (DS) + Risk and Compliance Owner (RCO)  
**Last reviewed:** 2026-05-22  
**Next review:** G2; update when new component or major change type identified  
**Staleness triggers:** New change type encountered; ADR process revised  
**Upstream links:** ADR-0001, RISK_APPETITE_CONSTRAINTS.md  
**Downstream links:** 03_DECISIONS/, 00_ADMIN/CHANGELOG.md  
**Decision references:** ADR-0001  
**Confidence:** 8/10 — Change types are well-defined; application to edge cases requires judgment

---

## Change Classification

### Class A — ADR Required (Immutable Record)

These changes require a formal ADR. No exception. ADRs are immutable once accepted.

| Change Type | Rationale |
|------------|-----------|
| New strategy class or strategy expansion (e.g., incorporating arb/) | Fundamental scope change; invalidates prior validation |
| Paper trading promotion (Phase 5 → 6) | Capital risk introduced |
| Live capital authorization (Phase 7 → 8) | Real capital at risk |
| Venue selection | Determines execution design, compliance, and data APIs |
| Risk limit changes (any hard limit in RISK_APPETITE_CONSTRAINTS.md) | Direct capital safety impact |
| Model version promotion to paper/live | Model risk change |
| Retraining in production | Prohibited; requires ADR to even design |
| Removing or changing a component interface (breaking change) | Downstream coupling change |
| Technology stack changes (language, data store) | Reproducibility impact |

### Class B — CHANGELOG Entry Required

| Change Type | Documentation |
|------------|---------------|
| New dependency added (pinned version) | CHANGELOG + DEPENDENCY_LOCKS/ |
| Minor interface field addition (backward-compatible) | INTERFACES_CONTRACTS.md version bump + CHANGELOG |
| New experiment type or new feature added | EXPERIMENT_LOG entry + DATA_FLOWS_LINEAGE.md |
| Runbook updated | CHANGELOG |
| Schedule or timeline change | ROADMAP_MILESTONES.md + CHANGELOG |

### Class C — Artifact Update Only (No Separate Process)

| Change Type | Documentation |
|------------|---------------|
| New snapshot registered | DATA_SNAPSHOTS_INDEX.md |
| Open question resolved | OPEN_QUESTIONS.md + linked artifact |
| Assumption validated or falsified | ASSUMPTIONS_REGISTER.md |
| Status report update | STATUS_REPORTS/ |

---

## Change Governance for Risk Limits

Risk limits (RISK_APPETITE_CONSTRAINTS.md) deserve special mention:

- **Increasing a limit** (loosening): requires ADR + RCO sign-off
- **Decreasing a limit** (tightening): requires ADR (conservative direction; still must be documented)
- **Temporary override**: PROHIBITED without ADR
- **Emergency override**: No emergency override path exists. Kill switch is the emergency response.

---

## Change Review Checklist

Before implementing any Class A or B change:

- [ ] Change classified correctly (A vs B vs C)
- [ ] If Class A: ADR drafted, reviewed, and accepted before implementation
- [ ] If Class B: CHANGELOG entry created before or immediately after implementation
- [ ] Downstream links updated (interfaces, runbooks, linked artifacts)
- [ ] No shadow changes (implementation must match documented change)
