# T-344 — GG-105 Decomposition Memo

**Date:** 2026-07-12. **Task:** T-344 (Iteration Plan v3, Window 1). **Scope:** diagnose, do not fix — no recalibration ADR this window.

**Question:** T4M-PROJ (ACTIVE, highest-volume band) shows a statistically significant, tercile-monotonic ANTI-PREDICTIVE relationship between computed edge and realized win rate on clean-epoch data (GG-105). Which mechanism drives it — (a) real signal-inversion, (b) fee/edge-frame artifact, (c) flat-sizing artifact, or (d) model miscalibration?

**Data:** freshly VPS-pulled this session (`scripts/build_t4_resolved_ledger.py --pull`), `logic_epoch == CURRENT_LOGIC_EPOCH (3)`, clean_n=412 (raw_n=656). This is larger than every prior GG-105 pass (T-324/T-329/T-332: n=271; T-333/T-341: n=338) — natural growth, not a re-derivation. The pattern **persists and has strengthened**: `scripts/run_band_monitor.py --no-c7` this session reproduces ANTI-PREDICTIVE at fisher_p=0.0464 (n_pos=389/n_neg=23, winrate_pos=0.614/winrate_neg=0.826), calibration slope b=0.600 (CI [0.419, 0.812], excludes 1.0, "overconfident") — versus T-341's p=0.0563 at n=338. More data, same or sharper signal.

---

## Headline finding: a new, real fee/edge-frame bug exists — and it does NOT explain GG-105

T-333's H5 (2026-07-11) tested whether the offline analysis tool's `compute_fee_net_edge()` (which omits vig entirely) matched the live gating formula, built a "live-parity" formula that deliberately mirrors `run_t4_mlb_live.py`'s actual sign convention, and concluded the pattern persists either way — a **tooling-parity** question, correctly resolved.

This task asked a narrower, previously untested question: is the live code's own vig handling *economically correct* in the first place, independent of whether the offline tool matches it?

**It is not.** `run_t4_mlb_live.py:952-1037`:

```python
gross_edge = p_t4 - mip - vig                     # line 952: vig baked in as a YES-frame cost
...
if gross_edge > 0.0:
    direction, directional_gross_edge = "YES", gross_edge
elif gross_edge < 0.0:
    direction, directional_gross_edge = "NO", -gross_edge   # line 1032: negates the WHOLE expression
...
directional_net_edge = directional_gross_edge - kalshi_fee
```

Negating `gross_edge = (p_t4 - mip) - vig` in full gives `directional_gross_edge = (mip - p_t4) + vig` — **vig flips from a cost to a credit** for every NO-direction bet. Compare against the codebase's own pre-existing, documented convention for vig (`run_exp017.py:41`, `"kalshi_vig: full spread (ask - bid)"`, and its bet-simulation logic):

```python
half_vig = vig / 2.0
price_paid = mip + half_vig            # YES: pay the ask, above mid
price_paid = (1.0 - mip) + half_vig    # NO:  pay the NO ask, above (1-mip) — vig is STILL a cost
```

Vig is a bid-ask spread: it is a cost of crossing the spread on *either* side, never a credit. `run_t4_mlb_live.py`'s sign flip is a genuine bug — distinct from GG-077 (the already-fixed `fee_net_edge` storage-layer sign bug in `paper_trader.py`) and distinct from T-333's H5 (a tooling-parity finding, not an economic-correctness one). It is being escalated as its own governance gap, **GG-112**, below.

**Scale of exposure:** 337/412 clean positions (81.8%) are NO-direction. Every one of them was gated on an edge inflated by `+2×vig` relative to the correct symmetric-cost treatment. Confirmed directly: recomputing edge with the live-buggy formula on the resolved ledger reproduces `n_neg=0` for all 412 rows (tautological — every resolved position cleared this exact gate by construction), while the corrected symmetric-vig formula produces `n_neg=137` (33.3% of clean_n) — real, previously-invisible negative-true-edge bets that the live gate is currently waving through.

### Does fixing it explain GG-105? No — it gets *worse*.

| Framing | n_pos | n_neg | winrate_pos | winrate_neg | Fisher p |
|---|---|---|---|---|---|
| LIVE (buggy, as-gated) | 412 | 0 | 0.626 | n/a | n/a (degenerate) |
| ANALYSIS (current tool, vig omitted) | 389 | 23 | 0.614 | 0.826 | 0.0464 |
| **CORRECTED (vig symmetric cost)** | **275** | **137** | **0.582** | **0.715** | **0.0094** |

Correcting the sign bug does not resolve the anti-predictive relationship — it makes it *more* significant (p: 0.046 → 0.0094) and reveals it spans a much larger share of the book (23 → 137 rows). **This rules out mechanism (b) as the cause of GG-105's win-rate inversion**, even though (b) is real and independently actionable (see GG-112).

---

## Ruling out compositional artifact (YES/NO base-rate mix)

Unconditional win rate differs sharply by direction: YES 44.0% (n=75) vs. NO 66.8% (n=337) — expected, since MLB hit-threshold NO bets typically price a less-than-coinflip event. Since the clean_n cohort is 82% NO, this raises the question of whether the tercile-monotonic pattern is just YES/NO mix shifting across terciles rather than a real within-direction inversion.

It is not a pure mix artifact. Under the corrected (symmetric-vig) formula, tercile win rates **within NO alone** still decline monotonically:

| NO-only tercile | n | edge range | win rate |
|---|---|---|---|
| 1 (most negative) | 112 | [-0.31, -0.02] | **70.5%** |
| 2 | 112 | [-0.02, 0.07] | 68.8% |
| 3 (most positive) | 113 | [0.07, 0.70] | **61.1%** |

YES-only (n=75, 25/tercile) is noisy and does not show a clean monotonic trend (40.0% → 48.0% → 44.0%) — consistent with T-333's prior observation that YES volume is too thin to draw an independent conclusion, but it does not contradict the NO-only finding, which carries 82% of the book and clears `MIN_N` comfortably in every tercile.

**Mechanism (c), flat-sizing artifact:** already ruled out by T-329 (size-weighted re-run showed the opposite of the compounding-risk hypothesis — avg stake *falls* with edge tercile, $-weighted return *rises*). This session's within-direction win-rate analysis is orthogonal (win-rate, not $-weighted) and consistent with the same conclusion: sizing is not implicated.

---

## Leading mechanism: (d) model miscalibration (overconfidence), not (a) sign-inversion

The within-NO tercile pattern (70.5% → 68.8% → 61.1%) has a specific shape: win rate stays **above 50% at every tercile**, including the highest-computed-edge one. A true sign-inversion (mechanism (a)) would predict win rates crossing below 50% (or below the market-implied rate) precisely where the model claims the most confidence — that is not what the data shows. Instead, the pattern is a monotonic *decay* in edge quality as claimed edge magnitude grows, which is the textbook signature of overconfidence: the model's directional call remains net-positive-information throughout, but its confidence (edge magnitude) systematically overstates true predictive strength at the tails.

This is consistent with, and reinforces, evidence already on record from T-333 and `run_band_monitor.py`:
- **Calibration slope b=0.600** (this session's fresh run, CI [0.419, 0.812], excludes 1.0) — an independent, model-level overconfidence measurement pointing the same direction as this session's edge-tercile finding.
- **H2 (T-333, confirmed by code read):** T1's calibrated pregame estimate (`p_t1`) is loaded into T4's context but discarded before the edge computation — never blended into `p_t4`. T4 trades on a raw in-game estimate with no calibrated prior to shrink toward.
- **H1/H4 (T-333, suggestive):** `ba_l10` (a small-window, n≤10 rolling batting average) feeds `p_t4` as a fixed per-AB Bernoulli parameter with no shrinkage; `ab_remaining` compounds that noise in the binomial tail calculation. Terciles with the most extreme `ba_l10` values produced the largest (noisiest) edges in T-333's join.

None of these mechanisms were re-tested from scratch this session (that is T-333's prior work, cited here for continuity) — this task's contribution is establishing that the fee/edge-frame explanation is *not* an alternative to them: correcting the frame bug does not make the miscalibration signature disappear, it sharpens it.

---

## Decomposition verdict

| Mechanism | Verdict this session |
|---|---|
| (a) real signal-inversion | **Ruled out as primary driver.** Win rate stays >50% (net informative) at every tercile, including the highest-edge one — a decay pattern, not a sign flip. |
| (b) fee/edge-frame artifact | **Real bug found (GG-112), but ruled out as GG-105's cause.** Correcting the identified vig-sign-flip bug *strengthens* the anti-predictive pattern (p: 0.046→0.0094) rather than resolving it. |
| (c) flat-sizing artifact | **Ruled out** (T-329, reconfirmed orthogonally this session). |
| (d) model miscalibration (overconfidence) | **Leading mechanism.** Consistent, convergent evidence: within-direction tercile decay (this session), calibration slope b=0.600 excluding 1.0 (this session's fresh `run_band_monitor.py` run), T1-estimate-discarded (T-333 H2), noisy small-window `ba_l10`/`ab_remaining` inputs (T-333 H1/H4, not yet interaction-tested). |

**No recalibration ADR proposed this window, per scope.** Any live-formula change (vig-sign fix, T1/T4 blending, ba_l10 shrinkage) requires its own DS sign-off and superseding ADR per Hard Rule 3 / ADR-0039 Tier B precedent.

**Recommended next steps (not this window):**
1. Fix GG-112 (vig sign) as an independent, low-risk correctness fix — it changes *which* bets clear the gate (removing ~1/3 of currently-approved NO bets that carry negative true edge), which is a capital-relevant behavior change even though it doesn't explain GG-105, and therefore needs its own scoped task + sign-off, not a silent patch.
2. A formal interaction model testing H1×H4 jointly (T-333 flagged this as not yet built).
3. Re-run Component A (full tercile/Fisher re-derivation) once `CURRENT_LOGIC_EPOCH` clears its ~14-day maturity window (~2026-07-19/20 per T-340) — standing watch item, unchanged by this task.

**Artifacts:** `scripts/run_t344_vig_sign_diag.py`, `exp_output/T344-VIG-SIGN-DIAG/vig_sign_diag_results.json`.
