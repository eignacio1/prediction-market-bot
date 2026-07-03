# Roadmap and Milestones — Prediction Market Trading Bot

**Purpose:** Map the phase gate sequence to calendar targets and artifact deliverables. Living document — updated at each gate.  
**Owner (role):** Execution Lead (EL)  
**Last reviewed:** 2026-07-02 (documentation-remediation pass) — corrects a violation of this document's own "monthly review" cadence commitment: it had not been touched since 2026-05-28 despite G5 closing that same week and Phase 6/7 running live for over a month since. See DECISION_LOG.md 2026-07-02 entry.  
**Next review:** G6 gate passage (EXP-017 CONFIRMED_POSITIVE + DS sign-off); monthly review in the interim — treat a missed monthly review as a staleness incident, not a formality  
**Staleness triggers:** Phase gate passed; milestone slipped >1 week; major dependency change; scope change  
**Upstream links:** PROJECT_CHARTER.md, SCOPE_IN_OUT.md, REQUIREMENTS.md  
**Downstream links:** 04_EXECUTION/PLAN.md, 04_EXECUTION/TODO_NEXT.md  
**Decision references:** ADR-0001, ADR-0002, ADR-0003, ADR-0004 (ACCEPTED — APR-0012)  
**Confidence:** 9/10 for Phases 0–5 (formally closed, evidenced by signed APRs); 7/10 for Phase 6/7 rows below (reconstructed from MEMORY_BANK.md narrative during this remediation pass, not independently re-verified against the VPS in this session — cross-check bet counts/dates against `MEMORY_BANK.md`'s Current State Snapshot before treating as authoritative)
**Decisions logged:** true — T-099 logged 2026-06-02: G7 (multi-sport gate), G8 (multi-venue/V-002 activation gate), G9 (scaled live operation gate), phase sequencing rationale. G0–G5 captured via APRs. See DECISION_LOG.md 2026-06-02 and 2026-07-02 (remediation pass).

---

## Phase Map

| Phase | Name | Gate | Target Completion | Status |
|-------|------|------|------------------|--------|
| 0 | Directory Scaffolding + Governance Spine | G0 Intent | 2026-05-22 | ✅ COMPLETE — APR-0002 signed |
| 1 | Spec + Research Framing | G1 Spec | 2026-05-22 | ✅ COMPLETE — APR-0003 signed |
| 2 | Architecture + Infrastructure Design | G2 Architecture | 2026-05-22 | ✅ COMPLETE — APR-0004 signed |
| 3 | Execution + Environment Build | G3 Execution | 2026-05-22 | ✅ COMPLETE — APR-0005 signed |
| 4 | Research Build + Evidence Capture | G4 Evidence | 2026-05-28 | ✅ COMPLETE — APR-0006 + APR-0012 signed; TEST Brier +0.0084/ECE 0.0247 |
| 5 | Operational Readiness | G5 Operational | 2026-05-28 | ✅ COMPLETE — APR-0007 signed 2026-05-28 |
| 6 | Paper Trading | — | 2026-05-29 (started) | ✅ ACTIVE — running continuously since T-060; MLB is the current live pool, NBA frozen (see Phase 6/7 addendum below) |
| 7 | Promotion Gate | G6 Release | Est. Aug–Oct 2026 (MLB accumulation + EXP-017) | 🟡 IN PROGRESS — count+sign threshold met on MLB (49/30), EXP-017 commercial validation + DS sign-off still binding (GG-004 OPEN) |
| 8 | Live Capital Operations | — | Post-G6 | 🔴 Not Started |
| 9 | Self-Service Governance | — | Ongoing from Phase 8 | 🔴 Not Started |

*(Corrected 2026-07-02 — this table previously showed Phases 5–7 as "🔴 Not Started," a leftover from before G5 closed on 2026-05-28. It had not been touched since, despite Phase 6/7 running live for the following five-plus weeks. See the Phase 5/6/7 section detail below, which was already partially accurate and is the basis for this correction, and the addendum after Phase 7 for the MLB pivot this table predates entirely.)*

---

## Phase 0 — Directory Scaffolding + Governance Spine
**Gate: G0 Intent | Status: ✅ COMPLETE (APR-0002 signed 2026-05-22)**

| Milestone | Owner | Status |
|-----------|-------|--------|
| Full directory skeleton instantiated | DS | ✅ Done 2026-05-21 |
| 00_ADMIN complete (Charter, RACI, Glossary, Approvals, Access) | DS/PO | ✅ Done 2026-05-22 |
| ADR-0001 and ADR-0002 accepted | DS | ✅ Done 2026-05-21 |
| MEMORY_BANK.md initialized with all canonical links | DS | ✅ Done 2026-05-22 |
| Baseline Context Pack produced | DS | ✅ Done 2026-05-22 (CP-2026-05-22_baseline-handoff.md) |
| G0 exit: Charter frozen; RACI published; Memory Bank initialized | DS/PO | ✅ COMPLETE — APR-0002 signed 2026-05-22 |

---

## Phase 1 — Spec + Research Framing
**Gate: G1 Spec | Status: ✅ COMPLETE (APR-0003 signed 2026-05-22)**

| Milestone | Owner | Status |
|-----------|-------|--------|
| REQUIREMENTS.md frozen (all FR/NFR complete) | PO | ✅ Done 2026-05-22 (T-010) |
| ACCEPTANCE_CRITERIA.md frozen | EO | ✅ Done 2026-05-22 (T-011) |
| RESEARCH_QUESTIONS.md initial set | RL | ✅ Done 2026-05-22 |
| HYPOTHESES.md initial set | RL | ✅ Done 2026-05-22 |
| Player_Attribute_Matrix staged as DS-01 with header | RL | ✅ Done 2026-05-22 (SNAP-001) |
| ADR-0002 confirmed (strategy class: forecast-only) | DS | ✅ Done 2026-05-21 |
| ASSUMPTIONS_REGISTER.md populated | RL/AO | ✅ Done 2026-05-22 |
| G1 exit: Requirements testable; priorities explicit; assumptions logged | PO/DS | ✅ COMPLETE — APR-0003 signed 2026-05-22 |

---

## Phase 2 — Architecture + Infrastructure Design
**Gate: G2 Architecture | Status: ✅ COMPLETE (APR-0004 signed 2026-05-22)**

| Milestone | Owner | Status |
|-----------|-------|--------|
| ARCHITECTURE_OVERVIEW.md canonical | AO | ✅ Done 2026-05-22 |
| INTERFACES_CONTRACTS.md with downstream acknowledgement | AO | ✅ Done 2026-05-22 |
| DATA_FLOWS_LINEAGE.md complete | AO | ✅ Done 2026-05-22 |
| RESILIENCE_FAILURE_MODES.md (all components) | AO | ✅ Done 2026-05-22 |
| THREAT_MODEL.md drafted | AO/RCO | ✅ Done 2026-05-22 |
| DEPENDENCY_LOCKS/ initialized | EL | ✅ Done 2026-05-22 |
| G2 exit: Interfaces stable; failure modes mapped; architecture canonical | AO/EL/DS | ✅ COMPLETE — APR-0004 signed 2026-05-22 |

---

## Phase 3 — Execution + Environment Build
**Gate: G3 Execution | Status: ✅ COMPLETE (APR-0005 signed 2026-05-22)**

| Milestone | Owner | Status |
|-----------|-------|--------|
| RUN_INSTRUCTIONS.md + ENVIRONMENTS.md canonical | EL | ✅ Done 2026-05-22 |
| PLAN.md + RID_LOG.md baselined | EL | ✅ Done 2026-05-22 |
| ADR-0003 accepted (Kalshi primary venue) | AO | ✅ Done 2026-05-23 (APR-0011) |
| C1 NBAIngestionClient implemented | EL | ✅ Done 2026-05-26 (T-032) |
| C2 FeatureStore implemented (v1.2.0, 31 features) | EL | ✅ Done 2026-05-28 (T-033/T-046) |
| C3 ModelForecaster + C4 RiskEngine + C6 AuditLogger implemented | EL | ✅ Done 2026-05-26–28 (T-034/T-039/T-039b) |
| 179/179 tests passing | EL | ✅ Done 2026-05-28 |
| G3 exit: Delivery path credible; owners assigned; constraints acknowledged | EL/DS | ✅ COMPLETE — APR-0005 signed 2026-05-22 |

---

## Phase 4 — Research Build + Evidence Capture
**Gate: G4 Evidence | Status: ✅ COMPLETE — G4 CLOSED 2026-05-28 (APR-0006 + APR-0012)**

| Milestone | Owner | Status |
|-----------|-------|--------|
| TEST_STRATEGY.md complete | EO | ✅ Done 2026-05-22 |
| VALIDATION_PLAN.md complete (req mapping table) | EO/MV | ✅ Done 2026-05-22 |
| EXP-001/002/003 complete (50-player cohort, SNAP-2026-05-28-001) | RL | ✅ Done 2026-05-28 (T-043) |
| G4 evidence criteria met (3/3 beat null; ECE<0.05 all) | RL | ✅ Done 2026-05-28 |
| HYP-001/002/004 confirmed; HYP-005 falsified | RL | ✅ Done 2026-05-28 (T-044) |
| FEATURE_VERSION 1.2.0 (prune F-032–F-038) | EL | ✅ Done 2026-05-28 (T-046) |
| ADR-0004 ACCEPTED via APR-0012 (LR+Platt model class, v1-9939a6a5) | AO | ✅ Done 2026-05-28 (T-047/048) |
| PERFORMANCE_METRICS.md populated (validation + TEST set) | MV | ✅ Done 2026-05-28 |
| VALIDATION_SIGNOFF.md — all 4 roles signed | MV/EO | ✅ Done 2026-05-28 |
| ASSUMPTIONS_LIMITATIONS.md populated | MV | ✅ Done 2026-05-28 |
| G4_VALIDATION_REPORT.md complete (TEST results populated) | EO | ✅ Done 2026-05-28 |
| G4 Context Pack produced (CP-2026-05-28) | DS | ✅ Done 2026-05-28 |
| TEST set evaluation — Brier +0.0084 / ECE 0.0247 / AUC 0.6062 | RL | ✅ Done 2026-05-28 (T-048) |
| Risk limit thresholds confirmed with evidence basis | RCO/MV | 🔲 DEFERRED — Phase 5 (live-data signal context required) |
| G4 exit: Evidence collected; model validated; TEST set assessed; sign-off path executed | EO/MV/DS | 🔲 PENDING |

---

## Phase 5 — Operational Readiness
**Gate: G5 Operational | Status: ✅ COMPLETE — APR-0007 signed 2026-05-28. All milestones below done 2026-05-28 (C7 monitoring/kill switch, C8 dashboard, kill switch drill PASSED at 0.340ms — KS-C8D7D90AF942, SENSITIVITY_STRESS_TESTS.md populated ST-001–004 all pass, CAPACITY_PLANNING.md stub created, ACC-0002 Kalshi read-only key provisioned). *(Status line corrected 2026-07-02 — table below already showed the milestones done; only this header still said "Not Started.")*

| Milestone | Owner | Due |
|-----------|-------|-----|
| C7 Monitoring + Kill Switch implemented and tested | EL | Phase 5 |
| C8 Visual Dashboard — Phase 5 panels (health + forecast performance + calibration trend + alert feed) | EL | Phase 5 |
| Kill switch drill timed and verified ≤60 seconds (TC-007, NFR-03) | EL/EO | Phase 5 |
| SLA_SLO_SLI.md thresholds populated with evidence | OO | Phase 5 |
| OBSERVABILITY.md wired (C7 metrics emitting) | OO | Phase 5 |
| Live credentials provisioned (ACC-0002) | EL | Phase 5 (before G5) |
| Venue API integration smoke test (no orders) | EL | Phase 5 |
| SENSITIVITY_STRESS_TESTS.md populated | MV | Phase 5 |
| CAPACITY_PLANNING.md created | OO | Phase 5 |
| G5 exit: Operable by someone other than builder; kill switch tested | OO/DS | G5 |

---

## Phase 6 — Paper Trading
**Gate: — | Status: ✅ ACTIVE since 2026-05-29 (T-060), running continuously through this writing (2026-07-02). *(Status line corrected 2026-07-02 — was still "Not Started" despite five-plus weeks of live paper trading.)***

| Milestone | Owner | Due | Status |
|-----------|-------|-----|--------|
| ADR-0004 formally accepted (APR-0012) | AO | G4 gate | ✅ Done 2026-05-28 |
| C5 Execution Engine implemented (simulated) | EL | Phase 6 | ✅ Done — PaperTrader, dual-ledger MLB/NBA |
| C8 Visual Dashboard — paper trading panels (P&L, fill rates, position history) | EL | Phase 6 | ✅ Done — localhost web dashboard added SESSION 104 (GG-057) |
| Live inference pipeline running (no orders) | EL | Phase 6 | ✅ Done — PIPE-02/03/06/07 (NBA), T1–T4M-PROJ (MLB) |
| Paper trading position sizing and order simulation | EL | Phase 6 | ✅ Done |
| HYP-003 tested (EXP-004 — edge vs vig) | RL | Phase 6 | ✅ CONFIRMED (NBA); MLB commercial validation is a separate open experiment, EXP-017, see Phase 7 |

**MLB extension to Phase 6 (not in the original phase design, added post-facto — no entry below predates this because Phase 6 was originally scoped single-sport/NBA):** MLB C1/C2/C3 unblocked Phase 3 gate (T-072, SESSION 73); MLB T1/T2/T3 paper trading cron-active; MLB T4M-PROJ live under ADR-0023; MLB T4M-ARITH/T4M-FLOW built and unit-tested under ADR-0039 but registry-`BLOCKED` pending their own experiments. This is the mechanism the Principal Vision section of `CLAUDE.md` describes ("New sport: new C1 data module, new C2 feature set, same methodology") operating for real, not a hypothetical — worth noting here since this document's original text gives no indication a second sport was ever added.

---

## Phase 7 — Promotion Gate
**Gate: G6 Release | Status: 🟡 IN PROGRESS (paper trading active on both books; MLB is the active G6 evidence pool)**

| Milestone | Owner | Due | Status |
|-----------|-------|-----|--------|
| Paper trading live (T-060) | EL | — | ✅ 2026-05-29 — PIPE-03 (NBA) running; MLB T1/T2/T3/T4M-PROJ cron/systemd-active since Phase 3 MLB unblock (T-072) |
| 30+ resolved paper bets with positive P&L (T-070) | DS | Originally ~2026-06-22 (NBA Finals window) | **NBA: 158/30 resolved but adjudicated a negative baseline (GG-034/GG-037) — frozen, not the active G6 pool.** **MLB (current active pool): 49/30 resolved as of SESSION 113 (2026-07-02), count+sign threshold met, +$100.00 realized P&L.** Count+sign alone does not close G6 — see next row. |
| EXP-017 commercial validation (real market-price benchmark, GG-004) | RL/DS | Binding G6 blocker | 🔴 **NOT YET RUN.** This is the actual gate, not the 30-bet count above — CLAUDE.md's "commercial validation gap" section governs. Do not treat the 49/30 or 158/30 figures as G6 progress without this. |
| ADR-0005 drafted (live capital authorization) | AO | After EXP-017 | 🔲 Not started |
| Final validation report (TEST set + live paper results) | MV/EO | After evidence | 🔲 Not started |
| Live credentials (ACC-0002 confirmed for write-mode) | EL | Phase 7 | 🔲 Not started |
| G6 exit: All release gate criteria; ADR-0005 accepted; APR-0009 signed | DS/RCO | G6 | 🔲 Not started |

**⚠️ Calendar Constraint (KI-009) — HISTORICAL, superseded by the MLB pivot, retained for record:**
The original 50-bet (later 30-bet) evidence gate was time-bounded by the NBA season calendar. The 2025-26 NBA Finals ended ~2026-06-22, after which NBA went dark until the 2026-27 season (per operator directive, NBA work is tabled until ~1 month before that tip-off). **This constraint is why MLB became the active G6 pool** — MLB's regular season provided a continuous accumulation window the NBA off-season could not. NBA's 158 resolved bets are frozen at a negative baseline (GG-034/GG-037) and are not being pursued toward G6; MLB is.

**APR-0016 ACCEPTED 2026-05-29 (DS):**
G6 evidence threshold formally revised from 50 → 30 resolved paper bets, applicable to whichever pool is active. Evidence quality standard (Brier-consistent positive EV) is unchanged. This threshold is now being evaluated against MLB, not NBA — see row above. ADR-0028 (ACCEPTED, SESSION 72) further refined this into the current segmented band-promotion / 6-item T1-only closure condition; read `MEMORY_BANK.md` M6 for the exact live wording rather than treating this paragraph as the final formulation.

*(This entire Phase 7 section was last substantively updated when NBA was still the active pool and 0 bets had resolved. Corrected 2026-07-02 to reflect the MLB pivot, current resolved-bet counts, and — most importantly — that EXP-017, not the bet count, is the actual binding blocker. See `03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-004.)*

---

## Phase 8+ — Live Capital + Self-Service Governance

| Phase | Description | Gate |
|-------|-------------|------|
| 8 | Live capital operations; full C1–C8 active | Post-G6 |
| 9 | Self-service governance; quarterly retrieval drills; meta-ADR reviews | Ongoing |

---

## Planned Artifacts (Phase 5+ — not yet created)

| Artifact | Phase | Module | Owner |
|---------|-------|--------|-------|
| SENSITIVITY_STRESS_TESTS.md | 5 | 08_MODEL_RISK_GOVERNANCE/ | MV |
| CAPACITY_PLANNING.md | 5 | 10_INFRA_OPERATIONS/ | OO |
| MIGRATION_PLAN.md | 6+ | 02_ARCHITECTURE_DESIGN/ | AO |
| FAIRNESS_BIAS_ASSESSMENT.md | 6+ | 08_MODEL_RISK_GOVERNANCE/ | MV |
| RELEASE_CHANGE_NOTES/Phase6.md | 6 | 10_INFRA_OPERATIONS/ | EL |
