# ADR-0003 — Venue Selection for Prediction Market Execution

**Status:** **ACCEPTED — 2026-05-23** — OQ-006 resolved; Polymarket US CA-legal confirmed; formally accepted by operator (Earl Ignacio)  
**Date:** 2026-05-22 (skeleton drafted)  
**Decision date:** 2026-05-23  
**Deciders:** DS (Earl Ignacio)  
**Supersedes:** None  
**Superseded by:** Supplemental ADR or Change Class B record (CHANGE_CONTROL.md) if venue list changes post-Phase 6  
**Upstream links:** ADR-0002 (forecast-only strategy); OQ-003 ✅ (resolved — NBA, Kalshi primary); OQ-006 ✅ (resolved — CA-legal venue enumeration confirmed)  
**Downstream links:** INTERFACES_CONTRACTS.md (C5 Execution Engine venue contract); EXECUTION_ARCHITECTURE.md (multi-venue edge normalization); RUN_INSTRUCTIONS.md (ENV-02 venue credentials)  
**Decision references:** ADR-0001, ADR-0002  
**Confidence:** 8/10 — Kalshi primary confirmed; Polymarket US confirmed CA-legal (CFTC-regulated, relaunched December 2025); multi-venue architecture accepted  

---

## Context

OQ-003 (resolved 2026-05-22) confirmed: the target domain is **NBA basketball**; the strategy is **dynamically agnostic** across NBA event types (player props, game outcomes, series outcomes); **Kalshi** is the primary venue for initial deployment.

Two additional constraints shape this decision:

1. **California legal landscape:** Earl Ignacio operates from California. Prediction market platforms must be legal for CA residents. Not all platforms are available to CA users. Full multi-venue deployment requires a complete enumeration of CA-legal venues (OQ-006).

2. **CFTC regulation:** Kalshi is regulated by the CFTC as a Designated Contract Market (DCM). This provides regulatory clarity for binary event contracts on sports outcomes. Other platforms (e.g., Polymarket) operate under different legal frameworks. The CFTC-regulated status of the venue is a compliance consideration (POLICY_REQUIREMENTS.md POL-001).

3. **Multi-venue normalization:** The C5 (Execution Engine) is designed to normalize edge calculations per-venue (EXECUTION_ARCHITECTURE.md). This means the forecasting layer (C3) outputs a probability estimate independent of venue; venue-specific spread and vig are applied at the execution layer. ADR-0003 must confirm the venue list that C5 must support.

---

## Decision Drivers

| Driver | Weight | Notes |
|--------|--------|-------|
| Legal availability in California | CRITICAL | Must be confirmed for any venue included |
| CFTC regulation / legal clarity | High | Reduces operational and compliance risk; Kalshi is the only currently CFTC-regulated sports prediction market |
| NBA contract coverage and liquidity | High | Venue must offer NBA event contracts with sufficient depth to execute at model-sized positions |
| API access and programmatic execution | High | C5 requires API access; manual execution is not a design option for Phase 5+ |
| Spread and vig (transaction costs) | Medium | Directly affects minimum required edge; lower spread = lower edge threshold |
| Venue concentration risk | Medium | Single-venue dependency creates operational risk; multi-venue reduces but complicates execution |
| Operational complexity of multi-venue | Medium | More venues = more credentials, more API integrations, more normalization complexity |

---

## Options Considered

### Option A: Kalshi-Only (Initial Deployment)

**Description:** Deploy exclusively on Kalshi for all NBA event contracts. Do not integrate additional venues until Kalshi trading is fully operational and producing paper trading evidence.

**Pros:**
- Single API integration; simplest C5 implementation
- Kalshi is CFTC-regulated; highest legal clarity
- Kalshi confirmed CA-legal
- Minimizes Phase 3–5 implementation scope

**Cons:**
- Concentration risk: single venue = single point of failure; if Kalshi suspends NBA markets or changes pricing, all activity halts
- Kalshi spreads may be suboptimal for some contract types; no competitive pricing alternative
- Does not leverage full CA-legal venue landscape

**Verdict:** Appropriate for **initial deployment (Phase 5–6)**. Accepted for the Kalshi-primary architecture. Should evolve to Option B post-G6 once the system is proven.

---

### Option B: Kalshi Primary + CA-Legal Multi-Venue (Full Deployment)

**Description:** Kalshi is the primary venue. Once operational, integrate additional CA-legal prediction market venues. C5 Execution Engine normalizes edge calculation per-venue and routes orders to the best-priced venue for each contract.

**Pros:**
- Reduces concentration risk
- Best execution pricing across venues; competitive spread selection
- Full market coverage: contracts available on one venue but not another can be captured
- Designed to be the long-run architecture per OQ-003 operator decision

**Cons:**
- Requires OQ-006 resolution: full CA-legal venue list must be confirmed before integration scope is defined
- Multiple API credentials (NFR-05; vault design becomes more complex)
- C5 multi-venue normalization adds implementation complexity
- Some platforms may have inferior liquidity, increasing spread costs

**Verdict:** **Target architecture for full deployment (post-G6)**. OQ-006 resolved at ADR-0003 formal acceptance (2026-05-23). CA-legal venues confirmed: Kalshi (CFTC-DCM, primary), Polymarket US (CFTC-regulated December 2025 relaunch, Phase 6+ secondary). Robinhood Prediction Markets deferred — CA availability unconfirmed; evaluate as additional venue emerges. Any new venue addition requires new ADR (Class A change).

---

### Option C: Polymarket or Non-CFTC Platform as Primary

**Description:** Use a non-CFTC platform (e.g., Polymarket, which operates via USDC/blockchain contracts) as the primary venue.

**Pros:**
- Potentially deeper liquidity for some markets
- Different asset types (crypto-native)

**Cons:**
- ~~Regulatory uncertainty under CA law and federal jurisdiction~~ — **UPDATE 2026-05-23:** Polymarket US relaunched December 2025 as a CFTC-regulated platform, legally available in California. This resolves the prior concern.
- Non-CFTC Polymarket (original) remains excluded; only Polymarket US (CFTC-regulated) is eligible
- Significantly higher compliance complexity vs. Kalshi-only

**Verdict (UPDATED 2026-05-23):** **REJECTED as primary venue.** Kalshi remains primary. However, **Polymarket US is now eligible for Option B multi-venue integration** — its December 2025 CFTC-regulated relaunch resolves the prior CA-legal concern. Polymarket US is added to the confirmed CA-legal venue list for Phase 6+ multi-venue deployment. Original (non-US) Polymarket remains excluded.

---

## Decision — ACCEPTED 2026-05-23

**Formally accepted by operator (Earl Ignacio / DS) on 2026-05-23 following OQ-006 resolution:**

1. **Kalshi is confirmed as the primary venue** for initial deployment (Phases 5–6). C5 Execution Engine will be designed for Kalshi API integration first. CFTC-regulated DCM; available all 50 states; NBA sports markets confirmed.

2. **Multi-venue (Option B) is the accepted architecture for full deployment (Phase 6+).** The confirmed CA-legal venue list is:
   - **Kalshi** (primary): CFTC-DCM; ~$5B monthly notional volume; full API
   - **Polymarket US** (secondary): CFTC-regulated (relaunched December 2025); CA-legal; open market data API; KYC required for execution
   - Additional venues: Evaluate as new CFTC-regulated platforms emerge; each requires Access Request (ACCESS_REQUESTS.md) + POLICY_REQUIREMENTS.md CA-compliance check before integration

3. **C5 must be architected from the start to support multi-venue normalization.** Single-venue Kalshi implementation is a Phase 5 scope reduction, not a permanent constraint. `venue_id` must remain a parameter in all C5 execution calls — hardcoding is PROHIBITED.

4. **Polymarket US is eligible for Option B integration** (updated from original skeleton). Original non-US Polymarket and any non-CFTC platform remain excluded (Rejected Option C).

5. **nba_api confirmed as Phase 3 data proxy** (OQ-015 ✅ resolved 2026-05-23). Synergy/Second Spectrum access deferred to Phase 4 if Phase 3 proxy proves insufficient.

---

## Consequences

### If accepted at G3 as drafted:

| Consequence | Artifact / Component | Action Required |
|------------|---------------------|----------------|
| C5 Execution Engine must support multi-venue normalization | EXECUTION_ARCHITECTURE.md | AO to update C5 interface contract before G3 |
| Kalshi API credentials required at ENV-02 | SECRETS_HANDLING.md, ENVIRONMENTS.md | API access request (ACCESS_REQUESTS.md) before Phase 5 |
| VENDOR_RISK.md VND-01 entry (venue) to be updated to KALSHI | VENDOR_RISK.md | AO to update risk entry at ADR-0003 acceptance |
| OQ-006 closure triggers multi-venue API integration scope | PLAN.md Phase 2+ | EL to add tasks once OQ-006 resolved |
| POLICY_REQUIREMENTS.md must confirm CA compliance for each added venue | POLICY_REQUIREMENTS.md | RCO review per new venue added |

### Architecture constraints recorded now:

- C5 must accept `venue_id` as a parameter in all execution calls. Hardcoding Kalshi into C5 is a prohibited pattern.
- Edge formula per-venue: `edge = p̂ - mid_price(venue) - (spread(venue) / 2)`. Spread must be fetched at order time, not estimated from prior observations.
- Any venue added after Phase 6 requires a supplemental ADR or a Change Class B record in CHANGE_CONTROL.md.

---

## Open Items (Resolved at Acceptance)

| Item | Status | Resolution |
|------|--------|-----------|
| OQ-006: CA-legal venue enumeration | ✅ RESOLVED 2026-05-23 | Kalshi (CFTC-DCM) + Polymarket US (CFTC-regulated, Dec 2025 relaunch) confirmed CA-legal |
| Kalshi API documentation review | Deferred to Phase 5 | C5 interface contract designed parameter-first; Kalshi API spec reviewed at ENV-02 activation |
| Legal review of non-Kalshi venues | ✅ Addressed — Polymarket US confirmed CFTC-regulated | Additional venues evaluated per ACCESS_REQUESTS.md as they emerge |

## Post-Acceptance Required Actions

| Consequence | Artifact | Action | Phase |
|------------|---------|--------|-------|
| VENDOR_RISK.md VND-01 update to Kalshi primary | VENDOR_RISK.md | AO to update risk entry | Phase 3 |
| Polymarket US added as secondary venue | VENDOR_RISK.md | Add VND-XX entry for Polymarket US | Phase 3 |
| requirements-dev.txt: add nba_api | DEPENDENCY_LOCKS/ | Add `nba_api>=1.5.0` to requirements | Phase 3 (T-032) |
| POLICY_REQUIREMENTS.md: CA compliance note | POLICY_REQUIREMENTS.md | Confirm Kalshi + Polymarket US CA-legal | Phase 3 |
| C5 venue list updated in code | src/prediction_market_bot/execution/ | `venue_id` parameter; VENUE_REGISTRY dict | Phase 5 (T-034) |

---

## Review Triggers

- OQ-006 resolved (triggers G3 readiness check)
- New CFTC-regulated NBA prediction market platform launches before G3
- CA legal landscape changes regarding prediction market access
- Kalshi changes NBA contract availability, pricing structure, or API terms

---

*This ADR skeleton was drafted 2026-05-22 (Phase 1, T-021). It will be updated as OQ-006 is resolved and Kalshi API documentation is reviewed. Formal acceptance is gated on G3 exit criteria.*
