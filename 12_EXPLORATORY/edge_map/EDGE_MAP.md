# Edge map — where the project has looked (W107.1, B-059)

Built 2026-11-09 from committed result files only; every row cites `path @ commit`. Machine-readable twin: `edge_map.json` (same rows). 40 hypotheses: 14 ACCRUING, 15 NO EFFECT NET, 7 RULED_OUT, 4 UNTESTED (W108.1 update 2026-11-10).

## In five sentences

1. The project has looked at 40 hypotheses across engines (NFL, NBA, NHL, MLB), ride/fade, momentum, longshot and pot-of-gold, props and retail, execution and fills, and live-market latency.
2. Nothing has survived costs in a forward test; the only cells with net above zero held out are two MLB total-line ride cells (117 and 30 games), measured once on a time split of the same archive with fills assumed at bid/ask, and both are still waiting on forward rows.
3. 7 hypotheses are ruled out and 15 show no effect net of cost, including every maker, taker-entry, momentum and retail-prop result so far.
4. 14 are still accruing: the NFL first-look cells reach their second look (n=150) between 2026-12-14 and 2027-01-09, the NBA engine cells have first looks from 2026-11-13 to 2026-11-25, NFL EXP-045 reads 2027-01-12, and MLB cells wait on judged games from 2027-03-01 and forward rows from about 2027-03-25.
5. 4 have never been tested: NBA, NFL and NHL props (the archive held only KXMLBHIT), multi-leg combos, the MLB backward test (void), and the candle scan for NFL; W108.1 ran the NBA/NHL ride board and pot of gold on 14 days of archive (the archive exists since 2026-10-28, GG-1330 resolved) and neither shows an effect net of cost; post-epoch fills sit at n=0 and the fee rule against demo fills is unconfirmed.

**Data epoch:** NO-side demo fills before 2026-11-06T01:03:42Z are mirror-priced (GG-1771/GG-1784); pre-epoch results are YES-only and never mixed with post-epoch. **Green rule:** green only if net > 0 held out (operator 2026-10-19); the two cells above qualify on the table but carry the caveats shown.

### Engines

| ID | Sport | Hypothesis | Gross | Cost | Net | n | Interval | Status | Next look |
|---|---|---|---|---|---|---|---|---|---|
| E01 | NFL | Game total vs market, T1 and T2 (EXP-037) | model Brier worse than market by +0.015 per rung | n/a (no edge to cost) | no edge: model loses to market | 72 games | +0.0151 [+0.0039, +0.0266] (T1) | RULED_OUT | closed (verdict issued) |
| E02 | NFL | Game total vs market, T3 (EXP-037) | first look reached; not read | n/a | not scored | 60 judged at first look | not read | ACCRUING | 2027-01-09 (second look at n=150) |
| E03 | NFL | Moneyline, spread, team total, T1-T3 (9 cells, EXP-037) | first look reached; not read | n/a | not scored | 60 judged at first look (cell-level counts vary) | not read | ACCRUING | 2026-12-14 to 2026-12-19 (second look at n=150) |
| E04 | NFL | QB-conditioned moneyline T1 (NFLQB) | sealed at 47 of 60 judged | n/a | not scored | 47 games | not read | ACCRUING | 2026-11-12/13 (projected) |
| E05 | NFL | Engine (EXP-045) net P&L: spread, total, team total | in-sample replay: spread -0.003, total +0.009, team total -0.021 per contract | fee included in replay | every interval includes 0 | judged n 429 / 442 / 337 (spread / total / team total) | spread [-0.039,+0.032]; total [-0.029,+0.045]; team total [-0.052,+0.008] | ACCRUING | 2027-01-12 (look 1, UNDERPOWERED; modal outcome not distinguishable ~85%) |
| E06 | NBA | Blend of engine and market price, v1/v2/v3 x moneyline, spread, total, team total (104.2) | out-of-sample log-loss gain <= 0 in every testable cell | n/a (descriptive) | no cell rejects at Holm/BH | 53 games | e.g. v1 total OOS log-loss gain -0.0160 [-0.038, -0.002] | NO EFFECT NET | see blend_test/plan_calendar.md |
| E07 | NBA | Engine v1, v2: moneyline, spread, game total, team total (EXP-044, 044b; 8 cells) | not read | n/a | not scored | 27-38 of 400 judged per cell | not read | ACCRUING | first looks 2026-11-17 to 2026-11-25, then monthly into Jan-Feb 2027 |
| E08 | NBA | Engine v3 (availability): spread, team total, moneyline, game total (EXP-044c) | not read; held-out 2025-26 Brier vs v2 core: spread -0.0076, team total -0.0025 (model vs model) | n/a | not vs market | 10-12 of 100 judged | spread [-0.0104,-0.0048] | ACCRUING | first looks 2026-11-13 to 2026-11-16 |
| E09 | NBA | Player points, availability-conditioned share (EXP-044d candidate) | engine set worse by +0.0131 at every strike | n/a | no edge | not stated in this map's sources | +0.0131 [+0.0106, +0.0158] | RULED_OUT | closed (not frozen) |
| E10 | NHL | Shrunk-spread challenger vs current engine (101) | Brier -0.0008 total, effect 0.0005-0.0008 | n/a (model vs model) | nothing vs market | 3,936 held-out games | total -0.00077 [-0.00140, -0.00013]; team total home includes 0 | RULED_OUT | closed (pre-registered rule: NO) |
| E11 | NHL | Regulation-total bias fix (model_pit), 100 | removes about a quarter of pooled bias (-0.080 to -0.059) | n/a | partial; not vs market | pooled regulation totals | not stated | NO EFFECT NET | none |
| E12 | NHL | Game total and moneyline vs market, T1-T3 (EXP-036) | not read | n/a | not scored | about 210 judged of 2,500 | not read | ACCRUING | projected 2028-04, or not reached |
| E13 | MLB | Two-factor model vs naive, moneyline and total (105.3) | Brier +0.0008 [-0.0010,+0.0025] ML; +0.0005 total | n/a (vs naive, not market) | not distinguishable | games in sample | see gross | NO EFFECT NET | none |
| E14 | MLB | Lineup-aware model vs Kalshi closing line (106.4) | moneyline model - market -0.0075 (market wins); total -0.0031 | n/a | moneyline: market wins; total: no gain | 753 games (ML), 735 (total) | ML [-0.0121,-0.0029]; total [-0.0075,+0.0011] | RULED_OUT | none |
| E15 | MLB | Game-market shadow cells: moneyline, run line, total, team total, T1-T3 (12 cells) | no judged games | n/a | not scored | 0 judged | n/a | ACCRUING | judged games begin 2027-03-01 |

### Ride / fade

| ID | Sport | Hypothesis | Gross | Cost | Net | n | Interval | Status | Next look |
|---|---|---|---|---|---|---|---|---|---|
| R01 | MLB, NBA, NHL, NFL | Ride and fade board, all families, held out (105.4) | no family passes out of sample after spread and fees | spread + fees included | 0 HELD_OUT cells | 160 held-out tests; 4 pass uncorrected (chance about 4) | Holm smallest adjusted p 1.0 | NO EFFECT NET | 2027-06-01 and 2027-07-15 (interim); MLB rows from ~2027-03-25 |
| R02 | MLB | EXP-042 backward test, 11 ride cells (W91.1) | void | n/a | 0 of 11 tested out of sample | 0 of 11 cells tested out of sample | n/a | UNTESTED | forward rows from ~2027-03-25 |
| R03 | MLB | Ladder ride: KXMLBTOTAL T0-2h, tight book, 2-5c gap (EXP-043 H-A) | net after spread and fee; held out once on a time split | spread and fees; fill at bid/ask assumed | +0.087 per contract | 117 games (second half) | [+0.034, +0.142] | ACCRUING (net>0 held out once) | forward rows from ~2027-03-25 |
| R04 | MLB | Ladder ride: KXMLBTOTAL T0-2h, tight book, 5c+ gap (EXP-043 H-B) | net after spread and fee; held out once | spread + fee included; fill at bid/ask assumed | +0.217 per contract | 30 games (second half) | [+0.095, +0.341] | ACCRUING (net>0 held out once) | forward rows from ~2027-03-25 |
| R05 | MLB | Ladder ride, the 5 other selected cells (36 testable, 7 selected) | not stated | spread and fees | FAILED held out | not stated | not stated | NO EFFECT NET | none |
| R06 | MLB, NFL (archive); NBA/NHL see R09 | Ladder ride, whole sample, taking the strike (W91.2) | gross: strike moves toward ladder +0.0133 at +1h | spread and fees | +0.007 per bet | 108,279 triggers / 2,191 games | [-0.002, +0.017] | NO EFFECT NET | none |
| R07 | NFL (NBA/NHL answered by R09) | Hold-out scan on candle data (W90.1) | underpowered | n/a | 0 candidates | 1 testable cell | n/a | UNTESTED | re-run at ~150 games per family |
| R08 | all | Fade, totals and team totals (cost-wall table, 106.2) | NFL team total -0.09 fit/-0.08 held-out; NFL total -0.12/-0.25; NHL total -0.37/-0.52; NBA -0.20/-0.18; MLB total +0.022 fit / +0.036 held-out | taker 1.5-2.3c each way; 4-8c props/team totals | MLB total interval [-0.008, ...] includes 0; the rest negative | NBA 23 games; others not stated | MLB total includes 0; the rest negative | NO EFFECT NET | none |
| R09 | NBA, NHL | Ride and fade board backward test, 14 days of archive (W108.1) | n/a | spread and fees (frozen ride_net) | 0 of 12 primary tests pass; best primary -0.003 per contract | 8 families; 30-41 held-out games each | best primary [-0.122, +0.106]; Holm rejected 0 of 12 | NO EFFECT NET | re-run at ~150 games per family |

### Momentum

| ID | Sport | Hypothesis | Gross | Cost | Net | n | Interval | Status | Next look |
|---|---|---|---|---|---|---|---|---|---|
| M01 | all | Moves of 3c+ continue or revert at 1h/3h (W90.3) | follow 0.000 to 0.004 per contract | following loses 4c (tight) to 13-17c (wide) | negative | n>=88 per slice | 0 of 97 testable cells routed to follow or fade | NO EFFECT NET | none |

### Longshot / pot of gold

| ID | Sport | Hypothesis | Gross | Cost | Net | n | Interval | Status | Next look |
|---|---|---|---|---|---|---|---|---|---|
| L01 | MLB, NFL | Longshot bias, 11 cells that survive cost in-sample (W89.2; re-run W98.2) | sign held in every re-run cell; net smaller than first reported | included | positive in-sample, smaller in all 11 | differs from the original run in every cell | several intervals include 0 | ACCRUING | forward rows from ~2027-03-25 (MLB); NFL KXNFLTOTAL during the season |
| L02 | MLB | Pot of gold, 17 pre-registered cells (105.6) | best KXMLBF5TOTAL 2-6h 90-95c fit +3.7c, held-out +5.5c on 32 games | 1-3c | 0 held-out ready | 40,520 settled first snapshots; 32 games in best cell | not stated | ACCRUING | MLB from ~2027-03-25 |
| L03 | NBA, NHL | Pot of gold in NBA and NHL (W108.1) | 14 days of archive, 4 Holm candidates | 1-3c | 0 routes held-out positive net | 3,794 joined snapshots; 243 NBA / 213 NHL games | Holm rejected 0 of 4 | NO EFFECT NET | re-read at ~150 games per sport |
| L04 | all | Multi-leg combos / parlays | cannot be measured yet | n/a | n/a | 0 | n/a | UNTESTED | not yet |

### Props / retail

| ID | Sport | Hypothesis | Gross | Cost | Net | n | Interval | Status | Next look |
|---|---|---|---|---|---|---|---|---|---|
| P01 | MLB | 50 prop and game-line cells, held-out, after Holm (106.3) | best KXMLBF5TOTAL >90c deep +2.3c | spread + fee | 0 net positive after Holm | held-out games per cell | best [+0.2c, +4.2c], Holm p 0.74 | NO EFFECT NET | none |
| P02 | MLB | KXMLBHIT retail gap | raw gap +1.2c [+0.6, +1.9] | included in net | net -1.4c [-2.7, +0.0] | 41,770 rows / 214 held-out games | [-2.7, +0.0] | NO EFFECT NET | none |
| P03 | MLB | Game lines (moneyline, spread, total) | negative | taker | net -3.2c | 74,839 rows / 1,188 games | [-5.0, -1.4] | NO EFFECT NET | none |
| P04 | NBA, NFL, NHL | Player and team props | archive holds only KXMLBHIT | n/a | n/a | 0 | n/a | UNTESTED | not yet (a gap, not a no) |

### Execution

| ID | Sport | Hypothesis | Gross | Cost | Net | n | Interval | Status | Next look |
|---|---|---|---|---|---|---|---|---|---|
| X01 | NFL, NBA, NHL | Fills: adverse selection, shadow orders (104.1) | 1-min markout -1.23c per fill, worse at higher price | n/a | negative | 99,864 usable orders; 13,164 filled (627 games) | E3 gap adjusted -2.6pp [-7.8, +2.4] | NO EFFECT NET | post-epoch rows when accrued (n=0 post-epoch) |
| X02 | NFL, NBA, NHL | Order placement rules (105.2) | no rest >=0.50: loss per fill -1.23c to -0.73c, P&L per order unchanged (-1.71c vs -1.67c) | fees included | negative in every price bucket | 65,217 orders / 17,135 fills / 1,800 games | post-at-bid +0.44c/order [+0.29,+0.61], fill rate -28.8 points | NO EFFECT NET | none |
| X03 | all | Maker quoting net of fees (106.2) | n/a | maker fee 0.0175 coef | -0.6c to -4.3c per fill in every bucket | not stated | none above 0 | RULED_OUT | none |
| X04 | NFL | ADR-0072 forward test (rest vs post), NFL as logged | (a) +0.190, (b) 0.376, (c) 30-min markout -0.0117 | n/a | ADOPT as logged; after GG-1771 correction INCONCLUSIVE | 41 games | (a) lower bound +0.088 as logged; YES-only (a) +.006 [-.100,.112] | ACCRUING | post-fix rows (epoch 2026-11-06T01:03:42Z) |
| X05 | NBA | ADR-0072 forward test, NBA | (a) holds, (b) fails | n/a | not computable after correction | not stated | not stated | ACCRUING | post-fix rows |
| X06 | NBA, NFL, NHL | Taking at the quote at decision time (forward entry cost) | taking at the quote loses about 0.10 per contract (NBA, NFL) | included | negative; intervals exclude zero (NBA, NFL) | NHL about 200 priced orders per arm; NBA/NFL not stated | NBA/NFL exclude 0; NHL +0.01 to +0.08 spans 0 | RULED_OUT | none |

### Latency

| ID | Sport | Hypothesis | Gross | Cost | Net | n | Interval | Status | Next look |
|---|---|---|---|---|---|---|---|---|---|
| T01 | MLB | Live-market latency thesis (T4M-PROJ), T-569 | price does not lag state in the data | n/a | pooled forward slope criterion fails | 398,865 rows / 8,325 tickers | cadence p50 103.9s | RULED_OUT | closed (current feature set only) |

## Sources and notes (path @ commit)

- **E01** 12_EXPLORATORY/nfl_first_look/results_W100_2.md @ 4fe12e3 ; 04_EXECUTION/PROOF_CALENDAR.md @ ef80ff9
- **E02** 04_EXECUTION/PROOF_CALENDAR.md @ ef80ff9 ; 12_EXPLORATORY/nfl_first_look/results_W101_2.md @ 67cf88a
- **E03** 04_EXECUTION/PROOF_CALENDAR.md @ ef80ff9 ; 12_EXPLORATORY/nfl_first_look/results_W101_2.md @ 67cf88a — Pre-registered modal outcome KEEP ACCRUING ~91%
- **E04** 04_EXECUTION/PROOF_CALENDAR.md @ ef80ff9
- **E05** 12_EXPLORATORY/nfl_engine_forward/results_W94_2.md @ ec92612 — In-sample replay, not a forward result
- **E06** 12_EXPLORATORY/quant_w104_blend/RESULT.md @ b78cc2b ; 12_EXPLORATORY/blend_test/plan_calendar.md @ 74729df — 0 of 8 testable cells reject; v3 had 9-11 games. NFL/NHL/MLB blend not computed
- **E07** 12_EXPLORATORY/blend_test/plan_calendar.md @ 74729df ; 12_EXPLORATORY/nba_engine_v3/results_W97_1.md @ c4afff4 — Power at w=.25 is 0.08-0.78
- **E08** 12_EXPLORATORY/nba_engine_v3/results_W97_1.md @ c4afff4 ; 12_EXPLORATORY/blend_test/plan_calendar.md @ 74729df — v3 cron install was refused by the classifier; no workaround tried
- **E09** 12_EXPLORATORY/nba_engine_v3/results_W97_1.md @ c4afff4
- **E10** 12_EXPLORATORY/nhl_engine/results_W101_1_nhl.md @ 666eeaf
- **E11** 12_EXPLORATORY/nhl_engine/results_W100_1.md @ 1b117ea
- **E12** 04_EXECUTION/PROOF_CALENDAR.md @ ef80ff9
- **E13** 12_EXPLORATORY/mlb_engine/RESULT_W105_3.md @ 921253c
- **E14** 12_EXPLORATORY/mlb_engine/RESULT_W106_4.md @ e0176e8 — Moneyline ruled out as tested; total is NO EFFECT NET. As-played lineups flatter the model
- **E15** 04_EXECUTION/PROOF_CALENDAR.md @ ef80ff9
- **R01** 12_EXPLORATORY/ride_board/RESULT.md @ 3e58045
- **R02** 12_EXPLORATORY/ride_cells/results_W91_1.md @ dc7f290 — Backward test void; forward test is the only one left
- **R03** 12_EXPLORATORY/ride_ladder/results_W91_2.md @ e8d2187 ; 12_EXPLORATORY/frozen_evidence_check/results_W98_2.md @ 805d4ca — Out-of-sample once, on a time split of the same archive; not a forward pass. Fills unmeasured. Carried as frozen EXP-043 H-A; the W98.2 frozen-evidence check did not re-run it
- **R04** 12_EXPLORATORY/ride_ladder/results_W91_2.md @ e8d2187 — 30 games; do not read the point estimate as size. Same caveats as R03
- **R05** 12_EXPLORATORY/ride_ladder/results_W91_2.md @ e8d2187 — 5 of 7 selected cells FAILED the held-out half
- **R06** 12_EXPLORATORY/ride_ladder/results_W91_2.md @ e8d2187 — NFL selected nothing; the NBA/NHL archive exists since 2026-10-28 and is tested in R09
- **R07** 12_EXPLORATORY/ride_market_scan/results_W90_1.md @ be44377
- **R08** 12_EXPLORATORY/quant_w106_costs/RESULT.md @ 0e612b8 — KXMLBHIT fade gross +0.008 on tight books, below cost
- **R09** 12_EXPLORATORY/edge_map/w108_1/RESULT_W108_1.md — Two non-primary tight-book FOLLOW-SPREAD cells have a positive held-out lower bound among 58 examined; not promoted
- **M01** 12_EXPLORATORY/momentum_j/results_W90.md @ f1d24f4
- **L01** 12_EXPLORATORY/longshot_bias/results_W89.md @ f50f49c ; 12_EXPLORATORY/frozen_evidence_check/results_W98_2.md @ 805d4ca — IN-SAMPLE, hold-to-settle. 66 BH-flagged cells, 53 erased by cost, 11 survive. W98.2: 11 of 13 frozen cells re-run, all DIFFER
- **L02** 12_EXPLORATORY/pot_of_gold/RESULT.md @ c2b883d — All 17 IN_SAMPLE; lottery-ticket overpay under 1c
- **L03** 12_EXPLORATORY/edge_map/w108_1/RESULT_W108_1.md — 62 NBA / 44 NHL routes still too thin to test; 40 / 26 failed held-out
- **L04** 12_EXPLORATORY/pot_of_gold/RESULT.md @ c2b883d
- **P01** 12_EXPLORATORY/quant_w106_props/RESULT.md @ 21bc755
- **P02** 12_EXPLORATORY/quant_w106_props/RESULT.md @ 21bc755 — Thin books lose 8-20c
- **P03** 12_EXPLORATORY/quant_w106_props/RESULT.md @ 21bc755
- **P04** 12_EXPLORATORY/quant_w106_props/RESULT.md @ 21bc755
- **X01** 12_EXPLORATORY/quant_w104_fills/RESULT.md @ cdcaa7a — Pre-epoch YES-only; post-epoch n=0
- **X02** 12_EXPLORATORY/quant_w105_orders/RESULT.md @ ee12477 — Pre-epoch YES-only
- **X03** 12_EXPLORATORY/quant_w106_costs/RESULT.md @ 0e612b8 — Fee check against demo fills UNCONFIRMED (probe refused)
- **X04** 12_EXPLORATORY/forward_test_nfl_final/results_W101_2.md @ 67cf88a ; 12_EXPLORATORY/gg1771_no_pricing/RESULT.md @ aae5e6c — ~46% of shadow orders were NO-side, mirror-priced before the fix
- **X05** 12_EXPLORATORY/gg1771_no_pricing/RESULT.md @ aae5e6c
- **X06** 12_EXPLORATORY/forward_entry_cost/results_W98_2.md @ 68ec470 — NHL not clearly negative
- **T01** 05_RESEARCH_EXPERIMENTS/RESULTS_SUMMARIES/T569_t4_latency_thesis_RESULTS.md @ f4e4236 — NOT SUPPORTED for the current feature set; other feature sets untested
