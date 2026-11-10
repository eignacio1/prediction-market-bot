# Router precedence — pre-registered BEFORE the POT_OF_GOLD branch is wired (W106.1 / B-056)

Committed before any change to `decision_trees/router.py`. Rules below are fixed; changing one is a dated edit
here plus a superseding note, not a quiet code change.

## Branches and what each claims
| Branch | Claims | Source |
|---|---|---|
| FADE | a side, when measured model skill and net edge exist | `_fade` |
| RIDE | a side, from a HELD_OUT / FORWARD_PASSED ride cell | `_ride` |
| POT_OF_GOLD | a side, from a HELD_OUT / FORWARD_PASSED longshot cell (`longshot.decide`: FADE_LONGSHOT, TAKE_FAVOURITE, BUY_LONGSHOT) | `_pot` |
| MOMENTUM_FOLLOW / MOMENTUM_FADE | a side, from a measured transition cell | `_momentum` |

## Rules (in order)
1. **Disqualifiers first.** `_disqualify` applies to every branch unchanged (no two-sided book, no tier, D0, price extreme).
2. **Status gate, everywhere.** A branch claims a side only from a cell with status HELD_OUT or FORWARD_PASSED and a
   net lower bound > 0 inside its book gate. IN_SAMPLE, FAILED, UNTESTED, missing cell: no claim. So an IN_SAMPLE
   pot-of-gold cell never produces a POT_OF_GOLD route, hence never an order.
3. **Opposite sides = NO_BET.** If any two of FADE, RIDE, POT_OF_GOLD claim opposite sides of the same market
   (e.g. FADE says NO while TAKE_FAVOURITE says YES), the route is NO_BET with reason `conflict`. No branch wins
   a disagreement; a disagreement between two measured claims is itself unmeasured territory.
4. **Same side = the more specific measured cell names the route.** Order of naming: RIDE, then POT_OF_GOLD, then
   FADE. Agreement is recorded (`agreed=True`, reason `<other>_agrees`). Sizing is not touched by agreement.
5. **POT_OF_GOLD alone** routes as POT_OF_GOLD with the longshot cell attached to the Route.
6. **MOMENTUM is last.** It only speaks when FADE, RIDE and POT_OF_GOLD all make no claim (unchanged).
7. **Existing T3 overlay unchanged:** FADE under t3 == "FADE" is HOLD (no claim) before rules 3-4.
8. **No evidence, no branch.** `Evidence.longshot is None` loads the shipped `longshot_cells.toml`; an empty table
   claims nothing. Default behaviour with zero orderable cells is byte-identical to today's router (NO_BET).

## Pre-registered expectation
With the shipped table (17 cells, all IN_SAMPLE) POT_OF_GOLD routes 0 live markets. The "17 cells routed" measure
means 17 cells are wired into the router in paper (logged as NO_BET `longshot:status_IN_SAMPLE`), not 17 orderable.
