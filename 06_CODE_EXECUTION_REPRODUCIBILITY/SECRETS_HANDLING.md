# Secrets Handling — Prediction Market Trading Bot

**Purpose:** Define how all credentials, API keys, and sensitive configuration are managed. Zero-tolerance policy for plaintext secrets.  
**Owner (role):** Architecture Owner (AO) + Risk and Compliance Owner (RCO)  
**Last reviewed:** 2026-07-21 (T-352, Window B — rotation cadence defined; Secret Types/Vault sections realigned to the already-decided live architecture per THREAT_MODEL.md TH-02/GG-093, which found this file's "Vault TBD, no live credentials exist" language stale ~6 weeks after G5 closed and the real credential went live under ADR-0008)  
**Next review:** G6 gate, or on any new credential type created  
**Staleness triggers:** New credential created; live environment activated; credential rotation; formal vault adoption (if ever revisited — currently not planned, see Vault Solution section below)  
**Upstream links:** ENVIRONMENTS.md, 09_SECURITY_PRIVACY_COMPLIANCE/  
**Downstream links:** 10_INFRA_OPERATIONS/RUNBOOKS/, THREAT_MODEL.md TH-02  
**Decision references:** ADR-0001, ADR-0008, NFR-05  
**Confidence:** 7/10 — Policy is clear; rotation cadence now defined (T-352); actual storage mechanism now documented and matches live reality (`.env` + `python-dotenv` + systemd `EnvironmentFile=`, not a vault — OQ-009/ACC-0004 remain formally PENDING/unresolved as a vault *decision*, but the project has operated on env-var storage since ADR-0008 without one, and TH-02's 2026-07-12 review accepted this as the current real-world control, not a gap awaiting closure)

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
| Venue API key | Phase 5+ (ACC-0002) — **live since ADR-0008, 2026-05-31** | `.env` file (untracked, gitignored) loaded via systemd `EnvironmentFile=` on the VPS; env vars at runtime locally — see below | Plaintext file committed to VCS, env file in VCS, code |
| Venue API secret | Phase 8 (G6+) — **paper-trading equivalent live since ADR-0008** | Same as above | Plaintext file committed to VCS, env file in VCS, code |
| Data source credentials | Phase 3+ (if needed) | OS keychain, or `.env`/env var if the source has no keychain-compatible client | Plaintext file, code |
| Database passwords | TBD | `.env`/env var, consistent with the above | Plaintext file, code |

---

## Vault Solution — decided-in-practice, not formally adopted (OQ-009/ACC-0004 remain PENDING)

**No dedicated secrets-vault product (HashiCorp Vault, AWS Secrets Manager, OS keychain) was ever formally selected at G5** — OQ-009 and ACC-0004 remain open/PENDING in `OPEN_QUESTIONS.md`/`ACCESS_REQUESTS.md`. In practice, the live system has operated since ADR-0008 (2026-05-31) on a simpler control: the Kalshi RSA credential lives in `/opt/prediction-market-bot/.env` on the VPS (gitignored, never committed), loaded into the process environment by `python-dotenv` locally and by systemd's `EnvironmentFile=` directive in `t4-mlb.service` in production — never hardcoded, never logged, never passed as a CLI arg. This satisfies the letter of NFR-05 ("Zero hardcoded secrets... Vault/env-var protocol only" — env-var is an explicitly named acceptable path, not vault-exclusive) and was reviewed and accepted as the current real-world control by `THREAT_MODEL.md` TH-02 (GG-093/T-347, 2026-07-12), which rewrote the threat model to describe this mechanism accurately rather than the stale "Vault TBD, no live credentials exist" framing this file carried until this review.

**This is a real, still-open gap relative to the original G5 plan** — a bare `.env` file has no encryption-at-rest, no access audit trail, and no secret-scoped revocation independent of rotating the underlying credential — but it is not a *silent* gap: it has been surfaced, reasoned about, and knowingly accepted as adequate at current paper-trading scale and single-operator threat model (TH-02). Formal vault adoption remains a candidate future hardening step, not a live blocker; revisit at G6 or if the threat model changes (e.g., multi-operator access, live capital).

**Candidate approaches, if formally revisited:**
- OS keychain (macOS Keychain / Linux Secret Service)
- HashiCorp Vault (self-hosted)
- python-keyring library
- AWS Secrets Manager (if cloud compute is ever adopted)

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

**Defined 2026-07-21 (T-352), closing the `[TBD at G5]` gap flagged by GG-093 and left open since G5 closed 2026-05-22 — the live Kalshi RSA credential (ADR-0008, 2026-05-31) had run 6+ weeks under no defined cadence at all before this update.**

| Credential | Rotation Frequency | Trigger for Immediate Rotation |
|------------|------------------|-------------------------------|
| Venue API key | 90 days (calendar) | Suspected exposure; personnel change; paper→live promotion |
| Venue API secret | 90 days (calendar), same rotation event as the key — Kalshi issues key+secret as a pair | Suspected exposure; personnel change; paper→live promotion |
| Data source credentials | 90 days if the source issues long-lived tokens; N/A for sources with no persistent credential | Suspected exposure |

**Rationale for 90 days:** no regulatory or venue-mandated cadence applies at paper-trading scale (Kalshi does not enforce key expiry), so this is a self-imposed hygiene interval, not a compliance-driven one — chosen as a conventional secret-rotation default (NIST SP 800-63B softened its own periodic-rotation mandate but 90 days remains a common baseline for keys with no compromise-detection telemetry backing them) balanced against the operational cost of a manual cutover (T-351's 2026-07-13 rotation required a coordinated local + VPS + `t4-mlb.service` restart + live-auth reverification — a real, non-zero-cost, non-automatable operation at this stage, with no automated rotation tooling built and none planned before a vault solution is selected). Revisit this cadence once the vault decision (below) lands — an automated vault-backed rotation could safely shorten this interval; until then, shortening it further only adds manual-cutover risk (each rotation is itself an opportunity to fat-finger the live credential) without a corresponding security gain over the actual live threat (TH-02: physical/credential compromise, not high-frequency online brute-force).

**Next scheduled rotation:** the T-351 (2026-07-13) rotation is the clock's start; +90 days = **2026-10-11**. Track via a `04_EXECUTION/TODO_NEXT.md` entry or calendar reminder — this document does not itself enforce the cadence, it only defines it (no automated rotation-due alerting exists yet; that would require the deferred vault/monitoring tooling below).

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
