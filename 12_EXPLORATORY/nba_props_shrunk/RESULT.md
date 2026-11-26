# EXP-047-S RESULT — shrunk per-minute rates × shrunk minutes through C2's usage shift vs C2 as logged

**Run:** 2026-11-25 (W129.2), once, `run_shrunk.py --final`. **PREREG:** `PREREG.md` at commit `8d6b97e6223cac434ad150d8897c52d56821609e`
(pushed before any judged row was read; `results.json` carries the same SHA). **Judged:** NBA 2025-26 regular season, priors from 2024-25.
**Verdict (PREREG §5 rule): SUPPORTED.** Pooled D interval wholly above zero and 4 of 4 stats positive.

## Primary
D = LL(C2) − LL(challenger); positive = challenger better. 90% game-clustered bootstrap, 2,000 resamples, seed 20261121.
| | D | 90% interval | rows | games |
|---|---|---|---|---|
| **Pooled** | **+0.001717** | [+0.001402, +0.002039] | 315,191 | 1,131 |

## Per stat (BH q 0.10 over 4 stats; every one-sided p at the 1/2001 floor)
| Stat | LL C2 | LL shrunk | D | 90% interval | Brier diff | BH |
|---|---|---|---|---|---|---|
| points | 0.35572 | 0.35423 | +0.001495 | [+0.001075, +0.001924] | +0.000381 | pass |
| rebounds | 0.34619 | 0.34528 | +0.000903 | [+0.000679, +0.001149] | +0.000312 | pass |
| assists | 0.30934 | 0.30819 | +0.001152 | [+0.000849, +0.001468] | +0.000399 | pass |
| threes | 0.45005 | 0.44633 | +0.003718 | [+0.002635, +0.004784] | +0.000752 | pass |

## Secondary (reported, never the verdict)
- **By prior games on this team:** 4–10: D +0.008799 [+0.007215, +0.010392] (47,405 rows). 11–30: +0.001054 [+0.000768, +0.001366]. 31+: +0.00001 [−0.000139, +0.000162], p(D≤0) 0.461, i.e. no measured difference once a player has 31+ games.
- **Out slice:** games with an Out player D +0.001472 [+0.001123, +0.001833]; without +0.002087 [+0.001553, +0.002656]. Both positive; the gain is not absorbed by the usage shift. (Slice game counts are team-game counts and do not sum to 1,131 games.)
- **Decomposition (same C2 shift):** shrunk rate × raw minutes +0.001660 [+0.001375, +0.001971]; raw rate × shrunk minutes +0.000190 [+0.000082, +0.000303]. Nearly all of the gain is the rate shrinkage.
- **Power:** per-game sd of D 0.00718; MDE (80%) 0.00053 at 1,131 games. Observed D is about 3.2× the MDE.
- **Dropped:** 43 of 1,230 games had no usable pre-tip report; 13,832 player rows (did not play) excluded. Players without a previous season: not measured (see limitations).

## Against the pre-stated modal outcome (P3)
Stated: SUPPORTED, pooled D +0.0010 to +0.0020, gain concentrated in 4–10, largest for threes and assists, near zero for points in 31+.
Actual: SUPPORTED, pooled D +0.00172 (inside the range). Concentration in 4–10 and a null in 31+ matched. Threes was largest as stated;
**assists was not second** (points +0.00149 was, assists +0.00115, rebounds +0.00090). The 31+ null was reported pooled, not per stat.

## Limitations
- 2025-26 is not fresh to the program (PREREG §2 disclosures: PAM-3 excluded it; C1 scored a different challenger on it). The 2026-27 forward rows are the out-of-sample check.
- `players_without_prev: 0` in `results.json` is an initialised field that `run_shrunk.py` never increments, so it is not a measurement. The share of rookies and new players in the judged rows is unreported; the no-previous-season path (league prior, raw minutes) is unit-tested.
- Threes use C2's raw 3PA attempt weights (not shrunk). Log-loss and Brier are input-quality scores against outcomes, not net after costs.
- The 4–10 stratum carries most of the gain, so live value falls through the season as samples fill.

## Consequence (PREREG §7)
SUPPORTED: class 3 carries to the C2 chain. The challenger logs forward beside C2 (Part C) and is **applied** only if the router scores it as a
split per leaf on net after costs per arm. This does not touch the verdict on any cell and orders are unchanged.
