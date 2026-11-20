# H4 execution / liquidity - result (W123.4, 2026-11-20)

**Last reviewed:** 2026-11-20. **Pre-registration:** `../HYPOTHESIS.md` section 3 (H4) + Addendum A (before results) + Addendum B (after the
frozen run returned 0 fills; disclosed there). **Code:** `scripts/h4_quote_sim.py`, test `tests/test_h4_quote_sim.py`.
**Data:** 2,131 post-epoch (>= 2026-11-06T01:03:42Z, GG-1771) arm orders, 157 fills, 1,738 settled; price archive 2.26M snapshots
(2026-11-06 on), 185,304 settled public Kalshi tickets. Raw: `result_gap15_frozen.json`, `result_gap35.json`.

## Verdict
**H4: hypothesis closed (EXP H-EDGE-4, parked for R&D) - NOT SUPPORTED, with a caveat on what was and was not tested.**
- The frozen rule (next snapshot <= 15 min) produced **0 simulated fills**: literally UNDERPOWERED. My Addendum A assumed 3-8 min
  snapshot spacing; the archive's real spacing is 19-30 min. That is a window error, logged below.
- The sensitivity run (gap <= 35 min, Addendum B, written after seeing the 0) gives 70,346 simulated fills; **18 family cells judged
  (>= 20 games), 0 with a net above zero.** Best: NHL spread -0.011 [-0.034, +0.013], NHL total -0.017 [-0.041, +0.006] per contract.
  Gross of adverse selection (spread earned minus the maker fee only) is **negative in all 18 judged cells (-0.076 to -0.131)**. So the
  verdict does not rest on the adverse-selection term: quoting one tick inside the top of book loses before AS is applied.
- Not tested: variant (b) consensus as fair (no free consensus overlaps the window); horizon below 24h (archive `close_time` is expiration,
  so every simulated fill is 24h+); intra-snapshot trades; queue position. A tighter-sampled depth capture could revisit it.

## Part A - adverse selection on real fills (1,738 settled orders: 145 filled, 1,593 unfilled)
Edge = won - limit price per contract. Positive AS = filled orders did worse than unfilled.
- **Pooled AS = -0.065** (filled +6.4c vs unfilled -0.8c at rest_touch). In aggregate the pre-registered measure does NOT show filled
  orders doing worse; fills are 101 NBA spread (22 games), 25 NBA total, rest 19 across 8 games. It is concentrated, not general.
- **RIDE** shows the earlier pattern: win 70.0% filled vs 80.9% unfilled (edge +1.7c vs +3.2c). FADE win 27.8% vs 19.6%, MOMENTUM 51.7% vs
  44.5% (filled better). Per family x horizon cells reach the 10-real-fill minimum only for NBA spread; every other family falls back
  to its family or to the pooled value (flagged `as_level` in the JSON).
- **Markouts of real fills** (mean, dollars, mid vs fill): 1 min -0.009 to -0.013 for RIDE/MOMENTUM/MODEL_FADE, FADE +0.006; 5 min FADE +0.027;
  30 min about 0; to the close FADE +0.024, MOMENTUM -0.003. Small and mostly inside one tick: no strong post-fill drift against us.
- By placement: rest_touch 137 fills, rest_inside 8 (too few to read: win 12.5%). By hours-to-close: 2-6h 68 fills (edge +10.1c), 6-24h
  71 (+2.0c), 0-2h 4, 24h+ 2. Full tables are in `result_gap35.json` under `part_a`.

## Part B - simulation (variant (a), market mid as fair; one contract each side)
Rule: spread >= 3 ticks; bid = bid+1c, ask = ask-1c; filled if the next snapshot trades through; held to settlement; maker fee;
net = gross - fee - AS; game-clustered bootstrap (2,000 draws, seed 20261120), 90% interval; BH q = 0.10 over K = 18.
| Family (24h+) | fills | games | net / contract [90%] | gross |
|---|---|---|---|---|
| NBA game | 205 | 72 | -0.063 [-0.110, -0.007] | -0.063 |
| NBA spread | 2,968 | 105 | -0.095 [-0.119, -0.069] | -0.107 |
| NBA total | 3,372 | 105 | -0.020 [-0.041, -0.001] | -0.087 |
| NBA team total | 11,912 | 105 | -0.034 [-0.045, -0.024] | -0.099 |
| NBA props (3pt, ast, pra, pts, reb) | 5.6-8.3k each | 72 | -0.114 to -0.125 | same |
| NFL spread / total / team total | 711 / 517 / 967 | 29-30 | -0.046 / -0.066 / -0.034 | -0.110 / -0.131 / -0.098 |
| NHL game | 112 | 61 | -0.027 [-0.125, +0.064] | -0.092 |
| NHL spread | 552 | 98 | -0.011 [-0.034, +0.013] | -0.076 |
| NHL total | 785 | 104 | -0.017 [-0.041, +0.006] | -0.081 |
| NHL team total / first goal / anytime | 3,392 / 1,648 / 2,076 | 73-108 | -0.112 to -0.124 | same |
Not judged (< 20 games): NFL game, NFL pass/rec/rush yards, NFL TD. AS used: 0 where no real fills exist for that family (so those cells carry
no AS credit or charge), the pooled -0.065 where only pooled data exist (that is a credit to net, so it flatters the result; gross shown beside it).
The sim and the real-fill measure disagree on sign of adverse movement, and gross is negative either way: the loss is the spread inside
being picked off by moves, plus fee, over a 20-30 min window.

## What this changes
No two-sided quoting demo proposal is written (rule: only if SUPPORTED). Capacity and placement work continue as before (FADE crossing
stays the W117.1 lead). Window error logged: the Addendum A snapshot-spacing assumption was never checked against the archive before it
was frozen.
