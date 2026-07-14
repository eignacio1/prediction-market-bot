# Threat Model — Prediction Market Trading Bot

**Purpose:** Identify threats to system integrity, data validity, capital safety, and governance. Maps threats to mitigations and residual risk. Required for G2 gate.  
**Owner (role):** Architecture Owner (AO) + Risk and Compliance Owner (RCO)  
**Status:** **CANONICAL — G2 Architecture Gate 2026-05-22** — Changes require ADR or formal Change Class A/B record  
**Last reviewed:** 2026-05-22 (G2 review; C4/C5 corrected; promoted DRAFT → CANONICAL; RCO = AO as sole operator)  
**Next review:** On staleness trigger only; expanded at G5 (pre-live-inference) and G6 (pre-live-capital)  
**Staleness triggers:** New component added; new external integration; security incident; venue API confirmed; live capital authorized  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, SYSTEM_CONTEXT.md, RESILIENCE_FAILURE_MODES.md  
**Downstream links:** 09_SECURITY_PRIVACY_COMPLIANCE/, 10_INFRA_OPERATIONS/RUNBOOKS/  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 6/10 — Threats identified for current scope; live-capital threat surface expands significantly at G5–G6
**Decisions logged:** true — TH-01–TH-09 threat prioritization and STRIDE scope decisions captured at G2 gate (APR-0004)

---

## Threat Modeling Scope

This model covers Phases 0–5 (research and operational readiness). Live capital threats are flagged and will be expanded at G5. Threats are categorized using a simplified STRIDE framework applied to this system's specific risk profile.

**⚠️ RESOLVED 2026-07-13 (GG-093, T-347) — the gap flagged 2026-07-06 (GG-074) is closed.** TH-02 below has been rewritten against the real, live ADR-0008 credential architecture (RSA-PSS/SHA-256 request signing, `kalshi_client.py`, `/root/.ssh/kalshi_bot.pem` on the VPS), the "Threats Out of Scope" table's two false rows are corrected, and a new **"Live Credential Attack Surface"** section below adds the key-compromise/rotation-policy/blast-radius analysis this document's own G5 trigger called for and that had never been done. This re-expansion surfaced genuine, previously undocumented findings — an unencrypted (no-passphrase) private key at rest, a shared CI/CD secret (`VPS_SSH_KEY`) that is transitively as powerful as the Kalshi credential itself, an overdue rotation-policy placeholder, and a contradiction between `deploy/env.template`'s "read-only" framing and ADR-0008's real write-capable behavior — each documented below rather than assumed away. See GG-093 in `GOVERNANCE_GAP_LOG.md` and `DECISION_LOG.md` (2026-07-13) for the full resolution record.

**Primary adversarial concern:** Most threats in this system are **accidental** (configuration errors, data contamination, process failures) rather than external adversarial. External attack surface is minimal until live capital is deployed.

---

## TH-01 — Data Contamination / Look-Ahead Bias (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Future data leaks into training features; model appears performant but has zero live edge |
| Category | Integrity (Accidental) |
| Attack vector | Internal (data pipeline logic error) |
| Affected components | C1, C2 |
| Likelihood | HIGH — This class of error is common and often silent |
| Impact | CRITICAL — Silently invalidates all backtesting results |
| Controls | (1) TI-01 through TI-04 temporal integrity rules in DATA_FLOWS_LINEAGE.md. (2) temporal_cutoff field mandatory in IF-C2-C3. (3) Outcome data ingested on separate path (DS-03 ≠ feature store). (4) Automated temporal overlap check in backtesting framework. |
| Residual risk | MEDIUM — Automated check catches most cases; novel feature types require manual review |
| Related FM | FM-02 |
| Revisit trigger | New feature added to lineage register |

---

## TH-02 — Credential Exposure (Accidental primary, adversarial secondary)

| Attribute | Detail |
|-----------|--------|
| Threat | Compromise or leakage of the live Kalshi RSA credential pair (`VENUE_API_KEY` key ID + the `VENUE_PRIVATE_KEY_PATH` private key), or of the `VPS_SSH_KEY` GitHub Actions secret that grants root access to the VPS host storing that key — either path enables unauthorized order submission on the live Kalshi account or corruption of the audit/evidence trail the G6 gate depends on |
| Category | Information Disclosure + Elevation of Privilege |
| Attack vector | Internal (developer/operator error — e.g. a `.pem` accidentally committed, a permissions misconfiguration) or External (VPS compromise via any vector — leaked SSH key, unpatched service, supply-chain issue in a dependency) — both converge on the same unencrypted key file once the VPS itself is reached |
| Affected components | C5 (`kalshi_client.py` signing), the VPS host (runs as `root`), CI/CD (`VPS_SSH_KEY`, shared across `deploy.yml`/`post_game_resolve.yml`/`tss_daily_sync.yml`) |
| Likelihood | LOW-MEDIUM — real RSA signing key has been live since 2026-05-31 (ADR-0008). It is stored as an **unencrypted PEM with no passphrase** — `kalshi_client.py`'s `_load_private_key()` calls `load_pem_private_key(pem_bytes, password=None)` — at `/root/.ssh/kalshi_bot.pem` on a single VPS running as `root`. `.gitignore`'s `*.pem` pattern and NFR-05 prevent VCS-path leakage but do nothing to protect against VPS-level compromise, and no vault product was ever implemented (see Live Credential Attack Surface section below) |
| Impact | MEDIUM today — ADR-0008's own governance constraint restricts the live key to a **demo** Kalshi account until G6 clears, so no real capital is directly at risk from this specific credential today. But compromise still corrupts the paper-trading evidence trail the G6 gate itself is built on (fabricated fills, tampered P&L), and the same unencrypted-PEM-on-root-owned-VPS pattern is a CRITICAL exposure if carried forward unchanged into a live-capital key post-G6 |
| Controls | (1) NFR-05 zero-hardcoded-secrets policy + `.gitignore *.pem` prevents VCS exposure. (2) ADR-0008's governance constraint restricts the live key to a demo account pre-G6. (3) RSA-PSS/SHA-256 request signing (`kalshi_client.py`'s `_sign_request()`, over `timestamp_ms + METHOD + path`) means a network-level MITM cannot forge orders without the private key file itself. (4) VPS deploy access is gated behind one GitHub Actions secret (`VPS_SSH_KEY`) rather than broadly distributed credentials. |
| Residual risk | MEDIUM — no vault, no passphrase, no rotation ever performed on `kalshi_bot.pem` since its creation (see below); a VPS compromise via *any* vector, not just a Kalshi-credential-specific one, yields full signing capability with no further barrier once the file is read |
| Related FM | FM-07 (adjacent — audit-log/evidence-trail integrity if the key is misused); no dedicated failure mode for credential compromise exists yet in `RESILIENCE_FAILURE_MODES.md` — recommend an FM-09 in a future revision of that document |
| Revisit trigger | G6 authorization (live-capital key); any VPS access-control or hosting change; any credential rotation event; any change to `kalshi_client.py`'s signing/key-loading code |

---

## Live Credential Attack Surface — Key Compromise, Rotation Policy, Blast Radius (added 2026-07-13, T-347/GG-093)

This section is the substantive re-expansion GG-093 called for: the analysis that was never done when ADR-0008 went live on 2026-05-31. It is grounded directly in `ADR-0008_kalshi-demo-order-execution.md`, `src/prediction_market_bot/c5_execution/kalshi_client.py`, `deploy/t4-mlb.service`, `.github/workflows/deploy.yml` (and its two sibling workflows), and `06_CODE_EXECUTION_REPRODUCIBILITY/SECRETS_HANDLING.md`.

**Credential inventory — what exists, where it lives, what it grants:**

| Credential | Location | Grants |
|---|---|---|
| `VENUE_API_KEY` (Kalshi key ID) | `/opt/prediction-market-bot/.env` on VPS (`deploy/t4-mlb.service:10`, `EnvironmentFile=`) | Identifies the key to Kalshi; alone (without the private key) cannot sign requests — RSA-PSS requires the private key material, so a `.env`-only leak is read-only-equivalent in practice |
| `VENUE_PRIVATE_KEY_PATH` → `kalshi_bot.pem` | `/root/.ssh/kalshi_bot.pem` on VPS (confirmed via `TODO_NEXT.md`, `KNOWN_ISSUES.md` KI-020, `SESSION_HANDOFF_20260531_2200.md`); locally at `~/.ssh/kalshi_bot.pem` on the operator's machine | Full order-submission signing capability (`submit_order`/`get_balance`) on the live Kalshi demo account — this is the credential that actually matters |
| `VPS_SSH_KEY` (GitHub Actions secret) | GitHub repo secrets; used by `deploy.yml`, `post_game_resolve.yml`, `tss_daily_sync.yml` — one secret shared across all three | Root SSH access to the VPS, i.e. transitively: read access to `kalshi_bot.pem` and `.env`, plus the ability to restart/modify the `t4-mlb`/`pmbot-web-dashboard` systemd services and tamper with the audit logs those services write (cross-ref FM-07/TH-09) |

**Blast-radius walkthrough (three compromise scenarios, not previously analyzed anywhere in this document set):**

1. **`kalshi_bot.pem` exfiltrated directly** (e.g. VPS root access via any other vector, a misconfigured backup, or the file's own permissions drifting off `chmod 600`) → immediate, unassisted order-signing capability on the demo account. No passphrase gate exists. If this same file (or a successor key generated the same way) is later repointed at a live-capital account without a hardening pass, this is a direct, silent path to unauthorized real-money trades — the architecture does not currently distinguish "demo key handling" from "live key handling" in any way beyond ADR-0008's governance *policy* (which account the key is provisioned against), not a technical control.
2. **`VPS_SSH_KEY` leaked** (compromised GitHub Actions runner, a maintainer's leaked personal credentials, a malicious PR that exfiltrates secrets during CI) → root shell on the VPS → direct read of `kalshi_bot.pem` and `.env`, i.e. this scenario collapses into scenario 1, plus the added capability to tamper with or halt the `t4-mlb`/`pmbot-web-dashboard` services and the audit logs they write. Because this one secret is shared identically across three separate workflows, a vulnerability in *any one* of the three workflow definitions (e.g. an untrusted-input injection in a future change to `tss_daily_sync.yml`) exposes all three, including the deploy path. **This makes `VPS_SSH_KEY` transitively as powerful as the Kalshi credential itself, despite GitHub Actions never touching Kalshi secrets directly** — a fact not previously stated anywhere in this project's governance documents.
3. **`.env` leaked in isolation** (without `kalshi_bot.pem`) → attacker has the key ID but not the signing material; RSA-PSS signing cannot be forged without the private key. Lower severity alone, but this exposure combined with scenario 1 or 2 is full compromise, and the two files sit on the same host with no compartmentalization between them.

**Rotation policy — status: overdue, not prospective.** `SECRETS_HANDLING.md` still marks venue-credential rotation as `[TBD at G5]` (its rotation-policy table, "Venue API key" and "Venue API secret" rows). **G5 formally closed 2026-05-22 — nine days *before* ADR-0008 put the real credential live on 2026-05-31.** This placeholder is not a future obligation; it describes a decision that should already have been made before the credential it governs went live, and as of this writing no rotation has ever been performed on `kalshi_bot.pem` since its creation (no rotation event appears in `DECISION_LOG.md` or `TODO_NEXT.md`). This project should not assert a rotation policy exists — it does not, beyond the placeholder text. Whether Kalshi's API supports dual-active-key rotation (issuing a second key, cutting over, revoking the first with zero downttime) is unverified against Kalshi's actual documentation as part of this analysis — flagged as an open question, not asserted either way.

**No vault — the design promise vs. the real mechanism.** `SECRETS_HANDLING.md`'s own storage-requirements table lists "Vault (TBD at G5)" as the required mechanism for venue credentials once Phase 5+ is reached. G5 closed without a vault ever being selected or implemented; the real, live mechanism is an unencrypted PEM file on a single VPS's root-owned filesystem, protected only by OS file permissions and whatever access control gates VPS root (currently: possession of `VPS_SSH_KEY`, or physical/console access to the droplet). This is a materially weaker control than the document's own design table promises, and `SECRETS_HANDLING.md`'s line 43 claim ("No live credentials exist") is independently false and has been since 2026-05-31 — that document has its own staleness gap, registered separately as **GG-116** rather than fixed here, since GG-093's scope is this threat model, not a rewrite of `SECRETS_HANDLING.md` itself.

**Unresolved contradiction — "read-only" vs. write-capable.** `deploy/env.template`'s comment on the `VENUE_API_KEY` line reads "Market data only — no order submission credentials in ENV-02," describing the key as provisioned read-only (ACC-0002, 2026-05-28). ADR-0008 (three days later, 2026-05-31) pairs that same key ID with a private key to perform real order submission. Local repo evidence cannot resolve whether (a) the key's Kalshi-side ACL was upgraded from read-only to write-capable when ADR-0008 shipped and the template comment was simply never updated, or (b) Kalshi's permission model does not actually gate order-submission capability by the API key ID the way the original template comment assumed (i.e. any key paired with a valid RSA signature can submit orders regardless of an initial "read-only" provisioning intent). This is a genuine open question requiring Kalshi-side verification, not something this document can settle from the codebase alone — flagged here rather than guessed at.

---

## TH-03 — Shadow Documentation / Governance Erosion (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Decisions made outside the directory; artifacts drift from reality; context rot recurs |
| Category | Integrity (Accidental) |
| Attack vector | Internal (process failure) |
| Affected components | All (governance layer) |
| Likelihood | HIGH — This is the identified cause of the previous iteration failure |
| Impact | HIGH — Loss of reproducibility; handoff failure; invalid decisions based on stale information |
| Controls | (1) Compass OS cadences mandatory. (2) Universal headers on all artifacts. (3) Anti-shadow-doc rule: 72-hour absorption deadline. (4) M1 freshness metric tracked weekly. (5) Escalation ladder: M1 < 85% → owner ping; < 75% → accountable review; < 65% → gate freeze. |
| Residual risk | MEDIUM — Process-based controls depend on operator discipline |
| Related FM | FM-08 |
| Revisit trigger | Quarterly retrieval drill; DIR health report below M1 threshold |

---

## TH-04 — Order Duplication / Double Submission (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Same order submitted twice due to retry logic or timeout; double position taken |
| Category | Integrity (Accidental) |
| Attack vector | Internal (network failure + retry without idempotency check) |
| Affected components | C5 (Phase 6+) |
| Likelihood | MEDIUM — Network failures are common; retry logic error is a known failure class |
| Impact | HIGH — Position exceeds approved limit; may breach risk limits |
| Controls | (1) idempotency_key required on all orders (IF-C5-VENUE). (2) Deduplication log in C6. (3) Venue confirmation checked before retry. |
| Residual risk | LOW (with idempotency key correctly implemented) |
| Related FM | FM-05 |
| Revisit trigger | Venue API change; any network failure event in paper/live trading |

---

## TH-05 — Kill Switch Failure (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Kill switch triggered but does not halt all components; losses continue |
| Category | Safety (Accidental) |
| Attack vector | Internal (implementation error in kill switch wiring) |
| Affected components | C7, all active components |
| Likelihood | LOW (if tested) → HIGH (if not tested before live use) |
| Impact | CRITICAL — Uncontrolled continued operation after halt signal |
| Controls | (1) Kill signal broadcast to all components simultaneously. (2) Each component independently checks kill flag. (3) Kill switch drill mandatory at G5 before any live use. (4) C7 monitors independently of C4. |
| Residual risk | LOW (if G5 drill passes) → CRITICAL (if G5 drill skipped) |
| Related FM | FM-06 |
| Revisit trigger | New component added; kill switch drill failure; architecture change |

---

## TH-06 — Model Overfitting / False Edge (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Model shows positive backtest performance due to overfitting; no real edge in live markets |
| Category | Integrity (Accidental) |
| Attack vector | Internal (insufficient validation discipline) |
| Affected components | C3 |
| Likelihood | HIGH — Overfitting is the dominant failure mode in predictive modeling |
| Impact | HIGH — Live capital deployed on a model with zero or negative EV |
| Controls | (1) Hold-out test set never used during development (accessed only at G4). (2) Null model comparison mandatory (market_implied_prob baseline). (3) Calibration curves required. (4) ≥3 independent experiments required for G4 evidence. (5) Risk limits prevent catastrophic drawdown even if model has negative edge. |
| Residual risk | MEDIUM — No guarantee of live edge; residual risk accepted and managed by risk limits |
| Related FM | FM-03 |
| Revisit trigger | G4 evidence review; live Brier score monitoring |

---

## TH-07 — Unauthorized Capital Deployment (Process Failure)

| Attribute | Detail |
|-----------|--------|
| Threat | Real capital deployed before G6 gate is cleared; premature live trading |
| Category | Safety (Process Failure) |
| Attack vector | Internal (gate bypass by operator) |
| Affected components | C5 (Phase 8) |
| Likelihood | LOW — Solo operator; temptation risk present without process controls |
| Impact | CRITICAL — Unvalidated model exposed to real capital loss |
| Controls | (1) C5 live mode hard-gated behind ADR-0005 acceptance. (2) Live venue credentials not created until G5+. (3) APR-0009 signature required. (4) G6 checklist explicit in ACCEPTANCE_CRITERIA.md. |
| Residual risk | LOW (process controls in place; single operator risk accepted) |
| Related FM | FM-04 |
| Revisit trigger | Any attempt to access live venue API before G6 |

---

## TH-08 — Stale Model in Production (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Market regime changes; model continues operating on stale assumptions; edge decays undetected |
| Category | Integrity (Accidental) |
| Attack vector | Environmental (market change) + Internal (monitoring gap) |
| Affected components | C3 (model), C7 (monitoring) |
| Likelihood | MEDIUM-HIGH — Market regimes do shift; signal decay is a known risk |
| Impact | HIGH — Continued operation generates negative EV |
| Controls | (1) Brier score monitoring on rolling 30-event window (FM-03). (2) Auto-alert at drift threshold. (3) No automated retraining in production — retraining requires ADR + new model version. (4) MONITORING_DRIFT_PLAN.md defines response. |
| Residual risk | MEDIUM — Monitoring provides early warning; action depends on operator response |
| Related FM | FM-03 |
| Revisit trigger | Live deployment; any drift alert |

---

## TH-09 — Audit Log Tampering or Loss (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | Audit log modified, deleted, or corrupted; decision history unrecoverable |
| Category | Integrity (Accidental) |
| Attack vector | Internal (storage failure, process crash during write) |
| Affected components | C6 |
| Likelihood | LOW (if append-only enforced) |
| Impact | HIGH — Loss of auditability; governance invariant violated; cannot reconstruct decisions |
| Controls | (1) Append-only log format; no modification path. (2) Write confirmation before acknowledging event. (3) Log integrity check (hash verification). (4) Backup rotation per DATA_RETENTION_DELETION.md. |
| Residual risk | LOW |
| Related FM | FM-07 |
| Revisit trigger | Storage architecture change; any disk failure event |

---

## Threat Summary Matrix

| ID | Threat | Likelihood | Impact | Net Risk | Status |
|----|--------|------------|--------|----------|--------|
| TH-01 | Data contamination / look-ahead bias | HIGH | CRITICAL | CRITICAL | Mitigated (automated checks required) |
| TH-02 | Credential exposure (live RSA key + `VPS_SSH_KEY` blast radius) | LOW-MED | MED (demo) →CRITICAL (post-G6 if unchanged) | MEDIUM | Partially mitigated — no vault, no passphrase, no rotation ever performed (see Live Credential Attack Surface section) |
| TH-03 | Shadow docs / context rot | HIGH | HIGH | HIGH | Mitigated (Compass OS cadences) |
| TH-04 | Order duplication | MED | HIGH | MED | Mitigated (idempotency key) |
| TH-05 | Kill switch failure | LOW (if tested) | CRITICAL | MED | Mitigated (G5 drill required) |
| TH-06 | Overfitting / false edge | HIGH | HIGH | HIGH | Partially mitigated (G4 evidence required) |
| TH-07 | Premature live capital | LOW | CRITICAL | MED | Mitigated (hard gate controls) |
| TH-08 | Stale model in production | MED | HIGH | MED | Mitigated (drift monitoring) |
| TH-09 | Audit log loss | LOW | HIGH | LOW | Mitigated (append-only + backup) |

---

## Threats Out of Scope (Phases 0–5)

The following threat categories were originally deferred to "Phase 6+." **Corrected 2026-07-13 (T-347/GG-093):** two of the four reasons below were falsified by ADR-0008 (2026-05-31) and are struck through with the corrected framing — real Kalshi credentials and a real (demo) account have existed for six+ weeks. See TH-02 and the Live Credential Attack Surface section above for the analysis that replaces the old "zero attack surface" assumption.

| Threat Category | Reason Deferred |
|-----------------|-----------------|
| External adversarial attacks on venue API | ~~No live credentials exist; external attack surface is zero~~ — **false since 2026-05-31 (ADR-0008). Now covered in-scope by TH-02 and the Live Credential Attack Surface section. Remains bounded to demo-account impact only while G6 is unmet.** |
| Account takeover / venue fraud | ~~No live account until G5+~~ — **false; a live demo Kalshi account has existed since ADR-0008. Real-capital account takeover stays out of scope until G6 (no real capital deployed), but demo-account order manipulation / evidence-trail corruption is now in scope — see TH-02.** |
| Price manipulation / market adversary | Cannot be fully mitigated; managed by position sizing limits |
| Regulatory/compliance action | Tracked in POLICY_REQUIREMENTS.md; no live trading until G6 |

**Next expansion trigger: G6 authorization (live capital).** At that point the live-capital credential's key-storage/passphrase/rotation posture (currently unencrypted PEM, no passphrase, no rotation — see Live Credential Attack Surface above) must be explicitly re-assessed, not silently carried forward from the demo-account arrangement this section now documents.
