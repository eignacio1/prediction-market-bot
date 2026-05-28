# Qualitative Signal Governance — Prediction Market Trading Bot

**Purpose:** Define what qualitative signals are, how they enter the pipeline, how they are versioned, and what temporal integrity rules govern their use in model training and inference.  
**Owner (role):** Research Lead (RL) + Architecture Owner (AO)  
**Status:** CANONICAL — 2026-05-28 (initial structure; T-058 context)  
**Last reviewed:** 2026-05-28  
**Next review:** Before first qualitative feature experiment (EXP-006+); after any new qualitative source is registered  
**Staleness triggers:** New qualitative source registered; operationalization of an existing source completed; temporal integrity protocol revised  
**Upstream links:** DATA_FLOWS_LINEAGE.md, INTERFACES_CONTRACTS.md (IF-DS-Q-C2)  
**Downstream links:** 05_RESEARCH_EXPERIMENTS/DATA_SOURCES/QUALITATIVE_REGISTRY.md, c2_feature_store/qualitative_store.py  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 9/10 — Framework defined; operationalization of individual sources is pending

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

## 7. Current Qualitative Sources

| DS-ID | Name | Status | Coverage | Operationalized |
|-------|------|--------|----------|-----------------|
| DS-01 | Player_Attribute_Matrix v4 (PAM) | Registered (SNAP-2026-05-22-001); not operationalized | 2026 Conference Finals rosters | ❌ Pending full 50-player classification + schema implementation |
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
