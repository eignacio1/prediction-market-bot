# NFL first look (≈ 2026-11-02): what it can and cannot tell us — EXPLORATORY

**EXPLORATORY. Not a verdict, not an addendum — the EXP-037 pre-registration is unchanged.** Written 2026-10-09, before any NFL cell has reached its judged n.

> **One line: at 60 games per cell the first look cannot detect any plausible effect against the market — the smallest it can see is about 0.038 Brier, and the 2025 gap is about 0.008. Expect "keep accruing" almost everywhere.**

## What the first look computes (EXP-037 §§2–4)
Per cell (4 families × T1/T2/T3 = 12): over the earliest 60 settled games, delta = Brier(X) − Brier(model), where X is the market mid (the decision) and
climatology (a sanity check). Positive = model better. A game-cluster bootstrap (B = 2000, two-sided 95% CI) gives the verdict:
**RULED_OUT** if the whole CI is below zero · **KEEP ACCRUING (SHADOW)** if it spans zero · **CANDIDATE-PENDING-CAPACITY** if the whole CI is above zero *and* net edge E_net > 0 under both fee candidates.

## What the 2025 season says (pre-2026 only; 272 regular-season games, frozen model, Kalshi KXNFLGAME moneyline mids)
| Comparison | Estimate (CI) | Per-game SD |
|---|---|---|
| Model vs market mid, ~24h / ~6h / ~0.5h before kickoff (n = 252 with a quote) | −0.0082 / −0.0074 / −0.0082 (each CI ≈ −0.021 to +0.006) | 0.106 / 0.107 / 0.108 |
| Model vs climatology — moneyline (n = 272) | +0.029 (+0.012 to +0.046) | 0.143 |
| Model vs climatology — spread, game total (sportsbook line as the one strike; a proxy) | +0.015 (+0.004 to +0.027) · +0.006 (−0.004 to +0.016) | 0.096 · 0.086 |

The market is slightly better than the model; the model is clearly better than climatology on moneyline and spread, indistinguishable on totals.
The three horizons give the *same* answer because the 2025 mid barely moves between 24h and 30 minutes — and they reuse the same 60 games.

## Detectability
The pre-registration assumed a per-game SD of 0.07 (MDE 0.025 at n = 60, 0.016 at n = 150). **Measured, it is ≈ 0.106 — 1.5× larger —
so MDE is ≈ 0.038 at n = 60 and ≈ 0.024 at n = 150.** Against climatology the MDE is 0.052 / 0.035 / 0.031 (moneyline / spread / total) at n = 60.
(Moneyline only: no pre-2026 spread, total or team-total prices exist, so those market SDs are unmeasured; treat 0.106 as the best available guess.)

## Most likely verdict, and the odds (true delta = the 2025 estimate, ≈ −0.008, n = 60)
- **Vs market, every cell: KEEP ACCRUING ≈ 91%.** RULED_OUT ≈ 9% (≈ 16% at n = 150); CANDIDATE < 1%.
- **Vs climatology** (sanity check): model should look better — point estimate above zero with ~94% (moneyline) / ~89% (spread) / ~72% (total) probability; CI excluding zero only ~35% / ~24% / ~9%.
- Team-total and the other ladder cells: no history, so no estimate; assume the same shape.

## What would genuinely surprise us
- **Any cell CANDIDATE at the first look:** needs a true edge ≥ ~0.02 for even a 30% chance. Treat it as a bug or luck until re-derived.
- **Any cell RULED_OUT at the first look in T1:** would need a true gap near −0.02 or worse (31% chance there); at −0.008 it is ~9%.
- **T1 → T2 → T3 ordering visibly monotone** (pre-registered): the 2025 data says the horizons are not separable at n = 60.
- **Model worse than climatology** on moneyline (≈ 6% chance) or spread (≈ 11%); totals (≈ 28%) would not surprise.
- Note the 12 cells are not 12 independent looks: the three horizons of a family share games, and about 1 in 20 cells flags by chance at a true delta of zero.

*Source: `12_EXPLORATORY/20261009_nfl_first_look_expectations/{study.py,results.json}` (normal approximation to the bootstrap for the odds; E_net ignored, so CANDIDATE odds are upper bounds). No 2026 row, sealed result or 2026 score was read.*
