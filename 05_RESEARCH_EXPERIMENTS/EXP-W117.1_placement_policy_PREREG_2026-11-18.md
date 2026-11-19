# EXP-W117.1 placement policy - pre-registration (frozen 2026-11-18T04:52:49Z)
**Last reviewed:** 2026-11-18. Demo only, kelly_fraction 0. Operator approved the frozen table and the switch 2026-11-17.

**Fit (before freeze, orders to 2026-11-18T03:45:47Z, post-epoch, never pooled with pre):** 486 orders; spread logged 0, archive-backfilled 454, none 32.
Per arm, game-clustered 95% interval of (cross - rest_touch) net per order, after exact fees and the real spread:
| arm | orders | games | cross net | cross - rest_touch |
|---|---|---|---|---|
| FADE | 105 | 20 | +0.166 [-0.016, +0.348] | +0.160 [-0.026, +0.345] |
| MOMENTUM | 96 | 21 | +0.052 [-0.087, +0.191] | +0.025 [-0.089, +0.139] |
| RIDE | 253 | 22 | +0.016 [-0.057, +0.089] | +0.016 [-0.056, +0.089] |

**Rule (policy.table_from_clustered):** a cell names `cross` only if the interval of (cross - rest_touch) is wholly above 0 AND the cell has
>= 20 games (minimum n per cell). Otherwise it keeps today's rule: rest at the touch, cancel at 60 s.
**Result: no cell qualifies. The frozen table has zero cells; every order stays rest_touch.** Turning the switch on is therefore a no-op until a
re-fit; it is on so the path is exercised and the next fit needs no code change.

**Forward comparison (policy vs today's rule):** identical while the table is empty. A re-fit is a new dated table and a new line here, on
spread-logged orders only (not archive-backfilled), post the freeze. Judged n: 100 resolved orders AND >= 20 games per arm and option.
**Reading a look:** per arm, the clustered interval of (cross - rest_touch) after costs. Wholly above 0 -> that cell gets `cross` in the next
frozen table. Includes 0 -> unchanged. Wholly below 0 -> the hypothesis "crossing helps this arm" is closed (EXP-W117.1, parked for R&D); no
arm closes. No look is read below its judged n.

**W119.3 amendment (2026-11-18):** one FADE cell added as a forward test (rest_inside, 50/50 vs rest_touch control); see EXP-W119.3_fade_inside_spread_PREREG_2026-11-18.md. The cross rule above is unchanged.
