# Open Questions — Prediction Market Trading Bot

**Purpose:** Capture all unresolved questions that block or risk downstream work. An open question without an owner and deadline is a gap waiting to cause a problem.  
**Owner (role):** Director/Sponsor (DS)  
**Last reviewed:** 2026-05-28 (EXP-001/002/003 COMPLETE — OQ-018 and OQ-019 filed based on experiment findings)  
**Next review:** Weekly DIR; resolve before relevant gate  
**Staleness triggers:** Question answered; new blocker identified; gate readiness review  
**Upstream links:** ASSUMPTIONS_REGISTER.md, REQUIREMENTS.md, ADR-0002  
**Downstream links:** ROADMAP_MILESTONES.md, 04_EXECUTION/RID_LOG.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 7/10 — Known unknowns catalogued; unknown unknowns surface during Phase 3

---

## Open Questions — Research / Data

| ID | Question | Why It Matters | Owner | Target Resolution | Gate |
|----|----------|----------------|-------|------------------|------|
| ~~OQ-001~~ | ~~What is the provenance and schema of Player_Attribute_Matrix v4? Who created it, when, and from what source data?~~ | **RESOLVED 2026-05-22** — see Resolved section | — | — | — |
| ~~OQ-015~~ | ~~Synergy / Second Spectrum tracking data access for Phase 3~~ | **RESOLVED 2026-05-23** — see Resolved section | — | — | — |
| OQ-002 | Does the Player_Attribute_Matrix contain sufficient events with resolved outcomes to produce statistically meaningful Brier scores? | Determines if ASM-003 (event volume) holds | RL | Phase 3 data ingestion | Phase 3 |
| ~~OQ-003~~ | ~~What is the target market category? (Sports, politics, crypto, economics?)~~ | **RESOLVED 2026-05-22** — see Resolved section | — | — | — |
| OQ-004 | What is the minimum event history required for a valid backtest? (N events for confidence intervals on Brier score?) | Prevents drawing conclusions from statistically insufficient experiments | RL | 2026-06-28 | ADR-0003 |
| OQ-005 | Which specific PRF archetypes and modifiers from the Player_Attribute_Matrix have the highest predictive signal for player props? | Framework for how to operationalize DS-01 is established (QUALITATIVE_SIGNALS.md, QUALITATIVE_REGISTRY.md, QualitativeSignalStore). Open question is now specifically: which of the 15 archetypes and 32 modifiers, once classified for the 50-player cohort, produce measurable Brier Δ? Requires running EXP after DS-01 QS snapshot is populated. | RL | Phase 6 experiment after DS-01 classification | Phase 6 |

---

| OQ-016 | What is the optimal ERI signal composition and weighting? (Which of eri_prev_hot, eri_prev_cold, eri_consec_cold_games adds signal vs noise?) | Determines whether ERI v0 features survive to FEATURE_VERSION 1.2.0 or are pruned | RL | Phase 4 feature importance analysis | Phase 4 |
| ~~OQ-017~~ | ~~Which PRF archetypes have the highest incremental Brier improvement?~~ | **RESOLVED 2026-05-28** — PRF one-hot encoding implemented (prf_w01…prf_w15, weighted continuous). EXP-008 measures per-archetype coefficients. Weighted hybrid notation from PAM v4 used directly as model input — no spurious ordinality. | — | — | — |
| ~~OQ-020~~ | ~~What is the practical temporal integrity protocol for QTI-03 backdating?~~ | **RESOLVED 2026-05-28** — QS-2026-05-28-002 established the operational standard: backdated=1 + per-player backdating_rationale citing seasons where archetype was observable. EXP-007 confirmed POSITIVE_SIGNAL (+0.0017 Brier) validating the approach. | — | — | — |
| OQ-021 | Which amplification contexts (qualitative × game situation) produce the largest per-context Brier Δ, and in what order should they be implemented? | QualitativeAmplifier (Layer 3, F-300+) is structured but stubbed. Five initial contexts defined (CTX-1 through CTX-5). Need to determine: (1) which PRF archetype × streak interactions have the most signal; (2) whether M-16 (clutch) × season stage is measurable at this dataset scale; (3) whether load stress (M-19 × above-avg-minutes) has Brier impact. Each context requires its own EXP before promotion. | RL | Phase 6 — after EXP-008 baseline established | Phase 6 |
| OQ-018 | What minimum player set size (N players) is required for the baseline LR model to consistently beat the null model Brier? | EXP-001 (10 players, 986 TRAIN rows) barely beat null (+0.0046). EXP-003 (197 TRAIN rows) failed. Training data volume appears to be the primary bottleneck — but the right player count is unknown. | RL | Phase 4 — expand player set incrementally (10→25→50) and track Brier improvement vs null | Phase 4 |
| OQ-019 | Does FEATURE_VERSION 1.1.0 (38 features, including ERI/schedule) outperform v1.0.0 (31 features) on the EXP-001 window? | HYP-005 requires an ablation experiment comparing v1.0.0 vs v1.1.0 on the same data. Cannot be answered without re-running the pipeline with feature version pinned at 1.0.0. | RL | Phase 4 ablation experiment (re-run EXP-001 window with v1.0.0 features) | Phase 4 |

---

## Open Questions — Architecture / Technology

| ID | Question | Why It Matters | Owner | Target Resolution | Gate |
|----|----------|----------------|-------|------------------|------|
| ~~OQ-006~~ | ~~CA-legal venue enumeration for full multi-venue deployment~~ | **RESOLVED 2026-05-23** — see Resolved section | — | — | — |
| OQ-007 | What technology stack (language, data storage, logging framework)? | Determines ENVIRONMENTS.md, DEPENDENCY_LOCKS/, and C1–C3 implementation | AO | G2 Architecture Gate | G2 |
| OQ-008 | What version control system and hosting approach? | Required before any code is written | DS | G2 Architecture Gate | G2 |
| OQ-009 | What secrets vault approach for API credentials? | Required before any venue API access | AO | G5 Operational Gate | G5 |
| OQ-010 | How will C7 monitoring collect metrics in the chosen stack? (Push vs pull; alerting mechanism?) | Required for kill switch wiring at G5 | AO | G5 Operational Gate | G5 |

---

## Open Questions — Risk / Execution

| ID | Question | Why It Matters | Owner | Target Resolution | Gate |
|----|----------|----------------|-------|------------------|------|
| OQ-011 | What is the appropriate Kelly fraction? (0.25×? 0.5×?) | Determines position sizing; affects drawdown risk materially | RCO + RL | G4 Evidence Gate | G4 |
| OQ-012 | What are the hard limit thresholds? (single-event %, daily loss %, drawdown %) | Currently TBD at G4 in RISK_APPETITE_CONSTRAINTS.md; must be evidence-based | RCO | G4 Evidence Gate | G4 |
| OQ-013 | What is the minimum paper trading period and event count before G6 promotion is eligible? | Determines Phase 6 duration and G6 readiness criteria | RCO + EO | ADR-0004 | G5 |
| OQ-014 | What is the initial live capital amount (if G6 is cleared)? | Required for RESOURCE_BUDGET.md; risk limits expressed as % of initial capital | DS + RCO | G6 Release Gate | G6 |

---

## Resolved Questions (Archive)

*Moved here when answered; resolution and date recorded.*

| ID | Question | Resolution | Date | Evidence |
|----|----------|-----------|------|----------|
| OQ-001 | DS-01 provenance: who created Player_Attribute_Matrix v4, when, from what sources? | **Creator:** Earl Ignacio (project owner / sole operator). **Date:** 2026-05-21. **Sport:** NBA basketball. **Document title:** "Weighted Hybrid PRF System — A Dynamically Agnostic Framework for Player Archetype Classification." **Sources:** NBA box score stats (Basketball-Reference/NBA.com), Synergy Sports tracking data, Second Spectrum tracking data, NBA game logs. **Schema:** 15-PRF taxonomy + 32 modifiers + weighted hybrid notation; 3-season data span. **Snapshot:** SNAP-001 registered. Full provenance in DATA_PROVENANCE.md. | 2026-05-22 | DATA_PROVENANCE.md; SNAP-001 (DATA_SNAPSHOTS_INDEX.md) |
| OQ-003 | Target market category? (sport, event type, venue) | **Domain:** NBA basketball. **Event type:** Dynamically agnostic — framework designed to cover any/all NBA prediction market types with tactical deployment per specific market. No single event type excluded. **Venue:** Kalshi (primary for initial deployment); multi-venue target for full deployment (all prediction markets legally available in CA — enumeration is OQ-006 remainder). | 2026-05-22 | Operator decision (Earl Ignacio, 2026-05-22); OQ-006 updated for remaining venue enumeration question |
| OQ-006 | CA-legal venue enumeration for full multi-venue deployment | **Confirmed CA-legal venues:** (1) **Kalshi** — CFTC Designated Contract Market (DCM); legally available in all 50 states including CA; ~$5B monthly notional volume; NBA sports markets; API available. (2) **Polymarket US** — Relaunched December 2025 as CFTC-regulated platform; CA-legal; NBA sports and general prediction markets; fully open API (public market data without auth; KYC required for order execution). **Note:** Polymarket US's CFTC-regulated status resolves the Option C concern in ADR-0003 — Polymarket US is now eligible for Option B multi-venue integration; ADR-0003 updated accordingly. Other platforms (Robinhood Prediction Markets, etc.) not confirmed CFTC-regulated or CA-legal as of 2026-05-23. | 2026-05-23 | Web research 2026-05-23; covers.com, actionnetwork.com, quantvps.com; ADR-0003 updated to ACCEPTED |
| OQ-015 | Can Synergy Sports and Second Spectrum tracking data be accessed for Phase 3? If not, what are the best publicly available proxy data sources? | **Synergy Sports:** No public API; enterprise-only (~$2,925/month); acquired by Sportradar. NOT viable as Phase 3 proxy. **Second Spectrum:** Enterprise/Genius Sports; no public access. NOT viable. **Confirmed proxy — nba_api (Python):** Free, open-source Python package wrapping NBA.com stats API. No authentication required. Provides box scores, play-by-play, shot charts, player stats, and NBA.com tracking endpoints (shot-level and possession-level data). Available via PyPI (`nba_api`). Sufficient for Phase 3 initial experiments using box-score features (PRF archetypes, game logs, player metrics). Tracking-specific modifiers (M-9, M-10, M-11 — possession distribution, defensive assignments) will be approximated from NBA.com tracking data available in `nba_api`. If approximations are insufficient in Phase 3 evidence, Synergy/Second Spectrum access is deferred to Phase 4 as an enhancement OQ. | 2026-05-23 | Web research 2026-05-23; github.com/swar/nba_api; pypi.org/project/nba_api; Synergy and Second Spectrum confirmed enterprise-only |
