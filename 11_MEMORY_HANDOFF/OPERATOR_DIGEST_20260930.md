# Operator Digest — 2026-09-30

- The NFL data feed was throwing away useful information (weather, starting quarterback, coaches, referee, sacks, penalties). It now keeps them.
- 2026 data is saved with a record of where and when it came from. Nothing was made up; missing values stay blank.
- The saved QB/weather values for weeks 1–3 are after-the-fact, not what was known before kickoff. Getting true pre-game values needs a repeat capture before games; nothing is scheduled.
- No model uses this data yet. No money at risk, no betting changes.
- The work sits on a branch, not yet merged into main.

## T-595 — keeping the evidence trail safe
- No money moved; nothing was changed on the live system.
- I saved a permanent copy of the records that prove which version of the bot produced past bets. Those records were set to expire in about a month. All 13 checks against them pass.
- New bets will now carry a label saying which model made them. Older bets stay unlabeled. I did not touch them.
- Those bets still don't count toward the proof: the counters don't read the label yet, and the change isn't deployed.
- A queued change from another session would stop all new bets if it went live before this one. Please don't merge it first.
- One cleanup of stale drafts is blocked by a lock on the shared folder. I left it for you.
