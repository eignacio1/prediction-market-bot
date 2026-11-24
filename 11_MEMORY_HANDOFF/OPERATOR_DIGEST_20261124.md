# Operator digest 2026-11-24
We built the tools that tell us how many more games each open question needs, and put a date on 9 of 18 of them (2 before). Earliest: NFL inactives about Dec 1; NBA props about late January. Our own early-line price reads slightly positive before costs and clearly negative after, so nothing here is a win yet. No real money, no change to the running bot. One site check (Docs Guard) is red on main from before this work.
# Operator Digest — 2026-11-24

- W124.4 (auto): W124.4 dense capture built and tested (props, 5-min games, trade prints); budget gate refuses on box disk; install not run, PR #556 unmerged
- W124.3 (auto): W124.3 H-EXEC-4 pre-registered before any forward fill was read; COLLECTING, first look 2026-12-01; PR #554 unmerged (guard red on main).

## W125.1 — Placement as a decision (EXECUTION E2/E3)
- **Built:** a fill model from real demo fills, by arm, market family and hours to start, with the fee actually charged and game-clustered intervals. A placement-rules switch is merged but OFF. The rules file is empty.
- **Found:** 3,214 orders since 11-12. The best cell has 11 settled-filled games against the bar of 20, so no placement rule is supported yet. Momentum fills most. Fade, ride and model-fade rarely fill. Markouts at +5 and +30 min are within 2¢ of zero.
- **Caps:** the day and event caps removed 13,237 orders, mostly before the raised caps took effect on 11-18. One leftover real-money copy sits in the RIDE board caps ($500 / $150). It is registered as GG-2008 and starves nothing today.
- **Needs you:** nothing. Turning the rules on is a dated proposal in RESULT.md, waiting on 20 games per cell.
