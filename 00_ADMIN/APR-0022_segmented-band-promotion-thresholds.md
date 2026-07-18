# APR-0022 — Segmented Per-Band Promotion Thresholds (ADR-0028)

**Status:** **ACCEPTED — DS sign-off Earl Ignacio, 2026-06-22 SESSION 72.** All 14 checklist items approved; GG-022 RESOLVED; T-148 DONE (see `03_DECISIONS/GOVERNANCE_GAP_LOG.md` GG-022, `04_EXECUTION/TODO_NEXT.md` T-148). **This document and `00_ADMIN/APPROVALS_REGISTER.md`'s APR-0022 row were never updated to reflect that sign-off — both still read PENDING a month later. Corrected 2026-07-17 (GG-126) as a doc-sync fix, not a new decision; no re-review was requested or performed today.**  
**ADR Reference:** ADR-0028_segmented-band-promotion-thresholds.md  
**Amends:** APR-0017 + APR-0019  
**Drafted:** 2026-06-22 SESSION 65  
**Reworked:** 2026-06-22 SESSION 65 — T4 criteria (Mods 6, 7) and T-AGG (Mod 8) moved from G6 to T4 Activation Gate  
**Registered by:** T-148

---

## Rework Note

Initial draft declined by DS: "sign off not granted — the segmentation for the promotion bands are still not fully aligned with the current structure per band."

Root cause: initial draft required T4 Tier 2 (Mods 6, 7) and T-AGG (Mod 8) for G6 closure. All T4 strategies are BLOCKED in BAND_REGISTRY (Phase 8+). G6 is a T1 live capital gate; T4 cannot generate real paper evidence at Phase 6/7. These criteria have been moved to a new "T4 Activation Gate" (Phase 8 pre-requisite) in ADR-0028.

---

## What Is Approved

DS approval of ADR-0028 (Segmented Per-Band Promotion Thresholds — reworked), which amends APR-0017 and APR-0019 with five modifications:

| Mod | Summary | Gate scope |
|---|---|---|
| 5 | Fill-realism mandate: T2-B and T2-D evaluate post-haircut P&L using T-153 p50 methodology | G6 (T1 bucket) + T4 Activation Gate (T4 bucket) |
| 6 | T4 Tier 2 thresholds formally derived: T2-A ≤20pp, T2-B post-haircut EV>0 (two-leg), T2-C Brier ≤0.265, T2-D post-haircut slope>0 (two-leg) | **T4 Activation Gate only (Phase 8 pre-requisite)** |
| 7 | T4 game-night floor: ≥5 nights explicitly required for T4 slope criteria (same df≥3 derivation as T1) | **T4 Activation Gate only** |
| 8 | T-AGG aggregate criterion: combined portfolio post-haircut EV>0 (T-AGG-A) + P&L slope>0 (T-AGG-B); evaluated after per-bucket Tier 2 passes at T4 Activation Gate | **T4 Activation Gate only (Phase 8 pre-requisite)** |
| 9 | YES-only gate clarification: T1 Tier 2 evaluates YES-direction eligible bets only while PAPER_YES_ONLY gate is active | G6 (T1 Tier 2 only) |

**G6 closure condition (T1-only):** Tier 0 + T1 statistical floor (≥66 eligible bets + ≥5 game nights) + Tier 1 (T1-A through T1-D) + Tier 2 (T1, Mods 5+9 apply) + Tier 3 + Formal prerequisites. T4 Tier 2 and T-AGG are NOT G6 requirements.

**T4 Activation Gate (Phase 8):** T4 ≥50 eligible bets + ≥5 game nights + T4 Tier 2 (T2-A/B/C/D, Mods 6+7) + T-AGG (Mod 8) + BLOCKED→ACTIVE promotion ADR + real-time C5 infra ADR + kill-switch SLA <5s revision. Independent of G6 — G6 may close before this gate opens.

**Resolves:** GG-022 (Paper-Fill Realism APR-0017 amendment) upon sign-off.

**Does NOT change:** Tier 0, Tier 1, Tier 3, per-bucket calibration floors (T1 ≥66 at G6; T4 ≥50 at T4 Activation Gate), T2-A/T2-C (non-P&L criteria), ADR-0024, C4 risk limits, formal gate prerequisites (APR-0008/0009).

---

## Broken-System Test (summary)

See ADR-0028 § Broken-System Tests. Core scenarios addressed:
- System EV-positive on paper fills but negative after realistic costs (caught by Mod 5)
- T4 with nominal EV > 0 but two-leg haircut goes negative (caught by Mod 6, at T4 Activation Gate)
- Portfolio aggregate negative even when per-bucket T2-B individually passes (caught by Mod 8, at T4 Activation Gate)
- NO counterfactuals inflating T1 Tier 2 sample (caught by Mod 9)

---

## Review Checklist

- [x] Rework rationale accepted — T4 BLOCKED (Phase 8+); T4 Tier 2 + T-AGG moved to T4 Activation Gate; G6 is T1-only
- [x] Mod 5 (fill-realism, G6 + T4 gate scope) reviewed against ADR-0028 full text
- [x] Mod 6 (T4 Tier 2 thresholds, T4 Activation Gate) reviewed
- [x] Mod 7 (T4 game-night floor ≥5, T4 Activation Gate) reviewed
- [x] Mod 8 (T-AGG, T4 Activation Gate) reviewed
- [x] Mod 9 (YES-only gate / T1 Tier 2, G6 scope) reviewed
- [x] G6 closure condition (T1-only, 6 items) reviewed
- [x] T4 Activation Gate conditions (5 items) reviewed
- [x] GG-022 closure confirmed upon sign-off
- [x] T-148 G6 blocker resolved upon sign-off

**Sign-off:** Earl Ignacio  
**Date:** 2026-06-22 (SESSION 72; this record corrected 2026-07-17 per GG-126 — sign-off itself is not new)  
**Role:** DS — Earl Ignacio
