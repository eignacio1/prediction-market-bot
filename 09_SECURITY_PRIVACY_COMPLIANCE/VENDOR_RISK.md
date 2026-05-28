# Vendor Risk — Prediction Market Trading Bot

**Purpose:** Assess the risk profile of each external dependency and vendor. Identifies concentration risk, availability risk, and key failure modes from third-party dependencies.  
**Owner (role):** Risk and Compliance Owner (RCO)  
**Last reviewed:** 2026-05-26 (ADR-0003 accepted; Kalshi confirmed primary; Polymarket US noted secondary)  
**Next review:** G5 (pre-live final vendor audit); update when vendor changes  
**Staleness triggers:** Venue API changes; new dependency added; vendor incident; Polymarket US promotion decision  
**Upstream links:** DEPENDENCIES.md, POLICY_REQUIREMENTS.md (POL-001, POL-003), RESILIENCE_FAILURE_MODES.md  
**Downstream links:** RID_LOG.md (RID-003), RUNBOOKS/  
**Decision references:** ADR-0001, ADR-0003 (ACCEPTED 2026-05-23)  
**Confidence:** 8/10 — Primary venue confirmed; multi-venue architecture pending Phase 6

---

## Vendor Register

### VND-01 — Kalshi (Primary); Polymarket US (Secondary — Phase 6+)

| Field | Detail |
|-------|--------|
| Vendor ID | VND-01 |
| Vendor name | **Kalshi** (primary — confirmed ADR-0003 2026-05-23) |
| Regulatory status | CFTC-regulated Designated Contract Market (DCM); legal in all 50 US states |
| Market availability | NBA player prop markets confirmed available |
| Secondary vendor | Polymarket US (Phase 6+ secondary; CFTC-regulated event contracts, relaunched Dec 2025) |
| Service type | Market data feed, order execution API, outcome resolution data |
| Criticality | **CRITICAL** — single point of failure for live trading |
| Dependency | DS-02, DS-03, RES-04, RES-05 |
| Concentration risk | HIGH — Kalshi is sole primary venue; Polymarket US is Phase 6+ only |
| Substitutability | LOW at Phase 5+ (model calibrated to Kalshi mid-price/spread); MEDIUM at Phase 3 (pre-training; nba_api proxy used) |

**Risk factors:**
- Venue API downtime → paper/live trading halted (FM-04 in RESILIENCE_FAILURE_MODES.md)
- Venue regulatory action (e.g., trading suspension) → total trading halt
- API breaking change → execution pipeline broken until patched
- TOS violation by operator → API access revoked
- Venue bankruptcy/closure → complete strategy failure
- Kalshi NBA market availability changes → strategy scope reduction

**Mitigations:**
- Kill switch halts all activity on API error (NFR-03)
- Circuit breaker pattern in C5 (FR-06) rejects orders on connectivity failure
- API client versioned and pinned; breaking changes detected at test time
- VENUE_ID parameterized in all C5 calls — no hardcoding; venue change requires config only
- Polymarket US designated as Phase 6+ fallback pending separate ADR
- Venue compliance documentation reviewed at G3 (ADR-0003 accepted)

**Open items:** Multi-venue CA-legal enumeration (full OQ-006 scope) deferred to Phase 6. Any additional venue requires new ADR (Class A change).

---

### VND-02 — Python Package Ecosystem

| Field | Detail |
|-------|--------|
| Vendor ID | VND-02 |
| Vendor name | PyPI ecosystem (scikit-learn, pandas, numpy, XGBoost, scipy, etc.) |
| Service type | Core computation, ML, data processing |
| Criticality | HIGH — model cannot run without these dependencies |
| Concentration risk | LOW — multiple independent maintainers; large ecosystems |
| Substitutability | MEDIUM — scikit-learn substitutes for XGBoost in extremis |

**Risk factors:**
- Supply chain compromise (malicious package update) — low probability, HIGH impact
- Breaking API change in minor version — controlled by pinning
- Package abandonment — low risk for mature packages (pandas, scikit-learn)

**Mitigations:**
- All dependencies pinned to exact versions (DEPENDENCIES.md; C-009)
- bandit scans all imports at pre-commit
- requirements-lock.txt maintained; changes require explicit review
- No auto-updates in production

---

### VND-03 — Secrets Vault (TBD)

| Field | Detail |
|-------|--------|
| Vendor ID | VND-03 |
| Vendor name | TBD — pending G5 (OQ-009) |
| Candidates | HashiCorp Vault, AWS Secrets Manager, macOS Keychain, python-dotenv (Phase 1-4 only) |
| Service type | Credential storage and retrieval |
| Criticality | HIGH at Phase 5+ — all live credentials depend on it |
| Concentration risk | HIGH — single vault; if unavailable, cannot access credentials |
| Substitutability | MEDIUM — env-var fallback with manual credential injection |

**Risk factors:**
- Vault unavailability → cannot start live pipeline
- Vault compromise → credential exposure (TH-02)
- Vault API change → pipeline startup broken

**Mitigations:**
- Vault selection at G5 with availability SLA evaluation
- Credential rotation policy (SECRETS_HANDLING.md)
- Emergency procedure: manual env-var injection with immediate post-incident vault repair

**Phase 1-4 note:** python-dotenv with .env file (gitignored) is acceptable for research-only phases. Not acceptable at Phase 5+.

---

### VND-04 — Version Control System

| Field | Detail |
|-------|--------|
| Vendor ID | VND-04 |
| Vendor name | Git (local) + remote host TBD (OQ-008) |
| Service type | Code versioning, artifact history, audit trail |
| Criticality | HIGH — code and governance artifact history |
| Concentration risk | LOW — local git always available; remote is backup |
| Substitutability | HIGH — git is standard; any remote host acceptable |

**Risk factors:**
- Remote host unavailability → no push/pull (local work continues)
- Accidental force-push of secrets → TH-02 risk; irreversible if public

**Mitigations:**
- .gitignore covers all secret file patterns
- Pre-commit hook prevents secrets from being committed
- Private repository only (no public exposure of model or credentials)
- Local git always has full history

---

## Vendor Risk Summary

| Vendor | Criticality | Concentration Risk | Phase First Active | Primary Risk |
|--------|-------------|-------------------|-------------------|--------------|
| VND-01 Kalshi (primary) | CRITICAL | HIGH | Phase 5 | Downtime, regulatory action, NBA market changes |
| VND-02 Python packages | HIGH | LOW | Phase 1 | Supply chain, breaking change |
| VND-03 Secrets Vault | HIGH | HIGH | Phase 5 | Unavailability, compromise |
| VND-04 VCS | HIGH | LOW | Phase 0 | Force-push secrets |

---

## Vendor Risk Acceptance

Before G5 (paper trading), RCO must explicitly accept or mitigate:

- [x] VND-01: Venue selected (Kalshi primary — ADR-0003 ACCEPTED 2026-05-23); TOS/regulatory confirmed (CFTC-DCM, all 50 states); API reliability SLA review pending G5
- [ ] VND-02: Dependency lock confirmed; bandit scan passing
- [ ] VND-03: Vault solution selected; availability tested; rotation policy active
- [ ] VND-04: Private repository confirmed; pre-commit hook active

---

## Contingency: If Venue (VND-01) Becomes Unavailable

| Scenario | Response | Owner |
|----------|----------|-------|
| Planned maintenance | Pause pipeline; resume after maintenance window | IO |
| Unplanned API outage | Kill switch auto-activates; monitor for recovery; log to RID_LOG.md | MO |
| Extended outage (>7 days) | DS decision: suspend strategy, evaluate alternative venue | DS |
| Venue closure / regulatory action | Full halt; capital recovered to operator; project re-scoped with ADR | DS + RCO |

**No automated failover to alternative venue is planned.** Any venue change requires ADR (Class A change — new venue selection).
