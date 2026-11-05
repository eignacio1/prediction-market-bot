# Multiplicity ledger — W102.4 Part B

Descriptive. **The pre-registered word stands in every row; the adjusted reading is information only.** Tools: `quant/multiplicity.py` (Holm, Benjamini-Hochberg, Lan-DeMets spending, repeated-look simulation), known-answer tests in `tests/test_quant_multiplicity.py`. Terms were read from the pre-registration files on `origin/main` on 2026-11-05; "not stated" means the grep of that file found no explicit statement (not that none exists).

| # | Test | Alpha / sidedness | Looks planned | Verdict so far (pre-registered word) | Adjusted reading |
|---|---|---|---|---|---|
| 1 | EXP-037, 12 NFL cells | 95% two-sided game-cluster CI per cell; "reported per cell, never pooled" | n=60, then n=150 or week 18; no third | GAME_TOTAL T1, T2 RULED_OUT (11-02); 10 cells KEEP ACCRUING | **Word would change** (see below) |
| 2 | EXP-037 NFL QB moneyline (NFLQB, 11-13 look) | as row 1 (C2 vs market); C1 challenger-vs-frozen one-sided 0.05, n=984, descriptive only | same as row 1; first look at n=60 (47 judged now) | none | none yet (no score) |
| 3 | ADR-0072 forward test, 4 book-sports | one-sided 95% (z 1.645), criteria (a)(b)(c) | judged n 550/arm; NFL one extra look; report recomputed daily (W101.2 obs 2) | NFL ADOPT; NBA, NHL (b) fails; third sport unchanged | **Word holds** (see below) |
| 4 | EXP-041 NFL anchored | pooled primary one-sided 0.05; Holm across 12 cells secondary, report-only | count-only 2027-01-10; scored at 500 games | none | none yet |
| 5 | EXP-042, 10 live ride cells (cell 10 retired) | one-sided 0.05, BH across cells | one scored look per cell at its judged n; mostly not reachable in 2026 | none (all IN_SAMPLE/UNTESTED) | none yet |
| 6 | EXP-043, 2 cells + H-B | one-sided 0.05; BH q=0.10 across 3 | cells ~2027-05; H-B n=7,535 | none | none yet |
| 7 | EXP-044 / 044b / 044c, per family | one-sided 0.05, n>=1,200, w>=0.01 | checkpoint 2027-01-31 (descriptive), verdict 2027-04-20 | none | none yet; b and c re-test the same families as 044 (a family of 3 engines x families not stated) |
| 8 | EXP-045, 3 families | one-sided centred bootstrap | Look 1 2027-01-12 (MDE 0.032, underpowered); continues into 2027 | none | none yet |
| 9 | NHL challengers (W100, W101) | one-sided/judged n per file (totals file: judged n section; alpha not stated in the lines read) | walk-forward test seasons 2023-25, 2026 descriptive | no live verdict (walk-forward descriptive) | none |

## Verdicts whose word would change under a family-wise view

**EXP-037 GAME_TOTAL T1 and T2 (RULED_OUT).** From the published CIs: T1 delta Brier -0.0161 [-0.0294, -0.0027] gives se 0.0068, z 2.35, two-sided p 0.019; T2 -0.0157 [-0.0299, -0.0011] gives p about 0.032. Holm across the 12 cells: T1 adjusted p 0.23, T2 0.35 — **neither rejects** at 0.05. Across the 4 families (T1/T2/T3 share the same games, so they are one finding counted twice, as the W98.2 note says): 0.019 x 4 = 0.075, still not. The pre-registration says verdicts are per cell and never pooled, so the word RULED_OUT stands; but a family-wise reader would call it "suggestive". Cost asymmetry: RULED_OUT stops scoring, not logging (arms keep logging), so a false RULED_OUT costs lost opportunity, not capital.

## Verdicts that survive

**ADR-0072 NFL ADOPT.** (a) +0.190, se 0.062: z 3.06, one-sided p 0.0011. Holm x4 book-sports: 0.0044. Daily recompute treated as k looks with a running mean: simulated null false-positive at z 1.645 is 0.22 at 20 looks and 0.32 at 100; the family-wise z bound is 2.37 (20 looks) to 2.64 (100). 3.06 clears all of these, so the word holds under daily reading for criterion (a). Caveats: criterion (b) is a point rule (ratio 0.376 >= 0.25), not a test; and Part A shows the (a) gain is ~95% selection, which the ADOPT word did not claim to separate.

## Where the exposure actually is

Counting only tests that can issue a word before 2027-05: row 1 (12 cells x 2 looks), row 3 (4 x daily), row 4 (12 secondary), row 5 (10), row 6 (3), row 7 (3 engine versions x up to 4 families), row 8 (3). That is roughly 50 family-members across the programme at one-sided 0.05 each; with no correction the expected number of false "PASS/BEATS" calls under all-null is about 2.5. Pre-registered modal outcomes (mostly KEEP ACCRUING / NOT DISTINGUISHABLE / UNDECIDED) are the real protection.

## Recommendation for the window (one line; the operator decides)
Future pre-registrations should name their family (which sibling tests share the claim) and the correction or spending rule for repeated looks (e.g. O'Brien-Fleming for k planned looks; a fixed one-time read for report-only dailies), stating it before the first row; existing registrations are unchanged.
