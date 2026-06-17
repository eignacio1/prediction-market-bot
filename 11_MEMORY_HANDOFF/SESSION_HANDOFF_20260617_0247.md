# Session Handoff — 2026-06-17T02:47Z (SESSION 64)

**Trigger:** Operator-initiated — "Commit and deploy - then session end."
**Last commit:** `897ff4d` (main) — pushed to GitHub + deployed to VPS (HEAD `897ff4d`)

---

## Status

- **Phase:** 6/7 ACTIVE — dark period open (Knicks won the Finals)
- **Tests:** 988/988 passing
- **Capital:** NO live capital — paper trading only
- **VPS:** 157.230.91.33 — HEAD `897ff4d`, calibration verified live (NBA 0.97→0.845, MLB identity)
- **Paper bets:** 117 resolved (≫ 30-bet numeric floor) — but the **binding G6 blockers are GG-004 (EXP-017 commercial validation) and T-148/T-177 (no demonstrated alpha)**, NOT the count. **G6 P&L gate is FAILING** (true drawdown 25.12%; book halted at the kill switch).

---

## ⚠️ STRATEGIC DECISIONS THIS SESSION

| Decision | Rationale | Canonical Reference | Owner |
|----------|-----------|--------------------|----|
| Apply temperature calibration to the **production Poisson probability**, not the LR+Platt model | The production T1 betting prob is `1 − Poisson_CDF` (ADR-0015), not `prod_model.joblib` (which only logs `p_estimate_lr`). Re-fitting Platt would have been a no-op on live behavior. Root cause of overconfidence = Poisson assumes var=mean but NBA scoring is over-dispersed. | ADR-0027 / APR-0021 | DS (operator directive) |
| NBA T = 2.05 (OOS-validated), not the in-sample optimum 3.10 | OOS fit (G2–G4) tested on G5 generalizes (G5 Brier 0.315→0.282); more conservative/defensible on a single-series n=158 sample. Provisional under ADR-0024 — re-derive on adequate sample at G6. | ADR-0027 §"Why T=2.05" | DS |
| Per-sport calibration registry with **fail-safe identity T=1.0** for unknown sports | Launching MLB must not silently inherit NBA's shrink. Directly serves "fix nodes before MLB." | `calibration.py` `DEFAULT_TEMPERATURE` | DS |
| **RECORD: recalibration DISPROVED the miscalibration hypothesis** | After calibration the edge is still anti-predictive (edge>0 winrate 0.356 vs edge≤0 0.747; top tercile 0.346 vs bottom 0.792). Calibration is a correctness fix, NOT evidence of profitability. GG-037 alpha half + GG-004 stay OPEN. | ADR-0027 §Consequences; GG-037; DECISION_LOG S64 | DS |
| C4 portfolio free-cash invariant: two-tier (8a solvency KILL, 8b 60%-of-equity REJECT) | GG-035 over-leverage ($1003.38 = 100.3% of initial deployed). 60% = `1−RESERVE_MANDATE_PCT` — no new free parameter; reserve promoted advisory→enforced. Base = equity (stricter underwater). | ADR-0026 / APR-0020 | DS |
| Re-froze the 158-bet NBA Finals dataset to resolve G5 (GG-036) | G5's 41 positions were unresolvable from nba_api; outcomes sourced and frozen — **NOT fabricated**. Capital unlocked; full-DB assessment ran on this set. | `data/nba_finals_clean_dataset.csv`; GG-036 | DS |

---

## Tasks Completed This Session

| Item | Result |
|------|--------|
| GG-036 — G5 resolvability | ✅ RESOLVED — re-frozen 158-bet dataset; G5 41 positions resolved (NOT fabricated); capital unlocked |
| GG-035 — over-leverage (ADR-0026/APR-0020) | ✅ RESOLVED (structural) — C4 two-tier free-cash invariant; `risk.py`, `paper_trader.py`, `tests/test_c4_risk.py` |
| GG-037 calibration half (ADR-0027/APR-0021) | ✅ RESOLVED — C3 temperature scaling on production Poisson prob; `calibration.py`, `run_paper_trade.py`, `scripts/derive_calibration.py`, `tests/test_c3_calibration.py` (14 tests) |
| Full-database assessment | ✅ COMPLETE — edge inversion confirmed survives calibration; no demonstrated alpha vs Kalshi |
| Governance closure | ✅ ADR-0026/0027 + APR-0020/0021 + DECISION_LOG S64 entries + G6 checklist (T2-A 🔴 FAILED, T2-C 🟡 masks failure) |
| Deploy | ✅ `897ff4d` pushed + VPS HEAD `897ff4d`; calibration verified live |
| Tests | ✅ 988/988 |

---

## ONE THING PENDING

**Nothing in-flight from this session — sprint is closed and deployed.** The next material decision is **T-177 (edge-inversion / no-alpha)**: the model edge is anti-predictive vs the Kalshi price even after calibration. This is now the substance of the G6 blocker (with GG-004). It cannot be resolved on the Finals data — it needs EXP-017 at scale (MLB dark period + NBA regular season). Do NOT call G6 until alpha is demonstrated.

Paper trading remains **halted at the drawdown kill switch** (true drawdown 25.12% > 20%); CHECK 2 fires before CHECK 8/calibration ever matters. The calibration and free-cash invariant are live but will only change behavior when the book is reset / a new sport starts.

---

## Current Paper Portfolio

- **Bankroll: −$254.59** (corrected, S63) — true drawdown **25.12%** (book halted at kill switch)
- `total_realized_pnl` corrected −8.46 → **−251.21** (S63/T-174); derive from `closed_positions`/C6 audit log, NOT JSON scalars
- Open: 41 G5 positions (game_date=2026-06-13), now resolvable via the re-frozen dataset (GG-036)
- Closed/Resolved: 117 | G6 count floor met, but **P&L gate FAILING** and alpha undemonstrated

---

## Active Cron on VPS (157.230.91.33)

```
21:00 UTC  — Health check
21:30 UTC  — PIPE-02 inference (run_pregame.py)
22:00 UTC  — PIPE-03 early (paper bets)
01:30 UTC  — PIPE-03 late (paper bets)
05:30 UTC  — GHA post-game resolve (actual ~09:00–09:50 UTC; treat 10:00 UTC as earliest reliable)
```
(All bet placement currently no-ops past the drawdown kill switch.)

---

## Key Constraints to Remember

1. Work wifi blocks Kalshi API — use any other network
2. No live capital until G6 (30 resolved paper bets + positive P&L — APR-0016/0017; **P&L gate currently FAILING**)
3. **INVARIANT:** derive P&L/drawdown from `closed_positions`/C6 audit log, never JSON scalars on books written before HEAD `52607f2`
4. **Production betting prob = Poisson (`run_paper_trade.py` ~543), NOT LR+Platt.** Calibration (ADR-0027) is applied there.
5. **Calibration is per-sport, fail-safe identity.** MLB T defaults to 1.0 until derived (T-176) — do NOT let MLB inherit NBA's T.
6. New-sport launch (MLB) must clear T-175 (free-cash coverage), T-176 (MLB T), T-178 (market_mapper pre-flight) — and the alpha question (T-177) governs G6.

---

## ⚙️ DECISION AUDIT

**Step 1:** `grep -rn "^\*\*Decisions logged:\*\* false" ...` → **clean** (no `decisions_logged: false` documents).

**Step 2:**

| Document | Decisions logged field | DECISION_LOG entries written | Status |
|----------|----------------------|------------------------------|--------|
| ADR-0026 | n/a (ADR) | ADR Index row + S64 GG-035 entry | ✅ |
| ADR-0027 | n/a (ADR) | ADR Index row + S64 GG-037 entry | ✅ |
| GOVERNANCE_GAP_LOG.md | n/a | GG-035/036/037 status updated | ✅ |
| APPROVALS_REGISTER.md | n/a | APR-0020/0021 added | ✅ |
| G6_GATE_CHECKLIST.md | n/a | T2-A/T2-C updated | ✅ |

---

## Resume Command

```bash
cd "/Users/earlignacio/Documents/Claude/Projects/Prediction Markets"
# Tell Claude: "Read 11_MEMORY_HANDOFF/MEMORY_BANK.md and SESSION_HANDOFF_20260617_0247.md, confirm 988 tests.
# Next: T-177 (edge-inversion/no-alpha, G6 blocker) and dark-period MLB build (T-176/T-178)."
```

---

## NEXT SESSION PRIMER

Read `MEMORY_BANK.md` (S64 delta block at the top of Current State Snapshot) and this handoff. The pre-MLB governance sprint is complete and deployed (HEAD `897ff4d`, 988 tests). The open thread is the **no-alpha finding (T-177 / GG-004)**: recalibration disproved miscalibration, so the model has no demonstrated edge vs the Kalshi market — this is the real G6 blocker. Next constructive work is the dark-period MLB build (MLB C1 data-source selection is pending operator/DS) plus T-175/T-176/T-178.
