# RESULT W127.3 — Kalshi combos through RFQ in the DEMO (descriptive; COMBO_PREREG.md unchanged)

**Last reviewed:** 2026-11-25 (W127.3). Source: box ledger `exp_output/COMBO_RFQ_DEMO/COMBO_RFQ_DEMO.jsonl`, read via box task `combo_rfq_demo_read` (result 20261125T0518Z). Demo exchange only; Kelly 0; 1 contract per RFQ.

## What ran
- Demo supports RFQs on production-named combo tickers (`KXMVECROSSCATEGORY-...`): `GET /markets/{t}` on demo resolved them, `POST /communications/rfqs` returned ids. Part A is not NONE.
- Two earlier runs sampled 0 combos. Cause found by stage counts: `kickoff_for_event` parses only KXNBAPTS/REB/AST/3PT, so the `KXNBAGAME-` lookup returned no tip for any game. Same defect sat in `nba_combo_shadow.py` (would have logged 0 rows once installed). Fixed in PR #580.
- Third run (05:13Z): 12 RFQs created (the nightly cap), games ~17 h to tip, 2 to 8 legs. The run then crashed on the accept cap (a failed accept counted against the client cap, not the run's), so only the first 3 quote records and no run summary were written; the other 9 RFQs are unrecorded and were not cancelled. Fix in PR #581.

## Numbers (n = 3 recorded of 12 created; read as plumbing, not rate)
| Quantity | Value |
|---|---|
| RFQs created / quote records written | 12 / 3 (quote rate over 12 NOT measured: 9 records lost to the crash) |
| Time to quote | 3.9 s, 9.0 s, 9.1 s |
| Demo accepts | 3 attempted: 1 rejected (HTTP 400 `invalid_parameters`, one-sided quote, YES bid 0), 2 accepted (HTTP 204) and **executed** |
| Quote vs engine P (buy-YES price minus engine P) | +0.328 (3 legs, one-sided), +0.101 (4 legs), −0.155 (7 legs) |
| Quote vs product of legs | +0.342, +0.102, −0.167 |

**What it says about the arm's cost.** On the two two-sided quotes the demo maker posted 0.45 / 0.55 (overround 1.00), the same quote for a 4-leg combo with engine P 0.349 and a 7-leg combo with engine P 0.605. A quote that does not move with the legs looks like a fixed demo market maker, not a priced book, so the quote-minus-engine gaps above describe the demo maker and do not estimate the production round cost. What carries over: RFQs on combos get quotes in single-digit seconds, accepting a quote fills in the demo, and the cost of the arm is whatever the maker quotes, not a spread we can read off the book. A production read needs production quotes (real capital, Hard Rule 2; not done).

## Hypothesis status
Nothing closed. EXP-COMBO-001 is untouched; E1 on combos: 2 demo fills (1 contract each, not settled; no P&L yet). E2 not measurable until they settle.

## Next
Merge #581, re-run next UTC day (cap resets) for a full 12-RFQ record with summary and cancels; check settlement of the 2 fills.
