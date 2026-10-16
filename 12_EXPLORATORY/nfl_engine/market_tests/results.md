# W77.2 -- Is each NFL factor REAL, PRICED, or INVISIBLE? (market-side verdicts)

EXPLORATORY. Plan frozen in `PLAN.md` before any computation. Data: rolling-origin 2020-2025 test set (1,612 games, identical to stage 3);
closing lines (nflverse `spread_line`, `total_line`, de-vigged moneyline) are the regression TARGET only, never a model input (GAP-4 / GG-733).
Files: `closing_line.json`, `power.json`, `timing.json`; code `extract_terms.py`, `closing_line.py`, `power.py`, `timing.py`. DEPTH D5(b). Recommendations only.

## A.1 Power -- was "no gain" informative?

MDE at 80% power = 2.8 x SE of the stage-3 paired dBrier (SE from its CI); injection = outcomes redrawn as if the term were FULLY real
(normal margin/total, sigma from data: 13.15 / 13.34), 500 repeats, P(BEATS) = share with CI upper < 0.

| Comparison | ml | spread | total | team_total | observed dBrier (ml / spread / total / team_total) |
|---|---|---|---|---|---|
| E vs B (F8) MDE80 | 0.0017 | 0.0015 | 0.0014 | 0.0010 | -0.0007 / -0.0007 / +0.0003 / -0.0005 |
| F vs C (F8 on C) MDE80 | 0.0017 | 0.0015 | 0.0014 | 0.0010 | -0.0007 / -0.0007 / +0.0003 / -0.0005 |
| C vs B (F5/F6) MDE80 | 0.0004 | 0.0003 | 0.0003 | 0.0002 | +0.0001 / +0.0001 / -0.00003 / +0.00003 |

Injection (term fully real): **F8 P(BEATS) = 19.8% ml, 21.4% spread, 20.6% total** (mean injected dBrier -0.0006 to -0.0007, which matches the *observed* -0.0007).
**F5/F6 P(BEATS) = 4.4% / 5.4% / 3.4%** -- at the false-positive floor; the term (mean shift 0.10 pts) is too small for 1,612 games to see.

**Reading:** the F8-sized outcome test detects a fully real F8 about one time in five. "No BEATS" for F8 was NOT informative; the observed gain is exactly the size a real term would give, just inside the noise.
For F5/F6 the test could never have said yes; "MATCHES" there is uninformative too.

## A.2 Closing line -- share of each term the market prices

close = a + b0 x engine_v0 + b x term (point-in-time inputs; bootstrap B=2000, seed 20261014, 95% CI). b = share priced (1.0 = fully, in the term's own points).
Sanity: corr(spread_line, margin) = 0.455 (sign convention OK). N=1,612 (F8-populated 1,436 gives the same numbers to 2 decimals).

| Close | engine_v0 coef | F5/F6 b [CI] | F8 b [CI] | R2 (engine only -> +terms) |
|---|---|---|---|---|
| spread | 0.81 [0.78, 0.84] | -0.36 [-1.27, 0.61] | **0.67 [0.45, 0.87]** | 0.658 -> 0.668 |
| total | 1.03 [0.99, 1.08] | 0.32 [-0.48, 1.10] | **0.34 [0.16, 0.51]** | 0.543 -> 0.547 |
| ml (logit) | 0.112 [0.109, 0.116] | -0.04 [-0.17, 0.10] | **0.094 [0.065, 0.120]** (0.84 of engine scale) | 0.677 |

F8: the close carries a statistically clear share (CI excludes 0) and the spread CI excludes 1.0 -- roughly two-thirds priced on spread, a third on total (total CIs are wide; note F8's term SD ~0.9 pts).
F5/F6: term SD is 0.18 pts, so the regression is blind: CIs span 0 AND 1.

## B.3 Timing -- does the price move after the information becomes public?

Archive coverage: **zero 2026 games have candles** (2026 KXNFLGAME markets are listed, none fetched); candles cover 2025 Oct-2026 Jan only (411 one-minute sets, 185 linked home-side games, 147 Sunday F8 games). Each set spans exactly 48h ending around settlement, so the series *starts at about the Friday report*.
- REPORT window (Fri 12:00 -> Sat 12:00 ET): **not testable** (n=0 -- no candles before the report). Needs candles from Wednesday on.
- INACTIVES window (ko-150min -> ko-30min): slope of home-mid on F8 term = **-0.0009 prob/pt [-0.0023, +0.0004]**, n=145. Full re-pricing of F8 would be ~ +0.028/pt (engine ml scale). Nothing detectable: the price does not move in the term's direction late; the inactives step is not carrying the term. (F8 is built from the Friday report, so this window is a proxy -- it detects drift toward the report-implied value, not the inactive list itself.)
- PLACEBO (Sat 12:00 -> ko-150min): -0.0001 [-0.0044, +0.0036], n=145 -- wide; consistent with zero.
- **Missing and sized:** (i) pre-report candles for the 415 KXNFLGAME markets (Wed-Fri; at 5-min ~ 1,500 candles/market) to test the Friday-report window; (ii) KXNFLSPREAD / KXNFLTOTAL / KXNFLTEAMTOTAL history is NOT FETCHED at all -- each is several strikes per game, a multiple of the 415 moneyline sets; (iii) 2026 games (weeks 1-6) have no candles; (iv) no inactives timestamp in nflverse, so ko-90min is approximated.

## B.4 Verdicts (with the numbers)

| Factor | Verdict | Basis | Stage |
|---|---|---|---|
| Team / QB base (engine v0 arm B) | **REAL-AND-PRICED** | Close ~ engine coef 0.81 (R2 0.66 spread, 0.54 total); W76.2: market ML mid beats every arm by ~0.009 Brier | applied |
| F8 non-QB starters out | **REAL-AND-PRICED (partly; the unpriced remainder is unproven)** | b = 0.67 [0.45, 0.87] spread / 0.34 [0.16, 0.51] total; outcome gain -0.0007 = size of a real term but power 20%; no late drift | applied |
| F5/F6 coverage x personnel | **INVISIBLE** | CIs span 0 and 1 on all three closes; P(BEATS) <= 5% at this size -- neither test can see it | applied |
| The engine itself (as a T1 game-market price) | **REAL-AND-PRICED -> no standalone edge** | Close contains what the engine knows and more; market leads by ~0.009 Brier (n=182, 2025) | applied |

Not shown: any NOT REAL. Nothing here proves a term worthless -- F5/F6 is simply below resolution.

## So what (recommend, not decide)

- Edge location: F8-type information is already in the close by the time the inactives list lands. The only window left that could still hold a lag is **Friday's report -> Saturday (T1 days-ahead/T2 boundary)**, which this archive cannot see. T2/inactives (same-day) shows no drift.
- Keep building game-market factors? **No-regret case against:** the market already prices ~2/3 of the biggest term we have; each further factor into the most-attended markets should be pre-registered as "thinner edge expected".
- Chase timing? **Cheap and falsifiable:** fetch Wed-Sun candles for KXNFLGAME 2025 games (one series, 5-min) and test the Friday-report window; then 2026 weeks 1-6.
- Thinner markets (team totals, props): this method cannot run there (no nflverse close for them); pricing share must come from the Kalshi series themselves -- that fetch is the prerequisite either way.
- Modal expectation recorded in PLAN.md (REAL-AND-PRICED or INVISIBLE) was the outcome.
