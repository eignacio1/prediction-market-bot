# NFR-05 Evidence — Secrets Management (zero hardcoded secrets)

> **Record as of 2026-07-06** — a frozen, dated record, not a living document. It is not kept in step with the system; see `00_ADMIN/DOC_REGISTRY.toml`.


**Requirement:** Secrets scan returns zero findings; no credentials in logs.

**Populated:** 2026-07-06 (GG-075 remediation) — this closes a caveat both `ACCEPTANCE_CRITERIA.md` and `VALIDATION_PLAN.md` explicitly flagged as "not independently re-verified" during the 2026-07-02 pass. A fresh scan was run as part of this remediation, not merely asserted.

## Fresh scan results (run 2026-07-06)

**Bandit** (`.venv311/bin/python3 -m bandit -r src/ -q -c pyproject.toml`):
- 0 Medium/High-confidence hardcoded-credential findings.
- 1 `B105:hardcoded_password_string` hit at `src/prediction_market_bot/c3_forecasting/forecaster.py:93` — **confirmed false positive**: `DIR_PASS = "PASS"` is a bet-direction enum constant (YES/NO/PASS), not a credential.
- Remaining findings (26 Low + 1 unrelated High) are subprocess/hashlib hygiene items (`B603`/`B607` subprocess-without-shell, `B324` SHA1-for-non-security-hashing in `train_and_save_model.py`'s model-version hash) — not secrets, out of scope for NFR-05.

**detect-secrets** (`.venv311/bin/python3 -m detect_secrets scan src/ --all-files`):
- **0 files with detected secrets.**

## Status

**MET — independently re-verified 2026-07-06.** Zero hardcoded secrets found by either tool; the one bandit hit is a confirmed false positive on an enum literal. `.pre-commit-config.yaml` continues to enforce both scanners pre-commit (NFR-05 design).
