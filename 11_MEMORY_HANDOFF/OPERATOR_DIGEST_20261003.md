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

## 50.1 (cloud) — fixes to how sessions work; nothing new trading
- Fixed the session tool that accidentally put unreviewed work live last night, and made the test suite pass cleanly in cloud sessions. All checks are green.
- Checked all 30 recently logged problems: 5 can likely be closed, a few are real and worth fixing soon, and three NHL items must be fixed before any NHL result is read.
- Correction: last night's work *did* go live. Every code change to main automatically updates the server and restarts the live MLB process. That is probably who kept restarting it.
- Because merging restarts the live MLB process, this session's changes wait for you to merge them.
- Most urgent: a local session must turn on the NFL/MLB shadow jobs before Sunday's NFL games.
- Still zero real money at risk.

## 51.2 — NHL silent drops (STANDARD)
The hockey test run was quietly skipping about a quarter of the markets (379 of 1,595) because Kalshi abbreviates four teams (San Jose, Tampa Bay, Los Angeles, New Jersey) differently than our data does. Fixed the matching and added counters that now say why any market is skipped. The fix is saved on its own branch and NOT live: putting it live restarts the baseball engine, so that's your call on timing. Earlier hockey results never included games with those four teams. Still no real money at risk.
