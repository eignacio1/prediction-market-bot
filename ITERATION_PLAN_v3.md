# Iteration Plan v3 — Post-Protocol: Diagnose the Anti-Predictive Signal + Pay Down Readiness Debt

**Author:** analytical-copilot, 2026-07-12. **IDs assigned T-344–T-350** (max in use T-343, GG-108→ new GG-112+). Reserve via `claim_session.sh`; re-check highest-in-use first (has drifted before).

**Origin:** session-open adversarial protocol, run after a week of edge-strategy focus. Infra clean (stubs 0, doc-debt 0, limits ADR-traced, T-336 anchor green). But the scan surfaced that the *active* band's edge is anti-predictive on clean data, sample is far from adequate, and pre-capital readiness slipped. This plan pivots from building tooling to **explaining GG-105 and closing safety gaps**.

**Principle:** DONE = test-backed (failed-before), reproducible from clean checkout, audit-trailed. Diagnose before fixing.

---

## Window 1 — Root-cause GG-105 (TOP PRIORITY; diagnose, do not fix)
### T-344 — GG-105 decomposition — ✅ DONE 2026-07-12
- **Do:** Decompose T4M-PROJ's significant, tercile-monotonic ANTI-PREDICTIVE edge→win-rate relationship (clean data). Test candidate mechanisms: (a) real signal-inversion, (b) fee/edge-frame artifact (chain to GG-020/GG-077), (c) flat-sizing artifact, (d) model miscalibration.
- **Exit:** memo naming the mechanism + which is ruled out; NO recalibration ADR yet.
- **Note:** uses current clean data — does NOT wait for more sample; pattern already significant.
- **Result:** (a)/(c) ruled out, (b) found a real but non-causal bug (GG-113, OPEN — correcting it strengthens the anti-predictive pattern, doesn't explain it), (d) model miscalibration/overconfidence is the leading mechanism. See `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T344_GG105_DECOMPOSITION_MEMO.md`, `DECISION_LOG.md` 2026-07-12.

## Window 2 — Verify edge-math foundations (feeds W1; parallel OK)
### T-345 — GG-020 fee verification — ✅ DONE 2026-07-12
- **Do:** Reconcile Kalshi 0.07 taker fee against real transaction receipts. If wrong, re-derive `fee_net_edge` and re-run the GG-105 test on corrected fees.
- **Exit:** fee confirmed or corrected; statement on whether the anti-predictive signal survives a correct fee.
- **Result:** fee rate itself unverifiable this pass (Kalshi fee docs still 429/302-blocked); clarified GG-105's driver is vig-*handling* (GG-113), not the fee *rate*. Fee-rate verification remains a separate open item. See `DECISION_LOG.md` 2026-07-12.

## Window 3 — Readiness debt (independent, parallelizable) — NOT STARTED
### T-346 — GG-092: write missing CRITICAL incident runbooks (FM-01/02/05/07)
### T-347 — GG-093: re-expand threat model for live Kalshi RSA-credential reality
- **Exit each:** artifact exists, reviewed; gap flipped RESOLVED. Pre-G6 obligations regardless of edge outcome.
- **Status:** not picked up by any session as of 2026-07-12 — no matching DECISION_LOG entries. Still open, still pre-G6 obligations.

## Window 4 — Housekeeping the protocol surfaced (low-context filler) — ✅ ALL DONE 2026-07-12
### T-348 — GG-107: commit/retire stale iteration-plan files in `main`; reconcile ID collision — ✅ DONE
- File-hygiene portion closed (both stale files retired to `11_MEMORY_HANDOFF/`). GG-107 itself stays OPEN — structural root cause (no collision check) unaddressed, recurred twice (GG-109→110, GG-111→112).
### T-349 — GG-096 (log ST-006 into SENSITIVITY_STRESS_TESTS.md) + GG-098 (stop citing T1 aggregate EV as milestone) — ✅ DONE
- GG-096 RESOLVED (doc updated with real evidence). GG-098 verified clean across 4 doc surfaces, left OPEN by design (pre-registered watch item).
### T-350 — Reconcile GG-078 vs T-342: confirm the T4 flat MC is framed short-horizon (~15-day kill fate), not a misleading long-horizon projection — ✅ DONE
- Finding did NOT confirm the stated premise: flat-mode risk accumulates gradually across the full year, structurally different from GG-078's proportional-sizing ~15-day finding — the two model different sizing regimes, not the same one restated. Caveat added to `mc_forward_projection.py`'s live report output; GG-078 cross-referenced. Both stay OPEN. See `DECISION_LOG.md` 2026-07-12.

## Also (not a task — do in the next real terminal)
- **Step 4 operational health**: SSH VPS, check T1/T4 cron liveness, `SemanticFloorViolation`, `CONTAMINATION_HALT`. Unverified this session (sandbox has no VPS access).

## Still gated (unchanged)
- GG-105 Component A tercile re-run (14-day epoch aging); T-343 recalibration (clean_n ≥ n*, ~months). Not pulled forward.

## Sequencing
W1+W2 together (W2 feeds W1). W3 fully parallel. W4 filler. Do NOT jump to recalibration before T-344 names the mechanism.

## Assumptions | Risks | Validation | Confidence
- **Assump:** GG-105 significance as logged (not re-run this session). **Risk:** tuning GG-105 away before diagnosing fee/frame artifact — W1/W2 ordering guards it. **Validation:** each window ends green + committed; VPS Step-4 owed. **Confidence:** HIGH on scan; GG-105 mechanism genuinely open.
