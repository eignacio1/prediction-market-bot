# ADR-0076: G6 per book and sport, with limits derived from measured tails

**Status:** ACCEPTED 2026-10-27 17:30 PT by the operator ("Yes I accept"); section 4 blanks stay blank until a positive Kelly is proposed (ADR-0048 unchanged).
**Date:** 2026-10-27 (W88.1) **Pillar:** PROOF + PLUMBING **Decisions logged:** true
**Evidence:** `12_EXPLORATORY/tails_evt/results_W88.md` and `tails_W88.json` (box data 2026-10-27, game-clustered, PR #337).

## 1. Problem
G6 ("30 resolved paper bets with positive P&L, per sport/pool, plus DS sign-off") is not closable as written. GG-204: ADR-0028's closure condition is scoped to T1, which is permanently `clean_n=0`. GG-285: APR-0024's per-band n* is 10-11 NFL seasons for NFL moneyline and about 1.6 MLB seasons for T4M-PROJ. ADR-0057 made closure cell-scoped but left GG-157, GG-038, GG-125 and the 2026-05-29 `_HARD_LIMITS` revision obligation open. The real-money limits in `risk.py` have no derivation from measured tails.

## 2. Qualification, per (book, sport)
A book qualifies for G6 when its cell WINS at its pre-registered judged n under ADR-0072 (and, where it applies, EXP-041's pooled test). A paper-only row is calibration evidence, not qualification; only real demo fills count (GG-527). Current state, from the measured data:
| Book | Fills / closed | P&L per filled bet | Qualified? |
|---|---|---|---|
| MLB T4M-PROJ | 177 / 4,316 | -$0.21 (n=177, 69 games) | No: negative, fills win 25.4% vs 48.3% for non-fills (adverse selection) |
| MLB T1 | 85 / 485 | -$1.50 (n=83, 57 games) | No |
| NFL, NHL, NBA, MLB postseason shadow arms | no fill-priced per-game P&L available | none | Cannot be assessed; see GG-1191 |

No book qualifies today. This ADR sets the rule, not a verdict.

## 3. Preconditions
1. The exposure gate is ENFORCING on every order path (GG-1082, GG-441). This is a precondition only; W88.2 flips it and this draft does not depend on that merge.
2. The tails in section 4 exist for the book, with an n adequate for the fit, or the limit is left blank with the reason.
3. DS sign-off (ADR-0005) and operator acceptance of the limit table.

## 4. Limits and their derivations
Units: USD at ledger measurement stakes, $1,000 normalized bankroll. Intervals are 95%, game-clustered. Normal assumptions are not used for any limit.
| Limit | Number | Derivation / reason |
|---|---|---|
| Per-game aggregate exposure cap (all bets on one game) | BLANK | A binary contract loses at most its stake, so the worst game loss equals stake deployed on that game; EVT on per-$ loss is undefined (capped at 1.0). The cap must be set from the Kelly multiplier and bankroll the operator chooses, not from a fitted tail. Reason left blank: no positive Kelly is authorized (ADR-0048). |
| Per-event cap `max_single_event_exposure_usd` (now 500) | BLANK, flagged | Its stated rationale (KXMLBHIT depth $500-$2,000/market, ADR-0048) is a point estimate that GG-155 found to swing 10-100x intraday. It is a depth backstop, not a tail derivation. Keep as is until a live depth measurement is used. |
| Daily loss (`MAX_DAILY_LOSS_PCT` 0.15, ADR-0012) | Keep; not tightened | Per-game 1-in-100 loss at measurement stakes: T4 filled $7.18 [2.98, 12.04], T4 paper $13.09 [10.44, 15.94], T1 paper $53.57 [40.49, 62.48]; T1 filled has no fit (14 exceedances, below 15). All are far under 15% of $1,000 at flat stakes. The binding risk is drawdown, not one day. |
| Drawdown kill (`max_drawdown_pct` 0.20 = $200) | Keep | 99th-percentile max drawdown over 90 games at flat stakes: T4 filled $99.6 as-is / $56.1 zero-edge; T4 paper $141.5 / $113.1; T1 filled $471 / $293 (bootstrap only); T1 paper $566 / $518. T4 stays under $200; T1 does not even at zero edge (GG-135 ruin geometry). Scales linearly with stake. |
| Deployment (`max_portfolio_deployment_pct` 60%, ADR-0026) | Keep | Not a tail quantity; unchanged by Part A. |

Where n is too small: T1 filled has no tail fit; T4 filled's 1-in-1000 interval is 3 to 57 and unusable; all 1-in-1000 figures beyond the sample are extrapolations. Any limit leaning on those is provisional and must be re-derived at each look. The tail fits rest on 14 to 99 exceedances and, for the filled books, on few losing games.

## 5. Kelly
Kelly stays at 0 (ADR-0048). The smallest positive Kelly the ADR could allow is ADR-0048's 0.10x multiplier row; per-game loss and drawdown scale linearly with stake, so the table above is multiplied by the ratio of that stake to the measurement stake. Reactivation still needs a qualified cell (section 2).

## 6. Relation to existing records
- ADR-0057: partially superseded. Replaced: its cell-scoped G6 definition becomes per (book, sport), and it adds precondition 3.1. Kept: its handling of T1's fate (section 4) is deferred.
- ADR-0028: its closure condition is superseded for the unclosable T1 scoping (GG-204).
- ADR-0048: unchanged; this ADR depends on its Kelly 0.
- ADR-0072: provides the judged-n verdict used in section 2.
- GG-204: resolved by the rule in section 2, on operator acceptance. GG-285: not resolved. The n* arithmetic is untouched; section 2 replaces the P&L-gate wait with per-cell judged-n verdicts, but whether that is the intended meaning of G6 is the operator's call.

## 7. Open items
GG-1190 T4 cache `cache_bankroll` flat at $1,000 against realized -$140.93; GG-1191 shadow books' fill-priced per-game P&L not obtained; GG-1192 per-event cap rationale is stale.

## Operator line
**Decision (2026-10-27 17:30 PT): "Yes I accept." Accepted as the G6 definition (per book and sport, limits as in section 4), with the blanks in section 4 left blank until a positive Kelly is proposed.**
