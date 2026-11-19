
## W119.2 — NBA depth wired (STANDARD)
NBA depth splits (matchup, rest, refs-style factors) are now wired into the router behind a switch that is OFF. Nothing live changed. The 12 NBA game cells now show as SHADOW in code, so the code count and the box agree at 60. A new layer-4 rule credits NBA spread T1 and team-total T1; D6 for NBA went from 4 to 7 wired on the box. Not credited: NBA moneyline T1-T3 (no per-arm evidence yet). Two factors (S3/S5) have no live data source on the box and log "unknown". Merged as PR #527, deployed. Your call later: when to flip the switch once shadow rows accrue.
## W119.3 - placement and log size (Earl)
- Moved: EXECUTION. The bot's FADE orders now try a better price on half of them, rest inside the spread, with the other half as the comparison. It's live on the box. Demo only, no real money.
- Early count only: 2 fills of 17 inside orders versus 22 of 342 at the touch. Far too few to judge; we need 100 orders and 20 games per side.
- The daily spending caps still block thousands of orders (about 5,000 RIDE, 2,000 each FADE and MOMENTUM) even after we raised them. Needs a look.
- The ride-board log is cut to what readers use; the real size saving shows up in about two days.
- Main's guard check was red from another window's gap cleanup; I fixed it with a generated file.
