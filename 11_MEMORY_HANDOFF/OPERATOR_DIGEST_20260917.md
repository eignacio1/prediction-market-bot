# Operator Digest — 2026-09-17

## T-554/GG-285 — Is APR-0024's P&L gate reachable?

Not within any practical horizon, for either cell with enough data to measure. T4M-PROJ needs ~1.6-1.7 more MLB seasons at the current pace just to hit the required sample size. NFL moneyline: ~11 seasons, ~11 calendar years. T1/T2/T3 can't even compute a target. Calibration metrics (Brier/ECE) already give usable reads at far smaller samples — P&L carries extra payoff variance on top of forecast error, which is the structural cause.

No gate, threshold, or verdict changes — EXP-027's UNDERPOWERED call stands. Drafted `APR-0035`: four options (keep gate as-is; add a faster calibration-based gate for cell promotion, P&L stays the live-capital gate; re-derive the sample size under different assumptions; a hybrid), none selected — your call.

**Awaiting your decision on APR-0035.** No urgency, nothing blocked today.

## 2026-09-17 05:42 — T-556: NFL positions opened; Kalshi order-fail diagnosis (no fix yet)

**What happened:** The system placed its first-ever 42 NFL bets on the demo Kalshi account. All 42 are on unplayed games, so none can be scored win/loss yet — expected, not a problem.

Separately, we dug into why real-money order placement keeps failing (GG-203). Ruled out four suspects: wrong web address, broken order form, mismatched account, "bet doesn't exist on practice site." None are the cause. Best guess now: Kalshi's internal order-routing is misconfigured on their end. No fix applied — needs Kalshi support, not more code on our side.

**Next:** after 2026-09-20, check whether those 42 NFL bets can finally be scored as win/loss.

## 2026-09-18 02:57 — T-558: GG-203 root cause found (still needs your action)

**What happened:** Found why real-money orders keep failing (GG-203). Not a code bug — a funding issue: Kalshi splits balance into "shards" by sport, and the practice account's sports shard has $0, though the overall balance shows funds. Confirmed two ways: extra order routing info made no difference (rules out a code fix); the balance-by-shard read showed $0 specifically in sports.

**Your money:** No live capital at risk — practice account only. No risk-limit or sizing change.

**Decision needed:** Yes — one API call moves balance into the sports shard. That's a funding action, outside what a coding session can do alone; needs your authorization, then one test order to confirm. GG-203 stays diagnosed, not fixed, until then.

**Worried about:** Nothing new.
