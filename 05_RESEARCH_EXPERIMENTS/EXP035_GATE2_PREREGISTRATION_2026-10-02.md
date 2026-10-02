# EXP-035 Gate 2 — pre-registration (T-605, 2026-10-02)

**Status: written and pushed BEFORE any KXMLBTOTAL candle was fetched or looked at.** The only KXMLBTOTAL data read so far is
archive + settlements (counts below) and the EXP-031/032 published family rows.

**This is a NEW test, designed after Part 1 failed (GG-333).** Part 1 (frozen e28166a, FAILED at 0972862, unrescued) is not
relabelled, re-run or re-scored by anything here. Part 1's candle numbers stay VOID. A Gate 2 PASS would say only that a
prevailing-quote rule sampled at archive timestamps reproduces the archive on a family Part 1 never touched; it validates nothing
retroactively.

## 1. Family choice — rule fixed before looking at candles
Rule: among archived MLB families, rank by settled-binary-ticker count (EXP-032 `ref.included_settled_tickers`); exclude any family
used in Part 1 (KXMLBTEAMTOTAL) or touched in D2 (KXMLBHIT, fee-rescored in D2(e)); take the largest remaining.

Inputs the rule used: KXMLBHIT 31,532 (excluded) · KXMLBTEAMTOTAL 10,701 (excluded) · **KXMLBTOTAL 9,093** · KXMLBSPREAD 6,132 ·
KXMLBF5TOTAL 5,278 · KXMLBF5SPREAD 3,024 · KXMLBF5 2,268 · KXMLBF3 2,268 · KXMLBF7 2,261 · KXMLBGAME 1,560.
**Chosen: KXMLBTOTAL.** Archive check (archive + settlements only): 9,185 tickers with a usable two-sided archive row, 9,093 binary-settled;
archive span 2026-08-01T23:01:11Z → 2026-10-02T05:40:02Z.

## 2. Changes from Part 1 (only what D2 found mismatched)
1. **Matching rule = EXP-034's frozen rule: the close of the latest candle at or before t.** 1-minute candles are fetched over
   [t−3600 s, t+120 s]. Prevailing = the 1-minute candle with the greatest `end_period_ts` ≤ t. If none exists in that hour the quote
   was unchanged for the hour, so the latest hourly candle with `end_period_ts` ≤ t supplies it. If neither exists the snapshot is
   unmatched and counts as a failure in G2 and G3 (as in Part 1).
2. **B and H are computed at the archive's own first-seen timestamp t0 per ticker** (EXP-031 `decision_snapshots`: earliest archive row with a non-null
   two-sided quote), using the hourly candle with the greatest `end_period_ts` ≤ t0 and bid>0, ask>0. Tickers with no such candle (first-seen inside the
   market's first hour) are excluded from G4/G5/G6, counted and reported. Because that changes the population, the **G4/G5/G6 reference is the archive's
   B/H/E recomputed on the same ticker subset with the same code** (`calib_gap`, median half-spread, null = EXP-031 family null 0.01038 from
   B−H−E of the published row). The published all-ticker row is printed alongside: B 0.01373, H 0.015, E −0.01165.

NOTHING ELSE CHANGES: window start, 0.01 agreement tolerance, usable = bid>0 and ask>0, G3 neighbours = previous/matched/next *rows* of the sorted 1-minute
series (when the match came from an hourly fallback, only that hourly candle's low/high), G7 hourly-by-tau construction, scalar settlements excluded.

## 3. Sampling and fetch
- G2/G3 sample: 400 tickers drawn with `numpy.random.default_rng(35035)` from the sorted tickers present in both archive and the listed-market set; for each, the archive
  rows at positions 0, 0.25, 0.5, 0.75, 1.0 (index round(pos·(n−1))), t = that row's run_ts. **Seed 35035 (Part 1 used 20261002).**
- Hourly candles for every ticker on both sides over [max(open_time, 2026-08-01T23:01:11Z), close_time+3600], period 60 (G1, G4–G7).
- Endpoint: historical when settled before 2026-08-03T00:00:00Z, else live. Raw payloads to the append-only idempotent store.
- Rate: one process, token bucket ≤3.3 req/s aggregate, halve on any 429. No background process left.

## 4. Thresholds — IDENTICAL to Part 1, none loosened
G1 ticker and usable-candle coverage ≥ 0.98 · G2 share within 0.01 on bid and ask ≥ 0.80 · G3 containment ≥ 0.95 · G4 |B_candle − B_ref| ≤ 0.003 ·
G5 |H_candle − H_ref| ≤ 0.005 · G6 sign(E_candle) = sign(E_ref) · G7 every measured EXP-032 tau bucket within 0.005 (KXMLBTOTAL measured buckets: all seven).
**Gate 2 PASSES only if G1–G7 all pass on KXMLBTOTAL.** Any miss = FAIL: candles are not validated for survey use; register, log, report, stop (no D5).

## 5. Secondary, not part of the verdict
KXMLBTEAMTOTAL re-run under the same two changes: stored Part 1 hourly candles + a new [t−3600,t+120] 1-minute fetch for the same 400 tickers/5 positions Part 1 drew
(seed 20261002 re-used only to reproduce that sample). Reported beside Gate 2, never counted toward PASS/FAIL, never used to relabel Part 1.

## 6. Reporting
Every gate printed against its threshold with n, plus: matched-by-1-minute vs hourly-fallback vs unmatched counts; excluded-first-hour ticker count; archive-vs-candle B/H on the identical subset.
