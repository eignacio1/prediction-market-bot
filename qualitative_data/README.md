# qualitative_data/ — Qualitative Signal Storage

**Purpose:** Holds versioned qualitative classification data for all registered qualitative sources (DS-01, DS-04+). This is the staging and active data area for qualitative features that enrich the raw box-score pipeline.

**Governance:** All files here are governed by `08_MODEL_RISK_GOVERNANCE/QUALITATIVE_SIGNALS.md`. Read that document before adding or modifying anything in this directory.

---

## Directory Structure

```
qualitative_data/
  README.md                        ← this file
  pam_v4/                          ← DS-01 Player Attribute Matrix v4
    SCHEMA.md                      ← column definitions for classification CSVs
    PAM_CLASSIFICATION_TEMPLATE.csv ← 50-player template; fill in to create a QS snapshot
    <QS-ID>_classifications.csv    ← registered snapshots (created when classifications done)
  future_sources/                  ← reserved for DS-04, DS-05, etc.
    .gitkeep
```

## Rules

1. **Never commit** `.env`, credentials, or personal data (none expected here, but noted for completeness).
2. **Template files are committed** — they are schema fixtures, not data.
3. **Populated classification CSVs are committed** once registered as QS snapshots — they are immutable data records, like code.
4. **Never modify a registered QS snapshot.** Create a new one (new QS-ID) to supersede.
5. **effective_from and classification_basis must be filled in** on every row before the CSV can be registered.

## How to create a new QS snapshot (DS-01 PAM)

1. Copy `pam_v4/PAM_CLASSIFICATION_TEMPLATE.csv` to `pam_v4/QS-YYYY-MM-DD-001_classifications.csv`
2. Fill in classifications for all players (see `pam_v4/SCHEMA.md` for column definitions)
3. Set `effective_from` and `effective_until` per QTI-02 rules in QUALITATIVE_SIGNALS.md
4. Register the QS-ID in `05_RESEARCH_EXPERIMENTS/DATA_SOURCES/QUALITATIVE_REGISTRY.md`
5. Register in `06_CODE_EXECUTION_REPRODUCIBILITY/DATA_SNAPSHOTS_INDEX.md`
6. Commit — the CSV is now an immutable registered snapshot
