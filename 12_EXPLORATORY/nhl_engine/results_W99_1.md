# W99.1 Part C — NHL overtime / shootout credit and the totals bias

Exploratory; merged model unchanged, no new `src/` module (there is no rule gap to build, see 1). Held out 2023–2025 regular season, 3,936 games, fit on strictly earlier seasons, `level_adjust` as in W98.1.

**1. The settlement rule is already exact in the merged model.** Rules read verbatim from R-067's cards (`sources/kalshi/{game,total,spread}.md`, HOCKEYWINNINGINPERIOD / HOCKEYTOTALS / HOCKEYSPREADS, Amendment 2, 2026-09-21): moneyline, totals and spreads count regulation + overtime + shootout by default; "A team winning the shootout constitutes one (1) goal for the team"; "Overtime goals are included unless explicitly excluded"; a tied *period* (sub-period markets only) is differential zero. Checked against the data: settled total − regulation total = +1 on 1,222 of 1,222 regulation ties and 0 on 4,257 of 4,257 non-ties (2022–2026 regular season). So an OT goal and a shootout credit both add exactly one, and `goals.simulate` (tie → winner +1) reproduces that. Regulation ties are always broken in all three families. No fix is licensed.

**2. Where the totals bias actually lives** (predicted − actual, goals/game; `results/w99_1_ot_diag.json`):

| Season | settled total | regulation total | tie-credit part | pred tie | actual tie |
|---|---|---|---|---|---|
| 2023 | −0.170 | −0.199 | +0.029 | 0.236 | 0.207 |
| 2024 | −0.115 | −0.134 | +0.019 | 0.226 | 0.207 |
| 2025 | −0.059 | −0.027 | −0.033 | 0.216 | 0.248 |

The under-prediction is in regulation scoring, not in the OT/SO credit. The credit part changes sign across seasons (+0.029, +0.019, −0.033; the tie-rate sampling error at n=1,312 is ≈ 0.011), which is what noise around a correct rule looks like. The open candidate cause from W98.1 is **falsified**: OT/SO credit and tie handling do not carry the totals bias. The remaining cause is the regulation level (the xG feature is refit each season; the bias shrinks 2023 → 2025, consistent with level drift that `level_adjust` only partly absorbs).

**3. The one OT/SO knob, `tie_odds` (fitted 1.41–1.59, lifts the regulation tie probability above independent Poisson), merged vs `tie_odds = 1.0`** (paired Brier, game-clustered 95% CI; `results/w99_1_ot_tieodds.json`):

| Family | merged | tie_odds=1 | difference [CI] |
|---|---|---|---|
| ML | 0.2393 | 0.2391 | −0.00018 [−0.00043, +0.00007] |
| SPREAD_HOME | 0.1970 | 0.1951 | **−0.00186 [−0.00233, −0.00136]** |
| TEAMTOTAL_HOME | 0.2328 | 0.2327 | −0.00010 [−0.00029, +0.00010] |
| TEAMTOTAL_AWAY | 0.2349 | 0.2350 | +0.00015 [−0.00006, +0.00036] |
| TOTAL | 0.2216 | 0.2218 | **+0.00024 [+0.00009, +0.00040]** |

Totals ladder mass moves by about −0.015 goals either way (against a bias of −0.03 to −0.20), so the knob cannot move the totals bias. It trades a small spread gain for a smaller totals loss. Both differences are under 0.002 Brier, chosen after seeing the held-out data; **not a result to freeze**. If the spread gain is wanted, it needs its own pre-registration on later seasons.

**4. This season vs Kalshi (descriptive).** Merged model, 2026, PRICE_ARCHIVE quotes, same 33 games as W97.4 (archive window since 2026-10-28T05:03Z): engine Brier 0.1849 vs market 0.1792, advantage −0.0057 (SE 0.0035, P(>0) 0.096); by family ML −0.007, SPREAD −0.008, TOTAL −0.005, TEAMTOTAL −0.005. Unchanged from W97.4 because the model is unchanged; nothing here is scored (n=33). `results/w99_1_kalshi_2026.json`.

**5. EXP-046: not earned, not frozen.** No variant moves totals; the market still leads on all four families.

**Stage.** NHL totals: regulation level is the open work, not settlement. D5(b) unchanged for NHL officials-free factors; this part moved no pillar measure but closed a candidate cause (PROOF: one hypothesis ruled out with a measurement).
