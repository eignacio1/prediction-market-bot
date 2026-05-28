# Dependency Locks

**Purpose:** Pinned dependency files for all environments. Lock files are the authoritative record of what runs in each environment. Any experiment record must cite the lock file version or hash used.  
**Owner (role):** Architecture Owner (AO)  
**Last reviewed:** 2026-05-22  
**Next review:** Phase 3 entry (re-lock with confirmed stack); on any dependency change  
**Staleness triggers:** New dependency added; version bump; security vulnerability patch  
**Upstream links:** 02_ARCHITECTURE_DESIGN/DEPENDENCIES.md  
**Downstream links:** 06_CODE_EXECUTION_REPRODUCIBILITY/RUN_INSTRUCTIONS.md, 05_RESEARCH_EXPERIMENTS/EXPERIMENT_LOG/  
**Decision references:** ADR-0001  
**Confidence:** 5/10 — Preliminary lock; stack finalized at G2; versions will be re-pinned at Phase 3

---

## Files

| File | Environment | Purpose |
|------|------------|---------|
| requirements-base.txt | All (ENV-01/02/03) | Core runtime dependencies |
| requirements-dev.txt | ENV-01 only | Development and test tooling |

## Usage

```bash
# Set up ENV-01 research environment
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r 06_CODE_EXECUTION_REPRODUCIBILITY/DEPENDENCY_LOCKS/requirements-dev.txt

# Install pre-commit hooks
pre-commit install
pre-commit run --all-files  # verify on first install
```

## Lock Policy

Per `02_ARCHITECTURE_DESIGN/DEPENDENCIES.md`:
- All versions pinned exactly (`==`)
- No range specifiers (`>=`, `~=`)
- Experiment records must cite lock file version
- Changes require CHANGELOG entry
- Breaking changes require ADR

## Re-lock Procedure

When updating a dependency:

1. Update the version in the lock file
2. Run `pip install -r requirements-dev.txt` to verify compatibility
3. Run full test suite (`pytest tests/`)
4. Add entry to `00_ADMIN/CHANGELOG.md`
5. Update "Last reviewed" date in this file
