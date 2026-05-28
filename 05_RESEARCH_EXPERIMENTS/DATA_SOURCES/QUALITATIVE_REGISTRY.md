# Qualitative Signal Registry — Prediction Market Trading Bot

**Purpose:** Living catalog of all registered qualitative data sources. Every qualitative source must be registered here with full provenance, schema pointer, temporal bounds, and operationalization status before any experiment may use it.  
**Owner (role):** Research Lead (RL)  
**Status:** ACTIVE — 2026-05-28 (initial structure)  
**Last reviewed:** 2026-05-28  
**Next review:** Whenever a new qualitative source is registered or operationalized  
**Staleness triggers:** New source registered; source operationalized; QS snapshot added; coverage expanded  
**Upstream links:** 08_MODEL_RISK_GOVERNANCE/QUALITATIVE_SIGNALS.md  
**Downstream links:** 02_ARCHITECTURE_DESIGN/DATA_FLOWS_LINEAGE.md (F-100+ features), c2_feature_store/qualitative_store.py  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 9/10 — Registry structure canonical; DS-01 entry reflects actual state

---

## Registry

### DS-01 — Player Attribute Matrix v4 (PAM)

| Field | Value |
|-------|-------|
| DS-ID | DS-01 |
| Full name | Player_Attribute_Matrix_v4.docx — "Weighted Hybrid PRF System: A Dynamically Agnostic Framework for Player Archetype Classification" |
| Creator | Earl Ignacio (project owner / sole operator) |
| Creation date | 2026-05-21 |
| Registered snapshot | SNAP-2026-05-22-001 (DATA_SNAPSHOTS_INDEX.md) |
| Source document | `05_RESEARCH_EXPERIMENTS/DATA_SOURCES/DS-01_Player_Attribute_Matrix_v4.docx` |
| Schema definition | `qualitative_data/pam_v4/SCHEMA.md` |
| Classification template | `qualitative_data/pam_v4/PAM_CLASSIFICATION_TEMPLATE.csv` |
| Active QS snapshots | **QS-2026-05-28-001** (`qualitative_data/pam_v4/QS-2026-05-28-001_classifications.csv`) — all 50 cohort players classified 2026-05-28 |
| Feature IDs | F-100–F-149 (PRF archetype), F-150–F-199 (modifiers) — reserved in DATA_FLOWS_LINEAGE.md |
| **Operationalization status** | **🟡 PARTIAL** — QS-2026-05-28-001 populated and validated (50/50 players, PRFs 1–15, all modifiers binary). QualitativeSignalStore load/enrich stubs still require implementation before features reach experiments. |
| What must happen to activate | (1) ✅ Classify all 50 cohort players — done (QS-2026-05-28-001); (2) ✅ QS snapshot registered; (3) Implement load_ds01_snapshot() temporal join in qualitative_store.py; (4) Wire enrich_features() after compute_features_bulk() in experiment runner; (5) Run EXP measuring Brier Δ with vs without qualitative features |

**Coverage as of 2026-05-28:**
- Document defines framework for 15 PRF archetypes + 32 modifiers
- Applied examples in document cover 2026 NBA Conference Finals rosters (SAS, OKC, NYK, CLE)
- **QS-2026-05-28-001:** All 50 TARGET_PLAYER_IDS classified — effective_from 2025-10-22 (start of 2025-26 season)

**DS-01 PRF Taxonomy summary (15 archetypes):**

| ID | Archetype | Notes |
|----|-----------|-------|
| PRF-1 | — | See DS-01 document |
| PRF-2 | — | See DS-01 document |
| PRF-3 | — | See DS-01 document |
| PRF-4 | — | See DS-01 document |
| PRF-5 | — | See DS-01 document |
| PRF-6 | — | See DS-01 document |
| PRF-7 | — | See DS-01 document |
| PRF-8 | — | See DS-01 document |
| PRF-9 | — | See DS-01 document |
| PRF-10 | — | See DS-01 document |
| PRF-11 | — | See DS-01 document |
| PRF-12 | — | See DS-01 document |
| PRF-13 | — | See DS-01 document |
| PRF-14 | — | See DS-01 document |
| PRF-15 | — | See DS-01 document |

*Archetype names/descriptions are in DS-01 document. Populate above when operationalization begins.*

**DS-01 Modifier summary (32 modifiers):**

| ID | Modifier | Threshold Criteria | Binary (0/1) |
|----|----------|-------------------|--------------|
| M-01 | — | See DS-01 document | — |
| M-02 | — | See DS-01 document | — |
| ... | — | See DS-01 document | — |
| M-32 | — | See DS-01 document | — |

*Modifier names/thresholds are in DS-01 document. Populate SCHEMA.md when operationalization begins.*

---

### DS-04 — (Reserved for future qualitative source)

| Field | Value |
|-------|-------|
| DS-ID | DS-04 |
| Status | Reserved — not yet registered |
| Registration trigger | Operator decision; follows registration process in QUALITATIVE_SIGNALS.md §6 |

---

### DS-05 — (Reserved for future qualitative source)

| Field | Value |
|-------|-------|
| DS-ID | DS-05 |
| Status | Reserved — not yet registered |

---

## QS Snapshot Log

Qualitative snapshots follow the same immutability rules as game-log snapshots (SNAP-IDs). Format: `QS-YYYY-MM-DD-NNN`.

| QS-ID | DS-ID | Covers | Player count | effective_from | effective_until | Created | Status |
|-------|-------|--------|--------------|----------------|-----------------|---------|--------|
| QS-2026-05-28-001 | DS-01 | 50-player cohort (TARGET_PLAYER_IDS) | 50 | 2025-10-22 | NULL (active) | 2026-05-28 | ✅ Registered — awaiting QualitativeSignalStore implementation |

---

## Activation Checklist for a New Qualitative Source

Before any QS snapshot can be used in an experiment:

- [ ] DS-ID assigned and entry added to this registry
- [ ] Source document registered in DATA_SNAPSHOTS_INDEX.md (original file)
- [ ] Schema defined in `qualitative_data/<source>/SCHEMA.md`
- [ ] Feature IDs F-XXX reserved in DATA_FLOWS_LINEAGE.md
- [ ] Classification template created and populated
- [ ] QS snapshot CSV created and registered (QS-ID in this log)
- [ ] `effective_from` and `classification_basis` documented per QTI-02
- [ ] QualitativeSignalStore updated to load this source's schema
- [ ] At least one EXP run measuring Brier Δ vs baseline without qualitative features
- [ ] CHANGELOG entry for the first experiment using this source
