# W105.2 / B-052 — counterfactual placement study (descriptive, held-out; nothing here changes an order)

**Operator line:** No placement rule makes these fills win — on this book every price bucket loses at 1 minute. Capping the price you rest at (don't rest at 0.50 or above) cuts the loss per fill by about 40% (−1.2¢ → −0.7¢), and resting at the bid instead of the mid cuts the loss per order by 0.4¢ but loses 29 points of fill rate; both still end negative. Testing a cap properly needs the post-#440 fields to accrue (distance from mid, depth) plus post-epoch (2026-11-06T01:03Z) NO-side fills: roughly one more NFL/NBA/NHL week for a first look, ~4 weeks for a game-clustered CI tight enough to separate the rules. Recommend a pre-registration of "do not rest ≥0.50 on the held side" as a shadow arm; not applied.

## Population and n (stated, per the epoch rule)
- Demo shadow orders (NFL/NBA/NHL), settled, matched to the policy log; intended side from the order (GG-1793), cache rescored (GG-1810).
- **Pre-epoch YES-only: n = 65,217 orders, 17,135 fills (13,164 with a 1-min markout), 1,800 games.** 47,394 pre-epoch NO orders excluded (mirror-priced, GG-1771/1784).
- **Post-epoch, all sides: n = 0** in the pulled data (epoch is 2026-11-06T01:03:42Z; the pull predates it). Nothing post-epoch is claimed.
- Not MLB paper-book fills. Arms: control 33,545 / treatment 31,672.

## Expected 1-minute markout of a fill, by price (held-side mid − fill price; game-clustered 90% CI)
| price | fills n | mean | 90% CI |
|---|---|---|---|
| <0.20 | 3746 | −0.0047 | −0.0067, −0.0025 |
| 0.20–0.35 | 2923 | −0.0065 | −0.0096, −0.0031 |
| 0.35–0.50 | 2720 | −0.0119 | −0.0171, −0.0067 |
| 0.50–0.65 | 1907 | −0.0196 | −0.0270, −0.0135 |
| 0.65–0.80 | 1148 | −0.0227 | −0.0311, −0.0159 |
| ≥0.80 | 720 | −0.0411 | −0.0653, −0.0203 |

Adverse selection is present everywhere and grows with price. It is a **slope, not a step**: the best change-point is 0.51 but its 90% interval is 0.29–0.79 (steps −0.7¢ → −2.6¢). Known-answer test recovers a planted 0.70 step to within 0.03, so the diffuse result is the data, not the tool.

## Rules on recorded quotes (pure filters; markout net per order posted)
| rule | posts | fill rate | per fill | net / order |
|---|---|---|---|---|
| none | 100% | 21.5% | −1.23¢ (−1.59, −0.89) | −0.26¢ (−0.36, −0.19) |
| no rest ≥0.80 | 92% | 22.1% | −1.06¢ | −0.23¢ |
| no rest ≥0.65 | 83% | 22.1% | −0.94¢ | −0.21¢ |
| no rest ≥0.50 | 71% | 21.5% | −0.73¢ (−1.00, −0.47) | −0.16¢ (−0.23, −0.10) |
Settle P&L per order posted: −1.71¢ baseline vs −1.67¢ with the ≥0.50 cap — **no distinguishable change** (intervals overlap fully). The cap helps the 1-min markout, not the settled outcome, at this n.

## Post lower (control at mid vs treatment at best bid; games with both arms, n=1,585)
Net markout per order **+0.44¢ (90% CI +0.29, +0.61)**; fill rate **−28.8 pts (−31.0, −26.9)**. Better per order, still negative in level, bought by posting far fewer fills.

## Not testable on this data
- **Cancel after t seconds:** cache fill/cancel times are when the collector first saw the fill, hours late — not exchange time. PR #440 now logs submit_ts; cancel/fill times still need exchange timestamps.
- **Mid minus k ticks, distance from mid, depth:** distance was never logged (arm is the only proxy); #440 starts logging mid, spread, top-of-book depth, submit time. n(orders with those fields) = 0 until accrual.

## Caveats
Markout is a 1-minute mark, not settlement; the h1 sample drops fills with no markout (3,971 of 17,135). Descriptive only; no pre-registration was in place, so none of this is a verdict (a rule chosen after seeing the slope is a hypothesis).
