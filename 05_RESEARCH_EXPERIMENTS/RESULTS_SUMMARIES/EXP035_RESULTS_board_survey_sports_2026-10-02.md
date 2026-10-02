# EXP-035 results — Part 1 FAILED; D2 diagnosis and fee re-score (T-605, 2026-10-02)

**Standing verdict (unchanged, unrescued):** EXP-035 Part 1 (frozen e28166a) FAILED at 0972862 (`gate_result.json`, GG-333).
G1 pass; G2 0.335 (need ≥0.80); G3 0.472 (need ≥0.95); G4 0.0319 vs 0.0257 (±0.003); G5 0.090 vs 0.04 (±0.005);
G6 pass (sign); G7 fails only [24,48)h. Candle numbers from Part 1 are VOID. **Nothing below relabels Part 1 and no D2
number validates candles.** Artifacts: `exp_output/EXP-035-BOARD-SURVEY-SPORTS/{diag_d2,fee_rescore}.json`;
code: `scripts/board_survey_sports_{gate,diag,fee}.py`; tests: `tests/test_board_survey_sports_gate.py` (13, green, pushed 9e7760d).

## D2(a) — G2/G3 failures, 1,988 sampled snapshots (666 pass Part 1 G2; 1,322 fail)
| class | n | share of failures |
|---|---|---|
| (i) no 1-min candle in [t−120s, t+120s] | 866 | 65.5% |
| — of which: hourly candle constant over the hour and prevailing agrees | 292 | |
| — of which: unresolvable from stored data (in-hour path unknown) | 451 | |
| — of which: no covering hourly candle | 123 | |
| — of which: constant hour and disagrees / archive quote outside hourly low–high | 0 / 0 | |
| (ii) candle found (or none ≥ t) but a different quote than the prevailing one; prevailing close ≤ t agrees | 290 (110 later change; 180 none ≥ t) | 21.9% |
| (iii) empty-book placeholder (bid ≤ 0 / ask ≥ 1) | 16 | 1.2% |
| (iv) prevailing close at or before t ALSO disagrees by >0.01 — the only H4 evidence | 130 | 9.8% (6.5% of all) |
| (v) no candle at or before t in window, none usable | 20 | 1.5% |

The matched candle's `end_period_ts` lies 55–118 s after t (5th–95th pct): it is the candle of the minute containing t, as the Part 1
text specified. Bounds on a prevailing-quote G2 share from stored data: agree 1,051 · disagree 343 · unresolved 594 →
**[0.529, 0.827]**, straddling the 0.80 threshold. The stored data cannot say whether the prevailing rule would have passed.

## D2(b) — first-seen (DIAGNOSTIC)
Candle first-seen minus archive first-seen, per ticker (n=10,675): median −60 min; p05 −660; p25 −120; p75 +20; p95 +40; min −960; max +239;
74.4% negative; none beyond ±24 h. "First-seen" in Part 1 is two different moments: the candle side is the earliest usable hourly candle
after the window start, the archive side is the first capture of the ticker (EXP-031 `decision_snapshots`).

| recomputation | n | B | H |
|---|---|---|---|
| archive first-seen (EXP-031 reference) | 10,701 | 0.02572 | 0.0400 |
| candle, Part 1 rule (first usable hourly) | 10,675 | 0.03193 | 0.0900 |
| DIAGNOSTIC: hourly close at/before archive first-seen | 7,933 | 0.02651 | 0.0400 |
| archive, same 7,933 subset | 7,933 | 0.02594 | 0.0400 |
| DIAGNOSTIC: first usable hourly at/after archive first-seen | 10,595 | 0.01863 | 0.0250 |

2,768 tickers have no hourly candle at or before their archive first-seen (first-seen falls in the market's first hour), so the prevailing-rule row covers 74%.
Hourly closes can be up to an hour stale. These are diagnostics on a subset, not a validation.

## D2(c) — H3, line-by-line review of `evaluate` against the Part 1 text
No defect that changes any gate. Re-running `evaluate` on the store reproduces the frozen `gate_result.json` exactly (refactor into tested helpers is
behavior-preserving). Two spec-vs-code notes, neither explains the failure: (1) G3's "minute before, containing, after" is implemented as the previous /
containing / next *rows* of a sparse series — wider than the text, i.e. more permissive; (2) a snapshot with no candle ≥ t counts as a G2/G3 failure.
Store: 13,026 rows, 1 revision row, no key with differing content across shards.

## D2(d) — verdicts
- **H1 (matching rule vs sparse 1-minute candles): SUPPORTED** as the largest contributor to G2/G3 — 65.5% of failures had no candle in the window, and a further 21.9% fail only because the matched candle is not the prevailing quote while the prevailing close agrees.
- **H2 (two different "first-seen" moments): SUPPORTED** as the contributor to G4/G5 — 74% of candle first-seens precede the archive's; the first-usable candle H (0.09) is the listing-time wide book. At the archive's own first-seen, on the 74% subset, B and H land within tolerance of the reference (0.0265 vs 0.0257; 0.040 vs 0.040) — labelled DIAGNOSTIC.
- **H3 (code defect): NOT SUPPORTED** as a cause (see c).
- **H4 (the data genuinely differ): UNDETERMINED** — only 130 snapshots (6.5%) demonstrably disagree on the prevailing close, but 594 (29.9%) cannot be resolved from stored data; not established, not excluded.

**Decision point:** (iv) does not carry the failure and H1/H2 account for most of the measurable part, so D3 (Gate 2 pre-registration on a fresh family) is warranted. It tests whether a prevailing-quote rule and archive-timestamp sampling reproduce the archive; it does not rescue Part 1.

## D2(e) — fee re-score of published E (policy a / first-seen; one-way taker fee at first-seen mid; verdict labels NOT changed)
Fee source: series API `GET /trade-api/v2/series/{KXMLBHIT,KXMLBTEAMTOTAL}` (retrieved 2026-10-02): `fee_type=quadratic`, `fee_multiplier=0.5`
(KXMLBGAME: `quadratic_with_maker_fees`, 0.5). docs.kalshi.com `getting_started/fee_rounding.md` (retrieved 2026-10-02): `trade_fee = ceil_6dp(model_fee)`, rounding
rebated per order — it defers the model. `api-reference/exchange/get-series-fee-changes.md` (2026-10-02): enum of fee types, "no description of their distinct mechanics",
no formula or coefficient. `getting_started/fee_schedule` returned 404. **The venue's coefficient is therefore NOT established from accessible docs (the PDF is unread, GG-332).**
Both candidates are shown; the 0.035 row (0.5 × 0.07) is an inference, not a source.

| family | E published | fee k=0.07 (ADR-0016) | E_net | fee k=0.035 (inferred) | E_net |
|---|---|---|---|---|---|
| KXMLBHIT (n=31,532) | −0.00080 (CI game [−0.0056, +0.0051]) | 0.01099 | −0.01179 | 0.00549 | −0.00629 |
| KXMLBTEAMTOTAL (n=10,701) | −0.02403 (CI game [−0.0411, −0.0130]) | 0.01536 | −0.03939 | 0.00768 | −0.03171 |

Fee only subtracts: both published verdicts (NO) stand. Policy (c) E is not re-scored (maker/fill fee treatment unestablished). Divergence to register: ADR-0016's
`0.07*p*(1-p)` is not confirmed or contradicted by the venue's accessible documentation; per-order ceil rounding is not modelled (per-contract expectation used).
