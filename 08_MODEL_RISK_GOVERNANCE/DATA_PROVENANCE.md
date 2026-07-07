# Data Provenance — Prediction Market Trading Bot

**Purpose:** Document the origin, transformation history, and custody chain for all data used in model training and evaluation. Required for audit and reproducibility.  
**Owner (role):** Research Lead (RL)  
**Last reviewed:** 2026-05-22  
**Next review:** G3 (DS-01 schema validation + snapshot registration); update when any data source changes  
**Staleness triggers:** New data source confirmed; snapshot registered; schema validation completed  
**Upstream links:** DATA_REQUIREMENTS.md, DATA_FLOWS_LINEAGE.md, DATA_SNAPSHOTS_INDEX.md  
**Downstream links:** EXPERIMENT_LOG/, MODEL_CARD.md  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 7/10 — OQ-001 resolved 2026-05-22; provenance documented; schema validated; snapshot registered. Confidence bounded by absence of formal experiment validation (Phase 3+).

---

## DS-01 — Player Attribute Matrix (OQ-001 RESOLVED 2026-05-22)

| Field | Detail |
|-------|--------|
| Dataset name | Player_Attribute_Matrix_v4.docx |
| Document title | "Weighted Hybrid PRF System — A Dynamically Agnostic Framework for Player Archetype Classification" |
| Creator | Earl Ignacio (project owner; sole operator) |
| Creation date | 2026-05-21 |
| Version | v4.0 (full designation: v4 — Weighted Hybrid + Full Template) |
| Format | .docx (Word document); structured text framework — NOT raw tabular data |
| Sport / domain | NBA basketball |
| Scope | All NBA markets (dynamically agnostic design); applied example: 2026 Conference Finals (WCF: SAS vs OKC; ECF: NYK vs CLE) |
| PDTP validation | 9.5/10 self-assessed; 11-pass Princeton Deep Thinking Protocol (P1-P11); P9 flagged (lineup-conditional weights not yet supported) |
| Prior versions | v1, v2 (foundational template + PRF definitions), v3 (multi-season validation added, ConFin-specific), v4 (weighted hybrid system, agnostic template restored) |
| Validation status | PROVENANCE VALIDATED — see OQ-001 resolution; schema validation pending (Phase 3) |
| Snapshot status | REGISTERED — see DATA_SNAPSHOTS_INDEX.md (SNAP-001) |

### DS-01 Framework Schema

The document defines a **player classification framework** (not a raw statistics dataset). Its schema has three layers:

**Layer 1 — PRF Taxonomy (15 categories):**

| PRF | Name | Defining Constraint |
|-----|------|---------------------|
| PRF-1 | Heliocentric On-Ball Engine | USG ≥ 30% |
| PRF-2 | Primary Facilitator/Creator | USG ≥ 22%; AST% ≥ 25%; creator-first |
| PRF-3 | Secondary Creator / Advantage Extender | USG 18-28%; secondary initiator |
| PRF-4 | 3-and-D / Off-Ball Shooter | USG ≤ 18%; off-ball movement dependent |
| PRF-5 | Slasher / Wing Scorer | USG 18-25%; rim-attack dependency |
| PRF-6 | Post Hub / Elbow Creator | Post USG > 20% |
| PRF-7 | Roll-Man / Screener | Screen assists + roll-man rate dominant |
| PRF-8 | Stretch Big / Pick-and-Pop | 3PA/g ≥ 2.5 at C/PF position |
| PRF-9 | Rim Anchor / Defensive Hub | Rim protection primary role |
| PRF-10 | Primary On-Ball Stopper | POA defensive assignment rate dominant |
| PRF-11 | Switchable Wing / Multi-Stopper | 1-4 or 1-5 switch capability documented |
| PRF-12 | Rebounder / Glass Specialist | OREB% + DREB% dominant role |
| PRF-13 | Transition Trigger / Pace Pusher | Transition rate top-decile |
| PRF-14 | Bench Microwave Scorer | Bench USG ≥ 22%; shot volatility above team mean |
| PRF-15 | Utility Depth / Low-Usage Stabilizer | USG ≤ 15%; turnover avoidance + role discipline |

**Layer 2 — Modifier System (32 modifiers M-1 through M-32):**
Threshold-anchored binary flags. Each has explicit activation criterion. Standard cap: 0-3 per player (generational players may carry more). Key modifiers:
- M-1 (Elite Gravity), M-2 (Elite Foul Drawer), M-3 (Elite Rim Finisher), M-4 (Elite Midrange Shotmaker), M-5 (Elite Pull-Up 3 Threat), M-6 (Elite Passing Vision), M-7 (Elite Handle), M-8 (Elite Screen Navigator), M-9 (Elite Help Rotator), M-10 (Elite Rim Deterrence), M-11 (Elite Switchability 1-4 or 1-5), M-12 (Elite Zone/Hybrid IQ), M-13 (Elite Offensive Rebounder), M-14 (Elite Defensive Rebounder), M-15 (Elite Transition Decision-Maker), M-16 (Elite Clutch Process), M-17 (High Variance/Streak Profile), M-18 (Low Variance/Error-Minimizer), M-19 (Injury-Managed/Load-Sensitive — GAME-DAY REAUTH REQUIRED), M-20 (Developmental Upside), M-21 (Veteran Floor General), M-22 through M-32 (Specialist categories)

**Layer 3 — Weighted Hybrid PRF Notation (v4 innovation):**
Weights derived from 6 evidence sources: possession distribution, primary defensive assignment %, minutes by role, shot profile distribution, touch-type distribution, lineup context adjustment. Notation: PRF-X [N%] / PRF-Y [M%] (weights sum to 100%). Applied through weight-aware scaling rules (Section 7) to forecast inputs.

### DS-01 Underlying Data Sources

The framework is built on publicly available NBA data and tracking data. Data sources referenced in the document:

| Source Category | Source / Provider | Metrics Derived | Notes |
|----------------|------------------|-----------------|-------|
| NBA box score statistics | Publicly available (NBA.com, Basketball-Reference) | USG%, FTr, eFG%, AST%, TOV%, OREB%, DREB%, 3P%, per-game stats (ppg, blk/g, etc.) | Standard publicly available metrics |
| Tracking data | Synergy Sports | Possession distribution %, defensive assignment rate, shot type distribution, screen assists, touch types | Cited explicitly in document (Sections 4.1, 8.2); subscription product |
| Tracking data | Second Spectrum | Face-guard rate, coverage distortion metrics, per-possession role attribution | Cited explicitly (Sections 4.1, PDTP P2); NBA partnership data |
| Lineup / role data | NBA game logs + lineup databases | Minutes by role (starter vs bench), lineup combinations | Derived from game-by-game logs |
| Derived frameworks | Positional polyvalence research (basketball analytics literature) | Theoretical basis for PRF hybridization | PDTP P2 citation |
| Self-generated (proprietary) | Earl Ignacio (creator) | PRF taxonomy, modifier thresholds, weighting methodology, scaling rules | Proprietary classification system built on top of the public data |

**Data span:** 3 seasons of regular-season + playoff data per player (per Section 8.2 usage guidelines).

### DS-01 Known Caveats and Risk Flags

1. **Framework, not raw data:** DS-01 is a classification framework applied to NBA data. It is NOT a raw statistics dataset. Experiments using DS-01 must define how PRF classifications and modifier flags are operationalized as numeric features.
2. **Tracking data dependency:** PRF weights and modifier thresholds depend on Synergy and Second Spectrum data for their most precise derivations. These are subscription products. Access to these sources for model training must be confirmed before Phase 3 experiments.
3. **Snapshot in time:** The 2026 Conference Finals application is a static snapshot. For live trading, PRF assignments and weights require per-series re-verification and M-19 game-day reauthorization.
4. **v5 known weaknesses (per document):** Lineup-conditional weights not yet implemented; dynamic weight evolution through a series not yet supported; modifier threshold drift needs quarterly review.
5. **Research input only:** DS-01 informs feature engineering design (PRF classifications as features; modifier flags as binary features; hybrid weights as continuous features). It must NOT be used directly as a predictive model output.

**Actions required before DS-01 can be used in any experiment:**
1. ~~Resolve OQ-001 (creator, creation date)~~ ✅ RESOLVED 2026-05-22
2. Confirm access to Synergy and/or Second Spectrum data (or identify public proxies) — flags as new OQ for Phase 3
3. Define operationalization of PRF classifications as numeric features for ML input
4. Validate operationalized features against DATA_REQUIREMENTS.md (DS-01 requirements)
5. Register snapshot with temporal_cutoff in DATA_SNAPSHOTS_INDEX.md ✅ SNAP-001 registered
6. Document transformation steps in DATA_FLOWS_LINEAGE.md at experiment time

---

## DS-02 — Market Data Feed

**⚠️ Corrected 2026-07-06 (GG-074 remediation) — "PENDING"/"TBD at ADR-0003" below is stale.** ADR-0003 (2026-05-23) confirmed Kalshi as primary venue and the live market data feed (KXNBAPTS for NBA, KXMLBHIT for MLB) has been active in production for weeks. "Domain: NBA basketball" is also stale — MLB is now the ACTIVE pool with its own KXMLBHIT market data feed; NBA is DARK/FROZEN.

| Field | Detail |
|-------|--------|
| Dataset name | Market data feed |
| Primary venue | Kalshi (OQ-003 resolved 2026-05-22) |
| Full deployment target | Multi-venue (all prediction markets legally available in CA) — subject to ADR-0003 |
| Status | PENDING — venue API access and schema TBD at ADR-0003; Kalshi confirmed as primary |
| Schema | TBD at ADR-0003; Kalshi REST API (kalshi.com) for market prices, bid/ask, settlement |
| Domain | NBA basketball (all market types — dynamically agnostic to event type within NBA) |

---

## DS-03 — Outcome / Resolution Data

**⚠️ Corrected 2026-07-06 (GG-074 remediation) — "PENDING" below is stale; ESPN/MLB Stats API outcome resolution has been live for both NBA and MLB for weeks, on the separate ingestion path this section requires.** "Domain: NBA" is also stale — MLB outcome resolution is equally active; NBA is DARK/FROZEN, not the sole domain.

| Field | Detail |
|-------|--------|
| Dataset name | Outcome / contract resolution data |
| Source | Venue API (Kalshi primary; multi-venue at full deployment — ADR-0003) |
| Domain | NBA (all event types — dynamically agnostic) |
| Status | PENDING |
| Critical constraint | MUST be ingested on a separate path from feature data; NEVER enters feature store (TI-03) |

---

## Data Provenance Audit Trail

Every experiment record must document:

1. All Snapshot IDs used
2. Schema version of each snapshot
3. Transformation steps applied (per DATA_FLOWS_LINEAGE.md lineage register)
4. temporal_cutoff for each feature
5. Outcome data used only for evaluation, not feature derivation

*Populated during Phase 3 as experiments are run.*
