# W89.2 — Where the line itself is wrong: calibration of Kalshi sports prices, and overreaction after large moves

Block 89.2 · claim T-1250..T-1252 / GG-1250..GG-1254 · run 2026-10-27 · code `calib.py`, `run_w89_2.py`, `survivors.py`; tests `tests/test_w89_2_longshot_bias.py`; raw outputs `out/`.
Measures the MARKET only. No model, order, gate, runner, pre-registration, stake or `kelly_fraction` was touched. **Every cell below is a CANDIDATE for a pre-registered market-anchored adjustment, not a trade.** All survivor statistics are in-sample.

## Method (with when-it-applies)
- **Data:** local price archive (`exp_output/PRICE_ARCHIVE/prices_*.jsonl`, 89 files, ~20-min snapshots) joined to Kalshi's own settled `result` (public unauthenticated GETs). 73,662 settled tickers; 164,245 ticker×tier first snapshots; 43,787 unsettled ticker×tier skipped. Families: MLB game-market families + KXMLBHIT, and NFL GAME/SPREAD/TOTAL/TEAMTOTAL.
- **Cell:** family × time-to-start tier × price bucket × book class. Price p = mid of the **first two-sided pre-start snapshot in the tier** (extends the EXP031 "earliest two-sided snapshot" rule to a fixed tier; EXP031 is not re-run or contradicted). Buckets: 0-1,1-5,5-10,10-15,…,90-95,95-99,99-100c.
- **Tiers:** MLB by hours to first pitch (T>24h, T6-24h, T2-6h, T0-2h; start parsed from the ticker HHMM, **read as ET — assumption**). NFL tickers carry the date only: D0/D1/D2+ by ET calendar day.
- **Book class:** tight = half-spread ≤ 1c ("deep"), wide otherwise; "all" is both. The archive records spread, not size — tight/wide is a proxy for depth, not depth.
- **Test:** cluster-robust (by game/event) z-test of mean(y − p) = 0. Applies only when a cell has ≥ 30 games and n·p̄, n·(1−p̄) ≥ 5; otherwise the cell is DESCRIPTIVE with no p-value. **Net edge:** the side the gap points to, entered at the quote (YES at ask, NO at 1 − bid), minus the k007 fee, with a game-clustered bootstrap 95% interval (1000 resamples, seed 20261027).
- **Family-wise statement:** Benjamini-Hochberg at q = 0.10 across **all 1,258 testable Part A cells** (every family × tier × bucket × book view, the overlapping views included, which makes BH conservative-to-neutral under positive dependence) and, separately, across the 40 testable Part B cells. FDR ≤ 10% within each family of tests.
- **Survival:** BH-flagged AND split-half (by time) sign agrees with the full-sample gap AND net-of-fee lower bound > 0 AND not NFL D0.
- **Quant bar (tests):** a simulated market with a known −6c longshot bias is recovered (p < 1e-3, NO side); 40 replicates of 25 calibrated cells never flagged more than 10 times and the false-positive rate of the raw test matched α in a 1000-sim check (4.6% at α = 0.05); a known mean-reverting walk is detected and a random walk is not; a 1-point bias is significant but net_lo < 0 after fee.

## Part A — result
2,219 cells, 1,258 testable. **66 BH-flagged** (28 all-book, 5 tight, 33 wide); 29 pass Bonferroni. **53 of the 66 have a net-of-fee lower bound ≤ 0** — a real gap between mid and settlement that the spread and fee erase (mostly wide-book F5/TEAMTOTAL cells). Net of cost, **11 cells survive** (listed; overlapping views of one cell kept as separate rows):

| Family | Tier | Bucket | Book | n | games | mean price | settled YES | gap | side | net/contract | net 95% lo | p |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| KXMLBHIT | T0-2h | 20-25c | all | 1892 | 368 | .222 | .272 | +.050 | YES | +.027 | +.0065 | 3e-6 |
| KXMLBHIT | T0-2h | 20-25c | tight | 1151 | 339 | .222 | .285 | +.063 | YES | +.044 | +.017 | 2e-6 |
| KXMLBF5TOTAL | T6-24h | 90-95c | all | 143 | 138 | .927 | .993 | +.067 | YES | +.038 | +.022 | <1e-12 |
| KXMLBF5TOTAL | T6-24h | 90-95c | wide | 111 | 107 | .925 | .991 | +.066 | YES | +.033 | +.011 | 8e-14 |
| KXMLBF5TOTAL | T2-6h | 90-95c | tight | 85 | 83 | .936 | .988 | +.053 | YES | +.043 | +.017 | 8e-6 |
| KXNFLTOTAL | D1 | 5-10c | all | 154 | 92 | .075 | .026 | −.049 | NO | +.038 | +.0065 | 2e-3 |
| KXMLBSPREAD | T>24h | 20-25c | tight | 186 | 147 | .222 | .151 | −.071 | NO | +.052 | +.0026 | 4e-3 |
| KXMLBTEAMTOTAL | T6-24h | 15-20c | tight | 49 | 40 | .172 | .061 | −.111 | NO | +.095 | +.0085 | 2e-3 |
| KXMLBF5 | T2-6h | 10-15c | all | 44 | 44 | .137 | .046 | −.092 | NO | +.078 | +.0087 | 3e-3 |
| KXMLBTOTAL | T0-2h | 85-90c | wide | 52 | 52 | .873 | .981 | +.108 | YES | +.089 | +.047 | 3e-8 |
| KXMLBF7 | T0-2h | 40-45c | wide | 121 | 88 | .429 | .529 | +.101 | YES | +.065 | +.0006 | 3e-3 |

Pattern: the surviving structure is **favourite-longshot at the totals ends** (high-priced "over/under hits" YES at 85-95c settling ~98-99%; low-priced longshots at 5-15c settling below price), plus one mid-price YES under-pricing in KXMLBHIT 20-25c close to start. Only the KXMLBHIT cell has n above ~200 and tight-book support; the rest have n of 44-186 and extreme buckets where the normal approximation rests on small expected counts (n·(1−p̄) ≈ 5-10 at 90-95c). Thin cells (n < 100) should be treated as leads, not findings.

**Thin vs deep:** tight books carry 5 of 66 flags and 4 of the 11 survivor rows; wide-book flags mostly die at the spread (53 of 66 flags have net_lo ≤ 0). Where a cell survives in both views (KXMLBHIT) the tight view has the larger net, as expected when the spread is the cost.

**NFL D0 excluded (contamination):** KXNFLTOTAL D0 5-10c NO also passed, but NFL tickers carry the date only, so a "D0" first snapshot may be in-play. Not counted and not a candidate. (GG-1252.)

## Part B — overreaction after large pre-game moves: DESCRIPTIVE / null
Moves ≥ 5c between consecutive snapshots ≤ 1h apart; later mid at +1h and +3h; cost = both half-spreads + 2 × k007 fee; one move per 9 snapshots per ticker; game-clustered. 40 of 56 cells testable. **All 40 are BH-flagged for net ≠ 0, and every net is NEGATIVE (−0.05 to −0.31)**; that flag says the round trip loses, not that there is reversion edge. Gross reversion is ≈ 0 to +0.10 (largest: KXNFLTEAMTOTAL down-moves at +3h, gross +0.096, net −0.12, 95% [−0.155, −0.090], 60 games; KXMLBF5SPREAD up at +3h gross +0.063, net −0.155). **Part B survivors (BH and net_lo > 0): 0.** No score data is joined, so Part B is pre-game only (NFL D0 excluded) and cannot separate news from flow; everything here is DESCRIPTIVE.

## Assumptions and limits (binding on how this is read)
1. MLB ticker HHMM read as ET (consistent with run_ts on a known game; not proven for every family).
2. NFL tiers are date-based; D1/D2+ are pre-game by construction, D0 is not.
3. Snapshot cadence ~20 min; "first snapshot in tier" is within one cadence of the tier boundary at best, and archive coverage starts 2026-08-01 (NFL 2026-09-05).
4. Survival is in-sample with a split-half sign check only; no out-of-sample hold-out exists yet. BH at q = 0.10 over 1,258 tests permits up to ~10% of the 66 flags to be false; the net-of-fee and split-half filters are not themselves corrected tests.
5. Entry at the quote assumes a fill at the displayed price at snapshot time; depth is unknown (spread proxy only), so net numbers are an upper bound for size.
6. Calibration gap is necessary, not sufficient: it does not say we can pick the side before it is priced, and it is a statement about the archived window, not the families forever. KXMLBHIT 20-25c T0-2h YES lines up directionally against EXP-029's HARMFUL verdict on one frozen model; this is a different question (the market's price, not the model) and neither confirms nor overturns it.

## Gaps registered
NHL, NBA and every parlay/multi-leg family are **not archived** → no calibration test possible (GG-1250). Candle history is partial and local-only (EXP-035 numbers void) (GG-1251). NFL date-only tickers (GG-1252). MLB HHMM-as-ET (GG-1253). No out-of-sample hold-out window (GG-1254).

## Operator line
**Three survivors deserve a pre-registration (still candidates, in-sample):** (1) KXMLBHIT T0-2h 20-25c YES — the only large-n, tight-book cell (n = 1,892 / 368 games, net +2.7c, lower bound +0.65c; tight view +4.4c); (2) KXMLBF5TOTAL T6-24h 90-95c YES (net +3.8c, lower +2.2c, n = 143); (3) KXNFLTOTAL D1 5-10c NO (net +3.8c, lower +0.65c, n = 154). Pre-register price band, tier, side, entry-at-quote and a forward window with n set from these variances before any further row is read; the other eight are leads. No Part B cell qualifies.
