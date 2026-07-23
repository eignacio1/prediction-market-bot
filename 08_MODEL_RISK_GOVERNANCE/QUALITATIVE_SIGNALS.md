# Qualitative Signal Governance — Prediction Market Trading Bot

**Purpose:** Define what qualitative signals are, how they enter the pipeline, how they are versioned, and what temporal integrity rules govern their use in model training and inference.  
**Owner (role):** Research Lead (RL) + Architecture Owner (AO)  
**Status:** CANONICAL — 2026-05-28 (updated after EXP-007 positive signal; three-layer amplification principle added)  
**Last reviewed:** 2026-07-23 — GG-074 monthly staleness review: verified current, no new drift found. Re-checked both points in the 2026-07-06 correction note below against live state: FEATURE_VERSION is still 1.4.0 (`c2_feature_store/features.py:120`); GG-094 (MLB has no qualitative/PRF-analogue layer) is still OPEN per `GOVERNANCE_GAP_LOG.md`. Also confirmed Section 7's Layer 3 status ("🔲 SKELETON") is still accurate — OQ-021 (L3 amplification needs non-linear model or more data) remains open per `MEMORY_BANK.md`'s M2 open-question table, no QualitativeAmplifier experiment has run since.  
**Next review:** After EXP-008 (PRF one-hot); after QualitativeAmplifier first experiment  
**Staleness triggers:** New qualitative source registered; operationalization of an existing source completed; temporal integrity protocol revised  
**Upstream links:** DATA_FLOWS_LINEAGE.md, INTERFACES_CONTRACTS.md (IF-DS-Q-C2)  
**Downstream links:** 05_RESEARCH_EXPERIMENTS/DATA_SOURCES/QUALITATIVE_REGISTRY.md, c2_feature_store/qualitative_store.py  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 9/10 — Framework defined; operationalization of individual sources is pending
**Decisions logged:** true — T-098 logged 2026-06-02: L1/L2/L3 layer definitions, temporal isolation (shift(1)) requirement, L3 promotion gate (Brier improvement ≥0.001 at N≥100), QUALITATIVE_REGISTRY.md as source registration requirement. See DECISION_LOG.md 2026-06-02.

**⚠️ Corrected 2026-07-06 (GG-074 remediation).** Two points:
1. **Section 7's "Layer 1: ✅ IMPLEMENTED (F-001–F-031, FEATURE_VERSION 1.2.0)" is stale on the version number** — confirmed via `c2_feature_store/features.py`, `FEATURE_VERSION` is now `1.4.0`, not 1.2.0. The feature set has been revised at least twice since this document's last edit (2026-05-28) without a corresponding update here.
2. **This entire document (PAM v4 / PRF taxonomy, Layers 1–3, Sections 1–9) is NBA-only and has no MLB counterpart, and this is a real scope gap, not just missing documentation.** Confirmed via direct code inspection: `c2_feature_store/mlb_features.py` (541 lines, `MLB_FEATURE_VERSION = "1.0.0"`) contains zero qualitative/archetype/role/PRF content — it computes only quantitative rolling-batter-stat features. `qualitative_store.py` and `qualitative_amplifier.py` (the modules this document describes in Sections 5 and 7) have no MLB references either. MLB's C2 feature store is quantitative-only; the "baseball analogue of the PRF framework" anticipated in `MLB_BUILDOUT_SCAFFOLD_PLAN.md` was never built. Since MLB is now the ACTIVE paper-trading pool (NBA is DARK/FROZEN), this document currently governs qualitative-signal practice for a book that isn't running, while the book that is running (MLB) has no qualitative-signal governance document or implementation at all. Recommend registering the missing MLB qualitative layer as its own governance-gap candidate if MLB's model is expected to eventually use structural/role context the way NBA's does — not resolved in this pass.

---

## 1. What Is a Qualitative Signal?

A **qualitative signal** is any player or team attribute that:

1. Cannot be derived algorithmically from box-score statistics alone
2. Requires human judgment, domain expertise, or specialized source data for classification
3. Is updated on a **seasonal or multi-season cadence** — not per-game
4. Has a defined **effective period** (start date, optional end date) during which the classification is considered valid

Qualitative signals are **auxiliary enhancements** to the raw quantitative computation base (F-001–F-031). They do not replace rolling box-score features; they provide structural context that box-score averages cannot capture — player archetype, role, tendencies, and modifiers that explain *how* a player produces stats, not just *how many*.

---

## 2. How Qualitative Signals Differ from Quantitative Features

| Dimension | Quantitative (F-001–F-031) | Qualitative (F-100+) |
|-----------|---------------------------|----------------------|
| Source | nba_api game logs (DS-02 via C1) | Classification documents, expert annotation, specialized data (DS-01+) |
| Update cadence | Per-game | Per-season or multi-season |
| Derivation | Deterministic formula (rolling mean, std, ratio) | Human judgment + criteria, or trained classifier |
| Look-ahead risk | Controlled by .shift(1) rolling window (TI-01) | Controlled by effective_date join guard (QTI-01) |
| Missing values | NaN for first game in window (low frequency) | NaN for any game_date before classification effective_from (expected for historical training) |
| Version key | FEATURE_VERSION (C2) | QS_VERSION (qualitative snapshot version) |

---

## 3. Temporal Integrity Rules for Qualitative Features

Qualitative features introduce a distinct look-ahead risk: a classification made using 2025-26 season observations must not contaminate training data from 2021-22. The following rules govern this.

### QTI-01 — Effective Date Guard (blocking rule)

Every qualitative classification must specify `effective_from` — the earliest game date for which the classification is valid. The C2 join must enforce:

```
JOIN condition: game_date >= classification.effective_from
               AND game_date < classification.effective_until (or game_date is CURRENT if NULL)
```

A classification with `effective_from = 2025-10-22` will produce NaN for all games before that date. **NaN is the correct, honest output for unclassified periods.** NaN imputation at C3 training time is acceptable; silent backfill is not.

### QTI-02 — Classification Basis Must Be Prior-Season Only

The `classification_basis` field of each qualitative record must document which seasons/sources informed the classification. A classification made on 2026-05-21 may only legitimately claim `effective_from` equal to the start of the season whose performance was the primary basis.

**Legitimate:** `effective_from = 2025-10-22` for a classification made in May 2026 based on the 2025-26 season  
**Not legitimate:** `effective_from = 2021-10-19` for the same classification — that would claim the 2025-26-based classification was knowable in 2021

### QTI-03 — Historical Backdating Requires Explicit Evidence

If a classification is backdated (e.g., "SGA was PRF-7 starting in the 2022-23 season"), the classification record must include:
- `backdated: true`
- `backdating_rationale` — specific evidence that this archetype was observable at that date
- A second review sign-off before the backdated record is used in any training run

Historical backdating is a legitimate and valuable technique — it extends qualitative enrichment into historical training data — but it carries increased look-ahead risk if done carelessly.

### QTI-04 — Qualitative Snapshot Immutability

Once a qualitative snapshot is registered in the QUALITATIVE_REGISTRY.md with a QS_ID, it is immutable. Corrections create a new snapshot version with a lineage note. No silent edits after registration.

---

## 4. Qualitative Feature Taxonomy

Qualitative features occupy the **F-100+ feature ID range** in DATA_FLOWS_LINEAGE.md.

| Range | Category | Description |
|-------|----------|-------------|
| F-100–F-149 | PRF Archetype features | Player Role Framework classification (DS-01 PAM) |
| F-150–F-199 | PRF Modifier features | Binary modifier flags from DS-01 PAM |
| F-200–F-249 | Future qualitative source 1 | Reserved for DS-04 |
| F-250–F-299 | Future qualitative source 2 | Reserved for DS-05 |
| F-300–F-399 | Composite / derived qualitative | Features derived from multiple qualitative sources |
| F-099 | Market price | DS-02 Kalshi mid-price (existing; not qualitative) |

Each source registers its feature IDs in DATA_FLOWS_LINEAGE.md before any experiment uses them.

---

## 5. Pipeline Integration — Where Qualitative Signals Enter

Qualitative features are loaded by the **C2 Feature Store** via the `QualitativeSignalStore` module. They do not flow through C1 (which handles time-series game log ingestion).

```
Quantitative path:  DS-02 (nba_api) → C1 → C2 FeatureStore → [F-001–F-031]
                                                    ↓
Qualitative path:   DS-01/DS-04+    → QualitativeSignalStore → [F-100+]
                    (classification        (join by player_id
                     documents)             + effective_date guard)
                                                    ↓
                                        Merged feature DataFrame → C3
```

The `QualitativeSignalStore` is a **C2 sub-module** (`c2_feature_store/qualitative_store.py`). It:
1. Loads a registered qualitative snapshot (CSV) keyed by QS_ID
2. Left-joins to the feature DataFrame by `player_id`
3. Applies the `effective_from` / `effective_until` guard (rows outside the window → NaN)
4. Returns the enriched DataFrame with F-100+ columns appended

This is a left-join: **games without a matching qualitative record produce NaN, never an error.** NaN qualitative features are handled by C3's existing NaN imputation (column median at fit; zero at inference).

---

## 6. Registration Process for a New Qualitative Source

Before any qualitative source can be used in an experiment:

1. **Document the source** — add to QUALITATIVE_REGISTRY.md with all required metadata fields
2. **Define the schema** — create `qualitative_data/<source_name>/SCHEMA.md` with column definitions
3. **Assign feature IDs** — register F-IDs in DATA_FLOWS_LINEAGE.md qualitative section
4. **Assign a DS-ID** — DS-01 (PAM), DS-04+, registered in DATA_REQUIREMENTS.md
5. **Create and register a QS_ID snapshot** — `qualitative_data/<source_name>/<QS_ID>_classifications.csv`
6. **Register temporal bounds** — set `effective_from`, `effective_until`, `classification_basis`
7. **Wire into QualitativeSignalStore** — add source schema to the loader
8. **File an experiment** — run at least one EXP against a held-out window to measure Brier Δ

Step 8 is required before any qualitative feature is promoted to production (ENV-02/03). The same G4-equivalent evidence bar applies: qualitative features must demonstrate measurable Brier improvement, not just theoretical plausibility.

---

## 7. The Three-Layer Auxiliary Architecture

Qualitative signals are explicitly **auxiliary** to quantitative computation. They do not replace rolling box-score features; they enhance them in a structured hierarchy. This hierarchy has three layers with distinct roles and distinct failure modes.

```
┌──────────────────────────────────────────────────────────────────────┐
│  LAYER 1 — QUANTITATIVE  (F-001–F-031)                               │
│  "What has this player done recently?"                               │
│  Source: nba_api rolling box-score (per-game, shift(1) window)       │
│  Signal: works in the AGGREGATE — 10 RBG is 10 RBG                  │
│  Failure mode: cannot distinguish structural player type             │
│   → Wemby's 10 RBG ≠ Zubac's 10 RBG in implication                 │
├──────────────────────────────────────────────────────────────────────┤
│  LAYER 2 — QUALITATIVE   (F-100–F-299)                               │
│  "Who is this player structurally?"                                  │
│  Source: PAM v4 PRF archetypes + modifiers (seasonal cadence)        │
│  Signal: player TYPE — role, tendencies, structural profile          │
│  Failure mode: applied uniformly — does not account for context      │
│   → M-16 (clutch) applied equally to OT and 20-pt blowouts          │
├──────────────────────────────────────────────────────────────────────┤
│  LAYER 3 — AMPLIFICATION (F-300+)                                    │
│  "When does this player's qualitative profile matter most?"          │
│  Source: F-100+ × game context signals (per-game, from L1 features) │
│  Signal: CONDITIONAL qualitative effect — archetype × situation      │
│  Principle: qualitative factors are amplified in high-leverage,      │
│   high-variance, or emotionally-loaded game contexts                 │
│   → M-17 (High Variance) × long cold streak = strong signal         │
│   → M-16 (Clutch) × close game = strong signal                      │
│   → PRF-1 (Heliocentric) × clutch possession = dominant signal      │
└──────────────────────────────────────────────────────────────────────┘
```

**Why ERI v0 failed (and what it teaches):**
The pruned ERI features (F-036–F-038: eri_prev_hot, eri_prev_cold, eri_consec_cold_games) measured momentum from outcomes but applied the signal uniformly across ALL game contexts. The signal existed but was diluted — a hot player in a 20-point blowout carries the same eri_prev_hot flag as a hot player entering overtime. Layer 3 addresses this by making qualitative effects conditional on game context. ERI-style momentum signals re-emerge naturally as F-300+ amplification features once they are gated by situational context rather than applied globally.

**The sports betting implication:**
In the aggregate, the mathematics resolves. Over thousands of player-game observations, rolling box-score statistics predict outcomes with measurable Brier improvement. What makes sports betting uncertain is the "loose variable" layer — qualitative factors that cause specific games to deviate from the aggregate. These loose variables are not uniformly distributed: they cluster in high-stakes, emotionally loaded, momentum-driven situations. Layer 3 is the mechanism for mapping this effect rather than averaging it away.

**Implementation status:**
- Layer 1: ✅ IMPLEMENTED (F-001–F-031, FEATURE_VERSION 1.2.0)
- Layer 2: ✅ IMPLEMENTED (F-100–F-181, QS-2026-05-28-002, EXP-007 POSITIVE_SIGNAL)
- Layer 3: 🔲 SKELETON (F-300+, QualitativeAmplifier, OQ-021 defines study)

---

## 8. PRF Weighted One-Hot Encoding

The PAM v4's weighted hybrid notation (PRF-X [N%] / PRF-Y [M%]) must be encoded properly as model input. Integer encoding (`prf_primary = 9`) implies spurious ordinality — PRF-9 is not "more than" PRF-1. The correct encoding is **weighted one-hot**: 15 continuous features `prf_w01`…`prf_w15` where values sum to 1.0 and hybrid weights distribute fractionally.

| Player | prf_primary | prf_secondary | prf_hybrid_weight | prf_w09 | prf_w11 | all others |
|--------|-------------|---------------|-------------------|---------|---------|-----------|
| Gobert (PRF-9 pure) | 9 | 0 | — | 1.00 | 0.00 | 0 |
| Mobley (PRF-9 [60%] / PRF-11 [40%]) | 9 | 11 | 0.60 | 0.60 | 0.40 | 0 |
| Draymond (PRF-11 [50%] / PRF-3 [30%]) | 11 | 3 | 0.50 | 0.00 | 0.50 | prf_w03=0.30 |

This encoding is implemented in `QualitativeSignalStore.compute_prf_onehot()`. Feature IDs: `prf_w01`…`prf_w15` (F-103–F-117, replacing F-100/F-101/F-102 integer columns).

---

## 9. Current Qualitative Sources

| DS-ID | Name | Status | Coverage | Operationalized |
|-------|------|--------|----------|-----------------|
| DS-01 | Player_Attribute_Matrix v4 (PAM) | ✅ ACTIVE — EXP-007 POSITIVE_SIGNAL (+0.0017 Brier, +0.0159 ECE) | 50-player cohort, effective 2021-10-19+ | ✅ QS-2026-05-28-002 (backdated); one-hot encoding EXP-008 |
| DS-04 | (Reserved — future source) | — | — | — |
| DS-05 | (Reserved — future source) | — | — | — |

---

## 8. What Counts as a Qualitative Source

Examples of qualitative signal types anticipated for future registration:

| Category | Example | DS-ID candidate |
|----------|---------|----------------|
| Player archetype | PRF taxonomy (DS-01 PAM) | DS-01 |
| Coaching system fit | Offensive system alignment scoring | DS-04 |
| Historical narrative | "Clutch" performer flag (human-reviewed) | DS-05 |
| Matchup context | Defensive scheme compatibility rating | DS-06 |
| Injury history | Chronic soft-tissue injury flag | DS-07 |
| Contract/motivation | Contract year flag, extension signed | DS-08 |

Each source must pass through the registration process in Section 6 before use. No source bypasses temporal integrity review regardless of perceived predictive value.
