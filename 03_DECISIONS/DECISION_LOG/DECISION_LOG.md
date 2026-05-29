# Decision Log — Prediction Market Trading Bot

**Purpose:** Chronological index of all decisions (ADRs, approvals, and notable judgment calls) made during this project. Single source of truth for "why did we decide X."  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-05-29 (APR-0016: G6 threshold revised 50→30; dark period plan documented; strategic shift captured)  
**Next review:** G5 Operational Gate; any new ADR/approval  
**Staleness triggers:** New ADR accepted; approval decision made; major judgment call not captured elsewhere  
**Upstream links:** 03_DECISIONS/  
**Downstream links:** 00_ADMIN/APPROVALS_REGISTER.md, all ADRs  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 9/10 — Current decisions fully logged; completeness depends on ongoing discipline

---

## ADR Index

| ADR ID | Title | Status | Date | Gate |
|--------|-------|--------|------|------|
| ADR-0001 | Adopt Compass OS as Project Governance Framework | ACCEPTED | 2026-05-21 | G0 |
| ADR-0002 | Strategy Class: Forecast-Only Research (No Arbitrage) | ACCEPTED | 2026-05-21 | G0/G1 |
| ADR-0003 | Venue Selection (Kalshi Primary; CA-Legal Multi-Venue) | ACCEPTED | 2026-05-23 | G3 |
| ADR-0004 | Model Class: LogisticRegression + Platt Scaling (Phase 3 Baseline) | ACCEPTED | 2026-05-28 | G4 (APR-0012) |
| ADR-0005 | Live Capital Authorization | PENDING | TBD | G6 |

---

## Notable Judgment Calls

*Decisions that do not rise to ADR level but are recorded to prevent future confusion.*

| Date | Decision | Rationale | Owner |
|------|----------|-----------|-------|
| 2026-05-21 | arb/ folder designated reference-only | Prior iteration contamination risk; no validation history; requires formal ADR (APR-0010) before any use | DS |
| 2026-05-21 | Player_Attribute_Matrix staged as research input only, not canonical | Provenance requires independent validation; source details need documentation | RL |
| 2026-05-21 | All nine governance roles assigned to solo operator (Earl Ignacio) | Solo build; role definitions preserved for future team scaling | DS |
| 2026-05-21 | Technology stack deferred to G2 | Cannot finalize stack without venue API constraints and data volume estimates | AO |
| 2026-05-22 | Risk limit thresholds marked TBD at G4 | Thresholds must be grounded in Brier score evidence; premature specification creates false precision | RCO |
| 2026-05-29 | G6 evidence threshold revised from 50 → 30 resolved paper bets (APR-0016) | NBA Finals end ~2026-06-22; ≤15 playoff games remain; at 4 bets/game-day max = ~60 bets theoretically but game-by-game uncertainty makes 50 unreliable as a fixed gate. 30 bets + EXP-010 EV evidence (+$0.0958/bet) is sufficient for live capital decision. Evidence quality unchanged. If not reached by Finals end, window extends to first 30 days of 2026-27 regular season. | DS |
| 2026-05-29 | Dark period build plan adopted: use NBA offseason (~2026-06-22 to 2026-10) for infrastructure work, not pause | Seasonal constraint forces a gap in paper bet accumulation. Rather than waiting, use the window for: Polymarket activation (T-077), DS-04 qualitative source (T-073), ADR-0005 live capital draft, Phase 8 preparation. This is an explicit strategic sequencing decision — do not treat dark period as idle time. | DS |
| 2026-05-29 | Handoff procedures upgraded: session handoffs must include "Strategic Decisions This Session" section | Prior handoffs captured code completions but dropped judgment calls (e.g., 50→30 threshold change). Root cause: no formal capture mechanism for decisions made during holistic reviews. Fix: invariant #9 in MEMORY_BANK + session handoff template updated. | DS |
| 2026-05-29 | Pilot experiment before infrastructure — standing sequencing rule | EXP-012 and EXP-013 falsified HYP-006 and HYP-007 after full infrastructure was built (TeamStatsStore, ScoringDistributionModel). Cost: ~3-5 hours stranded build. Rule: confirm hypothesis with minimal experiment before building supporting component. See LL-009. | DS |
| 2026-05-29 | T-072 model refresh elevated from "optional" to required before 2026-27 paper trading resumes | KI-013: model v1-28483b21 trained through 2026-05; 5+ months stale at 2026-27 season open. Paper bets in early 2026-27 with a stale model are lower-quality G6 evidence. Retrain by 2026-10-15 (before regular season tip-off). New ADR required per ADR-0004. | DS |

---

## Decision Principles

These principles guide all decisions in this project:

1. **No decision is reversible without a superseding ADR.** ADRs are immutable once accepted.
2. **"We'll fix it later" is a shadow commitment.** If it matters, log it as an open question or RID.
3. **Deferred decisions must have a named gate.** "TBD" without a deadline is a gap, not a decision.
4. **arb/ folder: gate is APR-0010, not momentum.** No incorporation without explicit approval.
5. **Live capital decisions require two artifacts:** a superseding ADR and a signed approval (APR-0009).
