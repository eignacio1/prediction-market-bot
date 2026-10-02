# EXP-035 Gate 2 — KXMLBTOTAL candle-vs-archive agreement — RESULT: PASSED (7/7)

**Part 1 (EXP-035 board survey) stays FAILED as recorded; this gate does not relabel it.** Gate 2 only asks whether
candle-reconstructed prevailing quotes agree with the live PRICE_ARCHIVE on the one family where both exist.

**Store / reader (D4, if published):** see the D4 section below once written. Verdict file: `exp_output/BOARD_SURVEY_SPORTS_G2/gate2_result.json`.

Frozen spec: `05_RESEARCH_EXPERIMENTS/EXP035_GATE2_PREREGISTRATION_2026-10-02.md` (seed 35035, 400 tickers, null 0.01038). Run exactly as frozen; no threshold, seed, rule or population edited.
Fetch: 11,174 calls, 0 x 429, 0 errors, 3,740 s wall, single fetcher at the 3.3 req/s cap.

| Gate | Threshold | Measured | Pass |
|---|---|---|---|
| G1 ticker / usable-candle coverage | >= 0.98 | 1.0000 / 0.9895 | yes |
| G2 share within 0.01 on bid and ask | >= 0.80 | 0.9437 (n=1955; minute 1907, hourly 46, unmatched 2) | yes |
| G3 containment in neighbours | >= 0.95 | 0.9990 (n=1955) | yes |
| G4 abs(B_candle - B_ref) | <= 0.003 | 0.01904 vs 0.01882 -> 0.00022 (n=6780; 2313 excluded, no prevailing hourly) | yes |
| G5 abs(H_candle - H_ref) | <= 0.005 | 0.0100 vs 0.0100 -> 0.0000 | yes |
| G6 sign(E) match | same sign | E_candle -0.00134, E_ref -0.00156 (both negative) | yes |
| G7 tau buckets within 0.005 | all 7 | all 7 ok (see note) | yes |

Notes, stated plainly:
- G7 bucket [24,48): ref 0.010 vs candle 0.015 is a difference of 0.005 at the threshold, passing by floating-point margin only (candle 0.014999999999999958). Half-spread values sit on the 0.005 tick grid, so buckets are quantised and a one-tick difference is exactly the tolerance. The gate passed as frozen; the quantisation is the reason the margin is thin, not evidence of strong agreement.
- G4 excluded 2313 of 9093 tickers for lacking a prevailing hourly candle; the comparison is on the remaining 6780 with the same code on both sides.
- G6: E is negative on both paths, i.e. the same sign; magnitude differs by 0.00022. This says nothing about edge; it says the reconstruction agrees with the archive.
- Scope: one family (KXMLBTOTAL). Agreement here licenses candle reconstruction for the same market structure; it does not by itself validate other series, which is why D4 publishes provenance per row.
- The KXMLBTEAMTOTAL secondary re-run is not part of the verdict.
