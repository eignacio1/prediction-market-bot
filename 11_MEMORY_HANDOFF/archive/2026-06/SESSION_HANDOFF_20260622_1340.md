# Session Handoff — 2026-06-22T13:40Z

**Trigger:** Operator-initiated (session end)
**Last commit:** `649eab7` (main) — **NOT YET committed/pushed this session** (working tree dirty; see Step 5 commit draft)

---

## Status

- **Phase:** 6/7 ACTIVE (paper trading HALTED at drawdown kill switch)
- **Tests:** 999/999 passing (was 988; +11)
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — cron DORMANT (dark period); HEAD `97e66ae` unchanged (no deploy this session)
- **Paper bets:** 158/30 resolved — G6 count satisfied; **positive-P&L gate FAILING** (−$248.90, 24.9% drawdown); GG-004 commercial-validation blocker OPEN

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| **ADR-0029 ACCEPTED — Tier A frozen, Tier B provisional** | DS sign-off recorded (Earl Ignacio). Two-tier acceptance reconciles hard rule #3 (ADR immutability) with the fact that sub-band rosters/numerics/alpha hypotheses are unvalidated: Tier A (architecture, principles, mechanisms, gate structure, ≤5s kill-switch req) is frozen; Tier B (roster, ALL numerics, alpha hypotheses) stays DECISION_LOG-revisable until each sub-band's Phase 8 Activation Gate. | ADR-0029 (ACCEPTED); DECISION_LOG S67 sign-off entry | DS |
| **Aggregate-parent retained** — `T4_IN_PLAY` stays as the budget/risk unit; 10 sub-bands route beneath it | Blast-radius: strategies C/E/G/H/K + ADR-0013 `T4_BAND_WEIGHT=0.27` all reference the aggregate; faithful to Tier A 'shared pool + caps' mechanism; minimal breakage | DECISION_LOG S67 scaffold entry; `execution_bands.py` | EL |
| **Tier B encoded in code, not just prose** — `T4SubBandSpec` + `T4_SUBBAND_REGISTRY` (all `status="BLOCKED"`) + `validate_t4_subbands()` invariant | Provisional governance metadata (Kelly, EXP gate, exposure cap, falsifiable alpha hypothesis) must be machine-checkable and enforce all-BLOCKED so no sub-band can go live without an activation ADR | DECISION_LOG S67 scaffold entry | EL |
| **`NOISE_BUFFER_BAND_T4=0.19` kept as aggregate default** (not split away) | It feeds the LIVE exit path in `run_t4_live.py` and is assert-pinned in two test files; per-sub-band buffers added only where ADR-0029 specifies, else `None`→fallback | DECISION_LOG S67 scaffold entry | EL |
| **Strategy K NOT redefined** — held at aggregate, overlap logged OPEN | Its `execution_scalp` identity overlaps the T4-MICRO carve-out (ADR-0030); whether K re-homes to ADR-0030 or re-scopes onto model_p sub-bands is an unresolved strategy-level governance question | DECISION_LOG S67 scaffold entry; `execution_bands.py` Strategy K note | EL |

*Kelly tail-calibration constraint enforced in code:* T4-PROJ provisional Kelly = 0.167 (NOT 0.25); T4-ARITH 0.22 placeholder held non-operational at 0.167; test locks `proj_kelly ≤ 0.167 < 0.25` (EXP-PROJ-01 / EXP-ARITH-01 pending).

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| ADR-0029 DS sign-off | ✅ ACCEPTED — status header + Accepted line; propagated to ADR-0028 notice, DECISION_LOG index + chronological entry |
| T-180 scaffold (`execution_bands.py`) | ✅ 10 sub-band enum + BandConfig; `T4_SUBBANDS`/`is_t4_subband()`/`t4_parent()`; per-sub-band NOISE_BUFFER; `T4SubBandSpec`+`T4_SUBBAND_REGISTRY`+`validate_t4_subbands()`; Strategy K + Kalshi venue notes |
| `tests/test_execution_bands.py` | ✅ rewrote 5-band assertions for aggregate+sub-band structure; added `TestT4SubBandRegistry` (6 invariant tests). +11 net → 999/999 |
| DECISION_LOG (rule #7) | ✅ sign-off entry + 4 scaffold design-decision entries |
| Nav artifacts | ✅ MEMORY_BANK / TODO_NEXT / PLAN updated |

---

## ONE THING PENDING

**Commit + push the working tree, then (per memory) attempt VPS deploy — BUT note cron is dormant (dark period) and T4 is BLOCKED, so the deploy is a no-op for live behavior.** Working tree has 6 modified files + 1 new (`ADR-0030`). Nothing is live-affecting: all T4 sub-bands are `status="BLOCKED"`, `requires_realtime=True`, Phase 8 — the paper book stays HALTED at the 25.12% drawdown kill switch regardless.

**Next substantive build (remaining T-180), only if Earl directs:** scaffold `t4_execution_engine.py` — the Layer 1 Continuous Evaluation + Layer 2 staleness-arbitrated execution queue. **This is the substance of Tier A** (the ~1,000-eval/game routing engine, hard rule #9); the enum/config landed this session is only plumbing. Also pending: `t4_price_cache.py` (GG-039), C7 ≤5s fast-halt design (GG-038, ADR required), real-time data feed (GG-040).

---

## Current Paper Portfolio

- Bankroll: $751.10 — 24.9% realized drawdown
- Open: 0 ($0.00 deployed)
- Resolved: 158 | G6 count gate satisfied (≥30); **positive-P&L gate FAILING** (P&L −$248.90)
- Book HALTED at drawdown kill switch (25.12% > 20%)

---

## Active Cron on VPS (157.230.91.33)

DORMANT — dark period (post-NBA-Finals). No live betting. MLB activation targeted Aug–Sep per DARK_PERIOD_PLAN.md Phase 3.

---

## Key Constraints to Remember

1. No live capital until G6 (**30 resolved paper bets + positive P&L** + DS sign-off ADR-0005 — APR-0016). Count met; P&L gate FAILING; GG-004 commercial-validation OPEN (the binding blocker).
2. **ADR-0029 Tier A is now frozen/immutable** (hard rule #3) — changes require a superseding ADR. Tier B (roster/numerics/alpha hypotheses) is DECISION_LOG-revisable per-sub-band until Phase 8 Activation Gates — NOT a superseding ADR.
3. T4 sub-bands are all BLOCKED/Phase 8 — the scaffold is structural only; no execution path exists yet.
4. INVARIANT: derive P&L/drawdown from `closed_positions`/C6 audit log, never JSON scalars on books written before HEAD `52607f2`.
5. Strategy K vs T4-MICRO (ADR-0030) overlap is an OPEN governance question — do not silently redefine K.

---

## NEXT SESSION PRIMER

ADR-0029 Tier A is frozen (DS-signed S67) and the `execution_bands.py` T4 sub-band scaffold has landed (999/999 tests) — but that is only enum/config plumbing. Read `11_MEMORY_HANDOFF/MEMORY_BANK.md` S67 DELTA, then `04_EXECUTION/TODO_NEXT.md` T-180. The immediate next build (if Earl directs) is `t4_execution_engine.py` — the Layer 1 Continuous Evaluation + Layer 2 staleness-arbitrated queue skeleton, which is the actual substance of Tier A (~1,000 evals/game, hard rule #9). All T4 remains BLOCKED/dark; no live behavior changes.
