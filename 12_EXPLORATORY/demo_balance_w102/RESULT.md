# Demo balance rejections (W102.3, 2026-11-05)

## Count (read-only, `logs/demo_fill_policy.jsonl`, 2026-10-16 to now)
Orders refused `insufficient_balance`: **2,259**, all shadow flat-stake orders (the demo account is shared; "book" = shadow arm).

| arm | MLB | NHL |
|---|---|---|
| control | 1,121 | 42 |
| treatment | 1,049 | 47 |

By day: 10-16 402, 10-17 233, 10-19 312, 10-22 120, 10-23 341, 10-24 310, 10-25 75, 10-27 255, 10-28 202, 10-29 9. **None since 10-29.** Not covered: refusals in the T4/T1 order paths' own logs (none matched this pattern in the files checked; their staged-order DBs were not read).
**Balance at each refusal: not recorded before this block** (the rows carry no balance), so it cannot be given for these 2,259. Only the 10-30 to 11-05 cash series exists (from the earlier W96.3 read).

## Cause (probable, not proven)
The Kalshi demo account is one pool. Orders are `good_till_canceled`; each resting order reserves its cash. The control arm never cancels, so unfilled control orders hold cash until the market ends. Refusals stopped after a balance change around 10-29, then cash fell from $3,287.58 (10-30) to $1,005.78 (11-05) with about 581 resting orders: about $380 a day. The earlier W96.3 hypothesis (the 60-second treatment cancel reserving cash) is contradicted: those are cancelled within a minute.
Proof still needs the balance on each refusal, which is now logged.

## Fix shipped (PR #426)
Every non-ok shadow order row now carries `demo_balance_usd`, `demo_portfolio_value_usd`, `demo_balance_age_s`, or `demo_balance_error` if the read fails (logging only, 15 s cache, never raises). 3 tests; 92 pass in the fill-policy suites.

## Operator / plumbing
At about $380 a day, $1,005.78 lasts roughly 2.6 days from 11-05, so refusals return near 11-08. A **demo top-up is plumbing** (no real money). The durable fix is cancelling or expiring control-arm orders, which changes the pre-registered control arm: an operator question, not made here.

## Found this block
GG-1770 (fill report inverts win/loss on NO-side fills) and GG-1771 (`submit_order` mirror-prices NO orders, HIGH). Both registered, not fixed.
