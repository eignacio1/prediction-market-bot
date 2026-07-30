# ADR-0049: Signed Edge Gate + Direction-Consistency Check (C4 CHECK 3/CHECK 4b)

**Status:** ACCEPTED (2026-07-29/30, DS sign-off = operator, per Strategic Analysis §A/§E/§H, 2026-07-29 — proceed authorized explicitly). Applied live — R2/GG-142, this session, `logic_epoch.py` 9→10.
**Date:** 2026-07-29
**Author:** Session `session/20260730T052831Z-r2-gate-fix`
**Depends on:** GG-142 (resolving), ADR-0048 (R1, `kelly_fraction=0` for T1/T2/T3/T4M-PROJ — this fix is correctness for when those bands are re-enabled, not a re-activation)

---

## 1. Defect

`risk.py`'s CHECK 3 (`evaluate_forecast()`) gated on `abs(edge) < MIN_EDGE_TO_APPROVE`. The `edge` field on a forecast record is not a raw YES-frame signal — every producer (`run_t4_mlb_live.py`, `run_mlb_paper_trade.py`'s `_directional_edge()`, `run_t2_mlb_sameday.py`) computes it as the **direction-resolved, fee/vig-net edge of the bet in `recommended_direction`**, established across GG-077/GG-087/GG-113/GG-119 as the shared convention this gate is supposed to consume. A positive value means "the recommended direction has a real net edge of this size." A negative value means the opposite: vig/fee cost exceeds the signal in the recommended direction — a confidently-**wrong** bet, not a smaller-but-still-valid one.

`abs()` erases that distinction. Any sufficiently-negative directional edge was treated as passing the threshold, rescuing confidently-wrong bets into approval. Measured impact (T4 epoch-8 cohort, `05_RESEARCH_EXPERIMENTS/STRATEGIC_ANALYSIS_2026-07-29.md` §A): 239/239 rescued evaluations = 46.1% of the cohort, all with `vig > |model_p − mid|`. The defect lives in the shared C4 gate (`risk.py`), not any one band's producer code — `run_mlb_paper_trade.py`'s own `_directional_edge()` docstring names this exact CHECK 3 as its intended consumer, confirming T1/T2/T4M-PROJ all feed the same vulnerable check. It bit T4 hardest because T4's NO-branch vig/edge magnitude distribution produces negative directional edges far more often than T1's; the code path is identical.

## 2. Fix

1. **CHECK 3 becomes a signed check**: `if edge < MIN_EDGE_TO_APPROVE` replaces `if abs(edge) < MIN_EDGE_TO_APPROVE`. Only a sufficiently positive directional edge clears the gate. The diagnostic `edge_signal` field in `_emit_edge_decision` is corrected identically (`edge >= MIN_EDGE_TO_APPROVE`, not `abs(edge) >= ...`) so audit logs stop mischaracterizing rejected-confidently-wrong bets as having cleared a signal threshold.

2. **New CHECK 4b — direction/edge-sign consistency**, inserted after CHECK 4 (direction actionable). `recommended_direction` is written at three sites in `risk.py` (lines formerly 413/505/623) but was never cross-checked against anything before this fix. CHECK 4b validates, only when the record carries an optional raw `gross_edge` field (not all producers set it — this check is additive, not a new hard requirement), that `direction == "YES"` implies `gross_edge > 0` and `direction == "NO"` implies `gross_edge < 0`. This is a different failure class than the signed-CHECK-3 fix: it catches a future GG-077-style bug where a producer assigns direction incorrectly relative to the raw signal it computed direction from, which a signed-but-still-consistent `edge` value alone would not reveal. Rejection reason: `direction_edge_sign_inconsistent`.

## 3. Why a new ADR, not an amendment to ADR-0048 or any prior sign-flip ADR (ADR-0043/ADR-0045)

Hard Rule 3: ADRs are immutable once accepted. ADR-0043/ADR-0045 fixed producer-side sign conventions (`_directional_edge()`, `run_t4_mlb_live.py`'s NO-branch vig handling) — this fix is consumer-side, in the shared C4 gate that reads whatever the producer already correctly computed. ADR-0048 zeroed sizing; this fix does not touch sizing and does not depend on ADR-0048's reactivation table. They are independent, hence a new document.

## 4. Relationship to ADR-0048 / live risk posture

**This is a correctness fix for the gate, not a re-activation.** All four bands (T1_MULTI_DAY, T2_SAME_DAY, T3_PRE_TIP, T4M_PROJ) remain at `kelly_fraction=0` per ADR-0048 §2.1, unchanged by this document. Evaluations continue to be logged (CHECK 3/4b rejections preserve full forecast context, same as the pre-existing `kelly_size_zero` rejection path) for research and for the eventual GG-105/D2 reactivation gate — this fix ensures that when a band is reactivated, its CHECK 3 gate will correctly reject confidently-wrong bets instead of rescuing them, which matters *more*, not less, once nonzero sizing resumes.

## 5. Epoch scope

`risk.py::evaluate_forecast()` is shared, unconditional code — every band (T1/T2/T3/T4M-PROJ) calls it identically; there is no band-gate around CHECK 3/CHECK 4b (matching the `ALL_BANDS` precedent set by GG-077's boundary, which also patched shared, unconditional write-path code in `paper_trader.py::open_position()`). `logic_epoch.py` epoch 10 (`resolving_gap="GG-142"`) is recorded with `bands_affected=frozenset({ALL_BANDS})`.

## 6. Verification

`tests/test_c4_risk.py`: `test_full_no_approval_flips_probabilities` corrected (previously asserted approval for `edge=-0.15` on a NO bet — encoded the bug as expected behavior; now uses the correctly-signed `edge=0.15`). Added `test_negative_directional_edge_rejected` (negative directional edge, any direction, must be REJECTED with `insufficient_edge`), `test_direction_edge_sign_inconsistency_rejected`, and `test_direction_edge_sign_consistent_no_still_approved` (CHECK 4b positive/negative cases). Full suite run: zero new failures versus pre-fix baseline (16 pre-existing failures, all attributable to ADR-0048's R1 zeroing of `KELLY_T4`/`kelly_fraction` and an unrelated `exp015` EV-formula issue, confirmed via `git stash` differential run — identical failure set with and without this change).
