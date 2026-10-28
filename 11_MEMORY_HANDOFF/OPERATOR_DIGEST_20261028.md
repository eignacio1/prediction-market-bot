# Operator Digest 2026-10-28

**Momentum test (W90.3).** We asked: when a game's price jumps 3 cents or more before the game, should the bot follow it or bet against it? Across about 20,000 moves in MLB, NFL, NBA and NHL, the answer is neither. The price afterward drifts randomly, and trading costs eat 4 to 17 cents per dollar either way. No situation was found where following or fading works, so the router gets nothing to route to momentum. Two small hints exist but are probably noise; we wait for real news timestamps and more data. Pillar moved: depth and proof. No money at risk, nothing running changed.
- T-1300 (auto): W90.1 PARTIAL: PRs 349 and 352 merged; hold-out scan 0 candidates (underpowered, GG-1292); Part B not started
- T-1350 (auto): W91.3 partial: #347 and #354 merged (6 NBA/NHL archive cron lines); box crontab install pending operator OK; scan not started
- W91.2 (T-1345, STANDARD): ride tree is now tested code (#353; nothing wired). Ladder ride measured on NFL+MLB (#356): net +0.007/bet [-0.002, 0.017]; 2 of 36 cells HELD_OUT (KXMLBTOTAL T0-2h tight, one OOS split, 5c+ only 30 games). Suggest adding both as HELD_OUT in ride_cells.toml and forward-testing. No operator decisions.

**W92.2 (proof work) — partly done.** Kalshi's exact trading fees are now in the code. They show our old fee estimate was too high for MLB, so past MLB results were slightly understated, not overstated. Two promising ladder-trade patterns are recorded as "held out" and a forward test (EXP-043) is locked in. No test can finish before 2027, because baseball is out of season and the pooled test needs thousands of games. Not done: re-checking every published result with the exact fees. Still zero real money at risk. One call for you: keep the two frozen experiments (EXP-041/042) on the old fee? I recommend yes.

## W92.1 — winter price archive (plain English)
The bot now records NBA and NHL betting prices around the clock, the same way it already did for baseball and football. That data is what lets us test those markets later without guessing. The six recording jobs had been written down in the plan but were never actually switched on; they are on now and we confirmed prices are landing. We also fixed the health check that had said "all green" while those jobs were off. No money, no bets, no change to anything trading. Nothing for you to do.

## W92.3 — NBA lineups and on/off (DEPTH)
Built point-in-time lineup/on-off ratings from play-by-play (PR #359, merged, CI green). On held-out 2024-26 games it lowers total-score error (gain 4.04, CI 1.92 to 6.10); no gain on margin beyond prior-season carry. B7 is interpreted on the total only, not applied: no NBA pre-game prices exist yet (92.1 capture not installed), so a market test is underpowered. K and decay untuned. Deploy read-back: main runs were cancelled by newer pushes; nothing t4-mlb imports changed. No operator decisions.

## W93.2 — NBA travel, time zones, altitude, referees
Moved: DEPTH (the NBA model's factor list grew by two).
- Built and tested two new pieces of NBA context: how far and how tired a team is coming into a game, and how tightly each referee crew calls fouls.
- Honest result: travel and time zones do not help predict who wins by how much. High altitude (Denver, Utah) nudges the total score up a little. Referee crews have only a weak, unstable effect.
- One gap: the league does not publish when a referee crew is assigned, and I found no free, allowed way to capture it live. A workaround attempt was refused by the safety check and I stopped there.
- No money, no bets, nothing new running. Zero real money at risk.

## W93.1 - NBA availability known before tip (T-1420)
- Built a point-in-time availability layer from the official injury report: a player listed Out plays 0.1% of the time, Questionable 51%, Probable 92%, Available 86%, not listed 76%.
- Using only what was known at tip, availability does not demonstrably improve the margin forecast beyond the rotation baseline (gain 0.307, interval spans zero, 2,008 games). That is an honest NO at this sample size.
- One lead: expected missing minutes does help (2.641, interval excludes zero). Carry it forward.
- Applied (against a price) is blocked: no 2026-27 event data yet and pre-tip prices only began accruing 2026-10-28. Registered as GG-1420 for the flex lane.
- PR #364 merged after two CI fixes. Deploy is by VPS cron now, not a GitHub job; no t4-mlb file was touched, so no t4-mlb restart is needed.
- Nothing needed from you.
