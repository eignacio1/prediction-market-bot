# Notebooks Policy — Prediction Market Trading Bot

**Purpose:** Define how Jupyter notebooks (or equivalent) may be used in this project. Notebooks are a common source of reproducibility failure and must be governed explicitly.  
**Owner (role):** Research Lead (RL)  
**Last reviewed:** 2026-05-22  
**Next review:** G2 Architecture Gate  
**Staleness triggers:** Notebook framework decision; any notebook committed to version control  
**Decision references:** ADR-0001, NFR-01  
**Confidence:** 7/10 — Policy is clear; specific tooling TBD at G2

---

## Core Rule — Notebooks Are for Exploration Only

Notebooks may be used for:
- Initial data exploration and visualization
- Hypothesis formation (before a formal experiment record is created)
- Sanity checks on intermediate outputs

Notebooks may NOT be used for:
- Final experiment results that will be cited in an experiment record
- Any pipeline step that runs in production (PIPE-01 through PIPE-04)
- Model training or evaluation that produces results for G4 evidence

**All results cited in experiment records must be reproducible from a committed script, not a notebook.**

---

## Notebook Lifecycle

```
Exploration notebook (throw-away)
         │
         ▼ [if useful findings]
Experiment record created (EXPERIMENT_LOG/EXP-NNN.md)
         │
         ▼
Findings extracted to a committed Python script
         │
         ▼
Script runs cleanly from RUN_INSTRUCTIONS.md
         │
         ▼
Notebook archived or deleted (not committed as canonical artifact)
```

---

## Notebook Naming and Storage

- Notebooks stored in: `05_RESEARCH_EXPERIMENTS/DATA_EXPLORATION_NOTES/`
- Naming: `YYYY-MM-DD_short-description.ipynb`
- Never committed with cell outputs — output cells must be cleared before commit (if committed at all)
- Kernels must be restarted and run top-to-bottom before any finding is extracted

---

## Prohibited Notebook Patterns

| Pattern | Risk | Alternative |
|---------|------|-------------|
| Using variables set in out-of-order cell execution | Hidden state dependency; results not reproducible | Restart kernel and run top-to-bottom |
| Loading data without a registered Snapshot ID | Violates snapshot discipline | Register snapshot first; reference ID in notebook |
| Committing notebooks with output cells | Output is stale; file size bloat | Clear outputs before commit |
| Citing notebook results in experiment record without script equivalent | Not reproducible | Extract to script first |
| Running notebooks in paper or live environment | Operational risk | Only scripts in PIPE-01 through PIPE-04 |
