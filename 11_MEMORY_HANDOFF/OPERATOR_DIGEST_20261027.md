# Operator Digest — 2026-10-27 (W89.1)

The kill switch is now enforcing on every order path, and I confirmed it on the box. A missing state file, a tripped book, or an unmapped band each refuse the order. Live state is healthy: MLB_T1 is feeding it and nothing is breached.

It went live without a LOG-ONLY game day first, as you directed. The cost is that we have no would-halt data. The thing to watch is a healthy book being wrongly refused, which would show up as zero fills. Rollback is one env var (`EXPOSURE_GATE_MODE=log`) or reverting bb03fd4.

Not done: the MLB-arm read-backs after the 06:07Z run (GG-1230/1232), an alarm for GG-1231, and the surface budget re-read, so RED to GREEN is unconfirmed. Also, the MLB_T4 book only appears once a game goes live. Status: PARTIAL.
- T-1290 (auto): W89.7 Part A partial: NBA/NHL/NFL Kalshi backfill + true-start join; PR 349 CI failed on EXPLORATORY fence, unmerged
