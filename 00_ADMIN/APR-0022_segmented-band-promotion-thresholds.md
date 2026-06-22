# APR-0022 — Segmented Per-Band Promotion Thresholds (ADR-0028)

**Status:** PENDING — DS sign-off required  
**ADR Reference:** ADR-0028_segmented-band-promotion-thresholds.md  
**Amends:** APR-0017 + APR-0019  
**Drafted:** 2026-06-22 SESSION 65  
**Registered by:** T-148

---

## What Is Approved

DS approval of ADR-0028 (Segmented Per-Band Promotion Thresholds), which amends APR-0017 and APR-0019 with five modifications:

| Mod | Summary |
|---|---|
| 5 | Fill-realism mandate: T2-B and T2-D (all buckets) evaluate post-haircut P&L using T-153 p50 methodology |
| 6 | T4 Tier 2 thresholds formally derived: T2-A ≤20pp, T2-B post-haircut EV>0 (two-leg), T2-C Brier ≤0.265, T2-D post-haircut slope>0 (two-leg) |
| 7 | T4 game-night floor: ≥5 nights explicitly required for T4 slope criteria (same df≥3 derivation as T1) |
| 8 | T-AGG aggregate criterion: combined portfolio post-haircut EV>0 (T-AGG-A) + P&L slope>0 (T-AGG-B); evaluated after per-bucket Tier 2 passes |
| 9 | YES-only gate clarification: T1 Tier 2 evaluates YES-direction eligible bets only while PAPER_YES_ONLY gate is active |

**Resolves:** GG-022 (Paper-Fill Realism APR-0017 amendment) upon sign-off.

**Does NOT change:** Tier 0, Tier 1, Tier 3, per-bucket calibration floors (T1 ≥66, T4 ≥50), T2-A/T2-C (non-P&L criteria), ADR-0024, C4 risk limits, formal gate prerequisites (APR-0008/0009).

---

## Broken-System Test (summary)

See ADR-0028 § Broken-System Tests. Core scenarios addressed:
- System EV-positive on paper fills but negative after realistic costs (caught by Mod 5)
- T4 with nominal EV > 0 but two-leg haircut goes negative (caught by Mod 6)
- Portfolio aggregate negative even when per-bucket T2-B individually passes (caught by Mod 8)
- NO counterfactuals inflating T1 Tier 2 sample (caught by Mod 9)

---

## Review Checklist

- [ ] All five modifications reviewed against ADR-0028 full text
- [ ] GG-022 closure confirmed upon sign-off
- [ ] T-148 G6 blocker resolved upon sign-off

**Sign-off:** _______________  
**Date:** _______________  
**Role:** DS — Earl Ignacio
