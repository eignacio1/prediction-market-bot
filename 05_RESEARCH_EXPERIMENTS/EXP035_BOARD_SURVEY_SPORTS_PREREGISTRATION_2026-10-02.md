# EXP-035 — Kalshi sports board beyond MLB/NFL: net of cost and fee

**Status:** PRE-REGISTERED, PART 1 (candle correctness gate) — FROZEN ON PUSH. Part 2 (cohort rules, cost surface, policies, decision rule) is added by a later commit labelled PART 2, pushed before any outcome statistic on a new family is computed. Part 1 is not edited by Part 2. Any change to either is a commit labelled AMENDMENT with its reason, made before the affected statistic is computed.
**Task:** T-604 · **Gaps:** GG-329, GG-332 · **Predecessors:** EXP-031, EXP-032, EXP-033 · **Wave 45 block 45.1**
**Date:** 2026-10-02 (UTC) · **Decisions logged:** false (one DECISION_LOG entry at close)

## 0. What was inspected before Part 1 was written

Endpoint behaviour and archive structure only. No candle-vs-archive comparison, no B, H or E from candles, no outcome from any new family.
- `GET /historical/cutoff`: `market_settled_ts` = 2026-08-03T00:00:00Z. Markets settled before it are served only by `/historical/*`, markets settled after it only by live `/markets` and the live candlestick endpoint.
- One historical NHL ticker, hourly and 1-minute candles: fields `end_period_ts`, `yes_bid`/`yes_ask` {open, high, low, close}, `price` {open, high, low, close, mean, previous}, `volume`, `open_interest`. `price` is null and volume is "0.00" while no trade has occurred. The OHLC low/high of a quote include empty-book extremes (bid low 0.01, ask high 1.00), so a range test on low/high is loose by construction. Candle `close` is the end-of-period quote.
- Archive KXMLBTEAMTOTAL: 319,984 rows, 10,780 tickers, 2026-08-01T23:01:11Z to 2026-10-01T02:20:02Z, 1,440 distinct run_ts, median gap 20 minutes. EXP-031 stored B=0.02572, H=0.04, E=-0.02403, null median 0.00975, 10,701 settled tickers included.

## 1. Part 1 — correctness gate (D1b). If it fails, every candle-based number is VOID.

**Population.** KXMLBTEAMTOTAL, all tickers whose archive rows lie in the archive window above. Candle-side universe: `/historical/markets` (settled before cutoff) plus live `/markets?status=settled` (after), both with `series_ticker=KXMLBTEAMTOTAL`, keeping markets with any quote period overlapping the window.

**Snapshot definition (candles alone).** Hourly candles (period_interval=60) over [window start, close_time]. A candle is usable if `yes_bid.close > 0` and `yes_ask.close > 0` (both non-null). Candle mid = (yes_bid.close + yes_ask.close)/2; half-spread = (yes_ask.close − yes_bid.close)/2. The decision snapshot per ticker is the earliest usable candle with `end_period_ts` ≥ window start. No archive timestamp is used to choose it.

**Matching rule for quote-level comparison.** A fixed-seed sample (numpy default_rng seed 20261002) of 400 tickers drawn from tickers present in both sources. For each, five archive snapshots at index positions 0, 25%, 50%, 75%, 100% of its usable snapshots sorted by run_ts. For each snapshot at time t, fetch 1-minute candles over [t−120s, t+120s]. The containing minute is the candle with the smallest `end_period_ts` ≥ t. Compare archive `yes_bid`/`yes_ask` to that candle's `yes_bid.close`/`yes_ask.close`.

**Tolerances (all must hold; written before any comparison was run).**
- G1 coverage: ≥ 98% of archive tickers with a settlement record appear in the candle-side universe; and of tickers on both sides, ≥ 98% have at least one usable hourly candle if they have a usable archive snapshot.
- G2 close agreement: share of sampled snapshots with |archive yes_bid − candle yes_bid.close| ≤ 0.01 AND |archive yes_ask − candle yes_ask.close| ≤ 0.01 is ≥ 80%.
- G3 range containment: share of sampled snapshots whose archive bid lies in [min low, max high] of candle yes_bid over the minute before, containing and after, and likewise for ask, is ≥ 95%.
- G4 B: |B_candle − 0.02572| ≤ 0.003, with B computed by `market_efficiency_survey.calib_gap` on candle-first-seen mids and the EXP-031 settlement cache.
- G5 H: |H_candle − 0.04| ≤ 0.005.
- G6 verdict: sign of E_candle = B_candle − 0.00975 − H_candle equals the sign of −0.02403 (negative).
- G7 H surface: the median hourly-candle half-spread in the pregame tau buckets used by EXP-032 (start clock from ticker) is within 0.005 of EXP-032's measured-cell median for the same bucket, for every EXP-032 measured KXMLBTEAMTOTAL tau bucket. The EXP-032 number is read from its `results.json`.

**Failure rule.** Any of G1–G7 failing: candle-based numbers are VOID, D2 and D3 are not extended to outcome statistics, the discrepancy is registered in the gap log, and the work is handed back after D1. Which gate failed and by how much is reported without rescue.

**Outcomes.** Computing B_candle uses settlements from the EXP-031 cache only; no new family outcome is touched in Part 1.
