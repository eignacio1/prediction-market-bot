# Kalshi combo (MVE) markets — mechanics, measured (W126.4 Part A)

**Last reviewed:** 2026-11-25. Source: Kalshi public read-only API (`/trade-api/v2`), one sample taken 2026-11-25T00:27Z. Sample archive:
`combo/nba_single_game_combos_2026-11-25T0027Z.jsonl.gz` (the 7,203 open NBA single-game combos; fields kept: legs, bid/ask and sizes, last, volume,
close). Scripts: `combo/q1.py`, `q2.py`, `tr2.py` (they read raw pulls kept outside the repo).

## How a combo is listed
- A **collection** (`mve_collection_ticker`) is a template; a **combo market** is an instance created on demand, in bulk. Each carries
  `mve_selected_legs = [{event_ticker, market_ticker, side}]` (side yes/no per leg) and a `custom_strike` map (Associated Markets / Sides).
  YES settles only if every leg resolves as selected. Settlement ~5 s after the last leg (`settlement_timer_seconds`).
- **Correction to the brief:** the per-game NBA collections (`KXMVENBASINGLEGAME-<game>`, 196 of them) stopped 2026-10-07. Today NBA same-game
  combos are instances inside the rolling `KXMVECROSSCATEGORY-R` collection; same-game = every leg's event shares one game suffix. Collections
  seen: KXMVENBASINGLEGAME (ended), KXMVENFLSINGLEGAME (empty), KXMVESPORTSMULTIGAMEEXTENDED, KXMVECROSSCATEGORY.
- Leg families in the 7,203 NBA same-game combos (leg counts): player points 23,118 · rebounds 8,538 · assists 8,098 · threes 5,433 · the
  `...PROT` variants (PTS 1,749, 3PT 907, REB 853, AST 659) · PRA 1,385 · moneyline 1,043 · total 438 · steals 407 · spread 383 · team total 267
  · blocks 212 · stocks 145 · double-double 133 · 1H/1Q lines ~600 · precise total 92. Legs per combo: 2 to 13 (3-leg 1,013; 4-leg 966; 5-leg 833).

## Quoting: there is effectively no standing book
- Of 61,000 open combos sampled: no quote at all 59,453 (97.4%); bid only 994 (bids of 0.0001-0.0003, placeholders); ask only 547;
  **two-sided 6**. NBA same-game: 7,003 no quote, 130 bid-only, 68 ask-only, **2 two-sided**.
- Quoted asks (NBA same-game, n=70): quartiles 0.136 / 0.388 / 0.562; ask size quartiles 9 / 31 / 114.
- Trades: 4,715 of 61,000 have volume; 470 of 7,203 NBA same-game. The pattern is request-for-quote style: one or two fills per market,
  typically large clips (sample trade count_fp 51.94). A last price with no standing bid is normal.
- Closing time of the NBA combos: about 47.5-48.5 h ahead at the sample, i.e. instances are created ~2 days before the game.

## Spread at T-2h / T-30m: **not measurable historically**
The public API gives no historical order-book snapshots for combos. From trade timestamps on the ended per-game collection (569 markets, 1,087
trades, Oct 2026): hours before close at deciles 1.2 / 2.4 / 5.0 / 11 / 11.4 / 11.7 / 12.0 / 12.7 / 16.7; 16.5% of trades within 2 h of close, 4.3%
within 30 min. So fills happen mostly far from tip, and a T-2h / T-30m quote has to be logged forward by the shadow writer (Part C). No spread
number is claimed here.

## Fees
Standard taker formula `round_up_centicent(M * 0.07 * C * P * (1-P))`. The combo multiplier M is **not** in `quant/kalshi_fees.json`; the default
(1.0) is used and flagged **unverified**. The shadow writer records fee-at-default and the arm's scoring must be re-run if the fee schedule
for combos differs.

## What this means for the arm
- There is nothing to "ride" in a thin book: a price exists mainly when a quoter answers a request. The shadow writer logs whatever quote is
  showing (bid/ask/size, or none), so the first measure is how often a priced two-sided market exists near tip.
- Hypothesis for the pre-registration: where an ask shows and the engine joint P is above ask + fee, the combo is a pot-of-gold fade-arm leaf.
