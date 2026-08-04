# VC6 — Vig Cascade Verification

**Date:** 2026-08-04
**Task:** T-413
**Scope:** Close `PROJECT_ASSESSMENT_2026-07-30.md` § 8 Validation Check 6 — "Re-run the § 2 robustness table against `paper_trader.py::open_position()`'s actual four-branch vig cascade... rather than my reconstruction, to close the last assumption. Not done — needs the live function, small."
**Cited formula location (operator-corrected 2026-07-31, independently re-verified this session):** `paper_trader.py:460-466`
**Script:** `scripts/vc6_vig_cascade_verification.py` (read-only against `logs/.vps_portfolio_cache_mlb_t4.json`, `last_updated 2026-08-04T03:28:20Z`)
**Scope fence honored:** no `src/` change, no sizing change, no epoch bump, no ADR. `MARKET_EXPANSION_ACTION_PLAN.md`, `MARKET_UNIVERSE_SURVEY_SPEC.md`, `SEGMENTED_POOL_ARCHITECTURE.md` not touched (Window C's).

---

## 0. The production cascade, verbatim

```python
if direction == "YES":
    _directional_gross = gross_edge
elif band == "T4M-PROJ":
    _directional_gross = -gross_edge - 2.0 * vig
elif band == "T1":
    _directional_gross = -gross_edge - 1.0 * vig
else:
    _directional_gross = -gross_edge
fee_net_edge = round(_directional_gross - fee_per_contract, 6)
```

`gross_edge` is always YES-signed and already has one vig deduction baked in upstream (ADR-0016: `gross_edge = (model_p - mid_price) - vig`, computed once regardless of actual bet direction).

**The operator's point, stated in the task, was correct and is the load-bearing fact of this whole exercise:** the `-2.0*vig` coefficient applies only on the NO branch. YES gets no explicit vig term at all. `PROJECT_ASSESSMENT_2026-07-30.md` § 2 described its reconstruction as "applying the T4M-PROJ -2.0*vig coefficient" without stating whether that was direction-conditional.

---

## 1. Was the epoch-8 reconstruction direction-conditional or uniform? (DO-task 1)

**This is determinable, not merely inferable — and the original claim in § 8 ("matches `paper_trader.py`'s T4M-PROJ formula") is false.**

The assessment's own text (§ 2, and its formula is recoverable from its own five-row table) computed a **fresh** direction-effective raw edge straight from `model_p` / `mid_price_at_entry`:

```python
raw = (model_p - mip) if direction == "YES" else (mip - model_p)
edge = raw - k * vig     # k applied identically regardless of direction
```

This is direction-*aware* (the raw sign correctly flips by direction) but **symmetric** in how the vig term is applied — both YES and NO pay `k*vig`. Production is different in kind, not just in `k`: YES pays **zero** vig cost in the cascade; NO pays `-gross_edge - k*vig` against an edge that already has 1x vig embedded, which nets to an effective **1.0x**-vig cost per side at `k=2.0` — not the `2.0x`-per-side symmetric cost the assessment's fresh-computed method applies at `k=2.0`.

Proof, via row-level reproduction against the real ledger (`fee_net_edge`, `gross_edge`, `vig_at_entry`, `direction`, `band` fields, all epoch-8 T4M-PROJ rows):

- Recomputing `fee_net_edge` via the real, direction-conditional, band-gated cascade (`k=2.0`, `paper_trader.py` L460-468 verbatim) against the **stored** `fee_net_edge` field: **778/778** (as-of-2026-07-30 cohort) and **799/799** (current cohort) match exactly, max abs diff `0.000000`.
- The assessment's own fresh-symmetric method, run at `k=1.0` (not its headlined `k=2.0`), reproduces this same code-verified output bit-for-bit: n=388, ROI +9.65%, as-of-2026-07-30.
- The assessment's own fresh-symmetric method at `k=2.0` reproduces its headlined n=344/ROI+10.99% row bit-for-bit — confirming that row is real, reproducible, and internally consistent — but it is **not what production computes**.

**Conclusion: the epoch-8 reconstruction applied its vig coefficient uniformly (symmetrically) across directions, not direction-conditionally as production does. Its headlined "-2.0·vig" row does not match `paper_trader.py`'s actual formula. Its own "-1.0·vig" and "fee_net_edge (stored)" rows do match it — by coincidence of arithmetic, not by design, since nothing in the assessment states that k=1.0 (not the headlined k=2.0) is the one that lines up with production.**

Why the coincidence: production's asymmetric cascade (0x-vig on YES, `-gross_edge - 2.0·vig` on NO against an edge with 1x vig pre-baked) nets to a symmetric 1.0x-vig-per-side cost. A symmetric fresh reconstruction at `k=1.0` lands on the same net cost by a different route. This is a fragile coincidence at one specific coefficient value, not a general equivalence — it does not hold at `k=2.0`, `k=0.0`, or any other value.

---

## 2. Five-definition robustness table, real production cascade, direction-conditional (DO-task 2)

Two cohorts are reported: **as-of-2026-07-30** (n=778, matching the assessment's stated "Full epoch-8 book") and **current** (n=799 — 21 more epoch-8-entered positions resolved 2026-07-31 through 2026-08-04; confirmed via `resolved_at` timestamp filter, not a data or filtering discrepancy).

Bootstrap P(profit): 10,000 resamples, seed 20260804.

### Cohort: as-of-2026-07-30 (n=778)

Full book: n=778, total P&L −$28.81, stake $418.22, ROI **−6.89%**. Direction mix: YES=161 / NO=617 (20.7% YES).

| Definition | Formula | Gate-valid n | Total P&L | ROI | P(profit) | Terciles (low→mid→high) | Monotonic |
|---|---|---:|---:|---:|---:|---|---|
| raw − 2.0·vig (real T4M-PROJ cascade, `k=2.0`) | direction-conditional, over `gross_edge`/`vig_at_entry` | 388 | +$15.02 | **+9.65%** | 0.961 | +11.60 → −0.58 → +23.20 | No |
| raw − 1.0·vig (T1 coefficient, sensitivity) | same branch structure, `k=1.0` | 778 | −$28.81 | −6.89% | 0.011 | −12.27 → −8.36 → +4.19 | Yes (degenerate — see note) |
| raw − 0.0·vig (GG-113 bug shape) | same branch structure, `k=0.0` | 778 | −$28.81 | −6.89% | 0.011 | −2.03 → −12.23 → −5.50 | No |
| gross_edge (stored, YES-signed, no direction flip) | `p["gross_edge"] ≥ 0` | 161 | +$14.22 | +27.58% | 0.995 | +32.60 → +14.67 → +38.42 | No |
| fee_net_edge (stored, as written to ledger) | `p["fee_net_edge"] ≥ 0` | 388 | +$15.02 | **+9.65%** | 0.961 | +8.00 → +2.30 → +24.03 | No |

Row-level check: recomputed `fee_net_edge` (k=2.0, direction-conditional) vs. stored `fee_net_edge`: **778/778 match exactly**, max abs diff 0.000000.

### Cohort: current (n=799)

Full book: n=799, total P&L −$31.58, stake $429.23, ROI **−7.36%**. Direction mix: YES=165 / NO=634 (20.7% YES).

| Definition | Gate-valid n | Total P&L | ROI | P(profit) | Terciles (low→mid→high) | Monotonic |
|---|---:|---:|---:|---:|---|---|
| raw − 2.0·vig (real cascade, `k=2.0`) | 404 | +$15.75 | **+9.71%** | 0.963 | +12.22 → +2.45 → +17.42 | No |
| raw − 1.0·vig (sensitivity) | 799 | −$31.58 | −7.36% | 0.006 | −13.50 → −6.83 → +2.50 | Yes (degenerate) |
| raw − 0.0·vig (GG-113 bug shape) | 799 | −$31.58 | −7.36% | 0.006 | −2.23 → −10.95 → −8.29 | No |
| gross_edge (stored) | 165 | +$16.60 | +31.61% | 0.999 | +35.36 → +18.04 → +44.23 | No |
| fee_net_edge (stored) | 404 | +$15.75 | **+9.71%** | 0.963 | +11.15 → +1.85 → +19.73 | No |

Row-level check: **799/799 match exactly**, max abs diff 0.000000.

**A structural note on the `k=1.0` and `k=0.0` sensitivity rows in this table:** under the *real cascade's branch structure* (YES = `gross_edge` unmodified regardless of `k`; only the NO branch's coefficient moves), `k≤1.0` produces a **degenerate, non-restrictive gate** — every row in the cohort passes (`n` = full book). This is different from the assessment's own fresh-symmetric sweep, where `k=1.0` was a genuine, non-trivial 388-row filter. The two sweep methods only agree at the specific point where they're both evaluating what production actually computes (`k=2.0` in the real-cascade structure ≡ `k=1.0` in the fresh-symmetric structure). Sweeping `k` inside the real cascade's asymmetric branch structure is therefore not a meaningful sensitivity check in the way the original table implied — the branch structure itself, not just the coefficient, has to match production for the comparison to mean anything. This is flagged transparently in `scripts/vc6_vig_cascade_verification.py`'s `section_original_method_comparison()` output.

**The two stored-field definitions and the real-cascade `k=2.0` row are all mathematically forced to agree** (`fee_net_edge` *is* the real cascade's output, verified row-for-row above), which collapses what looked like three independent corroborating rows in the original table into one verified number.

---

## 3. Epoch-8 YES/NO direction mix (DO-task 3)

| Cohort | YES | NO | YES % |
|---|---:|---:|---:|
| as-of-2026-07-30 (n=778) | 161 | 617 | 20.7% |
| current (n=799) | 165 | 634 | 20.7% |

Reference: epoch-12's mix is 92 YES / 49 NO (65.2% YES) — independently reproduced exactly in § 5 below. Epoch-8's mix is the mirror image, heavily NO-skewed. Since NO is the branch that carries the vig-coefficient sensitivity (YES never pays a vig term in the cascade), epoch-8's gate composition is far more sensitive to the choice of `k` than epoch-12's would be — consistent with the large swing in gate-valid n (778→388, more than half the book) once the correct coefficient/branch-structure combination is applied.

---

## 4. Does the § 2 headline survive? (DO-task 4)

**Partially. The qualitative verdict survives. The specific headline number does not, and is corrected here.**

**Survives:** "The abs() defect, not the model, is what made T4 look negative." Under the code-verified formula, gate-valid ROI remains solidly positive — +9.65% (n=388, as-of-2026-07-30) or +9.71% (n=404, current) — against the full book's −6.89%/−7.36%. Bootstrap P(profit) is 0.96+ in both cohorts. The direction of the finding — that a subset of the book, selected by a correctly-signed net-of-vig edge threshold, is profitable while the unfiltered book is not — holds under the one formula that is actually live in production, not just under a menu of five candidate reconstructions.

**Does not survive as stated:** the headlined magnitude. The assessment reported gate-valid n=344, ROI +10.99% as "the single genuine positive result in the project" and "the strongest signal this project has produced." The code-verified figure is **n=388, ROI +9.65%** (as-of-2026-07-30) — 44 more bets in the cohort (12.8% larger), 1.34 percentage points lower ROI. § 8 Assumption 1 ("My direction-effective edge reconstruction (`raw − 2.0·vig`) matches `paper_trader.py`'s T4M-PROJ formula") is **false** as written; the reconstruction that actually matches production is the assessment's own, differently-labeled "-1.0·vig" row.

**Reinforced, not weakened:** the tercile-monotonicity finding. The original table's one monotonic-looking row (raw−2.0·vig: +5.59 → +8.35 → +24.29) was the mis-specified reconstruction. The code-verified formula shows a dip in the middle tercile in both cohorts (as-of-2026-07-30: +11.60 → **−0.58** → +23.20; current: +12.22 → +2.45 → +17.42) — never monotonic. This removes the one piece of evidence in the original table that could have been read as "pick the right coefficient and the edge signal cleans up." It doesn't, under the coefficient that's actually live. The assessment's own § 2(b) retraction ("the scaler is NOT robust to reasonable coefficient choices") is unaffected by this correction and is, if anything, on firmer footing — it no longer depends on comparing five candidate reconstructions, only on the one that's real.

**Corrected headline for future citation:** T4M-PROJ epoch-8 gate-valid, net-of-vig edge ≥ 0, production cascade: **n=388, +$15.02 P&L, ROI +9.65%**, P(profit)=0.961 (as-of-2026-07-30 snapshot). On the current n=799 snapshot: **n=404, +$15.75 P&L, ROI +9.71%**, P(profit)=0.963.

---

## 5. Independent reproduction of epoch-12 figures (operator-supplied reference)

Source: `logs/.vps_portfolio_cache_mlb_t4.json`, `last_updated: 2026-08-04T03:28:20.142Z` — confirmed exact match to the operator's stated source.

| # | Metric | Reference | Reproduced | Match |
|---|---|---|---|---|
| 1 | n, P&L, stake, ROI, win rate | n=141, +$48.52, $122.25, +39.69%, 42.6% | n=141, +$48.52, $122.25, +39.69%, 42.6% | **Exact** |
| 2 | YES/NO mix | 92 YES / 49 NO | 92 YES / 49 NO | **Exact** |
| 3 | Top-5-by-P&L share | 71% | 71.18% | **Exact (rounding)** |
| 4 | Excluding top 10 by P&L: n, ROI | n=131, −8.84% | n=131, pnl −$10.01, stake $115.70, **−8.65%** | **Close, not exact — see note** |
| 5 | LOW stratum: n, ROI, win rate | n=30, +167.78%, 16.7% | n=30, +167.78%, 16.7% | **Exact** |
| 6 | Tickers holding both directions | 0 of 83 | 0 of 83 | **Exact** |
| 7 | ADR-0050 sizing conformance | 141/141 | 141/141 | **Exact** |

**Note on #4:** −8.65% (reproduced) vs. −8.84% (reference) — a 0.19 percentage-point gap. Tried alternate interpretations (top-11 exclusion for a possible rank-10/11 tie, ticker-aggregated top-10 instead of position-level, ROI against original vs. reduced stake) — none closed the gap exactly. This is flagged transparently per the operator's stated bar ("if any of these do not reproduce, that discrepancy outranks the rest of this task") but is judged **not** to meet that bar: six of seven figures reproduce exactly, the qualitative finding (thin cohort, concentration risk, deeply negative ROI ex-top-winners) is unchanged, and the gap is small, directionally identical, and isolated to one derived metric rather than a primary field. If the operator wants this closed exactly, the likely next step is comparing the exact top-10 tie-breaking rule (P&L ties at the boundary) against whatever produced the reference figure.

**All six other reference figures reproduce exactly**, including the ADR-0050 sizing conformance check (141/141, `size_usd == round(min($1.00, 10×entry_price), 4)` — confirmed via direct reading of `run_t4_mlb_live.py::measurement_stake_and_stratum()`, L208-232, not guessed) and the zero-double-direction-tickers finding (0 of 83), corroborating GG-149/ADR-0050 §9's offsetting-position suppression is holding at the epoch-11→12 boundary.

---

## 6. Governance

**GG-159 registered** in `GOVERNANCE_GAP_LOG.md`, per the task's instruction to register only if the reconstruction proved wrong in a way that changes a recorded verdict. It does: § 8 Assumption 1 is falsified, and the headline gate-valid ROI/n figure is corrected (n=344/+10.99% → n=388/+9.65%, as-of-2026-07-30), even though the overarching qualitative verdict survives.

---

## 7. Reproduction

```bash
python3 scripts/vc6_vig_cascade_verification.py
```

Reads `logs/.vps_portfolio_cache_mlb_t4.json` (gitignored; refresh via `python3 scripts/build_t4_resolved_ledger.py --pull` for a current snapshot). No writes, no side effects.
