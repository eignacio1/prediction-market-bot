# Rejected Options — Prediction Market Trading Bot

**Purpose:** Document options that were considered and explicitly rejected. Recording rejections prevents relitigating the same decisions in future sessions.  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-05-22  
**Next review:** G2 Architecture Gate; add entries whenever a design option is evaluated and rejected  
**Staleness triggers:** New option considered; conditions-for-reconsideration met  
**Upstream links:** ADR-0001, ADR-0002, TRADEOFFS.md  
**Downstream links:** OPEN_QUESTIONS.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 8/10 — Rejections are well-reasoned; conditions for reconsideration documented

---

## RO-001 — Incorporate arb/ Folder in Phase 0

| Attribute | Detail |
|-----------|--------|
| Option | Use the arb/ folder from the previous iteration as a foundation for Phase 0–3 research |
| Rejected in | ADR-0002 / APR-0010 (PENDING) |
| Reason | (1) The previous iteration suffered from data and process contamination. Incorporating its artifacts without full validation would reproduce the failure. (2) Arbitrage code from a different market regime or methodology requires validation equivalent to building new. (3) No provenance documentation exists for arb/ in the current directory. |
| Conditions for reconsideration | APR-0010 formally approved; ADR written for arb/ incorporation; full methodology audit complete |
| Who can re-open | DS only, with formal APR-0010 approval |

## RO-002 — Skip G0 and Start Research Immediately

| Attribute | Detail |
|-----------|--------|
| Option | Skip directory scaffolding and governance setup; start data exploration and modeling immediately |
| Rejected in | ADR-0001 |
| Reason | (1) The previous iteration skipped governance and failed due to context rot. (2) Starting research without a valid directory means all research artifacts will eventually need to be retrofitted — creating exactly the shadow doc problem Compass OS is designed to prevent. |
| Conditions for reconsideration | Never — governance spine is a prerequisite, not optional |

## RO-003 — Ad-Hoc Documentation (No Formal Framework)

| Attribute | Detail |
|-----------|--------|
| Option | Maintain documentation informally without Compass OS structure |
| Rejected in | ADR-0001 |
| Reason | This is the approach used in the previous iteration. Its failure is the reason for this iteration. |
| Conditions for reconsideration | Never |

## RO-004 — External Project Management Tool (Jira/Notion) as Governance Spine

| Attribute | Detail |
|-----------|--------|
| Option | Use a SaaS PM tool as the primary governance record |
| Rejected in | ADR-0001 |
| Reason | (1) Introduces external dependency on third-party availability and pricing. (2) Splits canonical record between PM tool and code directory — reproduces shadow doc pattern. (3) Compass OS co-locates all artifacts with code and data; no split record. |
| Conditions for reconsideration | If team scales beyond solo operator and a collaborative tool is needed — revisit at that point |

## RO-005 — Random Train/Test Split for Backtesting

| Attribute | Detail |
|-----------|--------|
| Option | Use random shuffling for train/test splits to maximize statistical efficiency |
| Rejected in | DATA_FLOWS_LINEAGE.md (TI-02) |
| Reason | Random splits in time-series data create look-ahead bias. Future data leaks into training. The Brier score from such a backtest is meaningless and potentially misleading. |
| Conditions for reconsideration | Never — chronological splits are a hard requirement for temporal data |

## RO-006 — Full Kelly Position Sizing

| Attribute | Detail |
|-----------|--------|
| Option | Use the full Kelly formula without a fractional discount |
| Rejected in | RISK_APPETITE_CONSTRAINTS.md |
| Reason | Full Kelly is optimal only under perfect calibration. A model with imperfect calibration or estimation error will overtrade and amplify drawdown. Fractional Kelly provides a practical safety margin. |
| Conditions for reconsideration | Never at initial deployment; potentially revisited after ≥N live events with demonstrated calibration and within-limits drawdown |

## RO-007 — Automated Retraining in Production

| Attribute | Detail |
|-----------|--------|
| Option | Allow the model to retrain automatically in response to new data in production |
| Rejected in | EXECUTION_ARCHITECTURE.md (TR-005) |
| Reason | (1) Automated retraining creates silent model changes that invalidate risk assumptions. (2) Cannot audit which model is running at a given time. (3) Drift from retraining may be undetectable until after capital loss. |
| Conditions for reconsideration | Post-G6 ADR with a formal controlled retraining framework including version pinning, validation gate, and approval process |
