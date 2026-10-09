
## W61.2 (T-750) — verdict readiness
The release path for the NFL first look now works end to end. In a rehearsal on a synthetic fixture, 59 games stayed sealed. At 60 games the cell released a manifest, an engine verdict and a first-look report, and the dashboard showed the verdict word. The rehearsal found two gaps, both fixed and deployed: the report was never written, and the dashboard never showed the verdict. GG-401 is closed and the gap log is trimmed. The NFL date rests on 100% schedule coverage, and no scores were read. One new open item: GG-532, the MLB shadow arm silent since 2026-10-08 01:43Z. It is unreproduced and needs its own session. No order, kelly or ledger changes.
- T-751 (auto): W61.3 exploratory fence + NFL challenger studies merged; no improvement over frozen EXP-037; no pre-registration warranted.

## W61.1 - T4M-PROJ now judged on real fills only
- The bot's player-hit strategy is now scored only on bets the exchange actually filled: 166 of 4,220 closed bets. The other 4,054 never filled and are kept only as a record of the model's predictions.
- After the 2026 World Series the bot stops placing paper bets on this strategy automatically. Predictions keep being recorded. Turning bets back on needs a new decision from you.
- One thing waiting: the running bot hasn't picked up the stop yet because a game was live during the update. It needs a restart after the last game, well before spring 2027.
- No real money involved; paper only.

## W62.2 — NFL history secured, first-look expectations written
- The saved 2025 Kalshi NFL price history is complete (892 of 892 games) and now copied to the server with checksums verified.
- I wrote down, before any 2026 results exist, what the first NFL look can and can't tell us. With 60 games per cell it can only detect a gap of about 0.038; last season's gap vs the market was about 0.008. Most likely result: "keep collecting."
- Nothing here touches live betting or money. Still zero real money at risk.
- Your calls: refresh the older tracked history files, schedule a server copy, and whether to flag that our assumed noise level looks too optimistic.
## W62.1 — MLB postseason tracking + silent-arm alarm
The MLB playoff tracker had gone quiet because it couldn't match a game whose start time had moved. That is fixed and live on the server. I also built an alarm: if a sport has games on the schedule but the tracker writes nothing, the dashboards now turn red and say how many hours it has been silent. Tested against the stored data, it would have gone red on the first evening. The tracker is not confirmed healthy yet; that needs its next scheduled run (about 12:07 UTC today). No money at risk, no betting changes.

## W62.3 (T-756) — STANDARD
- GG-527 RESOLVED: running t4-mlb has the stand-down gate (one authorized restart).
- T1 MLB: only 85 of 485 orders filled (17.5%). Fills -$1.50/bet, non-fills +$0.03/bet; both CIs span zero. Registered GG-536. Your call: what may the T1 book claim.
- NBA: flip check not ready (0 rows); removal script and first-look release verified, no src change.
- Do on/after 2026-10-21 10:00 UTC: `python3 scripts/remove_nba_preseason_cron.py` (dry-run, then `--apply`) and `scripts/w59_3_nba_flip_check.py`.
- Hook timeout: `governance_scan.sh` needs `"timeout": 120` in `.claude/settings.json`; not changed, say yes.

**W63.1 — MLB at full for the playoffs.** The 12 MLB game-bet categories (who wins, run line, game total, team total, at three timings) are now being tracked and counted. Coverage rose from 25 to 37 of 104 cells, and from 8 to 12 of 18 bet families. Still practice only, no money at risk. The player-hits arm was never broken: it matched players on every playoff game day, and today's zero is simply an off day. The next real check is tomorrow's 7am ET run.
- T-766 (auto): W63.2 Part A: NFL translation map written (MLB game model = NFL structure; top analogue is QB-shrunk performance); Part B pending.
