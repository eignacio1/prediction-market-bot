# W82.2 — ADR-0072 forward-test verdict, read on the box

**Source:** `/opt/prediction-market-bot/exp_output/FORWARD_TEST/w82_2/demo_fill_forward_report.json` (generated 2026-10-21T04:59:25Z; copy committed beside this file as `W82_2_forward_test_report.json`).
**Scope:** post-top-up fills only (order submitted at/after 2026-10-16T05:40Z; earlier fills descriptive only). Judged n = 550 settled fills per arm, unit = per (book, sport). Seed `w64-2`, share 0.5; assignment check: 27,204 orders checked, 0 mismatches; turn-off checks: none tripped. No parameter changed.
**Pillar / measure:** EXECUTION — verdict words per (book, sport): 0 → 1 INCONCLUSIVE + 3 NO VERDICT YET (shadow book). Paper book has no control arm in the log: descriptive only.

## Verdicts (shadow book)

| Sport | Fills ctl / trt | Games ctl / trt | (a) diff settle−price | (a) 95% one-sided lower bound (game-clustered) | (b) fill-rate ratio (rates ctl / trt) | (c) markout | Verdict |
|---|---|---|---|---|---|---|---|
| NFL | 3,085 / 878 | 13 / 13 | +0.153 (se 0.123; 95% interval −0.050 to +0.356) | −0.050 | 0.288 (0.575 / 0.166), holds | NOT_EVALUABLE (0 markouts) | **INCONCLUSIVE at judged n** — (a) lower bound not above 0, not rejected |
| NHL | 1,150 / 80 | 31 / 22 | +0.237 (se 0.092; interval +0.087 to +0.388) | +0.087 (descriptive) | 0.064 (0.562 / 0.036) — would FAIL (<0.25) | NOT_EVALUABLE | **NO VERDICT YET** (smaller arm 80 of 550) |
| NBA | 1,530 / 137 | 3 / 3 | +0.060 (se 0.077; interval −0.068 to +0.187) | −0.068 (descriptive) | 0.134 (0.429 / 0.058) — would FAIL | NOT_EVALUABLE | **NO VERDICT YET** (137 of 550) |
| MLB | 0 / 0 | 0 / 0 | n/a | n/a | n/a | NOT_EVALUABLE | **NO VERDICT YET** (0 of 550) |

No cell reads "(a)/(b) hold, pending (c)". (c) markouts are collected forward by `scripts/demo_fill_markout_collector.py` (epoch `exp_output/FORWARD_TEST/markouts/EPOCH.json`, created 2026-10-21T04:30Z); every cell stays NOT_EVALUABLE until markout rows reach judged n. Nothing may be ADOPTed before (c) is judged.

## Reading

- NFL reached judged n and did not clear (a): treatment edge is positive on point estimate but the lower bound is below 0 on 13 games. Not a rejection; with games clustered the interval is wide.
- NHL looks strongest on (a) but the treatment arm fills at 6% of control's rate; (b) would fail on current numbers. Descriptive only below judged n.
- NBA is 1 day into the season (3 games per arm); nothing to read.
- MLB: no post-top-up settled fills in either arm.

## Projected date to judged n (smaller arm, from post-top-up accrual 2026-10-16 → 2026-10-21, ~5 days)

- NHL: 80 fills in ~5 days ≈ 16/day; 470 to go ≈ 29 days → ~2026-11-19 (treatment fill rate is the constraint; assumes current rate holds).
- NBA: 137 fills accrued in the ~1 day since the 2026-10-20 opener; rate is a single-day estimate, so range ~2026-10-26 to 2026-11-05.
- MLB: season over; no projection (unlikely to reach 550 before spring 2027).
- NFL: judged n reached; verdict is INCONCLUSIVE, more games would narrow the interval but the state is already issued at this look.
