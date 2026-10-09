
## W61.2 (T-750) — verdict readiness
The release path for the NFL first look now works end to end. In a rehearsal on a synthetic fixture, 59 games stayed sealed. At 60 games the cell released a manifest, an engine verdict and a first-look report, and the dashboard showed the verdict word. The rehearsal found two gaps, both fixed and deployed: the report was never written, and the dashboard never showed the verdict. GG-401 is closed and the gap log is trimmed. The NFL date rests on 100% schedule coverage, and no scores were read. One new open item: GG-532, the MLB shadow arm silent since 2026-10-08 01:43Z. It is unreproduced and needs its own session. No order, kelly or ledger changes.
- T-751 (auto): W61.3 exploratory fence + NFL challenger studies merged; no improvement over frozen EXP-037; no pre-registration warranted.

## W61.1 - T4M-PROJ now judged on real fills only
- The bot's player-hit strategy is now scored only on bets the exchange actually filled: 166 of 4,220 closed bets. The other 4,054 never filled and are kept only as a record of the model's predictions.
- After the 2026 World Series the bot stops placing paper bets on this strategy automatically. Predictions keep being recorded. Turning bets back on needs a new decision from you.
- One thing waiting: the running bot hasn't picked up the stop yet because a game was live during the update. It needs a restart after the last game, well before spring 2027.
- No real money involved; paper only.

## W62.1 — MLB postseason tracking + silent-arm alarm
The MLB playoff tracker had gone quiet because it couldn't match a game whose start time had moved. That is fixed and live on the server. I also built an alarm: if a sport has games on the schedule but the tracker writes nothing, the dashboards now turn red and say how many hours it has been silent. Tested against the stored data, it would have gone red on the first evening. The tracker is not confirmed healthy yet; that needs its next scheduled run (about 12:07 UTC today). No money at risk, no betting changes.
