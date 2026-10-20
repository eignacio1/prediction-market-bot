# 06 Code, Execution & Reproducibility

**Last verified:** 2026-10-20 against `00_ADMIN/DOC_REGISTRY.toml`, `02_ARCHITECTURE_DESIGN/RUNTIME_MAP.md`, `deploy/`. **Owner (role):** Infrastructure Operator.

| Need | Canonical source |
|---|---|
| What runs on the box (crons, services, workflows) | `02_ARCHITECTURE_DESIGN/RUNTIME_REGISTRY.toml` and generated `RUNTIME_MAP.md` |
| How to deploy | `deploy/DEPLOYMENT_GUIDE.md`, `deploy/*.service` |
| Secrets rules (names only, never values) | `SECRETS_HANDLING.md`, `09_SECURITY_PRIVACY_COMPLIANCE/ACCESS_CONTROL_MATRIX.md` |
| Dependency pins | `DEPENDENCY_LOCKS/` |
| Superseded pipeline list | `ARCHIVE/2026/superseded/PIPELINES_JOBS_2026-05-29.md` (`PIPELINES_JOBS.md` is a pointer stub) |

`ENVIRONMENTS.md`, `RUN_INSTRUCTIONS.md`, `DATA_SNAPSHOTS_INDEX.md`, `ARTIFACT_REGISTRY.md` predate the current system. Each carries a status banner; where it disagrees with the sources above, the sources win. Staleness is tracked in `00_ADMIN/DOC_REGISTRY.toml` (`python3 scripts/doc_registry.py check`).
