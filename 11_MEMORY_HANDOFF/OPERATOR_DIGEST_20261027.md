
## W87.2 — kill switch on every order path (PARTIAL)
- The kill switch now watches the MLB T1 book and all shadow books on the box. The MLB T4 book joins once t4-mlb restarts; it was left running because a game was live.
- Every order now asks the switch first, but it is only logging what it would have blocked. Nothing is refused yet.
- Next: after one full game day, read that log, explain every would-halt, then flip to enforce in a separate PR.
- GG-1082 and GG-441 stay open until enforcement is on and read back on the box.
- No limits, stakes or orders changed. No real money involved.

## W88.2 (partial)
Still zero real money at risk. We found why the MLB game-market tracker went quiet: its data feed stopped refreshing after the season's last game, and that is fixed. Shadow records now carry when the price was read. Not done: switching the safety stop from "log only" to "enforcing". It waits for tonight's game to end. Nothing needs you for it.
