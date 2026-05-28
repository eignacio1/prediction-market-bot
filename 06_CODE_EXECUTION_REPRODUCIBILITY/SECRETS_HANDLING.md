# Secrets Handling — Prediction Market Trading Bot

**Purpose:** Define how all credentials, API keys, and sensitive configuration are managed. Zero-tolerance policy for plaintext secrets.  
**Owner (role):** Architecture Owner (AO) + Risk and Compliance Owner (RCO)  
**Last reviewed:** 2026-05-22  
**Next review:** G5 Operational Gate; then on any new credential created  
**Staleness triggers:** New credential created; vault solution selected; live environment activated; credential rotation  
**Upstream links:** ENVIRONMENTS.md, 09_SECURITY_PRIVACY_COMPLIANCE/  
**Downstream links:** 10_INFRA_OPERATIONS/RUNBOOKS/  
**Decision references:** ADR-0001, NFR-05  
**Confidence:** 6/10 — Policy is clear; implementation TBD at G5 when vault solution selected

---

## Core Policy — NFR-05

**Zero hardcoded secrets.** No API key, password, token, or credential of any kind may be:
- Stored in a code file (`.py`, `.js`, `.yaml`, `.json`, etc.)
- Committed to version control
- Written to a log file
- Stored in a `.env` file checked into version control
- Passed as a command-line argument visible in shell history

**Violation of this policy is a CRITICAL security incident** — treat as P1 in RID_LOG.md.

---

## Secret Types and Required Handling

| Secret Type | Phase When Created | Required Storage | Prohibited Storage |
|-------------|-------------------|-----------------|-------------------|
| Venue API key | Phase 5+ (ACC-0002) | Vault (TBD at G5) | Plaintext file, env file in VCS, code |
| Venue API secret | Phase 8 (G6+) | Vault | Plaintext file, env file in VCS, code |
| Data source credentials | Phase 3+ (if needed) | Vault or OS keychain | Plaintext file, code |
| Database passwords | TBD | Vault | Plaintext file, code |

---

## Vault Solution (TBD at G5)

Vault tooling is not selected until G5. Until then:

- **No live credentials exist** (no venue API connection in Phases 0–5)
- If any test API keys are created during Phase 3 development: use OS keychain or environment variables set at runtime, NEVER persisted in files
- Vault evaluation criteria: local-first, no cloud dependency required for Phases 0–5, compatible with selected technology stack

**Candidate approaches (decision deferred to G5):**
- OS keychain (macOS Keychain / Linux Secret Service)
- HashiCorp Vault (self-hosted)
- python-keyring library
- AWS Secrets Manager (if cloud compute selected at G5)

---

## Environment Variable Protocol

Until a vault is in place, credentials must be injected at runtime only:

```bash
# CORRECT: Set at runtime, not persisted
export VENUE_API_KEY="..."  # Set in terminal session only; not in .bashrc or .zshrc

# INCORRECT: Never do these
echo "VENUE_API_KEY=..." > .env  # Creates a file that could be committed
export VENUE_API_KEY="..." >> ~/.bashrc  # Persists across sessions
```

---

## Pre-Commit Checks

The following checks should be enforced before any code commit:

- [ ] `bandit` scan: no hardcoded secrets detected
- [ ] `git-secrets` or equivalent: no credential patterns in diff
- [ ] Manual review: no API key or token patterns in new files

**These checks are enforced from Phase 3 onward** when code begins to be written.

---

## Credential Rotation Policy

| Credential | Rotation Frequency | Trigger for Immediate Rotation |
|------------|------------------|-------------------------------|
| Venue API key | [TBD at G5] | Suspected exposure; personnel change |
| Venue API secret | [TBD at G5] | Suspected exposure; paper→live promotion |
| Data source credentials | [TBD] | Suspected exposure |

**Any suspected credential exposure is a P1 incident** — escalate per COMMUNICATIONS_PLAN.md; rotate immediately; log in 09_SECURITY_PRIVACY_COMPLIANCE/AUDIT_EVIDENCE/.

---

## Audit Trail

Every credential creation, rotation, and deletion must be logged:

| Event | What to Log | Where |
|-------|------------|-------|
| Credential created | Type, date, authorized by | 09_SECURITY_PRIVACY_COMPLIANCE/AUDIT_EVIDENCE/ |
| Credential rotated | Type, date, reason | 09_SECURITY_PRIVACY_COMPLIANCE/AUDIT_EVIDENCE/ |
| Credential deleted | Type, date | 09_SECURITY_PRIVACY_COMPLIANCE/AUDIT_EVIDENCE/ |
| Suspected exposure | Type, date, scope, response | RID_LOG.md (P1) + AUDIT_EVIDENCE/ |
