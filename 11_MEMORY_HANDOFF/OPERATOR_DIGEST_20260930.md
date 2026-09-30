# Operator Digest — 2026-09-30

- The NFL data feed was throwing away useful information (weather, starting quarterback, coaches, referee, sacks, penalties). It now keeps them.
- 2026 data is saved with a record of where and when it came from. Nothing was made up; missing values stay blank.
- The saved QB/weather values for weeks 1–3 are after-the-fact, not what was known before kickoff. Getting true pre-game values needs a repeat capture before games; nothing is scheduled.
- No model uses this data yet. No money at risk, no betting changes.
- The work sits on a branch, not yet merged into main.
