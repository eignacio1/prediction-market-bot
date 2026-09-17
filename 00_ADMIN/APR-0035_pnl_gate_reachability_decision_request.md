# APR-0035 — Is APR-0024's per-band P&L `n*` reachable within a practical horizon? (GG-285)

**Status:** DECISION REQUEST — not adjudicated at drafting time; presented options, did not select one.
**Touches (if accepted):** APR-0024 (superseding required regardless of option chosen, per Hard Rule 3 — ADRs/APRs are immutable, changes require a superseding document) and possibly ADR-0057 (in force, unaffected by this draft itself). No gate, threshold, or pre-registered verdict is changed by this document.
**Drafted:** 2026-09-17, T-554/GG-285.
**Prior context:** APR-0024 (ACCEPTED) sets the standard: `clean_n ≥ n*`, `n*` variance-derived live per band (95% power, α=0.05, one-sided, `scripts/run_power_calc.py`). EXP-027/HYP-012's 2026-09-15/16 re-run (T-550) returned `clean_n=14` against `n*=2610.35`, verdict `UNDERPOWERED` — unmodified by this document. Full supporting analysis: `05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T554_nstar_wall_analysis.md` (this session).

---

## The gap

APR-0024 correctly replaced ADR-0024's flat 30/150/500 heuristic with a variance-derived standard — a real methodological improvement, and this document does not question that improvement. What has not been stated in writing anywhere prior to this session is what that standard actually costs in calendar time at the effect sizes the system has actually measured. The answer, computed fresh this session from live data:

- **T4M-PROJ** (the bot's one operating cell): `n*=8,587`, `clean_n=765`, measured cadence 198.4 clean bets/week ⇒ **≈1.6–1.7 MLB seasons** of continuous cadence to reach `n*` at all — before any consideration of whether the sign/magnitude of the edge survives that long.
- **NFL moneyline** (EXP-027/HYP-012, the newest active cell): `n*=2,610.35`, `clean_n=14`, ⇒ **≈11 NFL seasons ≈ 11 elapsed calendar years** at the observed clean rate.
- **T1/T2/T3:** `clean_n<2` — no variance estimate exists at all; these cells have no computable wall, which is worse than a distant one.

Both signals share the same structural cause: **sd/mean ratio of 15.5x (NFL) to 28.2x (T4M-PROJ)**. P&L-per-bet carries payoff variance (win pays a multiple of stake, loss forfeits stake) on top of forecast error, which is what produces these ratios — not a flaw in the gate's math, a property of what the gate measures. Full derivation and the calibration-vs-P&L sample-size comparison (showing Brier/ECE are already informative at `n=284` for NFL, where P&L needs `n*=2,610`) are in the linked analysis file.

**If every cell with a measurable wall requires single-digit-to-double-digit years of uninterrupted cadence to clear `n* ` on P&L alone, then G6 cannot close on P&L evidence within any practical operating horizon as the gate is currently written — and the ~25-cell coverage target (`COVERAGE_TARGET_MATRIX.md`) compounds this, since each new cell starts its own multi-year P&L clock from `clean_n=0` on activation.** This is not a new fact discovered this session — every number above was already computable from data the system already had (`run_power_calc.py` and EXP-027's own result file) — but nobody had stated the implication in writing before now, which is the entire reason this APR exists.

---

## What this document does not do

This is analysis and a decision request. It does not: change `n*`, `alpha`, `power`, any gate threshold, or any pre-registered verdict; relabel EXP-027's `UNDERPOWERED` verdict; touch `kelly_fraction`/sizing, promote a cell, submit an order, or settle a position. EXP-027 stands exactly as T-550 recorded it.

---

## Options (presented, not selected)

**Option 1 — Keep the P&L gate exactly as APR-0024 defines it, and accept the horizon.** No superseding document required; this is the null option. Cost: explicit, in writing, that G6 does not close on P&L evidence for any current cell within a practical timeframe, and that the coverage-target expansion (moneyline, run line, totals, spread across five bands) inherits the same wall for every new cell it adds. This option is honest about the cost but does not change anything about whether the operator is comfortable carrying it.

**Option 2 — Add a calibration-based interim gate for cell *promotion* (research → paper-trading-with-expanded-scope, or similar), while P&L stays the sole gate for authorizing live capital.** Brier/ECE are already informative at sample sizes P&L cannot reach for years (n=284 for NFL's 2025 backtest vs. n*=2,610 for P&L) — this option would let a cell's calibration read qualify it for continued/expanded paper-trading investment (more archiving, more coverage-target cells opened) without waiting out P&L's wall, while G6's live-capital gate remains untouched at `clean_n ≥ n*` on P&L. **Requires a superseding APR to APR-0024** (to add a second, lower-stakes gate class distinct from the live-capital gate) and does not touch ADR-0057. This is the option Deliverable 2's calculation was built to support, without itself selecting it.

**Option 3 — Re-derive `n*` under a different power/alpha.** APR-0024's 95%/α=0.05/one-sided parameters are a conservative, standard choice, but not the only defensible one. Lowering power (e.g. 80%) or loosening alpha would shrink `n*` — by how much would need to be computed per cell before this option could be evaluated concretely; it is named here as a candidate, not analyzed, because doing so is itself a gate-parameter change this task's DO NOT list explicitly forbids performing in-session. **Requires a superseding APR to APR-0024** (the standard itself defines these parameters) and operator sign-off, since it changes what "adequately powered" means system-wide, not just for one cell.

**Option 4 — Something else the analysis surfaces, not enumerated above** — e.g., a hybrid where different bands carry different power/alpha targets based on their own cadence economics (T4M-PROJ's ~1.6-season wall is a fundamentally different proposition than NFL's ~11-season wall, and a single system-wide standard may not fit both well). Not developed here; flagged as a live possibility for the operator to raise if none of Options 1–3 fit.

---

## Not decided here

This document does not choose among the options above, does not amend APR-0024's text, and does not touch `COVERAGE_TARGET_MATRIX.md`'s expansion sequencing. Per Hard Rule 11, resolving this is out of scope for T-554 — registered and stopped here for the operator, consistent with APR-0033's precedent for this exact "present options, do not select" pattern.
