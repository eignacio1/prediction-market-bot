# Operator Digest — 2026-10-03

- T-631 (auto): T-631 (W48.1 exp037-land-deploy) stopped early at operator request: NFL rebased onto main (suite not run), nothing landed/deployed.
- W51.3 (auto): W51.3 — PR #157 made merge-ready (head 42a0d0d, CI green, MERGEABLE); NOT merged; NHL shadow cell table recorded

## 2026-10-03 — Kill-switch follow-up (plain English)
- The MLB kill switch has not tripped, and it would not trip when the stuck bets are finally settled.
- Earlier today I warned it could cross the 20% line. That was wrong: 16 of the 17 stuck bets are on markets Kalshi cancelled, so they are not losses.
- Real loss on the book, once those settle, lands near 11-12%, safely under 20%.
- Still zero real money at risk. Nothing in the live system was changed.
- Your call: how to count the 16 cancelled bets (treat as void, or at Kalshi's final price, or leave out of the 30-bet gate).
- The dashboard fix is ready but waiting until no games are live, because applying it restarts the live bot.
