# Data Sources — 05_RESEARCH_EXPERIMENTS/DATA_SOURCES/

**Purpose:** Staging area for raw research data inputs. Files here have registered snapshots but have NOT yet been ingested, cleaned, or validated for use in experiments. This folder is RESEARCH input only — no experiment record may reference these files directly; experiments must reference Snapshot IDs from DATA_SNAPSHOTS_INDEX.md.  
**Owner (role):** Research Lead (RL)  
**Last reviewed:** 2026-05-22  
**Next review:** Before each Phase 3 experiment; when new data sources are added  
**Staleness triggers:** New data source staged; file moved to active ingestion pipeline  
**Upstream links:** 08_MODEL_RISK_GOVERNANCE/DATA_PROVENANCE.md, 06_CODE_EXECUTION_REPRODUCIBILITY/DATA_SNAPSHOTS_INDEX.md  
**Downstream links:** 05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/ (via Snapshot ID only)  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 9/10

---

## Governance Rules for This Directory

1. **Files here are IMMUTABLE once staged.** They are registered snapshots. No modification after registration.
2. **No experiment may read files here directly.** All experiment access is through the ingestion pipeline (C1 Signal Ingestion, Phase 3+), which creates a validated copy and registers the Snapshot ID.
3. **Each file must have a corresponding SNAP-ID** in DATA_SNAPSHOTS_INDEX.md before any experiment is run.
4. **DS-01 is RESEARCH INPUT ONLY** — it informs feature design but is NOT a raw statistics file. Operationalization into ML features requires a separate feature engineering step.

---

## Registered Files

| File | Snapshot ID | Source | Staged Date | Notes |
|------|-------------|--------|------------|-------|
| DS-01_Player_Attribute_Matrix_v4.docx | SNAP-2026-05-22-001 | DS-01 (Earl Ignacio, 2026-05-21) | 2026-05-22 | Framework document; NBA basketball; provenance in DATA_PROVENANCE.md |

---

## Files Pending Registration

*None at this time.*

---

## Note on DS-01 Format

`DS-01_Player_Attribute_Matrix_v4.docx` is a **framework document**, not a tabular dataset. It defines:
- 15 PRF (Player Role Framework) archetypes with activation constraints
- 32 modifiers with explicit threshold criteria
- Weighted hybrid PRF notation methodology
- Applied classifications for 2026 NBA Conference Finals rosters

To use DS-01 in experiments, the framework classifications must be **operationalized into numeric features** (e.g., PRF category as one-hot or integer; modifier flags as binary; hybrid weights as continuous). This operationalization is a Phase 3 task.
