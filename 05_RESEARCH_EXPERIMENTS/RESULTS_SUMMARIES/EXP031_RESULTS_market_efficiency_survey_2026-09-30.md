# EXP-031 — Cross-family market-efficiency survey: RESULTS

**Task:** T-599 · **Gap:** GG-324 · **Pre-registration:** `05_RESEARCH_EXPERIMENTS/EXP031_MARKET_EFFICIENCY_PREREGISTRATION_2026-09-30.md` (pushed alone, 803f881, before any calibration statistic existed; unamended).
**Raw output:** `exp_output/EXP-031-MKT-EFF-SURVEY/{d1_inventory,d1_settled_coverage,d3_d4_results}.json`; code `scripts/market_efficiency_survey.py`, tests `tests/test_market_efficiency_survey.py` (6 pass). Measures the market only; no model, order, pool or sizing touched.

## Headline
**Zero CANDIDATES.** Of 14 families, 10 MLB families were measured and labelled; 4 NFL families are INCONCLUSIVE under the pre-registered n/days rule. Nothing beat KXMLBHIT on E under the frozen rule. This is a statement about calibration bias at the first-seen snapshot over a ~2-month window; it is not a verdict on any family or sport (see Limits).

## D1 — Inventory (premise check)
The brief's "119 files / 1.82M rows" did not hold: **122 directory entries (62 `prices_*.jsonl` + 59 `depth_*.jsonl` + `prices_2026-08-01.jsonl.BROKEN_FIRSTRUN`, which was NOT read — a first-run file set aside; its rows are excluded from every figure here), ~2.12M price rows, 14 families** (incl. KXMLBF7). Window 2026-08-01 → 2026-10-01 (NFL from 09-05). Every row is `status=active`; **the archive contains no settlement**, so outcomes were taken from Kalshi's own `result` (public read-only endpoint), 24 MB cached under `settlements/`. All 14 families are measurable; none UNMEASURABLE. Per-family rows / tickers / days / snapshots-per-ticker-day (median 6–24) / field coverage / settled coverage are in `d1_inventory.json` and `d1_settled_coverage.json`. Fields are uniform across families (19, 100% present); `volume>0` ranges 28% (F7) to 100% (KXNFLGAME); two-sided quote share 70% (HIT) to 99.8% (NFLGAME). Depth: sample only (~1.4k–2.8k rows/family; KXMLBF7 7 rows over 2 tickers; KXMLBHIT 68% usable). Settled ticker coverage: MLB ≈99% (yes/no), `scalar` 2–14 per family excluded; NFL 62–437 tickers per family not yet settled (games unplayed).

## D3/D4 — Table (B vs own null; E = B − null median − H; day-clustered and game-clustered 95% CIs on E)
| Rank | Family | Label | n | B | null med / 99.5% | Clears? | H | E | E CI game | E CI day |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | KXMLBHIT | REFERENCE | 31,532 | .0137 | .0045/.0082 | yes | .010 | −.0008 | [−.0056,.0051] | [−.0052,.0059] frag |
| 2 | KXMLBSPREAD | NO BETTER | 6,132 | .0092 | .0104/.0206 | **no** | .010 | −.0111 | [−.0140,.0062] | [−.0137,.0039] frag |
| 3 | KXMLBTOTAL | NO BETTER | 9,093 | .0137 | .0104/.0190 | **no** | .015 | −.0117 | [−.0165,.0073] | [−.0159,.0102] frag |
| 4 | KXMLBTEAMTOTAL | NO BETTER | 10,701 | .0257 | .0098/.0173 | yes | .040 | −.0240 | [−.0372,−.0147] | [−.0594,−.0156] |
| 5 | KXMLBGAME | NO BETTER | 1,560 | .0211 | .0199/.0417 | **no** | .040 | −.0388 | [−.0463,−.0023] | [−.0474,.0013] frag |
| 6 | KXMLBF5TOTAL | NO BETTER | 5,278 | .0629 | .0130/.0242 | yes | .145 | −.0951 | [−.1338,−.0456] | [−.1659,−.0132] |
| 7 | KXMLBF5 | NO BETTER | 2,268 | .0490 | .0177/.0355 | yes | .160 | −.1287 | [−.1390,−.1120] | [−.1448,−.1058] |
| 8 | KXMLBF3 | NO BETTER | 2,268 | .0465 | .0152/.0344 | yes | .175 | −.1437 | [−.1588,−.1316] | [−.1820,−.1304] |
| 9 | KXMLBF7 | NO BETTER | 2,261 | .0498 | .0166/.0363 | yes | .200 | −.1667 | [−.1723,−.1527] | [−.2557,−.1396] |
| 10 | KXMLBF5SPREAD | NO BETTER | 3,024 | .0899 | .0133/.0309 | yes | .275 | −.1984 | [−.2148,−.1794] | [−.2270,−.1614] |
| — | KXNFLGAME | INCONCLUSIVE (n=96) | | .148 | .102/.189 | no | | | | |
| — | KXNFLSPREAD / TEAMTOTAL / TOTAL | INCONCLUSIVE (distinct decision days <20) | 1,314 / 1,302 / 972 | .023/.048/.048 | .024/.045/.057 | no/yes/no | | | | |

**Families that FAIL their null (not candidates, not exploitable):** KXMLBSPREAD, KXMLBTOTAL, KXMLBGAME, and all four NFL families except KXNFLTEAMTOTAL (itself INCONCLUSIVE). **Families that clear their null but are not candidates:** KXMLBHIT (reference), KXMLBTEAMTOTAL and the five F-family series: a calibration gap exists in the first-seen quote, but E < 0 because the cost of crossing exceeds it.

Bucket pattern (full detail in JSON): KXMLBHIT realised frequency exceeds price in every populated bucket (+0.6 to +2.8 pts, most at 0.1–0.3 — the favourite-longshot signature in the opposite direction to a "longshots are overpriced" story: yes was underpriced). KXMLBTEAMTOTAL: yes underpriced at 0.5–0.7 (+1.4 to +3.7), overpriced at 0.2–0.4 (−2.7 to −4.4). KXMLBGAME: the 0.2 and 0.7 buckets have n=18 and n=11 and carry the gap; the bulk (0.4–0.5) is calibrated within 1.7 pts. F5SPREAD's mid is not a price: median vig 0.55, H=0.275 — wide stale early quotes.

## D5 — Join (shortlist)
**Shortlist: empty.** No family is a CANDIDATE, so no family is ordered for substrate work. For the record, from `PREGAME_FEATURE_ARCHITECTURE.md` §1.2/§3.2: MLB game-market families (moneyline, run line, totals, team totals, F3/F5/F7) have **no real forecaster** (default `StubMLBGameMarketForecastModel`), and the pre-game MLB factor classes beyond ba_l10/opp-SP/park are *not stored* (platoon, bullpen, lineup slot, weather, umpire, defence; build waits on MLB off-season, §3.3); `get_opp_runs_scored()` is consumed by nothing in a run path. `T586_absent_attribute_pricing.md` records costs per attribute (payload-field vs new accessor vs new C1) and states informativeness is unmeasured. Registry: KXMLBHIT has T4M_PROJ ACTIVE and T1/T2/T3 SHADOW; every other MLB/NFL `(MarketType, band)` cell found is `NOT_IMPLEMENTED`. Net: even a candidate in these families would have no feature substrate or cell at acceptable cost today, so the decision would move to data acquisition and cell registration — but there is no candidate to motivate it.

## Limits (binding)
1. **First-seen snapshot rule penalises early-listed families.** F3/F5/F7/F5SPREAD/TEAMTOTAL are listed days ahead; at first sight the quote is wide and H is large (up to 0.275), which drives E negative by construction and makes the mid a poor price (F5SPREAD vig 0.55). The result for those families is "not tradable at first sight", not "efficient". A later-snapshot test (e.g. the last pre-game quote) would be a *new* pre-registered experiment; it was not run here and the rule was not changed after results.
2. **Null band is narrow** (independent Bernoulli draws; complementary tickers within a game are correlated, 2–44 per event). Families that "clear" (F-family, TEAMTOTAL) may do so partly on that; the two fragile-flagged and the failures are conservative the other way.
3. B has a positive chance floor; only excess over the null was used. Window is ~2 months; NFL ~4 weeks, hence INCONCLUSIVE.
4. KXMLBHIT clears its null with E≈0 (CI spans 0, day-fragile): its yes-underpricing is real in-sample but not larger than its spread cost. This does not overturn or confirm EXP-029; no family, KXMLBHIT included, is recommended for or against.
5. Kalshi `result` is the venue's own settlement; voids (`scalar`) excluded.
6. Vig, spread stability, tick discreteness, convergence and depth were reported/inventoried, not ranked (per pre-registration); convergence was not computed (needs in-game snapshots; coverage differs by family).
