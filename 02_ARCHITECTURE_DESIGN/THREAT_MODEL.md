# Threat Model — Prediction Market Trading Bot

**Purpose:** Identify threats to system integrity, data validity, capital safety, and governance. Maps threats to mitigations and residual risk. Required for G2 gate.  
**Owner (role):** Architecture Owner (AO) + Risk and Compliance Owner (RCO)  
**Status:** **CANONICAL — G2 Architecture Gate 2026-05-22** — Changes require ADR or formal Change Class A/B record  
**Last reviewed:** 2026-05-22 (G2 review; C4/C5 corrected; promoted DRAFT → CANONICAL; RCO = AO as sole operator) — **TH-02 + Threats Out of Scope re-expanded 2026-07-12 (T-347/GG-093) for live-Kalshi-credential reality**  
**GG-074 monthly staleness review (2026-07-23):** read TH-01/TH-03–TH-09 in full (the entries GG-093 did not touch) against current system state. Found one real drift: TH-05's residual-risk line still carried conditional "if G5 drill passes / if skipped" language describing an unresolved state — both kill-switch drills resolved favorably weeks ago (NBA APR-0013, MLB APR-0023, both well within NFR-03's ≤60s per DECISION_LOG); corrected TH-05 and its Threat Summary Matrix row in place. TH-01, TH-03, TH-04, TH-06, TH-07, TH-08, TH-09 checked against current architecture (dual-ledger MLB/NBA split, T4 live, idempotency_key in execution, G4 evidence process) and remain accurate as written — no further drift found.  
**Next review:** On staleness trigger only; full re-expansion at G6 (pre-live-capital)  
**Staleness triggers:** New component added; new external integration; security incident; venue API confirmed; live capital authorized  
**Upstream links:** ARCHITECTURE_OVERVIEW.md, SYSTEM_CONTEXT.md, RESILIENCE_FAILURE_MODES.md  
**Downstream links:** 09_SECURITY_PRIVACY_COMPLIANCE/, 10_INFRA_OPERATIONS/RUNBOOKS/  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 6/10 for TH-02 and Threats Out of Scope (re-verified against live config 2026-07-12); 5/10 for TH-01/TH-03–TH-09 (unreviewed since G2, same staleness risk this pass just found in TH-02 may apply elsewhere and has not been checked)
**Decisions logged:** true — TH-01–TH-09 threat prioritization and STRIDE scope decisions captured at G2 gate (APR-0004); TH-02 re-expansion decisions captured 2026-07-12 (T-347, see DECISION_LOG.md)

---

## Threat Modeling Scope

This model covers Phases 0–5 (research and operational readiness). Live capital threats are flagged and will be expanded at G5. Threats are categorized using a simplified STRIDE framework applied to this system's specific risk profile.

**⚠️ Corrected 2026-07-06 (GG-074 remediation) — real gap found, not just doc staleness.** G5 closed and ADR-0008 (2026-05-31) enabled real Kalshi demo order submission (RSA-signed API credentials, live on the VPS for weeks) — but this document's closing line ("Expand this threat model at G5 before any live venue connection is established") was never acted on: this threat model has not been re-run since G5. TH-02 (Credential Exposure) still reads "Residual risk: LOW (Phases 0–5, no live credentials exist yet)" and "Threats Out of Scope (Phases 0–5)" still states "External adversarial attacks on venue API | No live credentials exist; external attack surface is zero" and "Account takeover / venue fraud | No live account until G5+" — all three are now false: real Kalshi RSA signing credentials exist and have been in active use in production since ADR-0008. The vault-tooling line in TH-02's controls ("implementation TBD at G2") is also resolved — the actual mechanism is `.env` + `python-dotenv` + OS env vars (NFR-05), not a Vault product. Recommend registering the un-expanded post-G5 threat model as its own governance gap — this is a real assessment gap (external attack surface analysis for live-but-demo Kalshi credentials has never been done), not merely a stale citation.

**✅ Actioned 2026-07-12 (T-347/GG-093) — the re-expansion this note called for is done; see TH-02 and "Threats Out of Scope" below, both rewritten in place.** This pass independently re-verified (not merely re-asserted) two carried-forward external findings against live config before writing them in: (1) `.github/workflows/{deploy,tss_daily_sync,post_game_resolve}.yml` all consume the same `VPS_SSH_KEY` secret (grep-confirmed, 2026-07-12) — one shared secret, three trigger surfaces, full root access to the VPS that also holds the live Kalshi RSA credential. (2) `deploy/t4-mlb.service` (the unit that actually loads `/opt/prediction-market-bot/.env` via `EnvironmentFile=` and runs as `root`) carries **zero** systemd hardening directives, while `scripts/pmbot-web-dashboard.service` (which needs no secrets at all) has `PrivateTmp`, `NoNewPrivileges`, `ReadOnlyPaths`, `MemoryMax`, and `CPUQuota` (file-diff-confirmed, 2026-07-12) — the unit protecting nothing is hardened; the unit protecting the live credential is not. Also newly found during this pass (not carried forward, discovered fresh): `06_CODE_EXECUTION_REPRODUCIBILITY/SECRETS_HANDLING.md`'s "Credential Rotation Policy" table still reads `[TBD at G5]` for the venue API key/secret rotation frequency — G5 closed 2026-05-22 and the live RSA credential has been in continuous use since ADR-0008 (2026-05-31), so as of this writing that credential has gone **6+ weeks live with no rotation cadence ever defined**, let alone executed. Separately, GG-116 (registered this session, 2026-07-12) confirms the exposure risk this section warns about is not hypothetical: a real Kalshi API key ID and private-key path sat in plaintext in a tracked handoff document for ~6 weeks before incidental discovery.

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

## TH-02 — Credential Exposure (Accidental)

| Attribute | Detail |
|-----------|--------|
| Threat | API keys, venue credentials, or account details committed to version control or stored in plaintext |
| Category | Information Disclosure (Accidental) |
| Attack vector | Internal (developer error) — **confirmed occurred**: prose/handoff documents, not just code, per GG-116 |
| Affected components | C5 (venue connection; live Kalshi RSA credential loaded via `EnvironmentFile=` in `t4-mlb.service`), C1 (data source connection), CI/CD (`.github/workflows/`, shared `VPS_SSH_KEY` secret) |
| Likelihood | **MEDIUM-HIGH (raised 2026-07-12, T-347)** — no longer theoretical: GG-116 confirms a real Kalshi API key ID + private-key path sat in plaintext in a tracked handoff doc for ~6 weeks before incidental discovery. NFR-05's controls scan code, not prose; that gap is unclosed. |
| Impact | HIGH — Venue account compromise; unauthorized order submission. Bounded today by demo-only capital (pre-G6), not bounded once live capital is authorized — this threat's impact ceiling rises at G6, not its likelihood. |
| Controls | (1) NFR-05: zero hardcoded secrets policy — **scope gap: covers code, not prose files; GG-116 leaked via a `.md` handoff doc, which no scan catches.** (2) Real mechanism (superseding the stale "Vault, TBD at G2" line): `.env` + `python-dotenv` + OS env vars, loaded on the VPS via systemd `EnvironmentFile=/opt/prediction-market-bot/.env` — confirmed live in `deploy/t4-mlb.service`, running as `root`, since ADR-0008 (2026-05-31). No vault product was ever selected or built; the env-var mechanism is what actually shipped and is what NFR-05 governs in practice. (3) SECRETS_HANDLING.md governs credential workflows in principle, but its own "Credential Rotation Policy" table (line 82) still reads `[TBD at G5]` for venue API key/secret rotation frequency — **unfilled 6+ weeks after G5 closed; the live RSA credential has never been rotated on any defined cadence.** (4) Pre-commit hook or manual audit before external repository push — covers code paths; GG-116 shows prose docs are a live blind spot in this control. (5) **New, verified 2026-07-12:** `t4-mlb.service` (holds the live credential) has zero systemd hardening (`NoNewPrivileges`, `PrivateTmp`, `ReadOnlyPaths` all absent; runs as `root`) — contrast `pmbot-web-dashboard.service` (holds no secrets), which has all three plus resource caps. (6) **New, verified 2026-07-12:** one shared `VPS_SSH_KEY` GitHub Actions secret (full root@VPS access) is reused across `deploy.yml`, `tss_daily_sync.yml`, and `post_game_resolve.yml` — three independent trigger/compromise surfaces for the same root-level credential blast radius. |
| Residual risk | **MEDIUM (unchanged 2026-07-13 later same session — GG-116 fully RESOLVED, both credential-material and history axes now closed).** The confirmed exposure (GG-116) is closed on both fronts: the leaked key ID was revoked in the Kalshi demo dashboard and a new key ID + private key pair generated and deployed (local + VPS `.env`, `t4-mlb.service` restarted, new key verified live via `get_balance()`, 2026-07-13); separately, the operator explicitly authorized and Claude executed a `git filter-repo --replace-text` history scrub, force-pushed to `origin/main` (`df50835` → `47096dd`), and propagated the rewrite to the local working tree and VPS deploy clone — zero occurrences of the leaked key ID verified across all refs post-scrub. Old key + old private key retained only as inert local/VPS backups (`kalshi_bot.pem.bak-20260713`) for rollback, not in active use. **Known residual, disclosed not hidden:** GitHub's `refs/pull/N/head` synthetic refs (20 existing PRs) are read-only and could not be force-pushed over, so old commits containing the (now-revoked) key ID may still be viewable via GitHub's PR UI/API for those PRs — a hygiene footnote on a dead credential, not an active-exposure risk. Residual risk held at MEDIUM rather than lowered further because what remains open is unrelated to GG-116 itself: rotation cadence is still undefined generally (T-352), the process holding the credential is still unsandboxed (T-353), and the CI/CD path to the host is still a single shared `VPS_SSH_KEY` across three workflows. Impact remains capital-bounded (demo only) until G6. |
| Related FM | N/A — no FM in RESILIENCE_FAILURE_MODES.md currently maps to credential exposure specifically; candidate for a future FM if this recurs. |
| Revisit trigger | Venue credentials rotated or created; any new prose/handoff document references a credential path or ID; CI/CD workflow file changed; systemd unit file changed; live capital authorized (G6) |

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
| Residual risk | LOW — **drill confirmed passed, both books** (GG-074 pass, 2026-07-23): NBA APR-0013, halt_time_ms=0.340 (2026-05-28); MLB APR-0023, halt_time_ms=0.116 (2026-06-27 session, register write-back 2026-07-18 per DECISION_LOG T-386). Both well within NFR-03's ≤60s. The prior conditional phrasing ("if drill passes / if skipped") described a not-yet-resolved state; both drills resolved this favorably weeks ago. |
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
| TH-02 | Credential exposure | MED-HIGH (confirmed occurred once — GG-116) | HIGH | HIGH | Partially mitigated (real creds live since ADR-0008; open gaps: unrotated 6+ wks, prose-doc leak vector unguarded by NFR-05 scans, shared 3-workflow CI/CD secret, unsandboxed systemd unit — see TH-02 above) |
| TH-03 | Shadow docs / context rot | HIGH | HIGH | HIGH | Mitigated (Compass OS cadences) |
| TH-04 | Order duplication | MED | HIGH | MED | Mitigated (idempotency key) |
| TH-05 | Kill switch failure | LOW (tested, both books) | CRITICAL | MED | Mitigated (G5 drills passed: NBA APR-0013, MLB APR-0023) |
| TH-06 | Overfitting / false edge | HIGH | HIGH | HIGH | Partially mitigated (G4 evidence required) |
| TH-07 | Premature live capital | LOW | CRITICAL | MED | Mitigated (hard gate controls) |
| TH-08 | Stale model in production | MED | HIGH | MED | Mitigated (drift monitoring) |
| TH-09 | Audit log loss | LOW | HIGH | LOW | Mitigated (append-only + backup) |

---

## Threats Out of Scope (Phases 0–5)

**⚠️ Rewritten 2026-07-12 (T-347/GG-093).** The two rows below were carried forward from the pre-G5 draft and were false as of ADR-0008 (2026-05-31) — see the GG-074 note under "Threat Modeling Scope" above. They are corrected in place here rather than deleted, since the deferral logic (impact is capital-bounded pre-G6) is still partially valid — only the "attack surface is zero" / "no live account" premises were wrong, not the entire row.

| Threat Category | Status as of 2026-07-12 |
|-----------------|-----------------|
| External adversarial attacks on venue API | **No longer out of scope — attack surface is real, not zero.** Real Kalshi RSA-signed API credentials have been live on the VPS since ADR-0008 (2026-05-31). Concrete surface: the RSA key file loaded via `EnvironmentFile=` into an unsandboxed `root` process (`t4-mlb.service`); a single `VPS_SSH_KEY` GitHub Actions secret shared across 3 workflows with full root access to the same host; an unrotated credential (SECRETS_HANDLING.md rotation table still `[TBD at G5]`, 6+ weeks after G5 closed). What remains genuinely deferred is *consequence*, not *surface*: a compromise today disrupts demo trading (spurious/cancelled orders, possible Kalshi account flagging), not real capital — that consequence ceiling changes at G6, not before. |
| Account takeover / venue fraud | **No longer out of scope — a live account (demo tier) has existed since ADR-0008 (2026-05-31), ~6 weeks before this correction.** Takeover risk is real today, gated only by (a) OS file permissions on `.env`/RSA key, (b) the shared `VPS_SSH_KEY` secret remaining uncompromised, and (c) no rotation ever having occurred. As above, consequence is bounded by demo-only capital until G6; the takeover mechanics themselves are not phase-gated. |
| Price manipulation / market adversary | Cannot be fully mitigated; managed by position sizing limits. (Unchanged — this row was not flagged as false and stands.) |
| Regulatory/compliance action | Tracked in POLICY_REQUIREMENTS.md; no live trading until G6. (Unchanged — this row was not flagged as false and stands; regulatory exposure genuinely is gated on live capital, unlike the two rows above.) |

**This satisfies the document's original "expand this threat model at G5" instruction below, ~6 weeks after G5 closed (2026-05-22).** Next scheduled expansion: **G6 (pre-live-capital)** — per line 7 above, and per the still-open items surfaced in TH-02: define an actual rotation cadence for the venue API key/secret (SECRETS_HANDLING.md), and evaluate whether `t4-mlb.service` should receive systemd hardening comparable to the dashboard unit before live capital is authorized.
