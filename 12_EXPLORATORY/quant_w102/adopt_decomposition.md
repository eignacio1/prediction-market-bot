# ADOPT gain decomposed (NFL shadow, post-top-up) — W102.4 Part A

Descriptive. Not a verdict, not a new test. Same rows as W101.2 (fills after the 2026-10-16T05:40Z top-up, settled): control n=6,904, treatment n=2,590, 41 games; total gain reproduced at +0.1896 (W101.2: +0.190).

Method: `quant/fill_decomposition.py`; known-answer tests (all placement / all selection / half-half / unmatched) in `tests/test_quant_fill_decomposition.py`. Strata = (ticker, held side); every order in a stratum shares one settlement, so a within-stratum difference is purely the price paid. Intervals: 90% game-cluster bootstrap, 2,000 reps, seed 7 (script: `adopt_decomposition_run.py`, reads local copies of the box cache).

| piece | value (per fill) | 90% interval | meaning |
|---|---|---|---|
| total | +0.190 | [+0.133, +0.244] | treatment minus control, settle-minus-price |
| (i) placement | +0.010 | [+0.006, +0.015] | both arms filled same market+side: price we get by waiting (n treatment 2,524 on 651 shared markets) |
| (iii) selection | +0.178 | [+0.120, +0.236] | control reweighted to treatment's fill mix |
| unmatched | +0.001 | [-0.004, +0.006] | treatment fills in 38 markets control never filled |
| (ii) skipped by waiting | -0.032 | [-0.090, +0.020] | control's value on 3,459 fills in markets treatment did not fill |

**For the operator:** of the 19 cents, about 1 cent is the price we get by waiting at the book, and about 18 cents is which orders end up filling. Waiting itself buys almost nothing per order; what it does is let the cancel-at-60s rule drop orders that only a quick fill would have caught, so the fills that remain sit in different (better-settling) markets. Control's fills in markets treatment skipped averaged -3 cents (interval spans zero), so the skipped fills were not clearly winners being missed, but they were not clearly losers either.

Caveats: (1) selection here is real in the P&L sense but it is not a price improvement — it depends on which markets fill at 60s and whether that persists; the 30-min markout (criterion c) found no placement benefit, consistent with a small placement piece. (2) Finer strata (ticker+side+hour) collapse common support (313 strata, 612 treatment fills), reading placement ~0 and putting more in "unmatched"; ticker+side+day gives placement +0.006, selection +0.174. The conclusion (selection dominates) is stable; the exact cents are not. (3) Treatment gets 38 more markets than the stratum list sees only through `unmatched`.

Recommendation to the window: the ADOPT word stands as issued; if adoption is considered, price it as a selection effect (fewer, better-settling fills), not a better-price effect. Nothing here changes any pre-registered rule.
