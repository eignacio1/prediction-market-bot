# Known Issues — Prediction Market Trading Bot

**Purpose:** Track known issues, limitations, and technical debt that are acknowledged but not yet resolved. Distinguishes between issues that are acceptable risks versus those that must be resolved before specific gate clearances.  
**Owner (role):** Infrastructure Operator (IO) + Model Owner (MO)  
**Last reviewed:** 2026-05-22  
**Next review:** Weekly cadence during active development; update when issue resolved or new issue discovered  
**Staleness triggers:** Issue resolved; new issue discovered; blocking condition changes  
**Upstream links:** RID_LOG.md, OPEN_QUESTIONS.md, RESILIENCE_FAILURE_MODES.md  
**Downstream links:** TODO_NEXT.md, RUNBOOKS/  
**Decision references:** ADR-0001  
**Confidence:** 9/10 — Current known issues accurately reflect Phase 0/1 state

---

## Active Known Issues

### KI-001 — DS-01 Provenance Unknown

| Field | Detail |
|-------|--------|
| Issue ID | KI-001 |
| Severity | HIGH |
| Category | Data governance |
| Description | Player_Attribute_Matrix_v4.docx source, creator, and creation date are unknown. The file exists as an artifact from a prior iteration but its provenance has not been documented. |
| Impact | Cannot use DS-01 in any experiment until OQ-001 is resolved |
| Workaround | None — must be resolved before Phase 3 work begins |
| Blocks gate | G1 exit; any experiment using DS-01 |
| Resolution path | Document source, creator, creation date; validate schema; register as snapshot (DATA_PROVENANCE.md action list) |
| Open question | OQ-001 |
| Status | OPEN — Phase 0 |

---

### KI-002 — Venue Not Selected

| Field | Detail |
|-------|--------|
| Issue ID | KI-002 |
| Severity | HIGH |
| Category | Architecture dependency |
| Description | The prediction market venue (Kalshi, Polymarket, or other) has not been selected. This blocks API client development, market data schema definition, and execution architecture finalization. |
| Impact | Blocks: DS-02/DS-03 schema, C5 implementation, HYP-003 testing, DEPENDENCIES.md vendor SDK, POLICY_REQUIREMENTS.md POL-001/POL-003 |
| Workaround | Research phase can proceed with DS-01 only; venue-dependent work deferred |
| Blocks gate | G3 (Architecture Complete) |
| Resolution path | ADR-0003: venue selection decision with TOS review |
| Open question | OQ-006 |
| Status | OPEN — deferred to G2/G3 |

---

### KI-003 — Secrets Vault Solution Undefined

| Field | Detail |
|-------|--------|
| Issue ID | KI-003 |
| Severity | MEDIUM (LOW at Phase 1-4; HIGH at Phase 5+) |
| Category | Security infrastructure |
| Description | No secrets vault solution has been selected. python-dotenv is acceptable for research-only phases but not for paper/live trading. |
| Impact | Cannot provision live API credentials safely until vault is in place |
| Workaround | python-dotenv (.env file, gitignored) for Phase 1-4 only |
| Blocks gate | G5 (Paper Trading Authorization) |
| Resolution path | Evaluate candidates (HashiCorp Vault, AWS Secrets Manager, macOS Keychain); select and document at G5 |
| Open question | OQ-009 |
| Status | OPEN — acceptable for current phase |

---

### KI-004 — C7 Monitoring Implementation Not Designed

| Field | Detail |
|-------|--------|
| Issue ID | KI-004 |
| Severity | MEDIUM (Phase 5+ blocker) |
| Category | Infrastructure |
| Description | The monitoring component (C7) design is specified at the interface level but the implementation approach (library, framework, alert delivery mechanism) has not been selected. |
| Impact | Cannot implement real-time drift detection or automated alerting |
| Workaround | Manual metric computation during Phase 3-4 experiments |
| Blocks gate | G5 (C7 must be active before paper trading) |
| Resolution path | Resolve OQ-010; implement C7 during Phase 4 |
| Open question | OQ-010 |
| Status | OPEN — deferred to Phase 4 |

---

### KI-005 — Kill Switch Not Implemented or Tested

| Field | Detail |
|-------|--------|
| Issue ID | KI-005 |
| Severity | MEDIUM (Phase 5+ blocker) |
| Category | Safety / NFR-03 |
| Description | The kill switch is designed (EXECUTION_ARCHITECTURE.md, RUNBOOK_kill-switch.md) but not implemented or tested. The drill (TC-009, TC-010) cannot be run until implementation is complete. |
| Impact | Cannot clear G5 gate; must not go to paper trading without tested kill switch |
| Workaround | None — kill switch implementation is required |
| Blocks gate | G5 (kill switch drill required) |
| Resolution path | Implement kill switch in Phase 4; drill in Phase 5 preparation |
| Open question | None — this is a known implementation task |
| Status | OPEN — implementation deferred to Phase 4 |

---

### KI-006 — Model Class Not Selected

| Field | Detail |
|-------|--------|
| Issue ID | KI-006 |
| Severity | LOW (Phase 3 task) |
| Category | Research |
| Description | Model class (logistic regression, XGBoost, or other) has not been selected. This is expected at Phase 0 — the selection is deferred to G3 after evidence from Phase 3 experiments. |
| Impact | MODEL_CARD.md model overview is template-only; METHODOLOGY.md model class is TBD |
| Workaround | N/A — this is the intended research process |
| Blocks gate | G4 (model must be selected and evidenced) |
| Resolution path | Phase 3 experiments evaluate candidates; ADR-0003 finalizes selection |
| Open question | OQ-007 (technology stack) |
| Status | OPEN — expected; not a problem at this phase |

---

### KI-007 — arb/ Folder Excluded from All Active Work

| Field | Detail |
|-------|--------|
| Issue ID | KI-007 |
| Severity | LOW (by design) |
| Category | Governance |
| Description | The arb/ folder from the prior iteration is explicitly excluded from all active development and experiments. It is reference-only for holistic future planning. Incorporating it requires a new ADR. |
| Impact | Any arbitrage strategy ideas from arb/ cannot be acted upon without ADR |
| Workaround | N/A — this is an intentional governance constraint, not a workaround situation |
| Blocks gate | Nothing currently; APR-0010 is the future gate |
| Resolution path | Future ADR if evidence at G4 suggests arbitrage is viable |
| Open question | None — constraint is intentional |
| Status | ACKNOWLEDGED BY DESIGN — see REJECTED_OPTIONS.md RO-001 |

---

### KI-008 — Production Model Untested on Playoff Data

| Field | Detail |
|-------|--------|
| Issue ID | KI-008 |
| Severity | HIGH |
| Category | Model validity / data distribution |
| Description | The production model (v1-28483b21, LR+Platt, 78 features) was trained and validated exclusively on regular season game logs (2021-26). All experiments EXP-001 through EXP-015 used `SEASON_TYPE_REGULAR`. Paper trading began 2026-05-29 during the NBA Western Conference Finals — a fundamentally different distribution: compressed rotations, elevated defensive intensity, no back-to-back scheduling, and high-stakes rest patterns not present in regular season data. |
| Impact | Paper trading bets placed during playoffs may not reflect the model's validated EV (+$0.0958/bet, EXP-010). If the model is miscalibrated for playoff conditions, paper P&L is not reliable G6 evidence. |
| Workaround | EXP-016 (T-072) quantifies the Brier degradation on held-out playoff rows. If Δ Brier < 0.012 (HYP-009 gate), paper results remain valid. If falsified, playoff-era paper bets must be annotated as lower-confidence G6 evidence. |
| Blocks gate | G6 — paper evidence reliability is partially dependent on playoff/regular distinction |
| Resolution path | 1. Run EXP-016 to get Δ Brier verdict (HYP-009). 2. If falsified, register playoff bets separately in paper portfolio and apply a confidence discount. 3. T-072: after 2025-26 Finals, retrain model with playoff data and evaluate Brier delta (ADR required). |
| Open question | None — resolution path is clear |
| Registered | 2026-05-29 |
| Status | OPEN — EXP-016 in progress |

---

### KI-009 — G6 50-Bet Gate Unreachable Within 2025-26 Season

| Field | Detail |
|-------|--------|
| Issue ID | KI-009 |
| Severity | MEDIUM |
| Category | Project timeline |
| Description | The G6 gate requires 50+ resolved paper bets with positive P&L. Paper trading commenced 2026-05-29 with the NBA Western Conference Finals in progress. At ~2 bets per game day and ~10-15 remaining playoff games before Finals end (~2026-06-22), the maximum achievable bet count before season end is ~30-45. After the Finals, the NBA goes dark until the 2026-27 season opens in October 2026. |
| Impact | G6 gate slips to Q1 2027 unless (a) the 50-bet threshold is formally adjusted via DS sign-off, or (b) the bet accumulation rate increases via the dual-window cron (PIPE-03 at 22:00 UTC + 01:30 UTC). |
| Workaround | Dual-window PIPE-03 cron (2026-05-29 update) increases expected bets to ~4/game day, making 50 bets achievable within the playoff window if games continue. If season ends short, carry evidence forward to 2026-27 regular season. |
| Blocks gate | G6 — calendar-bound |
| Resolution path | DS formal note in APPROVALS_REGISTER.md: G6 evidence window extends through first 30 days of 2026-27 regular season if 50-bet threshold not met by 2026-06-22. Threshold may be revised to 30 resolved bets + Brier-consistent EV via APR-0016. |
| Open question | None — operator decision required |
| Registered | 2026-05-29 |
| Status | OPEN — monitoring bet accumulation rate |

---

## Resolved Issues

*Populated as issues are resolved.*

| Issue ID | Resolution Date | Resolution Summary |
|----------|----------------|-------------------|
| — | — | — |

---

## Issue Triage Criteria

Issues are classified on two dimensions:

**Severity:**
- HIGH: Blocks a gate or makes a component unsafe to use
- MEDIUM: Must be resolved before a future phase; currently manageable with workaround
- LOW: Acknowledged limitation; acceptable for current state; no active blocker

**Resolution urgency:**
- G1 blocker: Must resolve before G1 exit
- G2 blocker: Must resolve before G2 exit
- G3 blocker: Must resolve before G3 exit
- G5 blocker: Must resolve before paper trading
- G6 blocker: Must resolve before live capital
- Non-blocking: Acknowledged; resolution opportunistic
