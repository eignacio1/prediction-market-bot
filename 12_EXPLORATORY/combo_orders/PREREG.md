# EXP-COMBOORD-001 — combo RFQ orders in the Kalshi DEMO, per leaf (pre-registration)

Last reviewed: 2026-11-26. Committed BEFORE any scheduled order. Parent: EXP-COMBO-001 (`12_EXPLORATORY/pot_of_gold/COMBO_PREREG.md`, frozen,
untouched). Doctrine: DOCTRINE §6, the pot of gold is an arm of the tree; the hunt starts in retail-priced parlay flow. DEMO only, Hard Rule 2.

## Question
For same-game NBA combos our engine prices (engine_v2 team draws + joint.py player stats), when we RFQ in the demo and the maker's quote differs from
our joint price by more than costs, does the filled position earn net of fee, per leaf, on held-out game-days?

## Which combos get an RFQ (the leaf rule, from the combo shadow)
Eligible = the shadow row is resolved, fully priced (no legs_unpriced), mc_se ≤ 0.01, **no flags**, and contains **no two player-points legs of teammates**
and **no same-player cross-stat pair** (the pricer is known wrong there; excluded from orders, not only from scoring).
Sample: deterministic sha256 round-robin over leg buckets 2-3 / 4-6 / 7+ (the 12 EXP-COMBO-001 leaves are scored from the shadow ledger; orders are
spread over the same buckets). Window: 30 min to 30 h before tip.

## Accept rule (the fade arm's entry rule for a combo, nothing more)
Accept the side with the larger edge only if `engine_side_p − quoted_price − fee ≥ 0.03`, fee = `ceil(0.07·p(1−p)·1e4)/1e4` at the quoted price
(default fee; the combo multiplier is unverified, so fee is recomputed per fill when the maker reports one). Otherwise no accept; the reason
(`no_quote`, `edge_below_threshold`, `one_sided_negative`, `not_listed`, `accept_failed`, `cap`) is counted and reported, never just logged.
Margin 0.03 = about 2 mc_se at the 0.01 se cap plus rounding of the 1¢ tick; it is a pre-registered constant, not tuned on outcomes.

## Stake and caps (each with its own derivation, GG-1935)
- Stake: 1 contract flat (CONTRACTS_FP "1.00"), `kelly_fraction` 0. Max loss per fill = $1.00 (a contract settles in [0, 1]).
- MAX_ACCEPTS_PER_RUN: **6**. Derivation: judged n 400 fills / (6 per day) = 67 daily runs, inside the NBA regular season from the first run (~11-27) to ~2027-02-10. The old cap of 3 would need 133 runs and end after the season.
- MAX_RFQS_PER_RUN / PER_NIGHT: **12** (unchanged). Derivation: at an expected accept rate of one in two on the quotes seen, 12 RFQs leave room for 6 accepts; the maker quote latency of 4–9 s makes 12 polls take well under the 90 s budget.
- Worst-case demo exposure: 6 fills × $1 = $6 per day. No real-money constant is borrowed.
- One run per day (the scheduled line), so the nightly cap is not the binding limit.

## Metrics
- **E1** fills (accepted and executed) per leaf and per day, and RFQ → quote → accept → executed funnel with the skip reasons above.
- **E2** mean net P&L per filled contract after fee, per leaf, with a bootstrap interval resampling game-days.
- **E3** win rate on fills vs the engine's own P on the same side (calibration), and fills vs non-fills among quoted RFQs (adverse selection).
- Baseline arm (ride): the same combos at the quote with no edge filter are NOT ordered; the shadow ledger carries the descriptive comparison.

## Judged n, look date, modal outcome
- Judged n: **400 executed fills from at least 40 game-days**. Derivation: the payoff of one contract has sd ≈ 0.5; to resolve a mean of 0.05 at two standard errors needs n = (2·0.5/0.05)² = 400. Hold-out: the last 40% of game-days by date, fixed now. No score below judged n.
- Descriptive looks (counts, funnel, skip reasons, no P&L verdict): weekly.
- Judged look: the first date n ≥ 400 and ≥ 40 game-days, projected 2027-02-10 at 6 fills a day.
- Modal pre-registered outcome: the interval on E2 spans zero, and the demo maker's fixed 0.45 / 0.55 quote means fills cluster where the engine disagrees most (long-leg combos), the same extrapolation region where the pricer is least checked. Reported as "hypothesis not supported at this n (EXP-COMBOORD-001, parked for R&D)", never "no edge". A positive E2 would be reported as demo-maker-specific until a production quote cost is measured.

## Caveat that binds every reading
The demo maker does not quote like a production maker (fixed 0.45 / 0.55 regardless of legs). These fills test our engine's probability and the plumbing end to end. They do not estimate the production cost of a combo, and no G6 evidence follows from them.
