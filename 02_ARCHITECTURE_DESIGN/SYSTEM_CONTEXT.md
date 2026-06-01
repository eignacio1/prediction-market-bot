# System Context — Prediction Market Trading Bot

**Purpose:** Define the external boundary of the system — what it touches, what touches it, and what it deliberately does not integrate with.  
**Owner (role):** Architecture Owner (AO)  
**Last reviewed:** 2026-05-22  
**Next review:** G2 Architecture Gate; then on any new external dependency  
**Staleness triggers:** New external system integrated; venue confirmed; data source changed; compliance scope change  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, 01_SPEC/SCOPE_IN_OUT.md  
**Downstream links:** INTERFACES_CONTRACTS.md, EXECUTION_ARCHITECTURE.md, 09_SECURITY_PRIVACY_COMPLIANCE/  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 7/10 — External actors identified; venue details pending ADR-0003
**Decisions logged:** true — System boundary decisions captured in ADR-0001 (scope), ADR-0002 (strategy class), ADR-0003 (venue)

---

## System Boundary Diagram

```
╔══════════════════════════════════════════════════════════════════════╗
║                    SYSTEM BOUNDARY                                    ║
║                                                                       ║
║  ┌─────────────────────────────────────────────────────────────┐     ║
║  │                  PREDICTION MARKET BOT                       │     ║
║  │                                                              │     ║
║  │    C1 → C2 → C3 → [C5] → [C4] → C6 ← C7                   │     ║
║  │                                                              │     ║
║  └──────────┬────────────────────────────┬────────────────────┘     ║
║             │                            │                            ║
╚═════════════╪════════════════════════════╪════════════════════════════╝
              │                            │
   ┌──────────▼──────────┐      ┌─────────▼──────────┐
   │  EXTERNAL: Data      │      │  EXTERNAL: Venue    │
   │  Sources             │      │  API (Phase 6+)     │
   │                      │      │                     │
   │  DS-01: Player       │      │  Kalshi / Polymarket│
   │  Attribute Matrix    │      │  (TBD — ADR-0003)   │
   │  (static file)       │      │  ─────────────────  │
   │                      │      │  Order submission   │
   │  DS-02: Market Data  │      │  Order book data    │
   │  Feed (Phase 6+)     │      │  Outcome resolution │
   │                      │      │                     │
   │  DS-03: Outcome Data │      │  GATED: G5 + ACC-   │
   │  (Phase 6+)          │      │  0002 required      │
   └──────────────────────┘      └─────────────────────┘

              ┌──────────────────────────────────────┐
              │   EXTERNAL: Operator (Earl Ignacio)   │
              │                                       │
              │  Research review (all phases)         │
              │  Gate approval (G0–G6)                │
              │  Kill switch override (manual)        │
              │  Risk limit configuration             │
              │  Capital authorization (G6+)          │
              └──────────────────────────────────────┘
```

---

## External Actors

### EA-01 — Player Attribute Matrix (DS-01)

| Attribute | Detail |
|-----------|--------|
| Type | Static file (XLSX / structured data) |
| Direction | Inbound to C1 |
| Phase | Available from Phase 1 (staged); used from Phase 3 |
| Trust level | Research input only. NOT canonical spec. Requires independent validation before any production use. |
| Governance | Must be registered as Snapshot (SNAP-YYYY-MM-DD-NNN) before any experiment references it |
| Constraint | See DATA_REQUIREMENTS.md: DS-01. Provenance must be documented. No live use without validated schema. |

### EA-02 — Market Data Feed (DS-02)

| Attribute | Detail |
|-----------|--------|
| Type | API or file feed (TBD at ADR-0003) |
| Direction | Inbound to C1 |
| Phase | Phase 6+ only |
| Trust level | External. Schema versioned and validated at ingestion. |
| Governance | Requires venue confirmation (ADR-0003) and operational access (ACC-0002, G5+) |
| Constraint | Price data used as features must respect temporal look-back window (TI-04). No direct database writes; only through C1 schema validation. |

### EA-03 — Outcome / Resolution Data (DS-03)

| Attribute | Detail |
|-----------|--------|
| Type | API or file feed (TBD at ADR-0003) |
| Direction | Inbound to C1 (separate ingestion path from features) |
| Phase | Phase 6+ for live; Phase 3+ for historical outcomes used in backtesting |
| Trust level | External |
| Constraint | MUST be ingested on a separate path from feature data and NEVER enter the feature store (TI-03). Used only for model evaluation and calibration. |

### EA-04 — Venue API (Phase 6+)

| Attribute | Detail |
|-----------|--------|
| Type | REST / WebSocket API (TBD at ADR-0003) |
| Direction | Bidirectional: data inbound (DS-02); orders outbound (Phase 8 only) |
| Phase | Phase 6+ (data); Phase 8+ (orders) |
| Trust level | External, authenticated. Credentials managed per NFR-05 (vault-based). |
| Governance | Requires ADR-0003 (venue selection), ACC-0002, APR-0008, G5 gate, and G6 gate before live order submission |
| Constraint | idempotency_key required on all order submissions to prevent duplication (FM-05). |

### EA-05 — Operator (Earl Ignacio)

| Attribute | Detail |
|-----------|--------|
| Type | Human operator |
| Direction | Command (configuration, gate approval, kill switch); Observation (monitoring, review) |
| Phase | All phases |
| Authority | Sole authority for gate approvals, capital authorization, and risk limit configuration |
| Constraint | Cannot override programmatic kill switch without an ADR. No single-person override for live capital decisions (even as sole operator — process required). |

---

## What Is Explicitly Outside the System Boundary

| Excluded Actor | Reason | Re-evaluation path |
|----------------|--------|--------------------|
| arb/ folder / arbitrage strategies | Reference-only from prior iteration; not validated; scope creep risk | Formal ADR required; APR-0010 PENDING |
| Multi-venue execution | Complexity before single-venue is validated | Post-G6 consideration |
| External human traders / signals | No external signal sources; sole-operator model | Post-G6 consideration |
| Brokerage / exchange margin accounts | Prediction markets operate on deposited capital, not margin | N/A to current venue targets |
| Automated model retraining in production | Frozen model policy; retraining requires ADR + new model version | Phase 8+ governance |
| Third-party analytics / BI tools | Data must not leave the local system boundary without explicit approval | Requires security review |

---

## Context Constraints

1. **Single-operator system.** All nine governance roles are held by one person. Gate process still applies — the operator cannot unilaterally skip gates even as sole approver.
2. **Local execution only (Phases 0–5).** No cloud dependencies until operational readiness confirmed at G5.
3. **No external credentials in scope.** Until venue is confirmed (ADR-0003), no API keys exist. When created, managed per NFR-05.
4. **Data does not leave the boundary.** Research data (Player_Attribute_Matrix) is not transmitted externally except when the system submits forecasts to a paper/live venue.
