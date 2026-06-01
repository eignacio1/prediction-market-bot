# Governance Gap Log — Prediction Market Trading Bot

**Purpose:** Register every discovered governance process failure — decisions that should have been made and weren't, thresholds set as placeholders and never revisited, architectural assumptions that went undocumented. This is distinct from DECISION_LOG (records decisions *made*) and KNOWN_ISSUES (records runtime bugs). This records failures of the governance *system itself*.  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-06-01  
**Next review:** Session start (mandatory scan); after every gate review; after any incident  
**Staleness triggers:** New gap discovered; existing gap resolved  
**Upstream links:** DECISION_LOG.md, KNOWN_ISSUES.md, LESSONS_LEARNED.md  
**Downstream links:** TODO_NEXT.md (remediation tasks), ADRs (resolution artifacts)  
**Decision references:** ADR-0007 (Governance Gap Logging — mandates this artifact)  
**Confidence:** 10/10 — Three gaps registered at artifact creation

---

## Why This Artifact Exists

The prior iteration failed to context rot → hallucination → contamination. The current iteration built extensive governance: ADRs, decision logs, gate reviews, session handoffs. Yet GG-001 through GG-003 still happened.

**The gap the prior system could not catch:** Decisions made correctly at an early phase that became *wrong* after the architecture grew past them — with nothing in the governance system to trigger a re-review.

Session-start scans caught `decisions_logged: false`. They did not catch "this value was set at G4 when we had 10 players and is now running on 80 players across 5 execution bands." The ARE WE COMPROMISED? check (MEMORY_BANK.md) was designed to catch this class of failure going forward.

---

## Active Gaps

### GG-001 — max_concurrent_positions: 10 stub survived G4→G5→G7 undetected

| Field | Detail |
|---|---|
| Gap ID | GG-001 |
| Category | Architectural placeholder survived gate review |
| What was missed | `_HARD_LIMITS["max_concurrent_positions"] = 10.0` was set at G4 as a stub with explicit `# TBD at G4 review` comment. The G4 gate review confirmed the *existence* of the check but never validated whether 10 was architecturally correct. Three subsequent phases (G5, G6, G7) were cleared without the value being revisited. |
| When it should have been caught | G4 Evidence Gate (2026-05-28) — when actual player cohort size, execution bands, and resolution lag were known |
| Phases it survived | G4 → G5 → G6 → G7 (3 gate clearances) |
| Why it survived | The governance scan checked `decisions_logged: false` in documentation headers. It did not check for `# stub` / `# placeholder` comments in source code. The gate review asked "does this work?" not "is this value correct for the architecture we just built?" |
| Impact | Count-based position gate was architecturally wrong for a multi-band, 80-player, multi-game quant execution system. Would have silently rejected valid bets in regular season on the first multi-game night. Active blocker during paper trading (9/10 positions filled, Finals G2 at risk). |
| Discovery | Operator manual review 2026-05-31 — noticed strategic incoherence between the limit and the execution architecture |
| Discovery method | Human eye test — NOT caught by any automated scan or governance artifact |
| Resolution | ADR-0006: delete count gate entirely; pipeline + Kelly + kill switch are the risk framework. Code fix: T-102 (2026-06-01). |
| Status | **RESOLVED 2026-06-01** — ADR-0006 accepted; `max_concurrent_positions` deleted from `_HARD_LIMITS`; CHECK 3 removed from `risk.py`; `current_open_positions` parameter removed from interface; 2 tests rewritten; VPS deploy pending |

---

### GG-002 — T1–T5 execution tier architecture required multiple sessions to implement correctly

| Field | Detail |
|---|---|
| Gap ID | GG-002 |
| Category | Incremental architecture without coherence checkpoints |
| What was missed | The T1–T5 time-horizon execution band framework was conceptually adopted as a governing architectural principle but was implemented piecemeal across multiple sessions without a coherence checkpoint confirming the risk framework had been updated to match. ExecutionBands (T-084), multi-band orchestrator (T-084), band-specific Kelly fractions, and dual-window cron were all built — but the risk framework they operate within (C4) retained a G4-era stub that was designed for a single-band, 10-player system. |
| When it should have been caught | At the end of any session that completed a major Phase 7 build (T-083, T-084) — when the scope of the execution architecture had clearly grown past the risk framework |
| Phases it survived | Phase 7 build (2026-05-29) through G7 run (2026-05-31) |
| Why it survived | No architectural coherence checkpoint existed. Session handoffs captured "tasks completed" but not "which G4 assumptions are now potentially stale given what we just built?" The mid-session checkpoint protocol (MEMORY_BANK.md) does not ask whether upstream risk limits are still valid for the components just deployed. |
| Impact | The system ran the first real game (NBA Finals G1, 2026-05-31) with an execution architecture designed for thousands of trades per season but a risk gate designed for 10 concurrent positions. The misalignment was structurally undetectable without operator review. |
| Discovery | Same session as GG-001 — operator identified the execution/risk coherence gap during GG-001 remediation discussion |
| Resolution | ADR-0006 (GG-001 resolution covers this). ARE WE COMPROMISED? check added to MEMORY_BANK.md session-start protocol to catch future coherence gaps. |
| Status | **RESOLVED 2026-06-01** — Root cause addressed by ADR-0006 + ARE WE COMPROMISED? watchdog |

---

### GG-003 — No automatic detection for "architecture outgrew its constraints"

| Field | Detail |
|---|---|
| Gap ID | GG-003 |
| Category | Systemic governance blind spot |
| What was missed | The governance system — ADRs, DECISION_LOG, gate reviews, session handoffs — was designed to prevent re-litigating resolved decisions and ensure new decisions were logged. It was not designed to detect the case where a correctly-made early decision becomes *wrong* because the system architecture grew past the assumptions that underpinned it. This is a distinct failure class from context rot (undocumented decisions) or scope creep (unauthorized changes). It is architectural coherence drift. |
| When it should have been caught | This is a structural gap — it predates any specific incident. The prior iteration failed to context rot; the mitigation (Compass OS) was thorough on decision documentation but created no mechanism to revisit early decisions when the architecture changed. |
| Impact | GG-001 and GG-002 are symptoms of this systemic gap. Any value in `_HARD_LIMITS`, any threshold in RISK_APPETITE_CONSTRAINTS.md, any ADR from G0–G4 is potentially stale if the architecture changed significantly after it was written. Without GG-003's mitigation, future versions of this gap will recur. |
| Discovery | 2026-06-01 operator escalation: "there is nothing in the system that would have caught this without manual review" |
| Resolution | ADR-0007: mandates GOVERNANCE_GAP_LOG.md as a required artifact. ARE WE COMPROMISED? check (MEMORY_BANK.md): 5-question strategic integrity check at session start. T-103: code stub scan added to session-start protocol. |
| Status | **RESOLVED 2026-06-01** — ADR-0007 accepted; watchdog protocol added to MEMORY_BANK.md |

---

### GG-004 — EV Validation Benchmark Was Never the Commercial Question

| Field | Detail |
|---|---|
| Gap ID | GG-004 |
| Category | Systemic research blind spot |
| What was missed | All 16 experiments in this project computed edge and EV using `mip = 0.50` as the market implied probability. The research process validated "does the model beat a coin flip?" — not "does the model beat an informed Kalshi market?" The commercial question the project is built to answer was never posed as an experiment. EXP-004 Part B and EXP-010 Part B used live prices but only as a 2-player spot check on a single day. This is not statistical validation. |
| When it should have been caught | G4 Evidence Gate (2026-05-28) — when the EV figure (+$0.0858/bet) was accepted as gate evidence. The gate question should have been "what is the benchmark for this EV figure?" It was not asked. |
| Phases it survived | G4 → G5 → G6 (all gate reviews) |
| Why it survived | Gate reviews asked "is the EV positive?" not "is the EV positive against the right benchmark?" The distinction between `mip=0.50` and `mip=kalshi_market_price` was not part of any experiment design checklist or gate criterion. No governance artifact asked: "what market are we competing against?" |
| Impact | The core commercial claim — model generates positive EV against real Kalshi prices — is unvalidated. Paper trading (Phase 6) is accumulating real-world evidence, but 30 bets is insufficient for statistical confidence and variance is high. If EXP-017 shows the model does NOT beat real prices, G6 gate cannot be cleared. |
| Discovery | 2026-06-01 — new terminal session review of run_exp010.py:164; operator escalation in session convergence |
| Discovery method | Code review by fresh model instance following CLAUDE.md session-start protocol. Human operator confirmed significance. |
| Resolution | EXP-017: backtest edge against actual historical Kalshi prices. OQ-023 registered. T-105 registered. |
| Status | OPEN — 2026-06-01; EXP-017 registered; blocks G6 confidence clearance |

---

## Resolved Gaps

| Gap ID | Resolution Date | Resolution Summary |
|---|---|---|
| GG-001 | 2026-06-01 | ADR-0006: count gate deleted; pipeline + Kelly + kill switch are the risk framework |
| GG-002 | 2026-06-01 | ADR-0006 covers this; ARE WE COMPROMISED? watchdog added |
| GG-003 | 2026-06-01 | ADR-0007: GOVERNANCE_GAP_LOG.md mandated; ARE WE COMPROMISED? protocol added |

---

## Gap Registration Template

When a new governance process failure is discovered:

```markdown
### GG-NNN — [Short title]

| Field | Detail |
|---|---|
| Gap ID | GG-NNN |
| Category | [Architectural placeholder / Incremental architecture / Systemic blind spot / other] |
| What was missed | [The specific decision, value, or check that was absent] |
| When it should have been caught | [Gate, phase, or trigger that should have flagged it] |
| Phases it survived | [G0→G1→...] |
| Why it survived | [Root cause of the governance failure — what scan/check/protocol did NOT catch it] |
| Impact | [What happened or could have happened as a result] |
| Discovery | [How and when it was found — especially if human eye test vs. automated] |
| Resolution | [ADR/APR/task that closes it] |
| Status | OPEN / IN PROGRESS / RESOLVED [date] |
```

---

## Invariant

**Every governance gap must be registered here before remediation work begins.** The act of registering a gap is itself load-bearing — it ensures that the process failure is documented independently of the fix, so that future sessions can distinguish "we fixed the bug" from "we fixed the system that allowed the bug."
